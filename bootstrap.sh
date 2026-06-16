#!/usr/bin/env bash
# Kiba one-line web installer.
#   curl -fsSL https://raw.githubusercontent.com/STO-Traders/KIBA/main/bootstrap.sh | bash
#
# Clones (or updates) Kiba, then runs the normal installer + setup wizard.
# Bypasses macOS Gatekeeper entirely since nothing is "downloaded & opened".
set -euo pipefail

REPO_URL="${KIBA_REPO:-https://github.com/STO-Traders/KIBA.git}"
DEST="${KIBA_DIR:-$HOME/Kiba}"

cyan(){ printf "\033[1;36m%s\033[0m\n" "$1"; }
yellow(){ printf "\033[1;33m%s\033[0m\n" "$1"; }
red(){ printf "\033[1;31m%s\033[0m\n" "$1"; }

command -v git >/dev/null 2>&1 || { red "git is required. Install Xcode Command Line Tools: xcode-select --install"; exit 1; }

if [ -d "$DEST/.git" ]; then
  yellow "Updating existing Kiba at $DEST …"
  git -C "$DEST" pull --ff-only || yellow "(couldn't fast-forward; using current copy)"
else
  cyan "Cloning Kiba into $DEST …"
  git clone --depth 1 "$REPO_URL" "$DEST"
fi

cd "$DEST"
exec bash ./install.sh
