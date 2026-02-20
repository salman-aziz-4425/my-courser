import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    anthropic_api_key: str = Field(default="")
    voyage_api_key: str = Field(default="")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")

    collection_name: str = Field(default="mycoursor")
    embedding_model: str = Field(default="voyage-code-3")
    embedding_dim: int = Field(default=1024)
    llm_model: str = Field(default="claude-sonnet-4-20250514")
    max_tokens: int = Field(default=4096)

    chunk_max_bytes: int = Field(default=4000)
    search_top_k: int = Field(default=10)

    ignore_dirs: list[str] = Field(
        default_factory=lambda: [
            ".git", "__pycache__", "node_modules", ".venv",
            "venv", "dist", "build", ".mypy_cache", ".pytest_cache",
            ".tox", "egg-info", ".eggs",
        ]
    )
    ignore_extensions: list[str] = Field(
        default_factory=lambda: [
            ".pyc", ".pyo", ".so", ".o", ".a", ".dylib",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
            ".mp3", ".mp4", ".wav", ".avi", ".mov",
            ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".exe", ".dll", ".bin", ".dat",
            ".lock", ".woff", ".woff2", ".ttf", ".eot",
        ]
    )


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        voyage_api_key=os.environ.get("VOYAGE_API_KEY", ""),
        qdrant_url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        qdrant_api_key=os.environ.get("QDRANT_API_KEY", ""),
        collection_name=os.environ.get("QDRANT_COLLECTION", "mycoursor"),
    )
