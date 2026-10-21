import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import index_pdfs_v3

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Kullanim: python scripts/build_v3_index.py "PDF_KLASORU"')
        sys.exit(1)

    index_pdfs_v3(sys.argv[1], limit=5)