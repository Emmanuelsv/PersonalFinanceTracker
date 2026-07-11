# Sistema de Gestión Financiera Personal
## Documento de Diseño de Producto, Arquitectura y Roadmap de Implementación

---

## 0. Resumen ejecutivo

Este documento define el diseño completo de una aplicación personal de gestión financiera, construida en Python, pensada para ser implementada por un agente de programación siguiendo prácticas de ingeniería de software profesional. Cubre modelo de datos, arquitectura, stack tecnológico, UX de registro, automatización bancaria futura, reportería, estructura de proyecto, estrategia de pruebas, roadmap por fases, y un conjunto de "Skills" (reglas de trabajo) para que el agente produzca código consistente y de alta calidad.

La recomendación central para el MVP es: **CLI + bot de Telegram** como interfaz de captura, **SQLite + SQLModel** como persistencia, **FastAPI** como capa de servicios internos, **Streamlit** para el dashboard de analítica, y **APScheduler** para el reporte semanal por correo — todo dentro de una Clean Architecture que deja la puerta abierta a Open Banking, Celery/Redis y PostgreSQL en fases posteriores sin reescribir el núcleo del dominio.

---

## 1. Visión y objetivos del producto

**Visión:** una herramienta personal que reduzca la fricción de registrar movimientos financieros a segundos, y que convierta esos datos en visibilidad real sobre el flujo de dinero, patrimonio y hábitos de gasto — con el menor mantenimiento manual posible.

**Objetivos no funcionales clave:**
- Escalable de "app de un solo usuario" a "app multiusuario" sin reescribir el dominio.
- Extensible: agregar un nuevo subtipo, canal de entrada o fuente bancaria no debe tocar más de 1-2 capas.
- Auditable: todo movimiento debe ser trazable (quién/qué lo creó, cuándo, si vino de una conciliación automática).
- Segura desde el día uno, aunque la integración bancaria real llegue después.

---

## 2. Modelo de datos

### 2.1 Entidades principales

**Movimiento** (entidad central)

| Campo | Tipo | Notas |
|---|---|---|
| `id` | UUID | PK |
| `tipo` | Enum: `INGRESO`, `SALIDA` | |
| `subtipo` | Enum/FK a `Categoria` | ver 2.2 |
| `fecha` | `date` | fecha del movimiento (no de registro) |
| `valor` | `Decimal` | **nunca usar `float` para dinero** |
| `descripcion` | `str` (opcional, texto libre) | |
| `fuente` | Enum: `MANUAL`, `IMPORTADO_CSV`, `BANCO_AUTOMATICO` | soporta la fase de automatización bancaria |
| `hash_conciliacion` | `str` (opcional) | hash determinístico para deduplicar importaciones |
| `creado_en` / `actualizado_en` | `datetime` | auditoría |
| `moneda` | Enum (`COP` por defecto) | pensar en multi-moneda a futuro sin costo extra |

**Categoria** (para no "quemar" los subtipos como strings sueltos)

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `nombre` | str (ej. "Transporte") |
| `tipo_asociado` | Enum: `INGRESO`, `SALIDA`, `AMBOS` |
| `activo` | bool (permite desactivar sin borrar histórico) |

Catálogo inicial de subtipos (semilla / *seed data*, no hardcodeado en el dominio): Transporte, Comida, Clases particulares, Apartamento Niquía, Otros ingresos, Otras salidas, Acciones, Banco, Ropa, Regalos, Plan celular, Vacaciones, Préstamos, Entretenimiento, Gastos personales, Casa, Seguridad social, Comisiones.

> **Decisión de diseño:** los subtipos viven en una tabla, no en un `Enum` de Python. Un `Enum` obligaría a tocar código y redeployar cada vez que quieras agregar "Mascotas" o "Educación". Una tabla permite gestionarlos desde la propia app.

**CuentaBancaria** (preparación para automatización, aunque el MVP no la use activamente)

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `nombre` | str |
| `entidad` | str |
| `tipo_cuenta` | Enum: `AHORROS`, `CORRIENTE`, `TARJETA_CREDITO`, `INVERSION` |
| `saldo_actual` | Decimal (opcional, cache) |
| `conector` | str (nombre del adapter, ver sección 7) |

**ReporteGenerado** (histórico de reportes enviados, útil para comparaciones semana contra semana)

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `periodo_inicio` / `periodo_fin` | date |
| `payload_json` | JSON con las métricas calculadas |
| `enviado_en` | datetime |

### 2.2 Relación conceptual

```
Categoria (1) ────< (N) Movimiento >──── (0..1) CuentaBancaria
                          │
                          └──< (N) ReporteGenerado.payload_json (agregación, no FK directa)
```

