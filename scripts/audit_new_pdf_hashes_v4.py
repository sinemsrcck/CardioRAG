
import csv
import hashlib
from collections import Counter
from pathlib import Path

from src.core import v4_collection


MANIFEST = Path("data/new_pdfs_manifest.csv")
OUTPUT = Path("data/evaluation/new_pdfs_sha256_audit_v4.csv")
BATCH_SIZE = 1000


def sha256_file(path):
    sha = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            sha.update(block)

    return sha.hexdigest()


def main():
    if not MANIFEST.is_file():
        raise FileNotFoundError(
            f"Manifest bulunamadi: {MANIFEST}"
        )

    with MANIFEST.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    required = {"pmcid", "filename", "full_path"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(
            "Manifest bos veya gerekli sutunlar eksik."
        )

    collection = v4_collection()
    total = collection.count()

    print("V4 koleksiyonu:", collection.name)
    print("Mevcut chunk:", total)
    print("Manifest PDF:", len(rows))

    # Mevcut V4 dosya kimliklerini oku.
    existing_ids = set()

    for offset in range(0, total, BATCH_SIZE):
        result = collection.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["metadatas"]
        )

        for metadata in result["metadatas"]:
            if metadata:
                file_id = metadata.get("file_id")
                if file_id:
                    existing_ids.add(file_id)

    print("V4 benzersiz file_id:", len(existing_ids))

    # Manifestteki dosyalari SHA-256 ile karsilastir.
    seen_hashes = set()
    results = []
    counts = Counter()

    for i, row in enumerate(rows, 1):
        path = Path(row["full_path"])

        file_hash = ""
        status = ""
        error = ""

        try:
            if not path.is_file():
                status = "missing_file"
            else:
                file_hash = sha256_file(path)

                if file_hash in seen_hashes:
                    status = "duplicate_within_manifest"
                elif file_hash in existing_ids:
                    status = "already_in_v4"
                else:
                    status = "new"

                seen_hashes.add(file_hash)

        except Exception as exc:
            status = "error"
            error = str(exc)

        counts[status] += 1

        results.append({
            "pmcid": row["pmcid"],
            "filename": row["filename"],
            "full_path": row["full_path"],
            "sha256": file_hash,
            "status": status,
            "error": error,
        })

        if i % 250 == 0 or i == len(rows):
            print(
                f"Kontrol edildi: {i}/{len(rows)}"
            )

    OUTPUT.parent.mkdir(
        parents=True, exist_ok=True
    )

    with OUTPUT.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "pmcid",
                "filename",
                "full_path",
                "sha256",
                "status",
                "error",
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n========== SHA-256 OZET ==========")
    print("Manifest toplam:", len(rows))

    for status in [
        "new",
        "already_in_v4",
        "duplicate_within_manifest",
        "missing_file",
        "error",
    ]:
        print(f"{status}: {counts[status]}")

    print("Rapor:", OUTPUT)

    if (
        counts["missing_file"] > 0
        or counts["error"] > 0
    ):
        print(
            "UYARI: Eksik veya hatali dosyalar var."
        )


if __name__ == "__main__":
    main()
