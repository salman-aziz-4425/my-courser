import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    database_url: str = Field(default="")

    embedding_dim: int = Field(default=768)
    llm_model: str = Field(default="gemini-2.5-flash")

    chunk_max_bytes: int = Field(default=4000)
    search_top_k: int = Field(default=10)

    ignore_dirs: list[str] = Field(
        default_factory=lambda: [
            ".git", "__pycache__", "node_modules", ".venv",
            "venv", "dist", "build", ".mypy_cache", ".pytest_cache",
            ".tox", "egg-info", ".eggs", ".pythonlibs",
            ".cache", ".upm", ".config", ".local", "attached_assets",
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
            ".map",
        ]
    )


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", ""),
    )
