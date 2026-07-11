from datetime import date

import pytest

from finanzas.domain.value_objects.periodo import Periodo


class TestPeriodo:
    def test_crear_periodo_valido(self) -> None:
        p = Periodo(fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 1, 31))
        assert p.fecha_inicio == date(2025, 1, 1)
        assert p.fecha_fin == date(2025, 1, 31)

    def test_fecha_inicio_despues_de_fecha_fin_lanza_error(self) -> None:
        with pytest.raises(ValueError):
            Periodo(
                fecha_inicio=date(2025, 2, 1),
                fecha_fin=date(2025, 1, 31),
            )

    def test_contains_fecha_dentro(self) -> None:
        p = Periodo(fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 1, 31))
        assert p.contains(date(2025, 1, 15))

    def test_contains_fecha_fuera(self) -> None:
        p = Periodo(fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 1, 31))
        assert not p.contains(date(2025, 2, 1))

    def test_for_month(self) -> None:
        p = Periodo.for_month(2025, 2)
        assert p.fecha_inicio == date(2025, 2, 1)
        assert p.fecha_fin == date(2025, 2, 28)
