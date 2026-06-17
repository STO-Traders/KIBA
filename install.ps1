# Kiba installer — Windows (PowerShell)
# Installs uv + Python 3.11, builds the venv, installs Kiba, then runs the setup wizard.
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Installing Kiba ..." -ForegroundColor Cyan

# 1) ensure uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv (Python toolchain manager) ..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv installed but not on PATH. Close this window, open a new PowerShell, and re-run install.ps1" -ForegroundColor Red
    exit 1
}
Write-Host ("uv ready  (" + (uv --version) + ")") -ForegroundColor Green

# 2) venv (uv auto-downloads Python 3.11)
Write-Host "Creating the Python 3.11 environment ..." -ForegroundColor Yellow
uv venv --python 3.11

# 3) deps + kiba command
Write-Host "Installing dependencies ..." -ForegroundColor Yellow
uv pip install -r requirements.txt
uv pip install -e .
Write-Host "Kiba installed." -ForegroundColor Green

$KibaBin = Join-Path $ScriptDir ".venv\Scripts\kiba.exe"

# 3b) put `kiba` on PATH so it works from ANY new terminal (not just an activated venv)
$ScriptsDir = Join-Path $ScriptDir ".venv\Scripts"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($null -eq $userPath) { $userPath = "" }
if ($userPath -notlike "*$ScriptsDir*") {
    [Environment]::SetEnvironmentVariable("Path", ($userPath.TrimEnd(';') + ";" + $ScriptsDir), "User")
    Write-Host "Added 'kiba' to your PATH (open a NEW terminal to use it anywhere)." -ForegroundColor Green
}
$env:Path = "$ScriptsDir;$env:Path"  # also works immediately in this window

# 3c) Desktop shortcut with the KIBA icon
try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $iconPath = Join-Path $ScriptDir "installer\assets\KIBA.ico"
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut((Join-Path $desktop "KIBA.lnk"))
    $sc.TargetPath = $KibaBin
    $sc.Arguments = "--stream"
    $sc.WorkingDirectory = $ScriptDir
    if (Test-Path $iconPath) { $sc.IconLocation = $iconPath }
    $sc.Description = "KIBA - autonomous AI coding agent"
    $sc.Save()
    Write-Host "Created a KIBA shortcut on your Desktop." -ForegroundColor Green
} catch {
    Write-Host "Could not create desktop shortcut: $_" -ForegroundColor Yellow
}

# 4) setup wizard
Write-Host "`nLaunching the setup wizard ..." -ForegroundColor Cyan
& $KibaBin setup

# 5) summary
Write-Host "`nKiba is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Start Kiba in a NEW terminal (kiba is now on your PATH):"
Write-Host "  kiba --stream"
Write-Host ""
Write-Host "Re-run setup later with:  kiba setup"
