"""Pruebas de extracción, transformación y carga sin tocar la base real."""

import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import main as etl_main
from src.extract import extraer_ordenes
from src.load import cargar_ventas
from src.transform import transformar_ventas


class ExtractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_dir = Path(self.temp_dir.name)

    def test_reads_csv_and_strips_header_and_value_whitespace(self) -> None:
        (self.data_dir / "ordenes.csv").write_text(
            "order_id ,user_id,id_producto,cantidad,fecha\n"
            " ord-1 , user-1 , prod-1 , 2 , 2025-01-02 \n",
            encoding="utf-8",
        )

        self.assertEqual(
            extraer_ordenes(self.data_dir),
            [
                {
                    "order_id": "ord-1",
                    "user_id": "user-1",
                    "id_producto": "prod-1",
                    "cantidad": "2",
                    "fecha": "2025-01-02",
                }
            ],
        )

    def test_rejects_csv_missing_required_column(self) -> None:
        (self.data_dir / "ordenes.csv").write_text(
            "order_id,user_id,id_producto,cantidad\nord-1,user-1,prod-1,2\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "fecha"):
            extraer_ordenes(self.data_dir)


class TransformTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalogo = [
            {
                "id_producto": "prod-1",
                "nombre_producto": "Producto de prueba",
                "precio_unitario": "12.50",
            }
        ]

    def test_joins_catalog_and_calculates_order_total(self) -> None:
        ordenes = [
            {
                "order_id": "ord-1",
                "user_id": "user-1",
                "id_producto": "prod-1",
                "cantidad": "2",
                "fecha": "2025-01-02",
            }
        ]

        self.assertEqual(
            transformar_ventas(ordenes, self.catalogo),
            [("ord-1", "user-1", "prod-1", "2025-01-02", 2, 12.5, 25.0)],
        )

    def test_rejects_order_for_product_missing_from_catalog(self) -> None:
        ordenes = [
            {
                "order_id": "ord-1",
                "user_id": "user-1",
                "id_producto": "unknown",
                "cantidad": "1",
                "fecha": "2025-01-02",
            }
        ]

        with self.assertRaisesRegex(ValueError, "no existe en el catálogo"):
            transformar_ventas(ordenes, self.catalogo)


class LoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "ventas_prueba.db"
        self.ventas = [
            ("ord-1", "user-1", "prod-1", "2025-01-02", 2, 12.5, 25.0)
        ]

    def test_repeated_load_replaces_rows_without_duplicating_them(self) -> None:
        self.assertEqual(cargar_ventas(self.ventas, self.db_path), (1, 25.0))
        self.assertEqual(cargar_ventas(self.ventas, self.db_path), (1, 25.0))

        with closing(sqlite3.connect(self.db_path)) as connection:
            count, total = connection.execute(
                "SELECT COUNT(*), SUM(total_venta) FROM ventas_analiticas"
            ).fetchone()

        self.assertEqual(count, 1)
        self.assertEqual(total, 25.0)

    def test_failed_load_rolls_back_and_preserves_previous_rows(self) -> None:
        cargar_ventas(self.ventas, self.db_path)
        duplicate_order = self.ventas[0]

        with self.assertRaisesRegex(RuntimeError, "no pudo completar la carga"):
            cargar_ventas([duplicate_order, duplicate_order], self.db_path)

        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT order_id, total_venta FROM ventas_analiticas"
            ).fetchall()

        self.assertEqual(rows, [("ord-1", 25.0)])


class PipelineTests(unittest.TestCase):
    def test_main_runs_csv_to_sqlite_using_temporary_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory) / "data"
            data_dir.mkdir()
            db_path = data_dir / "ventas_prueba.db"
            (data_dir / "ordenes.csv").write_text(
                "order_id,user_id,id_producto,cantidad,fecha\n"
                "ord-1,user-1,prod-1,2,2025-01-02\n",
                encoding="utf-8",
            )
            (data_dir / "catalogo_productos.csv").write_text(
                "id_producto,nombre_producto,precio_unitario\n"
                "prod-1,Producto de prueba,12.50\n",
                encoding="utf-8",
            )
            output = StringIO()

            with (
                patch.object(etl_main, "CARPETA_DATOS", data_dir),
                patch.object(etl_main, "RUTA_DB", db_path),
                redirect_stdout(output),
            ):
                result = etl_main.main()

            self.assertEqual(result, 0)
            self.assertIn("ETL finalizado correctamente.", output.getvalue())
            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(
                    "SELECT order_id, total_venta FROM ventas_analiticas"
                ).fetchall()

            self.assertEqual(rows, [("ord-1", 25.0)])


if __name__ == "__main__":
    unittest.main()
