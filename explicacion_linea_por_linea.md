# Guía del ETL M8: explicación paso a paso

Esta guía acompaña a [`main.py`](./main.py) y a los módulos de `src/`. Explica qué hace cada instrucción importante y cómo se conectan las piezas. La idea no es memorizar el código: es poder contar el recorrido de un registro desde el CSV hasta SQLite.

## 1. El recorrido completo

```text
main.py
  ├── extraer_ordenes() y extraer_catalogo()  → src/extract.py
  ├── transformar_ventas()                    → src/transform.py
  └── cargar_ventas()                         → src/load.py + sql/schema.sql
```

Usamos dos archivos de entrada:

- `data/ordenes.csv`: identifica el pedido, el usuario, el producto, la cantidad y la fecha.
- `data/catalogo_productos.csv`: relaciona el producto con su nombre y precio.

La transformación busca el precio del producto y calcula el total de la orden. El resultado se escribe en `data/ventas.db`, en una tabla llamada `ventas_analiticas`.

## 2. `main.py`: coordinar el proceso

### Imports

- `import sys`: permite escribir mensajes de error en la salida de errores (`stderr`).
- `from pathlib import Path`: ofrece una forma segura y legible de construir rutas de archivos.
- `from src.extract import ...`: importa las funciones que leen los CSV.
- `from src.load import cargar_ventas`: importa la función que escribe en SQLite.
- `from src.transform import transformar_ventas`: importa las reglas de limpieza y cálculo.

### Rutas del proyecto

- `CARPETA_PROYECTO = Path(__file__).resolve().parent`: obtiene la carpeta donde vive `main.py`, sin depender de la carpeta actual de la terminal.
- `CARPETA_DATOS = CARPETA_PROYECTO / "data"`: apunta a los CSV y a la base que se generará.
- `RUTA_DB = CARPETA_DATOS / "ventas.db"`: define la ubicación del archivo SQLite.
- `RUTA_SCHEMA = CARPETA_PROYECTO / "sql" / "schema.sql"`: señala el archivo con el DDL.

El operador `/` de `Path` combina fragmentos de ruta; no es una división matemática en este contexto.

### Función `main()`

- `def main() -> int:` declara la función principal. Devuelve un código numérico: `0` indica éxito y `1` indica error.
- `try:` comienza una sección en la que se capturan errores esperables del proceso.
- `extraer_ordenes(CARPETA_DATOS)` y `extraer_catalogo(CARPETA_DATOS)` leen las dos fuentes.
- `len(ordenes)` y `len(catalogo)` permiten mostrar cuántos registros se leyeron.
- `transformar_ventas(ordenes, catalogo)` valida los registros y calcula una fila analítica por pedido.
- `cargar_ventas(ventas, RUTA_DB, RUTA_SCHEMA)` prepara y ejecuta la carga de SQLite.
- `except (OSError, ValueError, RuntimeError) as error:` captura problemas de archivos, datos inválidos y errores de persistencia que nuestras funciones informan de forma controlada.
- `print(..., file=sys.stderr)` muestra el error en la salida destinada a diagnósticos.
- `return 1` indica que el programa no terminó correctamente.
- Los `print()` posteriores al `try` solo se ejecutan si la carga no falló; muestran conteo, importe y ubicación de la base.
- `if __name__ == "__main__":` evita que el ETL se ejecute accidentalmente si `main.py` se importa desde otro módulo.
- `raise SystemExit(main())` termina el programa usando el código devuelto por `main()`.

## 3. `src/extract.py`: leer y comprobar los CSV

### Imports y función común

