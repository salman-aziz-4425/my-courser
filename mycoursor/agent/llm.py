import anthropic

from mycoursor.config import Settings
from mycoursor.agent.prompt import SYSTEM_PROMPT, build_prompt
from mycoursor.retrieval.search import SearchResult


def ask(
    question: str,
    results: list[SearchResult],
    settings: Settings,
    stream: bool = True,
) -> str:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = build_prompt(question, results)

    if stream:
        return _stream_response(client, messages, settings)
    else:
        return _sync_response(client, messages, settings)


def _sync_response(
    client: anthropic.Anthropic,
    messages: list[dict],
    settings: Settings,
) -> str:
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def _stream_response(
    client: anthropic.Anthropic,
    messages: list[dict],
    settings: Settings,
) -> str:
    collected: list[str] = []
    with client.messages.stream(
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            collected.append(text)
    print()
    return "".join(collected)
