from mycoursor.retrieval.search import SearchResult

SYSTEM_PROMPT = """You are an expert software engineer assistant. You help developers understand and modify their codebase.

When the user asks you to make changes to code, respond with EDIT BLOCKS in the following format:

```edit
FILE: <file_path>
<<<<<<< ORIGINAL
<original code to replace>
=======
<new replacement code>
>>>>>>> UPDATED
```

Rules for edit blocks:
- The ORIGINAL section must match the existing code EXACTLY (including whitespace)
- You can include multiple edit blocks in a single response
- If creating a new file, leave the ORIGINAL section empty
- Always explain what changes you're making and why

When answering questions without edits, provide clear, concise explanations referencing specific files and line numbers from the context provided."""


def build_context(results: list[SearchResult]) -> str:
    if not results:
        return "No relevant code context found."

    parts: list[str] = []
    for r in results:
        header = f"--- {r.file_path} (lines {r.start_line}-{r.end_line}) [score: {r.score:.3f}] ---"
        parts.append(header)
        parts.append(r.text)
        parts.append("")
    return "\n".join(parts)


def build_prompt(question: str, results: list[SearchResult]) -> list[dict]:
    context = build_context(results)

    messages = [
        {
            "role": "user",
            "content": f"""Here is relevant code context from the repository:

{context}

---

User question: {question}""",
        }
    ]
    return messages
