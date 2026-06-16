# 🐺 KIBA — Editor Integrations

Run the KIBA agent from your editor. Each integration drives your existing KIBA install
via headless mode — no model is bundled. Install + configure KIBA first (`kiba setup`).

| Editor | Folder | Build → install |
|---|---|---|
| **VS Code** | [`vscode/`](vscode/) | `vsce package` → install the `.vsix` |
| **Cursor** | [`vscode/`](vscode/) | the **same** `.vsix` — Cursor is a VS Code fork and runs VS Code extensions |
| **JetBrains** (IntelliJ · PyCharm · WebStorm · Rider · GoLand · CLion) | [`jetbrains/`](jetbrains/) | `gradle buildPlugin` → install the `.zip` from disk |

**Common actions:** Ask KIBA · Ask about Selection · Run on Current File (autonomous).
VS Code / Cursor also add **Open KIBA Terminal**.
