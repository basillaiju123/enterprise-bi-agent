from qdrant_client.models import PointStruct

from src.rag.documents import build_knowledge_documents
from src.rag.embeddings import embed_texts
from src.rag.vector_store import (
    COLLECTION_NAME,
    create_collection,
    get_client,
)


def ingest_documents() -> None:
    create_collection()

    documents = build_knowledge_documents()
    texts = [document["text"] for document in documents]

    embeddings = embed_texts(texts)

    points = []

    for index, (document, embedding) in enumerate(
        zip(documents, embeddings)
    ):
        points.append(
            PointStruct(
                id=index,
                vector=embedding,
                payload={
                    "document_id": document["id"],
                    "type": document["type"],
                    "source": document["source"],
                    "text": document["text"],
                },
            )
        )

    client = get_client()

    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

        print(f"Ingested {len(points)} documents into Qdrant.")

    finally:
        client.close()


if __name__ == "__main__":
    ingest_documents()
