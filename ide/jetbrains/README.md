# 🐺 KIBA — JetBrains Plugin

Use the KIBA agent inside JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm, Rider, GoLand,
CLion, …). It drives your existing KIBA install via headless mode — no model is bundled.

## Actions (Tools ▸ KIBA, and the editor right-click menu)
- **Ask KIBA…** — ask a question
- **Ask KIBA about Selection** — uses the selected code as context
- **Run KIBA on Current File** — give a task; KIBA edits the file autonomously

Results appear in a dialog; long tasks run on a background progress indicator.

## Configure the KIBA binary
The plugin runs `kiba`. If it isn't on your PATH, set the **`KIBA_BIN`** environment
variable to the full path (e.g. `~/Documents/Kiba/.venv/bin/kiba`) before launching the IDE.

## Build (produces the installable plugin .zip)
Requires **JDK 17** and Gradle (or generate the wrapper first with `gradle wrapper`).

```bash
cd ide/jetbrains
gradle buildPlugin        # or: ./gradlew buildPlugin  (after gradle wrapper)
```

Output: `build/distributions/kiba-jetbrains-0.1.0.zip`.

## Install
In any JetBrains IDE: **Settings ▸ Plugins ▸ ⚙ ▸ Install Plugin from Disk…** → pick the
`.zip`. Restart the IDE. KIBA appears under **Tools ▸ KIBA** and the editor context menu.

> First run downloads the IntelliJ Platform SDK (~hundreds of MB) — that's normal for a
> JetBrains plugin build. Use **Run Plugin** (a Gradle task / IDE run config) to live-test
> in a sandbox IDE instance.

> Prerequisite: KIBA itself must be installed and configured (`kiba setup`).
