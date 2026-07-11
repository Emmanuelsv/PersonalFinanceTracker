from datetime import date
from uuid import uuid4

from finanzas.domain.entities.movimiento import FuenteMovimiento
from finanzas.infrastructure.bancos.conector_simulado import ConectorSimulado


class TestConectorSimulado:
    def setup_method(self) -> None:
        self.conector = ConectorSimulado(seed=42)
        self.cuenta_id = uuid4()

    def test_genera_movimientos(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 31)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        assert len(movimientos) > 0
        assert all(m.cuenta_id == self.cuenta_id for m in movimientos)

    def test_movimientos_tienen_fuente_correcta(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        for m in movimientos:
            assert m.fuente == FuenteMovimiento.BANCO_AUTOMATICO

    def test_movimientos_sin_categoria(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        for m in movimientos:
            assert m.categoria_id is None

    def test_movimientos_tienen_hash(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        for m in movimientos:
            assert m.hash_conciliacion is not None
            assert len(m.hash_conciliacion) == 64

    def test_movimientos_fechas_en_rango(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        for m in movimientos:
            assert desde <= m.fecha <= hasta

    def test_movimientos_valores_positivos(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        movimientos = self.conector.obtener_movimientos(
            self.cuenta_id, desde, hasta
        )
        for m in movimientos:
            assert m.valor > 0

    def test_determinismo_misma_seed(self) -> None:
        desde = date(2025, 1, 1)
        hasta = date(2025, 1, 7)
        conector1 = ConectorSimulado(seed=123)
        conector2 = ConectorSimulado(seed=123)
        movs1 = conector1.obtener_movimientos(self.cuenta_id, desde, hasta)
        movs2 = conector2.obtener_movimientos(self.cuenta_id, desde, hasta)
        assert len(movs1) == len(movs2)
        for m1, m2 in zip(movs1, movs2):
            assert m1.valor == m2.valor
            assert m1.descripcion == m2.descripcion
            assert m1.hash_conciliacion == m2.hash_conciliacion
