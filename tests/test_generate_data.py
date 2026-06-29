"""Pruebas del generador de datos sinteticos (rev. PR #6)."""
import os, sqlite3, sys
import pytest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import generate_data as gd  # noqa: E402

CONTRATO = ["id_cliente","nombre","ciudad","antiguedad_meses","tipo_contrato","plan",
            "monto_mensual","reclamos_ultimos_6_meses","pagos_atrasados","dias_sin_uso",
            "satisfaccion","abandono","edad","cantidad_servicios"]

@pytest.fixture(scope="module")
def con(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("db") / "test.db")
    gd.poblar(db, n=400, exportar_csv=False, reset=False)
    c = sqlite3.connect(db); yield c; c.close()

def test_minimo_clientes(con):
    assert con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] >= 400

def test_id_unico(con):
    n = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    u = con.execute("SELECT COUNT(DISTINCT id_cliente) FROM clientes").fetchone()[0]
    assert n == u

def test_tasa_churn(con):
    t = con.execute("SELECT AVG(abandono) FROM clientes").fetchone()[0]
    assert 0.15 <= t <= 0.45

def test_vista_contrato(con):
    cols = [c[1] for c in con.execute("PRAGMA table_info(comportamiento_cliente)")][:14]
    assert cols == CONTRATO

def test_coherencia_reclamos(con):
    # mismo filtro que la vista: ventana [ref-6m, ref] (punto 2)
    bad = con.execute("""SELECT COUNT(*) FROM comportamiento_cliente v
      LEFT JOIN (SELECT id_cliente,COUNT(*) n FROM reclamos
        WHERE fecha>=date((SELECT fecha_referencia FROM parametros WHERE id=1),'-6 months')
          AND fecha<=date((SELECT fecha_referencia FROM parametros WHERE id=1))
        GROUP BY id_cliente) r ON r.id_cliente=v.id_cliente
      WHERE v.reclamos_ultimos_6_meses<>COALESCE(r.n,0)""").fetchone()[0]
    assert bad == 0

def test_ventana_6_meses_excluye_futuro(con):
    # punto 2: un reclamo posterior a la fecha de referencia NO debe contarse.
    db = con.execute("PRAGMA database_list").fetchone()[2]
    c = sqlite3.connect(db)
    try:
        c.execute("PRAGMA foreign_keys=ON")
        ref = c.execute("SELECT fecha_referencia FROM parametros WHERE id=1").fetchone()[0]
        cid = c.execute("SELECT id_cliente FROM clientes LIMIT 1").fetchone()[0]
        antes = c.execute(
            "SELECT reclamos_ultimos_6_meses FROM comportamiento_cliente WHERE id_cliente=?",
            (cid,)).fetchone()[0]
        c.execute("INSERT INTO reclamos (id_cliente,fecha,tipo,canal,estado) "
                  "VALUES (?, date(?, '+10 days'), 'tecnico','app','abierto')", (cid, ref))
        c.commit()
        despues = c.execute(
            "SELECT reclamos_ultimos_6_meses FROM comportamiento_cliente WHERE id_cliente=?",
            (cid,)).fetchone()[0]
        assert despues == antes  # el reclamo futuro no se cuenta
    finally:
        c.close()

def test_un_solo_principal_activo(con):
    dup = con.execute("""SELECT COUNT(*) FROM (SELECT id_cliente FROM contratos
      WHERE es_principal=1 AND estado='activo' GROUP BY id_cliente HAVING COUNT(*)>1)""").fetchone()[0]
    assert dup == 0

def test_exactamente_un_principal_por_cliente(con):
    # punto 3: cada cliente tiene EXACTAMENTE un contrato principal activo.
    n_clientes = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    con_uno = con.execute(
        "SELECT COUNT(*) FROM (SELECT id_cliente FROM contratos "
        "WHERE es_principal=1 AND estado='activo' "
        "GROUP BY id_cliente HAVING COUNT(*)=1)").fetchone()[0]
    assert con_uno == n_clientes

def test_sin_nulos_obligatorios(con):
    nul = con.execute("SELECT SUM(plan IS NULL)+SUM(satisfaccion IS NULL)+SUM(abandono IS NULL) "
                      "FROM comportamiento_cliente").fetchone()[0]
    assert nul == 0

def test_reset_requerido(con, tmp_path):
    # sin reset sobre BD con datos -> SystemExit
    db = con.execute("PRAGMA database_list").fetchone()[2]
    with pytest.raises(SystemExit):
        gd.poblar(db, n=10, reset=False)

def _insertar_prediccion(db, cid):
    c = sqlite3.connect(db)
    try:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("INSERT INTO predicciones (id_cliente,probabilidad_churn,nivel_riesgo,"
                  "modelo,version_modelo,fecha_prediccion) VALUES (?,?,?,?,?,?)",
                  (cid, 0.5, "medio", "arbol_decision", "v1", "2026-06-28 00:00:00"))
        c.commit()
    finally:
        c.close()

def _n_predicciones(db):
    c = sqlite3.connect(db)
    try:
        return c.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0]
    finally:
        c.close()

def test_reset_conserva_predicciones(tmp_path):
    # punto 1: --reset preserva el historial de predicciones.
    db = str(tmp_path / "reset.db")
    gd.poblar(db, n=60, reset=False)
    _insertar_prediccion(db, "CXM0001")  # id determinista, se regenera con el mismo N
    assert _n_predicciones(db) == 1
    gd.poblar(db, n=60, reset=True)  # mismo N -> mismos ids -> FK valida en commit
    assert _n_predicciones(db) == 1  # conservadas

def test_reset_predicciones_borra_historial(tmp_path):
    # punto 1: --reset-predicciones es la accion explicita que borra el historial.
    db = str(tmp_path / "resetpred.db")
    gd.poblar(db, n=60, reset=False)
    _insertar_prediccion(db, "CXM0001")
    assert _n_predicciones(db) == 1
    gd.poblar(db, n=60, reset=True, reset_predicciones=True)
    assert _n_predicciones(db) == 0
