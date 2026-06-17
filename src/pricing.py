"""Model pricing + cost estimation for KIBA.

Prices are USD per 1,000,000 tokens, matched by longest model-id prefix so that
dated variants (e.g. ``claude-sonnet-4-6-20250930``) resolve to their family.
Users can override or extend the table with ``~/.kiba/pricing.json``:

    { "my-model": { "input": 1.0, "output": 3.0 } }

Estimates only — provider billing is authoritative.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# USD per 1M tokens: {prefix: {"input": <in>, "output": <out>}}
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    # Anthropic — Claude
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "claude-haiku-4": {"input": 0.80, "output": 4.0},
    "claude-fable-5": {"input": 3.0, "output": 15.0},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.0},
    # OpenAI — GPT (estimates)
    "gpt-5.4-nano": {"input": 0.15, "output": 0.60},
    "gpt-5.4-mini": {"input": 0.50, "output": 2.0},
    "gpt-5.4": {"input": 10.0, "output": 30.0},
    "gpt-5.3": {"input": 10.0, "output": 30.0},
    "gpt-5.2": {"input": 10.0, "output": 30.0},
    # GLM via z.ai (estimates; Coding Plan is subscription-billed, not per-token)
    "glm-5": {"input": 0.60, "output": 2.20},
    "glm-4": {"input": 0.60, "output": 2.20},
    "zai/glm-5": {"input": 0.60, "output": 2.20},
    "zai/glm-4": {"input": 0.60, "output": 2.20},
    # Minimax (estimate)
    "minimax-m2": {"input": 0.30, "output": 1.20},
}

_user_cache: dict[str, dict[str, float]] | None = None


def _load_user_pricing() -> dict[str, dict[str, float]]:
    global _user_cache
    if _user_cache is not None:
        return _user_cache
    _user_cache = {}
    path = Path.home() / ".kiba" / "pricing.json"
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict) and "input" in v and "output" in v:
                        _user_cache[str(k).lower()] = {
                            "input": float(v["input"]),
                            "output": float(v["output"]),
                        }
    except Exception:
        pass
    return _user_cache


def get_rates(model: str | None) -> dict[str, float] | None:
    """Return {"input","output"} USD/1M for a model id via longest-prefix match."""
    if not model:
        return None
    m = model.lower()
    table = {**DEFAULT_PRICING, **_load_user_pricing()}
    best: tuple[int, dict[str, float]] | None = None
    for prefix, rates in table.items():
        if m.startswith(prefix.lower()) and (best is None or len(prefix) > best[0]):
            best = (len(prefix), rates)
    return best[1] if best else None


def estimate_cost(model: str | None, input_tokens: int, output_tokens: int) -> float | None:
    """Estimated USD cost, or None if the model isn't in the pricing table."""
    rates = get_rates(model)
    if rates is None:
        return None
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def format_cost(usd: float | None) -> str:
    if usd is None:
        return "n/a (model not in price table)"
    if usd < 0.01:
        return f"${usd:.4f}"
    return f"${usd:,.2f}"
