"""Servicio para carga y validacion de archivos CSV de clientes."""

from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd

from utils.validators import crear_resultado_base, validar_dataframe


def cargar_y_validar_csv(archivo: str | Path | BinaryIO | Any) -> tuple[pd.DataFrame | None, dict]:
    """Lee un CSV, normaliza columnas y devuelve datos con resultado de validacion."""
    try:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
        df = pd.read_csv(archivo)
    except pd.errors.EmptyDataError:
        resultado = crear_resultado_base()
        resultado["es_valido"] = False
        resultado["errores"].append("El archivo CSV esta vacio o no contiene columnas.")
        return None, resultado
    except (UnicodeDecodeError, pd.errors.ParserError, OSError, ValueError) as exc:
        resultado = crear_resultado_base()
        resultado["es_valido"] = False
        resultado["errores"].append(f"No fue posible leer el archivo CSV: {exc}")
        return None, resultado

    df = normalizar_columnas(df)
    resultado = validar_dataframe(df)
    if not resultado["es_valido"]:
        return None, resultado

    return df, resultado


def construir_estado_carga(
    estado_actual: dict[str, Any],
    df: pd.DataFrame | None,
    resultado: dict,
    nombre_archivo: str,
) -> dict[str, Any]:
    """Construye el estado posterior a un intento de carga sin depender de Streamlit."""
    nuevo_estado = {
        "clientes_df": estado_actual.get("clientes_df"),
        "datos_cargados": estado_actual.get("datos_cargados", False),
        "nombre_archivo_activo": estado_actual.get("nombre_archivo_activo"),
        "ultimo_archivo_procesado": nombre_archivo,
        "resultado_validacion": resultado,
    }

    if resultado.get("es_valido") and df is not None:
        nuevo_estado["clientes_df"] = df
        nuevo_estado["datos_cargados"] = True
        nuevo_estado["nombre_archivo_activo"] = nombre_archivo

    return nuevo_estado


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina espacios externos en los nombres de columnas."""
    df_normalizado = df.copy()
    df_normalizado.columns = [str(col).strip() for col in df_normalizado.columns]
    return df_normalizado
