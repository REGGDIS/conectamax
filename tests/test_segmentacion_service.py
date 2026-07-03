import pandas as pd
import pytest

from services.segmentacion_service import (
    COLUMNAS_SEGMENTACION,
    calcular_conteo_clusters,
    calcular_resumen_clusters,
    calcular_tasa_abandono_por_cluster,
    describir_clusters,
    escalar_variables_segmentacion,
    generar_clusters,
    preparar_variables_segmentacion,
    segmentar_clientes_kmeans,
    validar_columnas_segmentacion,
)


def dataframe_clientes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0001", "CXM0002", "CXM0003", "CXM0004", "CXM0005", "CXM0006"],
            "nombre": ["Ana", "Luis", "Carolina", "Marcos", "Paula", "Diego"],
            "antiguedad_meses": [36, 8, 18, 24, 60, 3],
            "monto_mensual": [48990, 18990, 33990, 35990, 88990, 12990],
            "cantidad_servicios": [4, 1, 3, 3, 5, 1],
            "reclamos_ultimos_6_meses": [0, 2, 3, 1, 0, 4],
            "pagos_atrasados": [0, 1, 1, 0, 0, 3],
            "dias_sin_uso": [2, 14, 16, 5, 1, 25],
            "satisfaccion": [5, 3, 2, 4, 5, 1],
            "abandono": [0, 1, 1, 0, 0, 1],
            "nivel_riesgo": ["bajo", "alto", "medio", "bajo", "bajo", "alto"],
            "probabilidad_churn": [0.10, 0.85, 0.55, 0.20, 0.05, 0.90],
        }
    )


def test_columnas_validas() -> None:
    assert validar_columnas_segmentacion(dataframe_clientes()) == []


def test_columnas_faltantes() -> None:
    df = dataframe_clientes().drop(columns=["monto_mensual", "satisfaccion"])

    assert validar_columnas_segmentacion(df) == ["monto_mensual", "satisfaccion"]
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        preparar_variables_segmentacion(df)


def test_dataframe_vacio() -> None:
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        preparar_variables_segmentacion(pd.DataFrame())


def test_dataframe_vacio_con_columnas_validas() -> None:
    df = pd.DataFrame(columns=COLUMNAS_SEGMENTACION)

    with pytest.raises(ValueError, match="No hay registros suficientes"):
        preparar_variables_segmentacion(df)


def test_conversion_numerica() -> None:
    df = dataframe_clientes()
    df["satisfaccion"] = ["5", "3", "2", "4", "5", "1"]

    features = preparar_variables_segmentacion(df)

    assert pd.api.types.is_numeric_dtype(features["satisfaccion"])
    assert features["satisfaccion"].tolist() == [5, 3, 2, 4, 5, 1]


def test_imputacion_de_nulos() -> None:
    df = dataframe_clientes()
    df.loc[0, "monto_mensual"] = None

    features = preparar_variables_segmentacion(df)

    assert features["monto_mensual"].isna().sum() == 0
    assert features.loc[0, "monto_mensual"] == pytest.approx(33990.0)


def test_columna_completamente_invalida() -> None:
    df = dataframe_clientes()
    df["dias_sin_uso"] = ["x", "y", "z", "a", "b", "c"]

    with pytest.raises(ValueError, match="dias_sin_uso"):
        preparar_variables_segmentacion(df)


def test_escalado_con_medias_cercanas_a_cero() -> None:
    features = preparar_variables_segmentacion(dataframe_clientes())
    escaladas = escalar_variables_segmentacion(features)

    assert list(escaladas.columns) == COLUMNAS_SEGMENTACION
    assert escaladas.index.equals(features.index)
    assert all(abs(valor) < 1e-12 for valor in escaladas.mean().tolist())


def test_generacion_de_3_clusters() -> None:
    features = preparar_variables_segmentacion(dataframe_clientes())
    escaladas = escalar_variables_segmentacion(features)

    clusters = generar_clusters(escaladas)

    assert clusters.name == "cluster_id"
    assert clusters.index.equals(escaladas.index)
    assert sorted(clusters.unique().tolist()) == [0, 1, 2]


