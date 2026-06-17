# Kiba one-line web installer — Windows (PowerShell).
#   irm https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.ps1 | iex
#
# Clones (or updates) Kiba, then runs the Windows installer + setup wizard.
# Run from a normal PowerShell window — no admin needed.
$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:KIBA_REPO) { $env:KIBA_REPO } else { "https://github.com/STO-Traders/KIBA.git" }
$Dest    = if ($env:KIBA_DIR)  { $env:KIBA_DIR }  else { Join-Path $env:USERPROFILE "Kiba" }

# git is required to fetch Kiba
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git is required but not installed." -ForegroundColor Red
    Write-Host "Install it, then re-run this same command:" -ForegroundColor Yellow
    Write-Host "  winget install --id Git.Git -e --source winget" -ForegroundColor Cyan
    Write-Host "  (or download from https://git-scm.com/download/win )" -ForegroundColor Cyan
    return
}

if (Test-Path (Join-Path $Dest ".git")) {
    Write-Host "Updating existing Kiba at $Dest ..." -ForegroundColor Yellow
    git -C $Dest pull --ff-only
} else {
    Write-Host "Cloning Kiba into $Dest ..." -ForegroundColor Cyan
    git clone --depth 1 $RepoUrl $Dest
}

Set-Location $Dest

# Run the Windows installer with a bypassed policy so a locked-down machine still works.
# (Runs in a child process; it persists `kiba` onto the User PATH in the registry.)
powershell -ExecutionPolicy Bypass -File (Join-Path $Dest "install.ps1")

# Refresh THIS session's PATH from the persisted (registry) Machine + User values so
# `kiba` works immediately in the current window — no need to open a new terminal.
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = (@($machinePath, $userPath) | Where-Object { $_ }) -join ";"

# Belt-and-suspenders: make sure Kiba's Scripts dir is on this session's PATH even if
# the registry write lagged.
$scriptsDir = Join-Path $Dest ".venv\Scripts"
if ($env:Path -notlike "*$scriptsDir*") { $env:Path = "$scriptsDir;$env:Path" }

Write-Host ""
Write-Host "kiba is ready in THIS window. Try it now:" -ForegroundColor Green
Write-Host "  kiba --stream" -ForegroundColor Cyan
