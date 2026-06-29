"""Carga el modelo de churn y clasifica el riesgo (Spec 05, rev. PR #6).

Robustez del review:
- Valida modelo inexistente o corrupto (punto 9).
- Valida DataFrame vacio y columnas esperadas (punto 9).
- Obtiene la probabilidad de la clase positiva via classes_ (punto 10).
"""
from __future__ import annotations

import os

import joblib
import pandas as pd

from _paths import default_modelo

UMBRAL_BAJO = 0.30
UMBRAL_ALTO = 0.60
ID_COLS = ["id_cliente", "nombre"]
TARGET = "abandono"


def nivel_riesgo(prob: float) -> str:
    if prob < UMBRAL_BAJO:
        return "bajo"
    if prob < UMBRAL_ALTO:
        return "medio"
    return "alto"


def cargar_modelo(path: str | None = None):
    path = path or default_modelo()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No existe el modelo '{path}'. Ejecuta primero: python scripts/train.py")
    try:
        bundle = joblib.load(path)
    except Exception as e:  # corrupto / ilegible
        raise ValueError(f"No se pudo cargar el modelo '{path}': {e}")
    if isinstance(bundle, dict) and "pipeline" not in bundle:
        raise ValueError("El modelo cargado no tiene la clave 'pipeline'.")
    return bundle


def _pipeline_e_indice(bundle):
    pipeline = bundle["pipeline"] if isinstance(bundle, dict) else bundle
    if isinstance(bundle, dict) and "indice_clase_positiva" in bundle:
        return pipeline, bundle["indice_clase_positiva"]
    clases = list(getattr(pipeline, "classes_", [0, 1]))
    return pipeline, (clases.index(1) if 1 in clases else len(clases) - 1)


def predecir(df_clientes: pd.DataFrame, bundle=None) -> pd.DataFrame:
    if df_clientes is None or len(df_clientes) == 0:
        raise ValueError("El DataFrame de entrada esta vacio.")
    if "id_cliente" not in df_clientes.columns:
        raise ValueError("Falta la columna obligatoria 'id_cliente'.")
    bundle = bundle if bundle is not None else cargar_modelo()
    pipeline, idx = _pipeline_e_indice(bundle)

    X = df_clientes.drop(columns=[c for c in ID_COLS + [TARGET] if c in df_clientes.columns],
                         errors="ignore")
    feats = bundle.get("features") if isinstance(bundle, dict) else None
    if feats:
        faltan = [c for c in feats if c not in X.columns]
        if faltan:
            raise ValueError(f"Faltan columnas requeridas por el modelo: {faltan}")
        X = X[feats]

    probs = pipeline.predict_proba(X)[:, idx]
    return pd.DataFrame({
        "id_cliente": df_clientes["id_cliente"].values,
        "probabilidad_churn": probs.round(4),
        "nivel_riesgo": [nivel_riesgo(p) for p in probs],
    })
