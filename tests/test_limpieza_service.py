import pandas as pd

from services.carga_datos_service import construir_estado_carga
from services.limpieza_service import preparar_datos


def dataframe_sucio() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": [" C1 ", "", "C2", "C2", "C3"],
            "nombre": [" Ana   Rojas ", "Sin Uso", "   ", "Duplicado", "Carlos"],
            "ciudad": [" santiago ", "Temuco", "", "Valparaiso", "Concepcion"],
            "antiguedad_meses": ["12", "1", "-1", "24", ""],
            "tipo_contrato": [" mensual ", "Anual", "", "Mensual", "Anual"],
            "plan": [" fibra   plus ", "Basico", "", "Fibra", "Total"],
            "monto_mensual": ["10000", "15000", "-50", "20000", "abc"],
            "reclamos_ultimos_6_meses": ["1", "0", "-1", "2", ""],
            "pagos_atrasados": ["0", "0", "-3", "1", ""],
            "dias_sin_uso": ["5", "1", "-4", "8", ""],
            "satisfaccion": ["5", "4", "7", "3", ""],
            "abandono": ["0", "0", "1", "1", "2"],
            "edad": ["34", "30", "200", "44", "x"],
            "cantidad_servicios": ["2", "1", "-2", "3", ""],
        }
    )


def dataframe_valido() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["C1", "C2", "C3", "C4"],
            "nombre": ["Ana", "Luis", "Carla", "Mario"],
            "ciudad": ["Santiago", "Temuco", "Valparaiso", "Iquique"],
            "antiguedad_meses": [6, 18, 36, 60],
            "tipo_contrato": ["Mensual", "Anual", "Mensual", "Bienal"],
            "plan": ["Basico", "Fibra", "Total", "Fibra"],
            "monto_mensual": [10000, 20000, 30000, 40000],
            "reclamos_ultimos_6_meses": [0, 1, 0, 2],
            "pagos_atrasados": [0, 1, 0, 2],
            "dias_sin_uso": [1, 10, 20, 30],
            "satisfaccion": [1, 3, 4, 5],
            "abandono": [0, 1, 0, 1],
            "edad": [18, 30, 45, 60],
            "cantidad_servicios": [0, 1, 2, 3],
        }
    )


def test_dataframe_none() -> None:
    limpio, reporte = preparar_datos(None)

    assert limpio.empty
    assert reporte["filas_iniciales"] == 0
    assert reporte["filas_finales"] == 0


def test_dataframe_vacio() -> None:
    limpio, reporte = preparar_datos(pd.DataFrame())

    assert limpio.empty
    assert reporte["filas_eliminadas"] == 0


def test_no_modifica_dataframe_original() -> None:
    df = dataframe_sucio()
    original = df.copy(deep=True)

    preparar_datos(df)

    pd.testing.assert_frame_equal(df, original)


def test_elimina_ids_vacios() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())

    assert reporte["ids_vacios_eliminados"] == 1
    assert "" not in limpio["id_cliente"].tolist()


def test_elimina_ids_duplicados() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())

    assert reporte["duplicados_eliminados"] == 1
    assert limpio["id_cliente"].tolist().count("C2") == 1


def test_normalizacion_de_textos() -> None:
    limpio, _ = preparar_datos(dataframe_sucio())
    fila = limpio[limpio["id_cliente"] == "C1"].iloc[0]

    assert fila["nombre"] == "Ana Rojas"
    assert fila["ciudad"] == "Santiago"
    assert fila["tipo_contrato"] == "Mensual"
    assert fila["plan"] == "Fibra Plus"


def test_nombre_vacio() -> None:
    limpio, _ = preparar_datos(dataframe_sucio())
    fila = limpio[limpio["id_cliente"] == "C2"].iloc[0]

    assert fila["nombre"] == "Cliente sin nombre"


def test_categorias_vacias() -> None:
    limpio, _ = preparar_datos(dataframe_sucio())
    fila = limpio[limpio["id_cliente"] == "C2"].iloc[0]

    assert fila["ciudad"] == "No informado"
    assert fila["tipo_contrato"] == "No informado"
    assert fila["plan"] == "No informado"


def test_conversion_numerica_y_no_convertibles() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())

    assert limpio.loc[limpio["id_cliente"] == "C1", "monto_mensual"].iloc[0] == 10000.0
    assert reporte["valores_no_convertibles"]["monto_mensual"] == 1
    assert reporte["valores_no_convertibles"]["edad"] == 1


def test_imputacion_de_medianas() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())
    fila = limpio[limpio["id_cliente"] == "C2"].iloc[0]

    assert fila["edad"] == 34
    assert fila["antiguedad_meses"] == 12
    assert fila["monto_mensual"] == 10000.0
    assert reporte["valores_imputados"]["edad"] >= 1


