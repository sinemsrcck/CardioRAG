
import os
from functools import lru_cache

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

EMBEDDING_BATCH_SIZE = int(
    os.getenv("EMBEDDING_BATCH_SIZE", "32")
)


@lru_cache(maxsize=1)
def get_embedding_model():
    print(f"Embedding modeli yükleniyor: {EMBEDDING_MODEL}")

    model = SentenceTransformer(EMBEDDING_MODEL)
    return model


def embed_texts(texts, batch_size=None):
    """
    Metinleri normalize edilmiş embedding vektörlerine dönüştürür.
    """
    if not texts:
        return []

    model = get_embedding_model()

    batch_size = batch_size or EMBEDDING_BATCH_SIZE

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    return embeddings.tolist()


def embed_query(question):
    """
    Tek bir sorgu için embedding üretir.
    """
    if not question or not question.strip():
        raise ValueError("Sorgu boş olamaz.")

    return embed_texts([question])[0]
