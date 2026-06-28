"""Servicios puros de Pandas para limpieza y preparacion avanzada."""

from typing import Any

import pandas as pd

from config.settings import (
    COLUMNAS_DERIVADAS_LIMPIEZA,
    COLUMNAS_NUMERICAS_LIMPIEZA,
    COLUMNAS_TEXTO_LIMPIEZA,
    ID_COLUMN,
    RANGOS_VALIDOS_LIMPIEZA,
    TARGET_COLUMN,
    VALORES_RESPALDO_LIMPIEZA,
)


COLUMNAS_ENTERAS = [
    "edad",
    "antiguedad_meses",
    "cantidad_servicios",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    TARGET_COLUMN,
]

COLUMNAS_MEDIANA = [
    "edad",
    "antiguedad_meses",
    "monto_mensual",
    "cantidad_servicios",
    "dias_sin_uso",
    "satisfaccion",
]

COLUMNAS_CERO = [
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
]


def preparar_datos(df: pd.DataFrame | None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Limpia y prepara un DataFrame de clientes sin modificar el original."""
    datos = _normalizar_dataframe(df)
    reporte = _crear_reporte(len(datos))
    if datos.empty:
        reporte["filas_finales"] = 0
        return datos, reporte

    datos = _limpiar_identificadores(datos, reporte)
    datos = _limpiar_textos(datos)
    datos = _convertir_columnas_numericas(datos, reporte)
    datos = _aplicar_rangos_validos(datos, reporte)
    datos = _eliminar_abandono_invalido(datos, reporte)
    datos = _imputar_numericos(datos, reporte)
    datos = _aplicar_tipos_finales(datos)
    datos = _crear_variables_derivadas(datos)

    reporte["filas_finales"] = int(len(datos))
    reporte["filas_eliminadas"] = reporte["filas_iniciales"] - reporte["filas_finales"]
    reporte["columnas_derivadas"] = [col for col in COLUMNAS_DERIVADAS_LIMPIEZA if col in datos.columns]
    return datos.reset_index(drop=True), reporte


def _normalizar_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    """Devuelve una copia profunda o un DataFrame vacio si no hay datos."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.copy(deep=True)


def _crear_reporte(filas_iniciales: int) -> dict[str, Any]:
    """Crea la estructura base del reporte de limpieza."""
    return {
        "filas_iniciales": int(filas_iniciales),
        "filas_finales": 0,
        "filas_eliminadas": 0,
        "duplicados_eliminados": 0,
        "ids_vacios_eliminados": 0,
        "abandono_invalido_eliminado": 0,
        "valores_no_convertibles": {},
        "valores_fuera_de_rango": {},
        "valores_imputados": {},
        "valores_respaldo_usados": {},
        "columnas_derivadas": [],
    }


def _limpiar_identificadores(df: pd.DataFrame, reporte: dict[str, Any]) -> pd.DataFrame:
    """Normaliza ID, elimina vacios y conserva la primera aparicion duplicada."""
    if ID_COLUMN not in df.columns:
        return df.copy()

    datos = df.copy()
    datos[ID_COLUMN] = _normalizar_texto_basico(datos[ID_COLUMN])
    ids_vacios = datos[ID_COLUMN].eq("")
    reporte["ids_vacios_eliminados"] = int(ids_vacios.sum())
    datos = datos.loc[~ids_vacios].copy()

    duplicados = datos.duplicated(subset=[ID_COLUMN], keep="first")
    reporte["duplicados_eliminados"] = int(duplicados.sum())
    return datos.loc[~duplicados].copy()


def _limpiar_textos(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombre, ciudad, tipo de contrato y plan."""
    datos = df.copy()
    if "nombre" in datos.columns:
        datos["nombre"] = _normalizar_texto_basico(datos["nombre"])
        datos.loc[datos["nombre"].eq(""), "nombre"] = "Cliente sin nombre"

    for columna in COLUMNAS_TEXTO_LIMPIEZA:
        if columna not in datos.columns:
            continue
        datos[columna] = _normalizar_texto_basico(datos[columna]).str.title()
        datos.loc[datos[columna].eq(""), columna] = "No informado"
    return datos


def _convertir_columnas_numericas(df: pd.DataFrame, reporte: dict[str, Any]) -> pd.DataFrame:
    """Convierte columnas numericas con coercion y registra no convertibles."""
    datos = df.copy()
    for columna in COLUMNAS_NUMERICAS_LIMPIEZA:
        if columna not in datos.columns:
            continue
        original = datos[columna]
        texto = original.fillna("").astype(str).str.strip()
        convertida = pd.to_numeric(original, errors="coerce")
        no_convertibles = texto.ne("") & convertida.isna()
        reporte["valores_no_convertibles"][columna] = int(no_convertibles.sum())
        datos[columna] = convertida
    return datos


def _aplicar_rangos_validos(df: pd.DataFrame, reporte: dict[str, Any]) -> pd.DataFrame:
    """Convierte fuera de rango a NaN para posterior imputacion o eliminacion."""
    datos = df.copy()
    for columna, (minimo, maximo) in RANGOS_VALIDOS_LIMPIEZA.items():
        if columna not in datos.columns:
            continue
        serie = datos[columna]
        fuera_rango = pd.Series(False, index=datos.index)
        if minimo is not None:
            fuera_rango = fuera_rango | (serie < minimo)
        if maximo is not None:
            fuera_rango = fuera_rango | (serie > maximo)
        fuera_rango = fuera_rango & serie.notna()
        reporte["valores_fuera_de_rango"][columna] = int(fuera_rango.sum())
        datos.loc[fuera_rango, columna] = pd.NA
    return datos


def _eliminar_abandono_invalido(df: pd.DataFrame, reporte: dict[str, Any]) -> pd.DataFrame:
    """Elimina filas sin objetivo valido 0 o 1."""
    if TARGET_COLUMN not in df.columns:
        return df.copy()
    datos = df.copy()
    abandono_valido = datos[TARGET_COLUMN].isin([0, 1])
    reporte["abandono_invalido_eliminado"] = int((~abandono_valido).sum())
    return datos.loc[abandono_valido].copy()


def _imputar_numericos(df: pd.DataFrame, reporte: dict[str, Any]) -> pd.DataFrame:
    """Imputa faltantes numericos con mediana, cero o respaldo documentado."""
    datos = df.copy()
    for columna in COLUMNAS_MEDIANA:
        if columna not in datos.columns:
            continue
        faltantes = int(datos[columna].isna().sum())
        if faltantes == 0:
            reporte["valores_imputados"][columna] = 0
            continue
        mediana = datos[columna].dropna().median()
        if pd.isna(mediana):
            mediana = VALORES_RESPALDO_LIMPIEZA[columna]
            reporte["valores_respaldo_usados"][columna] = mediana
        datos[columna] = datos[columna].fillna(mediana)
        reporte["valores_imputados"][columna] = faltantes

    for columna in COLUMNAS_CERO:
        if columna not in datos.columns:
            continue
        faltantes = int(datos[columna].isna().sum())
        datos[columna] = datos[columna].fillna(0)
        reporte["valores_imputados"][columna] = faltantes
    return datos


def _aplicar_tipos_finales(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica tipos finales esperados para columnas numericas existentes."""
    datos = df.copy()
    for columna in COLUMNAS_ENTERAS:
        if columna in datos.columns:
            datos[columna] = datos[columna].round().astype("int64")
    if "monto_mensual" in datos.columns:
        datos["monto_mensual"] = datos["monto_mensual"].astype(float)
    if "satisfaccion" in datos.columns:
        datos["satisfaccion"] = datos["satisfaccion"].astype(float)
    return datos


def _crear_variables_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega variables descriptivas sin usar predicciones ni riesgo."""
    datos = df.copy()
    if "edad" in datos.columns:
        datos["grupo_edad"] = datos["edad"].apply(_grupo_edad)
    if "antiguedad_meses" in datos.columns:
        datos["grupo_antiguedad"] = datos["antiguedad_meses"].apply(_grupo_antiguedad)
    if "satisfaccion" in datos.columns:
        datos["nivel_satisfaccion"] = datos["satisfaccion"].apply(_nivel_satisfaccion)
    if "pagos_atrasados" in datos.columns:
        datos["tiene_morosidad"] = (datos["pagos_atrasados"] > 0).astype("int64")
    if "reclamos_ultimos_6_meses" in datos.columns:
        datos["tiene_reclamos"] = (datos["reclamos_ultimos_6_meses"] > 0).astype("int64")
    return datos


def _normalizar_texto_basico(serie: pd.Series) -> pd.Series:
    """Convierte a texto, elimina bordes y compacta espacios internos."""
    return serie.fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)


def _grupo_edad(valor: int) -> str:
    """Clasifica edad en grupos descriptivos."""
    if valor <= 29:
        return "18-29"
    if valor <= 44:
        return "30-44"
    if valor <= 59:
        return "45-59"
    return "60 o más"


def _grupo_antiguedad(valor: int) -> str:
    """Clasifica antiguedad en grupos descriptivos."""
    if valor <= 12:
        return "0-12 meses"
    if valor <= 24:
        return "13-24 meses"
    if valor <= 48:
        return "25-48 meses"
    return "49 meses o más"


def _nivel_satisfaccion(valor: float) -> str:
    """Clasifica satisfaccion en baja, media o alta."""
    if valor <= 2:
        return "Baja"
    if valor == 3:
        return "Media"
    return "Alta"
