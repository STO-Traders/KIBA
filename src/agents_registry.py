"""Custom agent types for Kiba — .kiba/agents/*.md (and ~/.kiba/agents/*.md).

Each file defines a named subagent the Agent/Task tool routes to via `agent_type`:

    ---
    name: code-reviewer
    description: Reviews diffs for bugs and risk
    tools: [Read, Grep, Glob, Bash]
    model: glm-5.2
    ---
    You are a meticulous code reviewer. Focus on correctness and risk...

The body becomes the subagent's system prompt; `tools` restricts its tool access.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .skills.frontmatter import parse_frontmatter


def _candidate_dirs(cwd: str | Path | None) -> list[Path]:
    # Order = precedence, because load_agent_types() keeps the FIRST definition of a name.
    # Project-local agents must win over global ones (like Claude Code), so walk cwd → root
    # FIRST (nearest dir wins), then fall back to the user-global dirs LAST.
    base = Path(cwd or Path.cwd())
    dirs: list[Path] = []
    for d in [base, *base.parents]:
        dirs.append(d / ".kiba" / "agents")
        dirs.append(d / ".claude" / "agents")
    dirs.append(Path.home() / ".kiba" / "agents")
    dirs.append(Path.home() / ".claude" / "agents")
    return dirs


def load_agent_types(cwd: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Discover and parse all custom agent definitions. First definition of a name wins."""
    agents: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for d in _candidate_dirs(cwd):
        key = str(d)
        if key in seen or not d.is_dir():
            continue
        seen.add(key)
        for f in sorted(d.glob("*.md")):
            try:
                res = parse_frontmatter(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            fm = res.frontmatter or {}
            name = str(fm.get("name") or f.stem).strip()
            if not name or name in agents:
                continue
            tools = fm.get("tools")
            if isinstance(tools, str):
                tools = [t.strip() for t in tools.replace(",", " ").split() if t.strip()]
            agents[name] = {
                "name": name,
                "description": str(fm.get("description") or ""),
                "tools": list(tools) if isinstance(tools, list) else None,
                "model": fm.get("model"),
                "prompt": (res.body or "").strip(),
            }
    return agents
