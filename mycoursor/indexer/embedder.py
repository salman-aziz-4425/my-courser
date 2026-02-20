import os
import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from mycoursor.config import Settings
from mycoursor.indexer.chunker import Chunk

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", ".embedder_model.pkl")
MODEL_PATH = os.path.normpath(MODEL_PATH)


class LocalEmbedder:
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            sublinear_tf=True,
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            ngram_range=(1, 2),
        )
        self.svd = TruncatedSVD(n_components=dim, random_state=42)
        self.fitted = False

    def fit(self, texts: list[str]) -> None:
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        actual_features = tfidf_matrix.shape[1]
        if actual_features < self.dim:
            self.svd = TruncatedSVD(n_components=actual_features, random_state=42)
        self.svd.fit(tfidf_matrix)
        self.fitted = True

    def transform(self, texts: list[str]) -> list[list[float]]:
        tfidf_matrix = self.vectorizer.transform(texts)
        reduced = self.svd.transform(tfidf_matrix)
        normalized = normalize(reduced, norm="l2")
        return normalized.tolist()

    def fit_transform(self, texts: list[str]) -> list[list[float]]:
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        actual_features = tfidf_matrix.shape[1]
        if actual_features < self.dim:
            self.svd = TruncatedSVD(n_components=actual_features, random_state=42)
        reduced = self.svd.fit_transform(tfidf_matrix)
        normalized = normalize(reduced, norm="l2")
        self.fitted = True
        return normalized.tolist()

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "svd": self.svd, "dim": self.dim}, f)

    @classmethod
    def load(cls, path: str) -> "LocalEmbedder":
        with open(path, "rb") as f:
            data = pickle.load(f)
        emb = cls(dim=data["dim"])
        emb.vectorizer = data["vectorizer"]
        emb.svd = data["svd"]
        emb.fitted = True
        return emb


_model_cache: LocalEmbedder | None = None


def _get_or_load_model(settings: Settings) -> LocalEmbedder | None:
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    if os.path.exists(MODEL_PATH):
        _model_cache = LocalEmbedder.load(MODEL_PATH)
        return _model_cache
    return None


def embed_chunks(chunks: list[Chunk], settings: Settings) -> list[list[float]]:
    global _model_cache
    texts = []
    for c in chunks:
        header = f"# {c.file_path} (lines {c.start_line}-{c.end_line})\n"
        texts.append(header + c.text)

    dim = min(settings.embedding_dim, len(texts) - 1) if len(texts) > 1 else 1
    model = LocalEmbedder(dim=dim)
    vectors = model.fit_transform(texts)
    model.save(MODEL_PATH)
    _model_cache = model
    return vectors


def embed_query(query: str, settings: Settings) -> list[float]:
    model = _get_or_load_model(settings)
    if model is None:
        raise RuntimeError("No embedding model found. Run 'index' first to build the model.")
    vectors = model.transform([query])
    return vectors[0]
