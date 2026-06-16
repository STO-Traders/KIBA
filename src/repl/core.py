"""Interactive REPL for Kiba."""

from __future__ import annotations

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.styles import Style
    from prompt_toolkit.completion import WordCompleter
    try:
        from prompt_toolkit.completion import FuzzyCompleter
    except Exception:  # pragma: no cover
        FuzzyCompleter = None  # type: ignore
    from prompt_toolkit.key_binding import KeyBindings
except ModuleNotFoundError:  # pragma: no cover
    class FileHistory:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class AutoSuggestFromHistory:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class Style:  # type: ignore
        @staticmethod
        def from_dict(*args, **kwargs):
            return None

    class WordCompleter:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
    FuzzyCompleter = None  # type: ignore

    class KeyBindings:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

    class PromptSession:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def prompt(self, *args, **kwargs):
            raise EOFError()

try:
    from rich.console import Console, Group
    from rich.align import Align
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.columns import Columns
except ModuleNotFoundError:  # pragma: no cover
    class Console:  # type: ignore
        def print(self, *args, **kwargs):
            return None

    Group = None  # type: ignore
    Align = None  # type: ignore
    Panel = None  # type: ignore
    Table = None  # type: ignore
    Text = None  # type: ignore
    Columns = None  # type: ignore

    class Markdown:  # type: ignore
        def __init__(self, text: str):
            self.text = text
from pathlib import Path
import asyncio
import sys
import json
import os
import random
from typing import Any

# Kooky status words shown while Kiba is busy processing a response
KIBA_STATUS_WORDS = [
    "Howling", "Prowling", "Sniffing", "Snarling",
    "Pouncing", "Burrowing", "Hunting", "Bamboozling",
    "Noodling", "Wrangling", "Skedaddling", "Hornswoggling",
    "Gallivanting", "Flummoxing", "Finagling", "Marinating",
    "Conjuring", "Scheming", "Tinkering", "Brewing",
    "Ruminating", "Sketching", "Whittling", "Zigzagging",
    "Moonwalking", "Canoodling", "Fiddle-faddling", "Reticulating",
    "Philosophising", "Crunching", "Forging", "Untangling",
    "Loping", "Skulking", "Bristling", "Tracking",
    "Scampering", "Rummaging", "Stalking", "Lurking",
    "Baying", "Growling", "Circling", "Slinking",
    "Ambushing", "Hackling", "Yipping", "Padding",
    "Scent-marking", "Moon-gazing", "Den-digging", "Pack-rallying",
    "Lone-wolfing", "Nosing", "Shitposting", "Doomscrolling",
    "Rage-quitting", "Crashing-out", "Touching-grass", "Malding",
    "Coping", "Seething", "Yeeting", "Vibe-checking",
    "Gaslighting", "Gatekeeping", "Girlbossing", "Menacing",
    "Plotting", "Sabotaging", "Procrastinating", "Overthinking",
    "Spiraling", "Catastrophizing", "Trauma-dumping", "Oversharing",
    "Cringing", "Facepalming", "Headdesking", "Eye-rolling",
    "Side-eyeing", "Ghosting", "Catfishing", "Negging",
    "Simping", "Stanning", "Trolling", "Flexing",
    "Capping", "Glazing", "Yapping", "Goblin-moding",
    "Gremlin-moding", "Feral-screaming", "Dissociating", "Hyperfixating",
    "Panic-installing", "Stack-overflowing", "Rubber-ducking", "Bikeshedding",
    "Yak-shaving", "Spaghetti-coding", "Duct-taping", "Hotfixing",
    "Force-pushing", "Merge-conflicting", "Winging-it", "Vibe-coding",
    "Hallucinating", "Improvising", "Flailing", "Caffeinating",
    "Snack-hunting", "Rage-baiting", "Clickbaiting", "Sub-tweeting",
    "Side-questing", "Min-maxing", "Speed-running", "Alt-tabbing",
    "Conspiracy-theorizing", "Tinfoil-hatting", "Manifesting", "Lollygagging",
    "Shenaniganing", "Tomfoolering", "Skullduggering", "Malarkeying",
    "Balderdashing", "Doom-prepping", "Goblin-snacking", "Sweating-profusely",
    "Bluffing", "Fuckin'-around", "Finding-out", "Clusterfucking",
    "Shitcanning", "Bullshitting", "Jackassing", "Bastardizing",
    "Pissing-about", "Buggering-about", "Twatwaffling", "Arsing-about",
    "Shit-shoveling", "Crap-flinging", "Hell-raising", "Shit-stirring",
    "Ballsing-it-up", "Cocking-it-up", "Bollocking", "Dipshittery",
    "Assclownery", "Horse-shitting", "Batshittery", "Fuckery-manufacturing",
    "Numbnutsing", "Dumbassing", "Half-assing", "Full-assing",
    "Pissant-ing", "Shitstorming", "Dumpster-firing", "Tomfuckery",
    "Asshattery", "Fucknuggeting", "Cussing-a-blue-streak", "Damn-it-all-ing",
    "Son-of-a-bitching", "Raising-hell", "Shit-the-bedding", "Gnashing",
    "Gnawing", "Ripping", "Tearing", "Shredding",
    "Mauling", "Savaging", "Devouring", "Feasting",
    "Bloodletting", "Marrow-sucking", "Fang-baring", "Hackle-raising",
    "Blood-scenting", "Kill-stalking", "Neck-snapping", "Pelt-shaking",
    "Wound-licking", "Rabid-frothing", "Hellhound-baying", "Alpha-asserting",
    "Territory-marking", "Intruder-snarling", "Predator-creeping", "Ambush-coiling",
    "Death-rolling", "Frenzy-feeding", "Berserk-charging", "Feral-lunging",
    "Wild-thrashing", "Beast-moding", "Primal-screaming", "Hunger-pacing",
    "Rabid-snapping", "Claw-sharpening", "Hunt-circling", "Shit-talking",
    "Shit-flinging", "Shit-wrangling", "Shit-mongering", "Shitwhistling",
    "Shitgibboning", "Bullshit-shoveling", "Horseshit-slinging", "Batshit-cracking",
    "Dogshit-coding", "Crapweaseling", "Crap-mongering", "Crap-canning",
    "Arse-faffing", "Arsewiping", "Arseholing", "Tosspotting",
    "Tosswaffling", "Wazzocking", "Pillocking", "Plonkering",
    "Muppeting", "Numptying", "Git-wrangling", "Sodding-about",
    "Bugger-all-doing", "Twatting-about", "Twonking", "Jackassery",
    "Dumbfuckery", "Clusterfuck-juggling", "Fuckabouting", "Fuckwitting",
    "Fucknozzling", "Fucksticking", "Shitkicking", "Ass-dragging",
    "Ass-hauling", "Ass-kicking", "Asshole-wrangling", "Trash-firing",
    "Garbage-juggling", "Hell-bent-charging", "Damnation-dealing", "Piss-boiling",
    "Pissed-offing", "Piss-and-vinegaring", "Bollocks-juggling", "Numbnutting",
    "Dipshitting", "Jackbooting", "Shitehawking", "Cock-up-fixing",
    "Balls-upping", "Knobheading", "Pissflapping", "Shit-canoeing",
    "Crapnuggeting", "Bastard-coding", "Hellfire-stoking", "Damn-near-dying",
    "Piss-takeing", "Throat-ripping", "Bone-ripping", "Marrow-ripping",
    "Sinew-ripping", "Fang-ripping", "Jaw-ripping", "Claw-ripping",
    "Talon-ripping", "Pelt-ripping", "Hide-ripping", "Snout-ripping",
    "Muzzle-ripping", "Gut-ripping", "Entrail-ripping", "Carcass-ripping",
    "Carrion-ripping", "Blood-ripping", "Spine-ripping", "Skull-ripping",
    "Ribcage-ripping", "Tendon-ripping", "Flesh-ripping", "Hackle-ripping",
    "Maw-ripping", "Gullet-ripping", "Haunch-ripping", "Gore-ripping",
    "Hunger-ripping", "Rage-ripping", "Frenzy-ripping", "Wrath-ripping",
    "Fury-ripping", "Venom-ripping", "Bile-ripping", "Foam-ripping",
    "Shadow-ripping", "Moon-ripping", "Night-ripping", "Storm-ripping",
    "Hell-ripping", "Death-ripping", "Doom-ripping", "Pack-ripping",
    "Den-ripping", "Lair-ripping", "Beast-ripping", "Predator-ripping",
    "Prey-ripping", "Wound-ripping", "Scar-ripping", "Throat-tearing",
    "Bone-tearing", "Marrow-tearing", "Sinew-tearing", "Fang-tearing",
    "Jaw-tearing", "Claw-tearing", "Talon-tearing", "Pelt-tearing",
    "Hide-tearing", "Snout-tearing", "Muzzle-tearing", "Gut-tearing",
    "Entrail-tearing", "Carcass-tearing", "Carrion-tearing", "Blood-tearing",
    "Spine-tearing", "Skull-tearing", "Ribcage-tearing", "Tendon-tearing",
    "Flesh-tearing", "Hackle-tearing", "Maw-tearing", "Gullet-tearing",
    "Haunch-tearing", "Gore-tearing", "Hunger-tearing", "Rage-tearing",
    "Frenzy-tearing", "Wrath-tearing", "Fury-tearing", "Venom-tearing",
    "Bile-tearing", "Foam-tearing", "Shadow-tearing", "Moon-tearing",
    "Night-tearing", "Storm-tearing", "Hell-tearing", "Death-tearing",
    "Doom-tearing", "Pack-tearing", "Den-tearing", "Lair-tearing",
    "Beast-tearing", "Predator-tearing", "Prey-tearing", "Wound-tearing",
    "Scar-tearing", "Throat-shredding", "Bone-shredding", "Marrow-shredding",
    "Sinew-shredding", "Fang-shredding", "Jaw-shredding", "Claw-shredding",
    "Talon-shredding", "Pelt-shredding", "Hide-shredding", "Snout-shredding",
    "Muzzle-shredding", "Gut-shredding", "Entrail-shredding", "Carcass-shredding",
    "Carrion-shredding", "Blood-shredding", "Spine-shredding", "Skull-shredding",
    "Ribcage-shredding", "Tendon-shredding", "Flesh-shredding", "Hackle-shredding",
    "Maw-shredding", "Gullet-shredding", "Haunch-shredding", "Gore-shredding",
    "Hunger-shredding", "Rage-shredding", "Frenzy-shredding", "Wrath-shredding",
    "Fury-shredding", "Venom-shredding", "Bile-shredding", "Foam-shredding",
    "Shadow-shredding", "Moon-shredding", "Night-shredding", "Storm-shredding",
    "Hell-shredding", "Death-shredding", "Doom-shredding", "Pack-shredding",
    "Den-shredding", "Lair-shredding", "Beast-shredding", "Predator-shredding",
    "Prey-shredding", "Wound-shredding", "Scar-shredding", "Throat-gnashing",
    "Bone-gnashing", "Marrow-gnashing", "Sinew-gnashing", "Fang-gnashing",
    "Jaw-gnashing", "Claw-gnashing", "Talon-gnashing", "Pelt-gnashing",
    "Hide-gnashing", "Snout-gnashing", "Muzzle-gnashing", "Gut-gnashing",
    "Entrail-gnashing", "Carcass-gnashing", "Carrion-gnashing", "Blood-gnashing",
    "Spine-gnashing", "Skull-gnashing", "Ribcage-gnashing", "Tendon-gnashing",
    "Flesh-gnashing", "Hackle-gnashing", "Maw-gnashing", "Gullet-gnashing",
    "Haunch-gnashing", "Gore-gnashing", "Hunger-gnashing", "Rage-gnashing",
    "Frenzy-gnashing", "Wrath-gnashing", "Fury-gnashing", "Venom-gnashing",
    "Bile-gnashing", "Foam-gnashing", "Shadow-gnashing", "Moon-gnashing",
    "Night-gnashing", "Storm-gnashing", "Hell-gnashing", "Death-gnashing",
    "Doom-gnashing", "Pack-gnashing", "Den-gnashing", "Lair-gnashing",
    "Beast-gnashing", "Predator-gnashing", "Prey-gnashing", "Wound-gnashing",
    "Scar-gnashing", "Throat-gnawing", "Bone-gnawing", "Marrow-gnawing",
    "Sinew-gnawing", "Fang-gnawing", "Jaw-gnawing", "Claw-gnawing",
    "Talon-gnawing", "Pelt-gnawing", "Hide-gnawing", "Snout-gnawing",
    "Muzzle-gnawing", "Gut-gnawing", "Entrail-gnawing", "Carcass-gnawing",
    "Carrion-gnawing", "Blood-gnawing", "Spine-gnawing", "Skull-gnawing",
    "Ribcage-gnawing", "Tendon-gnawing", "Flesh-gnawing", "Hackle-gnawing",
    "Maw-gnawing", "Gullet-gnawing", "Haunch-gnawing", "Gore-gnawing",
    "Hunger-gnawing", "Rage-gnawing", "Frenzy-gnawing", "Wrath-gnawing",
]

