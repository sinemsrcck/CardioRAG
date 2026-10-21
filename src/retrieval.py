
import re

from rank_bm25 import BM25Okapi

from src.core import v3_collection
from src.embeddings import embed_query
from src.core import generation_client

def tokenize(text):
    return re.findall(r"\w+", text.lower())


def semantic_search(question, top_k=20):
    store = v3_collection()

    if store.count() == 0:
        return []

    results = store.query(
        query_embeddings=[embed_query(question)],
        n_results=min(top_k, store.count()),
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


def bm25_search(question, top_k=20):
    store = v3_collection()

    data = store.get(
        include=["documents", "metadatas"]
    )

    documents = data["documents"]
    if not documents:
        return []

    tokenized_docs = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)

    scores = bm25.get_scores(tokenize(question))

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )

    hits = []

    for idx in ranked_indices[:top_k]:
        if scores[idx] <= 0:
            continue

        hits.append({
            "id": data["ids"][idx],
            "text": documents[idx],
            "metadata": data["metadatas"][idx],
            "bm25_score": float(scores[idx]),
        })

    return hits


def rrf_fusion(semantic_hits, bm25_hits, k=60, top_k=10):
    scores = {}
    merged = {}

    for hits in (semantic_hits, bm25_hits):
        for rank, hit in enumerate(hits, start=1):
            chunk_id = hit["id"]

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + 1 / (k + rank)
            )

            if chunk_id not in merged:
                merged[chunk_id] = hit.copy()

    ranked_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )

    results = []

    for chunk_id in ranked_ids[:top_k]:
        hit = merged[chunk_id].copy()
        hit["rrf_score"] = scores[chunk_id]
        results.append(hit)

    return results



def hybrid_search(question, top_k=10):
    english_query = translate_query(question)

    print(f"Orijinal soru: {question}")
    print(f"İngilizce arama sorgusu: {english_query}")

    # MiniLM çok dilli olduğu için orijinal soruyla arıyoruz.
    semantic_hits = semantic_search(question, top_k=20)

    # BM25 İngilizce makaleler üzerinde İngilizce sorguyla arıyor.
    bm25_hits = bm25_search(english_query, top_k=20)

    return rrf_fusion(
        semantic_hits,
        bm25_hits,
        top_k=top_k,
    )



def translate_query(question):
    """Türkçe soruyu İngilizce tıbbi arama sorgusuna dönüştürür."""
    client, model = generation_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Convert the user's question into a concise English "
                    "biomedical literature search query. "
                    "Preserve medical terminology, diseases, biomarkers, "
                    "and abbreviations. "
                    "Return ONLY the English search query. "
                    "Do not answer the question."
                ),
            },
            {"role": "user", "content": question},
        ],
    )

    return (response.choices[0].message.content or "").strip()
