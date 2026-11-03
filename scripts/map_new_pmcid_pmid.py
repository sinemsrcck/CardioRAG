
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

INPUT = Path("data/new_pdfs_manifest.csv")
OUTPUT = Path("data/pmcid_pmid_new.csv")

API = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi"  # Kullanilmiyor
IDCONV = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

BATCH_SIZE = 100
WAIT_SECONDS = 1.0
FIELDS = ["filename", "pmcid", "pmid", "doi", "status"]


def fetch_batch(pmcids):
    params = urllib.parse.urlencode({
        "ids": ",".join(pmcids),
        "format": "json",
        "tool": "CardioRAG"
    })

    request = urllib.request.Request(
        f"{IDCONV}?{params}",
        headers={"User-Agent": "CardioRAG/1.0"}
    )

    for attempt in range(5):
        try:
            with urllib.request.urlopen(
                request, timeout=60
            ) as response:
                return json.load(response)
        except Exception as exc:
            if attempt == 4:
                raise
            delay = 2 ** (attempt + 1)
            print(f"Baglanti hatasi: {exc}. {delay} sn bekleniyor.")
            time.sleep(delay)


def main():
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 7307:
        raise RuntimeError(
            f"Beklenen 7307 PDF, bulunan {len(rows)}"
        )

    completed = set()

    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("status") != "error":
                    completed.add(row["pmcid"])

    pending = [
        row for row in rows
        if row["pmcid"] not in completed
    ]

    print("Toplam:", len(rows))
    print("Tamamlanan:", len(completed))
    print("Bekleyen:", len(pending))

    # Mevcut dosyadaki error kayitlarini yeniden denemek icin
    # dosyayi once tekillestiriyoruz.
    existing = {}

    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                existing[row["pmcid"]] = row

    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        pmcids = [row["pmcid"] for row in batch]

        try:
            response = fetch_batch(pmcids)
            results = {
                r.get("requested-id", r.get("pmcid", "")): r
                for r in response.get("records", [])
            }

            for row in batch:
                pmcid = row["pmcid"]
                record = results.get(pmcid, {})

                pmid = record.get("pmid", "") or ""
                doi = record.get("doi", "") or ""

                status = (
                    "matched" if pmid
                    else "no_pmid" if record
                    else "not_found"
                )

                existing[pmcid] = {
                    "filename": row["filename"],
                    "pmcid": pmcid,
                    "pmid": pmid,
                    "doi": doi,
                    "status": status
                }

        except Exception as exc:
            print("BATCH HATASI:", exc)

            for row in batch:
                existing[row["pmcid"]] = {
                    "filename": row["filename"],
                    "pmcid": row["pmcid"],
                    "pmid": "",
                    "doi": "",
                    "status": "error"
                }

        # Her batch sonrasinda sonuclari kaydet.
        with OUTPUT.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(existing.values())

        print(
            f"Islenen: {min(start + BATCH_SIZE, len(pending))}"
            f"/{len(pending)}"
        )

        time.sleep(WAIT_SECONDS)

    print("\nTamamlandi:", OUTPUT)

    counts = {}
    for row in existing.values():
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1

    print("Sonuclar:", counts)


if __name__ == "__main__":
    main()
