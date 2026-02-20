from dataclasses import dataclass

from mycoursor.config import Settings
from mycoursor.indexer.embedder import embed_query
from mycoursor.indexer.store import get_connection


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
    conn = get_connection(settings)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT file_path, start_line, end_line, text, language,
                       1 - (embedding <=> %s::vector) AS score
                FROM code_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (str(query_vector), str(query_vector), k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    results: list[SearchResult] = []
    for row in rows:
        results.append(SearchResult(
            file_path=row[0],
            start_line=row[1],
            end_line=row[2],
            text=row[3],
            language=row[4],
            score=row[5],
        ))
    return results
