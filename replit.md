# mycoursor

## Overview
AI-powered code assistant with an IDE-like web interface. Indexes codebases using local TF-IDF embeddings, stores vectors in PostgreSQL + pgvector, and uses Gemini (via Replit AI Integrations) for AI chat. No API keys required.

## Project Architecture
```
mycoursor/
├── main.py              # CLI entry point (click-based)
├── config.py            # Settings via env vars
├── indexer/
│   ├── chunker.py       # File walking + line-based chunking
│   ├── embedder.py      # Local TF-IDF + SVD embeddings (scikit-learn)
│   └── store.py         # PostgreSQL + pgvector storage
├── retrieval/
│   └── search.py        # Semantic search via pgvector
├── agent/
│   ├── prompt.py        # System prompt + context building
│   ├── llm.py           # Gemini via Replit AI Integrations
│   └── parser.py        # Parse edit blocks from responses
├── editor/
│   └── apply.py         # Apply diffs to files
└── webapp/
    └── app.py           # FastAPI backend (API endpoints)

client/                  # React + Vite frontend
├── src/
│   ├── App.jsx          # Main app layout (IDE)
│   ├── styles.css       # Global styles (dark theme)
│   └── components/
│       ├── FileTree.jsx    # File explorer sidebar
│       ├── CodeViewer.jsx  # Syntax-highlighted code viewer
│       ├── ChatPanel.jsx   # AI chat with streaming
│       └── SearchPanel.jsx # Semantic search
└── vite.config.js       # Vite config (proxy /api → FastAPI:8000)
```

## Workflows
- **FastAPI Backend**: `uvicorn mycoursor.webapp.app:app` on port 8000
- **React Frontend**: `npm run dev` on port 5000 (proxies /api to backend)

## API Endpoints
- `GET /api/status` - System status and index info
- `GET /api/tree` - Project file tree
- `GET /api/file?path=...` - File content
- `PUT /api/file` - Save file changes (`{ path, content }`)
- `POST /api/index` - Re-index the project (background)
- `GET /api/index/status` - Check indexing progress
- `POST /api/search` - Semantic search (`{ query, top_k }`)
- `POST /api/chat` - AI chat with streaming SSE (`{ question, file_path }`)
- `POST /api/apply` - Apply AI-generated edit blocks (`{ file_path, original, updated }`)

## Environment
- `DATABASE_URL` - PostgreSQL (auto-provided by Replit)
- `AI_INTEGRATIONS_GEMINI_*` - Gemini access (auto-provided)
- No manual API keys needed

## User Preferences
- React for frontend
- FastAPI for backend
- Keep code simple and easy to understand
- Point-to-point functionality (no bloat)

## Recent Changes
- 2026-02-21: Added typewriter animation when applying AI code edits (green glow, blinking cursor, character-by-character reveal)
- 2026-02-21: Added AI-powered code editing (Apply button on edit blocks in chat)
- 2026-02-21: Added file editing in CodeViewer (Edit/Save/Cancel with Ctrl+S)
- 2026-02-21: Fixed vector dimension mismatch (fixed 64-dim embeddings)
- 2026-02-21: Fixed indexer to skip .cache and hidden directories
- 2026-02-21: Added background indexing with polling
- 2026-02-21: Added React + Vite frontend with IDE layout
- 2026-02-21: Switched backend from Flask to FastAPI
- 2026-02-20: Switched to local TF-IDF embeddings + Replit Gemini integration
- 2026-02-20: Initial build of all modules
