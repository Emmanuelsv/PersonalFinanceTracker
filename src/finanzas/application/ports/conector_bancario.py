from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from finanzas.domain.entities.movimiento import Movimiento


class ConectorBancario(ABC):
    @abstractmethod
    def obtener_movimientos(
        self, cuenta_id: UUID, desde: date, hasta: date
    ) -> list[Movimiento]: ...
