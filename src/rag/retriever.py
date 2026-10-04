from rank_bm25 import BM25Okapi

from src.rag.embeddings import embed_text
from src.rag.documents import build_knowledge_documents
from src.rag.vector_store import COLLECTION_NAME, get_client


DOCUMENTS = build_knowledge_documents()

TOKENIZED_DOCUMENTS = [
    document["text"].lower().split()
    for document in DOCUMENTS
]

BM25 = BM25Okapi(TOKENIZED_DOCUMENTS)

RRF_K = 60


def reciprocal_rank(rank: int) -> float:
    return 1.0 / (RRF_K + rank)


def retrieve_knowledge(
    question: str,
    top_k: int = 5,
) -> list[dict]:

    # -----------------------------
    # 1. Semantic ranking
    # -----------------------------
    query_vector = embed_text(question)

    client = get_client()

    try:
        semantic_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=len(DOCUMENTS),
            with_payload=True,
        ).points
    finally:
        client.close()

    semantic_rankings = {
        result.payload["document_id"]: rank
        for rank, result in enumerate(
            semantic_results,
            start=1,
        )
    }

    semantic_scores = {
        result.payload["document_id"]: result.score
        for result in semantic_results
    }

    # -----------------------------
    # 2. BM25 ranking
    # -----------------------------
    question_tokens = question.lower().split()

    bm25_scores = BM25.get_scores(question_tokens)

    lexical_rankings = sorted(
        range(len(DOCUMENTS)),
        key=lambda index: bm25_scores[index],
        reverse=True,
    )

    lexical_ranks = {
        DOCUMENTS[index]["id"]: rank
        for rank, index in enumerate(
            lexical_rankings,
            start=1,
        )
    }

    # -----------------------------
    # 3. Reciprocal Rank Fusion
    # -----------------------------
    candidates = []

    for document in DOCUMENTS:
        document_id = document["id"]

        semantic_rank = semantic_rankings.get(
            document_id,
            len(DOCUMENTS) + 1,
        )

        lexical_rank = lexical_ranks.get(
            document_id,
            len(DOCUMENTS) + 1,
        )

        rrf_score = (
            reciprocal_rank(semantic_rank)
            + reciprocal_rank(lexical_rank)
        )

        candidates.append(
            {
                "score": rrf_score,
                "semantic_score": semantic_scores.get(
                    document_id,
                    0.0,
                ),
                "semantic_rank": semantic_rank,
                "lexical_rank": lexical_rank,
                "type": document["type"],
                "source": document["source"],
                "text": document["text"],
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates[:top_k]
