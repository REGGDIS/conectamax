"""Repositorio SQLite para la vista de comportamiento de clientes."""

from pathlib import Path
import sqlite3

import pandas as pd

from config.settings import COLUMNAS_OBLIGATORIAS, DATABASE_PATH, VISTA_COMPORTAMIENTO_CLIENTE
from database.connection import cerrar_conexion, obtener_conexion


def obtener_comportamiento_clientes(
    database_path: str | Path | None = None,
) -> pd.DataFrame:
    """Obtiene clientes desde la vista analitica de SQLite."""
    ruta = _resolver_ruta(database_path)
    conexion = None
    try:
        conexion = obtener_conexion(ruta)
        consulta = f"""
            SELECT *
            FROM {VISTA_COMPORTAMIENTO_CLIENTE}
            ORDER BY id_cliente
        """
        df = pd.read_sql_query(consulta, conexion)
    except sqlite3.OperationalError as exc:
        raise RuntimeError(_mensaje_error_sqlite(exc)) from exc
    except sqlite3.Error as exc:
        raise RuntimeError(f"No fue posible consultar la vista de clientes: {exc}") from exc
    except pd.errors.DatabaseError as exc:
        raise RuntimeError(_mensaje_error_pandas(exc)) from exc
    finally:
        cerrar_conexion(conexion)

    _validar_columnas_obligatorias(df)
    return df.copy()


def _resolver_ruta(database_path: str | Path | None) -> Path:
    """Resuelve y valida la ruta sin crear una base SQLite vacia."""
    ruta = Path(database_path) if database_path is not None else DATABASE_PATH
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontro la base de datos SQLite: {ruta}")
    if not ruta.is_file():
        raise FileNotFoundError(f"La ruta SQLite no corresponde a un archivo: {ruta}")
    return ruta


def _validar_columnas_obligatorias(df: pd.DataFrame) -> None:
    """Valida el contrato minimo requerido por las vistas."""
    faltantes = [columna for columna in COLUMNAS_OBLIGATORIAS if columna not in df.columns]
    if faltantes:
        detalle = ", ".join(faltantes)
        raise RuntimeError(f"La vista de clientes no contiene columnas obligatorias: {detalle}")


def _mensaje_error_sqlite(exc: sqlite3.OperationalError) -> str:
    """Traduce errores SQLite frecuentes a mensajes de dominio."""
    mensaje = str(exc)
    if "no such table" in mensaje or "no such view" in mensaje:
        return f"No existe la vista SQLite requerida: {VISTA_COMPORTAMIENTO_CLIENTE}"
    return f"No fue posible consultar la vista de clientes: {mensaje}"


def _mensaje_error_pandas(exc: pd.errors.DatabaseError) -> str:
    """Traduce errores propagados por pandas.read_sql_query."""
    mensaje = str(exc)
    if "no such table" in mensaje or "no such view" in mensaje:
        return f"No existe la vista SQLite requerida: {VISTA_COMPORTAMIENTO_CLIENTE}"
    return f"No fue posible consultar la vista de clientes: {mensaje}"
