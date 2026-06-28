import pandas as pd

from services.cliente_service import (
    buscar_clientes,
    filtrar_clientes,
    obtener_cliente_por_id,
    obtener_opciones_filtro,
    ordenar_clientes,
)


def dataframe_clientes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0003", "CXM0001", "CXM0002", "CXM0004"],
            "nombre": ["Carolina Vega", "Ana Rojas", "Luis Paredes", "Marcos Soto"],
            "ciudad": ["Santiago", "Santiago", "Valparaiso", "Temuco"],
            "antiguedad_meses": [18, 36, 8, 24],
            "tipo_contrato": ["Mensual", "Anual", "Mensual", "Bienal"],
            "plan": ["Fibra Plus", "Hogar Total", "Basico", "Fibra Plus"],
            "monto_mensual": [33990, 48990, 18990, 35990],
            "reclamos_ultimos_6_meses": [3, 0, 2, 1],
            "pagos_atrasados": [1, 0, 1, 0],
            "dias_sin_uso": [16, 2, 14, 5],
            "satisfaccion": [2, 5, 3, 4],
            "abandono": [1, 0, 1, 0],
            "edad": [44, 34, 28, 39],
            "cantidad_servicios": [3, 4, 1, 3],
        }
    )


def test_busqueda_por_nombre() -> None:
    resultado = buscar_clientes(dataframe_clientes(), "Ana")

    assert resultado["id_cliente"].tolist() == ["CXM0001"]


def test_busqueda_por_identificador() -> None:
    resultado = buscar_clientes(dataframe_clientes(), "CXM0002")

    assert resultado["nombre"].tolist() == ["Luis Paredes"]


def test_busqueda_sin_distinguir_mayusculas() -> None:
    resultado = buscar_clientes(dataframe_clientes(), "carolina")

    assert resultado["id_cliente"].tolist() == ["CXM0003"]


def test_busqueda_con_coincidencia_parcial() -> None:
    resultado = buscar_clientes(dataframe_clientes(), "CXM000")

    assert len(resultado) == 4


def test_filtro_por_ciudad() -> None:
    resultado = filtrar_clientes(dataframe_clientes(), ciudades=["Santiago"])

    assert resultado["id_cliente"].tolist() == ["CXM0003", "CXM0001"]


def test_filtro_por_tipo_contrato() -> None:
    resultado = filtrar_clientes(dataframe_clientes(), tipos_contrato=["Mensual"])

    assert resultado["id_cliente"].tolist() == ["CXM0003", "CXM0002"]


def test_filtro_por_plan() -> None:
    resultado = filtrar_clientes(dataframe_clientes(), planes=["Fibra Plus"])

    assert resultado["id_cliente"].tolist() == ["CXM0003", "CXM0004"]


def test_filtro_por_abandono() -> None:
    resultado = filtrar_clientes(dataframe_clientes(), abandono=0)

    assert resultado["id_cliente"].tolist() == ["CXM0001", "CXM0004"]


def test_combinacion_de_busqueda_y_filtros() -> None:
    resultado = filtrar_clientes(
        dataframe_clientes(),
        termino="vega",
        ciudades=["Santiago"],
        tipos_contrato=["Mensual"],
        planes=["Fibra Plus"],
        abandono=1,
    )

    assert resultado["id_cliente"].tolist() == ["CXM0003"]


def test_obtener_cliente_por_id() -> None:
    cliente = obtener_cliente_por_id(dataframe_clientes(), "CXM0001")

    assert cliente is not None
    assert cliente["nombre"] == "Ana Rojas"


def test_cliente_inexistente() -> None:
    cliente = obtener_cliente_por_id(dataframe_clientes(), "NO_EXISTE")

    assert cliente is None


def test_dataframe_vacio() -> None:
    resultado = filtrar_clientes(pd.DataFrame(), termino="Ana")

    assert resultado.empty


def test_lista_de_opciones_unicas_ordenadas() -> None:
    opciones = obtener_opciones_filtro(dataframe_clientes(), "ciudad")

    assert opciones == ["Santiago", "Temuco", "Valparaiso"]


def test_ordenamiento_ascendente() -> None:
    resultado = ordenar_clientes(dataframe_clientes(), "monto_mensual", ascendente=True)

    assert resultado["id_cliente"].tolist() == ["CXM0002", "CXM0003", "CXM0004", "CXM0001"]


def test_ordenamiento_descendente() -> None:
    resultado = ordenar_clientes(dataframe_clientes(), "satisfaccion", ascendente=False)

    assert resultado["id_cliente"].tolist() == ["CXM0001", "CXM0004", "CXM0002", "CXM0003"]


def test_dataframe_original_no_se_modifica() -> None:
    df = dataframe_clientes()
    original = df.copy(deep=True)

    resultado = filtrar_clientes(df, ciudades=["Santiago"])
    resultado.loc[:, "ciudad"] = "Modificada"

    pd.testing.assert_frame_equal(df, original)
