from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TipoMovimiento(StrEnum):
    INGRESO = "INGRESO"
    SALIDA = "SALIDA"


class FuenteMovimiento(StrEnum):
    MANUAL = "MANUAL"
    IMPORTADO_CSV = "IMPORTADO_CSV"
    BANCO_AUTOMATICO = "BANCO_AUTOMATICO"


class Movimiento(SQLModel, table=True):
    __tablename__ = "movimientos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tipo: TipoMovimiento
    categoria_id: UUID | None = Field(
        default=None, foreign_key="categorias.id", nullable=True
    )
    fecha: date
    valor: Decimal = Field(max_digits=12, decimal_places=2)
    descripcion: str | None = None
    fuente: FuenteMovimiento = FuenteMovimiento.MANUAL
    hash_conciliacion: str | None = Field(default=None, index=True)
    moneda: str = "COP"
    cuenta_id: UUID | None = Field(
        default=None, foreign_key="cuentas_bancarias.id"
    )
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None
