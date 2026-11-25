"""Configurable semantic relevance gate for warehouse-domain questions."""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MIN_SEMANTIC_SCORE = 0.302452
ENV_NAME = "RAG_MIN_SEMANTIC_SCORE"


def get_min_semantic_score() -> float:
    """Return the configured cosine-similarity cutoff, validated to [0, 1]."""
    raw_value = os.getenv(ENV_NAME)
    if raw_value is None or not raw_value.strip():
        return DEFAULT_MIN_SEMANTIC_SCORE

    try:
        threshold = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{ENV_NAME} must be a number between 0 and 1; got {raw_value!r}."
        ) from exc

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            f"{ENV_NAME} must be between 0 and 1; got {threshold}."
        )

    return threshold


def is_relevant_score(score: float, threshold: float | None = None) -> bool:
    """Classify a maximum semantic similarity score against the configured cutoff."""
    cutoff = get_min_semantic_score() if threshold is None else threshold
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("Relevance threshold must be between 0 and 1.")
    return float(score) >= cutoff
