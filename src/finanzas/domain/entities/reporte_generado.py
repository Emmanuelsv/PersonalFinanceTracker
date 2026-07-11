from datetime import date, datetime
from uuid import UUID, uuid4

from sqlmodel import JSON, Field, SQLModel


class ReporteGenerado(SQLModel, table=True):
    __tablename__ = "reportes_generados"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    periodo_inicio: date
    periodo_fin: date
    payload_json: dict[str, object] = Field(default_factory=dict, sa_type=JSON)
    enviado_en: datetime | None = None
