
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import answer_minilm

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = input("Sorunuz: ").strip()

    if not question:
        print("Lutfen bir soru girin.")
        sys.exit(1)

    answer, sources = answer_minilm(question)

    print("\nCEVAP:\n")
    print(answer)

    print("\nKAYNAKLAR:\n")
    for source in sources:
        print(
            f'[{source["number"]}] '
            f'{source["filename"]} | '
            f'Sayfa {source["page"]} | '
            f'Cosine distance: {source["distance"]:.4f}'
        )
