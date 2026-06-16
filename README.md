<div align="center">

# 🐺 KIBA

**A self-installing AI coding agent for your terminal.**

One command installs everything. Works on **macOS · Linux · Windows**.
Runs on **Claude, GPT, or GLM** — your key, your model.

[Install](#-install) · [First run](#-first-run) · [Usage](#-using-kiba) · [Providers](#-providers) · [Troubleshooting](#-troubleshooting)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Platforms](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-success?style=for-the-badge)

![Kiba streaming](assets/kiba-stream.gif)

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

## 🚀 First run

The installer finishes by launching a **setup wizard**. Pick a provider preset, paste your
API key, and Kiba **live-tests the key before saving** — so you know it works immediately.

Re-run the wizard any time:

```bash
kiba setup
```

---

## 🐺 Using Kiba

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

## 🔌 Providers

The wizard offers presets so you never hand-type an endpoint:

| Preset | You provide | Routed to |
|---|---|---|
| **GLM — z.ai Coding Plan** *(recommended)* | a z.ai API key | Anthropic-compatible endpoint, model `glm-5.2` |
| **Claude — Anthropic** | an `sk-ant-…` key | `api.anthropic.com` |
| **OpenAI — GPT** | an `sk-…` key | `api.openai.com` |
| **Custom / advanced** | provider, base URL, model | anything |

> **Running GLM via a z.ai Coding Plan (Lite/Pro/Max)?** Use the **`anthropic`** provider with
> base URL `https://api.z.ai/api/anthropic` and model `glm-5.2`. The GLM preset configures this
> for you automatically. *(Don't use the `glm` provider for a z.ai key — it routes to the
> mainland `bigmodel.cn` endpoint and ignores your base URL.)*

---

## 📦 Other install options

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

## 🙏 Credits & license

Kiba is a personal build on top of the open-source
[**Clawd-Code**](https://github.com/GPT-AGI/Clawd-Code) — a Python reimplementation of
Claude Code's architecture. Released under the **[MIT License](LICENSE)**.
