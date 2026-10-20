import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.core import CardioRAG
if __name__=='__main__':
    folder=input('TXT klasör yolunu girin: ').strip().strip('"')
    if not Path(folder).is_dir(): raise SystemExit('Klasör bulunamadı.')
    CardioRAG().index_folder(folder)
