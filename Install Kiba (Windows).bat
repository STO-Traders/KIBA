@echo off
REM Double-click this file on Windows to install Kiba.
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
pause
