#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Creating local virtual environment..."
  python3 -m venv .venv
fi

if ! .venv/bin/python -c "import streamlit, yaml, pydantic" >/dev/null 2>&1; then
  echo "Installing project dependencies..."
  .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/streamlit run app.py
