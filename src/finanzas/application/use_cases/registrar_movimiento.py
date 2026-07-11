from datetime import date
from decimal import Decimal
from uuid import UUID

from finanzas.application.ports.repositorio_categorias import (
    RepositorioCategorias,
)
from finanzas.application.ports.repositorio_movimientos import (
    RepositorioMovimientos,
)
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)
from finanzas.domain.exceptions import (
    CategoriaInexistenteError,
    MovimientoInvalidoError,
)


class RegistrarMovimiento:
    def __init__(
        self,
        repo_movimientos: RepositorioMovimientos,
        repo_categorias: RepositorioCategorias,
    ) -> None:
        self.repo_movimientos = repo_movimientos
        self.repo_categorias = repo_categorias

    def ejecutar(
        self,
        tipo: TipoMovimiento,
        categoria_id: UUID,
        fecha: date,
        valor: Decimal,
        descripcion: str | None = None,
        fuente: FuenteMovimiento = FuenteMovimiento.MANUAL,
        hash_conciliacion: str | None = None,
        cuenta_id: UUID | None = None,
        moneda: str = "COP",
    ) -> Movimiento:
        categoria = self.repo_categorias.obtener_por_id(categoria_id)
        if not categoria:
            raise CategoriaInexistenteError(
                f"Category {categoria_id} does not exist"
            )
        if valor <= Decimal("0"):
            raise MovimientoInvalidoError(
                f"Movement value must be positive: {valor}"
            )
        movimiento = Movimiento(
            tipo=tipo,
            categoria_id=categoria_id,
            fecha=fecha,
            valor=valor,
            descripcion=descripcion,
            fuente=fuente,
            hash_conciliacion=hash_conciliacion,
            cuenta_id=cuenta_id,
            moneda=moneda,
        )
        return self.repo_movimientos.guardar(movimiento)
