from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from finanzas.application.use_cases.obtener_balance import (
    ObtenerBalanceMensual,
)
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)


class TestObtenerBalanceMensual:
    def setup_method(self) -> None:
        self.repo_mov = MagicMock()
        self.use_case = ObtenerBalanceMensual(self.repo_mov)

    def test_balance_mensual(self) -> None:

        cat_id = uuid4()
        movimientos = [
            Movimiento(
                tipo=TipoMovimiento.INGRESO,
                categoria_id=cat_id,
                fecha=date(2025, 1, 1),
                valor=Decimal("1000000"),
                fuente=FuenteMovimiento.MANUAL,
            ),
            Movimiento(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=cat_id,
                fecha=date(2025, 1, 15),
                valor=Decimal("250000"),
                fuente=FuenteMovimiento.MANUAL,
            ),
        ]
        self.repo_mov.listar_por_periodo.return_value = movimientos
        balance = self.use_case.ejecutar(2025, 1)
        assert balance.total_ingresos.cantidad == Decimal("1000000")
        assert balance.total_gastos.cantidad == Decimal("250000")
        assert balance.balance_neto.cantidad == Decimal("750000")
