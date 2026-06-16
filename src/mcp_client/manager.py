"""MCP (Model Context Protocol) client transport for Kiba.

KIBA already shipped MCP *tools* (MCP, ListMcpResourcesTool, ReadMcpResourceTool) that read
context.mcp_clients — but nothing ever populated it. This manager connects to MCP servers
(stdio / SSE / streamable-HTTP) declared in .mcp.json or settings.json, exposes each as a
synchronous client, and registers every server tool as a first-class `mcp__<server>__<tool>`.

Config (.mcp.json in cwd, ~/.mcp.json, or ~/.kiba/mcp.json):
  { "mcpServers": {
      "fs":     {"command": "uvx", "args": ["mcp-server-filesystem", "/path"], "env": {}},
      "remote": {"url": "https://example.com/mcp", "type": "http" | "sse"}
  }}

The async SDK is bridged to KIBA's synchronous tool layer by a dedicated background thread
running a persistent asyncio loop, so sessions stay open across synchronous tool calls.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from ..tool_system.protocol import ToolResult
from ..tool_system.registry import ToolSpec


def _read_json(path: Path) -> dict:
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def load_mcp_servers(cwd: str | Path | None = None) -> dict[str, dict]:
    """Merge mcpServers from ~/.kiba/mcp.json, ~/.mcp.json, and project .mcp.json (cwd)."""
    base = Path(cwd or Path.cwd())
    servers: dict[str, dict] = {}
    for path in (Path.home() / ".kiba" / "mcp.json", Path.home() / ".mcp.json", base / ".mcp.json"):
        servers.update(_read_json(path).get("mcpServers") or {})
    return servers


class _LoopThread:
    """Daemon thread running a persistent asyncio loop, so async MCP sessions can stay open
    while the synchronous REPL calls into them."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True, name="kiba-mcp-loop")
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro, timeout: float = 30):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    def stop(self) -> None:
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass


def _content_to_jsonable(result: Any) -> dict:
    out = []
    for c in getattr(result, "content", None) or []:
        ctype = getattr(c, "type", None)
        if ctype == "text":
            out.append({"type": "text", "text": getattr(c, "text", "")})
        elif ctype == "image":
            out.append({"type": "image", "mimeType": getattr(c, "mimeType", None)})
        else:
            out.append({"type": ctype or "unknown", "data": str(c)})
    payload: dict[str, Any] = {"content": out, "isError": bool(getattr(result, "isError", False))}
    structured = getattr(result, "structuredContent", None)
    if structured:
        payload["structured"] = structured
    return payload


class MCPServerClient:
    """Synchronous facade over one async MCP ClientSession."""

    def __init__(self, lt: _LoopThread, session: Any, tools: list, timeout: float = 30):
        self._lt = lt
        self._session = session
        self._tools = tools            # list of (name, description, input_schema)
        self._timeout = timeout

    def list_tools(self) -> list[str]:
        return [t[0] for t in self._tools]

    def tool_defs(self) -> list:
        return list(self._tools)

    def call_tool(self, tool_name: str, args: dict) -> Any:
        async def _c():
            r = await self._session.call_tool(tool_name, args or {})
            return _content_to_jsonable(r)
        return self._lt.run(_c(), self._timeout)

    def list_resources(self) -> list[dict]:
        async def _c():
            r = await self._session.list_resources()
            return [
                {
                    "uri": str(getattr(x, "uri", "")),
                    "name": getattr(x, "name", ""),
                    "mimeType": getattr(x, "mimeType", None),
                    "description": getattr(x, "description", None),
                }
                for x in getattr(r, "resources", [])
            ]
        return self._lt.run(_c(), self._timeout)

    def read_resource(self, uri: str) -> dict:
        async def _c():
            r = await self._session.read_resource(uri)
            contents = []
            for c in getattr(r, "contents", []):
                d: dict[str, Any] = {"uri": str(getattr(c, "uri", uri))}
                if getattr(c, "text", None) is not None:
                    d["text"] = c.text
                if getattr(c, "mimeType", None):
                    d["mimeType"] = c.mimeType
                contents.append(d)
            return {"contents": contents}
        return self._lt.run(_c(), self._timeout)


