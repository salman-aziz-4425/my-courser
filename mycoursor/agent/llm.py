import os

from google import genai
from google.genai import types

from mycoursor.config import Settings
from mycoursor.agent.prompt import SYSTEM_PROMPT, build_prompt
from mycoursor.retrieval.search import SearchResult

# Replit AI Integrations: Gemini access without requiring your own API key
AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")


def _get_client() -> genai.Client:
    return genai.Client(
        api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
        http_options={
            "api_version": "",
            "base_url": AI_INTEGRATIONS_GEMINI_BASE_URL,
        },
    )


def ask(
    question: str,
    results: list[SearchResult],
    settings: Settings,
    stream: bool = True,
) -> str:
    client = _get_client()
    messages = build_prompt(question, results)
    user_content = messages[0]["content"]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=8192,
    )

    if stream:
        return _stream_response(client, user_content, config, settings)
    else:
        return _sync_response(client, user_content, config, settings)


def _sync_response(
    client: genai.Client,
    content: str,
    config: types.GenerateContentConfig,
    settings: Settings,
) -> str:
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=content,
        config=config,
    )
    return response.text


def _stream_response(
    client: genai.Client,
    content: str,
    config: types.GenerateContentConfig,
    settings: Settings,
) -> str:
    collected: list[str] = []
    for chunk in client.models.generate_content_stream(
        model=settings.llm_model,
        contents=content,
        config=config,
    ):
        if chunk.text:
            print(chunk.text, end="", flush=True)
            collected.append(chunk.text)
    print()
    return "".join(collected)
