from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core import index_pdfs

if __name__ == '__main__':
    folder = input('PDF klasorunun tam yolunu yapistirin: ').strip().strip('"')
    raw = input('Kac PDF indekslensin? [5] (hepsi icin 0): ').strip()
    index_pdfs(folder, int(raw) if raw else 5)