def test_imputacion_de_ceros() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())
    fila = limpio[limpio["id_cliente"] == "C2"].iloc[0]

    assert fila["reclamos_ultimos_6_meses"] == 0
    assert fila["pagos_atrasados"] == 0
    assert reporte["valores_imputados"]["reclamos_ultimos_6_meses"] >= 1


def test_edad_fuera_de_rango() -> None:
    _, reporte = preparar_datos(dataframe_sucio())

    assert reporte["valores_fuera_de_rango"]["edad"] == 1


def test_satisfaccion_fuera_de_rango() -> None:
    _, reporte = preparar_datos(dataframe_sucio())

    assert reporte["valores_fuera_de_rango"]["satisfaccion"] == 1


def test_valores_negativos() -> None:
    _, reporte = preparar_datos(dataframe_sucio())

    assert reporte["valores_fuera_de_rango"]["monto_mensual"] == 1
    assert reporte["valores_fuera_de_rango"]["pagos_atrasados"] == 1


def test_abandono_invalido() -> None:
    limpio, reporte = preparar_datos(dataframe_sucio())

    assert reporte["abandono_invalido_eliminado"] == 1
    assert limpio["abandono"].isin([0, 1]).all()


def test_tipos_finales() -> None:
    limpio, _ = preparar_datos(dataframe_sucio())

    for columna in [
        "edad",
        "antiguedad_meses",
        "cantidad_servicios",
        "reclamos_ultimos_6_meses",
        "pagos_atrasados",
        "dias_sin_uso",
        "abandono",
    ]:
        assert pd.api.types.is_integer_dtype(limpio[columna])
    assert pd.api.types.is_float_dtype(limpio["monto_mensual"])
    assert pd.api.types.is_float_dtype(limpio["satisfaccion"])


def test_creacion_grupo_edad() -> None:
    limpio, _ = preparar_datos(dataframe_valido())

    assert limpio["grupo_edad"].tolist() == ["18-29", "30-44", "45-59", "60 o más"]


def test_creacion_grupo_antiguedad() -> None:
    limpio, _ = preparar_datos(dataframe_valido())

    assert limpio["grupo_antiguedad"].tolist() == [
        "0-12 meses",
        "13-24 meses",
        "25-48 meses",
        "49 meses o más",
    ]


def test_creacion_nivel_satisfaccion() -> None:
    limpio, _ = preparar_datos(dataframe_valido())

    assert limpio["nivel_satisfaccion"].tolist() == ["Baja", "Media", "Alta", "Alta"]


def test_creacion_tiene_morosidad() -> None:
    limpio, _ = preparar_datos(dataframe_valido())

    assert limpio["tiene_morosidad"].tolist() == [0, 1, 0, 1]


def test_creacion_tiene_reclamos() -> None:
    limpio, _ = preparar_datos(dataframe_valido())

    assert limpio["tiene_reclamos"].tolist() == [0, 1, 0, 1]


def test_contenido_del_reporte() -> None:
    _, reporte = preparar_datos(dataframe_sucio())

    assert reporte["filas_iniciales"] == 5
    assert "valores_no_convertibles" in reporte
    assert "valores_fuera_de_rango" in reporte
    assert "valores_imputados" in reporte
    assert reporte["columnas_derivadas"] == [
        "grupo_edad",
        "grupo_antiguedad",
        "nivel_satisfaccion",
        "tiene_morosidad",
        "tiene_reclamos",
    ]


def test_coherencia_filas_iniciales_finales_y_eliminadas() -> None:
    _, reporte = preparar_datos(dataframe_sucio())

    assert reporte["filas_iniciales"] == reporte["filas_finales"] + reporte["filas_eliminadas"]


def test_carga_valida_reinicia_estado_limpio() -> None:
    df = dataframe_valido()
    estado = {
        "clientes_df": dataframe_sucio(),
        "datos_cargados": True,
        "nombre_archivo_activo": "anterior.csv",
        "clientes_df_limpio": dataframe_valido(),
        "reporte_limpieza": {"filas_finales": 4},
        "datos_preparados": True,
    }
    resultado = {"es_valido": True, "errores": [], "advertencias": [], "resumen": {}}

    nuevo_estado = construir_estado_carga(estado, df, resultado, "nuevo.csv")

    assert nuevo_estado["clientes_df"] is df
    assert nuevo_estado["datos_cargados"] is True
    assert nuevo_estado["nombre_archivo_activo"] == "nuevo.csv"
    assert nuevo_estado["clientes_df_limpio"] is None
    assert nuevo_estado["reporte_limpieza"] is None
    assert nuevo_estado["datos_preparados"] is False
