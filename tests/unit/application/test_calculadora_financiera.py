from datetime import date
from decimal import Decimal
from uuid import uuid4

from finanzas.application.services.calculadora_financiera import (
    CalculadoraFinanciera,
)
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)
from finanzas.domain.value_objects.periodo import Periodo


class TestCalculadoraFinanciera:
    def setup_method(self) -> None:
        self.calculadora = CalculadoraFinanciera()
        self.categoria_gasto_id = uuid4()
        self.categoria_ingreso_id = uuid4()

    def _crear_movimiento(
        self,
        tipo: TipoMovimiento,
        valor: str,
        dia: int,
        categoria_id: uuid4 | None = None,
    ) -> Movimiento:
        return Movimiento(
            tipo=tipo,
            categoria_id=categoria_id or self.categoria_gasto_id,
            fecha=date(2025, 1, dia),
            valor=Decimal(valor),
            fuente=FuenteMovimiento.MANUAL,
        )

    def test_balance_mensual_con_ingresos_y_gastos(self) -> None:
        movimientos = [
            self._crear_movimiento(
                TipoMovimiento.INGRESO, "1000000", 1, self.categoria_ingreso_id
            ),
            self._crear_movimiento(TipoMovimiento.SALIDA, "250000", 5),
            self._crear_movimiento(TipoMovimiento.SALIDA, "50000", 10),
        ]
        periodo = Periodo.for_month(2025, 1)
        balance = self.calculadora.calcular_balance_mensual(movimientos, periodo)
        assert balance.total_ingresos.cantidad == Decimal("1000000")
        assert balance.total_gastos.cantidad == Decimal("300000")
        assert balance.balance_neto.cantidad == Decimal("700000")

    def test_balance_sin_movimientos(self) -> None:
        periodo = Periodo.for_month(2025, 1)
        balance = self.calculadora.calcular_balance_mensual([], periodo)
        assert balance.total_ingresos.cantidad == Decimal("0")
        assert balance.total_gastos.cantidad == Decimal("0")
        assert balance.balance_neto.cantidad == Decimal("0")

    def test_balance_solo_gastos(self) -> None:
        movimientos = [
            self._crear_movimiento(TipoMovimiento.SALIDA, "100000", 5),
        ]
        periodo = Periodo.for_month(2025, 1)
        balance = self.calculadora.calcular_balance_mensual(movimientos, periodo)
        assert balance.total_ingresos.cantidad == Decimal("0")
        assert balance.total_gastos.cantidad == Decimal("100000")
        assert balance.balance_neto.cantidad == Decimal("-100000")

    def test_tasa_ahorro(self) -> None:
        movimientos = [
            self._crear_movimiento(
                TipoMovimiento.INGRESO, "1000000", 1, self.categoria_ingreso_id
            ),
            self._crear_movimiento(TipoMovimiento.SALIDA, "300000", 5),
        ]
        periodo = Periodo.for_month(2025, 1)
        balance = self.calculadora.calcular_balance_mensual(movimientos, periodo)
        assert balance.tasa_ahorro == 70.0

    def test_tasa_ahorro_sin_ingresos(self) -> None:
        periodo = Periodo.for_month(2025, 1)
        balance = self.calculadora.calcular_balance_mensual([], periodo)
        assert balance.tasa_ahorro is None

    def test_gasto_por_categoria(self) -> None:
        cat_a = uuid4()
        cat_b = uuid4()
        movimientos = [
            self._crear_movimiento(TipoMovimiento.SALIDA, "10000", 5, cat_a),
            self._crear_movimiento(TipoMovimiento.SALIDA, "20000", 10, cat_a),
            self._crear_movimiento(TipoMovimiento.SALIDA, "15000", 15, cat_b),
        ]
        resultado = self.calculadora.gasto_por_categoria(movimientos)
        assert resultado[cat_a] == Decimal("30000")
        assert resultado[cat_b] == Decimal("15000")

    def test_gasto_por_categoria_ignora_ingresos(self) -> None:
        movimientos = [
            self._crear_movimiento(
                TipoMovimiento.INGRESO, "1000000", 1, self.categoria_ingreso_id
            ),
            self._crear_movimiento(TipoMovimiento.SALIDA, "50000", 5),
        ]
        resultado = self.calculadora.gasto_por_categoria(movimientos)
        assert self.categoria_ingreso_id not in resultado

    def test_promedio_mensual(self) -> None:
        movimientos = [
            self._crear_movimiento(TipoMovimiento.SALIDA, "30000", 5),
            self._crear_movimiento(TipoMovimiento.SALIDA, "60000", 15),
        ]
        promedio = self.calculadora.calcular_promedio_mensual(movimientos, meses=3)
        assert promedio == Decimal("30000")

    def test_promedio_mensual_sin_movimientos(self) -> None:
        promedio = self.calculadora.calcular_promedio_mensual([], meses=3)
        assert promedio == Decimal("0")
