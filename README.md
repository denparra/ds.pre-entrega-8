# Pre-entrega M8 — Persistencia de ventas con SQLAlchemy y SQLite

> **Curso:** Data Science II  
> **Módulo:** 8 — Persistencia y automatización de datos  
> **Consigna:** [`consigna-pre-entrega-md8.md`](./consigna-pre-entrega-md8.md)  

Este proyecto toma órdenes y un catálogo de productos en CSV, valida y transforma los registros, calcula el importe de cada pedido y guarda el resultado en una base local SQLite mediante **SQLAlchemy 2.x ORM**. La carga se puede repetir: cada ejecución reemplaza la tabla analítica en una transacción, por lo que no acumula filas duplicadas.

## Requisitos

- Python **3.10 o superior**.
- SQLAlchemy **2.x**, instalado desde `requirements.txt`.
- SQLite está incluido con Python; no requiere instalar ni levantar un servidor de base de datos.
- Windows: se puede usar el comando `py`. En otros sistemas, usar `python3` si `python` no está disponible.

## Instalación

Desde la raíz `CODERHOUSE`, entra en la carpeta `pre-entregamd8`, crea un entorno virtual e instala la única dependencia externa:

```powershell
cd "Data Science II/Modulo 8/pre-entregamd8"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En macOS o Linux, desde la raíz del proyecto:

```bash
cd "Data Science II/Modulo 8/pre-entregamd8"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Estructura del proyecto

```text
pre-entregamd8/
├── data/
│   ├── catalogo_productos.csv  # productos y precios de referencia
│   ├── ordenes.csv             # órdenes de venta de entrada
│   └── ventas.db               # SQLite generado al ejecutar (no se versiona)
├── src/
│   ├── __init__.py
│   ├── extract.py              # lectura y validación estructural de CSV
│   ├── transform.py            # limpieza, validación y cálculo de ventas
│   ├── models.py               # Base declarativa y modelo ORM Venta
│   └── load.py                 # Engine, Session y carga transaccional
├── consigna-pre-entrega-md8.md
├── main.py                     # coordina las tres etapas ETL
├── requirements.txt            # SQLAlchemy 2.x
├── README.md
└── .gitignore
```

Los CSV son datos de ejemplo reutilizados de la entrega M7 y están incluidos aquí para que este proyecto pueda ejecutarse sin depender de archivos externos.

## Qué hace el ETL

| Etapa | Archivo | Acción |
|---|---|---|
| **Extract — Extraer** | `src/extract.py` | Lee `ordenes.csv` y `catalogo_productos.csv`; comprueba que existan los encabezados necesarios y limpia espacios. |
| **Transform — Transformar** | `src/transform.py` | Valida claves, cantidad, fecha y precios; relaciona cada orden con el catálogo; calcula `total_venta = cantidad × precio_unitario`. |
| **Load — Cargar** | `src/models.py` + `src/load.py` | El ORM define y crea `ventas_analiticas`; `Session` carga las ventas transformadas en `data/ventas.db`. |

La tabla de destino guarda una fila por pedido con su usuario, producto, fecha, cantidad, precio unitario e importe total.

### SQLite y SQLAlchemy cumplen funciones distintas

- **SQLite** es la base de datos: el archivo local `data/ventas.db` almacena las filas.
- **SQLAlchemy** es la biblioteca de Python que conecta con SQLite y permite mapear objetos de Python a tablas.
- `Engine` administra la comunicación con la base; `Venta` describe el modelo; `Session` agrupa operaciones dentro de una transacción.

## Pasos para ejecutar

### Opción A: desde la raíz `CODERHOUSE` con el entorno propio de la entrega

```powershell
cd "Data Science II/Modulo 8/pre-entregamd8"
.\.venv\Scripts\python.exe main.py
```

El ejemplo usa el entorno `.venv` propio de esta entrega, creado en los pasos de **Instalación**. Si no quieres activar el entorno, llama directamente a su ejecutable:

```powershell
.\.venv\Scripts\python.exe main.py
```

### Opción B: desde la raíz `CODERHOUSE`

```powershell
.\.venv\Scripts\python.exe -m pip install -r "Data Science II/Modulo 8/pre-entregamd8/requirements.txt"
.\.venv\Scripts\python.exe "Data Science II/Modulo 8/pre-entregamd8/main.py"
```

El script encuentra los CSV y el archivo SQLite a partir de su propia ubicación; por eso funciona desde cualquiera de las dos carpetas.

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

Para inspeccionar algunas filas después de ejecutar, usando SQLAlchemy:

```powershell
.\.venv\Scripts\python.exe -c "from sqlalchemy import create_engine, text; e=create_engine('sqlite:///Data Science II/Modulo 8/pre-entregamd8/data/ventas.db'); c=e.connect(); print(c.execute(text('SELECT order_id, user_id, total_venta FROM ventas_analiticas LIMIT 5')).fetchall()); c.close(); e.dispose()"
```

## Cómo se evita duplicar los datos

Se aplican dos controles complementarios:

1. `order_id` es clave primaria (`primary_key=True`) en el modelo `Venta` de `src/models.py`, así la base no acepta dos filas con el mismo pedido.
2. Antes de insertar, el script borra el contenido anterior de `ventas_analiticas` y vuelve a cargar el conjunto completo dentro de `Session.begin()`. Si falla una inserción, SQLAlchemy revierte la limpieza y la carga; no queda una tabla a medio actualizar.

Por eso, al ejecutar `main.py` dos veces con los mismos CSV, la tabla sigue teniendo 123 filas en vez de 246. `Base.metadata.create_all(engine)` crea la tabla cuando hace falta, pero no evita duplicados por sí solo; la recarga controlada y la clave primaria cubren ese caso.

## Esquema de persistencia

La clase `Venta` de [`src/models.py`](./src/models.py) define las columnas y restricciones de la tabla. `Base.metadata.create_all(engine)` genera y ejecuta el DDL a partir de ese modelo. Incluye una clave primaria, campos obligatorios y restricciones `CHECK` para impedir cantidades no positivas e importes negativos; esta definición en código cumple el requisito de creación de tabla de la consigna.

## Errores y validaciones

- Si falta un CSV, una columna obligatoria o la dependencia SQLAlchemy, el programa no puede completar el proceso; el README indica cómo instalarla.
- Si una orden tiene campos vacíos, una fecha o cantidad inválida, un producto inexistente o un `order_id` repetido, la transformación se detiene antes de borrar o escribir la tabla.
- Si SQLAlchemy/SQLite rechaza la carga, el programa informa el error y la transacción revierte los cambios.

## Checklist de la consigna

- [x] Script funcional que ejecuta extracción, transformación y carga.
- [x] README con **Requisitos** y **Pasos para ejecutar**.
- [x] Modelo ORM y `Base.metadata.create_all(engine)` definen y crean la tabla de destino.
- [x] Lógica para evitar duplicados al repetir la carga.
- [x] `.gitignore` para la base generada, el entorno y los archivos temporales.
- [x] Historial local con commits incrementales y descriptivos.
- [ ] Publicar el repositorio en GitHub como repositorio público.

> La entrega ya tiene historial local. Solo falta vincularla a un repositorio público de GitHub para completar el último requisito.
