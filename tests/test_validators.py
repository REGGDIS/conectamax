import pandas as pd

from utils.validators import validar_dataframe


def dataframe_valido() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0001", "CXM0002"],
            "nombre": ["Ana Rojas", "Luis Paredes"],
            "ciudad": ["Santiago", "Valparaiso"],
            "antiguedad_meses": [24, 8],
            "tipo_contrato": ["Anual", "Mensual"],
            "plan": ["Fibra Plus", "Basico"],
            "monto_mensual": [32990, 18990],
            "reclamos_ultimos_6_meses": [0, 2],
            "pagos_atrasados": [0, 1],
            "dias_sin_uso": [2, 14],
            "satisfaccion": [5, 3],
            "abandono": [0, 1],
            "edad": [34, 28],
            "cantidad_servicios": [3, 1],
        }
    )


def test_dataframe_valido() -> None:
    resultado = validar_dataframe(dataframe_valido())

    assert resultado["es_valido"] is True
    assert resultado["errores"] == []
    assert resultado["advertencias"] == []


def test_dataframe_vacio_es_invalido() -> None:
    resultado = validar_dataframe(pd.DataFrame())

    assert resultado["es_valido"] is False
    assert resultado["errores"]


def test_columnas_obligatorias_faltantes() -> None:
    df = dataframe_valido().drop(columns=["nombre", "ciudad"])

    resultado = validar_dataframe(df)

    assert resultado["es_valido"] is False
    assert any("Faltan columnas obligatorias" in error for error in resultado["errores"])


def test_identificadores_duplicados_generan_advertencia() -> None:
    df = dataframe_valido()
    df.loc[1, "id_cliente"] = "CXM0001"

    resultado = validar_dataframe(df)

    assert resultado["es_valido"] is True
    assert resultado["resumen"]["duplicados_id"] == 1
    assert any("duplicados" in advertencia for advertencia in resultado["advertencias"])


def test_valores_faltantes_generan_advertencia() -> None:
    df = dataframe_valido()
    df.loc[0, "nombre"] = None

    resultado = validar_dataframe(df)

    assert resultado["es_valido"] is True
    assert resultado["resumen"]["valores_faltantes_por_columna"]["nombre"] == 1
    assert any("faltantes" in advertencia for advertencia in resultado["advertencias"])


def test_abandono_con_valores_invalidos() -> None:
    df = dataframe_valido()
    df.loc[0, "abandono"] = 2

    resultado = validar_dataframe(df)

    assert resultado["es_valido"] is True
    assert any("distintos de 0 y 1" in advertencia for advertencia in resultado["advertencias"])


def test_satisfaccion_fuera_de_rango() -> None:
    df = dataframe_valido()
    df.loc[0, "satisfaccion"] = 6

    resultado = validar_dataframe(df)

    assert resultado["es_valido"] is True
    assert any("rango 1 a 5" in advertencia for advertencia in resultado["advertencias"])
