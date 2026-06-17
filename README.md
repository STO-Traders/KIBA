<div align="center">

<img src="assets/KIBAlogo.png" alt="KIBA" width="220" />

# KIBA

**An agentic AI coding platform for your terminal.**

KIBA is a full-power coding agent — it reads, writes, edits, runs commands, searches
the web, drives sub-agents, and connects to live tools over MCP. One command installs
everything. **Bring your own model:** run it on **Claude, GLM, GPT, or Minimax**.

Built for serious builders — and tuned for **trading-system & quant development**
(NinjaScript C#, Pine, Python ML), with first-class MCP connections to the tools you
already use.

Works on **macOS · Linux · Windows**.

[Install](#-install) · [What KIBA can do](#-what-kiba-can-do) · [Models & providers](#-models--providers) · [MCP connections](#-mcp-connections) · [Usage](#-using-kiba) · [Troubleshooting](#-troubleshooting)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Platforms](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-success?style=for-the-badge)

![KIBA streaming](assets/kiba-stream.gif)

</div>

---

## ⚡ Install

One line. The installer sets up everything for you — `uv`, Python 3.11, a virtual
environment, all dependencies, and the `kiba` command. **No prior setup needed.**

**macOS / Linux** — paste into **Terminal**:

```bash
curl -fsSL https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.sh | bash
```

**Windows** — paste into **PowerShell** (not Command Prompt):

```powershell
irm https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.ps1 | iex
```

> ⚠️ The bash one-liner is **macOS/Linux only**. Don't paste it into Windows PowerShell —
> use the PowerShell line above.
>
> 🪟 Windows needs **git**. If the installer says it's missing, run
> `winget install --id Git.Git -e`, reopen PowerShell, then re-run the command.

Prefer not to use a one-liner? See **[other install options](#-other-install-options)**.

---

## 🐺 What KIBA can do

KIBA isn't a chat box — it's an autonomous agent with a real tool belt and an agent loop
that plans, acts, observes, and iterates until the job is done.

- **Full file + shell toolkit** — read, write, and surgically edit files; run shell
  commands; glob and grep across your repo; fetch and search the web.
- **Sub-agents & teams** — spin up specialized agents (reviewer, researcher, builder)
  that run their own tool loops and report back, so big tasks fan out in parallel.
- **Custom agent personas** — drop a `.kiba/agents/*.md` file to define a named agent
  with its own system prompt, model, and restricted tool set.
- **Skills** — reusable, parameterized command packs in `.kiba/skills/` that teach KIBA
  repeatable workflows.
- **Plan mode** — have KIBA design an approach and get your sign-off before it touches
  anything.
- **Project awareness** — pulls in your workspace, `git status`, and `CLAUDE.md` /
  project context automatically.
- **Background & scheduled work** — `cron` tasks, long-running jobs, and git **worktree**
  isolation for parallel edits.
- **LSP-aware editing** — language-server integration for smarter code navigation.
- **Streaming REPL** — live token streaming, history, tab-completion, multi-line input,
  and saved/restored sessions.
- **43 built-in agent tools** — a complete file/shell/web/task/agent/MCP tool surface — plus anything you connect over **MCP** (see below).

### Tuned for trading & development

KIBA is a general-purpose coding platform, and it's especially strong at the kind of work
trading desks actually do: building and refactoring **NinjaTrader 8 NinjaScript (C#)**
strategies and indicators, **Pine Script**, and **Python ML / data pipelines** — then
wiring them to market tooling through MCP (e.g. a TradingView MCP server). Use the same
agent for the strategy code, the backtest harness, and the research notebook.

---

## 🧠 Models & providers

**Your key, your model.** KIBA speaks to four provider backends and is model-agnostic —
swap models any time with `kiba setup`. The setup wizard pins the provider, endpoint, and
model for you so you never hand-type an endpoint.

| Provider | Models you can run | Routed to |
|---|---|---|
| **GLM — z.ai Coding Plan** *(recommended)* | `glm-5.2`, plus the GLM‑5.x / GLM‑4.x family | z.ai Anthropic‑compatible endpoint |
| **Claude — Anthropic** | the full Claude family — **Opus 4.x**, **Sonnet 4.x**, **Haiku 4.x** (and any current model id, e.g. **Fable**) | `api.anthropic.com` |
| **OpenAI — GPT** | **GPT‑5.4** / 5.2 / **5.3‑Codex** family | `api.openai.com` |
| **Minimax** | **MiniMax‑M2.7** family | Minimax Anthropic‑compatible endpoint |
| **Custom / advanced** | any provider, base URL, and model | anything |

> Models pass through to the provider, so newer model ids work the moment they ship —
> point KIBA at it and go.

---

## 🔌 MCP connections

KIBA ships a full **Model Context Protocol** client. It connects to MCP servers over
**stdio, SSE, or streamable‑HTTP** and registers every server tool as a first‑class
`mcp__<server>__<tool>` your agent can call directly.

Declare servers in any of:

- `.mcp.json` in your project (per‑repo tools)
- `~/.kiba/mcp.json` or `~/.mcp.json` (global tools)
- `settings.json`

```jsonc
{
  "mcpServers": {
    "fs":          { "command": "uvx", "args": ["mcp-server-filesystem", "/path"] },
    "tradingview": { "command": "node", "args": ["tradingview-mcp/server.js"] },
    "remote":      { "url": "https://example.com/mcp", "type": "http" }
  }
}
```

That's how you bolt market data, brokerage tooling, databases, or any custom MCP server
straight onto the agent.

---

## 🚀 First run

The installer finishes by launching a **setup wizard**. Pick a provider preset, paste your
API key, and KIBA **live-tests the key before saving** — so you know it works immediately.

Re-run the wizard any time:

```bash
kiba setup
```

---

## 🐺 Using KIBA

```bash
# from the Kiba folder
source .venv/bin/activate        # Windows:  .venv\Scripts\activate
kiba --stream
```

Then just type your request at the `❯` prompt. Handy in-app commands:

| Command | Does |
|---|---|
| `/help` | List commands |
| `/tools` | Show available agent tools |
| `/stream` | Toggle live token streaming |
| `/exit` | Quit |

**Tip — launch `kiba` from anywhere** (macOS/Linux):

```bash
echo 'alias kiba="'"$PWD"'/.venv/bin/kiba"' >> ~/.zshrc && source ~/.zshrc
```

---

## 🔑 Provider setup notes

The wizard offers presets so you never hand-type an endpoint:

> **Running GLM via a z.ai Coding Plan (Lite/Pro/Max)?** Use the **`anthropic`** provider with
> base URL `https://api.z.ai/api/anthropic` and model `glm-5.2`. The GLM preset configures this
> for you automatically. *(Don't use the `glm` provider for a z.ai key — it routes to the
> mainland `bigmodel.cn` endpoint and ignores your base URL.)*

---

## 📦 Other install options

- **VS Code extension:** build from [`ide/vscode/`](ide/vscode/) — Ask KIBA, ask about a selection, run it autonomously on a file, or open a KIBA terminal, all from the editor.
- **Windows installer wizard:** build a branded `KIBA-Setup.exe` from [`installer/`](installer/) (Inno Setup) — double-click GUI install with the KIBA logo + Start Menu / Desktop shortcuts.
- **Zip:** download `Kiba.zip`, unzip, then:
  - **macOS:** double-click `Install Kiba (Mac).command`
  - **Windows:** double-click `Install Kiba (Windows).bat`
  - **Linux:** `bash install.sh`
- Full per-OS walkthrough: **[QUICKSTART.md](QUICKSTART.md)**

---

## 🧯 Troubleshooting

| Symptom | Fix |
|---|---|
| `fi` / `exec` / `$DEST` errors in PowerShell | You pasted the **bash** one-liner into Windows. Use the **PowerShell** one instead. |
| `git is required` (Windows) | `winget install --id Git.Git -e`, reopen PowerShell, re-run. |
| `kiba` not found after install | Activate the venv first (`source .venv/bin/activate`), or add the alias above. |
| `invalid x-api-key` with a z.ai key | Base URL must be `https://api.z.ai/api/anthropic` (provider `anthropic`), model `glm-5.2`. Re-run `kiba setup`. |
| `1113 insufficient balance` | Your z.ai **Coding Plan** lives on the Anthropic endpoint above — not the OpenAI `/paas/v4` one. |

---

## 📄 License

KIBA is a product of **STO Algo LLC**, released under the **[MIT License](LICENSE)**.
