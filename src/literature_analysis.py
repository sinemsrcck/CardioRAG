import re
from pathlib import Path


STUDY_TYPES = {
    "Meta-analysis": [
        r"\bmeta.analysis\b",
        r"\bmeta analysis\b",
    ],
    "Systematic review": [
        r"\bsystematic review\b",
    ],
    "Randomized controlled trial": [
        r"\brandomi[sz]ed controlled trial\b",
        r"\brandomi[sz]ed clinical trial\b",
    ],
    "Cohort study": [
        r"\bcohort study\b",
        r"\bcohort analysis\b",
    ],
    "Case-control study": [
        r"\bcase.control study\b",
    ],
    "Review": [
        r"\breview\b",
    ],
}


def detect_study_type(title):
    """Başlıktan çalışma türünü tahmin eder."""
    title = title or ""

    for study_type, patterns in STUDY_TYPES.items():
        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return study_type

    return "Unknown"


def analyze_literature(sources):
    """
    RAG kaynaklarını makale bazında birleştirir
    ve yayın yılına göre sıralar.
    """

    articles = {}

    for source in sources:
        pmid = source.get("pmid")
        doi = source.get("doi")
        filename = source.get("filename", "")

        article_key = pmid or doi or filename

        if not article_key:
            continue

        if article_key not in articles:
            articles[article_key] = {
                "title": source.get("title", "Unknown"),
                "year": source.get("year"),
                "pmid": pmid,
                "doi": doi,
                "filename": filename,
                "study_type": detect_study_type(
                    source.get("title", "")
                ),
                "pages": set(),
                "source_numbers": [],
            }

        articles[article_key]["pages"].add(
            source.get("page")
        )

        articles[article_key]["source_numbers"].append(
            source.get("number")
        )

    result = []

    for article in articles.values():
        article["pages"] = sorted(
            p for p in article["pages"] if p is not None
        )

        article["source_numbers"] = sorted(
            set(article["source_numbers"])
        )

        result.append(article)

    result.sort(
        key=lambda article: int(article["year"] or 0),
        reverse=True
    )

    return {
        "total_articles": len(result),
        "latest_year": result[0]["year"] if result else None,
        "articles": result
    }