"""Modelos provisionales para pruebas de infraestructura SQLite."""

import sqlite3


def crear_tabla_clientes_prueba(conexion: sqlite3.Connection) -> None:
    """Crea una tabla minima y provisional solo para pruebas de infraestructura."""
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes_prueba (
            id_cliente TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            ciudad TEXT NOT NULL,
            tipo_contrato TEXT NOT NULL,
            plan TEXT NOT NULL,
            abandono INTEGER NOT NULL
        );
        """
    )
    conexion.commit()
