from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlmodel import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from finanzas.application.use_cases.listar_movimientos import (
    ListarMovimientos,
)
from finanzas.application.use_cases.obtener_balance import (
    ObtenerBalanceMensual,
)
from finanzas.application.use_cases.registrar_movimiento import (
    RegistrarMovimiento,
)
from finanzas.domain.entities.movimiento import TipoMovimiento
from finanzas.infrastructure.db.engine import engine
from finanzas.infrastructure.repositories.repositorio_categorias_sqlmodel import (
    RepositorioCategoriasSQLModel,
)
from finanzas.infrastructure.repositories.repositorio_movimientos_sqlmodel import (
    RepositorioMovimientosSQLModel,
)

SELECCION_TIPO, SELECCION_CATEGORIA, INGRESAR_VALOR, INGRESAR_DESCRIPCION = range(
    4
)

user_data_store: dict[int, dict] = {}


def _obtener_repo_categorias():
    session = Session(engine)
    return RepositorioCategoriasSQLModel(session), session


async def start(update: Update, _context) -> int:

    keyboard = [
        [
            InlineKeyboardButton("Income", callback_data="INGRESO"),
            InlineKeyboardButton("Expense", callback_data="SALIDA"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select the type of movement:", reply_markup=reply_markup
    )
    return 0


async def seleccionar_tipo(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    tipo = query.data
    context.user_data["tipo"] = tipo


    from sqlmodel import Session

    from finanzas.infrastructure.db.engine import engine
    from finanzas.infrastructure.repositories.repositorio_categorias_sqlmodel import (
        RepositorioCategoriasSQLModel,
    )

    session = Session(engine)
    try:
        repo = RepositorioCategoriasSQLModel(session)
        categorias = repo.listar_activas()
        keyboard = [
            [InlineKeyboardButton(c.nombre, callback_data=str(c.id))]
            for c in categorias
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Select category:", reply_markup=reply_markup
        )
    finally:
        session.close()
    return 1


async def seleccionar_categoria(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["categoria_id"] = query.data
    await query.edit_message_text("Enter the amount:")
    return 2


async def ingresar_valor(update: Update, context) -> int:

    text = update.message.text.strip()
    try:
        valor = Decimal(text)
        if valor <= 0:
            await update.message.reply_text("Amount must be positive. Try again:")
            return 2
        context.user_data["valor"] = valor
        await update.message.reply_text(
            "Enter a description (optional, or send /skip):"
        )
        return 3
    except InvalidOperation:
        await update.message.reply_text("Invalid amount. Try again:")
        return 2


async def ingresar_descripcion(update: Update, context) -> int:

    from sqlmodel import Session

    from finanzas.infrastructure.db.engine import engine
    from finanzas.infrastructure.repositories.repositorio_categorias_sqlmodel import (
        RepositorioCategoriasSQLModel,
    )
    from finanzas.infrastructure.repositories.repositorio_movimientos_sqlmodel import (
        RepositorioMovimientosSQLModel,
    )

    text = update.message.text.strip()
    descripcion = None if text == "/skip" else text

    session = Session(engine)
    try:
        repo_mov = RepositorioMovimientosSQLModel(session)
        repo_cat = RepositorioCategoriasSQLModel(session)
        use_case = RegistrarMovimiento(repo_mov, repo_cat)
        movimiento = use_case.ejecutar(
            tipo=TipoMovimiento(context.user_data["tipo"]),
            categoria_id=UUID(context.user_data["categoria_id"]),
            fecha=date.today(),
            valor=context.user_data["valor"],
            descripcion=descripcion,
        )
        await update.message.reply_text(
            f"Movement registered!\n"
            f"Type: {movimiento.tipo.value}\n"
            f"Amount: {movimiento.valor:.2f}\n"
            f"Description: {movimiento.descripcion or '(none)'}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        session.close()
    return -1


async def skip_descripcion(update: Update, context) -> int:
    context.user_data["descripcion"] = None
    return await ingresar_descripcion(update, context)


async def cmd_balance(update: Update, _context) -> None:
    from datetime import date

    session = Session(engine)
    try:
        repo_mov = RepositorioMovimientosSQLModel(session)
        use_case = ObtenerBalanceMensual(repo_mov)
        today = date.today()
        balance = use_case.ejecutar(today.year, today.month)
        await update.message.reply_text(
            f"*Balance for {today.strftime('%B %Y')}*\n"
            f"Income: {balance.total_ingresos}\n"
            f"Expenses: {balance.total_gastos}\n"
            f"Net: {balance.balance_neto}\n"
            + (
                f"Savings rate: {balance.tasa_ahorro:.1f}%"
                if balance.tasa_ahorro is not None
                else ""
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        session.close()


async def cmd_listar(update: Update, _context) -> None:
    from datetime import date

    session = Session(engine)
    try:
        repo_mov = RepositorioMovimientosSQLModel(session)
        use_case = ListarMovimientos(repo_mov)
        today = date.today()
        inicio = today.replace(day=1)
        movimientos = use_case.ejecutar(inicio, today)
        if not movimientos:
            await update.message.reply_text("No movements this month.")
            return
        lines = ["*Movements this month:*"]
        for m in movimientos[:10]:
            lines.append(
                f"{m.fecha} | {m.tipo.value:8s} | {m.valor:>10.2f} | "
                f"{m.descripcion or ''}"
            )
        if len(movimientos) > 10:
            lines.append(f"... and {len(movimientos) - 10} more")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        session.close()


def obtener_handlers() -> list:

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [CallbackQueryHandler(seleccionar_tipo)],
            1: [CallbackQueryHandler(seleccionar_categoria)],
            2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_valor)
            ],
            3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ingresar_descripcion),
                CommandHandler("skip", skip_descripcion),
            ],
        },
        fallbacks=[],
    )
    return [
        conv_handler,
        CommandHandler("balance", cmd_balance),
        CommandHandler("listar", cmd_listar),
    ]
