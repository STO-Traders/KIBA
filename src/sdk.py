"""Kiba Agent SDK — embed KIBA's agent in your own Python.

For the watchdog, STO_Bridge, or any automation that wants KIBA's full agent (tools,
MCP, hooks, autonomy) as a programmatic call instead of the CLI.

    from src.sdk import query, KibaAgent

    # one-shot
    text = query("summarize the git log")

    # multi-turn (keeps conversation + context across calls)
    agent = KibaAgent(cwd="/path/to/project")
    print(agent.ask("read config.py"))
    print(agent.ask("now explain the riskiest part"))   # remembers the prior turn

    # structured
    info = query_json("audit this repo for bugs")        # {result, usage, num_turns, session_id}

Defaults to autonomous mode (no human to approve tool prompts) — the bash
dangerous-command blocklist still applies. Pass auto_approve=False to disable.
"""

from __future__ import annotations

import os
from typing import Optional


class KibaAgent:
    """A reusable KIBA agent. Each instance keeps its own conversation/session."""

    def __init__(
        self,
        provider: Optional[str] = None,
        cwd: Optional[str] = None,
        auto_approve: bool = True,
        output_style: Optional[str] = None,
        trusted_dirs: Optional[list[str]] = None,
    ):
        # Explicit (not setdefault) so auto_approve=False actually disables it instead of
        # inheriting a sticky "1" from a previous instance. The REPL treats "0"/absent as off.
        os.environ["KIBA_AUTO_APPROVE"] = "1" if auto_approve else "0"
        if output_style:
            os.environ["KIBA_OUTPUT_STYLE"] = output_style
        if trusted_dirs:
            os.environ["KIBA_TRUSTED_DIRS"] = os.pathsep.join(trusted_dirs)

        from src.config import get_default_provider
        from src.repl.core import KibaREPL
        # KibaREPL captures Path.cwd() at construction; chdir only around that and restore the
        # host CWD so the SDK never permanently mutates the caller's working directory.
        prev_cwd = os.getcwd()
        try:
            if cwd:
                os.chdir(cwd)
            self._repl = KibaREPL(
                provider_name=provider or get_default_provider(),
                stream=False,
                quiet=True,
            )
        finally:
            if cwd:
                os.chdir(prev_cwd)

    def ask(self, prompt: str, max_turns: int = 30, images=None) -> str:
        """Run one turn and return the final assistant text. `images`: paths/URLs for vision."""
        return self._repl.execute(prompt, max_turns=max_turns, images=images).response_text or ""

    def ask_json(self, prompt: str, max_turns: int = 30) -> dict:
        """Run one turn and return {result, num_turns, usage, session_id}."""
        r = self._repl.execute(prompt, max_turns=max_turns)
        u = r.usage or {}
        return {
            "result": r.response_text or "",
            "num_turns": getattr(r, "num_turns", None),
            "usage": {
                "input_tokens": u.get("input_tokens", 0),
                "output_tokens": u.get("output_tokens", 0),
            },
            "session_id": self._repl.session.session_id,
        }

    @property
    def session_id(self) -> str:
        return self._repl.session.session_id

    @property
    def conversation(self):
        return self._repl.session.conversation


def query(prompt: str, *, max_turns: int = 30, images=None, **kwargs) -> str:
    """One-shot: run KIBA on a prompt and return the final text. `images`: paths/URLs."""
    return KibaAgent(**kwargs).ask(prompt, max_turns=max_turns, images=images)


def query_json(prompt: str, *, max_turns: int = 30, **kwargs) -> dict:
    """One-shot returning {result, num_turns, usage, session_id}."""
    return KibaAgent(**kwargs).ask_json(prompt, max_turns=max_turns)
