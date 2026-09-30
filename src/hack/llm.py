"""One interface over several LLM providers, so the provider is a .env choice.

    from hack import llm
    llm.ask("Summarise this complaint: ...")                  -> str
    llm.ask_json("Extract the amounts from ...", MySchema)    -> MySchema instance
    llm.chat([{"role": "user", "content": "hi"}], system=...) -> str

Providers (LLM_PROVIDER in .env):
- anthropic: Claude through Anthropic's API.
- vertex: Claude through Google Cloud (Vertex AI), billed to a Google Cloud project.
- gemini: Google's Gemini, with an AI Studio key or through a Google Cloud project.
- openai / azure: OpenAI directly or through Azure.
- mock: no key needed; text calls return a placeholder so the app still runs offline.
  `ask_json` raises in mock mode because there is nothing to parse.
"""

from functools import cache

from pydantic import BaseModel

from hack.config import env

Messages = list[dict[str, str]]

# Models that accept the server-side refusal fallback (a declined request is re-run on
# another Claude model instead of coming back empty). Anthropic's own API only.
_CLAUDE_FALLBACK_MODELS = ("claude-opus-5-5", "claude-opus-5", "claude-fable-5-1")


class LLMError(RuntimeError):
    pass


def provider() -> str:
    choice = env("LLM_PROVIDER", "auto").lower()
    if choice != "auto":
        return choice
    if env("ANTHROPIC_API_KEY"):
        return "anthropic"
    if env("AZURE_OPENAI_API_KEY"):
        return "azure"
    if env("OPENAI_API_KEY"):
        return "openai"
    if env("GEMINI_API_KEY"):
        return "gemini"
    return "mock"


def model_name() -> str:
    return {
        "anthropic": env("ANTHROPIC_MODEL", "claude-opus-5-5"),
        "vertex": env("ANTHROPIC_MODEL", "claude-opus-5-5"),
        "gemini": env("GEMINI_MODEL", "gemini-3.8-flash"),
        "openai": env("OPENAI_MODEL"),
        "azure": env("AZURE_OPENAI_DEPLOYMENT"),
    }.get(provider(), "mock")


def chat(messages: Messages, system: str = "") -> str:
    p = provider()
    if p == "mock":
        return f"[mock reply, no LLM key in .env] You said: {messages[-1]['content'][:200]}"
    if p in ("anthropic", "vertex"):
        resp = _claude().messages.create(messages=messages, **_claude_kwargs(system))
        _check_claude(resp)
        return "".join(b.text for b in resp.content if b.type == "text")
    if p == "gemini":
        resp = _gemini_generate(_gemini_contents(messages), _gemini_config(system))
        return resp.text or ""
    resp = _openai().chat.completions.create(
        model=model_name(), messages=_with_system(messages, system)
    )
    return resp.choices[0].message.content or ""


def ask(prompt: str, system: str = "") -> str:
    return chat([{"role": "user", "content": prompt}], system)


def ask_json[T: BaseModel](prompt: str, schema: type[T], system: str = "") -> T:
    p = provider()
    messages = [{"role": "user", "content": prompt}]
    if p == "mock":
        raise LLMError("ask_json needs a real LLM provider. Add a key to .env.")
    if p in ("anthropic", "vertex"):
        resp = _claude().messages.parse(
            messages=messages, output_format=schema, **_claude_kwargs(system)
        )
        _check_claude(resp)
        if resp.parsed_output is None:
            raise LLMError(f"Claude returned no readable JSON (stop_reason: {resp.stop_reason}).")
        return resp.parsed_output
    if p == "gemini":
        resp = _gemini_generate(
            _gemini_contents(messages),
            _gemini_config(system, response_mime_type="application/json", response_schema=schema),
        )
        if not isinstance(resp.parsed, schema):
            raise LLMError("Gemini returned no readable JSON.")
        return resp.parsed
    resp = _openai().chat.completions.parse(
        model=model_name(), messages=_with_system(messages, system), response_format=schema
    )
    msg = resp.choices[0].message
    if msg.refusal or msg.parsed is None:
        raise LLMError(f"Model refused or returned no JSON: {msg.refusal}")
    return msg.parsed


