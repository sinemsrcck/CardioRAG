
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

EVALUATION_DIR = BASE_DIR / "data" / "evaluation"
evaluation_files = sorted(
    EVALUATION_DIR.glob("rag_evaluation_*.csv"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

INPUT_CSV = evaluation_files[0] if evaluation_files else (
    EVALUATION_DIR / "rag_evaluation_v4.csv"
)
OUTPUT_CSV = EVALUATION_DIR / "relevance_pool_v4.csv"

RANKING_COLUMNS = {
    "semantic": "semantic_top10_articles",
    "bm25": "bm25_top10_articles",
    "rrf": "rrf_top10_articles",
    "reranked": "reranked_top10_articles",
}


def parse_articles(value):
    """Virgül veya | ile ayrılmış makale adlarını ayrıştırır."""
    if not value:
        return []

    separator = "|" if "|" in value else ","

    return [
        item.strip()
        for item in value.split(separator)
        if item.strip()
    ]


def build_pool():
    if not INPUT_CSV.exists():
        print(f"Değerlendirme dosyası henüz yok: {INPUT_CSV}")
        print("BM25 tamamlandıktan sonra değerlendirmeyi çalıştıracağız.")
        return

    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    pool = {}

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        required = {"id", *RANKING_COLUMNS.values()}
        missing = required - set(reader.fieldnames or [])

        if missing:
            raise ValueError(
                f"CSV'de eksik sütunlar: {sorted(missing)}"
            )

        for row in reader:
            question_id = row["id"].strip()

            for method, column in RANKING_COLUMNS.items():
                articles = parse_articles(row.get(column, ""))

                for rank, filename in enumerate(articles, start=1):
                    key = (question_id, filename)

                    if key not in pool:
                        pool[key] = {
                            "question_id": question_id,
                            "filename": filename,
                            "relevance": "",
                            "found_by": set(),
                            "best_rank": rank,
                        }

                    pool[key]["found_by"].add(method)
                    pool[key]["best_rank"] = min(
                        pool[key]["best_rank"], rank
                    )

    rows = sorted(
        pool.values(),
        key=lambda x: (
            x["question_id"],
            x["best_rank"],
            x["filename"]
        )
    )

    with OUTPUT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "question_id",
            "filename",
            "relevance",
            "found_by",
            "best_rank",
        ])

        for item in rows:
            writer.writerow([
                item["question_id"],
                item["filename"],
                item["relevance"],
                "|".join(sorted(item["found_by"])),
                item["best_rank"],
            ])

    print(f"Kullanilan degerlendirme dosyasi: {INPUT_CSV.name}")
    print(f"Aday makale sayısı: {len(rows)}")
    print(f"Dosya: {OUTPUT_CSV}")


if __name__ == "__main__":
    build_pool()
