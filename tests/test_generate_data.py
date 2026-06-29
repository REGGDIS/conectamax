"""Pruebas basicas del generador de datos sinteticos (Spec 02)."""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import generate_data as gd  # noqa: E402

CONTRATO = [
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
    "edad",
    "cantidad_servicios",
]


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    db = tmp_path_factory.mktemp("db") / "test.db"
    gd.poblar(str(db), n=400, exportar_csv=False)
    c = sqlite3.connect(str(db))
    yield c
    c.close()


def test_minimo_clientes(con):
    assert con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] >= 400


def test_id_unico(con):
    n = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    u = con.execute("SELECT COUNT(DISTINCT id_cliente) FROM clientes").fetchone()[0]
    assert n == u


def test_tasa_churn_razonable(con):
    tasa = con.execute("SELECT AVG(abandono) FROM clientes").fetchone()[0]
    assert 0.15 <= tasa <= 0.45


def test_vista_reproduce_contrato(con):
    cols = [c[1] for c in con.execute("PRAGMA table_info(comportamiento_cliente)")][:14]
    assert cols == CONTRATO


def test_coherencia_reclamos(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM comportamiento_cliente v "
        "LEFT JOIN (SELECT id_cliente,COUNT(*) n FROM reclamos GROUP BY id_cliente) r "
        "ON r.id_cliente=v.id_cliente "
        "WHERE v.reclamos_ultimos_6_meses<>COALESCE(r.n,0)"
    ).fetchone()[0]
    assert bad == 0


def test_coherencia_servicios(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM comportamiento_cliente v "
        "LEFT JOIN (SELECT id_cliente,COUNT(*) n FROM contratos "
        "WHERE estado='activo' GROUP BY id_cliente) k "
        "ON k.id_cliente=v.id_cliente "
        "WHERE v.cantidad_servicios<>COALESCE(k.n,0)"
    ).fetchone()[0]
    assert bad == 0


def test_sin_nulos_obligatorios(con):
    nul = con.execute(
        "SELECT SUM(plan IS NULL)+SUM(tipo_contrato IS NULL)+SUM(satisfaccion IS NULL)"
        "+SUM(abandono IS NULL) FROM comportamiento_cliente"
    ).fetchone()[0]
    assert nul == 0


def test_dominios_validos(con):
    assert (
        con.execute(
            "SELECT COUNT(*) FROM clientes WHERE satisfaccion NOT BETWEEN 1 AND 5"
        ).fetchone()[0]
        == 0
    )
    assert (
        con.execute("SELECT COUNT(*) FROM clientes WHERE abandono NOT IN (0,1)").fetchone()[0]
        == 0
    )


def test_reproducibilidad_semilla(tmp_path):
    db1 = tmp_path / "a.db"
    db2 = tmp_path / "b.db"
    gd.poblar(str(db1), n=50, exportar_csv=False)
    gd.poblar(str(db2), n=50, exportar_csv=False)
    c1 = sqlite3.connect(str(db1))
    c2 = sqlite3.connect(str(db2))
    ids1 = [r[0] for r in c1.execute("SELECT id_cliente FROM clientes ORDER BY id_cliente")]
    ids2 = [r[0] for r in c2.execute("SELECT id_cliente FROM clientes ORDER BY id_cliente")]
    c1.close()
    c2.close()
    assert ids1 == ids2
