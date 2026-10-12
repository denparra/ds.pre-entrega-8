# Pre-entrega M8 — Persistencia de ventas con SQLite

> **Curso:** Data Science II  
> **Módulo:** 8 — Persistencia y automatización de datos  
> **Consigna:** [`consigna-pre-entrega-md8.md`](./consigna-pre-entrega-md8.md)  
> **Guía detallada del código:** [`explicacion_linea_por_linea.md`](./explicacion_linea_por_linea.md)

Este proyecto toma órdenes y un catálogo de productos en CSV, valida y transforma los registros, calcula el importe de cada pedido y guarda el resultado en una base local SQLite. La carga se puede repetir: cada ejecución reemplaza la tabla analítica en una transacción, por lo que no acumula filas duplicadas.

## Requisitos

- Python **3.10 o superior**.
- No requiere instalar paquetes adicionales: utiliza `csv`, `sqlite3` y otros módulos incluidos con Python.
- Windows: se puede usar el comando `py`. En otros sistemas, usar `python3` si `python` no está disponible.

## Estructura del proyecto

```text
pre-entregamd8/
├── data/
│   ├── catalogo_productos.csv  # productos y precios de referencia
│   ├── ordenes.csv             # órdenes de venta de entrada
│   └── ventas.db               # SQLite generado al ejecutar (no se versiona)
├── sql/
│   └── schema.sql              # DDL de la tabla de destino
├── src/
│   ├── __init__.py
│   ├── extract.py              # lectura y validación estructural de CSV
│   ├── transform.py            # limpieza, validación y cálculo de ventas
│   └── load.py                 # creación del esquema y carga transaccional
├── consigna-pre-entrega-md8.md
├── explicacion_linea_por_linea.md
├── main.py                     # coordina las tres etapas ETL
├── README.md
└── .gitignore
```

Los CSV son datos de ejemplo reutilizados de la entrega M7 y están incluidos aquí para que este proyecto pueda ejecutarse sin depender de archivos externos.

## Qué hace el ETL

| Etapa | Archivo | Acción |
|---|---|---|
| **Extract — Extraer** | `src/extract.py` | Lee `ordenes.csv` y `catalogo_productos.csv`; comprueba que existan los encabezados necesarios y limpia espacios. |
| **Transform — Transformar** | `src/transform.py` | Valida claves, cantidad, fecha y precios; relaciona cada orden con el catálogo; calcula `total_venta = cantidad × precio_unitario`. |
| **Load — Cargar** | `src/load.py` + `sql/schema.sql` | Crea `ventas_analiticas` si aún no existe y carga las ventas transformadas en `data/ventas.db`. |

La tabla de destino guarda una fila por pedido con su usuario, producto, fecha, cantidad, precio unitario e importe total.

## Pasos para ejecutar

### Opción A: desde la carpeta de la entrega

```powershell
cd "Data Science II/Modulo 8/pre-entregamd8"
py main.py
```

Si el comando `py` no está disponible, prueba:

```powershell
python main.py
```

### Opción B: desde la raíz `CODERHOUSE`

```powershell
py "Data Science II/Modulo 8/pre-entregamd8/main.py"
```

El script encuentra los CSV y el DDL a partir de su propia ubicación; por eso funciona desde cualquiera de las dos carpetas.

## Resultado esperado

La primera ejecución crea `data/ventas.db` y muestra un resumen parecido a este:

```text
[1/3] Extrayendo órdenes y catálogo...
      Órdenes leídas: 123 | Productos: 15
[2/3] Validando y calculando el total de cada pedido...
      Pedidos listos para cargar: 123
[3/3] Guardando el resultado en SQLite...
ETL finalizado correctamente.
Registros en ventas_analiticas: 123
Importe total procesado: $100,141.82
Base de datos creada/actualizada: ...\data\ventas.db
```

La ruta y el formato del importe dependen del sistema operativo. La base `.db` es un archivo generado: `.gitignore` evita subirlo porque el script lo reconstruye desde los CSV.

Para inspeccionar la tabla después de ejecutar:

```powershell
py -c "import sqlite3; c=sqlite3.connect('Data Science II/Modulo 8/pre-entregamd8/data/ventas.db'); print(c.execute('SELECT order_id, user_id, total_venta FROM ventas_analiticas LIMIT 5').fetchall()); c.close()"
```

## Cómo se evita duplicar los datos

Se aplican dos controles complementarios:

1. `order_id` es clave primaria (`PRIMARY KEY`) en `sql/schema.sql`, así la base no acepta dos filas con el mismo pedido.
2. Antes de insertar, el script borra el contenido anterior de `ventas_analiticas` y vuelve a cargar el conjunto completo **dentro de una transacción**. Si falla una inserción, SQLite revierte la limpieza y la carga; no queda una tabla a medio actualizar.

Por eso, al ejecutar `py main.py` dos veces con los mismos CSV, la tabla sigue teniendo 123 filas en vez de 246. `CREATE TABLE IF NOT EXISTS` conserva la tabla y su estructura, pero por sí solo no evita duplicados en las filas; la recarga controlada y la clave primaria cubren ese caso.

## Esquema de persistencia

El archivo [`sql/schema.sql`](./sql/schema.sql) define la tabla de destino (**DDL**). Además de la clave primaria, incluye restricciones `NOT NULL` y `CHECK` para impedir cantidades no positivas e importes negativos.

## Errores y validaciones

- Si falta un CSV, una columna obligatoria o el archivo SQL, el programa informa el problema y termina con código de error.
- Si una orden tiene campos vacíos, una fecha o cantidad inválida, un producto inexistente o un `order_id` repetido, la transformación se detiene antes de borrar o escribir la tabla.
- Si SQLite rechaza la carga, el programa informa el error y la transacción revierte los cambios.

## Checklist de la consigna

- [x] Script funcional que ejecuta extracción, transformación y carga.
- [x] README con **Requisitos** y **Pasos para ejecutar**.
- [x] DDL en `sql/schema.sql`.
- [x] Lógica para evitar duplicados al repetir la carga.
- [x] `.gitignore` para la base generada, el entorno y los archivos temporales.
- [ ] Crear/publicar el repositorio público en GitHub y registrar commits incrementales descriptivos.

> El último punto requiere publicar este proyecto en GitHub y completar el historial de commits del repositorio.
