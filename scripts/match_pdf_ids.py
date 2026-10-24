
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

PDF_FOLDER = Path("data/pdfs")
OUTPUT_FILE = Path("data/pmcid_pmid_50.csv")
EMAIL = os.environ.get("NCBI_EMAIL", "")

pdfs = sorted(PDF_FOLDER.rglob("*.pdf"))[:50]

if not pdfs:
    raise SystemExit("PDF bulunamadi.")

if not EMAIL:
    raise SystemExit("NCBI_EMAIL ortam degiskenini ayarla.")

pmcids = []

for pdf in pdfs:
    match = re.match(r"(PMC\d+)", pdf.stem, re.IGNORECASE)
    if match:
        pmcids.append(match.group(1).upper())

params = urllib.parse.urlencode({
    "ids": ",".join(sorted(set(pmcids))),
    "format": "json",
    "tool": "CardioRAG",
    "email": EMAIL,
})

url = (
    "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    f"?{params}"
)
print("Sorgulanan PMCID:", pmcids)
print("NCBI URL:", url)
request = urllib.request.Request(
    url,
    headers={"User-Agent": f"CardioRAG/1.0 ({EMAIL})"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)

lookup = {
    record["pmcid"]: record
    for record in data.get("records", [])
    if record.get("pmcid")
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file)
    writer.writerow(["filename", "pmcid", "pmid", "doi", "status"])

    for pdf in pdfs:
        match = re.match(r"(PMC\d+)", pdf.stem, re.IGNORECASE)
        pmcid = match.group(1).upper() if match else ""
        record = lookup.get(pmcid, {})

        status = (
            "matched" if record.get("pmid")
            else "unmatched"
        )

        writer.writerow([
            pdf.name,
            pmcid,
            record.get("pmid", ""),
            record.get("doi", ""),
            status,
        ])

        print(pdf.name, "->", record.get("pmid", "BULUNAMADI"))

print("\nCSV kaydedildi:", OUTPUT_FILE)
