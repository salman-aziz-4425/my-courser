# mycoursor

## Overview
AI-powered CLI code assistant with semantic search. Indexes codebases using line-based chunking, local TF-IDF embeddings (scikit-learn), and PostgreSQL with pgvector for storage. Uses Gemini (via Replit AI Integrations) for code understanding and edit suggestions. No API keys required.

## Project Architecture
```
mycoursor/
├── main.py              # CLI entry point (click-based)
├── config.py            # Settings via env vars
├── indexer/
│   ├── chunker.py       # File walking + line-based chunking
│   ├── embedder.py      # Local TF-IDF + SVD embeddings (scikit-learn)
│   └── store.py         # PostgreSQL + pgvector operations
├── retrieval/
│   └── search.py        # Semantic search via pgvector
├── agent/
│   ├── prompt.py        # System prompt + context building
│   ├── llm.py           # Gemini via Replit AI Integrations (streaming)
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

## Environment
- `DATABASE_URL` - PostgreSQL connection (auto-provided by Replit)
- `AI_INTEGRATIONS_GEMINI_*` - Gemini access (auto-provided by Replit AI Integrations)
- No manual API keys needed

## Dependencies
- click, google-genai, psycopg2-binary, pgvector, scikit-learn, tree-sitter, pydantic

## Recent Changes
- 2026-02-20: Switched to local TF-IDF embeddings + Replit Gemini integration (no API keys)
- 2026-02-20: Switched from Voyage/Qdrant/Claude to Gemini/PostgreSQL
- 2026-02-20: Initial build of all modules
