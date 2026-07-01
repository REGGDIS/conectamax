"""Pruebas de indicadores globales de la vista Prediccion."""

import pandas as pd
import pytest

from views.prediccion import (
    calcular_porcentaje_riesgo_alto,
    calcular_probabilidad_promedio_churn,
    formatear_porcentaje,
)


def test_indicadores_globales_calculo_normal() -> None:
    pred = pd.DataFrame(
        {
            "nivel_riesgo": ["alto", "medio", "alto", "bajo"],
            "probabilidad_churn": [0.80, 0.40, 0.60, 0.20],
        }
    )

    assert calcular_porcentaje_riesgo_alto(pred) == 50.0
    assert calcular_probabilidad_promedio_churn(pred) == pytest.approx(50.0)
    assert formatear_porcentaje(calcular_porcentaje_riesgo_alto(pred)) == "50,00 %"


def test_indicadores_globales_dataframe_vacio() -> None:
    pred = pd.DataFrame(columns=["nivel_riesgo", "probabilidad_churn"])

    assert calcular_porcentaje_riesgo_alto(pred) == 0.0
    assert calcular_probabilidad_promedio_churn(pred) == 0.0
    assert formatear_porcentaje(calcular_probabilidad_promedio_churn(pred)) == "0,00 %"


def test_probabilidad_promedio_sin_columna_probabilidad_churn() -> None:
    pred = pd.DataFrame({"nivel_riesgo": ["alto", "medio", "bajo"]})

    assert calcular_probabilidad_promedio_churn(pred) == 0.0


def test_porcentaje_riesgo_alto_con_cero_clientes() -> None:
    pred = pd.DataFrame(columns=["nivel_riesgo"])

    assert calcular_porcentaje_riesgo_alto(pred) == 0.0
    assert formatear_porcentaje(calcular_porcentaje_riesgo_alto(pred)) == "0,00 %"
