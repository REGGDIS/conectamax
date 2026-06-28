# Decisiones tecnicas

## Arquitectura

La aplicacion mantiene una separacion por capas: `views/` para interfaz Streamlit, `services/` para casos de uso, `utils/` para validaciones reutilizables, `config/` para constantes del contrato de datos y `database/` reservado para persistencia futura. La navegacion vive en `app.py`, pero la logica de cada modulo se mantiene fuera de ese archivo.

## Uso temporal de CSV

CSV se usa como fuente temporal para validar la primera fase funcional sin depender de infraestructura externa. El archivo base es `data/clientes_simulados.csv` y la vista tambien permite procesar archivos CSV cargados por el usuario.

## PostgreSQL pendiente

PostgreSQL sera la base definitiva, pero no se integra todavia porque esta fase solo busca estabilizar contrato de datos, carga, validaciones y estado de sesion. Esto evita acoplar la interfaz a una persistencia que aun no esta disponible.

## session_state

`st.session_state` se inicializa de forma centralizada en `app.py`. Las claves principales son `clientes_df`, `datos_cargados`, `nombre_archivo_activo`, `ultimo_archivo_procesado` y `resultado_validacion`. La vista `Clientes` consume temporalmente `clientes_df` como fuente activa hasta que exista PostgreSQL.

## Validaciones estructurales y de calidad

Las validaciones estructurales bloquean el uso de archivos sin condiciones minimas, como DataFrame vacio, columnas obligatorias faltantes o ausencia de identificador y objetivo. Las validaciones de calidad generan advertencias sobre faltantes, duplicados, valores no convertibles, rangos invalidos y valores fuera del contrato.

## Conservacion de datos validos

Cuando un archivo invalido falla la validacion estructural, no reemplaza `clientes_df` ni `nombre_archivo_activo`. Solo actualiza `ultimo_archivo_procesado` y `resultado_validacion`, para informar el error sin perder los datos validos en uso.

## Separacion de responsabilidades

Las vistas muestran controles, mensajes y resumenes, pero no contienen la logica principal de datos. `services/carga_datos_service.py` lee el CSV, reinicia el puntero si corresponde, normaliza nombres de columnas y llama a `utils/validators.py`. `services/cliente_service.py` concentra busqueda, filtros, ordenamiento, conteo y recuperacion de clientes. Los servicios y validadores no dependen de Streamlit.

## Busqueda y filtros de clientes

La busqueda y los filtros del modulo `Clientes` se mantienen en `cliente_service.py` para que sean testeables y reemplazables. La vista solo captura parametros desde Streamlit, invoca el servicio y presenta resultados.

## Migracion futura mediante repositorios

La migracion a PostgreSQL se realizara mediante repositorios en `database/`. Los servicios deberan delegar consulta y persistencia a esos repositorios para evitar modificar las vistas cuando se reemplace el DataFrame en `session_state` por PostgreSQL.
