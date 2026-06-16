"""CLI entry point for Kiba."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table


def main():
    """CLI main entry point."""
    # Quick path for --version
    if len(sys.argv) == 2 and sys.argv[1] in ['--version', '-v', '-V']:
        from src import __version__
        print(f"kiba version {__version__} (Python)")
        return 0

    parser = argparse.ArgumentParser(
        description="Kiba - Claude Code Python Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kiba setup              Guided first-time setup (recommended)
  kiba --version          Show version
  kiba login              Configure API keys
  kiba config             Show current configuration
  kiba --stream           Start REPL with live response rendering
  kiba                    Start interactive REPL
"""
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Enable live response rendering in the REPL'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # setup subcommand (guided wizard)
    setup_parser = subparsers.add_parser('setup', help='Guided first-time setup wizard')

    # login subcommand
    login_parser = subparsers.add_parser('login', help='Configure API keys')

    # config subcommand
    config_parser = subparsers.add_parser('config', help='Show current configuration')

    args = parser.parse_args()

    # Handle --version
    if args.version:
        from src import __version__
        print(f"kiba version {__version__} (Python)")
        return 0

    # Handle --config
    if args.config:
        return show_config()

    # Handle commands
    if args.command == 'setup':
        return handle_setup()
    elif args.command == 'login':
        return handle_login()
    elif args.command == 'config':
        return show_config()

    # Default: start REPL
    return start_repl(stream=args.stream)


def _show_provider_defaults_table() -> None:
    """Print a table showing available providers and their defaults."""
    from src.providers import PROVIDER_INFO

    console = Console()
    table = Table(title="Available Providers & Defaults", show_header=True, header_style="bold")
    table.add_column("Provider", style="cyan")
    table.add_column("Default Model", style="magenta")
    table.add_column("Base URL", style="green")

    for name, info in PROVIDER_INFO.items():
        table.add_row(
            f"{name} ({info['label']})",
            info["default_model"],
            info["default_base_url"],
        )

    console.print(table)
    console.print()


# Curated one-click presets for the setup wizard. Each preset pins the provider,
# base URL and model so users never hit the Base-URL footgun.
SETUP_PRESETS = [
    {
        "label": "GLM — z.ai Coding Plan",
        "blurb": "GLM-5.2 via z.ai's Anthropic-compatible endpoint (recommended)",
        "provider": "anthropic",
        "base_url": "https://api.z.ai/api/anthropic",
        "model": "glm-5.2",
        "format": "anthropic",
        "key_hint": "your z.ai API key (z.ai dashboard → API Keys)",
    },
    {
        "label": "Claude — Anthropic",
        "blurb": "Anthropic's Claude models on the official API",
        "provider": "anthropic",
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-6",
        "format": "anthropic",
        "key_hint": "your Anthropic API key (sk-ant-…)",
    },
    {
        "label": "OpenAI — GPT",
        "blurb": "OpenAI GPT models on the official API",
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.4",
        "format": "openai",
        "key_hint": "your OpenAI API key (sk-…)",
    },
    {
        "label": "Custom / advanced",
        "blurb": "Pick provider, Base URL and model manually",
        "custom": True,
    },
]


# z.ai keys look like "<32 hex>.<suffix>" — sending one to the official Anthropic or
# OpenAI endpoint is the #1 setup footgun (HTTP 400/401). We detect that shape so the
# wizard can offer to switch to the GLM — z.ai preset automatically.
_ZAI_KEY_RE = re.compile(r"[0-9a-fA-F]{32}\.[A-Za-z0-9]{8,}")


def _looks_like_zai_key(api_key: str) -> bool:
    return bool(_ZAI_KEY_RE.fullmatch((api_key or "").strip()))


