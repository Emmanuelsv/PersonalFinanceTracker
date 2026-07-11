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


class TestCalculadoraAvanzada:
    def setup_method(self) -> None:
        self.calc = CalculadoraFinanciera()
        self.cat_fija = uuid4()
        self.cat_variable = uuid4()

    def _mov(
        self,
        tipo: TipoMovimiento,
        valor: str,
        dia: int,
        cat_id: uuid4 | None = None,
        descripcion: str | None = None,
    ) -> Movimiento:
        return Movimiento(
            tipo=tipo,
            categoria_id=cat_id or self.cat_variable,
            fecha=date(2025, 1, dia),
            valor=Decimal(valor),
            descripcion=descripcion,
            fuente=FuenteMovimiento.MANUAL,
        )

    def test_gasto_fijo_vs_variable(self) -> None:
        movs = [
            self._mov(TipoMovimiento.SALIDA, "50000", 1, self.cat_fija),
            self._mov(TipoMovimiento.SALIDA, "30000", 5, self.cat_variable),
            self._mov(TipoMovimiento.SALIDA, "50000", 10, self.cat_fija),
        ]
        resultado = self.calc.gasto_fijo_vs_variable(
            movs, {self.cat_fija}
        )
        assert resultado["fijo"] == Decimal("100000")
        assert resultado["variable"] == Decimal("30000")

    def test_detectar_anomalias(self) -> None:
        cat = uuid4()
        historicos = [
            self._mov(TipoMovimiento.SALIDA, "10000", 1, cat),
            self._mov(TipoMovimiento.SALIDA, "10000", 8, cat),
            self._mov(TipoMovimiento.SALIDA, "10000", 15, cat),
        ]
        actuales = [
            self._mov(TipoMovimiento.SALIDA, "25000", 5, cat),
        ]
        anomalias = self.calc.detectar_anomalias(historicos, actuales, umbral=0.1)
        assert len(anomalias) > 0
        assert anomalias[0]["categoria_id"] == cat

    def test_sin_anomalias(self) -> None:
        cat = uuid4()
        historicos = [
            self._mov(TipoMovimiento.SALIDA, "10000", 1, cat),
        ]
        actuales = [
            self._mov(TipoMovimiento.SALIDA, "10000", 5, cat),
        ]
        anomalias = self.calc.detectar_anomalias(historicos, actuales, umbral=0.3)
        assert len(anomalias) == 0

    def test_indice_salud_alto(self) -> None:
        periodo = Periodo.for_month(2025, 1)
        balance = self.calc.calcular_balance_mensual(
            [self._mov(TipoMovimiento.INGRESO, "1000000", 1, self.cat_fija)],
            periodo,
        )
        score = self.calc.indice_salud_financiera(balance, 5)
        assert score >= 40

    def test_indice_salud_bajo(self) -> None:
        periodo = Periodo.for_month(2025, 1)
        balance = self.calc.calcular_balance_mensual(
            [self._mov(TipoMovimiento.SALIDA, "100000", 1)],
            periodo,
        )
        score = self.calc.indice_salud_financiera(balance, 0)
        assert score < 40

    def test_costo_suscripciones(self) -> None:
        cat = uuid4()
        movs = [
            self._mov(TipoMovimiento.SALIDA, "15000", 1, cat, "Netflix"),
            self._mov(TipoMovimiento.SALIDA, "15000", 8, cat, "Netflix"),
            self._mov(TipoMovimiento.SALIDA, "15000", 15, cat, "Netflix"),
        ]
        total = self.calc.costo_suscripciones(movs, meses=3)
        assert total == Decimal("15000")

    def test_proyeccion_fin_mes(self) -> None:
        from datetime import date, timedelta
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        fin_mes = hoy.replace(day=28) + timedelta(days=4)
        fin_mes = fin_mes.replace(day=1) - timedelta(days=1)
        periodo = Periodo(inicio_mes, fin_mes)
        movs = [
            self._mov(TipoMovimiento.SALIDA, "30000", hoy.day),
        ]
        proyeccion = self.calc.proyeccion_fin_mes(movs, periodo)
        assert proyeccion > Decimal("0")
