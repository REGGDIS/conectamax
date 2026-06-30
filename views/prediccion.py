"""Vista Streamlit — Prediccion / Riesgo de churn (rev. PR #6).

- Captura errores para que la app no se caiga (punto 13).
- Aclara que usa SQLite y no el CSV cargado (punto 14).
- El registro NO usa limpiar=True por defecto; es opcional via checkbox (punto 12).
- Cache invalidada por mtime de BD y modelo (no bloqueante, ronda 2).
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
from _paths import default_db, default_modelo  # noqa: E402

DB = default_db()
MODELO = default_modelo()
COLORES = {"bajo": "#2ecc71", "medio": "#f1c40f", "alto": "#e74c3c"}


def _firma_archivo(path: str) -> float:
    """mtime del archivo como clave de cache; 0.0 si no existe."""
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


@st.cache_data(show_spinner=False)
def _cargar_predicciones(db_sig: float, modelo_sig: float):
    # db_sig y modelo_sig forman parte de la clave de cache: si cambia la BD o el
    # modelo (su mtime), Streamlit recalcula y no muestra predicciones obsoletas.
    df, bundle = rp.generar(DB, MODELO)
    meta = {"modelo": bundle.get("modelo_nombre", "arbol_decision"),
            "version": bundle.get("version", "v1")} if isinstance(bundle, dict) else {}
    return df, meta


def mostrar_prediccion():
    render()


def render():
    st.header("🔮 Prediccion de churn y nivel de riesgo")
    st.info("Esta vista usa la base de datos SQLite (vista `comportamiento_cliente`), "
            "**no** el CSV cargado manualmente en otros modulos.")
    st.caption("Modelo: arbol de decision · Umbrales: bajo < 30 % · medio 30–60 % · alto ≥ 60 %")

    if not os.path.exists(MODELO):
        st.warning("No existe el modelo entrenado. Ejecuta `python scripts/train.py` y recarga.")
        return
    if not os.path.exists(DB):
        st.warning("No existe la base de datos. Ejecuta `python scripts/init_db.py` y "
                   "`python scripts/generate_data.py`.")
        return

    try:
        pred, meta = _cargar_predicciones(_firma_archivo(DB), _firma_archivo(MODELO))
    except Exception as e:
        st.error(f"No se pudieron calcular las predicciones: {e}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes evaluados", len(pred))
    c2.metric("Riesgo alto", int((pred["nivel_riesgo"] == "alto").sum()))
    c3.metric("Riesgo medio", int((pred["nivel_riesgo"] == "medio").sum()))
    c4.metric("Riesgo bajo", int((pred["nivel_riesgo"] == "bajo").sum()))

    dist = pred["nivel_riesgo"].value_counts().reindex(["bajo", "medio", "alto"]).reset_index()
    dist.columns = ["nivel_riesgo", "clientes"]
    fig = px.bar(dist, x="nivel_riesgo", y="clientes", color="nivel_riesgo",
                 color_discrete_map=COLORES, title="Distribucion de clientes por nivel de riesgo")
    st.plotly_chart(fig, use_container_width=True)

    filtro = st.multiselect("Filtrar por nivel de riesgo", ["bajo", "medio", "alto"],
                            default=["alto", "medio"])
    tabla = pred[pred["nivel_riesgo"].isin(filtro)].sort_values("probabilidad_churn", ascending=False)
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    st.download_button("Descargar predicciones (CSV)", tabla.to_csv(index=False),
                       file_name="predicciones.csv", mime="text/csv")

    st.divider()
    reemplazar = st.checkbox("Reemplazar predicciones anteriores de esta version "
                             "(en vez de agregar al historial)", value=False)
    if st.button("💾 Registrar predicciones en la base de datos"):
        try:
            n = rp.guardar(DB, pred, meta.get("modelo", "arbol_decision"),
                           meta.get("version", "v1"), limpiar=reemplazar)
            st.success(f"{n} predicciones registradas en la tabla `predicciones`.")
        except Exception as e:
            st.error(f"No se pudo registrar: {e}")


if __name__ == "__main__":
    render()
