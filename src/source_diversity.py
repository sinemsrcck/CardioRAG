
from collections import defaultdict


def select_diverse_sources(
    hits,
    top_k=5,
    max_chunks_per_document=2
):
    """
    Rerank edilmis sonuclardan kaynak cesitliligi
    gozetilerek secim yapar.
    """

    selected = []
    document_counts = defaultdict(int)

    for hit in hits:
        metadata = hit.get("metadata") or {}

        # Mevcut V4 indeksinde chunk ID'si:
        # {file_id}_p{page}_c{chunk_index}
        chunk_id = hit.get("id", "")

        if "_p" in chunk_id:
            document_id = chunk_id.rsplit("_p", 1)[0]
        else:
            document_id = (
                metadata.get("path")
                or metadata.get("filename")
                or metadata.get("file_id")
                or chunk_id
            )

        if document_counts[document_id] >= max_chunks_per_document:
            continue

        selected.append(hit)
        document_counts[document_id] += 1

        if len(selected) >= top_k:
            break

    return selected
