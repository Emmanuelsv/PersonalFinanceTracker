from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.application.services.calculadora_financiera import (
    BalanceMensual,
    CalculadoraFinanciera,
)
from finanzas.domain.value_objects.periodo import Periodo


class ObtenerBalanceMensual:
    def __init__(
        self,
        repo_movimientos: RepositorioMovimientos,
        calculadora: CalculadoraFinanciera | None = None,
    ) -> None:
        self.repo_movimientos = repo_movimientos
        self.calculadora = calculadora or CalculadoraFinanciera()

    def ejecutar(self, year: int, month: int) -> BalanceMensual:
        periodo = Periodo.for_month(year, month)
        movimientos = self.repo_movimientos.listar_por_periodo(
            periodo.fecha_inicio, periodo.fecha_fin
        )
        return self.calculadora.calcular_balance_mensual(movimientos, periodo)
