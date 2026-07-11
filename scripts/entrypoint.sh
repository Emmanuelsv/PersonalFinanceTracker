#!/bin/bash
set -e

# Run database migrations
uv run alembic upgrade head

# Seed categories (idempotent)
uv run python -m scripts.seed_categorias

# Start the Telegram bot
exec uv run python -m finanzas.interfaces.telegram_bot.main