def reset() -> None:
    """Forget the SDK clients, so the next call picks up changed keys or provider in .env."""
    _claude.cache_clear()
    _gemini.cache_clear()
    _openai.cache_clear()


# --- provider plumbing -------------------------------------------------------------------


@cache
def _claude():
    import anthropic

    if provider() == "vertex":
        if not env("GOOGLE_CLOUD_PROJECT"):
            raise LLMError("Set GOOGLE_CLOUD_PROJECT in .env.")
        # Credentials come from `gcloud auth application-default login`
        return anthropic.AnthropicVertex(
            project_id=env("GOOGLE_CLOUD_PROJECT"),
            region=env("GOOGLE_CLOUD_LOCATION", "global"),
        )
    return anthropic.Anthropic()


@cache
def _gemini():
    from google import genai
    from google.genai import types

    # Retry busy (429) and overloaded (5xx) responses, which the free tier returns at peak
    # times. The Anthropic and OpenAI SDKs already retry these by default.
    retry = types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=4, http_status_codes=[429, 500, 502, 503, 504]
        )
    )
    if env("GEMINI_API_KEY"):
        return genai.Client(api_key=env("GEMINI_API_KEY"), http_options=retry)
    if not env("GOOGLE_CLOUD_PROJECT"):
        raise LLMError(
            "Set GEMINI_API_KEY, or GOOGLE_CLOUD_PROJECT to use Gemini via Google Cloud."
        )
    return genai.Client(
        vertexai=True,
        project=env("GOOGLE_CLOUD_PROJECT"),
        location=env("GOOGLE_CLOUD_LOCATION", "global"),
        http_options=retry,
    )


@cache
def _openai():
    import openai

    if provider() == "azure":
        if not model_name():
            raise LLMError("Set AZURE_OPENAI_DEPLOYMENT in .env.")
        return openai.AzureOpenAI(
            api_key=env("AZURE_OPENAI_API_KEY"),
            azure_endpoint=env("AZURE_OPENAI_ENDPOINT"),
            api_version=env("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
    if not model_name():
        raise LLMError("Set OPENAI_MODEL in .env.")
    return openai.OpenAI()


def _claude_kwargs(system: str) -> dict:
    model = model_name()
    kwargs = {
        "model": model,
        "max_tokens": 16000,
        "output_config": {"effort": env("ANTHROPIC_EFFORT", "medium")},
    }
    if system:
        kwargs["system"] = system
    if provider() == "anthropic" and model in _CLAUDE_FALLBACK_MODELS:
        kwargs["extra_headers"] = {"anthropic-beta": "server-side-fallback-2026-07-01"}
        kwargs["extra_body"] = {"fallbacks": "default"}
    return kwargs


def _check_claude(resp) -> None:
    if resp.stop_reason == "refusal":
        raise LLMError(f"Claude declined the request: {resp.stop_details}")


def _gemini_generate(contents: list[dict], config):
    """Call the main Gemini model; if it is still overloaded or over quota after the SDK's
    retries, send the same request to GEMINI_FALLBACK_MODEL (empty disables the fallback)."""
    from google.genai import errors

    main = model_name()
    fallback = env("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    try:
        return _gemini().models.generate_content(model=main, contents=contents, config=config)
    except errors.APIError as e:
        if e.code not in (429, 500, 502, 503, 504) or not fallback or fallback == main:
            raise
        return _gemini().models.generate_content(model=fallback, contents=contents, config=config)


def _gemini_contents(messages: Messages) -> list[dict]:
    # Gemini calls the assistant "model" and wraps text in parts
    return [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
    ]


def _gemini_config(system: str, **extra):
    from google.genai import types

    # Automatic function calling (Gemini running Python tools by itself) is unused here, and
    # leaving it on prints an SDK warning on every call
    return types.GenerateContentConfig(
        system_instruction=system or None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        **extra,
    )


def _with_system(messages: Messages, system: str) -> Messages:
    return [{"role": "system", "content": system}, *messages] if system else messages
