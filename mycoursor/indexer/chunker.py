import os
from dataclasses import dataclass, field

from mycoursor.config import Settings


@dataclass
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    text: str
    language: str = ""


LANG_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "bash",
    ".bash": "bash",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".sql": "sql",
    ".r": "r",
    ".R": "r",
}

TEXT_EXTENSIONS: set[str] = set(LANG_EXTENSIONS.keys()) | {
    ".txt", ".cfg", ".ini", ".env", ".gitignore", ".dockerignore",
    ".makefile", ".cmake", ".proto", ".graphql", ".xml", ".csv",
    ".rst", ".tex", ".conf", ".properties",
}


def _detect_language(path: str) -> str:
    _, ext = os.path.splitext(path)
    return LANG_EXTENSIONS.get(ext, "")


def _is_text_file(path: str, settings: Settings) -> bool:
    _, ext = os.path.splitext(path)
    if ext.lower() in {e.lower() for e in settings.ignore_extensions}:
        return False
    if ext in TEXT_EXTENSIONS or ext == "":
        return True
    return False


def _walk_files(root: str, settings: Settings) -> list[str]:
    paths: list[str] = []
    ignore = set(settings.ignore_dirs)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore and not d.startswith(".")]
        for fname in filenames:
            if fname.startswith("."):
                continue
            full = os.path.join(dirpath, fname)
            if _is_text_file(full, settings):
                paths.append(full)
    return sorted(paths)


def _chunk_by_lines(text: str, file_path: str, language: str, max_bytes: int) -> list[Chunk]:
    lines = text.splitlines(keepends=True)
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_bytes = 0
    start = 1

    for i, line in enumerate(lines, start=1):
        line_bytes = len(line.encode("utf-8", errors="replace"))
        if buf and buf_bytes + line_bytes > max_bytes:
            chunks.append(Chunk(
                file_path=file_path,
                start_line=start,
                end_line=i - 1,
                text="".join(buf),
                language=language,
            ))
            buf = []
            buf_bytes = 0
            start = i
        buf.append(line)
        buf_bytes += line_bytes

    if buf:
        chunks.append(Chunk(
            file_path=file_path,
            start_line=start,
            end_line=start + len(buf) - 1,
            text="".join(buf),
            language=language,
        ))
    return chunks


def chunk_file(file_path: str, settings: Settings) -> list[Chunk]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    if not text.strip():
        return []

    language = _detect_language(file_path)
    return _chunk_by_lines(text, file_path, language, settings.chunk_max_bytes)


def chunk_repository(root: str, settings: Settings) -> list[Chunk]:
    files = _walk_files(root, settings)
    all_chunks: list[Chunk] = []
    for fpath in files:
        all_chunks.extend(chunk_file(fpath, settings))
    return all_chunks