---

## 3. Arquitectura del sistema

Se propone **Clean Architecture** (también llamada Ports & Adapters / Hexagonal) porque el proyecto tiene dos ejes de cambio independientes que van a evolucionar en momentos distintos: (a) **cómo entran los datos** (CLI hoy, Telegram y banco automático mañana) y (b) **cómo se calculan y presentan** (reportes por correo hoy, dashboard interactivo mañana). Clean Architecture aísla el dominio de ambos ejes.

### 3.1 Capas

```
┌─────────────────────────────────────────────────────────┐
│  Interfaces (adapters de entrada/salida)                  │
│  CLI · Telegram Bot · API REST (FastAPI) · Dashboard      │
│  (Streamlit) · Email Sender · Importador CSV               │
├─────────────────────────────────────────────────────────┤
│  Application (casos de uso / orquestación)                │
│  RegistrarMovimiento · CalcularBalanceMensual ·            │
│  GenerarReporteSemanal · ConciliarMovimientosBanco         │
├─────────────────────────────────────────────────────────┤
│  Domain (núcleo puro, sin dependencias externas)           │
│  Entidades: Movimiento, Categoria, CuentaBancaria           │
│  Reglas de negocio: validaciones, cálculo de balance        │
├─────────────────────────────────────────────────────────┤
│  Infrastructure (detalles técnicos, reemplazables)          │
│  Repositorios SQLModel/SQLAlchemy · Cliente SMTP ·          │
│  Adapters bancarios · Scheduler · Almacenamiento de secretos│
└─────────────────────────────────────────────────────────┘
```

**Regla de dependencia:** las flechas de dependencia siempre apuntan hacia adentro (Interfaces → Application → Domain). El Domain no importa nada de Infrastructure ni de Interfaces. Esto es lo que permite, por ejemplo, cambiar SQLite por PostgreSQL, o Streamlit por React, sin tocar una sola regla de negocio.

### 3.2 Por qué cada principio aplica aquí

- **SOLID:** especialmente importante es *Dependency Inversion* — los casos de uso dependen de interfaces (`RepositorioMovimientos`, `EnviadorEmail`), no de implementaciones concretas. Así, agregar un conector bancario nuevo es implementar una interfaz, no modificar código existente (*Open/Closed*).
- **DRY:** los cálculos de agregación (balance, gasto por categoría) viven en un único servicio de dominio (`CalculadoraFinanciera`), reutilizado tanto por el reporte semanal como por el dashboard.
- **KISS:** el MVP evita microservicios, colas de mensajes y multi-tenant. Es un monolito modular — la complejidad se agrega solo cuando el roadmap la exige (fase 3 en adelante).
- **Tipado estático:** `mypy` en modo estricto sobre `domain` y `application`; algo más permisivo en `interfaces` donde hay más "pegamento".
- **Configuración por variables de entorno:** credenciales de SMTP, tokens de bots, cadenas de conexión y llaves de cifrado nunca en código ni en el repositorio — se gestionan vía `.env` (local) y *secret manager* del proveedor de hosting en producción.
- **Logging estructurado:** `structlog` o `logging` con formato JSON, para poder correlacionar "se importaron 12 movimientos, 2 duplicados descartados" sin tener que leer prints sueltos.
- **Manejo de errores:** excepciones de dominio propias (`MovimientoInvalidoError`, `CategoriaInexistenteError`) capturadas en la capa de interfaz y traducidas a mensajes entendibles (HTTP 422, mensaje de Telegram, etc.), nunca un stack trace crudo llegando al usuario.

---

## 4. Stack tecnológico

