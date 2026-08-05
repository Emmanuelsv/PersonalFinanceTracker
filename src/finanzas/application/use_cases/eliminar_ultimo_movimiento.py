
from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.domain.entities.movimiento import Movimiento


class NoHayMovimientosError(Exception):
    pass


class EliminarUltimoMovimiento:
    def __init__(self, repo_movimientos: RepositorioMovimientos) -> None:
        self.repo_movimientos = repo_movimientos

    def ejecutar(self) -> Movimiento:
        ultimo = self.repo_movimientos.obtener_ultimo()
        if not ultimo:
            raise NoHayMovimientosError(
                "No hay movimientos para eliminar"
            )
        self.repo_movimientos.eliminar(ultimo.id)
        return ultimo
