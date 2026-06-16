"""Layered settings for Kiba — settings.json (permissions, env, model, hooks, statusLine).

This is distinct from config.json (which holds provider credentials only). Settings are
deep-merged across three layers, highest precedence last:

    user        ~/.kiba/settings.json
    project     <dir>/.kiba/settings.json  and  .kiba/settings.local.json
                (every dir from cwd up to root; nearer dirs override farther ones)
    enterprise  a managed-settings.json in a system location (cannot be overridden)

Schema (all optional):
    {
      "model": "glm-5.2",
      "env": { "KIBA_AUTO_APPROVE": "1", "FOO": "bar" },
      "permissions": {
        "allow": ["Read", "Grep"],
        "deny":  ["WebFetch"],
        "ask":   ["Bash"],
        "defaultMode": "default | acceptEdits | plan | bypassPermissions"
      },
      "hooks": { "PreToolUse": [ {"matcher": "Bash", "hooks": [{"type":"command","command":"..."}]} ] },
      "statusLine": { "type": "command", "command": "..." }
    }
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

USER_SETTINGS = Path.home() / ".kiba" / "settings.json"

# Project-level settings filenames, checked in each directory from cwd up to root.
_PROJECT_NAMES = (".kiba/settings.json", ".kiba/settings.local.json")

# Enterprise managed policy — first existing wins, applied last (highest precedence).
_ENTERPRISE_CANDIDATES = (
    Path("/Library/Application Support/Kiba/managed-settings.json"),  # macOS
    Path("/etc/kiba/managed-settings.json"),                          # Linux
    Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Kiba" / "managed-settings.json",  # Windows
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `over` onto `base`. Dicts merge; lists union (order-preserving);
    scalars from `over` win."""
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + [x for x in v if x not in out[k]]
        else:
            out[k] = v
    return out


def load_settings(cwd: str | Path | None = None) -> dict[str, Any]:
    """Load and merge settings across user → project(s) → enterprise."""
    cwd = Path(cwd).resolve() if cwd else Path.cwd()

    merged: dict[str, Any] = {}
    # 1) user (lowest precedence)
    merged = _deep_merge(merged, _read_json(USER_SETTINGS))

    # 2) project files, farthest dir first so nearer dirs override
    for d in reversed([cwd, *cwd.parents]):
        for name in _PROJECT_NAMES:
            merged = _deep_merge(merged, _read_json(d / name))

    # 3) enterprise managed (highest precedence)
    for p in _ENTERPRISE_CANDIDATES:
        if p.is_file():
            merged = _deep_merge(merged, _read_json(p))
            break

    return merged


def apply_env(settings: dict[str, Any]) -> None:
    """Apply settings.env into os.environ. Existing (shell-set) vars are NOT clobbered,
    so an explicit shell value always wins over a settings default."""
    env = settings.get("env")
    if isinstance(env, dict):
        for k, v in env.items():
            if v is not None and k not in os.environ:
                os.environ[str(k)] = str(v)


def get_permissions(settings: dict[str, Any]) -> dict[str, Any]:
    """Normalized permission block: allow/deny/ask tool-name lists + defaultMode."""
    p = settings.get("permissions") or {}
    return {
        "allow": [str(x) for x in (p.get("allow") or [])],
        "deny": [str(x) for x in (p.get("deny") or [])],
        "ask": [str(x) for x in (p.get("ask") or [])],
        "defaultMode": p.get("defaultMode"),
    }
