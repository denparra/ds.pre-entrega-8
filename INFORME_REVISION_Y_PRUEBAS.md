# Revisión enfocada y reporte de pruebas — Pre-entrega M8

**Repositorio:** <https://github.com/denparra/ds.pre-entrega-8>

**Alcance:** revisión de los tres criterios indicados en la devolución y ejecución de la suite automatizada local.

## 1. Funcionalidad del flujo ETL — Cumple

- `main.py` coordina extracción, transformación y carga.
- `src/extract.py` conecta con las fuentes locales `data/ordenes.csv` y `data/catalogo_productos.csv`, y comprueba encabezados y estructura básica.
- `src/transform.py` limpia espacios, valida datos, relaciona cada orden con el catálogo y calcula `total_venta`.
- `src/load.py` persiste el resultado en `data/ventas.db`, una base SQLite local.
- La prueba `PipelineTests.test_main_runs_csv_to_sqlite_using_temporary_paths` ejecuta el flujo completo con CSV de prueba y confirma el registro cargado.

## 2. Diseño de persistencia y esquema — Cumple

- `src/models.py` declara la tabla `ventas_analiticas` mediante el ORM de SQLAlchemy; `Base.metadata.create_all(engine)` crea la tabla si no existe.
- El modelo almacena una fila por pedido, con identificadores, fecha, cantidad, precio unitario y total. `order_id` es clave primaria; los campos son obligatorios y hay restricciones para cantidades y valores no negativos.
- `src/load.py` ejecuta el reemplazo dentro de una transacción. La clave primaria y las validaciones complementan la carga repetible.
- Las pruebas de carga comprueban que una segunda ejecución no duplique filas y que una carga inválida revierta la transacción y conserve los datos previos.

## 3. Automatización, errores y repetibilidad — Cumple

- El flujo se inicia con `main.py` y resuelve las rutas a partir de la ubicación del proyecto.
- Los CSV faltantes o mal formados y los datos inválidos producen errores informativos. Los errores de SQLAlchemy se convierten en errores controlados; la transacción evita dejar una carga parcial.
- Las pruebas cubren columnas faltantes, referencias a productos inexistentes, carga repetida, rollback y ejecución integrada.

## Resultado de ejecución

- **Fecha:** 2026-10-20
- **Entorno:** Windows, Python 3.13.1, SQLAlchemy 2.0.52.
- **Comando:** `py -m unittest discover -s tests -v`
- **Resultado:** `Ran 7 tests ... OK` (7 pruebas aprobadas, 0 fallidas).
- **Aislamiento:** las pruebas crean una base SQLite en una carpeta temporal; no escriben en `data/ventas.db`.

La prueba integrada usa CSV pequeños preparados para el test; no se ejecutó aquí `main.py` contra los CSV reales de la entrega. Para reproducir la verificación, instala `requirements.txt` y ejecuta el comando anterior desde la raíz del proyecto.

## Nota de alcance

La consigna pide una persistencia básica para el resultado transformado, no un modelo relacional completo del catálogo. Como mejora futura —no bloqueante para estos criterios— se podría conservar también el nombre del producto en la tabla analítica o usar una representación decimal para importes monetarios.
