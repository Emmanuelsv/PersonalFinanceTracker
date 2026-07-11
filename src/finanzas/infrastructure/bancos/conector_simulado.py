from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from random import Random
from uuid import UUID

from finanzas.application.ports.conector_bancario import ConectorBancario
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)

DESCRIPCIONES_GASTO = [
    "Supermarket",
    "Gas station",
    "Restaurant",
    "Online purchase",
    "Utility bill",
    "Pharmacy",
    "ATM withdrawal",
    "Transfer",
]

DESCRIPCIONES_INGRESO = [
    "Salary",
    "Freelance payment",
    "Transfer received",
    "Interest payment",
]


class ConectorSimulado(ConectorBancario):
    def __init__(self, seed: int | None = None) -> None:
        self.random = Random(seed) if seed is not None else Random()

    def _generar_hash(
        self,
        fecha: date,
        valor: Decimal,
        descripcion: str | None,
        cuenta_id: UUID | None,
    ) -> str:
        raw = f"{fecha.isoformat()}|{valor}|{descripcion or ''}|{cuenta_id or ''}"
        return sha256(raw.encode()).hexdigest()

    def obtener_movimientos(
        self,
        cuenta_id: UUID,
        desde: date,
        hasta: date,
    ) -> list[Movimiento]:
        movimientos: list[Movimiento] = []
        delta = (hasta - desde).days
        num_movimientos = self.random.randint(max(1, delta // 2), delta)

        for _ in range(num_movimientos):
            dia = desde + timedelta(days=self.random.randint(0, delta))
            es_gasto = self.random.random() < 0.7
            tipo = TipoMovimiento.SALIDA if es_gasto else TipoMovimiento.INGRESO
            if es_gasto:
                valor = Decimal(str(round(self.random.uniform(1000, 500000), 2)))
                descripcion = self.random.choice(DESCRIPCIONES_GASTO)
            else:
                valor = Decimal(str(round(self.random.uniform(50000, 3000000), 2)))
                descripcion = self.random.choice(DESCRIPCIONES_INGRESO)

            movimiento = Movimiento(
                tipo=tipo,
                categoria_id=None,
                fecha=dia,
                valor=valor,
                descripcion=descripcion,
                fuente=FuenteMovimiento.BANCO_AUTOMATICO,
                cuenta_id=cuenta_id,
            )
            movimiento.hash_conciliacion = self._generar_hash(
                dia, valor, descripcion, cuenta_id
            )
            movimientos.append(movimiento)

        return movimientos
