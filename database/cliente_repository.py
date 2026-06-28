"""Repositorio provisional de clientes para infraestructura SQLite."""

from typing import Any
import sqlite3


def insertar_cliente(conexion: sqlite3.Connection, cliente: dict[str, Any]) -> None:
    """Inserta un cliente en la tabla provisional usando parametros SQL."""
    conexion.execute(
        """
        INSERT INTO clientes_prueba (
            id_cliente,
            nombre,
            ciudad,
            tipo_contrato,
            plan,
            abandono
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            cliente["id_cliente"],
            cliente["nombre"],
            cliente["ciudad"],
            cliente["tipo_contrato"],
            cliente["plan"],
            cliente["abandono"],
        ),
    )
    conexion.commit()


def obtener_todos_clientes(conexion: sqlite3.Connection) -> list[dict[str, Any]]:
    """Obtiene todos los clientes de la tabla provisional como diccionarios."""
    filas = conexion.execute(
        """
        SELECT id_cliente, nombre, ciudad, tipo_contrato, plan, abandono
        FROM clientes_prueba
        ORDER BY id_cliente;
        """
    ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_cliente_por_id(
    conexion: sqlite3.Connection,
    id_cliente: str,
) -> dict[str, Any] | None:
    """Obtiene un cliente por identificador o None si no existe."""
    fila = conexion.execute(
        """
        SELECT id_cliente, nombre, ciudad, tipo_contrato, plan, abandono
        FROM clientes_prueba
        WHERE id_cliente = ?;
        """,
        (id_cliente,),
    ).fetchone()
    if fila is None:
        return None
    return dict(fila)


def contar_clientes(conexion: sqlite3.Connection) -> int:
    """Cuenta clientes disponibles en la tabla provisional."""
    fila = conexion.execute("SELECT COUNT(*) AS total FROM clientes_prueba;").fetchone()
    if fila is None:
        return 0
    return int(fila["total"])
