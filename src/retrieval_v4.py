
from src.core import v4_collection
from src.embeddings import embed_query
from src.bm25_store import BM25Store
from src.retrieval import rrf_fusion, translate_query


def semantic_search_v4(question, top_k=20):
    store = v4_collection()

    count = store.count()
    if count == 0:
        return []

    results = store.query(
        query_embeddings=[embed_query(question)],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    hits = []

    for chunk_id, text, meta, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "id": chunk_id,
            "text": text,
            "metadata": meta,
            "distance": float(distance),
        })

    return hits


def bm25_search_v4(question, top_k=20):
    store = BM25Store()

    try:
        return store.search(question, top_k=top_k)
    finally:
        store.close()


def hybrid_search_v4(question, top_k=10):
    english_query = translate_query(question)

    print(f"Orijinal soru: {question}")
    print(f"Ingilizce arama sorgusu: {english_query}")

    semantic_hits = semantic_search_v4(question, top_k=20)
    bm25_hits = bm25_search_v4(english_query, top_k=20)

    return rrf_fusion(
        semantic_hits,
        bm25_hits,
        top_k=top_k,
    )