| Componente | Elección | Justificación |
|---|---|---|
| Lenguaje | Python 3.12 | pattern matching, mejor tipado, performance sobre 3.10 |
| Framework de servicios | **FastAPI** | tipado nativo con Pydantic, generación automática de OpenAPI, async listo para cuando el bot/webhooks lo necesiten |
| ORM / capa de datos | **SQLModel** (sobre SQLAlchemy) | combina el modelo Pydantic (validación) con el modelo de tabla (persistencia) en una sola clase — menos duplicación que SQLAlchemy puro |
| Base de datos MVP | **SQLite** | cero infraestructura, un solo archivo, perfecto para un usuario. Migración a Postgres es casi trivial porque SQLAlchemy abstrae el dialecto |
| Base de datos producción/multiusuario | **PostgreSQL** | soporta concurrencia real, tipos `JSONB` útiles para `payload_json`, y es el estándar de facto para escalar |
| Análisis de datos | **Pandas** | agregaciones (por mes, por categoría) sobre los movimientos exportados desde la BD |
| Visualización | **Plotly** | gráficos interactivos (zoom, hover con el detalle del movimiento) muy superiores a Matplotlib para un dashboard; Matplotlib se reserva para gráficos estáticos embebidos en el PDF/email del reporte semanal |
| Dashboard interactivo | **Streamlit** | permite construir el dashboard de analítica en días, no semanas, reutilizando directamente los casos de uso de `application/`. Se migraría a React solo si algún día se necesita una experiencia móvil pulida o multiusuario con roles |
| Programación de tareas (MVP) | **APScheduler** | corre el job del reporte semanal dentro del mismo proceso, sin infraestructura adicional |
| Programación de tareas (fase 2+) | **Celery + Redis** | necesario cuando existan sincronizaciones bancarias reales (jobs largos, reintentos, colas) — sobredimensionado para el MVP |
| Contenedores | **Docker** | reproducibilidad del entorno, facilita mover el proyecto a cualquier VPS o servicio cloud |
| CI/CD | **GitHub Actions** | lint (`ruff`), tipado (`mypy`), tests (`pytest`) en cada push; build de imagen Docker en cada release |
| Testing | **Pytest** + `pytest-cov` | estándar del ecosistema, buen soporte de fixtures para mockear repositorios y el envío de correos |

**Nota sobre lo que NO se recomienda para el MVP:** microservicios, Kubernetes, GraphQL, y un frontend en React desde el día uno. Todo esto añade tiempo de desarrollo sin resolver ningún problema real que tengas *hoy* con un solo usuario y datos de bajo volumen. El roadmap (sección 11) indica cuándo estas piezas empiezan a tener sentido.

---

## 5. Interfaz de registro de movimientos: comparación y recomendación

| Opción | Fricción de uso diario | Esfuerzo de construcción | Encaja con "MVP rápido" |
|---|---|---|---|
| CLI | Media (hay que abrir terminal) | Muy bajo | Sí, como fallback / power-user |
| App de escritorio (Tkinter/PyQt) | Baja, pero requiere abrir la app | Alto | No |
| Interfaz web (Streamlit) | Baja | Bajo (reutilizando el dashboard) | Sí, para revisar/editar |
| **Bot de Telegram** | **Muy baja** (un mensaje desde el celular) | Bajo-medio | **Sí — recomendado como canal principal** |
| WhatsApp (API de Meta) | Muy baja | Alto (requiere Business API, aprobación, costos) | No para MVP |
| Formularios rápidos (ej. Google Forms → Sheets) | Baja | Muy bajo, pero desconectado del resto del sistema | No (rompe la arquitectura) |
| Procesamiento de voz | Baja | Alto (requiere STT + parsing de lenguaje natural confiable) | No para MVP, sí como fase futura sobre el bot de Telegram |
| OCR de facturas | Media (hay que fotografiar) | Alto (requiere modelo de extracción confiable) | No para MVP |
| Importación CSV/Excel | N/A (es para carga masiva, no diaria) | Bajo | Sí, como complemento para carga histórica |

**Recomendación para el MVP: Bot de Telegram como canal principal + CLI como canal secundario/administrativo + importador CSV para cargar el histórico inicial.**

Justificación: un mensaje de Telegram como `gasto 25000 comida almuerzo` (o un flujo guiado con botones para tipo/subtipo) tiene la menor fricción posible desde el celular, que es donde realmente ocurre el gasto. El bot llama directamente al caso de uso `RegistrarMovimiento` de la capa `application/`, exactamente igual que lo haría la CLI o el futuro conector bancario — es solo otro *adapter* de entrada. Streamlit se reserva para consulta y edición, no para la captura rápida diaria.

---

## 6. Visualización y analítica

Los gráficos y métricas solicitados, más algunas adiciones de valor:

- Ingresos vs. gastos por mes (barras agrupadas)
- Gasto por categoría (barras horizontales o *treemap* — mejor que torta cuando hay 17 subtipos)
- Evolución del patrimonio (línea acumulada = ingresos − gastos, mes a mes)
- Flujo de caja (línea diaria/semanal dentro del mes)
- Tendencias (media móvil de 3 meses sobre gasto total y por categoría)
- Comparación entre meses (mismo mes año anterior vs. actual, si hay suficiente histórico)
- Distribución porcentual de gastos (treemap o barras apiladas al 100%)
- Balance mensual (ingreso − gasto, con color según sea positivo/negativo)
- Ahorro acumulado (línea de balance acumulado desde el inicio del registro)

