"""Punto de entrada de la aplicacion ConectaMax."""

import streamlit as st

from config.settings import APP_NAME
from views.analisis_view import mostrar_analisis
from views.carga_datos_view import mostrar_carga_datos
from views.clientes_view import mostrar_clientes
from views.dashboard_view import mostrar_dashboard


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
    """Muestra la pantalla inicial de la fase actual."""
    st.title(APP_NAME)
    st.info(
        "Fase funcional actual: carga de archivos CSV, validacion basica, "
        "consulta de clientes, dashboard, analisis descriptivo y preparacion de datos."
    )
    st.write("Prediccion se implementara en una fase posterior.")


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
        mostrar_modulo_pendiente("Prediccion")


if __name__ == "__main__":
    main()
