"""Secure-ish credential store for authenticated MCP servers.

Tokens are kept in ``~/.kiba/mcp_tokens.json`` with ``0600`` permissions so a
shared machine's other users can't read them. Each entry holds a bearer token
(and optional refresh metadata) keyed by MCP server name. The MCP manager reads
this at connect time and injects ``Authorization: Bearer <token>`` for
http/sse servers; ``McpAuthTool`` writes to it.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_PATH = Path.home() / ".kiba" / "mcp_tokens.json"


def _read() -> dict[str, Any]:
    try:
        if _PATH.is_file():
            data = json.loads(_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _write(data: dict[str, Any]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    os.replace(tmp, _PATH)
    try:
        os.chmod(_PATH, 0o600)
    except Exception:
        pass


def save_token(server: str, token: str, token_type: str = "Bearer", **meta: Any) -> None:
    data = _read()
    entry = {"token": token, "token_type": token_type}
    entry.update({k: v for k, v in meta.items() if v is not None})
    data[server] = entry
    _write(data)


def get_token(server: str) -> dict[str, Any] | None:
    return _read().get(server)


def auth_header(server: str) -> dict[str, str]:
    """Return an Authorization header dict for a server, or {} if none stored."""
    entry = get_token(server)
    if not entry or not entry.get("token"):
        return {}
    return {"Authorization": f"{entry.get('token_type', 'Bearer')} {entry['token']}"}


def delete_token(server: str) -> bool:
    data = _read()
    if server in data:
        del data[server]
        _write(data)
        return True
    return False


def list_servers() -> list[str]:
    return sorted(_read().keys())
