
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from src.pdf_processing import remove_references


@dataclass
class PDFPage:
    page_number: int
    text: str


def find_pdf_files(folder, limit=0):
    folder = Path(folder).expanduser().resolve()

    if not folder.is_dir():
        raise ValueError(f"PDF klasoru bulunamadi: {folder}")

    pdfs = sorted(
        path for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if limit > 0:
        return pdfs[:limit]

    return pdfs


def load_pdf_pages(pdf_path):
    """
    PDF'yi okur ve kaynakca temizligini belge
    genelinde yaparak sayfa numaralarini korur.
    """
    pdf_path = Path(pdf_path).resolve()

    with fitz.open(str(pdf_path)) as doc:
        pages = [
            PDFPage(
                page_number=i + 1,
                text=page.get_text("text")
            )
            for i, page in enumerate(doc)
        ]

    if not pages:
        return []

    # Kaynakca temizligini tum belgeye uygula.
    full_text = "\n".join(page.text for page in pages)
    cleaned_text = remove_references(full_text)

    # Kaynakca bulunmadiysa tum sayfalari koru.
    if cleaned_text == full_text.strip():
        return [
            page for page in pages
            if page.text.strip()
        ]

    # Temizlenen metnin uzunlugundan kesme noktasini bul.
    cutoff = len(cleaned_text)

    filtered_pages = []
    position = 0

    for page in pages:
        page_start = position
        page_end = page_start + len(page.text)

        if cutoff <= page_start:
            break

        if cutoff >= page_end:
            text = page.text
        else:
            text = page.text[:cutoff - page_start]

        if text.strip():
            filtered_pages.append(
                PDFPage(
                    page_number=page.page_number,
                    text=text.strip()
                )
            )

        position = page_end + 1

    return filtered_pages
