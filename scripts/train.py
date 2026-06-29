"""Entrena, evalua y persiste el modelo de churn (Spec 04).

Lee la vista `comportamiento_cliente` de data/conectamax.db, entrena un arbol de
decision (obligatorio) y una regresion logistica (deseable), evalua ambos contra
una linea base (clase mayoritaria) y guarda el arbol en models/modelo_churn.pkl.

Reglas del Plan v3.2 §29: split 80/20, stratify=y, random_state=42, Pipeline que
ajusta el preprocesamiento solo con el conjunto de entrenamiento (anti-fuga).

Uso:
    python scripts/train.py [--db data/conectamax.db] [--out models/modelo_churn.pkl]
"""
from __future__ import annotations

import argparse
import os
import sqlite3

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 42
ID_COLS = ["id_cliente", "nombre"]
TARGET = "abandono"
CATEGORICAS = ["ciudad", "tipo_contrato", "plan", "region", "segmento"]


def cargar(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM comportamiento_cliente", con)
    con.close()
    return df


def construir_pipeline(modelo, numericas):
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ("num", StandardScaler(), numericas),
    ])
    return Pipeline([("pre", pre), ("clf", modelo)])


def evaluar(nombre, pipe, Xte, yte, base):
    p = pipe.predict(Xte)
    met = {
        "accuracy": accuracy_score(yte, p),
        "recall": recall_score(yte, p),
        "precision": precision_score(yte, p),
        "f1": f1_score(yte, p),
    }
    print(f"\n=== {nombre} ===")
    print(f"  Accuracy : {met['accuracy']:.3f}  (linea base {base:.3f})")
    print(f"  Recall   : {met['recall']:.3f}  (clase churn)")
    print(f"  Precision: {met['precision']:.3f}")
    print(f"  F1       : {met['f1']:.3f}")
    print("  Matriz de confusion [ [TN FP] [FN TP] ]:")
    print("  ", confusion_matrix(yte, p).tolist())
    return met


def entrenar(db_path: str, out_path: str):
    df = cargar(db_path)
    y = df[TARGET]
    X = df.drop(columns=[c for c in ID_COLS + [TARGET] if c in df.columns])
    numericas = [c for c in X.columns if c not in CATEGORICAS]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    base = max(y_te.mean(), 1 - y_te.mean())
    print(f"Registros: {len(df)} | Tasa churn: {y.mean():.3f} | Linea base: {base:.3f}")

    arbol = construir_pipeline(
        DecisionTreeClassifier(max_depth=4, min_samples_leaf=30,
                               class_weight="balanced", random_state=SEED), numericas)
    arbol.fit(X_tr, y_tr)
    m_arbol = evaluar("Arbol de decision (obligatorio)", arbol, X_te, y_te, base)

    reglog = construir_pipeline(
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED), numericas)
    reglog.fit(X_tr, y_tr)
    m_reglog = evaluar("Regresion logistica (deseable)", reglog, X_te, y_te, base)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    joblib.dump(arbol, out_path)
    print(f"\nModelo guardado (arbol): {out_path}")
    print(f"Comparacion F1: arbol={m_arbol['f1']:.3f} | reglog={m_reglog['f1']:.3f}")
    print(f"Supera linea base: {'SI' if m_arbol['accuracy'] > base else 'NO'} (arbol)")
    return {"arbol": m_arbol, "reglog": m_reglog, "base": base}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(RAIZ, "data", "conectamax.db"))
    ap.add_argument("--out", default=os.path.join(RAIZ, "models", "modelo_churn.pkl"))
    a = ap.parse_args()
    entrenar(a.db, a.out)


if __name__ == "__main__":
    main()
