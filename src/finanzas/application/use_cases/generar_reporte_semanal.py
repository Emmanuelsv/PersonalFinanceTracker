from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from finanzas.application.ports.enviador_email import EnviadorEmail
from finanzas.application.ports.repositorio_categorias import (
    RepositorioCategorias,
)
from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.application.services.calculadora_financiera import (
    CalculadoraFinanciera,
)
from finanzas.domain.entities.reporte_generado import ReporteGenerado
from finanzas.domain.value_objects.periodo import Periodo
from finanzas.infrastructure.db.engine import engine


class GenerarReporteSemanal:
    def __init__(
        self,
        repo_movimientos: RepositorioMovimientos,
        repo_categorias: RepositorioCategorias,
        enviador_email: EnviadorEmail,
        calculadora: CalculadoraFinanciera | None = None,
    ) -> None:
        self.repo_movimientos = repo_movimientos
        self.repo_categorias = repo_categorias
        self.enviador_email = enviador_email
        self.calculadora = calculadora or CalculadoraFinanciera()

    def _generar_recomendaciones(
        self,
        _balance_actual: object,
        _balance_anterior: object,
        gasto_categorias: dict[UUID, Decimal],
        categorias_nombre: dict[UUID, str],
    ) -> list[str]:
        recomendaciones: list[str] = []
        top_categoria = max(
            gasto_categorias, key=lambda k: gasto_categorias[k], default=None
        )
        if top_categoria and top_categoria in categorias_nombre:
            recomendaciones.append(
                f"Your highest expense category this week is "
                f"'{categorias_nombre[top_categoria]}' "
                f"({gasto_categorias[top_categoria]:.2f})."
            )
        return recomendaciones

    def ejecutar(self, email_to: str) -> ReporteGenerado:
        hoy = date.today()
        lunes_actual = hoy - timedelta(days=hoy.weekday())
        domingo_actual = lunes_actual + timedelta(days=6)
        lunes_anterior = lunes_actual - timedelta(days=7)
        domingo_anterior = lunes_anterior + timedelta(days=6)

        mov_actual = self.repo_movimientos.listar_por_periodo(
            lunes_actual, domingo_actual
        )
        mov_anterior = self.repo_movimientos.listar_por_periodo(
            lunes_anterior, domingo_anterior
        )

        periodo_actual = Periodo(lunes_actual, domingo_actual)
        balance_actual = self.calculadora.calcular_balance_mensual(
            mov_actual, periodo_actual
        )
        periodo_anterior = Periodo(lunes_anterior, domingo_anterior)
        balance_anterior = self.calculadora.calcular_balance_mensual(
            mov_anterior, periodo_anterior
        )

        categorias = self.repo_categorias.listar_todas()
        categorias_nombre = {c.id: c.nombre for c in categorias}

        gasto_por_cat = self.calculadora.gasto_por_categoria(mov_actual)
        recomendaciones = self._generar_recomendaciones(
            balance_actual,
            balance_anterior,
            gasto_por_cat,
            categorias_nombre,
        )

        payload = {
            "periodo_inicio": lunes_actual.isoformat(),
            "periodo_fin": domingo_actual.isoformat(),
            "total_ingresos": str(balance_actual.total_ingresos.cantidad),
            "total_gastos": str(balance_actual.total_gastos.cantidad),
            "balance_neto": str(balance_actual.balance_neto.cantidad),
            "tasa_ahorro": balance_actual.tasa_ahorro,
            "gasto_por_categoria": {
                str(cat_id): {
                    "nombre": categorias_nombre.get(cat_id, "Unknown"),
                    "valor": str(valor),
                }
                for cat_id, valor in gasto_por_cat.items()
            },
            "recomendaciones": recomendaciones,
        }

        reporte = ReporteGenerado(
            periodo_inicio=lunes_actual,
            periodo_fin=domingo_actual,
            payload_json=payload,
        )

        from sqlmodel import Session

        session = Session(engine)
        try:
            session.add(reporte)
            session.commit()
            session.refresh(reporte)
        finally:
            session.close()

        cuerpo_html = self._armar_html(payload, categorias_nombre)
        self.enviador_email.enviar(
            para=email_to,
            asunto=f"Weekly Financial Report - {lunes_actual} to {domingo_actual}",
            cuerpo_html=cuerpo_html,
        )
        return reporte

    def _armar_html(
        self,
        payload: dict[str, Any],
        _categorias_nombre: dict[UUID, str],
    ) -> str:
        gastos_html = ""
        for _cat_id_str, info in payload.get("gasto_por_categoria", {}).items():
            gastos_html += (
                f"<li><b>{info['nombre']}</b>: {info['valor']} COP</li>"
            )
        recomendaciones_html = ""
        for r in payload.get("recomendaciones", []):
            recomendaciones_html += f"<li>{r}</li>"

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Weekly Financial Report</h2>
            <p>Period: {payload['periodo_inicio']} to {payload['periodo_fin']}</p>
            <table border="1" cellpadding="8" style="border-collapse: collapse;">
                <tr><td>Total Income</td><td>{payload['total_ingresos']} COP</td></tr>
                <tr><td>Total Expenses</td><td>{payload['total_gastos']} COP</td></tr>
                <tr><td>Net Balance</td><td>{payload['balance_neto']} COP</td></tr>
                <tr><td>Savings Rate</td><td>{payload['tasa_ahorro'] or 'N/A'}%</td></tr>
            </table>
            <h3>Expenses by Category</h3>
            <ul>{gastos_html}</ul>
            <h3>Recommendations</h3>
            <ul>{recomendaciones_html}</ul>
        </body>
        </html>
        """
