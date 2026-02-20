# mycoursor

## Overview
AI-powered CLI code assistant with semantic search. Indexes codebases using line-based chunking, Gemini embeddings, and PostgreSQL with pgvector for storage. Uses Gemini for code understanding and edit suggestions.

## Project Architecture
```
mycoursor/
├── main.py              # CLI entry point (click-based)
├── config.py            # Settings via env vars
├── indexer/
│   ├── chunker.py       # File walking + line-based chunking
│   ├── embedder.py      # Gemini embeddings (google-genai)
│   └── store.py         # PostgreSQL + pgvector operations
├── retrieval/
│   └── search.py        # Semantic search via pgvector
├── agent/
│   ├── prompt.py        # System prompt + context building
│   ├── llm.py           # Gemini API calls (streaming)
│   └── parser.py        # Parse edit blocks from responses
├── editor/
│   └── apply.py         # Apply diffs to files safely
└── __init__.py
```

## CLI Commands
- `python -m mycoursor.main index [PATH]` - Index a codebase
- `python -m mycoursor.main search "query"` - Semantic search
- `python -m mycoursor.main ask "question"` - Ask Gemini about the code
- `python -m mycoursor.main apply response.txt` - Apply saved edits
- `python -m mycoursor.main status` - Show config and index status

## Required Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (for embeddings + LLM)
- `DATABASE_URL` - PostgreSQL connection string (auto-provided by Replit)

## Dependencies
- click, google-genai, psycopg2-binary, pgvector, tree-sitter, pydantic

## Recent Changes
- 2026-02-20: Switched from Voyage/Qdrant/Claude to Gemini/PostgreSQL
- 2026-02-20: Initial build of all modules
