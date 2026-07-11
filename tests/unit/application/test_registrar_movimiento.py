from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from finanzas.application.use_cases.registrar_movimiento import (
    RegistrarMovimiento,
)
from finanzas.domain.entities.categoria import Categoria, TipoAsociado
from finanzas.domain.entities.movimiento import (
    TipoMovimiento,
)
from finanzas.domain.exceptions import (
    CategoriaInexistenteError,
    MovimientoInvalidoError,
)


class TestRegistrarMovimiento:
    def setup_method(self) -> None:
        self.repo_mov = MagicMock()
        self.repo_cat = MagicMock()
        self.use_case = RegistrarMovimiento(self.repo_mov, self.repo_cat)
        self.categoria = Categoria(
            nombre="Comida", tipo_asociado=TipoAsociado.SALIDA
        )

    def test_registrar_movimiento_valido(self) -> None:
        self.repo_cat.obtener_por_id.return_value = self.categoria
        self.repo_mov.guardar.return_value = self.categoria

        resultado = self.use_case.ejecutar(
            tipo=TipoMovimiento.SALIDA,
            categoria_id=self.categoria.id,
            fecha=date(2025, 1, 15),
            valor=Decimal("25000"),
            descripcion="Almuerzo",
        )
        assert resultado is not None
        self.repo_mov.guardar.assert_called_once()

    def test_categoria_inexistente(self) -> None:


        self.repo_cat.obtener_por_id.return_value = None
        with pytest.raises(CategoriaInexistenteError):
            self.use_case.ejecutar(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=uuid4(),
                fecha=date(2025, 1, 15),
                valor=Decimal("25000"),
            )

    def test_valor_cero_lanza_error(self) -> None:


        self.repo_cat.obtener_por_id.return_value = self.categoria
        with pytest.raises(MovimientoInvalidoError):
            self.use_case.ejecutar(
                tipo=TipoMovimiento.SALIDA,
                categoria_id=uuid4(),
                fecha=date(2025, 1, 15),
                valor=Decimal("0"),
            )
