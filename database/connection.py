"""Conexion desacoplada a SQLite para infraestructura futura."""

from pathlib import Path
import sqlite3

from config.settings import DATABASE_PATH


def obtener_conexion(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Obtiene una conexion SQLite configurada para la ruta indicada o la ruta central."""
    ruta = Path(database_path) if database_path is not None else DATABASE_PATH
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(ruta)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON;")
        return conexion
    except sqlite3.Error as exc:
        raise RuntimeError(f"No fue posible abrir la conexion SQLite: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"No fue posible preparar la ruta de SQLite: {exc}") from exc


def verificar_conexion(database_path: str | Path | None = None) -> bool:
    """Verifica si es posible abrir y consultar una conexion SQLite."""
    conexion: sqlite3.Connection | None = None
    try:
        conexion = obtener_conexion(database_path)
        conexion.execute("SELECT 1;").fetchone()
        return True
    except (RuntimeError, sqlite3.Error):
        return False
    finally:
        cerrar_conexion(conexion)


def cerrar_conexion(conexion: sqlite3.Connection | None) -> None:
    """Cierra una conexion SQLite si existe, ignorando cierres repetidos."""
    if conexion is None:
        return
    try:
        conexion.close()
    except sqlite3.Error:
        return
