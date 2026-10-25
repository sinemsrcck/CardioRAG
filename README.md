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

Örnek için:
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

**PDF makalelerini indeksleme

.\.venv\Scripts\python.exe scripts/build_index.py

PDF klasorunun tam yolunu yapistirin: C:\...\pdfler
Kac PDF indekslensin? [5] (hepsi icin 0): 5

İlk testte 4.456 PDF içinden 5 tanesi indekslenmiştir.

***RAG soru-cevap sistemini başlatma

.\.venv\Scripts\python.exe scripts/ask.py

Örnek soru 1:

İndekslenen makalelerde hangi kardiyovasküler hastalıklar ve tedavi yöntemleri incelenmiştir? Kaynaklarıyla açıkla.

Örnek soru 2:

İndekslenen makalelerde kalp yetmezliği ile ilgili hangi araştırma sonuçları raporlanmıştır? Yalnızca makalelerin kendi bulgularını kullan, kaynakça bölümlerini dikkate alma.

Örnek soru 3:

İndekslenen makalelerde hangi hasta grupları incelenmiştir ve temel araştırma bulguları nelerdir?


## Development Roadmap

See [TODO.md](TODO.md) for the current development progress, completed features, pending tasks, and planned experiments.