from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from finanzas.domain.entities.movimiento import Movimiento


class RepositorioMovimientos(ABC):
    @abstractmethod
    def guardar(self, movimiento: Movimiento) -> Movimiento: ...

    @abstractmethod
    def obtener_por_id(self, movimiento_id: UUID) -> Movimiento | None: ...

    @abstractmethod
    def listar_por_periodo(
        self, fecha_inicio: date, fecha_fin: date
    ) -> list[Movimiento]: ...

    @abstractmethod
    def listar_todos(self) -> list[Movimiento]: ...

    @abstractmethod
    def buscar_por_hash(self, hash_conciliacion: str) -> Movimiento | None: ...

    @abstractmethod
    def eliminar(self, movimiento_id: UUID) -> None: ...
