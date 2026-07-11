from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TipoCuenta(StrEnum):
    AHORROS = "AHORROS"
    CORRIENTE = "CORRIENTE"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    INVERSION = "INVERSION"


class CuentaBancaria(SQLModel, table=True):
    __tablename__ = "cuentas_bancarias"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nombre: str = Field(max_length=100, nullable=False)
    entidad: str = Field(max_length=100, nullable=False)
    tipo_cuenta: TipoCuenta
    saldo_actual: Decimal | None = Field(
        default=None, max_digits=12, decimal_places=2
    )
    conector: str | None = Field(default=None, max_length=100)
