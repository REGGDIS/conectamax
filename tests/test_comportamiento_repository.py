from contextlib import closing
import sqlite3

import pandas as pd
import pytest

from config.settings import COLUMNAS_OBLIGATORIAS, VISTA_COMPORTAMIENTO_CLIENTE
from repositories.comportamiento_repository import obtener_comportamiento_clientes


COLUMNAS_SQL = [
    "id_cliente TEXT",
    "nombre TEXT",
    "ciudad TEXT",
    "antiguedad_meses INTEGER",
    "tipo_contrato TEXT",
    "plan TEXT",
    "monto_mensual REAL",
    "reclamos_ultimos_6_meses INTEGER",
    "pagos_atrasados INTEGER",
    "dias_sin_uso INTEGER",
    "satisfaccion INTEGER",
    "abandono INTEGER",
    "edad INTEGER",
    "cantidad_servicios INTEGER",
    "region TEXT",
    "segmento TEXT",
]


def crear_base(tmp_path, filas: list[tuple] | None = None, columnas: list[str] | None = None):
    ruta = tmp_path / "clientes.db"
    columnas = columnas or COLUMNAS_SQL
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.execute(f"CREATE TABLE datos ({', '.join(columnas)});")
        if filas:
            nombres = [columna.split()[0] for columna in columnas]
            placeholders = ", ".join(["?"] * len(nombres))
            conexion.executemany(
                f"INSERT INTO datos ({', '.join(nombres)}) VALUES ({placeholders});",
                filas,
            )
        conexion.execute(f"CREATE VIEW {VISTA_COMPORTAMIENTO_CLIENTE} AS SELECT * FROM datos;")
        conexion.commit()
    return ruta


def filas_base() -> list[tuple]:
    return [
        (
            "CXM0002",
            "Luis Paredes",
            "Valparaiso",
            8,
            "Mensual",
            "Basico",
            18990,
            2,
            1,
            14,
            3,
            1,
            28,
            1,
            "Valparaiso",
            "Residencial",
        ),
        (
            "CXM0001",
            "Ana Rojas",
            "Santiago",
            36,
            "Anual",
            "Hogar Total",
            48990,
            0,
            0,
            2,
            5,
            0,
            34,
            4,
            "Metropolitana",
            "Premium",
        ),
    ]


def test_devuelve_dataframe_con_datos(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())

    df = obtener_comportamiento_clientes(ruta)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_devuelve_filas_ordenadas_por_id_cliente(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())

    df = obtener_comportamiento_clientes(ruta)

    assert df["id_cliente"].tolist() == ["CXM0001", "CXM0002"]


def test_conserva_columnas_obligatorias(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())


    df = obtener_comportamiento_clientes(ruta)

    assert set(COLUMNAS_OBLIGATORIAS).issubset(df.columns)


def test_conserva_columnas_adicionales(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())


    df = obtener_comportamiento_clientes(ruta)
    assert {"region", "segmento"}.issubset(df.columns)


def test_acepta_ruta_personalizada(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())


    df = obtener_comportamiento_clientes(str(ruta))
    assert df["id_cliente"].tolist() == ["CXM0001", "CXM0002"]


def test_base_inexistente_lanza_file_not_found(tmp_path) -> None:
    ruta = tmp_path / "no_existe.db"


    with pytest.raises(FileNotFoundError, match="No se encontro la base de datos SQLite"):
        obtener_comportamiento_clientes(ruta)


def test_vista_inexistente_lanza_runtime_error(tmp_path) -> None:
    ruta = tmp_path / "sin_vista.db"
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.execute("CREATE TABLE datos (id_cliente TEXT);")
        conexion.commit()

    with pytest.raises(RuntimeError, match="No existe la vista SQLite requerida"):
        obtener_comportamiento_clientes(ruta)


def test_vista_vacia_devuelve_dataframe_vacio_con_columnas(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas=[])

    df = obtener_comportamiento_clientes(ruta)

    assert df.empty
    assert set(COLUMNAS_OBLIGATORIAS).issubset(df.columns)


def test_vista_con_columnas_faltantes_lanza_runtime_error(tmp_path) -> None:
    ruta = crear_base(tmp_path, columnas=["id_cliente TEXT", "nombre TEXT"])

    with pytest.raises(RuntimeError, match="columnas obligatorias"):
        obtener_comportamiento_clientes(ruta)


def test_la_conexion_queda_cerrada_al_terminar(tmp_path) -> None:
    ruta = crear_base(tmp_path, filas_base())

    obtener_comportamiento_clientes(ruta)
    ruta.unlink()

    assert not ruta.exists()


def test_no_crea_archivo_sqlite_si_la_ruta_no_existe(tmp_path) -> None:
    ruta = tmp_path / "no_crear.db"

    with pytest.raises(FileNotFoundError):
        obtener_comportamiento_clientes(ruta)

    assert not ruta.exists()
