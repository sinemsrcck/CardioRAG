# CardioRAG

PubMed kardiyoloji makalelerinin metadata ve abstract alanlarını kalıcı ChromaDB indeksinde saklayan basit RAG prototipi. Osmanlıca Asistanı'ndaki chunking, RelayGPU embeddings ve QA yaklaşımından uyarlanmıştır.

## Kurulum (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:RELAY_API_KEY="YOUR_KEY"
$env:RELAY_BASE_URL="YOUR_ENDPOINT"
python scripts/build_index.py
python scripts/ask.py
```

TXT klasörü seçerken `01_UYGUN` klasörünün tam yolunu girin. Veriler `chroma_db` içine kaydedilir ve GitHub'a eklenmez.

## Veri biçimi

Her `.txt` içinde `BASLIK:`, `PMID:`, `DOI:`, `MESH TERIMLERI:` ve `ABSTRACT:` gibi alanlar bulunur. Sistem yalnızca abstract'ları indeksler, tam PDF metnini değil.

## Sınırlamalar

- Aynı PMID ile yeniden indeksleme aynı ID'leri günceller; ancak silinmiş/eski chunk'ları otomatik temizlemez.
- Yeniden çalıştırmada embedding istekleri tekrar yapılır. Sonraki sürümde hash bazlı atlama eklenebilir.
- RelayGPU üzerinde embedding ve chat modellerinin erişilebilir olması gerekir.
- Klinik karar verme sistemi değildir; yayınların lisanslarını kontrol edin.
