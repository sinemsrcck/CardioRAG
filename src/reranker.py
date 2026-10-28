
from functools import lru_cache

from sentence_transformers import CrossEncoder


RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def get_reranker():
    print(f"Reranker modeli yükleniyor: {RERANK_MODEL}")
    return CrossEncoder(RERANK_MODEL)


def rerank(question, hits, top_k=5):
    """
    Hybrid Search sonucundaki parçaları
    Cross-Encoder ile yeniden sıralar.

    question: İngilizce arama sorgusu
    hits: RRF sonuçları
    """
    if not hits:
        return []

    model = get_reranker()

    pairs = [
        (question, hit["text"])
        for hit in hits
    ]

    scores = model.predict(pairs)

    ranked = []

    for hit, score in zip(hits, scores):
        item = hit.copy()
        item["rerank_score"] = float(score)
        ranked.append(item)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return ranked[:top_k]

def rerank_hybrid(question, hits, top_k=5, rrf_weight=0.35):
    """
    RRF sıralaması ile Cross-Encoder sıralamasını
    rank-based fusion kullanarak birleştirir.
    """

    if not hits:
        return []

    model = get_reranker()

    pairs = [(question, hit["text"]) for hit in hits]
    scores = model.predict(pairs)

    ranked = []

    for rrf_rank, (hit, score) in enumerate(zip(hits, scores), start=1):
        item = hit.copy()
        item["rerank_score"] = float(score)
        item["rrf_rank"] = rrf_rank
        ranked.append(item)

    # Cross-Encoder sıralaması
    ce_sorted = sorted(
        ranked,
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    for ce_rank, item in enumerate(ce_sorted, start=1):
        item["ce_rank"] = ce_rank

    # Sıralama temelli birleşik puan
    for item in ranked:
        item["combined_score"] = (
            rrf_weight / (60 + item["rrf_rank"])
            + (1 - rrf_weight) / (60 + item["ce_rank"])
        )

    ranked.sort(
        key=lambda x: x["combined_score"],
        reverse=True
    )

    return ranked[:top_k]
