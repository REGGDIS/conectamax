"""Entrena, evalua y persiste el modelo de churn (Spec 04, rev. PR #6).

Cambios del review:
- Excluye `segmento` de las features para evitar fuga conceptual (punto 7).
- Imputacion dentro del Pipeline (punto 8).
- Persiste metadatos: pipeline, features, clase positiva, version, fecha, metricas.
- La clase positiva se obtiene de classes_ (punto 10).

Uso: python scripts/train.py [--db ...] [--out models/modelo_churn.pkl]
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from _paths import default_db, default_modelo

SEED = 42
TARGET = "abandono"
# Lista EXPLICITA de variables predictoras (no bloqueante, ronda 2): documenta el
# contrato del modelo y evita que columnas nuevas de la vista entren sin querer.
# Se excluyen a proposito: id_cliente, nombre, segmento (fuga conceptual) y el target.
CATEGORICAS = ["ciudad", "tipo_contrato", "plan", "region"]
NUMERICAS = ["antiguedad_meses", "monto_mensual", "reclamos_ultimos_6_meses",
             "pagos_atrasados", "dias_sin_uso", "satisfaccion", "edad",
             "cantidad_servicios"]
FEATURES = CATEGORICAS + NUMERICAS
VERSION = "v1"


def cargar(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        return pd.read_sql("SELECT * FROM comportamiento_cliente", con)
    finally:
        con.close()


def construir_pipeline(modelo, categoricas, numericas):
    cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                    ("oh", OneHotEncoder(handle_unknown="ignore"))])
    num = Pipeline([("imp", SimpleImputer(strategy="median")),
                    ("sc", StandardScaler())])
    pre = ColumnTransformer([("cat", cat, categoricas), ("num", num, numericas)])
    return Pipeline([("pre", pre), ("clf", modelo)])


def evaluar(nombre, pipe, Xte, yte, base):
    p = pipe.predict(Xte)
    met = {"accuracy": round(accuracy_score(yte, p), 4),
           "recall": round(recall_score(yte, p), 4),
           "precision": round(precision_score(yte, p), 4),
           "f1": round(f1_score(yte, p), 4)}
    print(f"\n=== {nombre} ===")
    print(f"  Accuracy : {met['accuracy']:.3f}  (linea base {base:.3f})")
    print(f"  Recall   : {met['recall']:.3f}  (clase churn)")
    print(f"  Precision: {met['precision']:.3f}")
    print(f"  F1       : {met['f1']:.3f}")
    print("  Matriz de confusion:", confusion_matrix(yte, p).tolist())
    return met


def entrenar(db_path: str, out_path: str):
    df = cargar(db_path)
    faltan = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if faltan:
        raise ValueError(f"La vista no expone columnas requeridas: {faltan}")
    y = df[TARGET]
    X = df[FEATURES]  # seleccion explicita de predictoras
    categoricas = list(CATEGORICAS)
    numericas = list(NUMERICAS)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    base = max(y_te.mean(), 1 - y_te.mean())
    print(f"Registros: {len(df)} | Tasa churn: {y.mean():.3f} | Linea base: {base:.3f}")
    print(f"Features ({len(X.columns)}): {list(X.columns)}")

    arbol = construir_pipeline(
        DecisionTreeClassifier(max_depth=4, min_samples_leaf=30,
                               class_weight="balanced", random_state=SEED),
        categoricas, numericas).fit(X_tr, y_tr)
    m_arbol = evaluar("Arbol de decision (obligatorio)", arbol, X_te, y_te, base)

    reglog = construir_pipeline(
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED),
        categoricas, numericas).fit(X_tr, y_tr)
    m_reglog = evaluar("Regresion logistica (deseable)", reglog, X_te, y_te, base)

    clases = list(arbol.classes_)
    bundle = {
        "pipeline": arbol,
        "modelo_nombre": "arbol_decision",
        "version": VERSION,
        "features": list(X.columns),
        "categoricas": categoricas,
        "clase_positiva": 1,
        "indice_clase_positiva": clases.index(1),
        "clases": clases,
        "fecha_entrenamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metricas": {"arbol": m_arbol, "regresion_logistica": m_reglog,
                     "linea_base": round(base, 4)},
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    joblib.dump(bundle, out_path)
    print(f"\nModelo + metadatos guardados: {out_path}")
    print(f"Supera linea base: {'SI' if m_arbol['accuracy'] > base else 'NO'} (arbol)")
    return {"arbol": m_arbol, "reglog": m_reglog, "base": base}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=default_db())
    ap.add_argument("--out", default=default_modelo())
    a = ap.parse_args()
    entrenar(a.db, a.out)


if __name__ == "__main__":
    main()
