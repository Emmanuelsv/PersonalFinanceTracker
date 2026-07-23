#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
exec "$PROJECT_ROOT/.venv/bin/python" -m streamlit run \
    "$PROJECT_ROOT/src/finanzas/interfaces/dashboard/app.py" \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true
