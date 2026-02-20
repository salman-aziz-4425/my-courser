import psycopg2
from pgvector.psycopg2 import register_vector

from mycoursor.config import Settings
from mycoursor.indexer.chunker import Chunk


def get_connection(settings: Settings):
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)
    return conn


def _create_table(settings: Settings, dim: int) -> None:
    conn = get_connection(settings)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("DROP TABLE IF EXISTS code_chunks;")
            cur.execute(f"""
                CREATE TABLE code_chunks (
                    id SERIAL PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    language TEXT DEFAULT '',
                    embedding vector({dim})
                );
            """)
        conn.commit()
    finally:
        conn.close()


def clear_table(settings: Settings) -> None:
    conn = get_connection(settings)
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS code_chunks;")
        conn.commit()
    finally:
        conn.close()


def upsert_chunks(
    chunks: list[Chunk],
    vectors: list[list[float]],
    settings: Settings,
) -> int:
    if not vectors:
        return 0

    dim = len(vectors[0])
    _create_table(settings, dim)

    conn = get_connection(settings)
    try:
        with conn.cursor() as cur:
            for chunk, vector in zip(chunks, vectors):
                cur.execute(
                    """
                    INSERT INTO code_chunks (file_path, start_line, end_line, text, language, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        chunk.file_path,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.text,
                        chunk.language,
                        str(vector),
                    ),
                )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM code_chunks;")
            count = cur.fetchone()[0]
            if count >= 100:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_code_chunks_embedding
                    ON code_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                conn.commit()

        return len(chunks)
    finally:
        conn.close()


def collection_info(settings: Settings) -> dict:
    conn = get_connection(settings)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'code_chunks');")
            exists = cur.fetchone()[0]
            if not exists:
                return {"table": "code_chunks", "status": "not_found"}
            cur.execute("SELECT COUNT(*) FROM code_chunks;")
            count = cur.fetchone()[0]
            return {
                "table": "code_chunks",
                "chunks_count": count,
                "status": "ready",
            }
    finally:
        conn.close()
