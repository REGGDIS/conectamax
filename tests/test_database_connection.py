import sqlite3

from database.connection import cerrar_conexion, obtener_conexion, verificar_conexion


def test_crea_base_temporal(tmp_path) -> None:
    ruta = tmp_path / "db" / "temporal.db"

    conexion = obtener_conexion(ruta)
    cerrar_conexion(conexion)

    assert ruta.exists()


def test_verifica_conexion_valida(tmp_path) -> None:
    ruta = tmp_path / "temporal.db"

    assert verificar_conexion(ruta) is True


def test_configura_row_factory(tmp_path) -> None:
    conexion = obtener_conexion(tmp_path / "temporal.db")

    fila = conexion.execute("SELECT 1 AS valor;").fetchone()
    cerrar_conexion(conexion)

    assert isinstance(fila, sqlite3.Row)
    assert fila["valor"] == 1


def test_activa_claves_foraneas(tmp_path) -> None:
    conexion = obtener_conexion(tmp_path / "temporal.db")

    fila = conexion.execute("PRAGMA foreign_keys;").fetchone()
    cerrar_conexion(conexion)

    assert fila[0] == 1


def test_cierre_controlado_con_none() -> None:
    cerrar_conexion(None)


def test_cierre_controlado_permite_cerrar_conexion(tmp_path) -> None:
    conexion = obtener_conexion(tmp_path / "temporal.db")

    cerrar_conexion(conexion)
    cerrar_conexion(conexion)


def test_crea_directorio_padre(tmp_path) -> None:
    ruta = tmp_path / "subdir" / "nested" / "temporal.db"

    conexion = obtener_conexion(ruta)
    cerrar_conexion(conexion)

    assert ruta.parent.exists()


def test_no_usa_base_real_del_proyecto(tmp_path) -> None:
    ruta = tmp_path / "aislada.db"

    conexion = obtener_conexion(ruta)
    cerrar_conexion(conexion)
    assert "conectamax.db" not in str(ruta)
