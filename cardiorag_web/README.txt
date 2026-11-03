CardioRAG V4 web arayuzu

1) app.py, templates/ klasoru ve requirements-web.txt dosyasini mevcut
   C:\CardioRAG\CardioRAG klasorune kopyalayin.
2) PowerShell'de proje klasorunde .venv etkinlestirilmisken:
   python -m pip install -r requirements-web.txt
3) .env dosyanizda MYSQL_PASSWORD ve mevcut RAG icin gerekli API
   ayarlarinin bulundugundan emin olun. Sifreleri HTML'e yazmayin.
4) python app.py
5) http://127.0.0.1:5000 adresini acin.

Mevcut src/answer_v4.py kullanilir. Sunucu internetten erisime acik degildir.
