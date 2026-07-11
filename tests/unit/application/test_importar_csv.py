from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from finanzas.application.use_cases.importar_csv import ImportarCSV
from finanzas.domain.entities.categoria import Categoria, TipoAsociado


class TestImportarCSV:
    def setup_method(self) -> None:
        self.repo_mov = MagicMock()
        self.repo_cat = MagicMock()
        self.use_case = ImportarCSV(self.repo_mov, self.repo_cat)
        self.categoria = Categoria(
            nombre="Comida", tipo_asociado=TipoAsociado.SALIDA
        )

    def test_importar_filas_validas(self) -> None:

        self.repo_cat.obtener_por_nombre.return_value = self.categoria
        self.repo_mov.buscar_por_hash.return_value = None
        self.repo_mov.guardar.return_value = MagicMock()

        filas = [
            {
                "tipo": "SALIDA",
                "categoria": "Comida",
                "fecha": date(2025, 1, 15),
                "valor": Decimal("25000"),
                "descripcion": "Almuerzo",
            }
        ]
        resultado = self.use_case.ejecutar(filas)
        assert resultado.importados == 1
        assert resultado.duplicados == 0
        assert resultado.errores == 0

    def test_importar_duplicado(self) -> None:

        from finanzas.domain.entities.categoria import Categoria, TipoAsociado

        cat = Categoria(nombre="Comida", tipo_asociado=TipoAsociado.SALIDA)
        self.repo_cat.obtener_por_nombre.return_value = cat
        self.repo_mov.buscar_por_hash.return_value = MagicMock()

        filas = [
            {
                "tipo": "SALIDA",
                "categoria": "Comida",
                "fecha": date(2025, 1, 15),
                "valor": Decimal("25000"),
                "descripcion": "Almuerzo",
            }
        ]
        resultado = self.use_case.ejecutar(filas)
        assert resultado.importados == 0
        assert resultado.duplicados == 1
        assert resultado.errores == 0

    def test_categoria_no_encontrada(self) -> None:

        self.repo_cat.obtener_por_nombre.return_value = None
        filas = [
            {
                "tipo": "SALIDA",
                "categoria": "Inexistente",
                "fecha": date(2025, 1, 15),
                "valor": Decimal("25000"),
            }
        ]
        resultado = self.use_case.ejecutar(filas)
        assert resultado.importados == 0
        assert resultado.errores == 1
