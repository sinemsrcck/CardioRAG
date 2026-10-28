
from src.core import v4_collection
from src.bm25_store import BM25Store

def main():
    collection = v4_collection()
    bm25 = BM25Store()

    batch_size = 500
    offset = 0
    total = 0
    added = 0

    try:
        print("Mevcut BM25 kayitlari okunuyor...")
        existing_ids = bm25.existing_chunk_ids()
        print(f"Mevcut kayit: {len(existing_ids)}")

        while True:
            data = collection.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas"]
            )

            if not data["ids"]:
                break

            records = []

            for chunk_id, text, meta in zip(
                data["ids"],
                data["documents"],
                data["metadatas"]
            ):
                if chunk_id in existing_ids:
                    continue

                records.append({
                    "id": chunk_id,
                    "file_id": meta["file_id"],
                    "filename": meta["filename"],
                    "page": meta["page"],
                    "text": text
                })

            if records:
                bm25.add_chunks(records)
                added += len(records)

            total += len(data["ids"])
            offset += len(data["ids"])

            if total % 5000 == 0:
                print(
                    f"Kontrol edilen: {total} | "
                    f"Yeni eklenen: {added}"
                )

        print("\n--- BM25 V4 ---")
        print("ChromaDB:", collection.count())
        print("SQLite FTS5:", bm25.count())
        print("Yeni eklenen:", added)

    finally:
        bm25.close()
        
if __name__ == "__main__":
    main()