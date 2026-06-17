"""Shared transient-error retry helpers for LLM providers.

Backend overloads (HTTP 529), rate limits (429), gateway/unavailable errors (5xx) and
dropped connections are transient — they almost always clear within seconds. Without a
retry, a momentary z.ai/GLM (or Anthropic/OpenAI) overload crashes the whole turn with a
raw stack trace. These helpers give every provider a uniform backoff-and-retry policy and
let the REPL recognize a transient failure so it can show a clean message instead.

Tunables (env):
    KIBA_MAX_RETRIES   max retry attempts after the first try (default 6)
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Callable, Optional

# Retryable HTTP statuses: timeout, conflict, rate limit, and the 5xx/overload family.
_TRANSIENT_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}

# Retryable exception class names — matched by name so we don't have to import every SDK's
# exception hierarchy (anthropic + openai expose the same shapes).
_TRANSIENT_NAMES = {
    "OverloadedError", "RateLimitError", "InternalServerError", "APITimeoutError",
    "APIConnectionError", "APIConnectionTimeoutError", "ServiceUnavailableError",
    "APIStatusError",  # only treated transient when its status_code is in _TRANSIENT_STATUS
}

def _int_env(name: str, default: int) -> int:
    """Parse an int env var, falling back to default on missing/blank/garbage input
    (a bad value must never crash the CLI at import time)."""
    try:
        return int(os.environ.get(name) or default)
    except (TypeError, ValueError):
        return default


MAX_RETRIES = _int_env("KIBA_MAX_RETRIES", 6)


def is_transient_error(exc: BaseException) -> bool:
    """True if `exc` is a transient API failure worth retrying (overload/rate-limit/5xx).

    Auth (401), bad-request (400) and not-found (404) are NOT transient — they re-fail
    identically on retry, so we surface them immediately.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        if status in _TRANSIENT_STATUS:
            return True
        # An APIStatusError with a non-transient code (e.g. 401/400) must NOT be retried.
        if 400 <= status < 600:
            return False
    if type(exc).__name__ in _TRANSIENT_NAMES:
        return True
    msg = str(exc).lower()
    return any(k in msg for k in (
        "overloaded", "temporarily", "rate limit", "timed out", "timeout",
        "connection reset", "connection aborted",
        " 429", " 529", " 502", " 503", " 504",
    ))


def retry_delay(attempt: int) -> float:
    """Exponential backoff with jitter, capped at 30s. `attempt` is 0-based."""
    base = min(2.0 ** attempt, 30.0)
    return base + random.uniform(0.0, base * 0.25)


def call_with_retries(fn: Callable[[], Any],
                      on_retry: Optional[Callable[..., None]] = None) -> Any:
    """Run `fn`, retrying transient errors with backoff. Re-raises the last error if it
    never succeeds or the error is non-transient. `on_retry(attempt, max, delay, exc)` is
    called (best-effort) before each sleep so callers can show progress."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — re-raised below when non-transient/exhausted
            if attempt >= MAX_RETRIES or not is_transient_error(e):
                raise
            delay = retry_delay(attempt)
            if on_retry is not None:
                try:
                    on_retry(attempt + 1, MAX_RETRIES, delay, e)
                except Exception:
                    pass
            time.sleep(delay)
