from datetime import UTC, date, datetime
from uuid import UUID

from sqlmodel import Session, asc, select

from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.domain.entities.movimiento import Movimiento


class RepositorioMovimientosSQLModel(RepositorioMovimientos):
    def __init__(self, session: Session) -> None:
        self.session = session

    def guardar(self, movimiento: Movimiento) -> Movimiento:
        now = datetime.now(UTC)
        if not movimiento.creado_en:
            movimiento.creado_en = now
        movimiento.actualizado_en = now
        self.session.add(movimiento)
        self.session.commit()
        self.session.refresh(movimiento)
        return movimiento

    def obtener_por_id(self, movimiento_id: UUID) -> Movimiento | None:
        return self.session.get(Movimiento, movimiento_id)

    def listar_por_periodo(
        self, fecha_inicio: date, fecha_fin: date
    ) -> list[Movimiento]:
        stmt = (
            select(Movimiento)
            .where(Movimiento.fecha >= fecha_inicio)
            .where(Movimiento.fecha <= fecha_fin)
            .order_by(asc(Movimiento.fecha))
        )
        return list(self.session.exec(stmt).all())

    def listar_todos(self) -> list[Movimiento]:
        stmt = select(Movimiento).order_by(asc(Movimiento.fecha))
        return list(self.session.exec(stmt).all())

    def buscar_por_hash(self, hash_conciliacion: str) -> Movimiento | None:
        stmt = select(Movimiento).where(
            Movimiento.hash_conciliacion == hash_conciliacion
        )
        return self.session.exec(stmt).first()

    def eliminar(self, movimiento_id: UUID) -> None:
        movimiento = self.obtener_por_id(movimiento_id)
        if movimiento:
            self.session.delete(movimiento)
            self.session.commit()
