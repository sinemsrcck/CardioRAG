
import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

from src.core import v4_collection
from src.document_loader import find_pdf_files
from src.index_state import IndexState
from src.indexer_v4 import index_pdf_v4


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--folder",
        required=True,
        help="PDF klasorunun yolu"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Islenecek maksimum PDF sayisi (0 = tumu)"
    )

    args = parser.parse_args()

    pdfs = find_pdf_files(args.folder, limit=args.limit)

    if not pdfs:
        print("PDF bulunamadi.")
        return

    collection = v4_collection()
    state = IndexState()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / (
        f"index_v4_{datetime.now():%Y%m%d_%H%M%S}.csv"
    )

    counts = {"indexed": 0, "skipped": 0, "failed": 0}
    start_time = time.perf_counter()

    try:
        with log_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["filename", "result", "duration_seconds"]
            )

            for i, pdf in enumerate(pdfs, 1):
                pdf_start = time.perf_counter()

                try:
                    result = index_pdf_v4(
                        pdf, collection, state
                    )
                except Exception as exc:
                    result = "failed"
                    print(f"Beklenmeyen hata: {pdf.name}: {exc}")

                duration = time.perf_counter() - pdf_start

                counts[result] += 1

                writer.writerow([
                    str(pdf),
                    result,
                    round(duration, 2)
                ])
                file.flush()

                print(
                    f"[{i}/{len(pdfs)}] "
                    f"{result.upper()} | "
                    f"{duration:.2f} sn"
                )

    finally:
        state.close()

    total_time = time.perf_counter() - start_time

    print("\n--- V4 INDEX OZETI ---")
    print("Yeni:", counts["indexed"])
    print("Atlanan:", counts["skipped"])
    print("Hata:", counts["failed"])
    print(f"Toplam sure: {total_time:.2f} sn")
    print("Log:", log_path)


if __name__ == "__main__":
    main()
