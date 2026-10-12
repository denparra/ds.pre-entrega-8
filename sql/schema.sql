-- Tabla analítica: una fila por pedido procesado.
CREATE TABLE IF NOT EXISTS ventas_analiticas (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    id_producto TEXT NOT NULL,
    fecha TEXT NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0),
    total_venta REAL NOT NULL CHECK (total_venta >= 0)
);
