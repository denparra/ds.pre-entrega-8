"""Persistencia de las ventas transformadas con SQLAlchemy ORM."""

from pathlib import Path

from sqlalchemy import URL, create_engine, delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Base, Venta


def cargar_ventas(
    ventas: list[tuple[str, str, str, str, int, float, float]],
    ruta_db: Path,
) -> tuple[int, float]:
    """Crea la tabla desde el modelo y reemplaza sus filas en una transacción."""
    if not ventas:
        raise ValueError("No hay ventas válidas; se conserva la base existente sin cambios.")

    # URL.create construye una URL SQLite segura a partir de la ruta del archivo.
    url_db = URL.create("sqlite", database=str(ruta_db.resolve()))
    engine = create_engine(url_db)

    try:
        # SQLAlchemy crea la tabla desde Venta si todavía no existe.
        Base.metadata.create_all(engine)

        # La Session agrupa operaciones ORM; begin confirma o revierte el lote completo.
        with Session(engine) as session:
            with session.begin():
                session.execute(delete(Venta))

                session.add_all(
                    [
                        Venta(
                            order_id=order_id,
                            user_id=user_id,
                            id_producto=id_producto,
                            fecha=fecha,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            total_venta=total_venta,
                        )
                        for (
                            order_id,
                            user_id,
                            id_producto,
                            fecha,
                            cantidad,
                            precio_unitario,
                            total_venta,
                        ) in ventas
                    ]
                )

                # Estas consultas sirven para comprobar la carga antes de cerrar la transacción.
                cantidad_cargada = session.scalar(
                    select(func.count()).select_from(Venta)
                ) or 0
                total_cargado = session.scalar(
                    select(func.coalesce(func.sum(Venta.total_venta), 0.0))
                ) or 0.0

        return int(cantidad_cargada), float(total_cargado)

    except SQLAlchemyError as error:
        raise RuntimeError(
            f"SQLAlchemy no pudo completar la carga en SQLite: {error}"
        ) from error
    finally:
        engine.dispose()
