
from src.core import v4_collection
from src.bm25_store import BM25Store


def main():
    collection = v4_collection()
    bm25 = BM25Store()

    batch_size = 500
    offset = 0
    total = 0

    try:
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
                records.append({
                    "id": chunk_id,
                    "file_id": meta["file_id"],
                    "filename": meta["filename"],
                    "page": meta["page"],
                    "text": text
                })

            bm25.add_chunks(records)

            total += len(records)
            offset += len(records)

            print(f"Aktarilan chunk: {total}")

        print("\n--- BM25 V4 ---")
        print("ChromaDB:", collection.count())
        print("SQLite FTS5:", bm25.count())

    finally:
        bm25.close()


if __name__ == "__main__":
    main()
