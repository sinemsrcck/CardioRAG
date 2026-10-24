
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
                answer, sources = answer_hybrid_v4(
                    question,
                    top_k=5,
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
