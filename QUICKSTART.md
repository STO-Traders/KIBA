# 🐺 Kiba — Quick Start

A self-installing AI coding agent in your terminal. One installer sets up everything
(Python, dependencies, the `kiba` command) and walks you through connecting your AI provider.

You do **not** need Python, Homebrew, or any setup beforehand — the installer handles it.

---

## Fastest: one-line install

**macOS / Linux** — paste into **Terminal**:

```bash
curl -fsSL https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.sh | bash
```

**Windows** — paste into **PowerShell** (not Command Prompt):

```powershell
irm https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.ps1 | iex
```

Both clone Kiba and install everything (Python, deps, the `kiba` command), then launch
the setup wizard. On macOS, because nothing is "downloaded and opened," the one-liner
**skips the Gatekeeper warning** entirely. On Windows it needs `git` — if it says git is
missing, run `winget install --id Git.Git -e` first, then re-run the command.

> ⚠️ The bash one-liner is **macOS/Linux only** — do **not** paste it into Windows
> PowerShell (you'll get `fi`/`exec`/`$DEST` errors). Use the PowerShell one-liner above.

---

## Install from the zip

### macOS
1. Unzip `Kiba.zip`.
2. Double-click **`Install Kiba (Mac).command`**.
   - First time, macOS may say it's from an unidentified developer: **right-click → Open → Open**.
   - Still blocked? Clear the quarantine flag: `xattr -dr com.apple.quarantine "/path/to/Kiba"`
   - Or just use the one-line installer above (no warning), or run `bash install.sh` in Terminal.
3. Follow the setup wizard.

### Windows
1. Unzip `Kiba.zip`.
2. Double-click **`Install Kiba (Windows).bat`**.
   - If SmartScreen warns: **More info → Run anyway**.
3. Follow the setup wizard.

### Linux
1. Unzip `Kiba.zip`.
2. In a terminal: `cd` into the folder and run `bash install.sh`.
3. Follow the setup wizard.

---

## The setup wizard

It asks one thing: **which provider**. Pick a preset and it auto-configures the
endpoint and model — you only paste your API key, and it **live-tests** the key
before saving.

| Preset | What you need |
|--------|---------------|
| **GLM — z.ai Coding Plan** (recommended) | A z.ai API key (z.ai dashboard → API Keys). Auto-uses GLM-5.2. |
| **Claude — Anthropic** | An Anthropic key (`sk-ant-…`). |
| **OpenAI — GPT** | An OpenAI key (`sk-…`). |
| **Custom / advanced** | Manually set provider, URL, model. |

---

## Run it

```bash
# from the Kiba folder
source .venv/bin/activate        # macOS/Linux   (Windows: .venv\Scripts\activate)
kiba --stream
```

Then just type your request at the `❯` prompt.

Re-run the wizard any time with: **`kiba setup`**

---

## Tips
- **Type `kiba` from anywhere (macOS/Linux):**
  `echo 'alias kiba="'"$PWD"'/.venv/bin/kiba"' >> ~/.zshrc && source ~/.zshrc`
- Keep your API key private. If you ever leak it, revoke it in your provider's dashboard.
- Useful in-app commands: `/help`, `/tools`, `/exit`.
