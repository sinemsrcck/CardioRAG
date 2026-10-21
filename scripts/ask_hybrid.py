
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import answer_hybrid


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = input("Sorunuz: ").strip()

    if not question:
        print("Lütfen bir soru girin.")
        sys.exit(1)

    answer, sources = answer_hybrid(question)

    print("\n========== CEVAP ==========\n")
    print(answer)

    print("\n========== KAYNAKLAR ==========\n")

    for source in sources:
        print(
            f"[{source['number']}] "
            f"{source['filename']} | "
            f"Sayfa {source['page']} | "
            f"RRF: {source['rrf_score']:.5f} | "
            f"Rerank: {source['rerank_score']:.5f}"
        )
