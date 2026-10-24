
import sys

from src.answer_v4 import answer_hybrid_v4


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = input("Sorunuz: ").strip()

    if not question:
        print("Lutfen bir soru girin.")
        return

    answer, sources = answer_hybrid_v4(question)

    print("\n========== V4 CEVAP ==========\n")
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


if __name__ == "__main__":
    main()
