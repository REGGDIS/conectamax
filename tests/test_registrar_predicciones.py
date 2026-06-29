"""Prueba del registro de predicciones (integracion Fase 7)."""
import os
import sqlite3
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import generate_data as gd  # noqa: E402
import train as tr  # noqa: E402
import registrar_predicciones as rp  # noqa: E402


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    base = tmp_path_factory.mktemp("pred")
    db = str(base / "conectamax.db")
    modelo = str(base / "modelo.pkl")
    gd.poblar(db, n=600, exportar_csv=False)
    tr.entrenar(db, modelo)
    df = rp.generar(db, modelo)
    rp.guardar(db, df, version="v1")
    return db


def test_se_registraron_predicciones(db):
    con = sqlite3.connect(db)
    n_pred = con.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0]
    n_cli = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    con.close()
    assert n_pred == n_cli


def test_niveles_y_rango_validos(db):
    con = sqlite3.connect(db)
    rows = con.execute("SELECT probabilidad_churn, nivel_riesgo FROM predicciones").fetchall()
    con.close()
    assert all(0.0 <= p <= 1.0 for p, _ in rows)
    assert all(n in ("bajo", "medio", "alto") for _, n in rows)


def test_separacion_real_vs_prediccion(db):
    # la vista analitica NO debe contener columnas de prediccion (anti-fuga §29.6)
    con = sqlite3.connect(db)
    cols = [c[1] for c in con.execute("PRAGMA table_info(comportamiento_cliente)")]
    con.close()
    assert "probabilidad_churn" not in cols
    assert "nivel_riesgo" not in cols
