"""Registra predicciones en la tabla `predicciones` (rev. PR #6).

- Activa claves foraneas (punto 11).
- Transacciones seguras con rollback y cierre (punto 6).
- `limpiar` por defecto False para no borrar el historial (punto 12).
- Toma modelo/version de los metadatos del bundle.
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime

import pandas as pd

import predictor as pr
from _paths import default_db, default_modelo


def generar(db_path: str, modelo_path: str):
    bundle = pr.cargar_modelo(modelo_path)
    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("SELECT * FROM comportamiento_cliente", con)
    finally:
        con.close()
    return pr.predecir(df, bundle), bundle


def guardar(db_path: str, df_pred: pd.DataFrame, modelo_nombre: str = "arbol_decision",
            version: str = "v1", limpiar: bool = False) -> int:
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = [(r.id_cliente, float(r.probabilidad_churn), r.nivel_riesgo,
              modelo_nombre, version, ahora)
             for r in df_pred.itertuples(index=False)]
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        if limpiar:
            con.execute("DELETE FROM predicciones WHERE modelo=? AND version_modelo=?",
                        (modelo_nombre, version))
        con.executemany(
            "INSERT INTO predicciones "
            "(id_cliente, probabilidad_churn, nivel_riesgo, modelo, version_modelo, fecha_prediccion) "
            "VALUES (?,?,?,?,?,?)", filas)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return len(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=default_db())
    ap.add_argument("--modelo", default=default_modelo())
    ap.add_argument("--version", default=None)
    ap.add_argument("--limpiar", action="store_true",
                    help="borra predicciones previas del mismo modelo+version")
    a = ap.parse_args()
    df, bundle = generar(a.db, a.modelo)
    nombre = bundle.get("modelo_nombre", "arbol_decision") if isinstance(bundle, dict) else "arbol_decision"
    version = a.version or (bundle.get("version", "v1") if isinstance(bundle, dict) else "v1")
    n = guardar(a.db, df, nombre, version, limpiar=a.limpiar)
    print(f"Predicciones registradas: {n}")
    print(df["nivel_riesgo"].value_counts().to_string())


if __name__ == "__main__":
    main()
