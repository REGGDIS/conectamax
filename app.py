"""Punto de entrada de la aplicacion ConectaMax."""

import streamlit as st

from config.settings import APP_NAME
from utils.ui_helpers import msg_info
from views.analisis_view import mostrar_analisis
from views.carga_datos_view import mostrar_carga_datos
from views.clientes_view import mostrar_clientes
from views.dashboard_view import mostrar_dashboard
from views.prediccion import mostrar_prediccion


SESSION_DEFAULTS = {
    "clientes_df": None,
    "datos_cargados": False,
    "nombre_archivo_activo": None,
    "ultimo_archivo_procesado": None,
    "resultado_validacion": None,
    "uploader_reset_counter": 0,
    "clientes_df_limpio": None,
    "reporte_limpieza": None,
    "datos_preparados": False,
}


def inicializar_estado() -> None:
    """Inicializa una unica fuente de estado para datos cargados."""
    for clave, valor in SESSION_DEFAULTS.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


def limpiar_datos_sesion() -> None:
    """Elimina de session_state los datos cargados y su validacion."""
    contador_actual = st.session_state.get("uploader_reset_counter", 0)
    for clave, valor in SESSION_DEFAULTS.items():
        st.session_state[clave] = valor
    st.session_state["uploader_reset_counter"] = contador_actual + 1


def mostrar_inicio() -> None:
    """Muestra la pantalla de bienvenida con descripcion y orientacion al usuario."""
    st.title(APP_NAME)
    st.markdown(
        "CRM analitico academico para **ConectaMax Telecom S.A.** "
        "Centraliza la informacion de clientes y predice el riesgo de abandono (churn) "
        "usando un modelo de arbol de decision entrenado sobre datos sinteticos."
    )

    st.subheader("Modulos disponibles")
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.markdown("- **Carga de datos** — importa y valida un CSV de clientes.")
        st.markdown("- **Clientes** — lista, busca y filtra clientes; ficha individual.")
        st.markdown("- **Dashboard** — KPIs e indicadores clave del negocio.")
    with col_der:
        st.markdown("- **Analisis** — tablas resumen y conclusiones descriptivas.")
        st.markdown("- **Prediccion** — probabilidad de churn y nivel de riesgo por cliente.")

    msg_info(
        "Por donde empezar",
        causa="Los datos sinteticos ya estan cargados en la base de datos local (SQLite).",
        accion=(
            "Explora **Clientes** o **Dashboard** para ver la informacion existente. "
            "Si tienes un CSV propio, empieza por **Carga de datos**. "
            "Para ver las predicciones de abandono, accede a **Prediccion**."
        ),
    )


def mostrar_modulo_pendiente(nombre: str) -> None:
    """Muestra un mensaje temporal para modulos no implementados."""
    st.title(nombre)
    st.warning("Modulo pendiente para una fase posterior.")


def main() -> None:
    """Configura la navegacion inicial de Streamlit."""
    st.set_page_config(page_title=APP_NAME, layout="wide")
    inicializar_estado()

    st.sidebar.title(APP_NAME)
    opcion = st.sidebar.radio(
        "Navegacion",
        ["Inicio", "Carga de datos", "Clientes", "Dashboard", "Analisis", "Prediccion"],
    )

    if opcion == "Inicio":
        mostrar_inicio()
    elif opcion == "Carga de datos":
        mostrar_carga_datos(limpiar_datos_sesion)
    elif opcion == "Clientes":
        mostrar_clientes()
    elif opcion == "Dashboard":
        mostrar_dashboard()
    elif opcion == "Analisis":
        mostrar_analisis()
    elif opcion == "Prediccion":
        mostrar_prediccion()


if __name__ == "__main__":
    main()
