import sys
import time
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import chromadb
from src.core import api_client, embed_batch, split_text

COLLECTION = 'cardiorag_abstract_txt_v1'
DEFAULT_FOLDER = r'C:\Users\SİNEM SARIÇİÇEK\Desktop\pubmed\txt için\makale_txtleri_FILTRE_SONUCLARI\01_UYGUN'


def get_store():
    db = chromadb.PersistentClient(path=str(ROOT / 'chroma_db'))
    return db.get_or_create_collection(name=COLLECTION, metadata={'hnsw:space': 'cosine'})


def parse_article(raw):
    header, separator, abstract = raw.partition('ABSTRACT:')
    if not separator or not abstract.strip():
        raise ValueError('ABSTRACT bolumu bulunamadi veya bos.')
    meta = {}
    keys = {'BASLIK': 'title', 'YIL': 'year', 'PMID': 'pmid', 'PMCID': 'pmcid', 'DOI': 'doi', 'PUBMED LINK': 'pubmed_url'}
    for line in header.splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        if k.strip() in keys:
            meta[keys[k.strip()]] = v.strip().lstrip('\ufeff\u200b')
    return meta, abstract.strip()


def index_txt(folder, limit=10):
    folder = Path(folder).expanduser()
    if not folder.is_dir():
        raise ValueError(f'Klasor bulunamadi: {folder}')
    paths = sorted(p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() == '.txt')
    if not paths:
        raise ValueError('TXT dosyasi bulunamadi.')
    selected = paths[:limit] if limit > 0 else paths
    client, store = api_client(), get_store()
    print(f'Toplam {len(paths)} TXT bulundu. Bu calismada {len(selected)} dosya kontrol edilecek.')
    ok = skipped = failed = 0
    for idx, path in enumerate(selected, 1):
        try:
            raw = path.read_text(encoding='utf-8-sig')
            meta, abstract = parse_article(raw)
            file_id = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]
            if store.get(where={'file_id': file_id}, limit=1)['ids']:
                skipped += 1
                print(f'[{idx}/{len(selected)}] Atlandi: {path.name}')
                continue
            chunks = split_text(abstract, size=1500, overlap=200)
            if not chunks:
                raise ValueError('Abstract bos.')
            ids = [f'{file_id}_{j}' for j in range(len(chunks))]
            metas = [{**meta, 'filename': path.name, 'file_id': file_id, 'chunk': j} for j in range(len(chunks))]
            # All embeddings first: no partially indexed file on an API failure.
            vectors = []
            for start in range(0, len(chunks), 20):
                batch = chunks[start:start + 20]
                vectors.extend(embed_batch(client, batch))
                time.sleep(1)
            if len(vectors) != len(chunks):
                raise ValueError('Embedding sayisi parca sayisiyla eslesmiyor.')
            store.upsert(ids=ids, documents=chunks, metadatas=metas, embeddings=vectors)
            ok += 1
            print(f'[{idx}/{len(selected)}] Indekslendi: {path.name} ({len(chunks)} parca)')
        except Exception as exc:
            failed += 1
            print(f'[{idx}/{len(selected)}] HATA: {path.name}: {exc}')
    print(f'Bitti. Yeni: {ok}, atlanan: {skipped}, hata: {failed}. Toplam TXT parcasi: {store.count()}')


if __name__ == '__main__':
    folder = input(f'TXT klasoru [{DEFAULT_FOLDER}]: ').strip().strip('"') or DEFAULT_FOLDER
    raw_limit = input('Kac TXT indekslensin? [10] (hepsi icin 0): ').strip()
    index_txt(folder, int(raw_limit) if raw_limit else 10)
