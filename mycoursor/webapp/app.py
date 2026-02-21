import os
import json
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from mycoursor.config import load_settings
from mycoursor.indexer.chunker import chunk_repository, LANG_EXTENSIONS
from mycoursor.indexer.embedder import embed_chunks
from mycoursor.indexer.store import upsert_chunks, collection_info, clear_table
from mycoursor.retrieval.search import search
from mycoursor.agent.prompt import SYSTEM_PROMPT, build_prompt

from google import genai
from google.genai import types

app = FastAPI()

PROJECT_ROOT = os.path.realpath(os.getcwd())
AI_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:5000", f"http://0.0.0.0:5000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

index_state = {"running": False, "result": None}


def _safe_path(path: str) -> str:
    real = os.path.realpath(path)
    if not real.startswith(PROJECT_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")
    return real


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10

class ChatRequest(BaseModel):
    question: str


@app.get("/api/status")
def get_status():
    s = load_settings()
    return {
        "llm_model": s.llm_model,
        "database": "connected" if s.database_url else "not configured",
        "gemini": "configured" if AI_KEY else "not configured",
        "index": collection_info(s),
        "indexing": index_state["running"],
    }


@app.get("/api/tree")
def get_tree():
    s = load_settings()
    return build_tree(PROJECT_ROOT, set(s.ignore_dirs), s)


def build_tree(root, ignore, settings):
    items = []
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return items
    for entry in entries:
        if entry.startswith("."):
            continue
        if entry in ignore:
            continue
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            children = build_tree(full, ignore, settings)
            if children:
                items.append({"name": entry, "path": full, "type": "dir", "children": children})
        else:
            _, ext = os.path.splitext(entry)
            if ext.lower() in {e.lower() for e in settings.ignore_extensions}:
                continue
            items.append({"name": entry, "path": full, "type": "file", "lang": LANG_EXTENSIONS.get(ext, "")})
    return items


@app.get("/api/file")
def get_file(path: str):
    safe = _safe_path(path)
    if not os.path.isfile(safe):
        raise HTTPException(status_code=404, detail="File not found")
    with open(safe, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    _, ext = os.path.splitext(safe)
    return {"path": safe, "content": content, "lang": LANG_EXTENSIONS.get(ext, "")}


def _do_index():
    try:
        s = load_settings()
        clear_table(s)
        chunks = chunk_repository(PROJECT_ROOT, s)
        if not chunks:
            index_state["result"] = {"chunks": 0, "message": "No files found."}
            return
        vectors = embed_chunks(chunks, s)
        count = upsert_chunks(chunks, vectors, s)
        index_state["result"] = {"chunks": count, "message": f"Indexed {count} chunks."}
    except Exception as e:
        index_state["result"] = {"chunks": 0, "message": f"Error: {e}"}
    finally:
        index_state["running"] = False


@app.post("/api/index")
def run_index():
    if index_state["running"]:
        return {"message": "Indexing already in progress..."}
    index_state["running"] = True
    index_state["result"] = None
    thread = threading.Thread(target=_do_index, daemon=True)
    thread.start()
    return {"message": "Indexing started..."}


@app.get("/api/index/status")
def index_status():
    return {
        "running": index_state["running"],
        "result": index_state["result"],
    }


@app.post("/api/search")
def run_search(req: SearchRequest):
    s = load_settings()
    results = search(req.query, s, top_k=req.top_k)
    return [
        {
            "file_path": r.file_path,
            "start_line": r.start_line,
            "end_line": r.end_line,
            "text": r.text,
            "lang": r.language,
            "score": round(r.score, 4),
        }
        for r in results
    ]


@app.post("/api/chat")
def run_chat(req: ChatRequest):
    s = load_settings()
    results = search(req.question, s, top_k=s.search_top_k)
    messages = build_prompt(req.question, results)
    user_content = messages[0]["content"]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=8192,
    )

    def stream():
        client = genai.Client(
            api_key=AI_KEY,
            http_options={"api_version": "", "base_url": AI_URL},
        )
        try:
            for chunk in client.models.generate_content_stream(
                model=s.llm_model, contents=user_content, config=config,
            ):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
