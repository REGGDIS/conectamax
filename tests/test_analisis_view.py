import pandas as pd
import pytest

from views.analisis_view import (
    calcular_correlaciones_abandono,
    formatear_etiqueta_variable,
    preparar_datos_boxplot,
    preparar_matriz_correlacion,
)


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


def test_preparar_matriz_correlacion_valida() -> None:
    matriz = preparar_matriz_correlacion(dataframe_clientes())

    assert "abandono" in matriz.columns
    assert "satisfaccion" in matriz.columns
    assert matriz.loc["satisfaccion", "abandono"] == pytest.approx(-0.894427, rel=1e-5)


def test_preparar_matriz_correlacion_convierte_textos_numericos() -> None:
    df = dataframe_clientes()
    df["satisfaccion"] = ["5", "3", "2", "4"]

    matriz = preparar_matriz_correlacion(df)

    assert matriz.loc["satisfaccion", "satisfaccion"] == 1.0
    assert matriz.loc["satisfaccion", "abandono"] == pytest.approx(-0.894427, rel=1e-5)


def test_preparar_matriz_correlacion_columnas_faltantes() -> None:
    df = dataframe_clientes().loc[:, ["satisfaccion", "abandono"]]

    matriz = preparar_matriz_correlacion(df)

    assert matriz.columns.tolist() == ["satisfaccion", "abandono"]
    assert matriz.index.tolist() == ["satisfaccion", "abandono"]


def test_preparar_matriz_correlacion_excluye_columnas_completamente_invalidas() -> None:
    df = dataframe_clientes()
    df["monto_mensual"] = ["x", "y", "z", "w"]

    matriz = preparar_matriz_correlacion(df)

    assert "monto_mensual" not in matriz.columns
    assert "satisfaccion" in matriz.columns


def test_preparar_matriz_correlacion_dataframe_vacio() -> None:
    with pytest.raises(ValueError, match="No hay datos"):
        preparar_matriz_correlacion(pd.DataFrame())


def test_preparar_matriz_correlacion_dataframe_none() -> None:
    with pytest.raises(ValueError, match="No se recibieron datos"):
        preparar_matriz_correlacion(None)


def test_preparar_matriz_correlacion_menos_de_2_variables_validas() -> None:
    df = pd.DataFrame({"satisfaccion": ["x", "y"], "abandono": [0, 1]})

    with pytest.raises(ValueError, match="2 variables numéricas válidas"):
        preparar_matriz_correlacion(df)


def test_preparar_matriz_correlacion_no_modifica_original() -> None:
    df = dataframe_clientes()
    df["satisfaccion"] = ["5", "3", "2", "4"]
    original = df.copy(deep=True)

    preparar_matriz_correlacion(df)

    pd.testing.assert_frame_equal(df, original)


def test_preparar_matriz_correlacion_cuadrada_y_simetrica() -> None:
    matriz = preparar_matriz_correlacion(dataframe_clientes())

    assert matriz.shape[0] == matriz.shape[1]
    pd.testing.assert_frame_equal(matriz, matriz.T)


def test_preparar_matriz_correlacion_diagonal_igual_a_1() -> None:
    df = dataframe_clientes()
    matriz = preparar_matriz_correlacion(df)

    for columna in matriz.columns:
        serie = pd.to_numeric(df[columna], errors="coerce").dropna()
        if serie.nunique() > 1:
            assert matriz.loc[columna, columna] == 1.0


def test_preparar_matriz_correlacion_variable_constante() -> None:
    df = dataframe_clientes()
    df["pagos_atrasados"] = [1, 1, 1, 1]
    original = df.copy(deep=True)

    matriz = preparar_matriz_correlacion(df)

    assert pd.isna(matriz.loc["pagos_atrasados", "pagos_atrasados"])
    assert pd.isna(matriz.loc["pagos_atrasados", "satisfaccion"])
    assert pd.isna(matriz.loc["satisfaccion", "pagos_atrasados"])
    pd.testing.assert_frame_equal(df, original)


def test_calcular_correlaciones_abandono_ordenada_por_valor_absoluto() -> None:
    matriz = pd.DataFrame(
        {
            "abandono": [1.0, -0.40, 0.70, 0.05],
            "satisfaccion": [-0.40, 1.0, -0.20, 0.10],
            "dias_sin_uso": [0.70, -0.20, 1.0, 0.30],
            "monto_mensual": [0.05, 0.10, 0.30, 1.0],
        },
        index=["abandono", "satisfaccion", "dias_sin_uso", "monto_mensual"],
    )

    resultado = calcular_correlaciones_abandono(matriz)

    assert resultado["variable"].tolist() == ["Días sin uso", "Satisfacción", "Monto mensual"]
    assert resultado["direccion"].tolist() == ["Positiva", "Negativa", "Sin relación lineal clara"]


def test_calcular_correlaciones_abandono_excluye_abandono_consigo_mismo() -> None:
    matriz = preparar_matriz_correlacion(dataframe_clientes())
    resultado = calcular_correlaciones_abandono(matriz)

    assert "Abandono" not in resultado["variable"].tolist()
