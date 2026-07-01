import pandas as pd
import pytest

import services.fuente_datos_service as fuente
from services.analisis_service import calcular_kpis
from services.cliente_service import filtrar_clientes


def dataframe_sqlite() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_cliente": ["CXM0001", "CXM0002", "CXM0003"],
            "nombre": ["Ana Rojas", "Luis Paredes", "Carolina Vega"],
            "ciudad": ["Santiago", "Valparaiso", "Santiago"],
            "antiguedad_meses": ["36", "8", "18"],
            "tipo_contrato": ["Anual", "Mensual", "Mensual"],
            "plan": ["Hogar Total", "Basico", "Fibra Plus"],
            "monto_mensual": ["48990", "dato invalido", "33990"],
            "reclamos_ultimos_6_meses": [0, 2, 3],
            "pagos_atrasados": [0, 1, 1],
            "dias_sin_uso": [2, 14, 16],
            "satisfaccion": [5, 3, 2],
            "abandono": [0, 1, 1],
            "edad": [34, 28, 44],
            "cantidad_servicios": [4, 1, 3],
            "region": ["Metropolitana", "Valparaiso", "Metropolitana"],
            "segmento": ["Premium", "Residencial", "Residencial"],
        }
    )


@pytest.fixture(autouse=True)
def limpiar_cache() -> None:
    fuente._cargar_clientes_cacheados.clear()


def preparar_repositorio(monkeypatch, tmp_path, df: pd.DataFrame):
    ruta = tmp_path / "clientes.db"
    ruta.write_bytes(b"sqlite-temporal")
    original = df.copy(deep=True)

    def repositorio(database_path):
        assert database_path == str(ruta)
        return original.copy(deep=True)

    monkeypatch.setattr(fuente, "obtener_comportamiento_clientes", repositorio)
    return ruta, original


def test_devuelve_una_copia_independiente(monkeypatch, tmp_path) -> None:
    ruta, original = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    df.loc[0, "nombre"] = "Modificada"

    assert original.loc[0, "nombre"] == "Ana Rojas"


def test_convierte_columnas_numericas_validas(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)

    assert pd.api.types.is_numeric_dtype(df["antiguedad_meses"])
    assert df.loc[0, "antiguedad_meses"] == 36


def test_convierte_valores_invalidos_a_nan(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)

    assert pd.isna(df.loc[1, "monto_mensual"])


def test_conserva_columnas_de_texto(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert df["nombre"].tolist() == ["Ana Rojas", "Luis Paredes", "Carolina Vega"]


def test_mantiene_columnas_adicionales(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert {"region", "segmento"}.issubset(df.columns)


def test_acepta_dataframe_vacio(monkeypatch, tmp_path) -> None:
    columnas = dataframe_sqlite().columns
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, pd.DataFrame(columns=columnas))

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert df.empty
    assert list(df.columns) == list(columnas)


def test_propaga_file_not_found(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        fuente.cargar_clientes_desde_sqlite(tmp_path / "no_existe.db")


def test_propaga_runtime_error(monkeypatch, tmp_path) -> None:
    ruta = tmp_path / "clientes.db"
    ruta.write_bytes(b"sqlite-temporal")

    def repositorio(database_path):
        raise RuntimeError("vista invalida")

    monkeypatch.setattr(fuente, "obtener_comportamiento_clientes", repositorio)

    with pytest.raises(RuntimeError, match="vista invalida"):
        fuente.cargar_clientes_desde_sqlite(ruta)


def test_no_elimina_filas(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert len(df) == 3


def test_no_crea_columnas_derivadas(monkeypatch, tmp_path) -> None:
    original = dataframe_sqlite()
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, original)

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert list(df.columns) == list(original.columns)


def test_cliente_service_funciona_con_dataframe_sqlite(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    resultado = filtrar_clientes(df, ciudades=["Santiago"], abandono=1)

    assert resultado["id_cliente"].tolist() == ["CXM0003"]


def test_analisis_service_funciona_con_dataframe_sqlite(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    kpis = calcular_kpis(df)

    assert kpis["total_clientes"] == 3
    assert kpis["clientes_abandonaron"] == 2


def test_columnas_usadas_por_dashboard_estan_disponibles(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    columnas_dashboard = {
        "ciudad",
        "tipo_contrato",
        "plan",
        "abandono",
        "monto_mensual",
        "reclamos_ultimos_6_meses",
        "pagos_atrasados",
        "dias_sin_uso",
        "satisfaccion",
    }
    assert columnas_dashboard.issubset(df.columns)


def test_primeras_columnas_del_contrato_son_compatibles(monkeypatch, tmp_path) -> None:
    ruta, _ = preparar_repositorio(monkeypatch, tmp_path, dataframe_sqlite())

    df = fuente.cargar_clientes_desde_sqlite(ruta)
    assert list(df.columns[:12]) == [
        "id_cliente",
        "nombre",
        "ciudad",
        "antiguedad_meses",
        "tipo_contrato",
        "plan",
        "monto_mensual",
        "reclamos_ultimos_6_meses",
        "pagos_atrasados",
        "dias_sin_uso",
        "satisfaccion",
        "abandono",
    ]