**Métricas adicionales sugeridas:**
- **Tasa de ahorro** = (ingresos − gastos) / ingresos, expresada en %.
- **Gasto fijo vs. variable**: clasificar subtipos como fijos (Plan celular, Casa, Seguridad social) o variables, para ver cuánto margen de maniobra hay realmente.
- **Detección de anomalías**: alertar si un subtipo se desvía más de X% respecto a su promedio de los últimos 3 meses.
- **Proyección de fin de mes**: con el gasto acumulado a la fecha, proyectar el cierre del mes por categoría.
- **Índice de salud financiera**: un score simple combinando tasa de ahorro, diversificación de gasto y tendencia de deuda (Préstamos).
- **Costo de suscripciones/recurrentes**: identificar movimientos que se repiten mes a mes con valor similar (candidatos a "Plan celular", streaming, etc.) para visibilizar gasto recurrente total.

---

## 7. Automatización bancaria (arquitectura preparada para fase futura)

Aunque no se implemente en el MVP, la arquitectura debe dejar el terreno listo desde ahora:

**Patrón Adapter para conectores bancarios**

```
application/ports/conector_bancario.py   → interfaz abstracta: obtener_movimientos(cuenta, desde, hasta)
infrastructure/bancos/
    conector_simulado.py                 → implementación fake para desarrollo/tests
    conector_open_banking_xyz.py         → implementación real futura (ej. vía un agregador tipo Belvo/Plaid en LatAm)
```

Los casos de uso (`ConciliarMovimientosBanco`) dependen solo de la interfaz `ConectorBancario`, nunca de una implementación concreta — así se puede empezar hoy con `ConectorSimulado` (genera datos de prueba) y reemplazarlo mañana sin tocar el dominio.

**Puntos clave de diseño:**

- **Credenciales:** nunca se guardan en texto plano ni en variables de entorno para producción real; se usa un *secret manager* (ej. Vault, AWS Secrets Manager, o como mínimo un archivo cifrado con `cryptography.Fernet` fuera del repositorio). El token de acceso a un agregador de Open Banking se trata como un secreto rotable, no como una contraseña fija.
- **Open Banking / agregadores:** en Colombia y LatAm, la vía realista no es conectarse banco por banco (cada uno tiene su propia API, si es que la expone), sino usar un agregador (ej. Belvo) que ya resuelve esa fragmentación. El `ConectorBancario` se implementa una vez por agregador, no una vez por banco.
- **Sincronización:** un job programado (Celery en fase 2) trae movimientos nuevos periódicamente; cada corrida se registra (éxito/fallo, cantidad de movimientos nuevos) para auditoría.
- **Conciliación y deduplicación:** cada movimiento importado genera un `hash_conciliacion` determinístico (ej. hash de fecha + valor + descripción normalizada + cuenta). Antes de insertar, se verifica si ese hash ya existe. Esto evita duplicados si el job corre dos veces o si el banco reenvía el mismo movimiento.
- **Movimientos en revisión:** los importados automáticamente entran con un estado "pendiente de categorizar" hasta que el usuario (o un clasificador simple basado en reglas/histórico) les asigna subtipo, en vez de asumir una categoría por defecto que ensucie las métricas.

---

## 8. Reportes automáticos por correo

**Flujo:**

1. `APScheduler` dispara el job cada domingo a una hora configurable.
2. El caso de uso `GenerarReporteSemanal` calcula, vía `CalculadoraFinanciera`: total ingresos, total gastos, balance, desglose por categoría, y compara contra la semana anterior (guardada en `ReporteGenerado`).
3. Se generan gráficos estáticos (Matplotlib, ya que van embebidos como imágenes en un correo, no interactivos) y se arma un HTML de correo.
4. `EnviadorEmail` (interfaz) envía el correo vía SMTP (ej. una cuenta de Gmail con contraseña de aplicación, o un servicio como SendGrid/Resend para mayor confiabilidad de entrega).
5. El resultado se persiste en `ReporteGenerado` para que la próxima semana tenga contra qué comparar, y para poder reconstruir un historial de reportes desde el dashboard.

**Contenido mínimo del reporte:** total ingresos, total gastos, balance, gasto por categoría (top 5 + resto agrupado en "otros"), comparación porcentual vs. semana anterior, y 1-2 recomendaciones automáticas generadas por reglas simples (ej. "tu gasto en Entretenimiento subió 40% esta semana" o "vas en camino a superar tu gasto promedio en Comida este mes").

---

## 9. Organización del proyecto

