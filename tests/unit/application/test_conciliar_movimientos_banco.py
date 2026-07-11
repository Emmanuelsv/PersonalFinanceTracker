from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from finanzas.application.use_cases.conciliar_movimientos_banco import (
    ConciliarMovimientosBanco,
)
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)


class TestConciliarMovimientosBanco:
    def setup_method(self) -> None:
        self.conector = MagicMock()
        self.repo_mov = MagicMock()
        self.use_case = ConciliarMovimientosBanco(
            self.conector, self.repo_mov
        )
        self.cuenta_id = uuid4()

    def _crear_movimiento_banco(
        self, hash_conc: str | None = None
    ) -> Movimiento:
        m = Movimiento(
            tipo=TipoMovimiento.SALIDA,
            categoria_id=None,
            fecha=date(2025, 1, 15),
            valor=Decimal("25000"),
            descripcion="Supermarket",
            fuente=FuenteMovimiento.BANCO_AUTOMATICO,
            cuenta_id=self.cuenta_id,
        )
        m.hash_conciliacion = hash_conc or "test_hash"
        return m

    def test_conciliar_movimientos_nuevos(self) -> None:
        movs = [
            self._crear_movimiento_banco("hash_1"),
            self._crear_movimiento_banco("hash_2"),
        ]
        self.conector.obtener_movimientos.return_value = movs
        self.repo_mov.buscar_por_hash.return_value = None
        self.repo_mov.guardar.return_value = MagicMock()

        resultado = self.use_case.ejecutar(
            self.cuenta_id, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert resultado.importados == 2
        assert resultado.duplicados == 0
        assert resultado.errores == 0

    def test_conciliar_duplicados(self) -> None:
        movs = [
            self._crear_movimiento_banco("hash_1"),
            self._crear_movimiento_banco("hash_1"),
        ]
        self.conector.obtener_movimientos.return_value = movs
        self.repo_mov.buscar_por_hash.return_value = MagicMock()

        resultado = self.use_case.ejecutar(
            self.cuenta_id, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert resultado.importados == 0
        assert resultado.duplicados == 2
        assert resultado.errores == 0

    def test_conciliar_error_en_conector(self) -> None:
        self.conector.obtener_movimientos.side_effect = Exception(
            "Connection failed"
        )
        resultado = self.use_case.ejecutar(
            self.cuenta_id, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert resultado.importados == 0
        assert resultado.errores == 1
