FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --no-cache-dir

WORKDIR /app

COPY pyproject.toml alembic.ini ./
COPY src/ src/
COPY scripts/ scripts/
COPY alembic/ alembic/

RUN uv sync --all-extras --no-dev
RUN uv pip install -e .
RUN chmod +x scripts/entrypoint.sh

CMD ["./scripts/entrypoint.sh"]
