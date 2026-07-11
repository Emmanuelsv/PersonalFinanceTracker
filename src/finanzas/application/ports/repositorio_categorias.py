from abc import ABC, abstractmethod
from uuid import UUID

from finanzas.domain.entities.categoria import Categoria


class RepositorioCategorias(ABC):
    @abstractmethod
    def guardar(self, categoria: Categoria) -> Categoria: ...

    @abstractmethod
    def obtener_por_id(self, categoria_id: UUID) -> Categoria | None: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Categoria | None: ...

    @abstractmethod
    def listar_activas(self) -> list[Categoria]: ...

    @abstractmethod
    def listar_todas(self) -> list[Categoria]: ...
