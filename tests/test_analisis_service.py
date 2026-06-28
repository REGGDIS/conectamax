import pandas as pd

from services.analisis_service import (
    aplicar_filtros_analisis,
    calcular_abandono_por_categoria,
    calcular_clientes_abandonaron,
    calcular_clientes_permanecen,
    calcular_kpis,
    calcular_monto_mensual_promedio,
    calcular_reclamos_promedio,
    calcular_satisfaccion_promedio,
    calcular_tasa_abandono,
    calcular_tasa_retencion,
    calcular_total_clientes,
)


def dataframe_clientes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0001", "CXM0002", "CXM0003", "CXM0004"],
            "nombre": ["Ana Rojas", "Luis Paredes", "Carolina Vega", "Marcos Soto"],
            "ciudad": ["Santiago", "Valparaiso", "Santiago", "Temuco"],
            "antiguedad_meses": [36, 8, 18, 24],
            "tipo_contrato": ["Anual", "Mensual", "Mensual", "Bienal"],
            "plan": ["Hogar Total", "Basico", "Fibra Plus", "Fibra Plus"],
            "monto_mensual": [48990, 18990, 33990, 35990],
            "reclamos_ultimos_6_meses": [0, 2, 3, 1],
            "pagos_atrasados": [0, 1, 1, 0],
            "dias_sin_uso": [2, 14, 16, 5],
            "satisfaccion": [5, 3, 2, 4],
            "abandono": [0, 1, 1, 0],
            "edad": [34, 28, 44, 39],
            "cantidad_servicios": [4, 1, 3, 3],
        }
    )


def test_total_de_clientes() -> None:
    assert calcular_total_clientes(dataframe_clientes()) == 4


def test_clientes_que_permanecen() -> None:
    assert calcular_clientes_permanecen(dataframe_clientes()) == 2


def test_clientes_que_abandonaron() -> None:
    assert calcular_clientes_abandonaron(dataframe_clientes()) == 2


def test_tasa_de_abandono() -> None:
    assert calcular_tasa_abandono(dataframe_clientes()) == 50.0


def test_tasa_de_retencion() -> None:
    assert calcular_tasa_retencion(dataframe_clientes()) == 50.0


def test_satisfaccion_promedio() -> None:
    assert calcular_satisfaccion_promedio(dataframe_clientes()) == 3.5


def test_monto_mensual_promedio() -> None:
    assert calcular_monto_mensual_promedio(dataframe_clientes()) == 34490.0


def test_reclamos_promedio() -> None:
    assert calcular_reclamos_promedio(dataframe_clientes()) == 1.5


def test_calcular_kpis_incluye_indicadores_principales() -> None:
    kpis = calcular_kpis(dataframe_clientes())

    assert kpis["total_clientes"] == 4
    assert kpis["clientes_permanecen"] == 2
    assert kpis["clientes_abandonaron"] == 2
    assert kpis["tasa_abandono"] == 50.0


def test_abandono_por_ciudad() -> None:
    resultado = calcular_abandono_por_categoria(dataframe_clientes(), "ciudad")
    santiago = resultado[resultado["ciudad"] == "Santiago"].iloc[0]

    assert santiago["total_clientes"] == 2
    assert santiago["clientes_abandonaron"] == 1
    assert santiago["tasa_abandono"] == 50.0


def test_abandono_por_contrato() -> None:
    resultado = calcular_abandono_por_categoria(dataframe_clientes(), "tipo_contrato")
    mensual = resultado[resultado["tipo_contrato"] == "Mensual"].iloc[0]

    assert mensual["total_clientes"] == 2
    assert mensual["clientes_abandonaron"] == 2
    assert mensual["tasa_abandono"] == 100.0


def test_abandono_por_plan() -> None:
    resultado = calcular_abandono_por_categoria(dataframe_clientes(), "plan")
    fibra = resultado[resultado["plan"] == "Fibra Plus"].iloc[0]

    assert fibra["total_clientes"] == 2
    assert fibra["clientes_abandonaron"] == 1
    assert fibra["tasa_abandono"] == 50.0


def test_filtro_individual_por_ciudad() -> None:
    resultado = aplicar_filtros_analisis(dataframe_clientes(), ciudades=["Santiago"])

    assert resultado["id_cliente"].tolist() == ["CXM0001", "CXM0003"]


def test_filtro_individual_por_contrato() -> None:
    resultado = aplicar_filtros_analisis(dataframe_clientes(), tipos_contrato=["Mensual"])

    assert resultado["id_cliente"].tolist() == ["CXM0002", "CXM0003"]


def test_filtro_individual_por_plan() -> None:
    resultado = aplicar_filtros_analisis(dataframe_clientes(), planes=["Fibra Plus"])

    assert resultado["id_cliente"].tolist() == ["CXM0003", "CXM0004"]


def test_filtro_individual_por_abandono() -> None:
    resultado = aplicar_filtros_analisis(dataframe_clientes(), abandono=0)

    assert resultado["id_cliente"].tolist() == ["CXM0001", "CXM0004"]


def test_combinacion_de_filtros() -> None:
    resultado = aplicar_filtros_analisis(
        dataframe_clientes(),
        ciudades=["Santiago"],
        tipos_contrato=["Mensual"],
        planes=["Fibra Plus"],
        abandono=1,
    )

    assert resultado["id_cliente"].tolist() == ["CXM0003"]


def test_dataframe_vacio() -> None:
    df = pd.DataFrame()

    assert calcular_total_clientes(df) == 0
    assert calcular_tasa_abandono(df) == 0.0
    assert aplicar_filtros_analisis(df).empty
    assert calcular_abandono_por_categoria(df, "ciudad").empty


def test_dataframe_none() -> None:
    assert calcular_total_clientes(None) == 0
    assert calcular_tasa_retencion(None) == 0.0
    assert calcular_satisfaccion_promedio(None) == 0.0
    assert aplicar_filtros_analisis(None).empty


def test_ausencia_de_division_por_cero_con_abandono_no_valido() -> None:
    df = dataframe_clientes()
    df["abandono"] = [None, "x", None, "x"]

    assert calcular_tasa_abandono(df) == 0.0
    assert calcular_tasa_retencion(df) == 0.0
    assert calcular_abandono_por_categoria(df, "ciudad").empty


def test_convierte_valores_numericos_sin_modificar_original() -> None:
    df = dataframe_clientes()
    df["satisfaccion"] = ["5", "3", "2", "4"]
    original = df.copy(deep=True)

    assert calcular_satisfaccion_promedio(df) == 3.5
    pd.testing.assert_frame_equal(df, original)


def test_dataframe_original_no_se_modifica_al_filtrar() -> None:
    df = dataframe_clientes()
    original = df.copy(deep=True)

    resultado = aplicar_filtros_analisis(df, ciudades=["Santiago"])
    resultado.loc[:, "ciudad"] = "Modificada"

    pd.testing.assert_frame_equal(df, original)


def test_columna_de_agrupacion_no_permitida_devuelve_vacio() -> None:
    resultado = calcular_abandono_por_categoria(dataframe_clientes(), "nombre")

    assert resultado.empty
