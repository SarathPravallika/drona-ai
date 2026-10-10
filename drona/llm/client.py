"""The only module that talks to an LLM provider. Everything else calls `complete()`."""

import time
from typing import Literal, TypeVar, overload

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

load_dotenv()  # GEMINI_API_KEY from .env (no-op if already set in the environment)

Tier = Literal["fast", "strong"]
Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": "..."}
T = TypeVar("T", bound=BaseModel)

# Pinned versions, not "-latest" aliases: an alias can change behaviour under us overnight.
# Free plan: no Pro models, so "strong" = a Flash model that thinks. Re-check availability when models retire.
MODELS: dict[Tier, str] = {
    "fast": "gemini-3.5-flash-lite",  # no thinking, ~3s: chat, short replies
    "strong": "gemini-3.6-flash",  # thinks, ~7s: grading, planning
}
TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 1.0
TRANSIENT_STATUS = {429, 500, 502, 503, 504}  # rate limit + server errors: worth one retry

_client: genai.Client | None = None


class LLMError(Exception):
    """The one error type callers handle, whatever provider is underneath."""


# Creates the Gemini client on first use, then reuses the same one
# Input: Nothing
# Output: A ready-to-use Gemini client (30-second timeout)
def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(http_options=types.HttpOptions(timeout=TIMEOUT_SECONDS * 1000))
    return _client


# Converts our provider-neutral messages into Gemini's format ("assistant" → "model")
# Input: Messages, e.g. [{"role": "user", "content": "Hi"}]
# Output: (System instruction text or None, list of Gemini messages)
def _to_gemini(messages: list[Message]) -> tuple[str | None, list[types.Content]]:
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system") or None
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
        if m["role"] != "system"
    ]
    return system, contents


# Decides whether an error is temporary (timeout, network, 429, 5xx), so one retry might succeed
# Input: The exception raised by the Gemini call
# Output: True if worth retrying, False otherwise
def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException | httpx.TransportError):
        return True
    return isinstance(exc, errors.APIError) and exc.code in TRANSIENT_STATUS


# Type hints only (no code runs here): tells the editor what complete() returns
# Input: Same as complete()
# Output: str without a schema; an instance of the schema class with one
@overload
def complete(messages: list[Message], schema: None = None, tier: Tier = "fast") -> str: ...
@overload
def complete(messages: list[Message], schema: type[T], tier: Tier = "fast") -> T: ...


# Sends a conversation to the LLM and returns its reply (retries once on a temporary error)
# Input: Messages, optional Pydantic schema class, tier ("fast" or "strong")
# Output: Reply text, or a validated schema object if a schema is given
def complete(messages: list[Message], schema: type[T] | None = None, tier: Tier = "fast") -> str | T:
    system, contents = _to_gemini(messages)
    config = types.GenerateContentConfig(system_instruction=system)
    if schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = schema

    for attempt in (1, 2):  # first try + one retry
        try:
            response = _get_client().models.generate_content(
                model=MODELS[tier], contents=contents, config=config
            )
            break
        except Exception as exc:
            if attempt == 1 and _is_transient(exc):
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise LLMError(f"{MODELS[tier]} call failed: {exc}") from exc

    text = response.text or ""
    if schema is None:
        return text
    try:
        return schema.model_validate_json(text)  # validate, don't trust
    except ValidationError as exc:
        raise LLMError(f"Response did not match {schema.__name__}: {exc}") from exc
