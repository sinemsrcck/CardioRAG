
import csv
import random
from pathlib import Path

import fitz

MANIFEST = Path("data/new_pdfs_manifest.csv")
SAMPLE_SIZE = 30

with MANIFEST.open(
    "r", encoding="utf-8-sig", newline=""
) as f:
    rows = list(csv.DictReader(f))

random.seed(42)
sample = random.sample(
    rows, min(SAMPLE_SIZE, len(rows))
)

results = []

for row in sample:
    path = Path(row["full_path"])

    status = "OK"
    pages = 0
    text_length = 0
    error = ""

    try:
        with fitz.open(path) as doc:
            pages = len(doc)

            if doc.needs_pass:
                status = "ENCRYPTED"
            elif pages == 0:
                status = "EMPTY_PDF"
            else:
                # İlk üç sayfada metin çıkarma testi
                for page_num in range(min(3, pages)):
                    text_length += len(
                        doc[page_num].get_text("text").strip()
                    )

                if text_length < 100:
                    status = "LOW_TEXT"

    except Exception as exc:
        status = "ERROR"
        error = str(exc)

    results.append({
        "filename": row["filename"],
        "status": status,
        "pages": pages,
        "text_length_first_3_pages": text_length,
        "error": error,
    })

    print(
        row["filename"],
        "|", status,
        "| pages:", pages,
        "| text:", text_length
    )

output = Path("data/evaluation/new_pdf_check_v4.csv")
output.parent.mkdir(parents=True, exist_ok=True)

with output.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print("\n========== OZET ==========")

for status in sorted(set(r["status"] for r in results)):
    count = sum(r["status"] == status for r in results)
    print(status, ":", count)

print("Rapor:", output)
