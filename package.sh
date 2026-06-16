#!/usr/bin/env bash
# Build a clean, sendable Kiba.zip (excludes venv, git, caches, build junk).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUT="${1:-Kiba.zip}"
rm -f "$OUT"

zip -r "$OUT" . \
  -x '.git/*' \
  -x '.venv/*' \
  -x '*/__pycache__/*' \
  -x '*.pyc' \
  -x '*.egg-info/*' \
  -x '.vscode/*' \
  -x '.DS_Store' \
  -x "$OUT" >/dev/null

SIZE="$(du -h "$OUT" | cut -f1)"
echo "✅ Created $OUT ($SIZE)"
echo "Send that file. Recipient unzips and runs the installer for their OS:"
echo "  macOS  : double-click 'Install Kiba (Mac).command'   (or: bash install.sh)"
echo "  Windows: double-click 'Install Kiba (Windows).bat'   (or: install.ps1)"
echo "  Linux  : bash install.sh"
