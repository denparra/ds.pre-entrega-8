"""Punto de entrada: coordina extracción, transformación y carga del ETL."""

import sys
from pathlib import Path

from src.extract import extraer_catalogo, extraer_ordenes
from src.load import cargar_ventas
from src.transform import transformar_ventas

# Resolver las rutas desde la carpeta de este archivo permite ejecutarlo desde otro directorio.
CARPETA_PROYECTO = Path(__file__).resolve().parent
CARPETA_DATOS = CARPETA_PROYECTO / "data"
RUTA_DB = CARPETA_DATOS / "ventas.db"


def main() -> int:
    """Ejecuta las tres etapas e informa el resultado de la carga."""
    try:
        print("[1/3] Extrayendo órdenes y catálogo...")
        ordenes = extraer_ordenes(CARPETA_DATOS)
        catalogo = extraer_catalogo(CARPETA_DATOS)
        print(f"      Órdenes leídas: {len(ordenes)} | Productos: {len(catalogo)}")

        print("[2/3] Validando y calculando el total de cada pedido...")
        ventas = transformar_ventas(ordenes, catalogo)
        print(f"      Pedidos listos para cargar: {len(ventas)}")

        print("[3/3] Guardando el resultado en SQLite...")
        cantidad, total = cargar_ventas(ventas, RUTA_DB)

    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("ETL finalizado correctamente.")
    print(f"Registros en ventas_analiticas: {cantidad}")
    print(f"Importe total procesado: ${total:,.2f}")
    print(f"Base de datos creada/actualizada: {RUTA_DB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
