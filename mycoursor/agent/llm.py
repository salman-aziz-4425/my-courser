from google import genai
from google.genai import types

from mycoursor.config import Settings
from mycoursor.agent.prompt import SYSTEM_PROMPT, build_prompt
from mycoursor.retrieval.search import SearchResult


def ask(
    question: str,
    results: list[SearchResult],
    settings: Settings,
    stream: bool = True,
) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)
    messages = build_prompt(question, results)
    user_content = messages[0]["content"]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=settings.max_tokens,
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
