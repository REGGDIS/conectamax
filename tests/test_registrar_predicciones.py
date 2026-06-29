"""Pruebas del registro de predicciones (rev. PR #6)."""
import os, sqlite3, sys
import pytest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import generate_data as gd  # noqa: E402
import train as tr  # noqa: E402
import registrar_predicciones as rp  # noqa: E402

@pytest.fixture(scope="module")
def db(tmp_path_factory):
    base = tmp_path_factory.mktemp("p")
    db = str(base / "c.db"); modelo = str(base / "m.pkl")
    gd.poblar(db, n=600, reset=False)
    tr.entrenar(db, modelo)
    df, bundle = rp.generar(db, modelo)
    rp.guardar(db, df, bundle["modelo_nombre"], bundle["version"])
    return db

def test_registradas(db):
    c = sqlite3.connect(db)
    n_pred = c.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0]
    n_cli = c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    c.close()
    assert n_pred == n_cli

def test_rangos(db):
    c = sqlite3.connect(db)
    rows = c.execute("SELECT probabilidad_churn, nivel_riesgo FROM predicciones").fetchall()
    c.close()
    assert all(0 <= p <= 1 for p, _ in rows)
    assert all(n in ("bajo", "medio", "alto") for _, n in rows)

def test_no_limpia_por_defecto(db):
    # registrar de nuevo sin limpiar debe ACUMULAR (no borrar historial)
    df, bundle = rp.generar(db, db.replace("c.db", "m.pkl"))
    antes = _count(db)
    rp.guardar(db, df, bundle["modelo_nombre"], bundle["version"])  # limpiar=False por defecto
    assert _count(db) == antes + len(df)

def test_anti_fuga(db):
    c = sqlite3.connect(db)
    cols = [x[1] for x in c.execute("PRAGMA table_info(comportamiento_cliente)")]
    c.close()
    assert "probabilidad_churn" not in cols and "nivel_riesgo" not in cols

def _count(db):
    c = sqlite3.connect(db); n = c.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0]; c.close(); return n
