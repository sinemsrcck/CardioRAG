
from src.retrieval import translate_query, rrf_fusion
from src.retrieval_v4 import semantic_search_v4, bm25_search_v4
from src.reranker import rerank
from src.chunk_quality import is_reference_chunk

question = "Koroner arter hastalığında statinlerin etkisi nedir?"
query = translate_query(question)

semantic = semantic_search_v4(query, top_k=20)
bm25 = bm25_search_v4(query, top_k=20)

# Her iki yöntem de aynı RRF aday havuzundan beslenecek.
candidates = rrf_fusion(semantic, bm25, top_k=40)

# Mevcut yöntem
baseline = rerank(query, candidates[:20], top_k=5)

# Deneysel yöntem
filtered = [
    hit for hit in candidates
    if not is_reference_chunk(hit.get("text", ""))
]

filtered_top20 = filtered[:20]
experiment = rerank(query, filtered_top20, top_k=5)

print("\nToplam RRF adayi:", len(candidates))
print("Filtrelenen kaynakca:", len(candidates) - len(filtered))
print("Filtre sonrasi reranker adayi:", len(filtered_top20))

for name, hits in [
    ("MEVCUT", baseline),
    ("KAYNAKCA FILTRELI", experiment)
]:
    print(f"\n========== {name} ==========")

    for i, hit in enumerate(hits, 1):
        print(f"{i}. {hit['metadata'].get('filename')}")
        print("Skor:", round(hit["rerank_score"], 3))
        print("Metin:", hit["text"][:250].replace("\n", " "))
