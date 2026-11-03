
import csv
import hashlib
import time
from datetime import datetime
from pathlib import Path

from src.core import v4_collection
from src.index_state import IndexState
from src.indexer_v4 import index_pdf_v4

AUDIT = Path("data/evaluation/new_pdfs_sha256_audit_v4.csv")
LOG_DIR = Path("logs")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    if not AUDIT.is_file():
        raise FileNotFoundError(AUDIT)

    with AUDIT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    selected = [r for r in rows if r["status"] == "new"]

    if len(selected) != 7307:
        raise RuntimeError(
            f"Beklenen 7307 PDF, bulunan {len(selected)}. "
            "Indeksleme baslatilmadi."
        )

    collection = v4_collection()
    state = IndexState()

    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / (
        f"index_manifest_v4_{datetime.now():%Y%m%d_%H%M%S}.csv"
    )

    counts = {"indexed": 0, "skipped": 0, "failed": 0}
    seen = set()

    print("Koleksiyon:", collection.name)
    print("Baslangic chunk:", collection.count())
    print("Secilen PDF:", len(selected))

    try:
        with log_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "result", "seconds", "detail"])

            for i, row in enumerate(selected, 1):
                path = Path(row["full_path"])
                expected = row["sha256"].lower().strip()
                start = time.perf_counter()
                detail = ""

                try:
                    if not path.is_file():
                        raise FileNotFoundError(path)

                    actual = sha256_file(path)

                    if actual != expected:
                        raise ValueError("SHA-256 degismis")

                    if actual in seen:
                        raise ValueError("Manifest icinde tekrar")

                    seen.add(actual)

                    # Eski kayitlari yeniden yazma.
                    existing = collection.get(
                        where={"file_id": actual},
                        include=[]
                    )["ids"]

                    if existing:
                        previous = state.get(actual)

                        if (
                            previous
                            and previous["status"] == "completed"
                            and len(existing) == previous["chunk_count"]
                        ):
                            result = "skipped"
                        else:
                            # Veri varsa ancak tutarsizsa otomatik silme.
                            raise RuntimeError(
                                "Mevcut chunk var fakat durum tutarsiz"
                            )
                    else:
                        result = index_pdf_v4(path, collection, state)

                except Exception as exc:
                    result = "failed"
                    detail = str(exc)

                counts[result] += 1

                elapsed = round(time.perf_counter() - start, 2)
                writer.writerow([str(path), result, elapsed, detail])
                f.flush()

                print(
                    f"[{i}/{len(selected)}] "
                    f"{result.upper()} | {path.name} | {elapsed} sn"
                )

    finally:
        state.close()

    print("\n--- SONUC ---")
    print(counts)
    print("Son chunk:", collection.count())
    print("Log:", log_path)


if __name__ == "__main__":
    main()
