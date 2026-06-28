"""Servicio para consulta, busqueda y filtrado de clientes."""

from typing import Any

import pandas as pd

from config.settings import (
    COLUMNAS_ORDEN_CLIENTES,
    ETIQUETAS_ABANDONO,
    ID_COLUMN,
    TARGET_COLUMN,
)


def normalizar_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    """Devuelve una copia segura del DataFrame o uno vacio si no hay datos."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.copy()


def buscar_clientes(df: pd.DataFrame | None, termino: str) -> pd.DataFrame:
    """Busca coincidencias parciales en identificador y nombre, sin distinguir mayusculas."""
    datos = normalizar_dataframe(df)
    termino_limpio = str(termino or "").strip()
    if datos.empty or not termino_limpio:
        return datos

    columnas_busqueda = [col for col in [ID_COLUMN, "nombre"] if col in datos.columns]
    if not columnas_busqueda:
        return datos.iloc[0:0].copy()

    mascara = pd.Series(False, index=datos.index)
    for columna in columnas_busqueda:
        mascara = mascara | datos[columna].astype(str).str.contains(
            termino_limpio,
            case=False,
            na=False,
            regex=False,
        )
    return datos.loc[mascara].copy()


def filtrar_clientes(
    df: pd.DataFrame | None,
    termino: str = "",
    ciudades: list[str] | None = None,
    tipos_contrato: list[str] | None = None,
    planes: list[str] | None = None,
    abandono: int | None = None,
) -> pd.DataFrame:
    """Combina busqueda por texto y filtros multiples sobre clientes."""
    datos = buscar_clientes(df, termino)
    if datos.empty:
        return datos

    datos = _filtrar_por_opciones(datos, "ciudad", ciudades)
    datos = _filtrar_por_opciones(datos, "tipo_contrato", tipos_contrato)
    datos = _filtrar_por_opciones(datos, "plan", planes)

    if abandono is not None and TARGET_COLUMN in datos.columns:
        abandono_numerico = pd.to_numeric(datos[TARGET_COLUMN], errors="coerce")
        datos = datos.loc[abandono_numerico == abandono].copy()

    return datos.copy()


def obtener_cliente_por_id(df: pd.DataFrame | None, id_cliente: str) -> dict[str, Any] | None:
    """Obtiene el primer cliente que coincide exactamente con el identificador."""
    datos = normalizar_dataframe(df)
    id_limpio = str(id_cliente or "").strip()
    if datos.empty or not id_limpio or ID_COLUMN not in datos.columns:
        return None

    coincidencias = datos[datos[ID_COLUMN].astype(str).str.strip() == id_limpio]
    if coincidencias.empty:
        return None
    return coincidencias.iloc[0].to_dict()


def obtener_opciones_filtro(df: pd.DataFrame | None, columna: str) -> list[str]:
    """Obtiene valores unicos no vacios ordenados para una columna."""
    datos = normalizar_dataframe(df)
    if datos.empty or columna not in datos.columns:
        return []

    serie = datos[columna].dropna().astype(str).str.strip()
    valores = [valor for valor in serie.unique().tolist() if valor]
    return sorted(valores, key=str.casefold)


def contar_resultados(df: pd.DataFrame | None) -> int:
    """Cuenta filas disponibles en un DataFrame de resultados."""
    if df is None:
        return 0
    return int(len(df))


def ordenar_clientes(
    df: pd.DataFrame | None,
    columna: str,
    ascendente: bool = True,
) -> pd.DataFrame:
    """Ordena clientes solo por columnas permitidas."""
    datos = normalizar_dataframe(df)
    if datos.empty or columna not in COLUMNAS_ORDEN_CLIENTES or columna not in datos.columns:
        return datos
    return datos.sort_values(by=columna, ascending=ascendente, kind="mergesort").copy()


def preparar_tabla_clientes(df: pd.DataFrame | None, columnas: list[str]) -> pd.DataFrame:
    """Prepara una copia para visualizacion con estado de abandono legible."""
    datos = normalizar_dataframe(df)
    columnas_existentes = [col for col in columnas if col in datos.columns]
    tabla = datos.loc[:, columnas_existentes].copy() if columnas_existentes else pd.DataFrame()
    if TARGET_COLUMN in tabla.columns:
        tabla[TARGET_COLUMN] = tabla[TARGET_COLUMN].map(_formatear_abandono)
    return tabla


def formatear_abandono(valor: Any) -> str:
    """Convierte el valor de abandono a una etiqueta comprensible."""
    return _formatear_abandono(valor)


def _filtrar_por_opciones(
    df: pd.DataFrame,
    columna: str,
    opciones: list[str] | None,
) -> pd.DataFrame:
    """Aplica un filtro por lista de opciones si la columna existe."""
    if not opciones or columna not in df.columns:
        return df.copy()
    opciones_limpias = {str(opcion).strip() for opcion in opciones if str(opcion).strip()}
    if not opciones_limpias:
        return df.copy()
    serie = df[columna].astype(str).str.strip()
    return df.loc[serie.isin(opciones_limpias)].copy()


def _formatear_abandono(valor: Any) -> str:
    """Devuelve etiqueta de abandono o el valor original como texto."""
    valor_numerico = pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0]
    if pd.isna(valor_numerico):
        return str(valor)
    return ETIQUETAS_ABANDONO.get(int(valor_numerico), str(valor))
