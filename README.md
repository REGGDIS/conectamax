# ConectaMax

Aplicacion academica tipo CRM para analizar y, en fases posteriores, predecir el abandono de clientes de una empresa ficticia de telecomunicaciones.

## Estado actual

La aplicacion permite cargar datos de clientes desde CSV, validar su estructura, conservar los datos validos activos en la sesion de Streamlit, preparar un dataset limpio, consultar clientes y revisar un dashboard con analisis descriptivo del abandono.

## Funcionalidades implementadas

- Contrato provisional de datos centralizado en `config/settings.py`.
- CSV simulado disponible en `data/clientes_simulados.csv`.
- Carga de CSV desde Streamlit mediante la vista `Carga de datos`.
- Boton para cargar el CSV simulado incluido en el proyecto.
- Boton para limpiar los datos activos y reiniciar el cargador de archivos.
- Validaciones estructurales bloqueantes y validaciones de calidad no bloqueantes.
- Servicio desacoplado para lectura, normalizacion de columnas y validacion de CSV.
- Estado centralizado con `st.session_state`.
- Preparacion avanzada de datos con reporte de limpieza y descarga de CSV preparado.
- Modulo `Clientes` para consultar, buscar, filtrar, ordenar y revisar fichas individuales.
- Modulo `Dashboard` con KPIs, filtros generales y graficos descriptivos en Plotly.
- Modulo `Analisis` con tablas resumen, comparacion por estado de abandono y conclusiones descriptivas simples.
- Infraestructura desacoplada para SQLite usando `sqlite3` de la biblioteca estandar.
- Repositorio provisional de clientes para pruebas de conexion y acceso a datos.
- Navegacion con Prediccion como modulo pendiente.
- Pruebas unitarias para validadores, servicios, infraestructura SQLite y CSV simulado.

## Modulo Clientes

El modulo `Clientes` usa el DataFrame activo almacenado en `st.session_state["clientes_df"]`.

Permite buscar por identificador o nombre. La busqueda ignora mayusculas, elimina espacios externos y acepta coincidencias parciales.

Filtros disponibles:

- Ciudad.
- Tipo de contrato.
- Plan.
- Estado de abandono: `Todos`, `Permanece`, `Abandonó`.

Ordenamiento disponible:

- `id_cliente`
- `nombre`
- `ciudad`
- `antiguedad_meses`
- `monto_mensual`
- `satisfaccion`

La vista muestra una tabla resumida de resultados y una ficha del cliente seleccionado con sus datos principales. No permite editar ni eliminar clientes en esta fase.

## Modulo Dashboard

El modulo `Dashboard` usa temporalmente el DataFrame activo almacenado en `st.session_state["clientes_df"]`.

Filtros generales disponibles:

- Ciudad.
- Tipo de contrato.
- Plan.
- Estado de abandono: `Todos`, `Permanece`, `Abandonó`.

KPIs implementados:

- Total de clientes.
- Clientes que permanecen.
- Clientes que abandonaron.
- Tasa de abandono.
- Tasa de retencion.
- Satisfaccion promedio.
- Monto mensual promedio.
- Reclamos promedio.
- Pagos atrasados promedio.
- Dias sin uso promedio.

Graficos disponibles:

- Clientes que permanecen frente a clientes que abandonaron.
- Tasa de abandono por tipo de contrato.
- Tasa de abandono por ciudad.
- Tasa de abandono por plan.
- Satisfaccion promedio segun abandono.
- Reclamos promedio segun abandono.
- Pagos atrasados promedio segun abandono.
- Dias sin uso promedio segun abandono.

Si no hay datos cargados o los filtros no devuelven registros, la vista muestra mensajes controlados y no genera errores.

## Modulo Analisis

El modulo `Analisis` complementa el dashboard con tablas resumen por tipo de contrato, ciudad y plan. Tambien muestra una comparacion de metricas promedio por estado de abandono y conclusiones descriptivas automaticas simples.

Las conclusiones usan expresiones descriptivas como "En los datos analizados se observa..." y no establecen causalidad.

## Preparacion avanzada de datos

La vista `Carga de datos` incluye una seccion `Preparación avanzada` que ejecuta un proceso reproducible sobre el DataFrame activo. El dataset original se conserva en `st.session_state["clientes_df"]` y el resultado limpio se guarda por separado en `st.session_state["clientes_df_limpio"]`.

Reglas principales de limpieza:

