# 🐺 KIBA — Windows Installer (`KIBA-Setup.exe`)

This folder builds a **branded GUI installer wizard** for Windows, using the KIBA logo.

## What it produces
`installer/dist/KIBA-Setup.exe` — a double-click installer that:
1. Copies KIBA into the user's profile (`%USERPROFILE%\KIBA`)
2. Runs `install.ps1` to set up `uv` + Python 3.11 + the venv + the `kiba` command
3. Creates Start Menu and (optional) Desktop shortcuts with the KIBA icon

## How to build it (on Windows)
1. Install **[Inno Setup 6](https://jrsoftware.org/isdl.php)** (free).
2. Get the KIBA source on the Windows machine:
   ```powershell
   git clone https://github.com/STO-Traders/KIBA.git
   ```
3. Open `installer\KIBA.iss` in the **Inno Setup Compiler** and click **Build**
   (or from a terminal: `iscc installer\KIBA.iss`).
4. The wizard appears at `installer\dist\KIBA-Setup.exe` — that's the shippable `wizard.exe`.

> The installer still needs internet on first run (to fetch `uv` + Python 3.11). For a
> fully offline installer, pre-bundle a `uv`/Python — ask and we'll extend the script.

## Assets (generated from `assets/KIBAlogo.png`)
- `assets/KIBA.ico` — multi-size app/setup icon
- `assets/wizard-large.bmp` (164×314) — wizard left panel
- `assets/wizard-small.bmp` (55×58) — wizard header

To regenerate them after changing the logo, re-run the Pillow snippet in the repo
(`pip install pillow`, then resize `assets/KIBAlogo.png` onto the BMP/ICO canvases).
