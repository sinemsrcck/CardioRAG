
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import minilm_collection, v3_collection
from src.embeddings import embed_query


def test_retrieval(question, top_k=5):
    query_vector = embed_query(question)

    collections = {
        "V2 - Kaynakca filtresiz": minilm_collection(),
        "V3 - Kaynakca filtreli": v3_collection(),
    }

    for name, store in collections.items():
        print(f"\n{'=' * 65}")
        print(name)
        print(f"Toplam chunk: {store.count()}")
        print("=" * 65)

        if store.count() == 0:
            continue

        results = store.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, store.count()),
            include=["documents", "metadatas", "distances"],
        )

        for i, (text, meta, distance) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ),
            start=1,
        ):
            print(f"\n[{i}] {meta['filename']}")
            print(f"Sayfa: {meta['page']}")
            print(f"Cosine distance: {distance:.4f}")
            print(f"Metin: {text[:350]}...")


if __name__ == "__main__":
    question = (
        "Bu makalelerde kardiyovasküler hastalıklarla "
        "ilgili hangi bulgular raporlanmıştır?"
    )

    test_retrieval(question)
