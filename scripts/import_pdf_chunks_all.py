
import getpass
import re

import mysql.connector

from src.core import v4_collection

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 500


def main():
    password = getpass.getpass("MySQL sifresi: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag",
    )

    cursor = connection.cursor()
    collection = v4_collection()

    try:
        cursor.execute(
            "SELECT dokuman_id, dosya_hash FROM dokumanlar"
        )

        document_lookup = {
            file_hash: document_id
            for document_id, file_hash in cursor.fetchall()
        }

        print("MySQL PDF kaydi:", len(document_lookup))

        # Mevcut chunk'lari chroma_id uzerinden tani.
        cursor.execute(
            "SELECT chroma_id FROM chunklar WHERE chroma_id IS NOT NULL"
        )
        existing_ids = {row[0] for row in cursor.fetchall()}

        # Her dokuman icin yeni chunk_sirasi degerini belirle.
        cursor.execute("""
            SELECT dokuman_id, COALESCE(MAX(chunk_sirasi), -1)
            FROM chunklar
            GROUP BY dokuman_id
        """)

        next_order = {
            doc_id: max_order + 1
            for doc_id, max_order in cursor.fetchall()
        }

        print("Mevcut MySQL chunk:", len(existing_ids))

        offset = 0
        inserted = 0
        skipped = 0
        missing_documents = set()

        while True:
            data = collection.get(
                limit=BATCH_SIZE,
                offset=offset,
                include=["documents", "metadatas"],
            )

            if not data["ids"]:
                break

            for chroma_id, text, metadata in zip(
                data["ids"],
                data["documents"],
                data["metadatas"],
            ):
                if chroma_id in existing_ids:
                    skipped += 1
                    continue

                file_id = metadata.get("file_id")
                document_id = document_lookup.get(file_id)

                if document_id is None:
                    missing_documents.add(file_id)
                    skipped += 1
                    continue

                match = re.search(r"_c(\d+)$", chroma_id)

                if not match:
                    skipped += 1
                    continue

                chunk_index = int(match.group(1))
                page = int(metadata.get("page", 0))

                chunk_order = next_order.get(document_id, 0)

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
                    """,
                    (
                        document_id,
                        chunk_order,
                        text,
                        EMBEDDING_MODEL,
                        page,
                        chunk_index,
                        chroma_id,
                    ),
                )

                next_order[document_id] = chunk_order + 1
                existing_ids.add(chroma_id)
                inserted += 1

            connection.commit()
            offset += len(data["ids"])

            print(
                f"Okunan: {offset} | "
                f"Yeni: {inserted} | "
                f"Atlanan: {skipped}"
            )

        cursor.execute("SELECT COUNT(*) FROM chunklar")
        mysql_count = cursor.fetchone()[0]

        print("\n--- SONUC ---")
        print("ChromaDB chunk:", collection.count())
        print("MySQL chunk:", mysql_count)
        print("Yeni eklenen:", inserted)
        print("Atlanan:", skipped)
        print("Eslesmeyen PDF kimligi:", len(missing_documents))

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
