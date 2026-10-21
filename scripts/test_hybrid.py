
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.retrieval import hybrid_search


question = (
    "Bu makalelerde kardiyovasküler hastalıklarla "
    "ilgili hangi bulgular raporlanmıştır?"
)

results = hybrid_search(question, top_k=10)

for i, hit in enumerate(results, start=1):
    meta = hit["metadata"]

    print(f"\n[{i}] {meta['filename']}")
    print(f"Sayfa: {meta['page']}")
    print(f"RRF Score: {hit['rrf_score']:.5f}")
    print(f"Metin: {hit['text'][:350]}...")
