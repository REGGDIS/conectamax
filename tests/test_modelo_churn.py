"""Pruebas del modelo y predictor (rev. PR #6)."""
import os, sqlite3, sys
import pandas as pd, pytest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import generate_data as gd  # noqa: E402
import train as tr  # noqa: E402
import predictor as pr  # noqa: E402

@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("m")
    db = str(base / "c.db"); out = str(base / "m.pkl")
    gd.poblar(db, n=800, reset=False)
    met = tr.entrenar(db, out)
    return db, out, met

def test_modelo_guardado_con_metadatos(entorno):
    import joblib
    _, out, _ = entorno
    b = joblib.load(out)
    assert os.path.exists(out)
    for k in ["pipeline", "features", "clase_positiva", "version", "metricas", "fecha_entrenamiento"]:
        assert k in b
    assert "segmento" not in b["features"]  # fuga conceptual excluida

def test_supera_linea_base(entorno):
    _, _, m = entorno
    assert m["arbol"]["accuracy"] > m["base"]

def test_recall(entorno):
    _, _, m = entorno
    assert m["arbol"]["recall"] >= 0.55

def test_predictor_valido(entorno):
    db, out, _ = entorno
    con = sqlite3.connect(db); df = pd.read_sql("SELECT * FROM comportamiento_cliente LIMIT 50", con); con.close()
    res = pr.predecir(df, pr.cargar_modelo(out))
    assert res["probabilidad_churn"].between(0, 1).all()
    assert set(res["nivel_riesgo"]).issubset({"bajo", "medio", "alto"})

def test_predictor_df_vacio(entorno):
    _, out, _ = entorno
    with pytest.raises(ValueError):
        pr.predecir(pd.DataFrame(), pr.cargar_modelo(out))

def test_predictor_modelo_inexistente():
    with pytest.raises(FileNotFoundError):
        pr.cargar_modelo("/tmp/no_existe_modelo.pkl")

def test_umbrales():
    assert pr.nivel_riesgo(0.1) == "bajo"
    assert pr.nivel_riesgo(0.45) == "medio"
    assert pr.nivel_riesgo(0.8) == "alto"