- `import csv`: activa el lector CSV que forma parte de la biblioteca estándar de Python.
- `from pathlib import Path`: permite recibir y comprobar rutas.
- `def _leer_csv(ruta, columnas_requeridas):` define una función auxiliar. El guion bajo inicial indica que está pensada para usarse dentro de este módulo.
- `if not ruta.is_file():` comprueba que la ruta exista y sea un archivo.
- `raise FileNotFoundError(...)` detiene el flujo con una explicación si falta la fuente.
- `ruta.open(..., encoding="utf-8-sig", newline="")` abre el archivo. `utf-8-sig` tolera CSV con marca BOM; `newline=""` es la forma recomendada al usar `csv`.
- `csv.DictReader(archivo)` transforma cada fila en un diccionario cuyas claves vienen del encabezado.
- `if lector.fieldnames is None:` detecta un archivo sin encabezados.
- `lector.fieldnames = [...]` elimina espacios accidentales de los nombres de columnas.
- `faltantes = columnas_requeridas - encabezados` encuentra las columnas que el proceso necesita, pero no están en el archivo.
- `if faltantes:` y `raise ValueError(...)` explican qué encabezados faltan; es mejor detenerse aquí que producir una carga incompleta.
- `filas: list[dict[str, str]] = []` crea la lista donde se guardarán las filas leídas.
- `enumerate(lector, start=2)` cuenta las filas desde 2 porque la fila 1 corresponde al encabezado.
- `if None in fila:` detecta valores de más en una fila, situación que `DictReader` guarda bajo la clave `None`.
- `fila_limpia = {...}` quita espacios al inicio y al final de cada valor. Si una celda está vacía, conserva una cadena vacía para que la transformación pueda validarla.
- `if not filas:` impide continuar con una fuente que tiene encabezados, pero ningún registro.
- `return filas` entrega los registros al siguiente paso.

### Funciones específicas

- `extraer_ordenes(carpeta_datos)` define los encabezados mínimos de `ordenes.csv` y delega la lectura en `_leer_csv`.
- `extraer_catalogo(carpeta_datos)` hace lo mismo para `catalogo_productos.csv`.
- Reutilizar `_leer_csv` evita escribir dos veces la misma lógica de apertura, encabezados y limpieza de espacios.

## 4. `src/transform.py`: limpiar, validar y calcular

### Imports

- `import math`: se utiliza para comprobar que un precio sea un número finito, no `NaN` o infinito.
- `from datetime import datetime`: permite verificar que la fecha tenga el formato esperado.

### Catálogo de precios

- `precios_por_producto = {}` crea un diccionario. La clave es el ID del producto y el valor es su precio.
- El `for` recorre cada producto y `enumerate(..., start=2)` permite incluir el número aproximado de fila en los mensajes de error.
- `id_producto = ...strip()` obtiene la clave y limpia espacios.
- La validación de cadena vacía rechaza productos sin ID.
- `if id_producto in precios_por_producto:` detecta IDs de producto repetidos; el proceso no decide silenciosamente cuál precio conservar.
- `float(producto["precio_unitario"])` convierte el precio de texto a número decimal.
- `except ValueError` añade contexto si el texto no se puede convertir.
- `math.isfinite(precio)` rechaza valores no finitos; `precio < 0` rechaza precios negativos.
- `precios_por_producto[id_producto] = precio` guarda el precio para buscarlo rápidamente al procesar cada orden.

### Órdenes

- `ventas = []` crea la lista de salida que más tarde se insertará en SQLite.
- `pedidos_vistos = set()` crea un conjunto para detectar IDs repetidos en el CSV.
- El segundo `for` recorre todas las órdenes y limpia espacios de sus claves de texto.
- `all((...))` comprueba que los campos obligatorios no estén vacíos.
- `if order_id in pedidos_vistos:` evita que una orden repetida en la fuente pase inadvertida.
- `if id_producto not in precios_por_producto:` comprueba que el producto tenga un precio en el catálogo.
- `int(orden["cantidad"])` convierte la cantidad a entero.
- `datetime.strptime(..., "%Y-%m-%d")` valida que la fecha siga el patrón año-mes-día.
- `if cantidad <= 0:` descarta cantidades cero o negativas, que no representan una venta válida en este ejercicio.
- `precio_unitario = precios_por_producto[id_producto]` obtiene el precio correspondiente a la orden.
- `round(cantidad * precio_unitario, 2)` calcula el importe y lo redondea a dos decimales.
- `ventas.append((...))` agrega una tupla con los siete valores en el mismo orden que las columnas de la tabla.
- `pedidos_vistos.add(order_id)` registra el pedido como procesado.
- `return ventas` entrega el conjunto validado; hasta este punto todavía no se modificó la base de datos.