```
finanzas-personales/
├── src/
│   └── finanzas/
│       ├── domain/
│       │   ├── entities/          # Movimiento, Categoria, CuentaBancaria
│       │   ├── value_objects/     # Dinero (Decimal + moneda), Periodo
│       │   └── exceptions.py
│       ├── application/
│       │   ├── use_cases/         # registrar_movimiento.py, generar_reporte_semanal.py...
│       │   ├── ports/             # interfaces: RepositorioMovimientos, EnviadorEmail, ConectorBancario
│       │   └── services/          # CalculadoraFinanciera
│       ├── infrastructure/
│       │   ├── db/                # engine, sesiones, modelos SQLModel, migraciones (Alembic)
│       │   ├── repositories/      # implementaciones concretas de los ports
│       │   ├── email/             # cliente SMTP
│       │   ├── bancos/            # conectores bancarios (simulado y reales)
│       │   └── scheduler/         # configuración de APScheduler/Celery
│       ├── interfaces/
│       │   ├── cli/               # comandos Typer/Click
│       │   ├── telegram_bot/      # handlers del bot
│       │   ├── api/               # routers FastAPI (si se expone API propia)
│       │   └── dashboard/         # app Streamlit
│       └── config/                # settings.py (Pydantic Settings, lee variables de entorno)
├── tests/
│   ├── unit/                      # domain y application, sin IO real
│   ├── integration/                # repositorios contra SQLite en memoria, envío de email mockeado
│   └── e2e/                       # flujo completo: mensaje de Telegram → BD → reporte
├── scripts/                        # seed de categorías, importadores puntuales, utilidades de migración
├── docs/                           # este documento, decisiones de arquitectura (ADRs)
├── alembic/                        # migraciones de esquema
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 10. Estrategia de pruebas

- **Pirámide de pruebas:** mayoría de pruebas unitarias sobre `domain/` y `application/` (rápidas, sin IO), un grupo intermedio de pruebas de integración contra una base SQLite en memoria y un mock del cliente SMTP/bot de Telegram, y un puñado de pruebas end-to-end que cubran los flujos críticos completos (registrar movimiento por Telegram → aparece en el reporte semanal).
- **Cobertura objetivo:** ≥90% en `domain/`, ≥80% en `application/`, sin exigir 100% en `interfaces/` (mucho de eso es *glue code* de bajo riesgo).
- **Mocking del banco:** el `ConectorSimulado` sirve tanto para desarrollo manual como para pruebas de `ConciliarMovimientosBanco`, incluyendo casos de duplicados y datos malformados.
- **Fixtures reutilizables:** un `Movimiento` de fábrica (`factory_boy` o simplemente funciones `crear_movimiento_de_prueba(**overrides)`) para no repetir la construcción de objetos en cada test.
- **Pruebas de regresión de cálculos financieros:** dado que el balance y el ahorro acumulado son datos sensibles, cada fórmula de `CalculadoraFinanciera` debe tener casos de prueba con valores conocidos de antemano (incluyendo bordes: mes sin movimientos, solo ingresos, solo gastos, valores negativos inválidos).
- **CI:** en cada push, GitHub Actions corre `ruff check`, `mypy`, y `pytest --cov`; un PR no se puede fusionar si baja la cobertura o falla el tipado.

---

## 11. Roadmap de implementación

**Fase 0 — Fundaciones (semana 1)**
Estructura de proyecto, configuración, modelo de datos, migraciones con Alembic, seed de las 17 categorías iniciales, capa de dominio con sus pruebas unitarias.

**Fase 1 — MVP de registro y consulta (semanas 2-3)**
Casos de uso de registro y consulta de movimientos. CLI funcional. Bot de Telegram con flujo guiado (tipo → subtipo → valor → descripción opcional). Importador CSV para cargar histórico.

**Fase 2 — Analítica y reporte semanal (semana 4)**
`CalculadoraFinanciera` con todas las métricas de la sección 6. Dashboard en Streamlit. Job de reporte semanal por correo con APScheduler.

**Fase 3 — Robustez y automatización bancaria simulada (semanas 5-6)**
`ConectorSimulado`, lógica de conciliación y deduplicación, estado "pendiente de categorizar", panel de revisión de importados en el dashboard.

**Fase 4 — Integración bancaria real (cuando aplique)**
Reemplazo del conector simulado por un agregador real (Open Banking), migración de APScheduler a Celery+Redis para manejar jobs de sincronización más pesados y con reintentos, migración de SQLite a PostgreSQL si el volumen o la necesidad de acceso concurrente lo justifica.

**Fase 5 — Extensiones (a demanda)**
Multi-moneda, multiusuario, OCR de facturas, procesamiento de voz sobre el bot, forecast con modelos simples de series de tiempo.

---

## 12. Skills para el agente de programación

Cada skill que sigue está pensada para regir cómo el agente escribe, revisa y entrega código en este proyecto.

### Skill 1 — Estándares de código y tipado

**Objetivo:** que todo el código sea legible, consistente y verificable estáticamente sin depender de que un humano lo revise línea por línea.

**Cuándo aplicarla:** en cada archivo `.py` que el agente cree o modifique.

**Buenas prácticas:**
- Type hints en el 100% de firmas de funciones y métodos públicos, incluyendo tipos de retorno.
- Nombres descriptivos y en español o inglés de forma **consistente dentro de un mismo módulo** (no mezclar `get_movimiento` con `obtener_categoria` en el mismo archivo).
- Docstrings estilo Google en toda clase y función pública, explicando propósito, parámetros, retorno y excepciones que puede lanzar.
- `ruff` para linting y formateo; `mypy --strict` sobre `domain/` y `application/`.
- Evitar "números mágicos" y strings sueltos: usar constantes o `Enum`.

**Ejemplos:**
```python
def calcular_balance_mensual(
    movimientos: list[Movimiento], periodo: Periodo
) -> BalanceMensual:
    """Calcula el balance de un periodo dado.

    Args:
        movimientos: movimientos ya filtrados al periodo de interés.
        periodo: rango de fechas sobre el que se calcula el balance.

    Returns:
        BalanceMensual con totales de ingreso, gasto y balance neto.
    """
