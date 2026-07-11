from datetime import date
from decimal import Decimal
from uuid import UUID

import typer
from sqlmodel import Session

from finanzas.application.use_cases.importar_csv import ImportarCSV
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

app = typer.Typer()


def _obtener_servicios():

    session = Session(engine)
    repo_mov = RepositorioMovimientosSQLModel(session)
    repo_cat = RepositorioCategoriasSQLModel(session)
    return session, repo_mov, repo_cat


@app.command()
def registrar(
    tipo: str = typer.Argument(help="INGRESO or SALIDA"),
    categoria_id: str = typer.Argument(help="Category UUID"),
    fecha: str = typer.Argument(help="Date in YYYY-MM-DD format"),
    valor: str = typer.Argument(help="Amount"),
    descripcion: str | None = typer.Option(None, "--descripcion", "-d"),
) -> None:

    session, repo_mov, repo_cat = _obtener_servicios()
    try:
        use_case = RegistrarMovimiento(repo_mov, repo_cat)
        movimiento = use_case.ejecutar(
            tipo=TipoMovimiento(tipo.upper()),
            categoria_id=UUID(categoria_id),
            fecha=date.fromisoformat(fecha),
            valor=Decimal(str(valor)),
            descripcion=descripcion,
        )
        typer.echo(f"Movement registered: {movimiento.id}")
    finally:
        session.close()


@app.command()
def listar(
    fecha_inicio: str | None = typer.Option(None, "--desde"),
    fecha_fin: str | None = typer.Option(None, "--hasta"),
) -> None:
    session, repo_mov, _ = _obtener_servicios()
    try:
        use_case = ListarMovimientos(repo_mov)
        desde = date.fromisoformat(fecha_inicio) if fecha_inicio else None
        hasta = date.fromisoformat(fecha_fin) if fecha_fin else None
        movimientos = use_case.ejecutar(desde, hasta)
        for m in movimientos:
            typer.echo(
                f"{m.fecha} | {m.tipo.value:8s} | {m.valor:>10.2f} | "
                f"{m.categoria_id} | {m.descripcion or ''}"
            )
    finally:
        session.close()


@app.command()
def balance(
    year: int = typer.Argument(..., help="Year"),
    month: int = typer.Argument(..., help="Month (1-12)"),
) -> None:
    session, repo_mov, _ = _obtener_servicios()
    try:
        use_case = ObtenerBalanceMensual(repo_mov)
        balance = use_case.ejecutar(year, month)
        typer.echo(f"Period: {balance.periodo.fecha_inicio} to {balance.periodo.fecha_fin}")
        typer.echo(f"Income:      {balance.total_ingresos}")
        typer.echo(f"Expenses:    {balance.total_gastos}")
        typer.echo(f"Net balance: {balance.balance_neto}")
        if balance.tasa_ahorro is not None:
            typer.echo(f"Savings rate: {balance.tasa_ahorro:.1f}%")
    finally:
        session.close()


@app.command()
def importar_csv(
    archivo: str = typer.Argument(help="Path to CSV file"),
) -> None:
    import pandas as pd

    session, repo_mov, repo_cat = _obtener_servicios()
    try:
        df = pd.read_csv(archivo)
        filas = df.to_dict("records")
        use_case = ImportarCSV(repo_mov, repo_cat)
        resultado = use_case.ejecutar(filas)
        typer.echo(
            f"Imported: {resultado.importados}, "
            f"Duplicates: {resultado.duplicados}, "
            f"Errors: {resultado.errores}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    app()
