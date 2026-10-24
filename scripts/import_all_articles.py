
import csv
import getpass
import os
import time
from pathlib import Path

import mysql.connector

from scripts.fetch_article_metadata import fetch_pubmed_metadata

CSV_PATH = Path("data/pmcid_pmid_all.csv")
BATCH_SIZE = 100
REQUEST_DELAY = 0.5
MAX_RETRIES = 3


def main():
    email = os.environ.get("NCBI_EMAIL", "").strip()

    if not email or "@" not in email:
        raise SystemExit("NCBI_EMAIL ayarlanmamis.")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = [
            row for row in csv.DictReader(file)
            if row["status"] == "matched" and row["pmid"]
        ]

    # Ayni PMID birden fazla PDF'de varsa tek makale kaydi olustur.
    unique_rows = {row["pmid"]: row for row in rows}
    print("Benzersiz makale:", len(unique_rows))

    password = getpass.getpass("MySQL sifresi: ")

    connection = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password=password,
        database="cardiorag",
    )

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT pmid FROM makaleler")
        existing_pmids = {str(row[0]) for row in cursor.fetchall()}

        pending = [
            row for pmid, row in unique_rows.items()
            if pmid not in existing_pmids
        ]

        print("MySQL'de mevcut:", len(existing_pmids))
        print("Yeni eklenecek:", len(pending))

        for start in range(0, len(pending), BATCH_SIZE):
            batch = pending[start:start + BATCH_SIZE]
            pmids = [row["pmid"] for row in batch]

            batch_number = start // BATCH_SIZE + 1
            print(f"Grup {batch_number}: {len(batch)} makale")

            articles = None

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    articles = fetch_pubmed_metadata(pmids, email)
                    break
                except Exception as error:
                    print(f"API hatasi (deneme {attempt}): {error}")
                    if attempt < MAX_RETRIES:
                        time.sleep(2 * attempt)

            if articles is None:
                print("Grup atlandi; tekrar calistirilinca denenecek.")
                continue

            metadata_lookup = {
                article["pmid"]: article for article in articles
            }

            try:
                for row in batch:
                    pmid = row["pmid"]
                    metadata = metadata_lookup.get(pmid, {})

                    cursor.execute(
                        """
                        INSERT INTO makaleler (
                            pmid, pmcid, doi, baslik,
                            yazarlar, dergi, yil, abstract
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            pmcid = COALESCE(makaleler.pmcid, VALUES(pmcid)),
                            doi = COALESCE(makaleler.doi, VALUES(doi)),
                            baslik = COALESCE(makaleler.baslik, VALUES(baslik)),
                            yazarlar = COALESCE(makaleler.yazarlar, VALUES(yazarlar)),
                            dergi = COALESCE(makaleler.dergi, VALUES(dergi)),
                            yil = COALESCE(makaleler.yil, VALUES(yil)),
                            abstract = COALESCE(makaleler.abstract, VALUES(abstract))
                        """,
                        (
                            pmid,
                            row["pmcid"] or None,
                            row["doi"] or None,
                            metadata.get("baslik"),
                            metadata.get("yazarlar"),
                            metadata.get("dergi"),
                            metadata.get("yil"),
                            metadata.get("abstract"),
                        ),
                    )

                connection.commit()
                print(f"Grup {batch_number} kaydedildi.")

            except Exception:
                connection.rollback()
                raise

            time.sleep(REQUEST_DELAY)

        cursor.execute("SELECT COUNT(*) FROM makaleler")
        print("\nMySQL toplam makale:", cursor.fetchone()[0])

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
