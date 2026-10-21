
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
