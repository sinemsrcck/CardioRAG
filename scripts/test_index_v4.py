
from pathlib import Path

from src.core import v4_collection
from src.document_loader import find_pdf_files
from src.index_state import IndexState
from src.indexer_v4 import index_pdf_v4


def main():
    pdf_folder = Path("data/pdfs")
    pdfs = find_pdf_files(pdf_folder, limit=1)

    if not pdfs:
        print(f"PDF bulunamadi: {pdf_folder}")
        return

    state = IndexState()

    try:
        result = index_pdf_v4(
            pdfs[0],
            v4_collection(),
            state
        )
        print("Sonuc:", result)
    finally:
        state.close()


if __name__ == "__main__":
    main()
