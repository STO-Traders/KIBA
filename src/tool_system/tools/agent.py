from __future__ import annotations

from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolCall, ToolResult
from ..registry import ToolRegistry, ToolSpec

_MAX_SUBAGENT_DEPTH = 2


class AgentTool:
    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="Agent",
            description=(
                "Spawn a subagent to handle a task autonomously. Pass `prompt` to launch a "
                "nested agent with its own tool-calling loop (returns its final result); set "
                "`background: true` to run it without blocking (returns a task_id to poll with "
                "TaskGet). Or pass `calls` to run a fixed sequence of tool calls as one step."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "prompt": {"type": "string"},
                    "description": {"type": "string"},
                    "background": {"type": "boolean"},
                    "max_turns": {"type": "integer"},
                    "calls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {"name": {"type": "string"}, "input": {"type": "object"}},
                            "required": ["name", "input"],
                        },
                    },
                    "stop_on_error": {"type": "boolean"},
                },
            },
            aliases=("Task",),
            is_destructive=True,
            max_result_size_chars=200_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        prompt = tool_input.get("prompt")
        if isinstance(prompt, str) and prompt.strip():
            return self._run_subagent(prompt, tool_input, context)
        calls = tool_input.get("calls")
        if calls is not None:
            return self._run_calls(calls, tool_input, context)
        raise ToolInputError("provide either 'prompt' (subagent) or 'calls' (batch)")

    # ------------------------------------------------------------------ subagent
    def _run_subagent(self, prompt: str, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        depth = getattr(context, "_subagent_depth", 0)
        if depth >= _MAX_SUBAGENT_DEPTH:
            return ToolResult(
                name="Agent",
                output={"error": f"subagent depth limit ({_MAX_SUBAGENT_DEPTH}) reached"},
                is_error=True,
            )
        provider = getattr(context, "provider", None)
        if provider is None:
            return ToolResult(
                name="Agent",
                output={"error": "no LLM provider available to spawn a subagent"},
                is_error=True,
            )
        max_turns = tool_input.get("max_turns") or 30
        background = bool(tool_input.get("background", False))

        def _execute() -> str:
            from ..agent_loop import run_agent_loop  # lazy: avoid circular import
            from ...agent.conversation import Conversation
            conv = Conversation()
            conv.add_user_message(prompt)
            prev = getattr(context, "_subagent_depth", 0)
            context._subagent_depth = prev + 1
            try:
                res = run_agent_loop(
                    conversation=conv,
                    provider=provider,
                    tool_registry=self._registry,
                    tool_context=context,
                    max_turns=int(max_turns),
                    stream=False,
                )
            finally:
                context._subagent_depth = prev
            return res.response_text or ""

        if not background:
            try:
                text = _execute()
            except Exception as e:
                return ToolResult(name="Agent", output={"error": str(e)}, is_error=True)
            return ToolResult(name="Agent", output={"result": text})

        # Background: spawn via TaskManager, register in context.tasks for TaskGet polling
        tm = getattr(context, "task_manager", None)
        if tm is None:
            return ToolResult(name="Agent", output={"error": "no task manager for background subagent"}, is_error=True)
        subject = (tool_input.get("description") or prompt)[:80]
        # The worker mutates `holder`; context.tasks[task_id] IS this same object, so
        # TaskGet sees live updates with no ordering race against task startup.
        holder: dict[str, Any] = {
            "id": None,
            "subject": f"subagent: {subject}",
            "status": "in_progress",
            "output": "",
        }

        def target(stop_event) -> None:
            try:
                holder["output"] = _execute()
                holder["status"] = "completed"
            except Exception as e:
                holder["output"] = f"Error: {e}"
                holder["status"] = "failed"

        task = tm.start(name="subagent", target=target)
        holder["id"] = task.task_id
        context.tasks[task.task_id] = holder
        return ToolResult(
            name="Agent",
            output={"task_id": task.task_id, "status": "in_progress",
                    "note": "running in background — poll with TaskGet(taskId)"},
        )

    # -------------------------------------------------------------------- batch
    def _run_calls(self, calls: Any, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        stop_on_error = bool(tool_input.get("stop_on_error", True))
        if not isinstance(calls, list):
            raise ToolInputError("calls must be an array")

        results: list[dict[str, Any]] = []
        any_error = False
        for idx, call in enumerate(calls):
            if not isinstance(call, dict):
                raise ToolInputError(f"calls[{idx}] must be an object")
            name = call.get("name")
            inp = call.get("input")
            if not isinstance(name, str) or not isinstance(inp, dict):
                raise ToolInputError(f"calls[{idx}] must include name:string and input:object")
            result = self._registry.dispatch(ToolCall(name=name, input=inp), context)
            results.append({"name": name, "is_error": result.is_error, "output": result.output})
            any_error = any_error or result.is_error
            if result.is_error and stop_on_error:
                break

        return ToolResult(name="Agent", output={"results": results}, is_error=any_error)
