"""Extracción de las fuentes CSV incluidas en el proyecto."""

import csv
from pathlib import Path


def _leer_csv(ruta: Path, columnas_requeridas: set[str]) -> list[dict[str, str]]:
    """Lee un CSV y comprueba que tenga las columnas necesarias."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {ruta}")

    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)

        if lector.fieldnames is None:
            raise ValueError(f"El CSV está vacío o no tiene encabezados: {ruta.name}")

        # Quitar espacios de los encabezados evita fallos por diferencias de formato.
        lector.fieldnames = [nombre.strip() for nombre in lector.fieldnames]
        encabezados = set(lector.fieldnames)
        faltantes = columnas_requeridas - encabezados

        if faltantes:
            nombres = ", ".join(sorted(faltantes))
            raise ValueError(f"A {ruta.name} le faltan estas columnas: {nombres}")

        filas: list[dict[str, str]] = []
        for numero_fila, fila in enumerate(lector, start=2):
            # DictReader guarda en la clave None los valores que sobran en una fila.
            if None in fila:
                raise ValueError(
                    f"La fila {numero_fila} de {ruta.name} tiene más valores que columnas."
                )

            fila_limpia = {
                nombre: (valor or "").strip()
                for nombre, valor in fila.items()
                if nombre is not None
            }
            filas.append(fila_limpia)

    if not filas:
        raise ValueError(f"El archivo no contiene registros: {ruta.name}")

    return filas


def extraer_ordenes(carpeta_datos: Path) -> list[dict[str, str]]:
    """Lee las órdenes y comprueba su estructura mínima."""
    columnas = {"order_id", "user_id", "id_producto", "cantidad", "fecha"}
    return _leer_csv(carpeta_datos / "ordenes.csv", columnas)


def extraer_catalogo(carpeta_datos: Path) -> list[dict[str, str]]:
    """Lee el catálogo de productos y comprueba su estructura mínima."""
    columnas = {"id_producto", "nombre_producto", "precio_unitario"}
    return _leer_csv(carpeta_datos / "catalogo_productos.csv", columnas)
