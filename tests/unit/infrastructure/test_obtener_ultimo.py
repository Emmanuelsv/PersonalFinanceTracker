import time
from datetime import date
from decimal import Decimal
from uuid import uuid4

from finanzas.domain.entities.categoria import Categoria, TipoAsociado
from finanzas.domain.entities.cuenta_bancaria import CuentaBancaria  # noqa: F401
from finanzas.domain.entities.movimiento import (
    FuenteMovimiento,
    Movimiento,
    TipoMovimiento,
)
from finanzas.infrastructure.repositories.repositorio_movimientos_sqlmodel import (
    RepositorioMovimientosSQLModel,
)


class TestObtenerUltimo:
    def test_obtener_ultimo_devuelve_el_creado_mas_reciente(
        self, session
    ) -> None:
        cat = Categoria(
            nombre="Comida", tipo_asociado=TipoAsociado.SALIDA
        )
        session.add(cat)
        session.commit()
        session.refresh(cat)

        repo = RepositorioMovimientosSQLModel(session)
        primero = repo.guardar(
            Movimiento(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=cat.id,
                fecha=date(2025, 1, 15),
                valor=Decimal("10000"),
                fuente=FuenteMovimiento.MANUAL,
            )
        )
        time.sleep(0.01)
        ultimo = repo.guardar(
            Movimiento(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=cat.id,
                fecha=date(2025, 1, 20),
                valor=Decimal("25000"),
                fuente=FuenteMovimiento.MANUAL,
            )
        )

        resultado = repo.obtener_ultimo()

        assert resultado is not None
        assert resultado.id == ultimo.id
        assert resultado.id != primero.id

    def test_obtener_ultimo_devuelve_none_cuando_vacio(self, session) -> None:
        repo = RepositorioMovimientosSQLModel(session)

        assert repo.obtener_ultimo() is None

    def test_obtener_ultimo_ignora_id_distinto_al_creado_en(
        self, session
    ) -> None:
        cat = Categoria(
            nombre="Ropa", tipo_asociado=TipoAsociado.SALIDA
        )
        session.add(cat)
        session.commit()
        session.refresh(cat)

        repo = RepositorioMovimientosSQLModel(session)
        repo.session.add(
            Movimiento(
                id=uuid4(),
                tipo=TipoMovimiento.SALIDA,
                categoria_id=cat.id,
                fecha=date(2025, 1, 1),
                valor=Decimal("5000"),
                fuente=FuenteMovimiento.MANUAL,
                creado_en=None,
            )
        )
        repo.session.commit()
        reciente = repo.guardar(
            Movimiento(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=cat.id,
                fecha=date(2025, 1, 2),
                valor=Decimal("9000"),
                fuente=FuenteMovimiento.MANUAL,
            )
        )

        resultado = repo.obtener_ultimo()

        assert resultado is not None
        assert resultado.id == reciente.id
