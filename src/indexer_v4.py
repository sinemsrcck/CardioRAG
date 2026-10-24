
import hashlib
from pathlib import Path

from src.chunking import split_pdf_pages
from src.document_loader import load_pdf_pages
from src.embeddings import embed_texts
from src.index_state import IndexState


def file_fingerprint(path):
    """Dosyanin iceriginden SHA-256 kimligi uretir."""
    sha = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(block)

    return sha.hexdigest()


def index_pdf_v4(pdf_path, collection, state):
    path = Path(pdf_path).resolve()
    file_id = file_fingerprint(path)

    previous = state.get(file_id)

    if previous and previous["status"] == "completed":
        stored_count = len(
            collection.get(
                where={"file_id": file_id},
                include=[]
            )["ids"]
        )

        if stored_count == previous["chunk_count"]:
            print(f"Atlandi (tamamlanmis): {path.name}")
            return "skipped"

    state.set_status(file_id, path, "processing")

    try:
        # Onceki yarim kalmis kayitlari temizle.
        collection.delete(where={"file_id": file_id})

        pages = load_pdf_pages(path)
        records = split_pdf_pages(pages)

        if not records:
            raise ValueError("PDF'den indekslenebilir metin cikmadi.")

        total_chunks = 0

        for start in range(0, len(records), 40):
            batch = records[start:start + 40]

            vectors = embed_texts(
                [record["text"] for record in batch]
            )

            ids = [
                f"{file_id}_p{record['page']}_c{record['chunk_index']}"
                for record in batch
            ]

            metadatas = [
                {
                    "file_id": file_id,
                    "filename": path.name,
                    "path": str(path),
                    "page": record["page"]
                }
                for record in batch
            ]

            collection.upsert(
                ids=ids,
                documents=[record["text"] for record in batch],
                metadatas=metadatas,
                embeddings=vectors
            )

            total_chunks += len(batch)

        # Yalnizca tum batch'ler yazildiktan sonra tamamlandi.
        state.set_status(
            file_id,
            path,
            "completed",
            chunk_count=total_chunks
        )

        print(
            f"Indekslendi: {path.name} "
            f"({total_chunks} chunk)"
        )

        return "indexed"

    except Exception as exc:
        state.set_status(
            file_id,
            path,
            "failed",
            error_message=str(exc)
        )
        print(f"HATA: {path.name}: {exc}")
        return "failed"
