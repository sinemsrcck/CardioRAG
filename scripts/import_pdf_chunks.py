
import csv
import getpass
import hashlib
from pathlib import Path

import mysql.connector

from src.document_loader import load_pdf_pages
from src.chunking import split_pdf_pages

CSV_PATH = Path("data/pmcid_pmid_50.csv")
PDF_FOLDER = Path("data/pdfs")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def file_fingerprint(path):
    sha = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(block)

    return sha.hexdigest()


def main():
    password = getpass.getpass("MySQL root sifresi: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag"
    )

    cursor = connection.cursor()

    total_chunks = 0
    processed_pdfs = 0

    try:
        with CSV_PATH.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row["status"] != "matched" or not row["pmid"]:
                    continue

                pdf_path = (PDF_FOLDER / row["filename"]).resolve()

                if not pdf_path.is_file():
                    print("PDF bulunamadi:", pdf_path)
                    continue

                file_id = file_fingerprint(pdf_path)

                cursor.execute(
                    """
                    SELECT dokuman_id
                    FROM dokumanlar
                    WHERE dosya_hash = %s AND pmid = %s
                    """,
                    (file_id, row["pmid"])
                )

                result = cursor.fetchone()

                if not result:
                    print("MySQL PDF kaydi bulunamadi:", pdf_path.name)
                    continue

                dokuman_id = result[0]

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM chunklar
                    WHERE dokuman_id = %s
                    """,
                    (dokuman_id,)
                )

                existing_chunks = cursor.fetchone()[0]

                if existing_chunks > 0:
                    print(
                        f"Atlandi (zaten chunk var): {pdf_path.name} "
                        f"({existing_chunks} chunk)"
                    )
                    continue

                pages = load_pdf_pages(pdf_path)
                records = split_pdf_pages(pages)

                if not records:
                    print("Chunk olusturulamadi:", pdf_path.name)
                    continue

                # Her PDF icin ayri transaction.
                connection.commit()
                connection.start_transaction()

                try:
                    for chunk_sirasi, record in enumerate(records):
                        chroma_id = (
                            f"{file_id}_p{record['page']}"
                            f"_c{record['chunk_index']}"
                        )

                        cursor.execute(
                            """
                            INSERT INTO chunklar (
                                dokuman_id,
                                chunk_sirasi,
                                metin,
                                embedding_modeli,
                                sayfa_no,
                                sayfa_chunk_index,
                                chroma_id
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                metin = VALUES(metin),
                                embedding_modeli = VALUES(embedding_modeli),
                                sayfa_no = VALUES(sayfa_no),
                                sayfa_chunk_index = VALUES(sayfa_chunk_index),
                                chroma_id = VALUES(chroma_id)
                            """,
                            (
                                dokuman_id,
                                chunk_sirasi,
                                record["text"],
                                EMBEDDING_MODEL,
                                record["page"],
                                record["chunk_index"],
                                chroma_id
                            )
                        )

                    connection.commit()
                    processed_pdfs += 1
                    total_chunks += len(records)

                    print(
                        f"{pdf_path.name}: "
                        f"{len(records)} chunk kaydedildi."
                    )

                except Exception:
                    connection.rollback()
                    raise

        cursor.execute("SELECT COUNT(*) FROM chunklar")
        print("\nIslenen PDF:", processed_pdfs)
        print("Bu calismadaki chunk sayisi:", total_chunks)
        print("MySQL toplam chunk:", cursor.fetchone()[0])

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
