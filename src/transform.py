"""Limpieza, validación y cálculo de ventas por pedido."""

import math
from datetime import datetime


def transformar_ventas(
    ordenes: list[dict[str, str]],
    catalogo: list[dict[str, str]],
) -> list[tuple[str, str, str, str, int, float, float]]:
    """Une órdenes con precios y calcula el total de cada pedido.

    Cada tupla de salida sigue este orden:
    order_id, user_id, id_producto, fecha, cantidad, precio_unitario, total_venta.
    """
    precios_por_producto: dict[str, float] = {}

    # Convertir el catálogo a un diccionario permite buscar cada precio por producto.
    for numero_fila, producto in enumerate(catalogo, start=2):
        id_producto = producto["id_producto"].strip()
        if not id_producto:
            raise ValueError(f"El catálogo tiene un id_producto vacío en la fila {numero_fila}.")
        if id_producto in precios_por_producto:
            raise ValueError(f"El producto {id_producto} aparece más de una vez en el catálogo.")

        try:
            precio = float(producto["precio_unitario"])
        except ValueError as error:
            raise ValueError(
                f"El precio del producto {id_producto} no es un número válido."
            ) from error

        if not math.isfinite(precio) or precio < 0:
            raise ValueError(f"El precio del producto {id_producto} debe ser un número no negativo.")

        precios_por_producto[id_producto] = precio

    ventas: list[tuple[str, str, str, str, int, float, float]] = []
    pedidos_vistos: set[str] = set()

    # Validar cada orden antes de iniciar la escritura en la base de datos.
    for numero_fila, orden in enumerate(ordenes, start=2):
        order_id = orden["order_id"].strip()
        user_id = orden["user_id"].strip()
        id_producto = orden["id_producto"].strip()

        if not all((order_id, user_id, id_producto, orden["cantidad"], orden["fecha"])):
            raise ValueError(f"La orden de la fila {numero_fila} tiene campos obligatorios vacíos.")
        if order_id in pedidos_vistos:
            raise ValueError(f"El pedido {order_id} está duplicado en el CSV de órdenes.")
        if id_producto not in precios_por_producto:
            raise ValueError(
                f"El producto {id_producto} de la orden {order_id} no existe en el catálogo."
            )

        try:
            cantidad = int(orden["cantidad"])
            fecha = datetime.strptime(orden["fecha"], "%Y-%m-%d").date().isoformat()
        except ValueError as error:
            raise ValueError(
                f"La cantidad o la fecha de la orden {order_id} no tiene un formato válido."
            ) from error

        if cantidad <= 0:
            raise ValueError(f"La cantidad de la orden {order_id} debe ser mayor que cero.")

        precio_unitario = precios_por_producto[id_producto]
        total_venta = round(cantidad * precio_unitario, 2)
        ventas.append(
            (
                order_id,
                user_id,
                id_producto,
                fecha,
                cantidad,
                precio_unitario,
                total_venta,
            )
        )
        pedidos_vistos.add(order_id)

    return ventas
