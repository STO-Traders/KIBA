#!/bin/zsh
# Kiba launcher — auto-activates venv and starts the REPL, then drops to a shell
cd "$HOME/Documents/Kiba"
source .venv/bin/activate
kiba --stream
exec zsh -l
