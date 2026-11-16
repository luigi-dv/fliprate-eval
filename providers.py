"""One async entry point, `call(model_key, messages)`, for every provider.

Handles message normalisation, per-provider concurrency limits, retries with
backoff (honouring retry-after), and an on-disk cache so re-runs are free.
"""
import asyncio
import hashlib
import json
import random

import anthropic
import groq

from config import (CACHE_DIR, CONCURRENCY, MAX_RATE_LIMIT_WAITS, MAX_RETRY_AFTER_S,
                    MAX_TRIES, MODELS)

_clients = {}
_semaphores = {}

RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APIConnectionError,  # includes timeouts
    groq.RateLimitError,
    groq.InternalServerError,
    groq.APIConnectionError,
)


def _client(provider):
    # SDK retries are off: the loop in call() does the retrying.
    if provider not in _clients:
        if provider == "anthropic":
            _clients[provider] = anthropic.AsyncAnthropic(max_retries=0)
        elif provider == "groq":
            _clients[provider] = groq.AsyncGroq(max_retries=0)
        else:
            raise ValueError(f"unknown provider: {provider}")
    return _clients[provider]


def _semaphore(provider):
    if provider not in _semaphores:
        _semaphores[provider] = asyncio.Semaphore(CONCURRENCY[provider])
    return _semaphores[provider]


def _cache_path(model_key, messages):
    # The model spec is part of the key so that changing a model ID or a
    # sampling setting never reuses an old answer. The system prompt is the
    # first message, so the default/guard conditions get separate entries.
    payload = model_key + json.dumps(messages, sort_keys=True)
    payload += json.dumps(MODELS[model_key], sort_keys=True)
    return CACHE_DIR / (hashlib.sha256(payload.encode()).hexdigest() + ".json")


async def _call_anthropic(spec, messages):
    # Anthropic takes the system prompt as a separate argument.
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    chat = [m for m in messages if m["role"] != "system"]
    kwargs = dict(
        model=spec["id"],
        max_tokens=spec["max_tokens"],
        system=system,
        messages=chat,
        **spec["extra"],
    )
    if spec["temperature"] is not None:
        kwargs["temperature"] = spec["temperature"]
    response = await _client("anthropic").messages.create(**kwargs)
    if response.stop_reason == "refusal":
        return "", False
    text = "".join(b.text for b in response.content if b.type == "text")
    return text, response.stop_reason == "max_tokens"


async def _call_groq(spec, messages):
    # Groq uses the OpenAI chat format, which is what `messages` already is.
    kwargs = dict(
        model=spec["id"],
        max_completion_tokens=spec["max_tokens"],
        messages=messages,
        **spec["extra"],
    )
    if spec["temperature"] is not None:
        kwargs["temperature"] = spec["temperature"]
    response = await _client("groq").chat.completions.create(**kwargs)
    choice = response.choices[0]
    return choice.message.content or "", choice.finish_reason == "length"


def _retry_after(error):
    response = getattr(error, "response", None)
    try:
        return float(response.headers["retry-after"])
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


async def call(model_key: str, messages: list[dict]) -> tuple[str, bool]:
    """Return (reply text, truncated) for `messages` ([{"role", "content"}]).

    `truncated` is True when the API stopped the reply at the output-token limit.
    """
    messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    path = _cache_path(model_key, messages)
    if path.exists():
        record = json.loads(path.read_text())
        return record["response"], record["truncated"]

    spec = MODELS[model_key]
    provider = spec["provider"]
    fn = {"anthropic": _call_anthropic, "groq": _call_groq}[provider]

    failures = rate_limit_waits = 0
    while True:
        try:
            async with _semaphore(provider):
                text, truncated = await fn(spec, messages)
            break
        except RETRYABLE as error:
            retry_after = _retry_after(error)
            if retry_after and retry_after > MAX_RETRY_AFTER_S:
                raise  # daily quota: resume later
            if isinstance(error, (anthropic.RateLimitError, groq.RateLimitError)):
                # Per-minute limit: wait for the window without using up a try.
                rate_limit_waits += 1
                if rate_limit_waits > MAX_RATE_LIMIT_WAITS:
                    raise
                backoff = min(20, 2 ** min(rate_limit_waits, 5))
            else:
                failures += 1
                if failures >= MAX_TRIES:
                    raise
                backoff = min(60, 2**failures)
            await asyncio.sleep(max(retry_after or 0, backoff) + random.random())

    if text.strip():  # never cache an empty reply; a re-run will ask again
        CACHE_DIR.mkdir(exist_ok=True)
        record = {"model_key": model_key, "model_id": spec["id"],
                  "messages": messages, "response": text, "truncated": truncated}
        path.write_text(json.dumps(record, ensure_ascii=False, indent=1))
    return text, truncated
