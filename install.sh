#!/usr/bin/env bash
# Kiba installer — macOS / Linux
# Installs uv + Python 3.11, builds the venv, installs Kiba, then runs the setup wizard.
set -euo pipefail

cyan(){ printf "\033[1;36m%s\033[0m\n" "$1"; }
green(){ printf "\033[1;32m%s\033[0m\n" "$1"; }
yellow(){ printf "\033[1;33m%s\033[0m\n" "$1"; }
red(){ printf "\033[1;31m%s\033[0m\n" "$1"; }

# Work from the folder this script lives in (the unzipped Kiba directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

cyan "🐺  Installing Kiba …"

# 1) ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
  yellow "Installing uv (Python toolchain manager) …"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# uv installs to ~/.local/bin (or ~/.cargo/bin on older versions)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  red "uv is installed but not on PATH yet. Close this window, open a new terminal, and re-run ./install.sh"
  exit 1
fi
green "uv ready  ($(uv --version))"

# 2) create the virtual environment (uv auto-downloads Python 3.11)
yellow "Creating the Python 3.11 environment …"
uv venv --python 3.11

# 3) install dependencies + the kiba command (editable)
yellow "Installing dependencies …"
uv pip install -r requirements.txt
uv pip install -e .
green "Kiba installed."

KIBA_BIN="$SCRIPT_DIR/.venv/bin/kiba"

# 4) run the guided setup wizard if we're in an interactive terminal
if [ -t 0 ] && [ -t 1 ]; then
  echo
  cyan "Launching the setup wizard …"
  "$KIBA_BIN" setup || true
else
  yellow "Non-interactive shell detected — configure later with:  kiba setup"
fi

# 5) summary + convenience alias
green "
✅  Kiba is ready!"
cat <<EOF

Start Kiba any time with:
  cd "$SCRIPT_DIR"
  source .venv/bin/activate
  kiba --stream

Optional — type 'kiba' from anywhere (adds a shell alias):
  echo 'alias kiba="$KIBA_BIN"' >> ~/.zshrc && source ~/.zshrc

Re-run setup later with:  kiba setup
EOF