```

**Errores comunes:** usar `float` para dinero (perder precisión), funciones sin type hints "porque son internas", docstrings que repiten el nombre de la función sin aportar información nueva.

**Checklist de validación:**
- [ ] `mypy` pasa sin errores en los módulos tocados.
- [ ] `ruff check` sin warnings nuevos.
- [ ] Toda función pública tiene docstring y tipos.
- [ ] Ningún valor monetario usa `float`.

---

### Skill 2 — Arquitectura y diseño orientado a objetos

**Objetivo:** mantener la separación de capas de Clean Architecture y aplicar SOLID de forma pragmática, no dogmática.

**Cuándo aplicarla:** al agregar cualquier caso de uso nuevo, entidad, o punto de integración externo (nuevo canal de entrada, nuevo conector bancario, nuevo tipo de reporte).

**Buenas prácticas:**
- Antes de escribir código, ubicar en qué capa vive cada pieza nueva (¿es regla de negocio → domain? ¿orquesta pasos → application? ¿habla con el mundo exterior → infrastructure/interfaces?).
- Toda dependencia hacia afuera del domain se hace a través de una interfaz (`Protocol` o clase abstracta) definida en `application/ports/`.
- Preferir composición sobre herencia salvo que exista una jerarquía "es-un" genuina.
- Aplicar un patrón de diseño solo cuando resuelve un problema real presente en el código, no de forma anticipada ("por si acaso").

**Ejemplos:** el `ConectorBancario` como interfaz con dos implementaciones (`ConectorSimulado`, futuro `ConectorOpenBanking`) es un caso correcto de *Strategy/Adapter*. Forzar un patrón *Factory* para instanciar dos clases fijas sería sobre-ingeniería.

**Errores comunes:** que `domain/` importe algo de `infrastructure/` (rompe la regla de dependencia), lógica de negocio "escondida" dentro de un handler de Telegram o de un endpoint FastAPI en vez de en un caso de uso.

**Checklist de validación:**
- [ ] `domain/` no tiene imports de `infrastructure/` ni `interfaces/`.
- [ ] El caso de uso nuevo depende de interfaces, no de clases concretas.
- [ ] La lógica de negocio no vive dentro de un handler/endpoint.

---

### Skill 3 — Manejo de errores y logging

**Objetivo:** que los fallos sean explícitos, trazables y presentados de forma útil al usuario final, sin exponer detalles internos.

**Cuándo aplicarla:** en cualquier punto donde pueda fallar una operación (validación de datos, IO de base de datos, llamada a un servicio externo, parsing de un mensaje del bot).

**Buenas prácticas:**
- Excepciones de dominio propias y específicas (`MovimientoInvalidoError`, en vez de `ValueError` genérico) para que la capa de interfaz pueda traducirlas a una respuesta adecuada.
- Logging estructurado (nivel `INFO` para eventos de negocio relevantes, `WARNING` para situaciones recuperables como un duplicado descartado, `ERROR` para fallos que requieren atención).
- Nunca silenciar excepciones con un `except: pass`.
- Los mensajes de error hacia el usuario (Telegram, CLI, dashboard) son amigables; el detalle técnico completo va solo al log.

**Ejemplos:**
```python
try:
    movimiento = registrar_movimiento(datos)
