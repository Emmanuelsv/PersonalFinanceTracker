# FinanzasPersonales — AGENTS.md

## Project overview

Personal finance management app (Spanish, single-user MVP). Greenfield — `diseno-app-finanzas-personales.md` is the authoritative design document.

## Stack

| Component | Choice |
|---|---|
| Language | Python 3.12 |
| Services | FastAPI (internal), Streamlit (dashboard) |
| ORM | SQLModel (over SQLAlchemy) |
| DB | SQLite (MVP) → PostgreSQL (future) |
| Scheduler | APScheduler (MVP) → Celery+Redis (future) |
| Deps mgmt | `uv` or `poetry` — `pyproject.toml` is source of truth |
| Lint | `ruff` |
| Type check | `mypy --strict` on `domain/` and `application/` |
| Test | `pytest` + `pytest-cov` |
| CI | GitHub Actions (ruff → mypy → pytest --cov) |

## Architecture

Clean Architecture (Ports & Adapters). Package layout under `src/finanzas/`:

```
domain/          # entities, value_objects, exceptions — no external deps
application/     # use_cases, ports (interfaces), services (CalculadoraFinanciera)
infrastructure/  # db, repositories, email, bancos, scheduler
interfaces/      # cli, telegram_bot, api, dashboard
config/          # Pydantic Settings from env vars
```

**Cardinal rule:** `domain/` must never import from `infrastructure/` or `interfaces/`. Business logic lives in use cases, not in handlers/endpoints.

## Key design decisions

- **Categories are a DB table** (not Python enums) — managed via the app, no code changes needed to add new ones.
- **Money uses `Decimal`** — never `float` for currency.
- **Banco connector** is a pluggable adapter via `application/ports/` — `ConectorSimulado` for dev/tests, real one later.
- **Config** via Pydantic Settings reading env vars; `.env` is gitignored, only `.env.example` in repo.
- **Logging** structured (JSON), no secrets in logs.
- **Domain exceptions** (`MovimientoInvalidoError`, `CategoriaInexistenteError`) — caught at interface layer, translated to user-friendly messages.
- **Deduplication** via deterministic `hash_conciliacion` (fecha+valor+descripción+cuenta).
- **Conventional Commits** for commit messages.

## Commands (to be created)

```bash
uv sync              # install deps
ruff check           # lint
mypy src/            # type check
pytest               # run tests
pytest --cov         # test with coverage
pytest tests/unit/   # single category
```

## Testing strategy

- **Unit tests** — `domain/` + `application/`, no IO, fixtures/factories for Movimiento
- **Integration** — SQLite in-memory, mocked SMTP/Telegram
- **E2E** — full flows (Telegram → DB → report), a few critical paths only
- **Target**: ≥90% `domain/`, ≥80% `application/`, no strict target on `interfaces/`
- **Naming**: `test_<behavior>_when_<condition>` (e.g. `test_balance_es_negativo_cuando_gastos_superan_ingresos`)

## Seed data

17 initial categories (Transporte, Comida, Clases particulares, etc.) seeded via script in `scripts/`, not hardcoded.

## Implementation phases

| Phase | Focus |
|---|---|
| 0 | Structure, config, model, migrations, domain tests |
| 1 | Use cases, CLI, Telegram bot, CSV import |
| 2 | CalculadoraFinanciera, Streamlit dashboard, weekly email report |
| 3 | ConectorSimulado, conciliación, deduplication |
| 4+ | Real bank integration, Celery, PostgreSQL, multi-currency, multi-user |
