"""Servicios puros de Pandas para analisis descriptivo de clientes."""

from typing import Any

import pandas as pd

from config.settings import (
    COLUMNAS_AGRUPACION_ANALISIS,
    ETIQUETAS_ABANDONO,
    TARGET_COLUMN,
)


NUMERIC_COLUMNS = {
    TARGET_COLUMN,
    "monto_mensual",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    "satisfaccion",
}


def normalizar_dataframe_analisis(df: pd.DataFrame | None) -> pd.DataFrame:
    """Devuelve una copia segura del DataFrame para analisis."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.copy(deep=True)


def calcular_total_clientes(df: pd.DataFrame | None) -> int:
    """Calcula la cantidad total de clientes disponibles."""
    datos = normalizar_dataframe_analisis(df)
    return int(len(datos))


def calcular_clientes_abandonaron(df: pd.DataFrame | None) -> int:
    """Calcula la cantidad de clientes con abandono igual a 1."""
    abandono = _serie_numerica(df, TARGET_COLUMN)
    if abandono.empty:
        return 0
    return int((abandono == 1).sum())


def calcular_clientes_permanecen(df: pd.DataFrame | None) -> int:
    """Calcula la cantidad de clientes con abandono igual a 0."""
    abandono = _serie_numerica(df, TARGET_COLUMN)
    if abandono.empty:
        return 0
    return int((abandono == 0).sum())


def calcular_tasa_abandono(df: pd.DataFrame | None) -> float:
    """Calcula la tasa de abandono como porcentaje entre clientes validos."""
    abandono = _serie_numerica(df, TARGET_COLUMN).dropna()
    abandono = abandono[abandono.isin([0, 1])]
    if abandono.empty:
        return 0.0
    return float((abandono == 1).mean() * 100)


def calcular_tasa_retencion(df: pd.DataFrame | None) -> float:
    """Calcula la tasa de retencion como porcentaje entre clientes validos."""
    abandono = _serie_numerica(df, TARGET_COLUMN).dropna()
    abandono = abandono[abandono.isin([0, 1])]
    if abandono.empty:
        return 0.0
    return float((abandono == 0).mean() * 100)


def calcular_satisfaccion_promedio(df: pd.DataFrame | None) -> float:
    """Calcula la satisfaccion promedio."""
    return _promedio(df, "satisfaccion")


def calcular_monto_mensual_promedio(df: pd.DataFrame | None) -> float:
    """Calcula el monto mensual promedio."""
    return _promedio(df, "monto_mensual")


def calcular_reclamos_promedio(df: pd.DataFrame | None) -> float:
    """Calcula el promedio de reclamos de los ultimos 6 meses."""
    return _promedio(df, "reclamos_ultimos_6_meses")


def calcular_pagos_atrasados_promedio(df: pd.DataFrame | None) -> float:
    """Calcula el promedio de pagos atrasados."""
    return _promedio(df, "pagos_atrasados")


def calcular_dias_sin_uso_promedio(df: pd.DataFrame | None) -> float:
    """Calcula el promedio de dias sin uso."""
    return _promedio(df, "dias_sin_uso")


def calcular_kpis(df: pd.DataFrame | None) -> dict[str, float | int]:
    """Calcula los indicadores principales del dashboard."""
    return {
        "total_clientes": calcular_total_clientes(df),
        "clientes_permanecen": calcular_clientes_permanecen(df),
        "clientes_abandonaron": calcular_clientes_abandonaron(df),
        "tasa_abandono": calcular_tasa_abandono(df),
        "tasa_retencion": calcular_tasa_retencion(df),
        "satisfaccion_promedio": calcular_satisfaccion_promedio(df),
        "monto_mensual_promedio": calcular_monto_mensual_promedio(df),
        "reclamos_promedio": calcular_reclamos_promedio(df),
        "pagos_atrasados_promedio": calcular_pagos_atrasados_promedio(df),
        "dias_sin_uso_promedio": calcular_dias_sin_uso_promedio(df),
    }


def aplicar_filtros_analisis(
    df: pd.DataFrame | None,
    ciudades: list[str] | None = None,
    tipos_contrato: list[str] | None = None,
    planes: list[str] | None = None,
    abandono: int | None = None,
) -> pd.DataFrame:
    """Aplica filtros generales de analisis sin modificar el DataFrame original."""
    datos = normalizar_dataframe_analisis(df)
    if datos.empty:
        return datos

    datos = _filtrar_por_opciones(datos, "ciudad", ciudades)
    datos = _filtrar_por_opciones(datos, "tipo_contrato", tipos_contrato)
    datos = _filtrar_por_opciones(datos, "plan", planes)

    if abandono is not None and TARGET_COLUMN in datos.columns:
        abandono_numerico = pd.to_numeric(datos[TARGET_COLUMN], errors="coerce")
        datos = datos.loc[abandono_numerico == abandono].copy()

    return datos.copy()


def calcular_abandono_por_categoria(
    df: pd.DataFrame | None,
    columna: str,
) -> pd.DataFrame:
    """Calcula total, abandonos y tasa de abandono por una categoria permitida."""
    datos = _preparar_datos_numericos(df, [TARGET_COLUMN])
    columnas_resultado = [columna, "total_clientes", "clientes_abandonaron", "tasa_abandono"]
    if datos.empty or columna not in datos.columns or columna not in COLUMNAS_AGRUPACION_ANALISIS:
        return pd.DataFrame(columns=columnas_resultado)

    datos = datos.dropna(subset=[columna]).copy()
    datos[columna] = datos[columna].astype(str).str.strip()
    datos = datos[datos[columna] != ""]
    datos = datos[datos[TARGET_COLUMN].isin([0, 1])]
    if datos.empty:
        return pd.DataFrame(columns=columnas_resultado)

    resumen = (
        datos.groupby(columna, dropna=False)[TARGET_COLUMN]
        .agg(total_clientes="count", clientes_abandonaron="sum")
        .reset_index()
    )
    resumen["clientes_abandonaron"] = resumen["clientes_abandonaron"].astype(int)
    resumen["tasa_abandono"] = resumen.apply(
        lambda fila: _porcentaje(fila["clientes_abandonaron"], fila["total_clientes"]),
        axis=1,
    )
    return resumen.sort_values("tasa_abandono", ascending=False, kind="mergesort").reset_index(drop=True)


def calcular_satisfaccion_promedio_por_abandono(df: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula satisfaccion promedio agrupada por estado de abandono."""
    return calcular_promedio_por_abandono(df, "satisfaccion")


