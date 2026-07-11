from uuid import UUID

from sqlmodel import Session, select

from finanzas.application.ports.repositorio_categorias import (
    RepositorioCategorias,
)
from finanzas.domain.entities.categoria import Categoria


class RepositorioCategoriasSQLModel(RepositorioCategorias):
    def __init__(self, session: Session) -> None:
        self.session = session

    def guardar(self, categoria: Categoria) -> Categoria:
        self.session.add(categoria)
        self.session.commit()
        self.session.refresh(categoria)
        return categoria

    def obtener_por_id(self, categoria_id: UUID) -> Categoria | None:
        return self.session.get(Categoria, categoria_id)

    def obtener_por_nombre(self, nombre: str) -> Categoria | None:
        stmt = select(Categoria).where(Categoria.nombre == nombre)
        return self.session.exec(stmt).first()

    def listar_activas(self) -> list[Categoria]:
        stmt = select(Categoria).where(Categoria.activo)
        return list(self.session.exec(stmt).all())

    def listar_todas(self) -> list[Categoria]:
        stmt = select(Categoria)
        return list(self.session.exec(stmt).all())
