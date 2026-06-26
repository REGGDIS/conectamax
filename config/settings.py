"""Configuracion central del contrato provisional de datos."""

from pathlib import Path


APP_NAME = "ConectaMax"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_EJEMPLO_PATH = DATA_DIR / "clientes_simulados.csv"

ID_COLUMN = "id_cliente"
TARGET_COLUMN = "abandono"

COLUMNAS_OBLIGATORIAS = [
    "id_cliente",
    "nombre",
    "ciudad",
    "antiguedad_meses",
    "tipo_contrato",
    "plan",
    "monto_mensual",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    "satisfaccion",
    "abandono",
]

COLUMNAS_OPCIONALES = [
    "edad",
    "cantidad_servicios",
]

COLUMNAS_NUMERICAS = [
    "antiguedad_meses",
    "monto_mensual",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    "satisfaccion",
    "abandono",
    "edad",
    "cantidad_servicios",
]

COLUMNAS_TEXTO = [
    "id_cliente",
    "nombre",
    "ciudad",
    "tipo_contrato",
    "plan",
]

VALORES_ABANDONO_PERMITIDOS = [0, 1]
COLUMNAS_NO_NEGATIVAS = [
    "antiguedad_meses",
    "monto_mensual",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    "satisfaccion",
    "abandono",
    "edad",
    "cantidad_servicios",
]

SATISFACCION_MIN = 1
SATISFACCION_MAX = 5
EDAD_MIN_RAZONABLE = 0
EDAD_MAX_RAZONABLE = 110
