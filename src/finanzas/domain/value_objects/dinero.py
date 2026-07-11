from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Moneda(StrEnum):
    COP = "COP"
    USD = "USD"
    EUR = "EUR"


@dataclass(frozen=True)
class Dinero:
    cantidad: Decimal
    moneda: Moneda = Moneda.COP

    def __post_init__(self) -> None:
        pass

    def __add__(self, other: "Dinero") -> "Dinero":
        if self.moneda != other.moneda:
            raise ValueError(
                f"Cannot add different currencies: {self.moneda} vs {other.moneda}"
            )
        return Dinero(cantidad=self.cantidad + other.cantidad, moneda=self.moneda)

    def __sub__(self, other: "Dinero") -> "Dinero":
        if self.moneda != other.moneda:
            raise ValueError(
                f"Cannot subtract different currencies: {self.moneda} vs {other.moneda}"
            )
        return Dinero(cantidad=self.cantidad - other.cantidad, moneda=self.moneda)

    def __gt__(self, other: "Dinero") -> bool:
        if self.moneda != other.moneda:
            raise ValueError(
                f"Cannot compare different currencies: {self.moneda} vs {other.moneda}"
            )
        return self.cantidad > other.cantidad

    def __lt__(self, other: "Dinero") -> bool:
        if self.moneda != other.moneda:
            raise ValueError(
                f"Cannot compare different currencies: {self.moneda} vs {other.moneda}"
            )
        return self.cantidad < other.cantidad

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dinero):
            return NotImplemented
        return self.cantidad == other.cantidad and self.moneda == other.moneda

    def __repr__(self) -> str:
        return f"{self.cantidad:.2f} {self.moneda.value}"
