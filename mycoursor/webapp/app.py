import os
import json

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from mycoursor.config import load_settings, Settings
from mycoursor.indexer.chunker import chunk_repository, _walk_files, _detect_language, LANG_EXTENSIONS
from mycoursor.indexer.embedder import embed_chunks
from mycoursor.indexer.store import upsert_chunks, collection_info, clear_table
from mycoursor.retrieval.search import search
from mycoursor.agent.prompt import SYSTEM_PROMPT, build_prompt
from mycoursor.agent.parser import parse_edit_blocks

from google import genai
from google.genai import types

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

AI_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.getcwd())


def _settings() -> Settings:
    return load_settings()


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    s = _settings()
    info = collection_info(s)
    return jsonify({
        "embedding": "local (scikit-learn TF-IDF)",
        "llm_model": s.llm_model,
        "database": "connected" if s.database_url else "not configured",
        "gemini": "configured" if AI_KEY else "not configured",
        "index": info,
        "project_root": PROJECT_ROOT,
    })


@app.route("/api/tree")
def api_tree():
    s = _settings()
    root = request.args.get("root", PROJECT_ROOT)
    ignore = set(s.ignore_dirs)
    tree = _build_tree(root, ignore, s)
    return jsonify(tree)


def _build_tree(root, ignore, settings):
    items = []
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return items

    for entry in entries:
        if entry.startswith(".") and entry not in (".env",):
            continue
        if entry in ignore:
            continue
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            children = _build_tree(full, ignore, settings)
            if children:
                items.append({
                    "name": entry,
                    "path": full,
                    "type": "directory",
                    "children": children,
                })
        else:
            _, ext = os.path.splitext(entry)
            if ext.lower() in {e.lower() for e in settings.ignore_extensions}:
                continue
            lang = LANG_EXTENSIONS.get(ext, "")
            items.append({
                "name": entry,
                "path": full,
                "type": "file",
                "language": lang,
            })
    return items


@app.route("/api/file")
def api_file():
    path = request.args.get("path", "")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    if not path.startswith(PROJECT_ROOT):
        return jsonify({"error": "Access denied"}), 403
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        _, ext = os.path.splitext(path)
        lang = LANG_EXTENSIONS.get(ext, "text")
        return jsonify({"path": path, "content": content, "language": lang})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/index", methods=["POST"])
def api_index():
    data = request.get_json(silent=True) or {}
    root = data.get("root", PROJECT_ROOT)
    s = _settings()
    try:
        clear_table(s)
        chunks = chunk_repository(root, s)
        if not chunks:
            return jsonify({"status": "ok", "chunks": 0, "message": "No files found to index."})
        vectors = embed_chunks(chunks, s)
        count = upsert_chunks(chunks, vectors, s)
        return jsonify({"status": "ok", "chunks": count, "message": f"Indexed {count} chunks."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    s = _settings()
    try:
        results = search(query, s, top_k=data.get("top_k", 10))
        return jsonify([{
            "file_path": r.file_path,
            "start_line": r.start_line,
            "end_line": r.end_line,
            "text": r.text,
            "language": r.language,
            "score": round(r.score, 4),
        } for r in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    s = _settings()
    results = search(question, s, top_k=s.search_top_k)
    messages = build_prompt(question, results)
    user_content = messages[0]["content"]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=8192,
    )

    def generate():
        client = genai.Client(
            api_key=AI_KEY,
            http_options={"api_version": "", "base_url": AI_URL},
        )
        try:
            for chunk in client.models.generate_content_stream(
                model=s.llm_model,
                contents=user_content,
                config=config,
            ):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
