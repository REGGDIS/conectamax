"""Configuracion central del contrato provisional de datos."""

from pathlib import Path


APP_NAME = "ConectaMax"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_EJEMPLO_PATH = DATA_DIR / "clientes_simulados.csv"
DATABASE_PATH = DATA_DIR / "conectamax.db"

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

COLUMNAS_CLIENTES_TABLA = [
    "id_cliente",
    "nombre",
    "ciudad",
    "tipo_contrato",
    "plan",
    "monto_mensual",
    "satisfaccion",
    "abandono",
]

COLUMNAS_ORDEN_CLIENTES = [
    "id_cliente",
    "nombre",
    "ciudad",
    "antiguedad_meses",
    "monto_mensual",
    "satisfaccion",
]

ETIQUETAS_ABANDONO = {
    0: "Permanece",
    1: "Abandonó",
}

OPCIONES_FILTRO_ABANDONO = {
    "Todos": None,
    "Permanece": 0,
    "Abandonó": 1,
}

COLUMNAS_AGRUPACION_ANALISIS = [
    "ciudad",
    "tipo_contrato",
    "plan",
]

ETIQUETAS_COLUMNAS_ANALISIS = {
    "ciudad": "Ciudad",
    "tipo_contrato": "Tipo de contrato",
    "plan": "Plan",
    "satisfaccion": "Satisfacción promedio",
    "reclamos_ultimos_6_meses": "Reclamos promedio",
    "pagos_atrasados": "Pagos atrasados promedio",
    "dias_sin_uso": "Días sin uso promedio",
}
