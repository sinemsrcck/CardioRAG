
import getpass

import mysql.connector

from src.core import v4_collection


def main():
    password = getpass.getpass("MySQL root sifresi: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag"
    )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT chroma_id, metin
            FROM chunklar
            ORDER BY chunk_id
        """)

        mysql_records = cursor.fetchall()
        cursor.close()

        collection = v4_collection()

        chroma_data = collection.get(
            include=["documents"]
        )

        chroma_records = dict(
            zip(
                chroma_data["ids"],
                chroma_data["documents"]
            )
        )

        missing = []
        different = []

        for chroma_id, text in mysql_records:
            if chroma_id not in chroma_records:
                missing.append(chroma_id)
            elif text != chroma_records[chroma_id]:
                different.append(chroma_id)

        mysql_ids = {row[0] for row in mysql_records}
        extra = set(chroma_records) - mysql_ids

        print("\n--- MYSQL / CHROMADB KONTROLU ---")
        print("MySQL chunk:", len(mysql_records))
        print("ChromaDB chunk:", len(chroma_records))
        print("ChromaDB'de eksik:", len(missing))
        print("Metni farkli:", len(different))
        print("MySQL'de eksik:", len(extra))

        if not missing and not different and not extra:
            print("\nSONUC: Tum chunklar birebir eslesiyor!")
        else:
            print("\nSONUC: Eslesme sorunlari bulundu.")
            print("Ornek eksik:", missing[:5])
            print("Ornek farkli:", different[:5])
            print("Ornek fazla:", list(extra)[:5])

    finally:
        connection.close()


if __name__ == "__main__":
    main()