def test_reproducibilidad_con_random_state_42() -> None:
    features = preparar_variables_segmentacion(dataframe_clientes())
    escaladas = escalar_variables_segmentacion(features)

    clusters_1 = generar_clusters(escaladas, random_state=42)
    clusters_2 = generar_clusters(escaladas, random_state=42)

    pd.testing.assert_series_equal(clusters_1, clusters_2)


def test_clientes_insuficientes() -> None:
    features = preparar_variables_segmentacion(dataframe_clientes().head(2))
    escaladas = escalar_variables_segmentacion(features)

    with pytest.raises(ValueError, match="clientes suficientes"):
        generar_clusters(escaladas, n_clusters=3)


def test_conteo_por_cluster() -> None:
    resultado = segmentar_clientes_kmeans(dataframe_clientes())
    conteo = resultado["conteo_clusters"]

    assert conteo["total_clientes"].sum() == 6
    assert set(conteo.columns) == {"cluster_id", "cluster", "total_clientes"}


def test_resumen_de_promedios() -> None:
    resultado = segmentar_clientes_kmeans(dataframe_clientes())
    resumen = resultado["resumen_clusters"]

    assert {"cluster_id", "cluster", "total_clientes"}.issubset(resumen.columns)
    assert set(COLUMNAS_SEGMENTACION).issubset(resumen.columns)
    assert resumen["total_clientes"].sum() == 6


def test_tasa_de_abandono_por_cluster() -> None:
    segmentado = pd.DataFrame(
        {
            "cluster_id": [0, 0, 1, 1, 2, 2],
            "cluster": ["Clúster 1", "Clúster 1", "Clúster 2", "Clúster 2", "Clúster 3", "Clúster 3"],
            "abandono": [0, 1, 1, 1, 0, 0],
        }
    )

    tasa = calcular_tasa_abandono_por_cluster(segmentado)

    assert tasa.loc[tasa["cluster_id"] == 0, "tasa_abandono"].iloc[0] == 50.0
    assert tasa.loc[tasa["cluster_id"] == 1, "clientes_abandonaron"].iloc[0] == 2
    assert tasa.loc[tasa["cluster_id"] == 2, "tasa_abandono"].iloc[0] == 0.0


def test_ausencia_de_nulos_en_resultados() -> None:
    df = dataframe_clientes()
    df.loc[0, "monto_mensual"] = None

    resultado = segmentar_clientes_kmeans(df)

    assert not resultado["clientes_segmentados"][["cluster_id", "cluster"]].isna().any().any()
    assert not resultado["conteo_clusters"].isna().any().any()
    assert not resultado["resumen_clusters"].isna().any().any()
    assert not resultado["tasa_abandono_clusters"].isna().any().any()


def test_abandono_no_entra_en_variables_de_entrenamiento() -> None:
    features = preparar_variables_segmentacion(dataframe_clientes())

    assert "abandono" not in features.columns
    assert "nivel_riesgo" not in features.columns
    assert "probabilidad_churn" not in features.columns
    assert list(features.columns) == COLUMNAS_SEGMENTACION


def test_dataframe_original_no_se_modifica() -> None:
    df = dataframe_clientes()
    original = df.copy(deep=True)

    segmentar_clientes_kmeans(df)

    pd.testing.assert_frame_equal(df, original)


def test_descripciones_neutrales() -> None:
    resultado = segmentar_clientes_kmeans(dataframe_clientes())
    descripciones = describir_clusters(resultado["resumen_clusters"])
    texto = " ".join(descripciones).lower()

    assert len(descripciones) == 3
    assert "causalidad" in texto
    assert "malos" not in texto
    assert "problematicos" not in texto
    assert "premium" not in texto
    assert "alto riesgo" not in texto


def test_calculos_con_dataframe_segmentado_vacio() -> None:
    assert calcular_conteo_clusters(pd.DataFrame()).empty
    assert calcular_resumen_clusters(pd.DataFrame()).empty
    assert calcular_tasa_abandono_por_cluster(pd.DataFrame()).empty
