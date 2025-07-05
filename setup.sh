#!/usr/bin/env bash
# Simple setup script for the BEDROT data lake project.
set -euo pipefail

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
VENV_DIR="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "Virtual environment is ready. Activate with: source $VENV_DIR/bin/activate"

