from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostTracker:
    total_units: int = 0
    events: list[str] = field(default_factory=list)
    # Token + cost accounting (model-aware)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    turns: int = 0
    last_model: str | None = None
    last_usage: dict | None = None

    def record(self, label: str, units: int) -> None:
        self.total_units += units
        self.events.append(f'{label}:{units}')

    def record_usage(self, model: str | None, input_tokens: int, output_tokens: int) -> None:
        """Accumulate a turn's token usage and its estimated USD cost."""
        from .pricing import estimate_cost

        self.input_tokens += int(input_tokens or 0)
        self.output_tokens += int(output_tokens or 0)
        self.turns += 1
        self.last_model = model
        self.last_usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        cost = estimate_cost(model, input_tokens, output_tokens)
        if cost:
            self.estimated_cost_usd += cost

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
