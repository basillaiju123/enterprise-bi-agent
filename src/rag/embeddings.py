from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Generate an embedding for a single text string."""
    return _model.encode(
        text,
        normalize_embeddings=True,
    ).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple text strings."""
    return _model.encode(
        texts,
        normalize_embeddings=True,
    ).tolist()
