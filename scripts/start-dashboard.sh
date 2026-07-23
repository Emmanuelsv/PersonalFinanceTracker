#!/bin/bash
set -e
exec uv run streamlit run src/finanzas/interfaces/dashboard/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true
