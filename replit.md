# mycoursor

## Overview
AI-powered CLI code assistant with semantic search. Indexes codebases using tree-sitter chunking, Voyage AI embeddings, and Qdrant vector storage. Uses Claude for code understanding and edit suggestions.

## Project Architecture
```
mycoursor/
├── main.py              # CLI entry point (click-based)
├── config.py            # Settings via env vars
├── indexer/
│   ├── chunker.py       # File walking + line-based chunking
│   ├── embedder.py      # Voyage AI embeddings
│   └── store.py         # Qdrant vector operations
├── retrieval/
│   └── search.py        # Semantic search
├── agent/
│   ├── prompt.py        # System prompt + context building
│   ├── llm.py           # Claude API calls (streaming)
│   └── parser.py        # Parse edit blocks from responses
├── editor/
│   └── apply.py         # Apply diffs to files safely
└── __init__.py
```

## CLI Commands
- `python -m mycoursor.main index [PATH]` - Index a codebase
- `python -m mycoursor.main search "query"` - Semantic search
- `python -m mycoursor.main ask "question"` - Ask Claude about the code
- `python -m mycoursor.main apply response.txt` - Apply saved edits
- `python -m mycoursor.main status` - Show config and index status

## Required Environment Variables
- `VOYAGE_API_KEY` - Voyage AI API key for embeddings
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `QDRANT_URL` - Qdrant server URL (default: http://localhost:6333)
- `QDRANT_API_KEY` - Qdrant API key (optional for local)

## Dependencies
- click, anthropic, voyageai, qdrant-client, tree-sitter, pydantic

## Recent Changes
- 2026-02-20: Initial build of all modules
