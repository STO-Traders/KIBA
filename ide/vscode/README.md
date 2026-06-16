# 🐺 KIBA — VS Code Extension

Use the KIBA agent inside VS Code. It drives your existing KIBA install via headless mode —
no model is bundled.

## Commands (Cmd/Ctrl+Shift+P → "KIBA:")
- **KIBA: Ask** — ask a question (⌘⌥K / Ctrl+Alt+K)
- **KIBA: Ask about Selection** — right-click a selection → asks with that code as context
- **KIBA: Run on Current File (autonomous)** — give a task; KIBA edits the file (auto-approve)
- **KIBA: Open Terminal** — opens a terminal running `kiba --stream`

Output appears in the **KIBA** output channel.

## Settings
| Setting | Default | Meaning |
|---|---|---|
| `kiba.binaryPath` | `kiba` | Path to the `kiba` executable. On macOS that's usually `~/Documents/Kiba/.venv/bin/kiba`. |
| `kiba.autoApprove` | `true` | Let "Run on Current File" act autonomously (sets `KIBA_AUTO_APPROVE`; the dangerous-command blocklist still applies). |
| `kiba.maxTurns` | `30` | Max tool-call turns per request. |

## Build / install
Requires Node + [`@vscode/vsce`](https://github.com/microsoft/vscode-vsce):

```bash
cd ide/vscode
npm install -g @vscode/vsce
vsce package            # produces kiba-0.1.0.vsix
```

Then in VS Code: **Extensions → … → Install from VSIX…** and pick `kiba-0.1.0.vsix`.
Or press **F5** in this folder to launch an Extension Development Host for live debugging.

> Prerequisite: KIBA itself must be installed and configured (`kiba setup`) so the `kiba`
> command works in your shell. Set `kiba.binaryPath` if it isn't on PATH.
