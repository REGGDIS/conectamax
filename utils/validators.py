"""Validaciones estructurales y de calidad para datos de clientes."""

from typing import Any

import pandas as pd

from config.settings import (
    COLUMNAS_NO_NEGATIVAS,
    COLUMNAS_NUMERICAS,
    COLUMNAS_OBLIGATORIAS,
    EDAD_MAX_RAZONABLE,
    EDAD_MIN_RAZONABLE,
    ID_COLUMN,
    SATISFACCION_MAX,
    SATISFACCION_MIN,
    TARGET_COLUMN,
    VALORES_ABANDONO_PERMITIDOS,
)


ResultadoValidacion = dict[str, Any]


def crear_resultado_base() -> ResultadoValidacion:
    """Crea la estructura comun usada por todas las validaciones."""
    return {
        "es_valido": True,
        "errores": [],
        "advertencias": [],
        "resumen": {},
    }


def validar_estructura(df: pd.DataFrame) -> ResultadoValidacion:
    """Valida condiciones estructurales que impiden usar el archivo."""
    resultado = crear_resultado_base()

    if df.empty:
        resultado["errores"].append("El archivo no contiene filas de datos.")

    columnas = set(df.columns)
    columnas_faltantes = [col for col in COLUMNAS_OBLIGATORIAS if col not in columnas]
    if columnas_faltantes:
        resultado["errores"].append(
            "Faltan columnas obligatorias: " + ", ".join(columnas_faltantes)
        )

    if ID_COLUMN not in columnas:
        resultado["errores"].append(
            f"No existe la columna identificadora obligatoria '{ID_COLUMN}'."
        )
    elif df[ID_COLUMN].isna().all() or df[ID_COLUMN].astype(str).str.strip().eq("").all():
        resultado["errores"].append(
            f"La columna identificadora '{ID_COLUMN}' esta completamente vacia."
        )

    if TARGET_COLUMN not in columnas:
        resultado["errores"].append(
            f"No existe la columna objetivo obligatoria '{TARGET_COLUMN}'."
        )

    resultado["es_valido"] = not resultado["errores"]
    resultado["resumen"].update(_crear_resumen_basico(df))
    return resultado


def validar_calidad(df: pd.DataFrame) -> ResultadoValidacion:
    """Detecta problemas de calidad que generan advertencias no bloqueantes."""
    resultado = crear_resultado_base()
    resumen = _crear_resumen_basico(df)
    resumen["valores_faltantes_por_columna"] = _contar_valores_faltantes(df)
    resumen["duplicados_id"] = _contar_identificadores_duplicados(df)

    faltantes_total = int(df.isna().sum().sum())
    if faltantes_total > 0:
        resultado["advertencias"].append(
            f"Se encontraron {faltantes_total} valores faltantes."
        )

    duplicados_id = resumen["duplicados_id"]
    if duplicados_id > 0:
        resultado["advertencias"].append(
            f"Se encontraron {duplicados_id} identificadores duplicados en '{ID_COLUMN}'."
        )

    _validar_columnas_numericas(df, resultado)
    _validar_valores_abandono(df, resultado)
    _validar_valores_no_negativos(df, resultado)
    _validar_satisfaccion(df, resultado)
    _validar_edad(df, resultado)

    resultado["resumen"].update(resumen)
    return resultado


def validar_dataframe(df: pd.DataFrame) -> ResultadoValidacion:
    """Ejecuta validaciones estructurales y, si aplica, validaciones de calidad."""
    estructura = validar_estructura(df)
    calidad = validar_calidad(df) if estructura["es_valido"] else crear_resultado_base()

    return {
        "es_valido": estructura["es_valido"],
        "errores": estructura["errores"],
        "advertencias": calidad["advertencias"],
        "resumen": {**estructura["resumen"], **calidad["resumen"]},
    }


def _crear_resumen_basico(df: pd.DataFrame) -> dict[str, Any]:
    """Resume dimensiones basicas del DataFrame."""
    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
    }


def _contar_valores_faltantes(df: pd.DataFrame) -> dict[str, int]:
    """Cuenta valores faltantes por columna."""
    return {col: int(total) for col, total in df.isna().sum().items() if int(total) > 0}


def _contar_identificadores_duplicados(df: pd.DataFrame) -> int:
    """Cuenta filas con identificador duplicado, si existe la columna."""
    if ID_COLUMN not in df.columns:
        return 0
    return int(df[ID_COLUMN].duplicated().sum())


def _validar_columnas_numericas(df: pd.DataFrame, resultado: ResultadoValidacion) -> None:
    """Advierte columnas numericas con valores no convertibles."""
    for columna in COLUMNAS_NUMERICAS:
        if columna not in df.columns:
            continue
        valores = df[columna].dropna()
        no_convertibles = pd.to_numeric(valores, errors="coerce").isna().sum()
        if int(no_convertibles) > 0:
            resultado["advertencias"].append(
                f"La columna '{columna}' tiene {int(no_convertibles)} valores no numericos."
            )


def _validar_valores_abandono(df: pd.DataFrame, resultado: ResultadoValidacion) -> None:
    """Advierte valores de abandono distintos de los permitidos."""
    if TARGET_COLUMN not in df.columns:
        return
    serie = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    invalidos = df[TARGET_COLUMN].notna() & ~serie.isin(VALORES_ABANDONO_PERMITIDOS)
    if int(invalidos.sum()) > 0:
        resultado["advertencias"].append(
            f"La columna '{TARGET_COLUMN}' contiene valores distintos de 0 y 1."
        )


def _validar_valores_no_negativos(df: pd.DataFrame, resultado: ResultadoValidacion) -> None:
    """Advierte valores negativos en columnas que deben ser no negativas."""
    for columna in COLUMNAS_NO_NEGATIVAS:
        if columna not in df.columns:
            continue
        serie = pd.to_numeric(df[columna], errors="coerce")
        negativos = int((serie < 0).sum())
        if negativos > 0:
            resultado["advertencias"].append(
                f"La columna '{columna}' contiene {negativos} valores negativos."
            )


def _validar_satisfaccion(df: pd.DataFrame, resultado: ResultadoValidacion) -> None:
    """Advierte satisfacciones fuera del rango configurado."""
    columna = "satisfaccion"
    if columna not in df.columns:
        return
    serie = pd.to_numeric(df[columna], errors="coerce")
    fuera_rango = int(((serie < SATISFACCION_MIN) | (serie > SATISFACCION_MAX)).sum())
    if fuera_rango > 0:
        resultado["advertencias"].append(
            f"La columna '{columna}' tiene {fuera_rango} valores fuera del rango 1 a 5."
        )


def _validar_edad(df: pd.DataFrame, resultado: ResultadoValidacion) -> None:
    """Advierte edades negativas o poco razonables cuando la columna exista."""
    columna = "edad"
    if columna not in df.columns:
        return
    serie = pd.to_numeric(df[columna], errors="coerce")
    fuera_rango = int(
        ((serie < EDAD_MIN_RAZONABLE) | (serie > EDAD_MAX_RAZONABLE)).sum()
    )
    if fuera_rango > 0:
        resultado["advertencias"].append(
            f"La columna '{columna}' tiene {fuera_rango} edades negativas o poco razonables."
        )
