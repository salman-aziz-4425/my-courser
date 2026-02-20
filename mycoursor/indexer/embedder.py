from google import genai
from google.genai import types

from mycoursor.config import Settings
from mycoursor.indexer.chunker import Chunk


BATCH_SIZE = 100


def _get_client(settings: Settings) -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def embed_texts(texts: list[str], settings: Settings) -> list[list[float]]:
    client = _get_client(settings)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = client.models.embed_content(
            model=settings.embedding_model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=settings.embedding_dim,
            ),
        )
        for emb in result.embeddings:
            all_embeddings.append(emb.values)

    return all_embeddings


def embed_query(query: str, settings: Settings) -> list[float]:
    client = _get_client(settings)
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=settings.embedding_dim,
        ),
    )
    return result.embeddings[0].values


def embed_chunks(chunks: list[Chunk], settings: Settings) -> list[list[float]]:
    texts = []
    for c in chunks:
        header = f"# {c.file_path} (lines {c.start_line}-{c.end_line})\n"
        texts.append(header + c.text)
    return embed_texts(texts, settings)
