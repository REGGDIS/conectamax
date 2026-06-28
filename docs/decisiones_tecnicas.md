# Decisiones tecnicas

## Arquitectura

La aplicacion mantiene una separacion por capas: `views/` para interfaz Streamlit, `services/` para casos de uso, `utils/` para validaciones reutilizables, `config/` para constantes del contrato de datos y `database/` reservado para persistencia futura. La navegacion vive en `app.py`, pero la logica de cada modulo se mantiene fuera de ese archivo.

## Uso temporal de CSV

CSV se usa como fuente temporal para validar las primeras fases funcionales sin depender de infraestructura externa. El archivo base es `data/clientes_simulados.csv` y la vista tambien permite procesar archivos CSV cargados por el usuario.

## SQLite pendiente

SQLite sera la base definitiva, pero no se integra todavia porque esta fase solo busca estabilizar contrato de datos, carga, validaciones, estado de sesion y analisis descriptivo. Esto evita acoplar la interfaz a una persistencia que aun no esta disponible.

## session_state

`st.session_state` se inicializa de forma centralizada en `app.py`. Las claves principales son `clientes_df`, `datos_cargados`, `nombre_archivo_activo`, `ultimo_archivo_procesado` y `resultado_validacion`. Las vistas `Clientes`, `Dashboard` y `Analisis` consumen temporalmente `clientes_df` como fuente activa hasta que exista persistencia.

## Uso de Plotly

Plotly se incorpora para los graficos descriptivos del dashboard porque se integra bien con Streamlit, permite visualizaciones interactivas y evita construir graficos manuales complejos. En esta fase se usa solo en la capa de vista.

## Validaciones estructurales y de calidad

Las validaciones estructurales bloquean el uso de archivos sin condiciones minimas, como DataFrame vacio, columnas obligatorias faltantes o ausencia de identificador y objetivo. Las validaciones de calidad generan advertencias sobre faltantes, duplicados, valores no convertibles, rangos invalidos y valores fuera del contrato.

## Conservacion de datos validos

Cuando un archivo invalido falla la validacion estructural, no reemplaza `clientes_df` ni `nombre_archivo_activo`. Solo actualiza `ultimo_archivo_procesado` y `resultado_validacion`, para informar el error sin perder los datos validos en uso.

## Separacion de responsabilidades

Las vistas muestran controles, mensajes, tablas y graficos, pero no contienen la logica principal de datos. `services/carga_datos_service.py` lee el CSV, reinicia el puntero si corresponde, normaliza nombres de columnas y llama a `utils/validators.py`. `services/cliente_service.py` concentra busqueda, filtros, ordenamiento, conteo y recuperacion de clientes. `services/analisis_service.py` concentra KPIs, filtros analiticos, agrupaciones y promedios por abandono. Los servicios y validadores no dependen de Streamlit ni Plotly.

## Calculos fuera de las vistas

La logica analitica se mantiene en `services/analisis_service.py` para que sea testeable y reemplazable. Las vistas `dashboard_view.py` y `analisis_view.py` solo solicitan parametros de interfaz, invocan el servicio y presentan los resultados. Esta decision evita duplicar reglas de calculo y facilita sustituir el origen de datos en una fase posterior.

## Busqueda y filtros de clientes

La busqueda y los filtros del modulo `Clientes` se mantienen en `cliente_service.py` para que sean testeables y reemplazables. La vista solo captura parametros desde Streamlit, invoca el servicio y presenta resultados.

## Migracion futura mediante repositorios

La evolucion prevista es `session_state / CSV provisional` -> repositorios -> SQLite. Los servicios deberan delegar consulta y persistencia a repositorios en `database/` para evitar modificar las vistas cuando se reemplace el DataFrame en `session_state` por consultas a SQLite. En particular, las agregaciones de `analisis_service.py` podran sustituirse gradualmente por consultas SQL cuando exista SQLite.
