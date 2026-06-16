"""Lifecycle hooks for Kiba — shell commands the agent runs on events.

Configured under settings.json "hooks". Supported events: PreToolUse, PostToolUse,
UserPromptSubmit, Stop, SubagentStop, SessionStart, SessionEnd, PreCompact, Notification.

Each hook command receives a JSON payload on stdin and may:
  - exit 0  -> allow (stdout is injected as context for prompt/session events)
  - exit 2  -> block (PreToolUse blocks the tool; stderr is surfaced to the model)
  - print JSON {"decision": "block", "reason": "..."} or
    {"hookSpecificOutput": {"permissionDecision": "deny"|"allow",
                            "additionalContext": "..."}}

Config shape:
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Write", "hooks": [ {"type": "command", "command": "...", "timeout": 60} ] }
    ],
    "UserPromptSubmit": [ { "hooks": [ {"type": "command", "command": "..."} ] } ]
  }
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HookOutcome:
    blocked: bool = False
    messages: list[str] = field(default_factory=list)   # reasons / stderr to surface
    context: list[str] = field(default_factory=list)     # additionalContext to inject

    @property
    def message_text(self) -> str:
        return "\n".join(m for m in self.messages if m).strip()

    @property
    def context_text(self) -> str:
        return "\n".join(c for c in self.context if c).strip()


class HookRunner:
    """Runs configured shell hooks for lifecycle events."""

    def __init__(self, settings: dict[str, Any] | None = None,
                 cwd: str | Path | None = None, default_timeout: int = 60):
        self.hooks = (settings or {}).get("hooks") or {}
        self.cwd = str(cwd or Path.cwd())
        self.default_timeout = default_timeout

    def has(self, event: str) -> bool:
        return bool(self.hooks.get(event))

    def _matching(self, event: str, tool_name: str | None) -> list[dict]:
        out: list[dict] = []
        for entry in self.hooks.get(event) or []:
            if not isinstance(entry, dict):
                continue
            matcher = entry.get("matcher")
            entry_hooks = entry.get("hooks") or []
            if tool_name is None or not matcher or matcher in ("*", ""):
                out.extend(entry_hooks)
                continue
            try:
                matched = re.search(matcher, tool_name) is not None
            except re.error:
                matched = (matcher == tool_name)
            if matched:
                out.extend(entry_hooks)
        return out

    def run(self, event: str, payload: dict | None = None,
            tool_name: str | None = None) -> HookOutcome:
        outcome = HookOutcome()
        hooks = self._matching(event, tool_name)
        if not hooks:
            return outcome

        data = dict(payload or {})
        data.setdefault("hook_event_name", event)
        if tool_name:
            data.setdefault("tool_name", tool_name)
        data.setdefault("cwd", self.cwd)
        stdin_payload = json.dumps(data, default=str)

        for h in hooks:
            if not isinstance(h, dict) or h.get("type") != "command":
                continue
            cmd = h.get("command")
            if not cmd:
                continue
            timeout = h.get("timeout", self.default_timeout)
            try:
                proc = subprocess.run(
                    cmd, shell=True, cwd=self.cwd, input=stdin_payload,
                    capture_output=True, text=True, timeout=timeout, env=dict(os.environ),
                )
            except subprocess.TimeoutExpired:
                outcome.messages.append(f"hook timed out after {timeout}s: {cmd}")
                continue
            except Exception as e:
                outcome.messages.append(f"hook failed to run: {e}")
                continue

            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()

            if stdout:
                parsed = None
                try:
                    parsed = json.loads(stdout)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    if parsed.get("decision") == "block":
                        outcome.blocked = True
                        if parsed.get("reason"):
                            outcome.messages.append(str(parsed["reason"]))
                    hso = parsed.get("hookSpecificOutput")
                    if isinstance(hso, dict):
                        if hso.get("permissionDecision") == "deny":
                            outcome.blocked = True
                            if hso.get("permissionDecisionReason"):
                                outcome.messages.append(str(hso["permissionDecisionReason"]))
                        if hso.get("additionalContext"):
                            outcome.context.append(str(hso["additionalContext"]))
                    if parsed.get("systemMessage"):
                        outcome.messages.append(str(parsed["systemMessage"]))
                else:
                    # Plain stdout becomes injected context (UserPromptSubmit/SessionStart)
                    outcome.context.append(stdout)

            if proc.returncode == 2:
                outcome.blocked = True
                if stderr:
                    outcome.messages.append(stderr)
            elif proc.returncode != 0 and stderr:
                outcome.messages.append(stderr)

        return outcome
