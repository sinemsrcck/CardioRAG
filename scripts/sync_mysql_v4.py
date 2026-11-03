
import argparse
import csv
import getpass
import hashlib
import re
from pathlib import Path

import mysql.connector

from src.core import v4_collection


MANIFEST = Path("data/new_pdfs_manifest.csv")
METADATA = Path("data/pubmed_metadata_new.csv")

CHUNK_PATTERN = re.compile(r"^([0-9a-f]{64})_p(\d+)_c(\d+)$")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pdf_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare_chunks(collection, file_hash):
    result = collection.get(
        where={"file_id": file_hash},
        include=["documents", "metadatas"],
    )

    chunks = []
    seen = set()

    for chunk_id, content, metadata in zip(
        result["ids"],
        result["documents"],
        result["metadatas"],
    ):
        match = CHUNK_PATTERN.fullmatch(chunk_id)

        if not match:
            raise ValueError(f"Gecersiz Chroma ID: {chunk_id}")

        hash_part, page, page_index = match.groups()

        if hash_part != file_hash:
            raise ValueError(f"Hash uyusmazligi: {chunk_id}")

        if metadata.get("file_id") != file_hash:
            raise ValueError(f"Metadata hash uyusmazligi: {chunk_id}")

        if int(metadata.get("page", -1)) != int(page):
            raise ValueError(f"Sayfa uyusmazligi: {chunk_id}")

        if chunk_id in seen:
            raise ValueError(f"Tekrarlanan chunk: {chunk_id}")

        if content is None:
            raise ValueError(f"Bos dokuman alani: {chunk_id}")

        seen.add(chunk_id)

        chunks.append((
            int(page),
            int(page_index),
            chunk_id,
            content,
        ))

    chunks.sort(key=lambda x: (x[0], x[1]))

    if not chunks:
        raise ValueError(f"Chroma chunk bulunamadi: {file_hash}")

    return chunks


def sync_one(conn, collection, row, article):
    pmcid = row["pmcid"].strip()
    pmid = article["pmid"].strip()
    path = Path(row["full_path"])

    if not path.is_file():
        raise FileNotFoundError(path)

    if article["pmcid"].strip().upper() != pmcid.upper():
        raise ValueError(f"PMCID uyusmazligi: {pmcid}")

    if article["status"] != "matched":
        raise ValueError(f"Metadata dogrulanmamis: {pmcid}")

    file_hash = pdf_hash(path)
    chunks = prepare_chunks(collection, file_hash)

    cursor = conn.cursor()

    try:
        conn.start_transaction()

        # Mevcut PMID kaydini degistirmiyoruz.
        cursor.execute(
            "SELECT pmcid FROM makaleler WHERE pmid = %s",
            (pmid,),
        )
        existing_article = cursor.fetchone()

        if existing_article is None:
            year = article["yil"].strip()

            cursor.execute(
                """
                INSERT INTO makaleler
                (pmid, pmcid, doi, baslik, yazarlar,
                 dergi, yil, abstract)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    pmid,
                    pmcid,
                    article["doi"].strip() or None,
                    article["baslik"],
                    article["yazarlar"],
                    article["dergi"],
                    int(year) if year else None,
                    article["abstract"],
                ),
            )
        elif (existing_article[0] or "").upper() != pmcid.upper():
            raise ValueError(f"Mevcut PMID-PMCID uyusmazligi: {pmid}")

        # PDF hash benzersiz olmali.
        cursor.execute(
            """
            SELECT dokuman_id, pmid
            FROM dokumanlar
            WHERE dosya_hash = %s
            """,
            (file_hash,),
        )
        existing_document = cursor.fetchone()

        if existing_document:
            document_id, document_pmid = existing_document

            if document_pmid != pmid:
                raise ValueError(
                    f"PDF hash baska PMID'ye ait: {file_hash}"
                )
        else:
            cursor.execute(
                """
                INSERT INTO dokumanlar
                (pmid, dosya_turu, dosya_yolu, dosya_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (pmid, "pdf", str(path), file_hash),
            )
            document_id = cursor.lastrowid

        # Kismi aktarim varsa tekrar eklemek yerine
        # mevcut kayitlari kontrol ediyoruz.
        cursor.execute(
            """
            SELECT chunk_sirasi, chroma_id
            FROM chunklar
            WHERE dokuman_id = %s
            """,
            (document_id,),
        )
        existing_chunks = dict(cursor.fetchall())

        if existing_chunks:
            expected_ids = {
                i: chunk[2] for i, chunk in enumerate(chunks)
            }

            if existing_chunks != expected_ids:
                raise ValueError(
                    f"Mevcut chunk kayitlari uyusmuyor: {pmcid}"
                )

            conn.commit()
            return len(chunks), "already_synced"

        records = [
            (
                document_id,
                index,
                content,
                EMBEDDING_MODEL,
                page,
                page_index,
                chunk_id,
            )
            for index, (page, page_index, chunk_id, content)
            in enumerate(chunks)
        ]

        cursor.executemany(
            """
            INSERT INTO chunklar
            (dokuman_id, chunk_sirasi, metin,
             embedding_modeli, sayfa_no,
             sayfa_chunk_index, chroma_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            records,
        )

        conn.commit()
        return len(records), "inserted"

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Islenecek maksimum PDF sayisi",
    )
    args = parser.parse_args()

    if args.limit < 1:
        raise ValueError("Limit en az 1 olmali")

    manifest = load_csv(MANIFEST)
    metadata_rows = load_csv(METADATA)

    metadata = {
        row["pmcid"].strip().upper(): row
        for row in metadata_rows
    }

    collection = v4_collection()

    password = getpass.getpass("MySQL root sifresi: ")

    conn = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag",
        autocommit=False,
    )

    inserted = 0
    skipped = 0
    total_chunks = 0

    try:
        for index, row in enumerate(manifest[:args.limit], 1):
            pmcid = row["pmcid"].strip().upper()
            article = metadata.get(pmcid)

            if article is None:
                raise ValueError(f"Metadata bulunamadi: {pmcid}")

            count, status = sync_one(
                conn, collection, row, article
            )

            if status == "inserted":
                inserted += 1
            else:
                skipped += 1

            total_chunks += count

            print(
                f"[{index}/{min(args.limit, len(manifest))}] "
                f"{pmcid} | {status} | chunk: {count}"
            )

    finally:
        conn.close()

    print("\n--- SONUC ---")
    print("Yeni eklenen PDF:", inserted)
    print("Zaten senkron PDF:", skipped)
    print("Kontrol edilen chunk:", total_chunks)


if __name__ == "__main__":
    main()
