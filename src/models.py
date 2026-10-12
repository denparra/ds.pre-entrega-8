"""Modelos ORM: cada clase representa una tabla de SQLite."""

from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Registro central de modelos y metadatos de SQLAlchemy."""


class Venta(Base):
    """Una fila por pedido procesado y persistido."""

    __tablename__ = "ventas_analiticas"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_venta_cantidad_positiva"),
        CheckConstraint("precio_unitario >= 0", name="ck_venta_precio_no_negativo"),
        CheckConstraint("total_venta >= 0", name="ck_venta_total_no_negativo"),
    )

    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), nullable=False)
    id_producto: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[str] = mapped_column(String(10), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    total_venta: Mapped[float] = mapped_column(Float, nullable=False)