def _test_api_key(fmt: str, base_url: str, model: str, api_key: str):
    """Live-test an API key with a tiny request. Returns (ok: bool, detail: str)."""
    import json as _json
    import urllib.request
    import urllib.error

    base = base_url.rstrip("/")
    if fmt == "anthropic":
        url = base + "/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "reply with ok"}],
        }
    else:  # openai-compatible
        url = base + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "reply with ok"}],
        }

    req = urllib.request.Request(
        url, data=_json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return (resp.status == 200, f"HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()[:200]
        except Exception:
            body = ""
        return (False, f"HTTP {e.code} {body}")
    except Exception as e:
        return (False, str(e))


def handle_setup():
    """Guided, preset-driven first-time setup wizard with live key validation."""
    from src.config import set_api_key, set_default_provider

    console = Console()
    console.print("\n[bold bright_cyan]🐺 Kiba Setup[/bold bright_cyan]")
    console.print("[dim]Pick a provider preset — Kiba fills in the rest.[/dim]\n")

    for i, p in enumerate(SETUP_PRESETS, 1):
        console.print(f"  [bold cyan]{i}[/bold cyan]. [bold]{p['label']}[/bold]")
        console.print(f"     [dim]{p['blurb']}[/dim]")
    console.print()

    choice = Prompt.ask(
        "Choose a setup",
        choices=[str(i) for i in range(1, len(SETUP_PRESETS) + 1)],
        default="1",
    )
    preset = SETUP_PRESETS[int(choice) - 1]

    # Advanced path → reuse the full manual flow
    if preset.get("custom"):
        return handle_login()

    provider = preset["provider"]
    base_url = preset["base_url"]
    model = preset["model"]
    fmt = preset["format"]

    console.print(f"\n[bold]{preset['label']}[/bold]")
    console.print(f"  [dim]Endpoint:[/dim] {base_url}")
    console.print(f"  [dim]Model:[/dim]    {model}\n")

    while True:
        api_key = Prompt.ask(f"Paste {preset['key_hint']}", password=True)
        if not api_key:
            console.print("[red]API key cannot be empty.[/red]")
            continue

        console.print("\n[dim]Testing your key against the endpoint…[/dim]")
        ok, detail = _test_api_key(fmt, base_url, model, api_key)
        if ok:
            console.print("[green]✓ Key works![/green]")
            break

        console.print(f"[red]✗ Key test failed:[/red] [dim]{detail}[/dim]")

        # Smart hint: a z.ai-shaped key on a non-z.ai endpoint is the #1 footgun.
        # Offer to switch to the GLM — z.ai preset and re-test the SAME key.
        if _looks_like_zai_key(api_key) and "z.ai" not in base_url:
            console.print(
                "\n[bold yellow]💡 That looks like a z.ai key[/bold yellow] "
                "[dim](format 32hex.suffix)[/dim], but this preset points at "
                f"[dim]{base_url}[/dim]."
            )
            console.print(
                "   z.ai keys must go through the [bold]GLM — z.ai Coding Plan[/bold] "
                "preset (endpoint [dim]https://api.z.ai/api/anthropic[/dim], model "
                "[dim]glm-5.2[/dim])."
            )
            if Confirm.ask(
                "   Switch to GLM — z.ai and re-test this key?", default=True
            ):
                glm = next(
                    p
                    for p in SETUP_PRESETS
                    if str(p.get("base_url", "")).startswith("https://api.z.ai")
                )
                provider, base_url, model, fmt = (
                    glm["provider"],
                    glm["base_url"],
                    glm["model"],
                    glm["format"],
                )
                preset = glm
                console.print(f"\n[bold]{glm['label']}[/bold]")
                console.print(f"  [dim]Endpoint:[/dim] {base_url}")
                console.print(f"  [dim]Model:[/dim]    {model}")
                console.print(
                    "\n[dim]Re-testing your key against the z.ai endpoint…[/dim]"
                )
                ok, detail = _test_api_key(fmt, base_url, model, api_key)
                if ok:
                    console.print("[green]✓ Key works![/green]")
                    break
                console.print(f"[red]✗ Still failing:[/red] [dim]{detail}[/dim]")

        what = Prompt.ask(
            "What now?",
            choices=["retry", "save", "cancel"],
            default="retry",
        )
        if what == "retry":
            continue
        if what == "cancel":
            console.print("[yellow]Setup cancelled. Nothing saved.[/yellow]")
            return 1
        break  # save anyway

    set_api_key(provider, api_key=api_key, base_url=base_url, default_model=model)
    set_default_provider(provider)

    console.print("\n[bold green]✓ Kiba is configured![/bold green]")
    console.print(f"  Provider: [cyan]{provider}[/cyan]  ·  Model: [magenta]{model}[/magenta]")
    console.print("\n[dim]Start chatting with:[/dim] [bold]kiba --stream[/bold]\n")
    return 0


def handle_login():
    """Interactive API configuration."""
    console = Console()
    console.print("\n[bold blue]Kiba - API Configuration[/bold blue]\n")

    # Show available providers and their defaults
    _show_provider_defaults_table()

    # Select provider
    from src.providers import PROVIDER_INFO
    provider_names = list(PROVIDER_INFO.keys())

    provider = Prompt.ask(
        "Select LLM provider",
        choices=provider_names,
        default="anthropic"
    )

    info = PROVIDER_INFO[provider]

    # Input API Key
    api_key = Prompt.ask(
        f"Enter {provider.upper()} API Key",
        password=True
    )

    if not api_key:
        console.print("\n[red]Error: API Key cannot be empty[/red]")
        return 1

    # Optional: Base URL (show default)
    console.print(f"\n[dim]Default:[/dim] {info['default_base_url']}")
    base_url = Prompt.ask(
        f"{provider.upper()} Base URL",
        default=info["default_base_url"]
    )

    # Optional: Default Model (show available options)
    console.print(f"\n[dim]Available models:[/dim] {', '.join(info['available_models'])}")
    console.print(f"[dim]Default:[/dim] [bold]{info['default_model']}[/bold]")
    default_model = Prompt.ask(
        f"{provider.upper()} Default Model",
        default=info["default_model"]
    )

    # Save configuration
    from src.config import set_api_key, set_default_provider

    set_api_key(provider, api_key=api_key, base_url=base_url, default_model=default_model)
    set_default_provider(provider)

    console.print(f"\n[green]✓ {provider.upper()} API Key saved successfully![/green]")
    console.print(f"[green]✓ Default provider set to: {provider}[/green]\n")
    return 0


def show_config():
    """Show current configuration."""
    console = Console()

    try:
        from src.config import load_config, get_config_path

        config = load_config()
        config_path = get_config_path()

        console.print(f"\n[bold]Configuration File:[/bold] {config_path}\n")
        console.print("[bold]Current Configuration:[/bold]\n")

        # Show default provider
        console.print(f"[cyan]Default Provider:[/cyan] {config.get('default_provider', 'Not set')}")

        # Show providers (without showing full API keys)
        console.print("\n[cyan]Configured Providers:[/cyan]")
        for provider_name, provider_config in config.get("providers", {}).items():
            api_key = provider_config.get("api_key", "")
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "Not set"

            console.print(f"\n  [yellow]{provider_name.upper()}:[/yellow]")
            console.print(f"    API Key: {masked_key}")
            console.print(f"    Base URL: {provider_config.get('base_url', 'Not set')}")
            console.print(f"    Default Model: {provider_config.get('default_model', 'Not set')}")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error loading configuration: {e}[/red]\n")
        return 1

    return 0


def start_repl(stream: bool = False):
    """Start interactive REPL."""
    from src.config import get_default_provider
    from src.repl import KibaREPL

    provider = get_default_provider()
    repl = KibaREPL(provider_name=provider, stream=stream)
    repl.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
