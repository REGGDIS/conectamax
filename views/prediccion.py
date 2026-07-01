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
from utils.ui_helpers import msg_advertencia, msg_error, msg_exito, msg_info  # noqa: E402

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


def calcular_porcentaje_riesgo_alto(pred: pd.DataFrame) -> float:
    total = len(pred)
    if total == 0 or "nivel_riesgo" not in pred.columns:
        return 0.0
    return float((pred["nivel_riesgo"] == "alto").sum() / total * 100)


def calcular_probabilidad_promedio_churn(pred: pd.DataFrame) -> float:
    if pred.empty or "probabilidad_churn" not in pred.columns:
        return 0.0
    probabilidades = pd.to_numeric(pred["probabilidad_churn"], errors="coerce").dropna()
    if probabilidades.empty:
        return 0.0
    return float(probabilidades.mean() * 100)


def formatear_porcentaje(valor: float | int) -> str:
    return f"{float(valor):.2f} %".replace(".", ",")


def render():
    st.title("Prediccion de churn")
    st.markdown(
        "Probabilidad de abandono y nivel de riesgo de cada cliente, "
        "calculados con el modelo de arbol de decision entrenado sobre la base de datos local."
    )
    st.info(
        "Esta vista usa directamente la base de datos **SQLite** "
        "(vista `comportamiento_cliente`), **no** el CSV que puedas haber cargado "
        "en el modulo Carga de datos.",
        icon="ℹ️",
    )

    with st.expander("Como interpretar las predicciones"):
        st.markdown(
            "**Probabilidad de churn:** valor entre 0 % y 100 % que estima la "
            "probabilidad de que el cliente abandone el servicio segun el modelo entrenado.  \n"
            "**Niveles de riesgo** (umbrales del Plan v3.2 §29.5):  \n"
            "- 🟢 **Bajo** — probabilidad < 30 %: baja probabilidad estimada de abandono.  \n"
            "- 🟡 **Medio** — 30 % ≤ probabilidad < 60 %: requiere seguimiento preventivo.  \n"
            "- 🔴 **Alto** — probabilidad ≥ 60 %: cliente prioritario para retención.  \n\n"
            "El modelo es un **arbol de decision** (max_depth=4, class_weight='balanced'). "
            "Las predicciones son estimaciones estadisticas, no certezas."
        )

    if not os.path.exists(MODELO):
        msg_advertencia(
            "No existe el modelo entrenado.",
            causa=f"No se encontro el archivo `{MODELO}`.",
            accion="Ejecuta `python scripts/train.py` desde la raiz del proyecto y recarga esta pagina.",
        )
        return
    if not os.path.exists(DB):
        msg_advertencia(
            "No existe la base de datos.",
            causa=f"No se encontro el archivo `{DB}`.",
            accion="Ejecuta `python scripts/init_db.py` y luego `python scripts/generate_data.py`.",
        )
        return

    try:
        pred, meta = _cargar_predicciones(_firma_archivo(DB), _firma_archivo(MODELO))
    except Exception as e:
        msg_error(
            "No se pudieron calcular las predicciones.",
            causa=str(e),
            accion="Verifica que el modelo y la base de datos sean validos y vuelve a recargar.",
        )
        return

    st.subheader("Resumen de riesgo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes evaluados", len(pred))
    c2.metric("Riesgo alto", int((pred["nivel_riesgo"] == "alto").sum()))
    c3.metric("Riesgo medio", int((pred["nivel_riesgo"] == "medio").sum()))
    c4.metric("Riesgo bajo", int((pred["nivel_riesgo"] == "bajo").sum()))
    c5, c6 = st.columns(2)
    c5.metric(
        "Porcentaje en riesgo alto",
        formatear_porcentaje(calcular_porcentaje_riesgo_alto(pred)),
    )
    c6.metric(
        "Probabilidad promedio de churn",
        formatear_porcentaje(calcular_probabilidad_promedio_churn(pred)),
    )

    dist = pred["nivel_riesgo"].value_counts().reindex(["bajo", "medio", "alto"]).reset_index()
    dist.columns = ["nivel_riesgo", "clientes"]
    fig = px.bar(
        dist,
        x="nivel_riesgo",
        y="clientes",
        color="nivel_riesgo",
        color_discrete_map=COLORES,
        title="Distribucion de clientes por nivel de riesgo",
        labels={"nivel_riesgo": "Nivel de riesgo", "clientes": "Clientes"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tabla de predicciones")
    filtro = st.multiselect(
        "Filtrar por nivel de riesgo",
        ["bajo", "medio", "alto"],
        default=["alto", "medio"],
        help="Muestra solo los clientes con los niveles de riesgo seleccionados.",
    )
    tabla = pred[pred["nivel_riesgo"].isin(filtro)].sort_values("probabilidad_churn", ascending=False)

    if tabla.empty:
        msg_info(
            "No hay clientes que coincidan con los niveles de riesgo seleccionados.",
            accion="Selecciona al menos un nivel de riesgo en el filtro de arriba.",
        )
    else:
        st.dataframe(tabla, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar predicciones (CSV)",
            tabla.to_csv(index=False),
            file_name="predicciones.csv",
            mime="text/csv",
        )

    st.divider()
    st.subheader("Registrar en la base de datos")
    st.markdown(
        "Guarda las predicciones actuales en la tabla `predicciones` de SQLite. "
        "Puedes **acumular historial** (opcion por defecto) o **reemplazar** "
        "las predicciones anteriores de esta misma version del modelo."
    )

    reemplazar = st.checkbox(
        "Reemplazar predicciones anteriores de esta version (en vez de agregar al historial)",
        value=False,
    )
    if reemplazar:
        msg_advertencia(
            "Esta accion borrara las predicciones existentes de esta version antes de insertar las nuevas.",
            causa="La opcion 'Reemplazar' elimina los registros de la tabla `predicciones` "
                  f"con modelo='{meta.get('modelo', 'arbol_decision')}' y "
                  f"version='{meta.get('version', 'v1')}' antes de insertar.",
            accion="Si solo quieres agregar al historial sin borrar nada, desmarca esta opcion.",
        )

    if st.button("Registrar predicciones en la base de datos"):
        try:
            n = rp.guardar(
                DB,
                pred,
                meta.get("modelo", "arbol_decision"),
                meta.get("version", "v1"),
                limpiar=reemplazar,
            )
            msg_exito(
                f"{n} predicciones registradas en la tabla `predicciones`.",
                causa=f"Modelo: {meta.get('modelo', 'arbol_decision')} · "
                      f"Version: {meta.get('version', 'v1')}.",
                accion="Puedes volver a registrar en cualquier momento; el historial se acumula salvo que uses 'Reemplazar'.",
            )
        except Exception as e:
            msg_error(
                "No se pudieron registrar las predicciones.",
                causa=str(e),
                accion="Verifica que la base de datos sea accesible y vuelve a intentarlo.",
            )


if __name__ == "__main__":
    render()