except MovimientoInvalidoError as exc:
    logger.warning("movimiento_rechazado", motivo=str(exc), datos=datos)
    return "No pude registrar ese movimiento: " + str(exc)
```

**Errores comunes:** capturar `Exception` genérica y ocultar el error real, loggear datos sensibles (credenciales, tokens) en texto plano.

**Checklist de validación:**
- [ ] Toda excepción capturada es específica, no `Exception` a secas (salvo en el borde más externo de la app, como último resguardo).
- [ ] Ningún log contiene secretos o credenciales.
- [ ] El usuario final nunca ve un stack trace crudo.

---

### Skill 4 — Testing

**Objetivo:** dar confianza para refactorizar y agregar funcionalidades sin romper lo existente.

**Cuándo aplicarla:** junto con cada caso de uso o regla de negocio nueva, no como una tarea aparte al final.

**Buenas prácticas:**
- Escribir primero el caso feliz y al menos un caso borde por función de dominio (mes sin movimientos, valores en cero, subtipo inexistente).
- Usar fixtures/factories para no repetir construcción de objetos de prueba.
- Mockear todo lo externo (SMTP, API de Telegram, conector bancario) en pruebas unitarias e integración; solo las pruebas e2e pueden tocar un entorno más real (y aun así, contra un sandbox, nunca un banco real).
- Nombrar los tests describiendo el comportamiento esperado, no la función probada (`test_balance_es_negativo_cuando_gastos_superan_ingresos`).

**Errores comunes:** pruebas que solo verifican que "no lance excepción" sin comprobar el valor calculado, pruebas de integración que dependen de servicios externos reales (hacen el CI lento y frágil).

**Checklist de validación:**
- [ ] Toda regla de cálculo financiero tiene al menos un caso feliz y un caso borde probado.
- [ ] Ninguna prueba unitaria hace IO real (red, disco, email).
- [ ] `pytest --cov` no baja la cobertura previa.

---

### Skill 5 — Seguridad y manejo de credenciales

**Objetivo:** proteger datos financieros y credenciales de acceso (bot de Telegram, SMTP, futuros tokens bancarios) incluso en un proyecto de un solo usuario.

**Cuándo aplicarla:** siempre que se introduzca una credencial, token, o dato sensible nuevo.

**Buenas prácticas:**
- Ninguna credencial en el código fuente ni en el repositorio; todo vía variables de entorno (`.env`, nunca commiteado) o un secret manager en producción.
- Tokens bancarios/API cifrados en reposo si se persisten (ej. `cryptography.Fernet`), nunca en texto plano en la base de datos.
- Validar y sanear cualquier entrada externa (mensajes de Telegram, archivos CSV importados) antes de usarla en una consulta o cálculo.
- Principio de menor privilegio: la cuenta de correo usada para enviar reportes no debería tener acceso a nada más que enviar correo.

**Errores comunes:** subir un `.env` real al repositorio, loggear el token del bot de Telegram, confiar en el contenido de un CSV importado sin validar tipos/rangos.

**Checklist de validación:**
- [ ] `.env` está en `.gitignore` y solo existe `.env.example` en el repo.
- [ ] Ninguna credencial aparece en logs ni en mensajes de error.
- [ ] Toda entrada externa se valida antes de usarse.

---

### Skill 6 — Rendimiento y optimización

**Objetivo:** que la app siga siendo rápida a medida que crece el histórico de movimientos, sin optimizar prematuramente donde no hace falta.

**Cuándo aplicarla:** en consultas de agregación (reportes, dashboard) y en cualquier importación masiva (CSV, sincronización bancaria).

**Buenas prácticas:**
- Delegar agregaciones (sumas, agrupaciones por categoría/mes) a la base de datos o a Pandas, no a loops de Python sobre listas de objetos.
- Índices en `fecha`, `tipo`, `subtipo_id` de la tabla de movimientos, ya que son los filtros más frecuentes.
- Paginar o limitar rangos de fecha en consultas del dashboard en vez de traer todo el histórico siempre.
- Medir antes de optimizar: no introducir cachés o estructuras complejas sin evidencia de que la consulta simple es lenta.

**Errores comunes:** cargar toda la tabla de movimientos en memoria para calcular un total que la base de datos podría calcular con un `SUM`, N+1 queries al listar movimientos con su categoría.

**Checklist de validación:**
- [ ] Las agregaciones usan SQL/Pandas, no loops manuales en Python.
- [ ] No hay N+1 queries en los listados principales.
- [ ] Las columnas de filtro frecuente tienen índice.

---

### Skill 7 — Gestión de dependencias y entornos

**Objetivo:** que el proyecto sea reproducible en cualquier máquina o entorno de CI sin sorpresas de versiones.

**Cuándo aplicarla:** al agregar cualquier librería nueva o modificar el entorno de ejecución.

**Buenas prácticas:**
- `pyproject.toml` como única fuente de verdad de dependencias, gestionado con `uv` o `poetry`.
- Fijar versiones mínimas compatibles, no versiones exactas rígidas salvo que haya una razón concreta (evita conflictos de resolución).
- Separar dependencias de desarrollo (`pytest`, `ruff`, `mypy`) de las de producción.
- Toda dependencia nueva se justifica: ¿resuelve algo que la librería estándar o lo ya instalado no resuelve?

**Errores comunes:** instalar una librería pesada para resolver algo trivial (ej. una librería completa de fechas para un solo cálculo que `datetime` ya cubre), no fijar ninguna versión y romper el build meses después.

**Checklist de validación:**
- [ ] Toda dependencia nueva está en `pyproject.toml`, no instalada "a mano" sin registrar.
- [ ] El proyecto instala limpio en un entorno nuevo (`uv sync` / `poetry install`) sin pasos manuales adicionales.

---

### Skill 8 — Git, commits y revisión de código

**Objetivo:** mantener un historial legible que sirva como documentación del porqué de los cambios, no solo del qué.

**Cuándo aplicarla:** en cada commit y pull request.

**Buenas prácticas:**
- Commits atómicos: un commit, un cambio lógico coherente (no mezclar una refactorización con una funcionalidad nueva).
- Mensajes de commit en formato *Conventional Commits* (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`), con un cuerpo que explique el porqué cuando el cambio no sea obvio.
- Ramas por funcionalidad (`feature/bot-telegram-registro`), nunca commitear directo a `main`.
- Antes de abrir PR: correr lint, tipado y tests localmente — el CI es una red de seguridad, no el primer filtro.

