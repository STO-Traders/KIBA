#!/usr/bin/env bash
# Double-click this file on macOS to install Kiba (no terminal knowledge needed).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
bash ./install.sh
echo
read -n 1 -s -r -p "Press any key to close this window…"
echo