class _MCPProxyTool:
    """Registry tool that proxies `mcp__<server>__<tool>` to its MCP client."""

    def __init__(self, server: str, name: str, description: str, input_schema: dict):
        self._server = server
        self._name = name
        self._full = f"mcp__{server}__{name}"
        self._desc = description or f"MCP tool '{name}' from server '{server}'"
        self._schema = input_schema if isinstance(input_schema, dict) and input_schema else {"type": "object"}

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self._full,
            description=self._desc,
            input_schema=self._schema,
            is_destructive=True,
            max_result_size_chars=100_000,
        )

    def run(self, tool_input: dict, context: Any) -> ToolResult:
        client = context.mcp_clients.get(self._server)
        if client is None:
            return ToolResult(name=self._full, output={"error": f"mcp server not connected: {self._server}"}, is_error=True)
        try:
            out = client.call_tool(self._name, tool_input or {})
        except Exception as e:
            return ToolResult(name=self._full, output={"error": str(e)}, is_error=True)
        return ToolResult(name=self._full, output=out)


class MCPManager:
    def __init__(self, timeout: float = 30):
        self.clients: dict[str, MCPServerClient] = {}
        self.errors: dict[str, str] = {}
        self._lt: _LoopThread | None = None
        self._stacks: list = []
        self.timeout = timeout

    def connect_all(self, servers: dict[str, dict], registry=None) -> dict[str, MCPServerClient]:
        """Connect every configured server; register its tools into `registry` if given."""
        if not servers:
            return {}
        self._lt = _LoopThread()
        for name, cfg in servers.items():
            if not isinstance(cfg, dict):
                continue
            try:
                client = self._connect_one(name, cfg)
            except Exception as e:
                self.errors[name] = str(e)
                continue
            self.clients[name] = client
            if registry is not None:
                for tname, tdesc, tschema in client.tool_defs():
                    try:
                        registry.register(_MCPProxyTool(name, tname, tdesc, tschema))
                    except Exception:
                        pass  # duplicate / invalid name — keep going
        return self.clients

    def _connect_one(self, name: str, cfg: dict) -> MCPServerClient:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def _conn():
            stack = AsyncExitStack()
            if cfg.get("command"):
                params = StdioServerParameters(
                    command=cfg["command"],
                    args=list(cfg.get("args") or []),
                    env={**os.environ, **(cfg.get("env") or {})},
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            elif cfg.get("url"):
                ttype = (cfg.get("type") or "http").lower()
                if ttype == "sse":
                    from mcp.client.sse import sse_client
                    read, write = await stack.enter_async_context(sse_client(cfg["url"]))
                else:
                    from mcp.client.streamable_http import streamablehttp_client
                    res = await stack.enter_async_context(streamablehttp_client(cfg["url"]))
                    read, write = res[0], res[1]
            else:
                raise ValueError("MCP server config needs 'command' (stdio) or 'url' (http/sse)")
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            tlist = await session.list_tools()
            tools = [
                (t.name, getattr(t, "description", "") or "", getattr(t, "inputSchema", None) or {"type": "object"})
                for t in tlist.tools
            ]
            return stack, session, tools

        stack, session, tools = self._lt.run(_conn(), timeout=self.timeout)
        self._stacks.append(stack)
        return MCPServerClient(self._lt, session, tools, self.timeout)

    def close(self) -> None:
        if self._lt is None:
            return
        for stack in self._stacks:
            try:
                self._lt.run(stack.aclose(), timeout=5)
            except Exception:
                pass
        self._stacks.clear()
        self._lt.stop()
        self._lt = None
