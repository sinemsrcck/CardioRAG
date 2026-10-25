
import csv
import time
from datetime import datetime
from pathlib import Path

from src.answer_v4 import answer_hybrid_v4

INPUT_PATH = Path("data/test_questions_v4.csv")
OUTPUT_DIR = Path("data/evaluation")

REJECTION_TEXT = (
    "yeterince ilgili kaynak bulunamadı"
)

def unique_article_ranking(hits):
    """
    Chunk siralamasini benzersiz makale siralamasina donusturur.
    Her makalenin ilk goruldugu sirayi korur.
    """
    articles = []
    seen = set()

    for hit in hits:
        metadata = hit.get("metadata") or {}
        filename = metadata.get("filename")

        if not filename or filename in seen:
            continue

        seen.add(filename)
        articles.append(filename)

    return articles

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Test dosyasi bulunamadi: {INPUT_PATH}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"rag_evaluation_{timestamp}.csv"

    with INPUT_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        questions = list(csv.DictReader(file))

    print("Toplam test sorusu:", len(questions))

    fieldnames = [
        "id",
        "category",
        "question",
        "expected_behavior",
        "response_time_seconds",
        "source_count",
        "unique_article_count",
        "sources_with_pmid",
        "sources_with_doi",
        "retrieved_pmids",
        "retrieved_dois",
        "retrieved_filenames",
        "semantic_top10_ids",
        "bm25_top10_ids",
        "rrf_top10_ids",
        "reranked_top10_ids",
        "semantic_top10_articles",
        "bm25_top10_articles",
        "rrf_top10_articles",
        "reranked_top10_articles",
        "rejected",
        "answer",
        "error",
    ]

    with output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(questions, start=1):
            question = row["question"]

            print(
                f"\n[{index}/{len(questions)}] "
                f"{question}"
            )

            start_time = time.perf_counter()

            try:
                answer, sources, debug = answer_hybrid_v4(
                    question,
                    top_k=5,
                    return_debug=True,
                )

                elapsed = time.perf_counter() - start_time

                unique_articles = {
                    source.get("pmid")
                    or source.get("filename")
                    for source in sources
                }

                rejected = (
                    REJECTION_TEXT in answer.lower()
                    and len(sources) == 0
                )

                result = {
                    "id": row.get("id", ""),
                    "category": row.get("category", ""),
                    "question": question,
                    "expected_behavior": row.get(
                        "expected_behavior", ""
                    ),
                    "response_time_seconds": round(elapsed, 2),
                    "source_count": len(sources),
                    "unique_article_count": len(unique_articles),
                    "sources_with_pmid": sum(
                        bool(source.get("pmid"))
                        for source in sources
                    ),
                    "sources_with_doi": sum(
                        bool(source.get("doi"))
                        for source in sources
                    ),

                    "semantic_top10_ids": "|".join(
                        str(hit.get("id", ""))
                        for hit in debug["semantic_hits"][:10]
                    ),
                    "semantic_top10_articles": "|".join(
                        unique_article_ranking(debug["semantic_hits"])[:10]
                    ),
                    "bm25_top10_articles": "|".join(
                        unique_article_ranking(debug["bm25_hits"])[:10]
                    ),
                    "rrf_top10_articles": "|".join(
                        unique_article_ranking(debug["hybrid_hits"])[:10]
                    ),
                    "reranked_top10_articles": "|".join(
                        unique_article_ranking(debug["reranked_hits"])[:10]
                    ),
                    "bm25_top10_ids": "|".join(
                        str(hit.get("id", ""))
                        for hit in debug["bm25_hits"][:10]
                    ),
                    "rrf_top10_ids": "|".join(
                        str(hit.get("id", ""))
                        for hit in debug["hybrid_hits"][:10]
                    ),
                    "reranked_top10_ids": "|".join(
                        str(hit.get("id", ""))
                        for hit in debug["reranked_hits"][:10]
                    ),

                    "retrieved_pmids": "|".join(
                    str(s.get("pmid"))
                    for s in sources
                    if s.get("pmid")
                    ),
                    "retrieved_dois": "|".join(
                        str(s.get("doi"))
                        for s in sources
                        if s.get("doi")
                    ),
                    "retrieved_filenames": "|".join(
                    str(s.get("filename"))
                    for s in sources
                    if s.get("filename")
                    ),
                    "rejected": rejected,
                    "answer": answer,
                    "error": "",
                }

                print(
                    f"Sure: {elapsed:.2f} sn | "
                    f"Kaynak: {len(sources)} | "
                    f"Red: {rejected}"
                )

            except Exception as exc:
                elapsed = time.perf_counter() - start_time

                result = {
                    "id": row.get("id", ""),
                    "category": row.get("category", ""),
                    "question": question,
                    "expected_behavior": row.get(
                        "expected_behavior", ""
                    ),
                    "response_time_seconds": round(elapsed, 2),
                    "source_count": 0,
                    "unique_article_count": 0,
                    "sources_with_pmid": 0,
                    "sources_with_doi": 0,
                    "retrieved_pmids": "",
                    "retrieved_dois": "",
                    "retrieved_filenames": "",
                    "semantic_top10_ids": "",
                    "semantic_top10_articles": "",
                    "bm25_top10_articles": "",
                    "rrf_top10_articles": "",
                    "reranked_top10_articles": "",
                    "bm25_top10_ids": "",
                    "rrf_top10_ids": "",
                    "reranked_top10_ids": "",
                    "rejected": False,
                    "answer": "",
                    "error": str(exc),
                }

                print("HATA:", exc)

            writer.writerow(result)
            file.flush()

    print("\nDegerlendirme tamamlandi.")
    print("Sonuc dosyasi:", output_path)


if __name__ == "__main__":
    main()
