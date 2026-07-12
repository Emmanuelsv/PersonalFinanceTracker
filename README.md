# FinanzasPersonales

**Asistente de finanzas personales — Telegram, CLI y Dashboard**

Aplicación MVPs (single-user) para el registro, consulta y análisis de finanzas personales. Construida con **Clean Architecture (Ports & Adapters)** en Python. Disponible como bot de Telegram, interfaz de línea de comandos y dashboard web con Streamlit.

---

## ✨ Características

### Telegram Bot
| Comando | Descripción |
|---|---|
| `/start` | Conversación guiada para registrar un movimiento: selecciona tipo (ingreso/gasto), categoría, valor y descripción opcional |
| `/balance` | Resumen del mes actual: total ingresos, total gastos, neto y tasa de ahorro |
| `/listar` | Lista los movimientos del mes actual (hasta 10) con fecha, tipo, monto y descripción |

### CLI (Typer)
| Comando | Descripción |
|---|---|
| `finanzas registrar` | Registra un movimiento con tipo, categoría, fecha, valor y descripción opcional |
| `finanzas listar` | Lista movimientos filtrados por rango de fechas |
| `finanzas balance` | Muestra el balance de un mes específico |
| `finanzas importar-csv` | Importa movimientos desde un archivo CSV |

### Dashboard (Streamlit + Plotly)
- **KPIs**: Ingresos, gastos, neto y tasa de ahorro del mes seleccionado
- **Gráficos**: Ingresos vs gastos por mes (barras agrupadas), gastos por categoría (treemap + barras), evolución del patrimonio (línea), flujo de caja diario
- **Distribución porcentual** de gastos por categoría
- **Score de salud financiera** (0–100)
- **Detección de anomalías**: alerta cuando un gasto en una categoría varía >40% respecto al histórico
- **Movimientos sin categoría**: asigna categoría directamente desde el dashboard
- **Suscripciones**: costo promedio mensual de pagos recurrentes
- **Proyección**: gasto proyectado a fin de mes

### Reportes Semanales por Email
- Envío automático cada domingo a las 10:00 AM vía APScheduler + SMTP
- Resumen HTML con ingresos, gastos, desglose por categoría y recomendaciones

### Conciliación Bancaria
- Conector simulado para desarrollo/pruebas
- Deduplicación determinista mediante hash SHA-256 (`hash_conciliacion`)
- Use case `ConciliarMovimientosBanco` listo para conectar con bancos reales

### Cálculos Financieros
| Cálculo | Descripción |
|---|---|
| Balance mensual | Ingresos − Gastos = Neto, tasa de ahorro |
| Gasto por categoría | Suma de gastos agrupados por categoría |
| Gasto fijo vs variable | Clasifica por conjunto de categorías |
| Promedio mensual | Total / número de meses |
| Score de salud | 0–100 basado en tasa de ahorro, diversidad de categorías y nivel de deuda |
| Detección de anomalías | Variación >40% contra promedio histórico |
| Proyección fin de mes | Gasto proyectado basado en promedio diario |
| Costo de suscripciones | Pagos recurrentes del mismo monto entre meses |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────┐
│          Interfaces                  │
│  (Telegram Bot / CLI / Dashboard)   │
├─────────────────────────────────────┤
│          Application                 │
│  (Use Cases / Services / Ports)     │
├─────────────────────────────────────┤
│         Infrastructure               │
│  (DB / Repositorios / Email / API)  │
├─────────────────────────────────────┤
│            Domain                    │
│  (Entities / Value Objects / Exceptions)
└─────────────────────────────────────┘
```

**Regla cardinal:** `domain/` nunca importa de `infrastructure/` ni `interfaces/`. Toda la lógica de negocio vive en los casos de uso.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| ORM | SQLModel (SQLAlchemy) |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Migraciones | Alembic |
| Bot Telegram | python-telegram-bot 21+ |
| CLI | Typer |
| Dashboard | Streamlit + Plotly + Pandas |
| API (futura) | FastAPI + Uvicorn |
| Tareas programadas | APScheduler |
| Email | SMTP con STARTTLS |
| Configuración | Pydantic Settings |
| Logging | Structlog |
| Seguridad | Cryptography |
| Dependencias | `uv` |
| Linter | Ruff |
| Type checker | mypy (strict) |
| Tests | pytest + pytest-cov |

---

## 🚀 Empezar (Desarrollo Local)

### Prerrequisitos

- Python 3.12+
- `uv` ([instalar](https://docs.astral.sh/uv/#installation))

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Emmanuelsv/PersonalFinanceTracker.git
cd PersonalFinanceTracker

# Instalar dependencias
uv sync --all-extras

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu TELEGRAM_BOT_TOKEN
```

