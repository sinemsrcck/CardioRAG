
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.retrieval import (
    translate_query,
    semantic_search,
    bm25_search,
    rrf_fusion,
)
from src.reranker import rerank


question = (
    "Bu makalelerde kardiyovasküler hastalıklarla "
    "ilgili hangi bulgular raporlanmıştır?"
)

# 1. Türkçe sorudan İngilizce arama sorgusu oluştur
english_query = translate_query(question)

print(f"\nOrijinal soru: {question}")
print(f"İngilizce sorgu: {english_query}")

# 2. MiniLM ve BM25 aramalarını gerçekleştir
semantic_hits = semantic_search(question, top_k=20)
bm25_hits = bm25_search(english_query, top_k=20)

# 3. RRF ile sonuçları birleştir
hybrid_hits = rrf_fusion(
    semantic_hits,
    bm25_hits,
    top_k=20,
)

print("\n========== RRF İLK 5 ==========")

for i, hit in enumerate(hybrid_hits[:5], start=1):
    meta = hit["metadata"]
    print(
        f"[{i}] {meta['filename']} | "
        f"Sayfa {meta['page']} | "
        f"RRF: {hit['rrf_score']:.5f}"
    )

# 4. Cross-Encoder ile yeniden sırala
reranked_hits = rerank(
    english_query,
    hybrid_hits,
    top_k=5,
)

print("\n========== CROSS-ENCODER İLK 5 ==========")

for i, hit in enumerate(reranked_hits, start=1):
    meta = hit["metadata"]

    print(f"\n[{i}] {meta['filename']}")
    print(f"Sayfa: {meta['page']}")
    print(f"RRF Score: {hit['rrf_score']:.5f}")
    print(f"Rerank Score: {hit['rerank_score']:.5f}")
    print(f"Metin: {hit['text'][:400]}...")
