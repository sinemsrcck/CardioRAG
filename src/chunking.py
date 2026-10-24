
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text_recursive(
    text,
    chunk_size=1500,
    chunk_overlap=250
):
    """
    Metni kontrollu sekilde parcalara ayirir.
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    return splitter.split_text(text)


def split_pdf_pages(pages):
    """
    PDF sayfalarini ayri ayri chunk'lara ayirir.
    Sayfa numaralarini korur.
    """
    records = []

    for page in pages:
        chunks = split_text_recursive(page.text)

        for chunk_index, chunk in enumerate(chunks):
            records.append({
                "page": page.page_number,
                "chunk_index": chunk_index,
                "text": chunk
            })

    return records
