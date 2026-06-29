"""Genera predicciones de churn para todos los clientes y las registra en la
tabla `predicciones` (Spec 05 / integracion Fase 7).

Mantiene separados el estado real (`abandono` en clientes) y la prediccion
(tabla `predicciones`), conforme al Plan v3.2 §29.6.

Uso:
    python scripts/registrar_predicciones.py [--db data/conectamax.db]
        [--modelo models/modelo_churn.pkl] [--version v1] [--limpiar]
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime

import pandas as pd

import predictor as pr  # mismo directorio scripts/

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_NOMBRE = "arbol_decision"


def generar(db_path: str, modelo_path: str) -> pd.DataFrame:
    """Lee la vista analitica y devuelve id_cliente, probabilidad y nivel."""
    con = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM comportamiento_cliente", con)
    con.close()
    modelo = pr.cargar_modelo(modelo_path)
    return pr.predecir(df, modelo)


def guardar(db_path: str, df_pred: pd.DataFrame, modelo_nombre: str = MODELO_NOMBRE,
            version: str = "v1", limpiar: bool = False) -> int:
    """Inserta las predicciones en la tabla `predicciones`. Si limpiar=True,
    borra las predicciones previas de ese modelo+version."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = [
        (row.id_cliente, float(row.probabilidad_churn), row.nivel_riesgo,
         modelo_nombre, version, ahora)
        for row in df_pred.itertuples(index=False)
    ]
    con = sqlite3.connect(db_path)
    if limpiar:
        con.execute("DELETE FROM predicciones WHERE modelo=? AND version_modelo=?",
                    (modelo_nombre, version))
    con.executemany(
        "INSERT INTO predicciones "
        "(id_cliente, probabilidad_churn, nivel_riesgo, modelo, version_modelo, fecha_prediccion) "
        "VALUES (?,?,?,?,?,?)", filas)
    con.commit()
    con.close()
    return len(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(RAIZ, "data", "conectamax.db"))
    ap.add_argument("--modelo", default=os.path.join(RAIZ, "models", "modelo_churn.pkl"))
    ap.add_argument("--version", default="v1")
    ap.add_argument("--limpiar", action="store_true", help="borra predicciones previas del modelo+version")
    a = ap.parse_args()
    df = generar(a.db, a.modelo)
    n = guardar(a.db, df, version=a.version, limpiar=a.limpiar)
    print(f"Predicciones registradas: {n}")
    print(df["nivel_riesgo"].value_counts().to_string())


if __name__ == "__main__":
    main()
