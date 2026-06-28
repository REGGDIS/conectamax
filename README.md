# ConectaMax

Aplicacion academica tipo CRM para analizar y, en fases posteriores, predecir el abandono de clientes de una empresa ficticia de telecomunicaciones.

## Estado actual

La aplicacion permite cargar datos de clientes desde CSV, validar su estructura, conservar los datos validos activos en la sesion de Streamlit, consultar clientes y revisar un dashboard con analisis descriptivo del abandono.

## Funcionalidades implementadas

- Contrato provisional de datos centralizado en `config/settings.py`.
- CSV simulado disponible en `data/clientes_simulados.csv`.
- Carga de CSV desde Streamlit mediante la vista `Carga de datos`.
- Boton para cargar el CSV simulado incluido en el proyecto.
- Boton para limpiar los datos activos y reiniciar el cargador de archivos.
- Validaciones estructurales bloqueantes y validaciones de calidad no bloqueantes.
- Servicio desacoplado para lectura, normalizacion de columnas y validacion de CSV.
- Estado centralizado con `st.session_state`.
- Modulo `Clientes` para consultar, buscar, filtrar, ordenar y revisar fichas individuales.
- Modulo `Dashboard` con KPIs, filtros generales y graficos descriptivos en Plotly.
- Modulo `Analisis` con tablas resumen, comparacion por estado de abandono y conclusiones descriptivas simples.
- Navegacion con Prediccion como modulo pendiente.
- Pruebas unitarias para validadores, servicio de carga, servicio de clientes, servicio de analisis y CSV simulado.

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

## Dependencias

Esta fase utiliza solo:

- `streamlit`
- `pandas`
- `plotly`
- `pytest`

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

Si un archivo invalido se procesa despues de uno valido, los datos activos anteriores se conservan.

## Funcionalidades pendientes

- Persistencia en SQLite.
- Integracion con la base de datos.
- Limpieza/preparacion avanzada.
- Modelo predictivo.
- Clasificacion de riesgo.
- Reportes finales.
- Autenticacion.

SQLite sera integrado en una fase posterior como base definitiva del proyecto.

## Limitaciones actuales

- Los modulos `Dashboard` y `Analisis` consumen temporalmente `st.session_state["clientes_df"]`.
- No existe persistencia de datos; al reiniciar la sesion se deben cargar nuevamente.
- No hay modelo predictivo ni clasificacion de riesgo.
- Los graficos y conclusiones son descriptivos y no implican causalidad.
