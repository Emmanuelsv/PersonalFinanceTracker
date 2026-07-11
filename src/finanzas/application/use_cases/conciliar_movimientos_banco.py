from dataclasses import dataclass
from datetime import date
from uuid import UUID

from finanzas.application.ports.conector_bancario import ConectorBancario
from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)


@dataclass
class ResultadoConciliacion:
    importados: int = 0
    duplicados: int = 0
    errores: int = 0


class ConciliarMovimientosBanco:
    def __init__(
        self,
        conector: ConectorBancario,
        repo_movimientos: RepositorioMovimientos,
    ) -> None:
        self.conector = conector
        self.repo_movimientos = repo_movimientos

    def ejecutar(
        self,
        cuenta_id: UUID,
        desde: date,
        hasta: date,
    ) -> ResultadoConciliacion:
        resultado = ResultadoConciliacion()

        try:
            movimientos_banco = self.conector.obtener_movimientos(
                cuenta_id, desde, hasta
            )
        except Exception:
            resultado.errores += 1
            return resultado

        for movimiento in movimientos_banco:
            try:
                if not movimiento.hash_conciliacion:
                    resultado.errores += 1
                    continue

                existente = self.repo_movimientos.buscar_por_hash(
                    movimiento.hash_conciliacion
                )
                if existente:
                    resultado.duplicados += 1
                    continue

                movimiento.cuenta_id = cuenta_id
                self.repo_movimientos.guardar(movimiento)
                resultado.importados += 1
            except Exception:
                resultado.errores += 1

        return resultado
