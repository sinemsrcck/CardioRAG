# CardioRAG - Temiz Demo

Bu proje PDF makalelerin metnini sayfa bazinda parcalar, Relay uyumlu embedding API ile vektor haline getirir, ChromaDB'de kalici olarak tutar ve sorulara ilgili kaynaklarla yanit verir.

## Kurulum (Windows PowerShell)

1. Bu ZIP'i **yeni, bos bir klasore** cikartin. Onceki paketlerle birlestirmeyin.
2. `.env.example` dosyasini `.env` olarak kopyalayin: `Copy-Item .env.example .env`
3. `.env` icine RELAY_API_KEY ve RELAY_BASE_URL degerlerini girin. API anahtarini GitHub'a yuklemeyin.
4. Mevcut venv'i kullanacaksaniz `.venv` klasorunu yeni proje klasorune tasiyabilirsiniz; ancak Python ortamlarinin konuma bagli olabileceginden **yeniden olusturmak daha guvenlidir**:
   - `py -m venv .venv`
   - `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
5. ` .\.venv\Scripts\python.exe scripts/build_index.py ` komutunu calistirin. PDF klasorunu ve 5 sayisini girin.
6. ` .\.venv\Scripts\python.exe scripts/ask.py ` komutunu calistirin ve sorular sorun.

## Notlar
- PDF dosyalari GitHub'a yuklenmez; sadece yerel dosyalardan okunur.
- Indeks `chroma_db` klasorunde kalici tutulur. Aynı PDF degismediyse yeniden indekslenmez.
- Tarama goruntusu olan PDF'ler OCR olmadan okunamaz. Tablolarda bilgi kaybi olabilir.
- Ilac dozlari ancak makale metninde bulunuyorsa ve calisma baglaminda aktarilir; klinik tavsiye degildir.
- API'nin secilen model adlarini desteklemesi gerekir; gerekirse `.env` icinde CHAT_MODEL/EMBED_MODEL degistirilir.
- Degistirilen PDF eski vektorleri otomatik silmez; demo surumunde veritabani temizligi gerekebilir.
