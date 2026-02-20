from dataclasses import dataclass

from qdrant_client.models import ScoredPoint

from mycoursor.config import Settings
from mycoursor.indexer.embedder import embed_query
from mycoursor.indexer.store import get_client


@dataclass
class SearchResult:
    file_path: str
    start_line: int
    end_line: int
    text: str
    language: str
    score: float


def search(query: str, settings: Settings, top_k: int | None = None) -> list[SearchResult]:
    k = top_k or settings.search_top_k
    query_vector = embed_query(query, settings)
    client = get_client(settings)

    hits: list[ScoredPoint] = client.query_points(
        collection_name=settings.collection_name,
        query=query_vector,
        limit=k,
        with_payload=True,
    ).points

    results: list[SearchResult] = []
    for hit in hits:
        payload = hit.payload or {}
        results.append(SearchResult(
            file_path=payload.get("file_path", ""),
            start_line=payload.get("start_line", 0),
            end_line=payload.get("end_line", 0),
            text=payload.get("text", ""),
            language=payload.get("language", ""),
            score=hit.score if hit.score else 0.0,
        ))
    return results
