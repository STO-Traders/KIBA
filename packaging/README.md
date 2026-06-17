# 🐺 KIBA — Desktop Apps & Launchers

Make KIBA open like a normal desktop app — a double-click icon, no terminal commands.

## macOS — `KIBA.app`
```bash
bash packaging/macos/build-app.sh --desktop
```
Builds `dist/KIBA.app` (with the KIBA logo icon) and drops a copy on your **Desktop**.
Double-click to launch. First run on a Mac: **right-click → Open** (it's unsigned).
It opens Terminal running KIBA.

## Windows — Desktop shortcut
**Already installed?** Make the desktop icon:
```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\Create-Desktop-Shortcut.ps1
```
**Fresh install?** You get a Desktop shortcut automatically — both `install.ps1` and the
`KIBA-Setup.exe` wizard ([`installer/`](../installer/)) create one with the KIBA icon.

Either way you end up with a **KIBA** icon on the Desktop that opens the agent.
