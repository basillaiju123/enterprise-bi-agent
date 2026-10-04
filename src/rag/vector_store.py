from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


COLLECTION_NAME = "enterprise_knowledge"
VECTOR_SIZE = 384
QDRANT_PATH = "data/qdrant"


def get_client() -> QdrantClient:
    return QdrantClient(path=QDRANT_PATH)


def create_collection() -> None:
    client = get_client()

    try:
        existing_collections = [
            collection.name
            for collection in client.get_collections().collections
        ]

        if COLLECTION_NAME not in existing_collections:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
    finally:
        client.close()
