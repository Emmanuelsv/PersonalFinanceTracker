from datetime import date
from decimal import Decimal
from hashlib import sha256
from typing import Any

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


class ResultadoImportacion:
    def __init__(
        self,
        importados: int = 0,
        duplicados: int = 0,
        errores: int = 0,
    ) -> None:
        self.importados = importados
        self.duplicados = duplicados
        self.errores = errores


class ImportarCSV:
    def __init__(
        self,
        repo_movimientos: RepositorioMovimientos,
        repo_categorias: RepositorioCategorias,
    ) -> None:
        self.repo_movimientos = repo_movimientos
        self.repo_categorias = repo_categorias

    def _generar_hash(
        self,
        fecha: date,
        valor: Decimal,
        descripcion: str | None,
        cuenta_id: str | None,
    ) -> str:
        raw = f"{fecha.isoformat()}|{valor}|{descripcion or ''}|{cuenta_id or ''}"
        return sha256(raw.encode()).hexdigest()

    def ejecutar(self, filas: list[dict[str, Any]]) -> ResultadoImportacion:
        importados = 0
        duplicados = 0
        errores = 0

        for fila in filas:
            try:
                categoria = self.repo_categorias.obtener_por_nombre(
                    fila["categoria"]
                )
                if not categoria:
                    errores += 1
                    continue

                hash_conc = self._generar_hash(
                    fila["fecha"],
                    fila["valor"],
                    fila.get("descripcion"),
                    None,
                )
                existente = self.repo_movimientos.buscar_por_hash(hash_conc)
                if existente:
                    duplicados += 1
                    continue

                tipo = TipoMovimiento(fila["tipo"])
                movimiento = Movimiento(
                    tipo=tipo,
                    categoria_id=categoria.id,
                    fecha=fila["fecha"],
                    valor=fila["valor"],
                    descripcion=fila.get("descripcion"),
                    fuente=FuenteMovimiento.IMPORTADO_CSV,
                    hash_conciliacion=hash_conc,
                )
                self.repo_movimientos.guardar(movimiento)
                importados += 1
            except Exception:
                errores += 1

        return ResultadoImportacion(
            importados=importados,
            duplicados=duplicados,
            errores=errores,
        )
