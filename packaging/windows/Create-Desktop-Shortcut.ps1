# Create a "KIBA" shortcut on the Desktop that launches KIBA, with the KIBA icon.
# Run once on a machine that already has KIBA installed:
#   powershell -ExecutionPolicy Bypass -File packaging\windows\Create-Desktop-Shortcut.ps1
$ErrorActionPreference = "Stop"

$kibaDir = Join-Path $env:USERPROFILE "Kiba"
$exe  = Join-Path $kibaDir ".venv\Scripts\kiba.exe"
$icon = Join-Path $kibaDir "installer\assets\KIBA.ico"

if (-not (Test-Path $exe)) {
    Write-Host "KIBA not found at $exe — install KIBA first (install.ps1 / KIBA-Setup.exe)." -ForegroundColor Red
    exit 1
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "KIBA.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $exe
$sc.Arguments = "--stream"
$sc.WorkingDirectory = $kibaDir
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Description = "KIBA - autonomous AI coding agent"
$sc.Save()

Write-Host "Created a KIBA shortcut on your Desktop: $lnk" -ForegroundColor Green
Write-Host "Double-click it to launch KIBA." -ForegroundColor Green
