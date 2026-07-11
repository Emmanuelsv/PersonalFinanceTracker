import calendar
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Periodo:
    fecha_inicio: date
    fecha_fin: date

    def __post_init__(self) -> None:
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError(
                f"fecha_inicio ({self.fecha_inicio}) must be before or equal to "
                f"fecha_fin ({self.fecha_fin})"
            )

    def contains(self, d: date) -> bool:
        return self.fecha_inicio <= d <= self.fecha_fin

    @classmethod
    def for_month(cls, year: int, month: int) -> "Periodo":
        _, last_day = calendar.monthrange(year, month)
        return cls(
            fecha_inicio=date(year, month, 1),
            fecha_fin=date(year, month, last_day),
        )
