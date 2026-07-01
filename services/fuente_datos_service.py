"""Servicio comun para cargar clientes desde SQLite."""

from pathlib import Path

import pandas as pd

try:
    import streamlit as st
except ModuleNotFoundError:
    st = None

from config.settings import COLUMNAS_NUMERICAS, DATABASE_PATH
from repositories.comportamiento_repository import obtener_comportamiento_clientes


def cargar_clientes_desde_sqlite(
    database_path: str | Path | None = None,
) -> pd.DataFrame:
    """Carga clientes desde SQLite y normaliza tipos numericos sin limpiar filas."""
    ruta = _resolver_ruta(database_path)
    mtime = _obtener_mtime(ruta)
    df = _cargar_clientes_cacheados(str(ruta), mtime)
    return _normalizar_tipos_numericos(df.copy())


def _cache_data(func=None, **kwargs):
    """Usa cache de Streamlit si esta disponible; en tests puros queda neutro."""
    _ = kwargs
    if st is not None:
        return st.cache_data(show_spinner=False)(func) if func is not None else st.cache_data(show_spinner=False)

    def decorar(funcion):
        funcion.clear = lambda: None
        return funcion

    return decorar(func) if func is not None else decorar


@_cache_data
def _cargar_clientes_cacheados(database_path: str, database_mtime: float) -> pd.DataFrame:
    """Carga cacheada; mtime invalida resultados cuando cambia la base."""
    _ = database_mtime
    return obtener_comportamiento_clientes(database_path).copy()


def _normalizar_tipos_numericos(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas numericas presentes con coercion segura."""
    datos = df.copy()
    for columna in COLUMNAS_NUMERICAS:
        if columna in datos.columns:
            datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
    return datos


def _resolver_ruta(database_path: str | Path | None) -> Path:
    return Path(database_path) if database_path is not None else DATABASE_PATH


def _obtener_mtime(database_path: Path) -> float:
    if not database_path.exists():
        raise FileNotFoundError(f"No se encontro la base de datos SQLite: {database_path}")
    return database_path.stat().st_mtime
