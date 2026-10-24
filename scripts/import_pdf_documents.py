
import csv
import getpass
import hashlib
from pathlib import Path

import mysql.connector

PDF_FOLDER = Path("data/pdfs")
CSV_PATH = Path("data/pmcid_pmid_all.csv")


def sha256_file(path):
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

    try:
        inserted = 0
        skipped = 0

        with CSV_PATH.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                if row["status"] != "matched" or not row["pmid"]:
                    skipped += 1
                    continue

                pdf_path = (
                    PDF_FOLDER / row["filename"]
                ).resolve()

                if not pdf_path.is_file():
                    print("PDF bulunamadi:", pdf_path)
                    skipped += 1
                    continue

                file_hash = sha256_file(pdf_path)

                cursor.execute(
                    """
                    INSERT INTO dokumanlar
                        (pmid, dosya_turu, dosya_yolu, dosya_hash)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        dokuman_id = dokuman_id
                    """,
                    (
                        row["pmid"],
                        "pdf",
                        str(pdf_path),
                        file_hash
                    )
                )

                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1

        connection.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM dokumanlar"
        )

        print("Yeni PDF kaydi:", inserted)
        print("Atlanan:", skipped)
        print("MySQL toplam PDF:", cursor.fetchone()[0])

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