## 5. `sql/schema.sql`: definir la tabla (DDL)

- `CREATE TABLE IF NOT EXISTS ventas_analiticas` crea la tabla solo si aún no existe.
- `order_id TEXT PRIMARY KEY` guarda el ID del pedido y prohíbe más de una fila con el mismo ID.
- `user_id`, `id_producto` y `fecha` son `TEXT NOT NULL`: deben contener texto y no pueden quedar vacíos como `NULL`.
- `cantidad INTEGER NOT NULL CHECK (cantidad > 0)` guarda un entero y agrega una regla para rechazar cantidades inválidas.
- `precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0)` guarda el precio como número y prohíbe negativos.
- `total_venta REAL NOT NULL CHECK (total_venta >= 0)` guarda el importe calculado y también prohíbe negativos.

Este SQL es el **DDL** (*Data Definition Language*): instrucciones que describen la estructura de la base, no los registros que contiene.

## 6. `src/load.py`: cargar de forma repetible

### Preparar la carga

- `import sqlite3` importa el módulo estándar para conectarse a SQLite.
- `ruta_schema.is_file()` comprueba que el DDL exista antes de abrir la base.
- `ruta_schema.read_text(...)` lee el SQL como texto.
- `conexion = sqlite3.connect(ruta_db)` abre la base o crea el archivo si todavía no existe.
- `conexion.executescript(ddl)` ejecuta el DDL y crea la tabla si falta.

### Reemplazar la tabla dentro de una transacción

- `with conexion:` agrupa los cambios de datos en una transacción: al terminar correctamente se confirman; si ocurre un error, SQLite los revierte.
- `DELETE FROM ventas_analiticas` limpia la carga anterior porque este ejemplo publica una fotografía completa del CSV.
- `conexion.executemany(...)` inserta todas las tuplas en una operación por lote.
- Los signos `?` son parámetros; `sqlite3` coloca los valores de cada tupla sin concatenarlos dentro del SQL.
- Las consultas `SELECT COUNT(*)` y `SELECT COALESCE(SUM(...), 0)` verifican el número de filas y el importe cargado.
- El `except sqlite3.Error` convierte los errores de la base en un mensaje entendible para `main.py`.
- El bloque `finally` cierra la conexión tanto si la carga termina bien como si falla.

### Por qué no se duplican las filas

La carga usa dos protecciones:

1. `order_id` es clave primaria y SQLite rechaza un pedido repetido.
2. La limpieza y la inserción ocurren en una transacción; cada corrida vuelve a construir la tabla con el contenido de las fuentes.

Así, correr el mismo script dos veces no transforma 123 pedidos en 246. Si una fila falla durante la escritura, la transacción revierte la limpieza y mantiene la versión anterior.

## 7. Cómo explicarlo en una revisión

> “El programa lee dos CSV: órdenes y catálogo. Limpia espacios y valida encabezados, cantidades, fechas, productos y precios. Luego une cada orden con el precio de su producto y calcula el importe. Finalmente crea la tabla SQLite si falta y recarga los registros en una transacción. `order_id` es clave primaria y cada corrida reemplaza la fotografía anterior, por eso no acumula duplicados.”

## 8. Orden sugerido para estudiar el código

1. Lee `main.py` para ver el orden general.
2. Abre `src/extract.py` y sigue una fila desde el CSV.
3. Revisa `src/transform.py` con una orden de ejemplo y calcula su importe a mano.
4. Lee `sql/schema.sql` para entender dónde terminará esa fila.
5. Sigue `src/load.py` para ver cómo se crea y actualiza la tabla.
6. Ejecuta `main.py` dos veces y confirma que el conteo sigue en 123.
