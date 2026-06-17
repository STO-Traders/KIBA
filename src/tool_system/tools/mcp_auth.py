"""McpAuthTool — authenticate to remote (http/sse) MCP servers.

Supports two flows and stores the resulting bearer token via
``src.mcp_client.token_store`` so the MCP manager injects it on connect:

  * ``token``              — save a static bearer/PAT you already hold.
  * ``client_credentials`` — OAuth2 client-credentials grant: POST to a token
                             endpoint with client_id/client_secret (+scope) and
                             store the returned ``access_token``.

Plus ``status`` (list authenticated servers) and ``logout`` (remove a token).
After authenticating, reconnect (restart the session or re-init MCP) so the new
credentials take effect.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolResult
from ..registry import ToolSpec


class McpAuthTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="McpAuth",
            description=(
                "Authenticate to a remote MCP server and store its credentials. "
                "actions: 'token' (save a bearer token), 'client_credentials' "
                "(OAuth2 client-credentials grant), 'status' (list authenticated "
                "servers), 'logout' (remove a server's token)."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["token", "client_credentials", "status", "logout"],
                    },
                    "server": {"type": "string", "description": "MCP server name from .mcp.json"},
                    "token": {"type": "string", "description": "Bearer token (action=token)"},
                    "token_endpoint": {"type": "string", "description": "OAuth2 token URL"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "scope": {"type": "string"},
                },
                "required": ["action"],
            },
            is_destructive=False,
            max_result_size_chars=4000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        from ...mcp_client import token_store

        action = tool_input.get("action")

        if action == "status":
            servers = token_store.list_servers()
            return ToolResult(
                name="McpAuth",
                output={"authenticated_servers": servers, "count": len(servers)},
            )

        server = (tool_input.get("server") or "").strip()
        if action in ("token", "client_credentials", "logout") and not server:
            raise ToolInputError("'server' is required for this action")

        if action == "logout":
            removed = token_store.delete_token(server)
            return ToolResult(
                name="McpAuth",
                output={"server": server, "removed": removed},
            )

        if action == "token":
            token = (tool_input.get("token") or "").strip()
            if not token:
                raise ToolInputError("'token' is required for action=token")
            token_store.save_token(server, token, token_type="Bearer")
            return ToolResult(
                name="McpAuth",
                output={
                    "server": server,
                    "stored": True,
                    "note": "Reconnect (restart session) for the token to take effect.",
                },
            )

        if action == "client_credentials":
            endpoint = (tool_input.get("token_endpoint") or "").strip()
            client_id = (tool_input.get("client_id") or "").strip()
            client_secret = (tool_input.get("client_secret") or "").strip()
            if not endpoint or not client_id or not client_secret:
                raise ToolInputError(
                    "client_credentials requires token_endpoint, client_id, client_secret"
                )
            form = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
            if tool_input.get("scope"):
                form["scope"] = tool_input["scope"]
            data = urllib.parse.urlencode(form).encode()
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read().decode())
            except Exception as e:  # noqa: BLE001
                return ToolResult(
                    name="McpAuth",
                    output={"server": server, "error": f"token request failed: {e}"},
                    is_error=True,
                )
            access = body.get("access_token")
            if not access:
                return ToolResult(
                    name="McpAuth",
                    output={"server": server, "error": "no access_token in response", "response": body},
                    is_error=True,
                )
            token_store.save_token(
                server,
                access,
                token_type=body.get("token_type", "Bearer"),
                expires_in=body.get("expires_in"),
                scope=body.get("scope"),
            )
            return ToolResult(
                name="McpAuth",
                output={
                    "server": server,
                    "stored": True,
                    "token_type": body.get("token_type", "Bearer"),
                    "expires_in": body.get("expires_in"),
                    "note": "Reconnect (restart session) for the token to take effect.",
                },
            )

        raise ToolInputError(f"unknown action: {action}")
