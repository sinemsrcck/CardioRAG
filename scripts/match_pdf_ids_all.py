
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

PDF_FOLDER = Path("data/pdfs")
OUTPUT_FILE = Path("data/pmcid_pmid_all.csv")
EMAIL = os.environ.get("NCBI_EMAIL", "").strip()

BATCH_SIZE = 100
REQUEST_DELAY = 0.5
MAX_RETRIES = 3

if not EMAIL:
    raise SystemExit("NCBI_EMAIL ortam degiskeni ayarlanmamis.")


def get_pmcid(pdf):
    match = re.match(r"(PMC\d+)", pdf.stem, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def fetch_batch(pmcids):
    params = urllib.parse.urlencode({
        "ids": ",".join(pmcids),
        "format": "json",
        "tool": "CardioRAG",
        "email": EMAIL,
    })

    url = (
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        f"?{params}"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"CardioRAG/1.0 ({EMAIL})"}
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)

            return {
                record["pmcid"].upper(): record
                for record in data.get("records", [])
                if record.get("pmcid")
            }

        except Exception as error:
            print(f"API hatasi (deneme {attempt}): {error}")

            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)

    return None


def main():
    pdfs = sorted(PDF_FOLDER.rglob("*.pdf"))

    if not pdfs:
        raise SystemExit("PDF bulunamadi.")

    print("Toplam PDF:", len(pdfs))

    existing = {}

    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            for row in csv.DictReader(file):
                existing[row["filename"]] = row

    pmcids = sorted({
        get_pmcid(pdf)
        for pdf in pdfs
        if get_pmcid(pdf)
        and existing.get(pdf.name, {}).get("status") != "matched"
    })

    print("Sorgulanacak benzersiz PMCID:", len(pmcids))

    lookup = {}

    for start in range(0, len(pmcids), BATCH_SIZE):
        batch = pmcids[start:start + BATCH_SIZE]
        batch_number = start // BATCH_SIZE + 1

        print(f"API grubu {batch_number}: {len(batch)} PMCID")

        result = fetch_batch(batch)

        if result is not None:
            lookup.update(result)
        else:
            print("Grup basarisiz; sonraki calismada tekrar denenecek.")

        # Her gruptan sonra sonuclari kaydet.
        with OUTPUT_FILE.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["filename", "pmcid", "pmid", "doi", "status"]
            )
            writer.writeheader()

            for pdf in pdfs:
                pmcid = get_pmcid(pdf)
                old = existing.get(pdf.name, {})
                record = lookup.get(pmcid, {})

                pmid = record.get("pmid") or old.get("pmid", "")
                doi = record.get("doi") or old.get("doi", "")

                writer.writerow({
                    "filename": pdf.name,
                    "pmcid": pmcid,
                    "pmid": pmid,
                    "doi": doi,
                    "status": "matched" if pmid else "unmatched",
                })

        time.sleep(REQUEST_DELAY)

    print("\nEslesme tamamlandi.")
    print("CSV:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