def calcular_reclamos_promedio_por_abandono(df: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula reclamos promedio agrupados por estado de abandono."""
    return calcular_promedio_por_abandono(df, "reclamos_ultimos_6_meses")


def calcular_pagos_atrasados_promedio_por_abandono(df: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula pagos atrasados promedio agrupados por estado de abandono."""
    return calcular_promedio_por_abandono(df, "pagos_atrasados")


def calcular_dias_sin_uso_promedio_por_abandono(df: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula dias sin uso promedio agrupados por estado de abandono."""
    return calcular_promedio_por_abandono(df, "dias_sin_uso")


def calcular_promedio_por_abandono(df: pd.DataFrame | None, columna: str) -> pd.DataFrame:
    """Calcula el promedio de una metrica numerica segun estado de abandono."""
    columnas_resultado = ["abandono", "estado_abandono", "promedio"]
    datos = _preparar_datos_numericos(df, [TARGET_COLUMN, columna])
    if datos.empty or columna not in datos.columns or TARGET_COLUMN not in datos.columns:
        return pd.DataFrame(columns=columnas_resultado)

    datos = datos[datos[TARGET_COLUMN].isin([0, 1])].copy()
    if datos.empty:
        return pd.DataFrame(columns=columnas_resultado)

    resumen = datos.groupby(TARGET_COLUMN, dropna=False)[columna].mean().reset_index(name="promedio")
    resumen["abandono"] = resumen[TARGET_COLUMN].astype(int)
    resumen["estado_abandono"] = resumen["abandono"].map(ETIQUETAS_ABANDONO)
    return resumen.loc[:, columnas_resultado].sort_values("abandono").reset_index(drop=True)


def contar_por_abandono(df: pd.DataFrame | None) -> pd.DataFrame:
    """Cuenta clientes por estado de abandono con etiquetas legibles."""
    columnas_resultado = ["abandono", "estado_abandono", "total_clientes"]
    datos = _preparar_datos_numericos(df, [TARGET_COLUMN])
    if datos.empty or TARGET_COLUMN not in datos.columns:
        return pd.DataFrame(columns=columnas_resultado)

    datos = datos[datos[TARGET_COLUMN].isin([0, 1])].copy()
    if datos.empty:
        return pd.DataFrame(columns=columnas_resultado)

    resumen = datos.groupby(TARGET_COLUMN).size().reset_index(name="total_clientes")
    resumen["abandono"] = resumen[TARGET_COLUMN].astype(int)
    resumen["estado_abandono"] = resumen["abandono"].map(ETIQUETAS_ABANDONO)
    return resumen.loc[:, columnas_resultado].sort_values("abandono").reset_index(drop=True)


def obtener_opciones_filtro_analisis(df: pd.DataFrame | None, columna: str) -> list[str]:
    """Obtiene valores unicos no vacios para filtros de analisis."""
    datos = normalizar_dataframe_analisis(df)
    if datos.empty or columna not in datos.columns:
        return []

    serie = datos[columna].dropna().astype(str).str.strip()
    valores = [valor for valor in serie.unique().tolist() if valor]
    return sorted(valores, key=str.casefold)


def _promedio(df: pd.DataFrame | None, columna: str) -> float:
    """Calcula un promedio numerico seguro."""
    serie = _serie_numerica(df, columna).dropna()
    if serie.empty:
        return 0.0
    return float(serie.mean())


def _serie_numerica(df: pd.DataFrame | None, columna: str) -> pd.Series:
    """Devuelve una serie numerica convertida con coercion de errores."""
    datos = normalizar_dataframe_analisis(df)
    if datos.empty or columna not in datos.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(datos[columna], errors="coerce")


def _preparar_datos_numericos(df: pd.DataFrame | None, columnas: list[str]) -> pd.DataFrame:
    """Copia el DataFrame y convierte columnas numericas solicitadas."""
    datos = normalizar_dataframe_analisis(df)
    if datos.empty:
        return datos
    for columna in columnas:
        if columna in datos.columns and columna in NUMERIC_COLUMNS:
            datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
    return datos


def _filtrar_por_opciones(
    df: pd.DataFrame,
    columna: str,
    opciones: list[str] | None,
) -> pd.DataFrame:
    """Aplica un filtro por opciones de texto si corresponde."""
    if not opciones or columna not in df.columns:
        return df.copy()
    opciones_limpias = {str(opcion).strip() for opcion in opciones if str(opcion).strip()}
    if not opciones_limpias:
        return df.copy()
    serie = df[columna].astype(str).str.strip()
    return df.loc[serie.isin(opciones_limpias)].copy()


def _porcentaje(numerador: Any, denominador: Any) -> float:
    """Calcula porcentaje evitando division por cero."""
    denominador_num = pd.to_numeric(pd.Series([denominador]), errors="coerce").iloc[0]
    numerador_num = pd.to_numeric(pd.Series([numerador]), errors="coerce").iloc[0]
    if pd.isna(denominador_num) or denominador_num == 0 or pd.isna(numerador_num):
        return 0.0
    return float((numerador_num / denominador_num) * 100)
