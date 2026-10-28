
import csv
from pathlib import Path

from src.retrieval import translate_query, rrf_fusion
from src.retrieval_v4 import semantic_search_v4, bm25_search_v4
from src.reranker import rerank, rerank_hybrid

TEST_IDS = {"1", "3", "6", "12", "15"}
OUTPUT = Path("data/evaluation/reranker_comparison_v4.csv")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open("data/test_questions_v4.csv", encoding="utf-8-sig", newline="") as f:
    questions = [
        row for row in csv.DictReader(f)
        if row["id"].strip() in TEST_IDS
    ]

results = []

for row in questions:
    question = row["question"]
    print(f"\nSORU {row['id']}: {question}")

    english = translate_query(question)
    semantic = semantic_search_v4(english, top_k=20)
    bm25 = bm25_search_v4(english, top_k=20)
    candidates = rrf_fusion(semantic, bm25, top_k=40)

    methods = {
        "cross_encoder": rerank(english, candidates, top_k=5),
        "hybrid": rerank_hybrid(english, candidates, top_k=5),
    }

    for method, hits in methods.items():
        print(f"\n  {method.upper()}")

        for rank, hit in enumerate(hits, 1):
            meta = hit.get("metadata") or {}
            filename = meta.get("filename", "")
            snippet = hit.get("text", "")[:350].replace("\n", " ")

            print(f"  {rank}. {filename}")
            print(f"     {snippet[:180]}")

            results.append({
                "question_id": row["id"],
                "question": question,
                "method": method,
                "rank": rank,
                "filename": filename,
                "chunk_id": hit.get("id", ""),
                "rerank_score": hit.get("rerank_score", ""),
                "combined_score": hit.get("combined_score", ""),
                "snippet": snippet,
            })

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question_id", "question", "method", "rank",
            "filename", "chunk_id", "rerank_score",
            "combined_score", "snippet"
        ])
        writer.writeheader()
        writer.writerows(results)

print(f"\nSonuclar kaydedildi: {OUTPUT}")
