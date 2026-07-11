from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TipoAsociado(StrEnum):
    INGRESO = "INGRESO"
    SALIDA = "SALIDA"
    AMBOS = "AMBOS"


class Categoria(SQLModel, table=True):
    __tablename__ = "categorias"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, nullable=False)
    tipo_asociado: TipoAsociado
    activo: bool = True
