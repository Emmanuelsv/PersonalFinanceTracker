from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from finanzas.domain.entities.movimiento import (
    Movimiento,
    TipoMovimiento,
)
from finanzas.domain.value_objects.dinero import Dinero
from finanzas.domain.value_objects.periodo import Periodo


class BalanceMensual:
    def __init__(
        self,
        periodo: Periodo,
        total_ingresos: Dinero,
        total_gastos: Dinero,
    ) -> None:
        self.periodo = periodo
        self.total_ingresos = total_ingresos
        self.total_gastos = total_gastos
        self.balance_neto = total_ingresos - total_gastos

    @property
    def tasa_ahorro(self) -> float | None:
        if self.total_ingresos.cantidad == 0:
            return None
        return float(
            (self.balance_neto.cantidad / self.total_ingresos.cantidad) * 100
        )


class CalculadoraFinanciera:
    def calcular_balance_mensual(
        self, movimientos: list[Movimiento], periodo: Periodo
    ) -> BalanceMensual:
        ingresos = sum(
            (m.valor for m in movimientos if m.tipo == TipoMovimiento.INGRESO),
            Decimal("0"),
        )
        gastos = sum(
            (m.valor for m in movimientos if m.tipo == TipoMovimiento.SALIDA),
            Decimal("0"),
        )
        return BalanceMensual(
            periodo=periodo,
            total_ingresos=Dinero(cantidad=ingresos),
            total_gastos=Dinero(cantidad=gastos),
        )

    def gasto_por_categoria(
        self, movimientos: list[Movimiento]
    ) -> dict[UUID, Decimal]:
        result: dict[UUID, Decimal] = {}
        for m in movimientos:
            if m.tipo == TipoMovimiento.SALIDA and m.categoria_id is not None:
                result[m.categoria_id] = (
                    result.get(m.categoria_id, Decimal("0")) + m.valor
                )
        return result

    def calcular_promedio_mensual(
        self, movimientos: list[Movimiento], meses: int = 3
    ) -> Decimal:
        if not movimientos:
            return Decimal("0")
        total = sum((m.valor for m in movimientos), Decimal("0"))
        return total / Decimal(str(meses))

    def gasto_fijo_vs_variable(
        self,
        movimientos: list[Movimiento],
        categorias_fijas: set[UUID],
    ) -> dict[str, Decimal]:
        fijo = Decimal("0")
        variable = Decimal("0")
        for m in movimientos:
            if m.tipo == TipoMovimiento.SALIDA:
                if m.categoria_id is not None and m.categoria_id in categorias_fijas:
                    fijo += m.valor
                else:
                    variable += m.valor
        return {"fijo": fijo, "variable": variable}

    def detectar_anomalias(
        self,
        movimientos_ultimos_meses: list[Movimiento],
        movimientos_mes_actual: list[Movimiento],
        umbral: float = 0.4,
    ) -> list[dict[str, object]]:
        gasto_historico = self.gasto_por_categoria(movimientos_ultimos_meses)
        total_historico = sum(gasto_historico.values(), Decimal("0"))
        gasto_actual = self.gasto_por_categoria(movimientos_mes_actual)
        total_actual = sum(gasto_actual.values(), Decimal("0"))

        anomalias: list[dict[str, object]] = []
        if total_historico == 0 or total_actual == 0:
            return anomalias

        for cat_id, actual in gasto_actual.items():
            historico = gasto_historico.get(cat_id, Decimal("0"))
            if historico == 0:
                continue
            cambio = float((actual - historico) / historico)
            if abs(cambio) > umbral:
                anomalias.append(
                    {
                        "categoria_id": cat_id,
                        "cambio_pct": round(cambio * 100, 1),
                        "actual": actual,
                        "historico": historico,
                    }
                )
        return anomalias

    def proyeccion_fin_mes(
        self,
        movimientos: list[Movimiento],
        periodo: Periodo,
    ) -> Decimal:
        hoy = date.today()
        if hoy < periodo.fecha_inicio or hoy > periodo.fecha_fin:
            return Decimal("0")
        dias_transcurridos = (hoy - periodo.fecha_inicio).days + 1
        if dias_transcurridos <= 0:
            return Decimal("0")
        total_gasto = sum(
            (m.valor for m in movimientos if m.tipo == TipoMovimiento.SALIDA),
            Decimal("0"),
        )
        dias_totales = (periodo.fecha_fin - periodo.fecha_inicio).days + 1
        promedio_diario = total_gasto / Decimal(str(dias_transcurridos))
        return promedio_diario * Decimal(str(dias_totales))

    def indice_salud_financiera(
        self,
        balance: BalanceMensual,
        num_categorias_gasto: int,
        total_prestamos: Decimal = Decimal("0"),
    ) -> float:
        score = 0.0
        if balance.tasa_ahorro is not None:
            if balance.tasa_ahorro >= 20:
                score += 40
            elif balance.tasa_ahorro >= 10:
                score += 25
            elif balance.tasa_ahorro >= 0:
                score += 10
        if num_categorias_gasto >= 3:
            score += 20
        elif num_categorias_gasto >= 1:
            score += 10
        if total_prestamos == 0:
            score += 20
        elif total_prestamos < balance.total_ingresos.cantidad * Decimal("0.3"):
            score += 10
        score = min(score, 100.0)
        return score

    def costo_suscripciones(
        self,
        movimientos: list[Movimiento],
        meses: int = 3,
        tolerancia: Decimal = Decimal("0.1"),
    ) -> Decimal:

        candidatos: dict[UUID, list[Decimal]] = defaultdict(list)
        for m in movimientos:
            if m.tipo == TipoMovimiento.SALIDA and m.descripcion and m.categoria_id is not None:
                candidatos[m.categoria_id].append(m.valor)
        total_suscripciones = Decimal("0")
        for valores in candidatos.values():
            if len(valores) < meses:
                continue
            avg = sum(valores, Decimal("0")) / Decimal(str(len(valores)))
            es_recurrente = all(
                abs(v - avg) <= avg * tolerancia for v in valores
            )
            if es_recurrente:
                total_suscripciones += avg
        return total_suscripciones