**Errores comunes:** commits tipo "cambios varios" o "fix", ramas de meses de antigüedad sin integrar (aumenta el riesgo de conflictos), mezclar formateo automático masivo con cambios funcionales en el mismo commit.

**Checklist de validación:**
- [ ] El mensaje de commit sigue Conventional Commits y describe el *porqué*, no solo el *qué*.
- [ ] El PR toca un solo tema/funcionalidad.
- [ ] Lint, tipado y tests pasan antes de pedir revisión.

---

### Skill 9 — Refactorización y mantenibilidad continua

**Objetivo:** evitar que el código se degrade con el tiempo a medida que se agregan funcionalidades bajo presión de tiempo.

**Cuándo aplicarla:** cuando se detecta duplicación, una función que creció demasiado, o una capa que empieza a filtrar responsabilidades de otra.

**Buenas prácticas:**
- Regla de las tres repeticiones: si una misma lógica aparece por tercera vez, se extrae a una función/servicio compartido.
- Funciones y métodos cortos con una sola responsabilidad clara (si el nombre necesita "y" para describir lo que hace, probablemente debería dividirse).
- Refactorizar con la red de seguridad de los tests existentes: si no hay test que cubra el comportamiento actual, se escribe antes de tocar el código.
- Documentar decisiones de arquitectura no obvias como ADRs cortos en `docs/`.

**Errores comunes:** refactorizar y agregar funcionalidad nueva en el mismo cambio (dificulta revisar y hacer rollback), posponer refactorizaciones indefinidamente hasta que el módulo se vuelve intocable.

**Checklist de validación:**
- [ ] Ninguna función nueva supera ~40-50 líneas sin una razón clara.
- [ ] Toda refactorización va en un commit/PR separado de la funcionalidad nueva.
- [ ] Existe test previo cubriendo el comportamiento antes de refactorizar código sin cobertura.

---

## 13. Cómo usar este documento con el agente de programación

Este documento está pensado para pegarse (completo o por secciones) como contexto inicial de un agente de programación, en el siguiente orden sugerido de trabajo:

1. Sección 9 (estructura de carpetas) + Sección 2 (modelo de datos) → generar el esqueleto del proyecto y las entidades de dominio con sus pruebas.
2. Sección 3 (arquitectura) + Skills 1-2 → establecer las interfaces (`ports`) antes de cualquier implementación concreta.
3. Sección 5 y Fase 1 del roadmap → construir el bot de Telegram y la CLI sobre los casos de uso ya definidos.
4. Sección 6 y 8 + Fase 2 del roadmap → analítica, dashboard y reporte semanal.
5. Sección 7 + Fase 3 del roadmap → simulación de banco, conciliación y deduplicación.

En cada entrega, pedirle al agente que valide su trabajo contra el checklist de la skill correspondiente antes de darla por terminada.
