"""Anthropic provider implementation."""

from __future__ import annotations

import os
import time
from typing import Generator, Optional, Any

try:
    import anthropic  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _MissingAnthropic:
        class Anthropic:  # type: ignore[no-redef]
            def __init__(self, *args, **kwargs):
                raise ModuleNotFoundError(
                    "anthropic package is not installed. Install optional dependencies to use AnthropicProvider."
                )

    anthropic = _MissingAnthropic()

from .base import BaseProvider, ChatResponse, MessageInput, TextChunkCallback
from ._retry import (
    MAX_RETRIES as _MAX_RETRIES,
    is_transient_error as _is_transient_error,
    retry_delay as _retry_delay,
    call_with_retries as _call_with_retries,
)

# Default max output tokens. 4096 truncates large tool calls — e.g. a Write whose `content`
# is a whole file — which corrupts the JSON arguments ("missing required field"). Raise it;
# override per-model with KIBA_MAX_TOKENS.
_DEFAULT_MAX_TOKENS = int(os.environ.get("KIBA_MAX_TOKENS") or 8192)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    def __init__(
        self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            base_url: Base URL (optional)
            model: Default model (default: claude-sonnet-4-6)
        """
        super().__init__(api_key, base_url, model or "claude-sonnet-4-6")

        self._client_kwargs = {"api_key": api_key}
        if base_url:
            self._client_kwargs["base_url"] = base_url
        self.client = None

    def _ensure_client(self):
        if self.client is not None:
            return self.client
        self.client = anthropic.Anthropic(**self._client_kwargs)
        return self.client

    def _system_param(self, system) -> dict[str, Any]:
        """Wrap the system prompt with a cache_control breakpoint so the (large, stable)
        system + CLAUDE.md context is cached across turns — big token savings on GLM/Claude.
        Disable with KIBA_NO_PROMPT_CACHE=1. No-op for empty/non-string system prompts."""
        if not system:
            return {}
        if os.environ.get("KIBA_NO_PROMPT_CACHE") or not isinstance(system, str):
            return {"system": system}
        return {"system": [{"type": "text", "text": system,
                            "cache_control": {"type": "ephemeral"}}]}

    def _build_chat_response(self, response: Any) -> ChatResponse:
        """Convert Anthropic SDK response into the shared ChatResponse shape."""
        content_text = ""
        tool_uses: list[dict[str, Any]] = []

        for block in response.content:
            block_type = getattr(block, "type", "text")
            if block_type == "text":
                text_val = getattr(block, "text", "")
                if text_val is not None:
                    content_text += str(text_val)
            elif block_type == "tool_use":
                tool_uses.append({
                    "id": str(getattr(block, "id", "")),
                    "name": str(getattr(block, "name", "")),
                    "input": dict(getattr(block, "input", {})),
                })

        usage = getattr(response, "usage", None)
        return ChatResponse(
            content=content_text,
            model=getattr(response, "model", self.model or ""),
            usage={
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            },
            finish_reason=str(getattr(response, "stop_reason", "stop")),
            tool_uses=tool_uses if tool_uses else None,
        )

    def chat(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """Synchronous chat completion.

        Args:
            messages: List of chat messages
            tools: Optional list of tool schemas
            **kwargs: Additional parameters (model, max_tokens, temperature, etc.)

        Returns:
            Chat response
        """
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", _DEFAULT_MAX_TOKENS)

        system = kwargs.pop("system", None)

        # Convert messages to Anthropic format
        anthropic_messages = self._prepare_messages(messages)

        # Make API call
        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools

        on_retry = kwargs.pop("on_retry", None)
        rest = {k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]}

        response = _call_with_retries(lambda: client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=anthropic_messages,
            **self._system_param(system),
            **extra_kwargs,
            **rest,
        ), on_retry=on_retry)

        return self._build_chat_response(response)

    def chat_stream(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion.

        Args:
            messages: List of chat messages
            tools: Optional list of tool schemas
            **kwargs: Additional parameters

        Yields:
            Chunks of response content
        """
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", _DEFAULT_MAX_TOKENS)
        system = kwargs.pop("system", None)
        kwargs.pop("on_retry", None)

        # Convert messages
        anthropic_messages = self._prepare_messages(messages)

        # Stream API call
        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools
        rest = {k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]}

        # Retry only the connect phase: once we've yielded a chunk, a transient failure can't
        # be replayed without duplicating output, so we let it propagate.
        yielded = False
        for i in range(_MAX_RETRIES + 1):
            try:
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    messages=anthropic_messages,
                    **self._system_param(system),
                    **extra_kwargs,
                    **rest,
                ) as stream:
                    for text in stream.text_stream:
                        yielded = True
                        yield text
                return
            except Exception as e:  # noqa: BLE001
                if i >= _MAX_RETRIES or not _is_transient_error(e) or yielded:
                    raise
                time.sleep(_retry_delay(i))

    def chat_stream_response(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        on_text_chunk: TextChunkCallback | None = None,
        **kwargs
    ) -> ChatResponse:
        """Stream Anthropic text chunks and return the final structured response."""
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", _DEFAULT_MAX_TOKENS)
        system = kwargs.pop("system", None)
        on_retry = kwargs.pop("on_retry", None)
        anthropic_messages = self._prepare_messages(messages)

        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools
        rest = {k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]}

        # `delivered` tracks whether any chunk reached on_text_chunk. A transient failure is
        # only safe to retry while it's False — once text is on screen, replaying would
        # duplicate it, so we re-raise instead.
        state = {"streamed": "", "delivered": False}

        def attempt():
            state["streamed"] = ""
            final = None
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                messages=anthropic_messages,
                **self._system_param(system),
                **extra_kwargs,
                **rest,
            ) as stream:
                for text in stream.text_stream:
                    if not text:
                        continue
                    state["streamed"] += text
                    state["delivered"] = True
                    if on_text_chunk is not None:
                        on_text_chunk(text)
                try:
                    return stream.get_final_message()
                except Exception:
                    return None

        final_message = None
        for i in range(_MAX_RETRIES + 1):
            try:
                final_message = attempt()
                break
            except Exception as e:  # noqa: BLE001
                if i >= _MAX_RETRIES or not _is_transient_error(e) or state["delivered"]:
                    raise
                delay = _retry_delay(i)
                if on_retry is not None:
                    try:
                        on_retry(i + 1, _MAX_RETRIES, delay, e)
                    except Exception:
                        pass
                time.sleep(delay)

        if final_message is not None:
            return self._build_chat_response(final_message)

        return ChatResponse(
            content=state["streamed"],
            model=model,
            usage={},
            finish_reason="stop",
            tool_uses=None,
        )

    def get_available_models(self) -> list[str]:
        """Get list of available Anthropic models.

        Returns:
            List of model names
        """
        return [
            # Claude 4 series (latest)
            "claude-sonnet-4-6",
            "claude-sonnet-4-5",
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-0",
            "claude-sonnet-4-20250514",
            "claude-opus-4-6",
            "claude-opus-4-5",
            "claude-opus-4-5-20251101",
            "claude-opus-4-1",
            "claude-opus-4-1-20250805",
            "claude-opus-4-0",
            "claude-opus-4-20250514",
            "claude-haiku-4-5",
            "claude-haiku-4-5-20251001",
            # Legacy
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
