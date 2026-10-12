"""Persistencia de las ventas transformadas en SQLite."""

import sqlite3
from pathlib import Path


def cargar_ventas(
    ventas: list[tuple[str, str, str, str, int, float, float]],
    ruta_db: Path,
    ruta_schema: Path,
) -> tuple[int, float]:
    """Crea el esquema y reemplaza la tabla analítica en una transacción."""
    if not ruta_schema.is_file():
        raise FileNotFoundError(f"No se encontró el esquema SQL: {ruta_schema}")

    ddl = ruta_schema.read_text(encoding="utf-8")
    conexion: sqlite3.Connection | None = None

    try:
        conexion = sqlite3.connect(ruta_db)

        # Crear la tabla si aún no existe. El archivo SQL contiene el DDL.
        conexion.executescript(ddl)

        # La limpieza y la recarga son atómicas: ante un error, SQLite revierte ambas.
        with conexion:
            conexion.execute("DELETE FROM ventas_analiticas")
            conexion.executemany(
                """
                INSERT INTO ventas_analiticas (
                    order_id,
                    user_id,
                    id_producto,
                    fecha,
                    cantidad,
                    precio_unitario,
                    total_venta
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ventas,
            )

            cantidad_cargada = conexion.execute(
                "SELECT COUNT(*) FROM ventas_analiticas"
            ).fetchone()[0]
            total_cargado = conexion.execute(
                "SELECT COALESCE(SUM(total_venta), 0) FROM ventas_analiticas"
            ).fetchone()[0]

        return cantidad_cargada, float(total_cargado)

    except sqlite3.Error as error:
        raise RuntimeError(f"No se pudo completar la carga en SQLite: {error}") from error
    finally:
        if conexion is not None:
            conexion.close()
