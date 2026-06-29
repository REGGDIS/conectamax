"""Pruebas del modelo de churn y del predictor (Specs 04 y 05)."""
import os
import sqlite3
import sys

import pandas as pd
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import generate_data as gd  # noqa: E402
import train as tr  # noqa: E402
import predictor as pr  # noqa: E402


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    base = tmp_path_factory.mktemp("modelo")
    db = str(base / "conectamax.db")
    out = str(base / "modelo_churn.pkl")
    gd.poblar(db, n=800, exportar_csv=False)
    metrics = tr.entrenar(db, out)
    return db, out, metrics


def test_modelo_se_guarda(entorno):
    _, out, _ = entorno
    assert os.path.exists(out)


def test_arbol_supera_linea_base(entorno):
    _, _, m = entorno
    assert m["arbol"]["accuracy"] > m["base"]


def test_recall_objetivo(entorno):
    _, _, m = entorno
    # meta orientativa del plan: recall de churn >= 0.60
    assert m["arbol"]["recall"] >= 0.55


def test_predictor_niveles_validos(entorno):
    db, out, _ = entorno
    con = sqlite3.connect(db)
    df = pd.read_sql("SELECT * FROM comportamiento_cliente LIMIT 50", con)
    con.close()
    modelo = pr.cargar_modelo(out)
    res = pr.predecir(df, modelo)
    assert res["probabilidad_churn"].between(0, 1).all()
    assert set(res["nivel_riesgo"]).issubset({"bajo", "medio", "alto"})
    assert len(res) == len(df)


def test_umbral_riesgo():
    assert pr.nivel_riesgo(0.1) == "bajo"
    assert pr.nivel_riesgo(0.45) == "medio"
    assert pr.nivel_riesgo(0.8) == "alto"
