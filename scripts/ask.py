import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.core import CardioRAG
rag=CardioRAG()
print('CardioRAG hazır. Çıkmak için boş Enter.')
while True:
    q=input('\nSoru: ').strip()
    if not q: break
    answer,sources=rag.answer(q)
    print('\n'+answer+'\n')
    for i,s in enumerate(sources,1):
        m=s['metadata']
        print(f"[{i}] {m.get('title')} | {m.get('pubmed_url') or m.get('doi_url')}")
