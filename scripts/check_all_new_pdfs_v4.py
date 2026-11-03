
import csv
from collections import Counter
from pathlib import Path

import fitz

MANIFEST = Path("data/new_pdfs_manifest.csv")
OUTPUT = Path("data/evaluation/all_new_pdf_check_v4.csv")

with MANIFEST.open(
    encoding="utf-8-sig", newline=""
) as f:
    files = list(csv.DictReader(f))

results = []
counts = Counter()

for index, row in enumerate(files, start=1):
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
                for page_num in range(min(3, pages)):
                    text_length += len(
                        doc[page_num].get_text("text").strip()
                    )

                if text_length < 100:
                    status = "LOW_TEXT"

    except Exception as exc:
        status = "ERROR"
        error = str(exc)

    counts[status] += 1

    results.append({
        "pmcid": row["pmcid"],
        "filename": row["filename"],
        "status": status,
        "pages": pages,
        "text_length_first_3_pages": text_length,
        "error": error,
    })

    if status != "OK":
        print(
            f"[{index}/{len(files)}] "
            f"{row['filename']} -> {status}"
        )

    if index % 500 == 0:
        print(f"Kontrol edildi: {index}/{len(files)}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print("\n========== SONUC ==========")
print("Toplam kontrol edilen:", len(results))

for status, count in sorted(counts.items()):
    print(f"{status}: {count}")

print("Rapor:", OUTPUT)
