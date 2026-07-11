from decimal import Decimal

import pytest

from finanzas.domain.value_objects.dinero import Dinero, Moneda


class TestDinero:
    def test_crear_dinero_valido(self) -> None:
        dinero = Dinero(cantidad=Decimal("100.50"))
        assert dinero.cantidad == Decimal("100.50")
        assert dinero.moneda == Moneda.COP

    def test_crear_dinero_con_moneda_explicita(self) -> None:
        dinero = Dinero(cantidad=Decimal("50"), moneda=Moneda.USD)
        assert dinero.moneda == Moneda.USD

    def test_crear_dinero_negativo(self) -> None:
        dinero = Dinero(cantidad=Decimal("-10"))
        assert dinero.cantidad == Decimal("-10")

    def test_sumar_dos_dineros_misma_moneda(self) -> None:
        a = Dinero(cantidad=Decimal("100"))
        b = Dinero(cantidad=Decimal("50"))
        resultado = a + b
        assert resultado.cantidad == Decimal("150")

    def test_sumar_diferentes_monedas_lanza_error(self) -> None:
        a = Dinero(cantidad=Decimal("100"), moneda=Moneda.COP)
        b = Dinero(cantidad=Decimal("50"), moneda=Moneda.USD)
        with pytest.raises(ValueError, match="different currencies"):
            _ = a + b

    def test_restar_dinero(self) -> None:
        a = Dinero(cantidad=Decimal("200"))
        b = Dinero(cantidad=Decimal("50"))
        resultado = a - b
        assert resultado.cantidad == Decimal("150")

    def test_comparar_dinero(self) -> None:
        a = Dinero(cantidad=Decimal("100"))
        b = Dinero(cantidad=Decimal("200"))
        assert a < b
        assert b > a

    def test_dinero_igualdad(self) -> None:
        a = Dinero(cantidad=Decimal("100"))
        b = Dinero(cantidad=Decimal("100"))
        assert a == b

    def test_repr(self) -> None:
        dinero = Dinero(cantidad=Decimal("100.50"))
        assert repr(dinero) == "100.50 COP"