### Base de Datos

```bash
# Ejecutar migraciones
uv run alembic upgrade head

# (Opcional) Crear tablas directamente sin migraciones
uv run python -c "from finanzas.infrastructure.db.engine import crear_tablas; crear_tablas()"

# Sembrar categorías iniciales (idempotente)
uv run python -m scripts.seed_categorias
```

### Iniciar el Bot de Telegram

```bash
uv run python -m finanzas.interfaces.telegram_bot.main
```

El bot inicia un servidor HTTP de health check en el puerto `$PORT` (o `8000`) para despliegues en Render, y luego comienza a recibir mensajes vía polling.

### Iniciar el Dashboard

```bash
uv run streamlit run src/finanzas/interfaces/dashboard/app.py
```

### CLI

```bash
# Ver comandos disponibles
uv run finanzas --help

# Registrar un movimiento
uv run finanzas registrar INGRESO <categoria_id> 2026-07-01 1500000 --descripcion "Salario"

# Listar movimientos
uv run finanzas listar

# Ver balance mensual
uv run finanzas balance 2026 7

# Importar CSV
uv run finanzas importar-csv ruta/al/archivo.csv
```

---

## 📖 Uso Detallado

### Telegram Bot

1. Inicia una conversación con [@TuBot](https://t.me/) en Telegram
2. Envía `/start` para registrar un gasto o ingreso
3. Sigue la conversación guiada: tipo → categoría → valor → descripción
4. Usa `/balance` para ver el resumen del mes
5. Usa `/listar` para ver los movimientos recientes

**Formato del CSV para importar:**

```csv
fecha,tipo,valor,descripcion,categoria
2026-07-01,SALIDA,50000,Almuerzo,Comida
2026-07-02,INGRESO,2000000,Salario,Otros ingresos
```

---

## 📁 Estructura del Proyecto

```
├── .env.example              # Variables de entorno de ejemplo
├── .dockerignore
├── .gitignore
├── AGENTS.md                 # Guía del proyecto para asistentes IA
├── Dockerfile                # Imagen Docker para Render
├── render.yaml               # Configuración de despliegue en Render
├── pyproject.toml            # Dependencias y configuración de herramientas
├── alembic.ini               # Configuración de Alembic
├── alembic/
│   ├── env.py                # Entorno de Alembic (usa settings)
│   ├── script.py.mako        # Template para migraciones
│   └── versions/
│       └── 9e8669e0391b_initial_schema.py  # Migración inicial
│
├── scripts/
│   ├── entrypoint.sh          # Punto de entrada Docker
│   └── seed_categorias.py     # Seed de 24 categorías iniciales
│
├── src/finanzas/
│   ├── config/
│   │   └── settings.py        # Pydantic Settings (DATABASE_URL, TELEGRAM_BOT_TOKEN, etc.)
│   │
│   ├── domain/
│   │   ├── entities/          # Modelos de negocio
│   │   │   ├── categoria.py   # Categoría de ingresos/gastos
│   │   │   ├── cuenta_bancaria.py
│   │   │   ├── movimiento.py  # Movimiento financiero
│   │   │   └── reporte_generado.py
│   │   ├── value_objects/
│   │   │   ├── dinero.py      # Moneda + cantidad (inmutable)
│   │   │   └── periodo.py     # Rango de fechas
│   │   └── exceptions.py      # Excepciones de dominio
│   │
│   ├── application/
│   │   ├── ports/             # Interfaces (contratos)
│   │   │   ├── repositorio_movimientos.py
│   │   │   ├── repositorio_categorias.py
│   │   │   ├── conector_bancario.py
│   │   │   └── enviador_email.py
│   │   ├── use_cases/         # Casos de uso
│   │   │   ├── registrar_movimiento.py
│   │   │   ├── listar_movimientos.py
│   │   │   ├── obtener_balance.py
│   │   │   ├── importar_csv.py
│   │   │   ├── conciliar_movimientos_banco.py
│   │   │   └── generar_reporte_semanal.py
│   │   └── services/
│   │       └── calculadora_financiera.py  # Motor de cálculos
│   │
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── engine.py      # SQLModel engine + sesión
│   │   │   └── models.py      # Re-exporta todas las entidades
│   │   ├── repositories/      # Implementaciones concretas
│   │   │   ├── repositorio_movimientos_sqlmodel.py
│   │   │   └── repositorio_categorias_sqlmodel.py
│   │   ├── bancos/
│   │   │   └── conector_simulado.py  # Banco simulado para pruebas
│   │   ├── email/
│   │   │   └── enviador_email_smtp.py
│   │   └── scheduler/
│   │       └── config.py      # APScheduler (reporte semanal)
│   │
│   └── interfaces/
│       ├── telegram_bot/
│       │   ├── main.py        # Bootstrap del bot + health check HTTP
│       │   └── handlers.py    # Handlers de comandos y conversaciones
│       ├── cli/
│       │   └── app.py         # CLI con Typer
│       ├── api/               # FastAPI (no implementado aún)
│       └── dashboard/
│           └── app.py         # Dashboard Streamlit
│
└── tests/
    ├── conftest.py            # Fixtures compartidos
    ├── unit/
    │   ├── domain/
    │   │   ├── test_dinero.py
    │   │   └── test_periodo.py
    │   ├── application/
    │   │   ├── test_calculadora_financiera.py
    │   │   ├── test_calculadora_avanzada.py
    │   │   ├── test_registrar_movimiento.py
    │   │   ├── test_obtener_balance.py
    │   │   ├── test_listar_movimientos.py
    │   │   ├── test_importar_csv.py
    │   │   └── test_conciliar_movimientos_banco.py
    │   └── infrastructure/
    │       └── test_conector_simulado.py
    ├── integration/           # Por implementar
    └── e2e/                   # Por implementar
```

---

## ☁️ Despliegue en Render

### Opción 1: Usando render.yaml (Blueprints)

1. Haz fork/push del repositorio a GitHub
2. En [Render Dashboard](https://dashboard.render.com/), ve a **Blueprints**
3. Conecta tu repositorio
4. Render detectará automáticamente el `render.yaml` y creará:
   - **Web Service** `finanzas-bot` (tipo Docker)
   - **PostgreSQL** `finanzas-db` (plan free)
5. Agrega la variable de entorno `TELEGRAM_BOT_TOKEN` manualmente (es `sync: false` por seguridad)
6. Render asignará `DATABASE_URL` automáticamente desde la base de datos PostgreSQL
7. Haz clic en **Apply** y espera el despliegue

### Opción 2: Manual desde el Dashboard

1. Crea un nuevo **Web Service** (no Background Worker — no disponible en plan free)
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Runtime**: Docker
   - **Plan**: Free
4. Agrega un **PostgreSQL** database desde el dashboard (plan free)
5. En Environment Variables, setea:
   - `TELEGRAM_BOT_TOKEN` — tu token de BotFather
   - `DATABASE_URL` — se auto-asigna al crear la base de datos PostgreSQL
6. Despliega

### Importante

- El bot incluye un **servidor HTTP de health check** (puerto `$PORT`) para que Render detecte un puerto abierto y no termine el servicio
- Las migraciones y el seed se ejecutan automáticamente al iniciar (`entrypoint.sh`)
- Los datos persisten en PostgreSQL (no en SQLite)
- En el plan free, el servicio puede dormir después de 15 minutos de inactividad; al recibir un mensaje en Telegram, Render lo despierta (tarda unos segundos)

---

## 🔧 Variables de Entorno

| Variable | Obligatoria | Defecto | Descripción |
|---|---|---|---|
| `DATABASE_URL` | ✅ | `sqlite:///./finanzas.db` | URL de conexión a la base de datos. En Render se asigna automáticamente desde PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token del bot de Telegram (de [@BotFather](https://t.me/BotFather)) |
| `SECRET_KEY` | ⚠️ Recomendada | `change-this-to-a-random-secret-key` | Clave secreta para la aplicación. Genera una con: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `LOG_LEVEL` | ❌ | `INFO` | Nivel de logging: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SMTP_HOST` | ❌ | `smtp.gmail.com` | Servidor SMTP para reportes semanales |
| `SMTP_PORT` | ❌ | `587` | Puerto SMTP |
| `SMTP_USER` | ❌ | — | Usuario SMTP (ej. tu correo Gmail) |
| `SMTP_PASSWORD` | ❌ | — | Contraseña de aplicación SMTP |
| `EMAIL_FROM` | ❌ | — | Dirección de correo remitente |
| `EMAIL_TO` | ❌ | — | Dirección de correo destinatario de los reportes |

---

## 🗄️ Base de Datos

### Migraciones (Alembic)

```bash
# Crear una nueva migración
uv run alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones
uv run alembic upgrade head

# Revertir una migración
uv run alembic downgrade -1
```

### Tablas

| Tabla | Descripción |
|---|---|
| `categorias` | Categorías de ingresos y gastos (24 precargadas) |
| `movimientos` | Registros financieros con tipo, valor, fecha, categoría y hash de conciliación |
| `cuentas_bancarias` | Cuentas bancarias para conciliación |
| `reportes_generados` | Historial de reportes semanales generados |

### Seed de Categorías

```bash
uv run python -m scripts.seed_categorias
```

El script es **idempotente**: solo crea categorías que no existan (verifica por nombre).

**Categorías incluidas (24):**

| Ingresos (11) | Gastos (13) |
|---|---|
| Clases particulares, Apartamento Niquía, Booking, Airbnb, Servicio de programación, Ventas, Otros ingresos, Acciones, Indrive, Didi, Uber | Transporte, Comida, Otras salidas, Ropa, Regalos, Plan celular, Vacaciones, Préstamos, Entretenimiento, Aseo personal, Carro, Casa, Seguridad social |

---

## 🧪 Tests y Calidad de Código

```bash
# Ejecutar todos los tests con cobertura
uv run pytest --cov

# Solo tests unitarios
uv run pytest tests/unit/

# Linter
uv run ruff check

# Type checker
uv run mypy src/
```

**Estado actual:**
- 49 tests
- 96% de cobertura
- Cobertura objetivo: ≥90% domain, ≥80% application

---

## 📋 Roadmap

| Fase | Estado | Descripción |
|---|---|---|
| 0 | ✅ | Estructura, configuración, modelo, migraciones, tests de dominio |
| 1 | ✅ | Casos de uso, CLI, Telegram bot, importación CSV |
| 2 | ✅ | Calculadora financiera, dashboard Streamlit, reportes semanales |
| 3 | ✅ | Conector simulado, conciliación bancaria, deduplicación |
| 4+ | ⏳ | Integración bancaria real (bancos colombianos), Celery + Redis, PostgreSQL producción, multi-moneda, multi-usuario, API REST con FastAPI |

---

## 🤝 Contribuir

Este proyecto sigue **Conventional Commits** para los mensajes de commit.

```bash
feat: add new feature
fix: correct bug in parser
refactor: extract calculator service
test: add coverage for edge cases
```

---

## 📄 Licencia

MIT