- Normalizacion de `id_cliente`, eliminacion de IDs vacios y duplicados conservando la primera aparicion.
- Normalizacion de textos en `nombre`, `ciudad`, `tipo_contrato` y `plan`.
- Conversion numerica con `pd.to_numeric(..., errors="coerce")`.
- Imputacion por mediana para edad, antiguedad, monto mensual, cantidad de servicios, dias sin uso y satisfaccion.
- Imputacion con cero para reclamos y pagos atrasados.
- Eliminacion de filas con `abandono` faltante o distinto de `0` y `1`.
- Correccion de valores fuera de rango mediante conversion a faltante y posterior imputacion.

Variables derivadas agregadas:

- `grupo_edad`.
- `grupo_antiguedad`.
- `nivel_satisfaccion`.
- `tiene_morosidad`.
- `tiene_reclamos`.

El reporte de limpieza resume filas iniciales y finales, filas eliminadas, duplicados, IDs vacios, objetivos invalidos, valores no convertibles, valores fuera de rango, imputaciones y columnas derivadas. El CSV preparado puede descargarse como `clientes_preparados.csv` sin escribir archivos automaticamente en el repositorio.

## Infraestructura SQLite

La ruta futura de base de datos esta centralizada en `config/settings.py` mediante `DATABASE_PATH`, apuntando a `data/conectamax.db` sin rutas absolutas.

La capa `database/` incluye:

- `connection.py`: apertura, verificacion y cierre de conexiones SQLite con `sqlite3`.
- `models.py`: tabla minima `clientes_prueba`, exclusiva para pruebas de infraestructura.
- `cliente_repository.py`: insercion, consulta por ID, consulta total y conteo sobre la tabla provisional.

Esta infraestructura no reemplaza todavia `st.session_state["clientes_df"]` ni define el esquema definitivo. El archivo `conectamax.db`, el script SQL final, el modelo de tablas, el diccionario de datos y el generador de 2.000 clientes siguen pendientes.

Las pruebas de base de datos usan bases SQLite temporales creadas con `tmp_path`; no usan `data/conectamax.db`.

## Dependencias

Esta fase utiliza solo:

- `streamlit`
- `pandas`
- `plotly`
- `pytest`

SQLite se usa mediante `sqlite3`, incluido en la biblioteca estandar de Python.

## Instalacion

Ejecutar los comandos con el entorno virtual activo.

```powershell
python -m pip install -r requirements.txt
```

## Ejecucion

```powershell
python -m streamlit run app.py
```

## Pruebas

```powershell
python -m pytest
```

## Contrato provisional de datos

Columnas obligatorias:

```text
id_cliente
nombre
ciudad
antiguedad_meses
tipo_contrato
plan
monto_mensual
reclamos_ultimos_6_meses
pagos_atrasados
dias_sin_uso
satisfaccion
abandono
```

Columnas opcionales:

```text
edad
cantidad_servicios
```

La columna `abandono` acepta solo:

- `0`: permanece
- `1`: abandono

La columna `id_cliente` actua como identificador unico provisional.

## CSV simulado

El archivo `data/clientes_simulados.csv` contiene 45 clientes ficticios, sin duplicados ni valores faltantes. Puede cargarse desde la vista `Carga de datos` con el boton `Usar CSV simulado`.

## Estado de sesion

La aplicacion mantiene estas claves principales en `st.session_state`:

- `clientes_df`: DataFrame activo valido.
- `datos_cargados`: indica si existen datos validos activos.
- `nombre_archivo_activo`: archivo cuyos datos estan actualmente en uso.
- `ultimo_archivo_procesado`: ultimo archivo que se intento validar.
- `resultado_validacion`: resultado del ultimo intento de validacion.
- `clientes_df_limpio`: DataFrame preparado por la limpieza avanzada.
- `reporte_limpieza`: resumen del proceso de preparacion.
- `datos_preparados`: indica si existe un dataset limpio activo.

Si un archivo invalido se procesa despues de uno valido, los datos activos anteriores se conservan.

## Funcionalidades pendientes

- Persistencia en SQLite.
- Integracion con la base de datos.
- Esquema definitivo de SQLite.
- Modelo predictivo.
- Clasificacion de riesgo.
- Reportes finales.
- Autenticacion.

SQLite sera integrado en una fase posterior como base definitiva del proyecto.

## Limitaciones actuales

- Los modulos `Dashboard` y `Analisis` consumen temporalmente `st.session_state["clientes_df"]`.
- El dataset limpio queda preparado y descargable, pero no reemplaza globalmente al dataset original.
- La infraestructura SQLite existe, pero las vistas y servicios funcionales aun no la consumen.
- La tabla `clientes_prueba` no representa el esquema definitivo.
- No existe persistencia de datos; al reiniciar la sesion se deben cargar nuevamente.
- No hay modelo predictivo ni clasificacion de riesgo.
- Los graficos y conclusiones son descriptivos y no implican causalidad.
