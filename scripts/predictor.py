"""Carga el modelo de churn y clasifica el riesgo por cliente (Spec 05).

Aplica los umbrales del Plan v3.2 §29.5 sobre la probabilidad estimada:
  < 30 %  -> bajo   |   30-60 % -> medio   |   >= 60 % -> alto
"""
from __future__ import annotations

import os

import joblib
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_PATH = os.path.join(RAIZ, "models", "modelo_churn.pkl")
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


def cargar_modelo(path: str = MODELO_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No existe el modelo '{path}'. Ejecuta primero: python scripts/train.py")
    return joblib.load(path)


def predecir(df_clientes: pd.DataFrame, modelo=None) -> pd.DataFrame:
    """Recibe filas de `comportamiento_cliente` y devuelve
    id_cliente, probabilidad_churn y nivel_riesgo."""
    modelo = modelo if modelo is not None else cargar_modelo()
    X = df_clientes.drop(columns=[c for c in ID_COLS + [TARGET] if c in df_clientes.columns])
    probs = modelo.predict_proba(X)[:, 1]
    return pd.DataFrame({
        "id_cliente": df_clientes["id_cliente"].values,
        "probabilidad_churn": probs.round(4),
        "nivel_riesgo": [nivel_riesgo(p) for p in probs],
    })
