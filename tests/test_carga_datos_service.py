from io import StringIO

from config.settings import CSV_EJEMPLO_PATH
from services.carga_datos_service import cargar_y_validar_csv, construir_estado_carga


CSV_VALIDO = """id_cliente,nombre,ciudad,antiguedad_meses,tipo_contrato,plan,monto_mensual,reclamos_ultimos_6_meses,pagos_atrasados,dias_sin_uso,satisfaccion,abandono,edad,cantidad_servicios
CXM0001,Ana Rojas,Santiago,24,Anual,Fibra Plus,32990,0,0,2,5,0,34,3
CXM0002,Luis Paredes,Valparaiso,8,Mensual,Basico,18990,2,1,14,3,1,28,1
"""


def test_archivo_csv_valido() -> None:
    df, resultado = cargar_y_validar_csv(StringIO(CSV_VALIDO))

    assert df is not None
    assert resultado["es_valido"] is True
    assert resultado["errores"] == []
    assert df.shape == (2, 14)


def test_archivo_csv_vacio() -> None:
    df, resultado = cargar_y_validar_csv(StringIO(""))

    assert df is None
    assert resultado["es_valido"] is False
    assert resultado["errores"]


def test_archivo_csv_con_estructura_incorrecta() -> None:
    csv_invalido = "id_cliente,nombre\nCXM0001,Ana Rojas\n"

    df, resultado = cargar_y_validar_csv(StringIO(csv_invalido))

    assert df is None
    assert resultado["es_valido"] is False
    assert any("Faltan columnas obligatorias" in error for error in resultado["errores"])


def test_normaliza_nombres_de_columnas() -> None:
    csv_con_espacios = CSV_VALIDO.replace("id_cliente", " id_cliente ", 1)

    df, resultado = cargar_y_validar_csv(StringIO(csv_con_espacios))

    assert df is not None
    assert resultado["es_valido"] is True
    assert "id_cliente" in df.columns


def test_archivo_invalido_no_reemplaza_estado_activo() -> None:
    df_valido, resultado_valido = cargar_y_validar_csv(StringIO(CSV_VALIDO))
    assert df_valido is not None

    estado = construir_estado_carga({}, df_valido, resultado_valido, "valido.csv")
    df_invalido, resultado_invalido = cargar_y_validar_csv(StringIO("id_cliente,nombre\n1,Ana\n"))

    estado_actualizado = construir_estado_carga(
        estado,
        df_invalido,
        resultado_invalido,
        "invalido.csv",
    )

    assert estado_actualizado["clientes_df"] is df_valido
    assert estado_actualizado["datos_cargados"] is True
    assert estado_actualizado["nombre_archivo_activo"] == "valido.csv"
    assert estado_actualizado["ultimo_archivo_procesado"] == "invalido.csv"
    assert estado_actualizado["resultado_validacion"] is resultado_invalido


def test_reutiliza_archivo_con_puntero_avanzado() -> None:
    archivo = StringIO(CSV_VALIDO)
    archivo.read()

    df, resultado = cargar_y_validar_csv(archivo)

    assert df is not None
    assert resultado["es_valido"] is True
    assert df.shape == (2, 14)


def test_csv_simulado_es_valido() -> None:
    df, resultado = cargar_y_validar_csv(CSV_EJEMPLO_PATH)

    assert df is not None
    assert resultado["es_valido"] is True
    assert df.shape == (45, 14)
