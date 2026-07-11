from datetime import date
from unittest.mock import MagicMock

from finanzas.application.use_cases.listar_movimientos import (
    ListarMovimientos,
)


class TestListarMovimientos:
    def setup_method(self) -> None:
        self.repo_mov = MagicMock()
        self.use_case = ListarMovimientos(self.repo_mov)

    def test_listar_todos(self) -> None:
        self.repo_mov.listar_todos.return_value = []
        resultado = self.use_case.ejecutar()
        assert resultado == []
        self.repo_mov.listar_todos.assert_called_once()

    def test_listar_por_periodo(self) -> None:

        self.repo_mov.listar_por_periodo.return_value = []
        resultado = self.use_case.ejecutar(
            fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 1, 31)
        )
        assert resultado == []
        self.repo_mov.listar_por_periodo.assert_called_once_with(
            date(2025, 1, 1), date(2025, 1, 31)
        )
