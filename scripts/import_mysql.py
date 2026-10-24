
import csv
import getpass
from pathlib import Path

import mysql.connector

CSV_PATH = Path("data/pmcid_pmid_50.csv")

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
    processed = 0
    skipped = 0

    with CSV_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["status"] != "matched" or not row["pmid"]:
                skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO makaleler (pmid, pmcid, doi)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    pmcid = VALUES(pmcid),
                    doi = VALUES(doi)
                """,
                (
                    row["pmid"],
                    row["pmcid"],
                    row["doi"] or None
                )
            )

            processed += 1

    connection.commit()

    print("Islenen makale:", processed)
    print("Atlanan:", skipped)

    cursor.execute("SELECT COUNT(*) FROM makaleler")
    print("MySQL toplam makale:", cursor.fetchone()[0])

except Exception:
    connection.rollback()
    raise

finally:
    cursor.close()
    connection.close()
