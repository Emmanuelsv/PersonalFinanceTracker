from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine

from finanzas.domain.entities.categoria import Categoria, TipoAsociado
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)


@pytest.fixture
def categoria_comida() -> Categoria:
    return Categoria(
        nombre="Comida",
        tipo_asociado=TipoAsociado.SALIDA,
    )


@pytest.fixture
def categoria_salario() -> Categoria:
    return Categoria(
        nombre="Salario",
        tipo_asociado=TipoAsociado.INGRESO,
    )


@pytest.fixture
def movimiento_gasto(categoria_comida: Categoria) -> Movimiento:
    return Movimiento(
        tipo=TipoMovimiento.SALIDA,
        categoria_id=categoria_comida.id,
        fecha=date(2025, 1, 15),
        valor=Decimal("25000"),
        descripcion="Almuerzo",
        fuente=FuenteMovimiento.MANUAL,
    )


@pytest.fixture
def movimiento_ingreso(categoria_salario: Categoria) -> Movimiento:
    return Movimiento(
        tipo=TipoMovimiento.INGRESO,
        categoria_id=categoria_salario.id,
        fecha=date(2025, 1, 1),
        valor=Decimal("1000000"),
        descripcion="Salario enero",
        fuente=FuenteMovimiento.MANUAL,
    )


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
