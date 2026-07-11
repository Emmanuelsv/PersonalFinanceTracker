from datetime import date

from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.domain.entities.movimiento import Movimiento


class ListarMovimientos:
    def __init__(
        self, repo_movimientos: RepositorioMovimientos
    ) -> None:
        self.repo_movimientos = repo_movimientos

    def ejecutar(
        self,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
    ) -> list[Movimiento]:
        if fecha_inicio and fecha_fin:
            return self.repo_movimientos.listar_por_periodo(
                fecha_inicio, fecha_fin
            )
        return self.repo_movimientos.listar_todos()
