import pandas as pd
import pytest

from views.analisis_view import formatear_etiqueta_variable, preparar_datos_boxplot


def dataframe_clientes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0001", "CXM0002", "CXM0003", "CXM0004"],
            "satisfaccion": [5, 3, 2, 4],
            "reclamos_ultimos_6_meses": [0, 2, 3, 1],
            "pagos_atrasados": [0, 1, 1, 0],
            "dias_sin_uso": [2, 14, 16, 5],
            "monto_mensual": [48990, 18990, 33990, 35990],
            "antiguedad_meses": [36, 8, 18, 24],
            "abandono": [0, 1, 1, 0],
        }
    )


def test_preparar_datos_boxplot_normal() -> None:
    resultado = preparar_datos_boxplot(dataframe_clientes(), "satisfaccion")

    assert resultado.columns.tolist() == ["estado_abandono", "satisfaccion"]
    assert resultado["estado_abandono"].tolist() == ["Permanece", "Abandonó", "Abandonó", "Permanece"]
    assert resultado["satisfaccion"].tolist() == [5, 3, 2, 4]


def test_preparar_datos_boxplot_variable_faltante() -> None:
    df = dataframe_clientes().drop(columns=["dias_sin_uso"])

    with pytest.raises(ValueError, match="dias_sin_uso"):
        preparar_datos_boxplot(df, "dias_sin_uso")


def test_preparar_datos_boxplot_abandono_faltante() -> None:
    df = dataframe_clientes().drop(columns=["abandono"])

    with pytest.raises(ValueError, match="abandono"):
        preparar_datos_boxplot(df, "satisfaccion")


def test_preparar_datos_boxplot_conversion_numerica() -> None:
    df = dataframe_clientes()
    df["monto_mensual"] = ["48990", "no valido", "33990", "35990"]

    resultado = preparar_datos_boxplot(df, "monto_mensual")

    assert resultado["monto_mensual"].tolist() == [48990.0, 33990.0, 35990.0]
    assert resultado["estado_abandono"].tolist() == ["Permanece", "Abandonó", "Permanece"]


def test_preparar_datos_boxplot_dataframe_vacio() -> None:
    resultado = preparar_datos_boxplot(pd.DataFrame(), "satisfaccion")

    assert resultado.empty
    assert resultado.columns.tolist() == ["estado_abandono", "satisfaccion"]


def test_preparar_datos_boxplot_no_modifica_original() -> None:
    df = dataframe_clientes()
    df["satisfaccion"] = ["5", "3", "2", "4"]
    original = df.copy(deep=True)

    preparar_datos_boxplot(df, "satisfaccion")

    pd.testing.assert_frame_equal(df, original)


def test_formatear_etiqueta_variable() -> None:
    assert formatear_etiqueta_variable("dias_sin_uso") == "Días sin uso"
    assert formatear_etiqueta_variable("columna_desconocida") == "columna_desconocida"
