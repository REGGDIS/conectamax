# ConectaMax

Aplicacion academica tipo CRM para analizar y, en fases posteriores, predecir el abandono de clientes de una empresa ficticia de telecomunicaciones.

## Estado actual

La primera fase funcional permite cargar datos de clientes desde CSV, validar su estructura, mostrar advertencias de calidad y conservar los datos validos activos en la sesion de Streamlit.

## Funcionalidades implementadas

- Contrato provisional de datos centralizado en `config/settings.py`.
- CSV simulado disponible en `data/clientes_simulados.csv`.
- Carga de CSV desde Streamlit mediante la vista `Carga de datos`.
- Boton para cargar el CSV simulado incluido en el proyecto.
- Boton para limpiar los datos activos y reiniciar el cargador de archivos.
- Validaciones estructurales bloqueantes y validaciones de calidad no bloqueantes.
- Servicio desacoplado para lectura, normalizacion de columnas y validacion de CSV.
- Estado centralizado con `st.session_state`.
- Navegacion inicial con modulos pendientes.
- Pruebas unitarias para validadores, servicio de carga y CSV simulado.

## Dependencias

Esta fase utiliza solo:

- `streamlit`
- `pandas`
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

- Dashboard completo.
- Modulo de clientes.
- Graficos de analisis.
- PostgreSQL.
- SQLAlchemy.
- Modelo predictivo.
- Reportes.
- Autenticacion.

PostgreSQL sera integrado en una fase posterior como base definitiva del proyecto.
