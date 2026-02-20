import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from mycoursor.config import Settings
from mycoursor.indexer.chunker import Chunk


UPSERT_BATCH = 100


def get_client(settings: Settings) -> QdrantClient:
    if settings.qdrant_api_key:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(settings: Settings) -> None:
    client = get_client(settings)
    collections = [c.name for c in client.get_collections().collections]
    if settings.collection_name not in collections:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dim,
                distance=Distance.COSINE,
            ),
        )


def delete_collection(settings: Settings) -> None:
    client = get_client(settings)
    collections = [c.name for c in client.get_collections().collections]
    if settings.collection_name in collections:
        client.delete_collection(collection_name=settings.collection_name)


def upsert_chunks(
    chunks: list[Chunk],
    vectors: list[list[float]],
    settings: Settings,
) -> int:
    client = get_client(settings)
    ensure_collection(settings)

    points = []
    for chunk, vector in zip(chunks, vectors):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.text,
                "language": chunk.language,
            },
        )
        points.append(point)

    for i in range(0, len(points), UPSERT_BATCH):
        batch = points[i : i + UPSERT_BATCH]
        client.upsert(
            collection_name=settings.collection_name,
            points=batch,
        )

    return len(points)


def collection_info(settings: Settings) -> dict:
    client = get_client(settings)
    try:
        info = client.get_collection(settings.collection_name)
        return {
            "name": settings.collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": info.status.value if info.status else "unknown",
        }
    except Exception:
        return {"name": settings.collection_name, "status": "not_found"}
