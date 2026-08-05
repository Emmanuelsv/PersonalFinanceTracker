from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from finanzas.application.use_cases.eliminar_ultimo_movimiento import (
    EliminarUltimoMovimiento,
    NoHayMovimientosError,
)
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)


class TestEliminarUltimoMovimiento:
    def setup_method(self) -> None:
        self.repo_mov = MagicMock()
        self.use_case = EliminarUltimoMovimiento(self.repo_mov)

    def test_elimina_ultimo_cuando_existe(self) -> None:
        ultimo = Movimiento(
            tipo=TipoMovimiento.SALIDA,
            fecha=date(2025, 1, 15),
            valor=Decimal("25000"),
            descripcion="Almuerzo",
            fuente=FuenteMovimiento.MANUAL,
        )
        self.repo_mov.obtener_ultimo.return_value = ultimo

        resultado = self.use_case.ejecutar()

        assert resultado == ultimo
        self.repo_mov.eliminar.assert_called_once_with(ultimo.id)

    def test_retorna_none_cuando_no_hay_movimientos(self) -> None:
        self.repo_mov.obtener_ultimo.return_value = None

        with pytest.raises(NoHayMovimientosError):
            self.use_case.ejecutar()

        self.repo_mov.eliminar.assert_not_called()
