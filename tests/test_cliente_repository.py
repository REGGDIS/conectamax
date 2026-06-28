from database.cliente_repository import (
    contar_clientes,
    insertar_cliente,
    obtener_cliente_por_id,
    obtener_todos_clientes,
)
from database.connection import cerrar_conexion, obtener_conexion
from database.models import crear_tabla_clientes_prueba


def cliente_base(id_cliente: str = "CXM0001") -> dict:
    return {
        "id_cliente": id_cliente,
        "nombre": "Ana Rojas",
        "ciudad": "Santiago",
        "tipo_contrato": "Anual",
        "plan": "Fibra Plus",
        "abandono": 0,
    }


def conexion_temporal(tmp_path):
    conexion = obtener_conexion(tmp_path / "clientes.db")
    crear_tabla_clientes_prueba(conexion)
    return conexion


def test_inserta_cliente(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)

    insertar_cliente(conexion, cliente_base())

    assert contar_clientes(conexion) == 1
    cerrar_conexion(conexion)


def test_obtiene_todos_los_clientes(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)
    insertar_cliente(conexion, cliente_base("CXM0001"))
    insertar_cliente(conexion, cliente_base("CXM0002"))

    clientes = obtener_todos_clientes(conexion)
    cerrar_conexion(conexion)

    assert [cliente["id_cliente"] for cliente in clientes] == ["CXM0001", "CXM0002"]


def test_obtiene_cliente_por_id(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)
    insertar_cliente(conexion, cliente_base())

    cliente = obtener_cliente_por_id(conexion, "CXM0001")
    cerrar_conexion(conexion)

    assert cliente is not None
    assert cliente["nombre"] == "Ana Rojas"


def test_cliente_inexistente_devuelve_none(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)

    cliente = obtener_cliente_por_id(conexion, "NO_EXISTE")
    cerrar_conexion(conexion)

    assert cliente is None


def test_cuenta_clientes(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)
    insertar_cliente(conexion, cliente_base("CXM0001"))
    insertar_cliente(conexion, cliente_base("CXM0002"))
    insertar_cliente(conexion, cliente_base("CXM0003"))

    total = contar_clientes(conexion)
    cerrar_conexion(conexion)

    assert total == 3


def test_inserta_varios_clientes(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)
    for indice in range(1, 4):
        insertar_cliente(conexion, cliente_base(f"CXM000{indice}"))

    clientes = obtener_todos_clientes(conexion)
    cerrar_conexion(conexion)

    assert len(clientes) == 3


def test_pruebas_independientes_usan_base_temporal(tmp_path) -> None:
    conexion = conexion_temporal(tmp_path)

    assert contar_clientes(conexion) == 0
    cerrar_conexion(conexion)


def test_no_depende_de_base_real_del_proyecto(tmp_path) -> None:
    ruta = tmp_path / "repositorio.db"
    conexion = obtener_conexion(ruta)
    crear_tabla_clientes_prueba(conexion)
    insertar_cliente(conexion, cliente_base())

    assert ruta.exists()
    assert "conectamax.db" not in str(ruta)
    assert contar_clientes(conexion) == 1
    cerrar_conexion(conexion)
