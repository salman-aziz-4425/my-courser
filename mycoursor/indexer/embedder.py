import voyageai

from mycoursor.config import Settings
from mycoursor.indexer.chunker import Chunk


BATCH_SIZE = 64


def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    client = voyageai.Client(api_key=settings.voyage_api_key)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = client.embed(batch, model=settings.embedding_model, input_type="document")
        all_embeddings.extend(result.embeddings)

    return all_embeddings


def embed_query(query: str, settings: Settings) -> list[float]:
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed([query], model=settings.embedding_model, input_type="query")
    return result.embeddings[0]


def embed_chunks(chunks: list[Chunk], settings: Settings) -> list[list[float]]:
    texts = []
    for c in chunks:
        header = f"# {c.file_path} (lines {c.start_line}-{c.end_line})\n"
        texts.append(header + c.text)
    return embed_texts(texts, settings)
