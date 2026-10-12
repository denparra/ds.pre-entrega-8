# Pre-entrega: Persistencia e integración de scripts ETL

## Objetivo

Implementar un flujo de trabajo que automatice la persistencia de datos desde un origen transaccional hacia una base de datos analítica. El proceso debe ser **repetible y estar documentado**.

Esta práctica consolida los conceptos de capa de persistencia e integración de scripts **ETL** (*Extract, Transform, Load*): extraer, transformar y cargar datos.

## Qué debes construir

Crea un repositorio de código con un script de automatización —en **Python o SQL**— que realice este flujo:

1. Conectarse con una fuente de datos. Puede ser un dataset local o una base de datos remota.
2. Aplicar una transformación básica, como limpieza o agregación.
3. Cargar el resultado en una base de datos local: **SQLite o MySQL**.
4. Incluir un `README.md` que explique cómo ejecutar el proceso.

> **Opción recomendada para esta entrega:** SQLite. Es local, no requiere configurar un servidor y cumple con la consigna. MySQL también es válido.

## Entregable

Un **repositorio público en GitHub** que incluya:

- Los scripts de automatización ETL.
- El esquema de la base de datos y la definición de la tabla de destino.
- Un `README.md` con instrucciones de ejecución.
- Un archivo `.gitignore` adecuado para el proyecto.

## Pasos sugeridos

1. **Inicialización:** crea el repositorio en GitHub e incluye un `.gitignore` adecuado.
2. **Persistencia:** diseña el esquema de la tabla donde guardarás los datos transformados.
3. **Automatización:** escribe el script para extraer, transformar y cargar los datos. Trata errores comunes de conexión.
4. **Documentación:** explica en el README el patrón de datos utilizado y cómo configurar y ejecutar el entorno.

## Criterios de revisión

- [ ] El repositorio contiene un script funcional que ejecuta la carga sin errores de sintaxis.
- [ ] El README tiene secciones claras y concisas de **Requisitos** y **Pasos para ejecutar**.
- [ ] Un archivo SQL o el propio script define la creación de la tabla de destino (**DDL**).
- [ ] El historial de commits muestra avances incrementales con mensajes descriptivos.
- [ ] La carga evita duplicar datos, por ejemplo, mediante una clave o una limpieza previa de la tabla.

## Conexión con el contenido del módulo

Este entregable aplica los conceptos de **capas de persistencia** y **automatización de procesos ETL**. El objetivo es pasar de ejecutar consultas manualmente a contar con un proceso de datos coordinado mediante código.
