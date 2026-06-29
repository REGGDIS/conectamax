"""Vista Streamlit — Predicción / Riesgo de churn (BORRADOR · Fase 6-7).

Wire-up pendiente: Roberto debe enganchar `render()` en la navegación de `app.py`
(donde hoy aparece "Predicción" como módulo pendiente).

Flujo:
  1. Carga el modelo persistido (models/modelo_churn.pkl).
  2. Lee la vista analítica `comportamiento_cliente` desde SQLite.
  3. Calcula probabilidad de churn y nivel de riesgo (umbrales §29.5).
  4. Muestra KPIs, gráfico y tabla filtrable.
  5. Permite registrar las predicciones en la tabla `predicciones`.

Nota de integración: esta vista NO modifica la lógica de Roberto; consume la misma
vista `comportamiento_cliente` (mismas columnas de config/settings.py).
"""
import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import predictor as pr  # noqa: E402
import registrar_predicciones as rp  # noqa: E402

DB = os.path.join(RAIZ, "data", "conectamax.db")
MODELO = os.path.join(RAIZ, "models", "modelo_churn.pkl")
COLORES = {"bajo": "#2ecc71", "medio": "#f1c40f", "alto": "#e74c3c"}


@st.cache_data(show_spinner=False)
def _cargar_predicciones():
    return rp.generar(DB, MODELO)


def render():
    st.header("🔮 Predicción de churn y nivel de riesgo")
    st.caption("Modelo: árbol de decisión · Umbrales: bajo < 30 % · medio 30–60 % · alto ≥ 60 %")

    if not os.path.exists(MODELO):
        st.warning("No existe el modelo entrenado. Ejecuta `python scripts/train.py` y recarga.")
        return
    if not os.path.exists(DB):
        st.warning("No existe la base de datos. Ejecuta `python scripts/init_db.py` y "
                   "`python scripts/generate_data.py`.")
        return

    pred = _cargar_predicciones()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes evaluados", len(pred))
    c2.metric("Riesgo alto", int((pred["nivel_riesgo"] == "alto").sum()))
    c3.metric("Riesgo medio", int((pred["nivel_riesgo"] == "medio").sum()))
    c4.metric("Riesgo bajo", int((pred["nivel_riesgo"] == "bajo").sum()))

    # Gráfico de distribución
    dist = pred["nivel_riesgo"].value_counts().reindex(["bajo", "medio", "alto"]).reset_index()
    dist.columns = ["nivel_riesgo", "clientes"]
    fig = px.bar(dist, x="nivel_riesgo", y="clientes", color="nivel_riesgo",
                 color_discrete_map=COLORES, title="Distribución de clientes por nivel de riesgo")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla filtrable
    filtro = st.multiselect("Filtrar por nivel de riesgo", ["bajo", "medio", "alto"],
                            default=["alto", "medio"])
    tabla = pred[pred["nivel_riesgo"].isin(filtro)].sort_values("probabilidad_churn", ascending=False)
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    st.download_button("Descargar predicciones (CSV)", tabla.to_csv(index=False),
                       file_name="predicciones.csv", mime="text/csv")

    # Persistencia
    st.divider()
    if st.button("💾 Registrar estas predicciones en la base de datos"):
        n = rp.guardar(DB, pred, version="v1", limpiar=True)
        st.success(f"{n} predicciones registradas en la tabla `predicciones`.")


# Permite ejecutar la vista de forma aislada: streamlit run views/prediccion.py
if __name__ == "__main__":
    render()