from src.agent import Session
from src.config import get_provider_config
from src.outputStyles import resolve_output_style
from src.providers import get_provider_class
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.base import ChatMessage
from src.providers.minimax_provider import MinimaxProvider
from src.tool_system.context import ToolContext
from src.tool_system.permissions import ToolPermissionContext
from src.tool_system.defaults import build_default_registry
from src.tool_system.protocol import ToolCall
from src.tool_system.agent_loop import ToolEvent, run_agent_loop, summarize_tool_result, summarize_tool_use

# New command system imports
from src.command_system import (
    CommandRegistry,
    CommandResult,
    create_command_context,
    execute_command_async,
    execute_command_sync,
    register_builtin_commands,
)
from src.cost_tracker import CostTracker
from src.history import HistoryLog


class KibaREPL:
    """Interactive REPL for Kiba."""

    def __init__(self, provider_name: str = "glm", stream: bool = False, quiet: bool = False, session=None):
        self.console = Console()
        self.provider_name = provider_name
        self.stream = stream
        self.quiet = quiet
        self.multiline_mode = False

        # Layered settings.json (permissions, env, model, hooks). Apply env FIRST so it can
        # set KIBA_AUTO_APPROVE / KIBA_TRUSTED_DIRS / KIBA_OUTPUT_STYLE before we read them.
        from src.settings import load_settings, apply_env, get_permissions
        self.settings = load_settings()
        apply_env(self.settings)
        self._settings_perms = get_permissions(self.settings)
        self._mode = (self._settings_perms.get("defaultMode") or "").strip()

        # Load configuration
        config = get_provider_config(provider_name)
        if not config.get("api_key"):
            self.console.print("[red]Error: API key not configured.[/red]")
            self.console.print("Run [bold]kiba login[/bold] to configure.")
            sys.exit(1)

        # Initialize provider
        provider_class = get_provider_class(provider_name)
        self.provider = provider_class(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model=self.settings.get("model") or config.get("default_model"),
        )

        # Create a fresh session, or reuse one passed in (--continue / --resume)
        self.session = session if session is not None else Session.create(
            provider_name,
            self.provider.model
        )

        self.tool_registry = build_default_registry()

        # Optional autonomous / broadened-access config via environment:
        #   KIBA_AUTO_APPROVE=1      -> auto-approve every tool permission prompt
        #                               (the bash dangerous-command blocklist still applies)
        #   KIBA_TRUSTED_DIRS=a:b:c  -> extra dirs the agent may read/write (os.pathsep-separated)
        #   KIBA_OUTPUT_STYLE=name   -> persona/output style from ~/.kiba/output-styles/<name>.md
        self._auto_approve = os.environ.get("KIBA_AUTO_APPROVE", "").strip().lower() in ("1", "true", "yes", "on")
        # settings.json permissions.defaultMode can also drive autonomy:
        #   bypassPermissions -> auto-approve everything   ·   plan -> planning posture
        if self._mode == "bypassPermissions":
            self._auto_approve = True
        trusted_dirs = [d for d in os.environ.get("KIBA_TRUSTED_DIRS", "").split(os.pathsep) if d.strip()]
        deny_tools = self._settings_perms.get("deny") or []

        if trusted_dirs or deny_tools:
            perm_ctx = ToolPermissionContext.from_iterables(
                deny_tools or None,
                workspace_root=Path.cwd(),
                additional_working_directories=trusted_dirs or None,
                allow_docs=self._auto_approve,
            )
            self.tool_context = ToolContext(workspace_root=Path.cwd(), permission_context=perm_ctx)
        else:
            self.tool_context = ToolContext(workspace_root=Path.cwd())

        self.tool_context.ask_user = self._ask_user_questions

        # Lifecycle hooks (settings.json "hooks") — fire on tool use, prompts, session events
        from src.hooks.runner import HookRunner
        self.hook_runner = HookRunner(self.settings, cwd=Path.cwd())
        self.tool_context.hook_runner = self.hook_runner
        self.tool_context.provider = self.provider  # lets the Agent tool spawn subagents

        # Permission handler with status control for proper input handling
        self._current_status = None
        if self._auto_approve:
            self.tool_context.permission_handler = self._auto_approve_permission
            if not quiet:
                self.console.print(
                    "[dim yellow]⚡ Autonomous mode on — tool actions auto-approved "
                    "(dangerous-command blocklist still active).[/dim yellow]"
                )
        elif self._mode == "acceptEdits":
            self.tool_context.permission_handler = self._accept_edits_permission
        else:
            self.tool_context.permission_handler = self._handle_permission_request

        if self._mode == "plan":
            self.tool_context.plan_mode = True

        # Persona / output style (falls back to the built-in 'default' if unset or missing)
        style_env = os.environ.get("KIBA_OUTPUT_STYLE", "").strip()
        if style_env:
            self.tool_context.output_style_name = style_env
            self.tool_context.output_style_dir = Path.home() / ".kiba" / "output-styles"

        # MCP servers (stdio/SSE/HTTP) from .mcp.json — connect, populate mcp_clients,
        # and register each server tool as a first-class `mcp__<server>__<tool>`.
        self.mcp_manager = None
        try:
            from src.mcp_client.manager import MCPManager, load_mcp_servers
            _servers = load_mcp_servers(Path.cwd())
            if _servers:
                self.mcp_manager = MCPManager()
                _clients = self.mcp_manager.connect_all(_servers, registry=self.tool_registry)
                self.tool_context.mcp_clients = dict(_clients)
                import atexit
                atexit.register(self.mcp_manager.close)
                if not quiet:
                    if _clients:
                        self.console.print(f"[dim cyan]🔌 MCP connected: {', '.join(_clients)}[/dim cyan]")
                    for _nm, _err in self.mcp_manager.errors.items():
                        self.console.print(f"[dim red]   MCP '{_nm}' failed: {_err}[/dim red]")
        except Exception as _e:
            if not quiet:
                self.console.print(f"[dim red]MCP init skipped: {_e}[/dim red]")

        # Original built-in commands - define this FIRST!
        self._original_built_ins = [
            "/",
            "/help",
            "/exit",
            "/quit",
            "/q",
            "/clear",
            "/save",
            "/load",
            "/multiline",
            "/stream",
            "/render-last",
            "/tools",
            "/tool",
            "/skills",
            "/init",
        ]
        self._built_in_commands = list(self._original_built_ins)

        # Initialize new command system
        self._init_command_system()

        # Prompt toolkit with tab completion
        history_file = Path.home() / ".kiba" / "history"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        self.completer = WordCompleter(self._get_slash_command_words(), ignore_case=True)

        # Key bindings for multiline
        self.bindings = KeyBindings()
        if hasattr(self.bindings, "add"):
            @self.bindings.add("/")  # type: ignore[attr-defined]
            def _show_slash_completions(event):  # type: ignore[no-untyped-def]
                buf = event.current_buffer
                if buf.text == "":
                    buf.insert_text("/")
                    buf.start_completion(select_first=False)

        if self.quiet:
            # Headless mode never reads interactive input — skip prompt_toolkit so it
            # doesn't emit "Input is not a terminal" on non-tty stdin.
            self.prompt_session = None
        else:
            self.prompt_session = PromptSession(
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                style=Style.from_dict({
                    'prompt': 'bold blue',
                }),
                key_bindings=self.bindings,
                complete_while_typing=True,
            )

    def _ask_user_questions(self, questions: list[dict]) -> dict[str, str]:
        # Stop the Rich status spinner if running, so we can get clean input
        if self._current_status is not None:
            try:
                self._current_status.stop()
            except Exception:
                pass

        answers: dict[str, str] = {}
        for q in questions:
            question_text = str(q.get("question", "")).strip()
            options = q.get("options") or []
            multi = bool(q.get("multiSelect", False))
            if not question_text or not isinstance(options, list) or len(options) < 2:
                continue

            header = str(q.get("header", "")).strip()
            title = f"[bold]{question_text}[/bold]"
            if header:
                title = f"[bold cyan]\\[{header}][/bold cyan] {title}"
            self.console.print(f"\n{title}")
            labels: list[str] = []
            for i, opt in enumerate(options, start=1):
                label = str((opt or {}).get("label", "")).strip()
                desc = str((opt or {}).get("description", "")).strip()
                labels.append(label)
                # Highlight the recommended option (Claude Code marks it "(Recommended)")
                if "recommend" in label.lower():
                    self.console.print(f"  [bold green]{i}. {label}[/bold green]  [dim]{desc}[/dim]")
                else:
                    self.console.print(f"  [bold]{i}.[/bold] {label}  [dim]{desc}[/dim]")
            other_idx = len(labels) + 1
            self.console.print(f"  [bold]{other_idx}.[/bold] Other  [dim]Provide custom text[/dim]")
            if multi:
                self.console.print("[dim]Tip: pick multiple, comma-separated (e.g. 1,3)[/dim]")

            prompt = "Select (comma-separated) > " if multi else "Select > "
            raw = input(prompt).strip()
            if not raw:
                choice_str = "1"
            else:
                choice_str = raw

            selected: list[str] = []
            parts = [p.strip() for p in choice_str.split(",") if p.strip()]
            if not parts:
                parts = ["1"]
            for part in parts:
                try:
                    idx = int(part)
                except ValueError:
                    idx = -1
                if idx == other_idx:
                    free = input("Other > ").strip()
                    if free:
                        selected.append(free)
                    continue
                if 1 <= idx <= len(labels):
                    selected.append(labels[idx - 1])
            if not selected:
                selected = [labels[0]]
            answers[question_text] = ", ".join(selected) if multi else selected[0]

        # Restart spinner after getting answers
        if self._current_status is not None:
            try:
                self._current_status.start()
            except Exception:
                pass

        return answers

    def _auto_approve_permission(
        self,
        tool_name: str,
        message: str,
        suggestion: str | None,
    ) -> tuple[bool, bool]:
        """Auto-approve every tool permission prompt (KIBA_AUTO_APPROVE mode).

        This only bypasses the interactive consent prompt. The hard safety floors
        — the bash dangerous-command blocklist and the trusted-directory boundary —
        are enforced elsewhere and still apply.
        """
        return (True, False)

    def _accept_edits_permission(
        self,
        tool_name: str,
        message: str,
        suggestion: str | None,
    ) -> tuple[bool, bool]:
        """acceptEdits mode: auto-approve file writes/edits, prompt for everything else."""
        if str(tool_name) in ("Write", "Edit", "NotebookEdit"):
            return (True, False)
        return self._handle_permission_request(tool_name, message, suggestion)

    def _handle_permission_request(
        self,
        tool_name: str,
        message: str,
        suggestion: str | None,
    ) -> tuple[bool, bool]:
        """Handle interactive permission requests from tools.

        Args:
            tool_name: Name of the tool requesting permission.
            message: Message explaining what permission is needed.
            suggestion: Optional suggestion for enabling the setting.

        Returns:
            Tuple of (allowed: bool, continue_without_caching: bool).
            continue_without_caching is always False since we don't cache in REPL.
        """
        # No interactive TTY (headless/piped) → can't prompt; deny safely instead of
        # hanging on input(). Set KIBA_AUTO_APPROVE=1 for autonomous tool use.
        if not sys.stdin.isatty():
            return (False, False)

        # Stop the Rich status spinner if running, so we can get clean input
        if self._current_status is not None:
            try:
                self._current_status.stop()
            except Exception:
                pass

        self.console.print("")
        self.console.print("[bold yellow]⚠ Permission Required[/bold yellow]")
        self.console.print(f"  {message}")
        self.console.print("")

        # Determine if this is a setting that can be enabled
        can_enable_setting = False
        setting_to_enable: str | None = None

        msg_lower = message.lower()
        if "allow_docs" in msg_lower or "documentation files" in msg_lower:
            pc = self.tool_context.permission_context
            if hasattr(pc, 'allow_docs') and not pc.allow_docs:
                can_enable_setting = True
                setting_to_enable = "allow_docs"

        # Build options
        options: list[tuple[str, str]] = [
            ("y", "Yes, allow this action"),
            ("n", "No, deny this action"),
        ]
        if can_enable_setting:
            options.insert(0, ("e", f"Enable {setting_to_enable} and allow"))

        self.console.print("[bold]Options:[/bold]")
        for i, (key, desc) in enumerate(options, start=1):
            self.console.print(f"  {i}. [{key}] {desc}")
        self.console.print("")

        # Get input - use standard input() which works after stopping status
        choice = input("Select option> ").strip().lower()

        # Parse choice based on the actual displayed options
        if can_enable_setting:
            # Menu: 1=Enable, 2=Yes, 3=No
            if choice in ("1", "e", "enable"):
                self._enable_permission_setting(setting_to_enable)
                return True, False
            elif choice in ("2", "y", "yes", ""):
                return True, False
            elif choice in ("3", "n", "no"):
                return False, False
        else:
            # Menu: 1=Yes, 2=No
            if choice in ("1", "y", "yes", ""):
                return True, False
            elif choice in ("2", "n", "no"):
                return False, False

        # Default to deny for invalid input
        self.console.print("[dim]Invalid choice, defaulting to deny.[/dim]")
        return False, False

    def _enable_permission_setting(self, setting_name: str | None) -> None:
        """Enable a permission setting in the tool context."""
        if not setting_name:
            return

        self.console.print(f"\n[dim]Enabling {setting_name}...[/dim]")

        if setting_name == "allow_docs":
            pc = self.tool_context.permission_context
            if hasattr(pc, 'allow_docs'):
                pc.allow_docs = True
                self.console.print(f"[green]✓ {setting_name} enabled for this session[/green]")
                return

        self.console.print(f"[dim]Could not enable {setting_name}.[/dim]")

    def _init_command_system(self):
        """Initialize the new command system."""
        # Also register to global registry so execute_command_async can find commands
        register_builtin_commands(None)  # None = use global registry

        # Create command registry and register built-ins
        self.command_registry = CommandRegistry()
        register_builtin_commands(self.command_registry)

        # Create cost tracker and history
        self.cost_tracker = CostTracker()
        self.history_log = HistoryLog()

        # Create command context
        self.command_context = create_command_context(
            workspace_root=Path.cwd(),
            conversation=self.session.conversation,
            cost_tracker=self.cost_tracker,
            history=self.history_log,
        )

        # Merge new commands with built-in list for completion
        self._update_built_in_commands_with_command_system()

    def _update_built_in_commands_with_command_system(self):
        """Update the built-in commands list with commands from the new system."""
        # Start with original built-ins
        self._built_in_commands = list(self._original_built_ins)

        # Add commands from the new command system
        try:
            for cmd in self.command_registry.list_commands():
                cmd_name = f"/{cmd.name}"
                if cmd_name not in self._built_in_commands:
                    self._built_in_commands.append(cmd_name)
                # Add aliases
                for alias in cmd.aliases:
                    alias_name = f"/{alias}"
                    if alias_name not in self._built_in_commands:
                        self._built_in_commands.append(alias_name)
        except Exception:
            pass

    def _try_execute_new_command(self, command: str, args: str) -> tuple[bool, str | None]:
        """Try to execute a command using the new command system (sync path for LocalCommand only).

        Returns:
            Tuple of (handled: bool, result_text: str | None)
        """
        try:
            success, result_text, error = execute_command_sync(
                command, args, self.command_context
            )
            if success:
                return True, result_text
            else:
                return False, error
        except Exception as e:
            return False, str(e)

    async def _try_execute_command_async(self, command: str, args: str) -> CommandResult:
        """Execute a command asynchronously, supporting both LocalCommand and PromptCommand.

        Returns:
            CommandResult with the execution result
        """
        try:
            return await execute_command_async(command, args, self.command_context)
        except Exception as e:
            return CommandResult.error(command, str(e))

    def _handle_command_result(self, result: CommandResult) -> bool:
        """Handle the result of a command execution.

        Returns True if the command was handled, False otherwise.
        """
        if not result.success:
            if result.error:
                self.console.print(f"[red]{result.error}[/red]")
            return True

        if result.result_type == "text":
            if result.text:
                self.console.print("\n" + result.text)
                self.console.print()
            return True

        elif result.result_type == "prompt":
            # For PromptCommand, extract the text content and send to LLM
            prompt_text = ""
            for item in result.prompt_content:
                if item.get("type") == "text":
                    prompt_text = item.get("text", "")
                    break

            if prompt_text:
                # Send the prompt to the LLM for interactive execution
                # Use higher max_turns for complex commands like /init
                self.console.print("[dim]Initializing workspace setup...[/dim]")
                self.chat(prompt_text, max_turns=100)
            return True

        elif result.result_type == "skip":
            # Command handled silently
            return True

        return False

    def _get_slash_command_words(self) -> list[str]:
        words = list(self._built_in_commands)
        try:
            from src.skills.loader import get_all_skills

            cwd = self.tool_context.cwd or self.tool_context.workspace_root
            for s in get_all_skills(project_root=cwd):
                words.append(f"/{s.name}")
        except Exception:
            pass
        deduped: list[str] = []
        seen: set[str] = set()
        for w in words:
            lw = w.lower()
            if lw in seen:
                continue
            seen.add(lw)
            deduped.append(w)
        return deduped

    def _refresh_completer(self) -> None:
        try:
            words = self._get_slash_command_words()
            try:
                base = WordCompleter(words, ignore_case=True, match_middle=True)
            except TypeError:
                base = WordCompleter(words, ignore_case=True)
            self.completer = FuzzyCompleter(base) if FuzzyCompleter is not None else base
            if hasattr(self, "prompt_session") and getattr(self.prompt_session, "completer", None) is not None:
                self.prompt_session.completer = self.completer
        except Exception:
            return

    def _show_slash_palette(self, query: str | None = None) -> None:
        q = (query or "").strip().lower()
        self.console.print("\n[bold]Available commands and skills:[/bold]")

        # Collect all commands
        all_commands: list[tuple[str, str, str]] = []  # (name, description, type)
        seen: set[str] = set()

        def add_command(name: str, desc: str, cmd_type: str = "command") -> None:
            if name in seen:
                return
            seen.add(name)
            if q and q not in name.lower() and q not in desc.lower():
                return
            all_commands.append((name, desc, cmd_type))

        # Add built-in commands
        for cmd in self._original_built_ins:
            if cmd == "/":
                continue
            add_command(cmd, "", "command")

        # Add commands from new command system
        try:
            for cmd in self.command_registry.list_commands():
                cmd_name = f"/{cmd.name}"
                if cmd_name in self._original_built_ins:
                    continue
                alias_str = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                add_command(f"{cmd_name}{alias_str}", cmd.description, "command")
        except Exception:
            pass

        # Add skills
        try:
            from src.skills.loader import get_all_skills

            cwd = self.tool_context.cwd or self.tool_context.workspace_root
            skills = list(get_all_skills(project_root=cwd))
            skills.sort(key=lambda s: s.name.lower())
            for s in skills:
                desc = (s.description or "").strip()
                add_command(f"/{s.name}", desc, "skill")
        except Exception:
            pass

        # Sort and display
        all_commands.sort(key=lambda x: x[0].lower())
        for name, desc, cmd_type in all_commands:
            if cmd_type == "skill":
                self.console.print(f"  [magenta]{name}[/magenta]")
                if desc:
                    self.console.print(f"    [dim]{desc}[/dim]")
            else:
                if desc:
                    self.console.print(f"  {name}  [dim]- {desc}[/dim]")
                else:
                    self.console.print(f"  {name}")

        self.console.print()

    def _shorten_path_text(self, text: str) -> str:
        root = str(self.tool_context.workspace_root)
        cwd = str(self.tool_context.cwd or self.tool_context.workspace_root)
        for base in (cwd, root):
            prefix = base.rstrip("/") + "/"
            if text.startswith(prefix):
                return "./" + text[len(prefix):]
            text = text.replace(prefix, "")
        return text

    def _display_cwd(self) -> str:
        cwd = str(Path.cwd())
        home = str(Path.home())
        if cwd.startswith(home):
            return cwd.replace(home, "~", 1)
        return cwd

    def _truncate_middle(self, text: str, limit: int) -> str:
        if limit <= 0 or len(text) <= limit:
            return text
        if limit <= 3:
            return text[:limit]
        head = max(1, (limit - 1) // 2)
        tail = max(1, limit - head - 1)
        return f"{text[:head]}…{text[-tail:]}"

    def _print_startup_header(self):
        from src import __version__

        display_path = self._display_cwd()
        provider_label = f"{self.provider_name.upper()} Provider"
        model_label = self.provider.model or "Unknown model"

        banner_ascii = "\n".join([
            "██╗  ██╗██╗██████╗  █████╗ ",
            "██║ ██╔╝██║██╔══██╗██╔══██╗",
            "█████╔╝ ██║██████╔╝███████║",
            "██╔═██╗ ██║██╔══██╗██╔══██║",
            "██║  ██╗██║██████╔╝██║  ██║",
            "╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝",
        ])

        sprite_grid = [
            "...kkkkkkkk......",
            ".ssssssssssss....",
            ".ssssssssssss.ss.",
            ".sskksssskkss..ss",
            ".sskksssskkss..ss",
            ".ssssssssssss..ss",
            ".sssssWWsssss..ss",
            "ssssssssssss.ssss",
            "sssssssssssssssss",
            "ssssssssssssss...",
            "ssssssssssssss...",
            ".ss.ss..ss.ss....",
            ".ss.ss..ss.ss....",
        ]
        sprite_colors = {"k": "black", "s": "#cd8b8b", "W": "white"}
        mascot_ascii = "\n".join(sprite_grid)

        if Panel is None or Group is None or Align is None or Table is None or Text is None or Columns is None:
            print(banner_ascii)
            print(mascot_ascii)
            print(f"Kiba v{__version__}")
            print(f"{model_label} · {provider_label}")
            print(f"{display_path}\n")
            return

        width = getattr(self.console, "width", 80)
        content_width = max(28, min(width - 12, 72))
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bright_black", justify="right", no_wrap=True)
        table.add_column(style="white", ratio=1)
        table.add_row("Version", Text.assemble(("Kiba", "bold white"), ("  ", ""), (f"v{__version__}", "bold cyan")))
        table.add_row("Model", Text(model_label, style="bold magenta"))
        table.add_row("Provider", Text(provider_label, style="bold green"))
        table.add_row("Workspace", Text(self._truncate_middle(display_path, content_width - 12), style="bold blue"))

        footer = Text("/help  •  /tools  •  /stream  •  /render-last  •  /exit", style="dim")
        banner_block = Align.center(Text(banner_ascii, style="bold orange3", no_wrap=True))
        mascot_block = Text(no_wrap=True)
        for _i, _row in enumerate(sprite_grid):
            if _i:
                mascot_block.append("\n")
            for _ch in _row:
                if _ch == ".":
                    mascot_block.append("  ")
                else:
                    mascot_block.append("██", style=sprite_colors[_ch])
        info_row = Align.center(Columns([mascot_block, table], align="center", expand=False))
        body = Group(
            banner_block,
            Text(""),
            info_row,
            Text(""),
            Align.center(footer),
        )
        header = Panel(
            body,
            border_style="bright_black",
            subtitle="[dim]interactive terminal[/dim]",
            padding=(1, 2),
        )
        self.console.print(header)
        self.console.print()

    def run(self):
        """Run the REPL."""
        self._print_startup_header()

        while True:
            try:
                self._refresh_completer()
                # Dynamic prompt based on multiline mode
                # Using '❯' for a modern feel
                prompt_text = '... ' if self.multiline_mode else '❯ '
                user_input = self.prompt_session.prompt(
                    prompt_text,
                    multiline=self.multiline_mode
                )

                if not user_input.strip():
                    self.multiline_mode = False
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                    continue

                # Send to LLM
                self.chat(user_input)
                self.multiline_mode = False

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
                self.multiline_mode = False
                continue
            except EOFError:
                self.console.print("\n[blue]Goodbye![/blue]")
                break

    def handle_command(self, command: str):
        """Handle slash commands."""
        raw = command.strip()
        if raw == "/":
            self._show_slash_palette()
            return
        if raw.startswith("/") and " " not in raw and raw.lower() not in (c.lower() for c in self._built_in_commands):
            query = raw[1:]
            if query:
                self._show_slash_palette(query=query)
                return

        # First, try the new command system
        if raw.startswith("/"):
            parts = raw[1:].split(maxsplit=1)
            cmd_name = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Check if this command exists in the new command system
            # but skip the ones we handle specially
            # Note: /context, /compact, /skill need special handling, don't route through new system
            # /init is handled via new command system (PromptCommand) so it's NOT in special_commands
            special_commands = {
                'exit', 'quit', 'q',
                'help', 'tools', 'tool',
                'save', 'load', 'multiline', 'stream', 'render-last',
                'skill',
                'context', 'compact',  # These need special handling
                ''
            }

            # Handle /init through the new command system (PromptCommand path)
            if cmd_name == 'init':
                # Use async path for PromptCommand
                try:
                    # Run async command execution in a new event loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._try_execute_command_async(cmd_name, args)
                        )
                        result = future.result()

                    if result.success:
                        self._handle_command_result(result)
                    elif result.error:
                        self.console.print(f"[red]{result.error}[/red]")
                except Exception as e:
                    self.console.print(f"[red]Error executing /init: {e}[/red]")
                return

            if cmd_name not in special_commands:
                # Try to execute via new command system
                # First try sync path for LocalCommand (faster)
                try:
                    handled, result_text = self._try_execute_new_command(cmd_name, args)
                    if handled:
                        if result_text:
                            self.console.print("\n" + result_text)
                        self.console.print()
                        return
                except Exception as e:
                    # Fall through to async path
                    pass

                # Use async path for PromptCommand
                # Run in a new event loop since we're in a sync context
                try:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._try_execute_command_async(cmd_name, args)
                        )
                        result = future.result()

                    if result.success:
                        if self._handle_command_result(result):
                            return
                except Exception:
                    pass

        # Fall back to original command handling
        cmd = raw.lower()

        if cmd in ['/exit', '/quit', '/q']:
            self.console.print("[blue]Goodbye![/blue]")
            sys.exit(0)

        elif cmd == '/help':
            self.show_help()

        elif cmd == '/tools':
            names = [spec.name for spec in self.tool_registry.list_specs()]
            names.sort(key=str.lower)
            self.console.print("\n[bold]Available tools:[/bold]")
            for name in names:
                self.console.print(f"  - {name}")
            self.console.print()

        elif cmd.startswith('/tool'):
            parts = command.strip().split(maxsplit=2)
            if len(parts) < 2:
                self.console.print("[red]Usage: /tool <name> <json-input>[/red]")
                return
            name = parts[1]
            payload = {}
            if len(parts) == 3:
                try:
                    payload = json.loads(parts[2])
                except json.JSONDecodeError as e:
                    self.console.print(f"[red]Invalid JSON input: {e}[/red]")
                    return
            try:
                result = self.tool_registry.dispatch(ToolCall(name=name, input=payload), self.tool_context)
            except Exception as e:
                self.console.print(f"[red]Tool error: {e}[/red]")
                return
            self.console.print("\n[bold]Tool result:[/bold]")
            self.console.print(json.dumps(result.output, indent=2, ensure_ascii=False))
            self.console.print()

        elif cmd == '/clear':
            # Try new command system first, fall back to original
            try:
                handled, result_text = self._try_execute_new_command('clear', '')
                if handled and result_text:
                    self.console.print("\n[green]" + result_text + "[/green]")
                    return
            except Exception:
                pass
            # Original implementation
            self.session.conversation.clear()
            self.console.print("[green]Conversation cleared.[/green]")

        elif cmd == '/save':
            self.save_session()

        elif cmd == '/multiline':
            self.multiline_mode = not self.multiline_mode
            status = "enabled" if self.multiline_mode else "disabled"
            self.console.print(f"[green]Multiline mode {status}.[/green]")
            if self.multiline_mode:
                self.console.print("[dim]Press Meta+Enter or Esc+Enter to submit.[/dim]")

        elif cmd == '/stream' or cmd.startswith('/stream '):
            parts = raw.split(maxsplit=1)
            if len(parts) == 1:
                status = "enabled" if self.stream else "disabled"
                self.console.print(f"[green]Stream mode {status}.[/green]")
                return

            action = parts[1].strip().lower()
            if action in {"on", "true", "1", "enable", "enabled"}:
                self.stream = True
            elif action in {"off", "false", "0", "disable", "disabled"}:
                self.stream = False
            elif action == "toggle":
                self.stream = not self.stream
            else:
                self.console.print("[red]Usage: /stream [on|off|toggle][/red]")
                return

            status = "enabled" if self.stream else "disabled"
            self.console.print(f"[green]Stream mode {status}.[/green]")

        elif cmd == '/render-last':
            rendered = self._render_last_assistant_message()
            if not rendered:
                self.console.print("[yellow]No assistant response available to render.[/yellow]")

        elif cmd.startswith('/load'):
            parts = command.strip().split(maxsplit=1)
            if len(parts) < 2:
                self.console.print("[red]Usage: /load <session-id>[/red]")
            else:
                session_id = parts[1]
                self.load_session(session_id)

        elif cmd == '/skill':
            self._handle_skill_command()

        elif cmd == '/context':
            # Populate command context config for context analysis
            self.command_context.config["provider"] = self.provider
            self.command_context.config["model"] = self.provider.model
            self.command_context.config["tool_schemas"] = [
                spec.to_dict() if hasattr(spec, "to_dict") else {
                    "name": spec.name,
                    "description": spec.description,
                    "input_schema": dict(spec.input_schema) if hasattr(spec.input_schema, "keys") else spec.input_schema,
                }
                for spec in self.tool_registry.list_specs()
            ]
            self.command_context.config["system_prompt"] = ""
            # Try new command system
            try:
                handled, result_text = self._try_execute_new_command('context', '')
                if handled and result_text:
                    self.console.print(Markdown(result_text))
                    return
            except Exception:
                pass
            self.console.print("[yellow]/context analysis unavailable in this context.[/yellow]")

        elif cmd == '/compact':
            # Populate command context config for compact
            self.command_context.config["provider"] = self.provider
            self.command_context.config["model"] = self.provider.model
            self.command_context.config["system_prompt"] = ""
            # Try new command system
            try:
                handled, result_text = self._try_execute_new_command('compact', '')
                if handled and result_text:
                    self.console.print("\n[green]" + result_text + "[/green]")
                    return
            except Exception:
                pass
            # Simple fallback: just clear conversation
            self.session.conversation.clear()
            self.console.print("[green]Conversation cleared.[/green]")

        else:
            if raw.startswith("/"):
                if self._try_run_skill_slash(raw):
                    return
            self.console.print(f"[red]Unknown command: {command}[/red]")

    def _try_run_skill_slash(self, raw: str) -> bool:
        text = raw.strip()
        if not text.startswith("/"):
            return False
        body = text[1:]
        if not body:
            return False
        if body.split(maxsplit=1)[0].lower() in {c.lstrip("/").lower() for c in self._built_in_commands if c != "/"}:
            return False

        parts = body.split(maxsplit=1)
        skill_name = parts[0].strip()
        args = parts[1] if len(parts) > 1 else ""
        if not skill_name:
            return False

        try:
            result = self.tool_registry.dispatch(
                ToolCall(name="Skill", input={"skill": skill_name, "args": args}),
                self.tool_context,
            )
        except Exception as e:
            self.console.print(f"[red]Skill error: {e}[/red]")
            return True

        payload = result.output if isinstance(result.output, dict) else {}
        if result.is_error or not payload.get("success"):
            err = payload.get("error") if isinstance(payload.get("error"), str) else "Unknown skill error"
            self.console.print(f"[red]{err}[/red]")
            return True

        self.console.print(f"[dim]Launching skill: {payload.get('commandName', skill_name)}[/dim]")
        meta_parts: list[str] = []
        loaded = payload.get("loadedFrom")
        if isinstance(loaded, str) and loaded:
            meta_parts.append(f"source={loaded}")
        model = payload.get("model")
        if isinstance(model, str) and model:
            meta_parts.append(f"model={model}")
        tools = payload.get("allowedTools")
        if isinstance(tools, list) and tools:
            shown = ", ".join(str(t) for t in tools[:6])
            more = f" (+{len(tools) - 6})" if len(tools) > 6 else ""
            meta_parts.append(f"tools={shown}{more}")
        if meta_parts:
            self.console.print(f"[dim]{' · '.join(meta_parts)}[/dim]")

        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            self.console.print("[red]Skill produced empty prompt[/red]")
            return True

        self.chat(prompt)
        return True

    def show_help(self):
        """Show help message."""
        help_text = """
**Available Commands:**

- `/` - Show all commands and skills
- `/help` - Show this help message
- `/exit`, `/quit`, `/q` - Exit the REPL
- `/clear`, `/reset`, `/new` - Clear conversation history
- `/save` - Save current session
- `/load <session-id>` - Load a previous session
- `/multiline` - Toggle multiline input mode
- `/stream [on|off|toggle]` - Toggle live response rendering
- `/render-last` - Re-render the last assistant reply as Markdown
- `/tools` - List available built-in tools
- `/tool <name> <json>` - Run a tool directly
- `/skills` - List all available skills
- `/init` - Create CLAUDE.md file for the project
- `/cost` - Show session cost and usage
- `/compact` - Compact conversation to save context space

**Usage:**
- Type your message and press Enter to chat
- Use Tab for command completion
- Press Ctrl+C to interrupt current operation
- Press Ctrl+D to exit
- Use `/multiline` for multi-paragraph inputs
"""
        self.console.print(Markdown(help_text))

    def _handle_skill_command(self) -> None:
        """Handle /skill command - list all available skills."""
        try:
            from src.skills.loader import get_all_skills

            cwd = self.tool_context.cwd or self.tool_context.workspace_root
            skills = list(get_all_skills(project_root=cwd))
            skills.sort(key=lambda s: s.name.lower())

            if not skills:
                self.console.print("\n[bold]Available Skills:[/bold]")
                self.console.print("[dim]No skills found.[/dim]")
                self.console.print("[dim]Create skills in ~/.kiba/skills/ or ~/.claude/skills/ or .kiba/skills/ in your project.[/dim]")
                return

            # Group skills by source
            from collections import defaultdict
            by_source: dict[str, list] = defaultdict(list)
            for s in skills:
                loaded = getattr(s, "loaded_from", "") or "unknown"
                by_source[loaded].append(s)

            self.console.print(f"\n[bold]Available Skills ({len(skills)}):[/bold]")
            for source in sorted(by_source.keys()):
                source_skills = by_source[source]
                self.console.print(f"\n[cyan]{source.title()} Skills:[/cyan]")
                for s in source_skills:
                    desc = (getattr(s, "description", None) or "").strip()
                    user_invocable = getattr(s, "user_invocable", True)
                    inv_str = "" if user_invocable else " [dim](not user-invocable)[/dim]"
                    self.console.print(f"  [green]/{s.name}[/green]{inv_str}")
                    if desc:
                        self.console.print(f"    [dim]{desc}[/dim]")
            self.console.print()
        except Exception as e:
            self.console.print(f"[red]Error loading skills: {e}[/red]")

    def _is_recoverable_tool_error(self, tool_name: str, tool_output) -> bool:
        if not isinstance(tool_name, str):
            return False
        if not isinstance(tool_output, dict):
            return False
        name = tool_name.strip().lower()
        err = tool_output.get("error")
        if not isinstance(err, str):
            return False
        e = err.lower()
        if name == "read" and e.startswith("file not found:"):
            p = err.split(":", 2)[-1].strip()
            if "/.kiba/skills/" in p or "\\.kiba\\skills\\" in p or "/.claude/skills/" in p or "\\.claude\\skills\\" in p:
                return True
        return False

    def _provider_uses_system_kwarg(self) -> bool:
        return isinstance(self.provider, (AnthropicProvider, MinimaxProvider))

    def _build_direct_stream_payload(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        style_name = getattr(self.tool_context, "output_style_name", None)
        style_dir = getattr(self.tool_context, "output_style_dir", None)
        style_prompt = resolve_output_style(style_name, style_dir).prompt

        if self._provider_uses_system_kwarg():
            return self.session.conversation.get_messages(), (
                {"system": style_prompt} if style_prompt.strip() else {}
            )

        messages: list[dict[str, Any]] = []
        for msg in self.session.conversation.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
        if style_prompt.strip():
            messages = [{"role": "system", "content": style_prompt}, *messages]
        return messages, {}

    def _should_try_direct_stream(self, user_input: str) -> bool:
        if not self.stream:
            return False
        text = user_input.strip().lower()
        if not text or text.startswith("/"):
            return False
        if len(text) > 240:
            return False

        code_task_markers = (
            "/", "\\", "src/", "tests/", ".py", ".ts", ".md",
            "file", "files", "read", "write", "edit", "modify", "change",
            "search", "grep", "glob", "bash", "shell", "command", "run",
            "test", "fix", "bug", "refactor", "repo", "repository",
            "project", "workspace", "folder", "directory", "function",
            "class", "module", "code", "implementation", "readme",
            "pyproject", "package.json", "git", "commit", "diff", "tool",
            "文件", "代码", "仓库", "项目", "目录", "读取", "写入", "修改",
            "搜索", "运行", "测试", "修复", "命令", "工具", "函数", "类",
        )
        return not any(marker in text for marker in code_task_markers)

    def _stream_direct_response(self, on_text_chunk=None) -> str | None:
        streamed_chunks: list[str] = []

        try:
            api_messages, call_kwargs = self._build_direct_stream_payload()
            stream_iter = self.provider.chat_stream(api_messages, tools=None, **call_kwargs)
            for chunk in stream_iter:
                if not chunk:
                    continue
                streamed_chunks.append(chunk)
                if on_text_chunk is not None:
                    on_text_chunk(chunk)
        except Exception:
            # Safe fallback: only fall back when nothing has been emitted yet.
            if not streamed_chunks:
                return None
            raise

        if not streamed_chunks:
            return None

        full_response = "".join(streamed_chunks)
        self.session.conversation.add_assistant_message(full_response)
        return full_response

    def _get_last_assistant_text(self) -> str | None:
        for message in reversed(self.session.conversation.messages):
            if message.role != "assistant":
                continue
            content = message.content
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    block_type = getattr(block, "type", None)
                    if block_type == "text":
                        text = getattr(block, "text", "")
                        if isinstance(text, str) and text:
                            parts.append(text)
                joined = "".join(parts).strip()
                if joined:
                    return joined
        return None

    def _render_last_assistant_message(self) -> bool:
        text = self._get_last_assistant_text()
        if not text:
            return False
        self.console.print("\n[bold]Last Assistant Response[/bold]")
        self.console.print(Markdown(text))
        self.console.print()
        return True

    def _expand_mentions(self, text: str) -> str:
        """Expand `@path` tokens by inlining the referenced file's contents (Claude Code @-mentions)."""
        import re
        cwd = self.tool_context.cwd or self.tool_context.workspace_root
        additions = []
        for m in re.finditer(r"(?<![\w@])@([^\s]+)", text or ""):
            raw = m.group(1).rstrip(".,;:)")
            try:
                p = Path(raw).expanduser()
                if not p.is_absolute():
                    p = Path(cwd) / raw
                if p.is_file():
                    content = p.read_text(errors="replace")[:20000]
                    additions.append(f"\n\n--- @{raw} ---\n{content}")
            except Exception:
                pass
        return (text or "") + "".join(additions)

    def execute(self, prompt: str, max_turns: int = 30, images=None):
        """Run one agent turn and RETURN the AgentLoopResult (no printing/rendering).

        Shared by the SDK and headless mode. Fires UserPromptSubmit/Stop hooks and saves
        the session. Multi-turn: call repeatedly on the same REPL to keep conversation state.
        """
        hr = getattr(self, "hook_runner", None)
        if hr is not None and hr.has("UserPromptSubmit"):
            up = hr.run("UserPromptSubmit", {"prompt": prompt})
            if up.blocked:
                raise RuntimeError(up.message_text or "blocked by UserPromptSubmit hook")
            if up.context_text:
                prompt = f"{prompt}\n\n{up.context_text}"
        prompt = self._expand_mentions(prompt)
        if images:
            self.session.conversation.add_user_message_with_images(prompt, images)
        else:
            self.session.conversation.add_user_message(prompt)
        result = run_agent_loop(
            conversation=self.session.conversation,
            provider=self.provider,
            tool_registry=self.tool_registry,
            tool_context=self.tool_context,
            max_turns=max_turns,
            stream=False,
        )
        try:
            self.session.save()
        except Exception:
            pass
        if hr is not None and hr.has("Stop"):
            hr.run("Stop", {"response": result.response_text})
        return result

    def run_headless(self, prompt: str, output_format: str = "text", max_turns: int = 30, images=None) -> int:
        """Run a single prompt non-interactively, print the result, and return an exit code.

        Powers `kiba -p '...'` and piped stdin. Keeps stdout clean — plain text, or a
        JSON envelope with --output-format json — so KIBA can be scripted, cron'd, driven
        by the watchdog, or embedded via the SDK. Tool/streaming chrome is suppressed.
        """
        hr = getattr(self, "hook_runner", None)
        if hr is not None and hr.has("SessionStart"):
            hr.run("SessionStart", {"source": "headless"})
        if hr is not None and hr.has("UserPromptSubmit"):
            up = hr.run("UserPromptSubmit", {"prompt": prompt})
            if up.blocked:
                print(up.message_text or "blocked by UserPromptSubmit hook", file=sys.stderr)
                return 1
            if up.context_text:
                prompt = f"{prompt}\n\n{up.context_text}"
        prompt = self._expand_mentions(prompt)
        if images:
            self.session.conversation.add_user_message_with_images(prompt, images)
        else:
            self.session.conversation.add_user_message(prompt)
        try:
            result = run_agent_loop(
                conversation=self.session.conversation,
                provider=self.provider,
                tool_registry=self.tool_registry,
                tool_context=self.tool_context,
                max_turns=max_turns,
                stream=False,
                verbose=False,
            )
        except Exception as e:
            print(f"kiba: error: {e}", file=sys.stderr)
            return 1

        try:
            self.session.save()
        except Exception:
            pass

        text = result.response_text or ""
        if hr is not None and hr.has("Stop"):
            hr.run("Stop", {"response": text})
        if hr is not None and hr.has("SessionEnd"):
            hr.run("SessionEnd", {"reason": "headless_complete"})
        if output_format == "json":
            usage = result.usage or {}
            print(json.dumps({
                "result": text,
                "session_id": self.session.session_id,
                "num_turns": getattr(result, "num_turns", None),
                "usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
                "model": getattr(self.provider, "model", None),
                "provider": self.provider_name,
            }, ensure_ascii=False))
        else:
            print(text)
        return 0

    def chat(self, user_input: str, max_turns: int = 20):
        """Send message to LLM and display response.

        Args:
            user_input: The user message to send.
            max_turns: Maximum number of tool call turns (default 20, higher for complex commands).
        """
        # UserPromptSubmit hooks — may block the prompt or inject extra context
        hr = getattr(self, "hook_runner", None)
        if hr is not None and hr.has("UserPromptSubmit"):
            up = hr.run("UserPromptSubmit", {"prompt": user_input})
            if up.blocked:
                self.console.print(f"[red]⛔ {up.message_text or 'Prompt blocked by hook'}[/red]")
                return
            if up.context_text:
                user_input = f"{user_input}\n\n{up.context_text}"

        # Add user message
        self.session.conversation.add_user_message(user_input)

        try:
            self.console.print("\n[bold]Assistant[/bold]")

            stream_started = False

            def _stop_status_once() -> None:
                nonlocal stream_started
                if self._current_status is not None and not stream_started:
                    try:
                        self._current_status.stop()
                    except Exception:
                        pass
                stream_started = True

            def on_event(ev: ToolEvent) -> None:
                if ev.kind == "tool_use":
                    summary = summarize_tool_use(ev.tool_name, ev.tool_input or {})
                    if isinstance(summary, str) and summary:
                        summary = self._shorten_path_text(summary)
                    suffix = f" [dim]({summary})[/dim]" if summary else ""
                    self.console.print(f"[dim]•[/dim] [cyan]{ev.tool_name}[/cyan]{suffix} [dim]running...[/dim]")
                    return
                if ev.kind == "tool_result":
                    if ev.is_error:
                        if self._is_recoverable_tool_error(ev.tool_name, ev.tool_output):
                            return
                        msg = ""
                        if isinstance(ev.tool_output, dict) and isinstance(ev.tool_output.get("error"), str):
                            msg = ev.tool_output["error"]
                        self.console.print(f"[red]  ↳ {msg or 'Error'}[/red]")
                        return
                    msg = summarize_tool_result(ev.tool_name, ev.tool_output)
                    if isinstance(msg, str):
                        prefix = f"{ev.tool_name} · "
                        if msg.startswith(prefix):
                            msg = msg[len(prefix):]
                        msg = self._shorten_path_text(msg)
                    self.console.print(f"[dim]  ↳ {msg}[/dim]")
                    return
                if ev.kind == "tool_error":
                    msg = ev.error or "Error"
                    self.console.print(f"[red]  ↳ {msg}[/red]")

            def on_text_chunk(chunk: str) -> None:
                if not chunk:
                    return
                _stop_status_once()
                self.console.print(chunk, end="", markup=False, highlight=False, soft_wrap=True)

            if self._should_try_direct_stream(user_input):
                self._current_status = self.console.status(f"[dim]{random.choice(KIBA_STATUS_WORDS)}…[/dim]", spinner="dots")
                with self._current_status:
                    direct_response = self._stream_direct_response(on_text_chunk=on_text_chunk)
                self._current_status = None
                if direct_response is not None:
                    self.console.print("\n")
                    return

            # Use agent loop with tools for any provider that supports it
            self._current_status = self.console.status(f"[dim]{random.choice(KIBA_STATUS_WORDS)}…[/dim]", spinner="dots")
            with self._current_status:
                result = run_agent_loop(
                    conversation=self.session.conversation,
                    provider=self.provider,
                    tool_registry=self.tool_registry,
                    tool_context=self.tool_context,
                    max_turns=max_turns,
                    stream=self.stream,
                    verbose=False,
                    on_event=on_event,
                    on_text_chunk=on_text_chunk if self.stream else None,
                )
            self._current_status = None

            # Record usage to cost tracker
            if result.usage:
                input_tokens = result.usage.get("input_tokens", 0)
                output_tokens = result.usage.get("output_tokens", 0)
                if input_tokens > 0 or output_tokens > 0:
                    self.cost_tracker.record(
                        f"turn_{result.num_turns}_tokens",
                        input_tokens + output_tokens
                    )
                    # Also update command context for new commands
                    if hasattr(self, 'command_context') and self.command_context:
                        self.command_context.cost_tracker = self.cost_tracker

            if self.stream and stream_started:
                self.console.print()
                self.console.print()
            else:
                self.console.print(Markdown(result.response_text))
                self.console.print("\n")

            if hr is not None and hr.has("Stop"):
                hr.run("Stop", {"response": result.response_text})

        except Exception as e:
            error_str = str(e)

            # Check for authentication errors
            if "401" in error_str or "authentication" in error_str.lower() or "令牌" in error_str:
                self.console.print(f"\n[red]❌ Authentication Error: {e}[/red]")
                self.console.print("\n[yellow]Your API key appears to be invalid or expired.[/yellow]")

                # Ask if user wants to reconfigure
                from rich.prompt import Prompt
                choice = Prompt.ask(
                    "\nWould you like to reconfigure your API key now?",
                    choices=["y", "n"],
                    default="y"
                )

                if choice == "y":
                    self._handle_relogin()
                else:
                    self.console.print("\n[dim]You can run [bold]kiba login[/bold] later to update your API key.[/dim]")
            else:
                # Generic error handling
                self.console.print(f"\n[red]Error: {e}[/red]")
                import traceback
                traceback.print_exc()

    def _handle_relogin(self):
        """Handle re-authentication when API key fails."""
        from rich.prompt import Prompt
        from src.config import set_api_key, set_default_provider
        from src.providers import PROVIDER_INFO

        self.console.print("\n[bold blue]🔑 Reconfigure API Key[/bold blue]\n")

        # Show available providers and defaults
        provider_names = list(PROVIDER_INFO.keys())
        self.console.print("[bold]Available providers:[/bold]")
        for name, info in PROVIDER_INFO.items():
            self.console.print(f"  [cyan]{name}[/cyan] - {info['label']} (default model: {info['default_model']})")
        self.console.print()

        # Select provider
        provider = Prompt.ask(
            "Select LLM provider",
            choices=provider_names,
            default=self.provider_name if self.provider_name in provider_names else "anthropic"
        )

        info = PROVIDER_INFO[provider]

        # Prefer the user's ALREADY-SAVED settings as defaults so reconfiguring
        # doesn't silently reset a custom Base URL / model (e.g. a z.ai endpoint).
        try:
            saved = get_provider_config(provider) or {}
        except Exception:
            saved = {}
        saved_base_url = saved.get("base_url") or info["default_base_url"]
        saved_model = saved.get("default_model") or info["default_model"]

        # Input API Key
        api_key = Prompt.ask(
            f"Enter {provider.upper()} API Key",
            password=True
        )

        if not api_key:
            self.console.print("\n[red]Error: API Key cannot be empty[/red]")
            return

        # Optional: Base URL (defaults to your saved value)
        self.console.print(f"\n[dim]Default:[/dim] {saved_base_url}")
        base_url = Prompt.ask(
            f"{provider.upper()} Base URL",
            default=saved_base_url
        )

        # Optional: Default Model (defaults to your saved value)
        self.console.print(f"\n[dim]Available models:[/dim] {', '.join(info['available_models'])}")
        self.console.print(f"[dim]Default:[/dim] [bold]{saved_model}[/bold]")
        default_model = Prompt.ask(
            f"{provider.upper()} Default Model",
            default=saved_model
        )

        # Save configuration
        set_api_key(provider, api_key=api_key, base_url=base_url, default_model=default_model)
        set_default_provider(provider)

        self.console.print(f"\n[green]✓ {provider.upper()} API Key updated successfully![/green]\n")

        # Reinitialize provider
        from src.config import get_provider_config
        from src.providers import get_provider_class

        config = get_provider_config(provider)
        provider_class = get_provider_class(provider)

        self.provider = provider_class(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model=config.get("default_model")
        )
        self.provider_name = provider

        self.console.print("[green]✓ Provider reinitialized. You can continue chatting![/green]\n")

    def save_session(self):
        """Save current session."""
        self.session.save()
        self.console.print(f"[green]Session saved: {self.session.session_id}[/green]")

    def load_session(self, session_id: str):
        """Load a previous session.

        Args:
            session_id: Session ID to load
        """
        from src.agent import Session

        loaded_session = Session.load(session_id)
        if loaded_session is None:
            self.console.print(f"[red]Session not found: {session_id}[/red]")
            return

        # Replace current session
        self.session = loaded_session
        self.console.print(f"[green]Session loaded: {session_id}[/green]")
        self.console.print(f"[dim]Provider: {loaded_session.provider}, Model: {loaded_session.model}[/dim]")
        self.console.print(f"[dim]Messages: {len(loaded_session.conversation.messages)}[/dim]")

        # Show conversation history
        if loaded_session.conversation.messages:
            self.console.print("\n[bold]Conversation History:[/bold]")
            for msg in loaded_session.conversation.messages[-5:]:  # Show last 5 messages
                role_color = "blue" if msg.role == "user" else "green"
                self.console.print(f"[{role_color}]{msg.role}[/{role_color}]: {msg.content[:100]}...")
