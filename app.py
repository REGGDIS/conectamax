"""Punto de entrada de la aplicacion ConectaMax."""

import streamlit as st

from config.settings import APP_NAME
from views.carga_datos_view import mostrar_carga_datos
from views.clientes_view import mostrar_clientes


SESSION_DEFAULTS = {
    "clientes_df": None,
    "datos_cargados": False,
    "nombre_archivo_activo": None,
    "ultimo_archivo_procesado": None,
    "resultado_validacion": None,
    "uploader_reset_counter": 0,
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
        "manejo centralizado de datos y consulta de clientes."
    )
    st.write("Analisis y Prediccion se implementaran en fases posteriores.")


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
        ["Inicio", "Carga de datos", "Clientes", "Analisis", "Prediccion"],
    )

    if opcion == "Inicio":
        mostrar_inicio()
    elif opcion == "Carga de datos":
        mostrar_carga_datos(limpiar_datos_sesion)
    elif opcion == "Clientes":
        mostrar_clientes()
    elif opcion == "Analisis":
        mostrar_modulo_pendiente("Analisis")
    elif opcion == "Prediccion":
        mostrar_modulo_pendiente("Prediccion")


if __name__ == "__main__":
    main()
