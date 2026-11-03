@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Gerekli paketler kuruluyor veya kontrol ediliyor...
py -m pip install pymupdf requests
if errorlevel 1 (
 echo Paket kurulumu basarisiz. Python kurulu mu kontrol edin.
 pause
 exit /b 1
)
echo.
echo PDF'lerden TXT dosyalari olusturuluyor...
py pubmed_pdf_to_txt.py
pause
