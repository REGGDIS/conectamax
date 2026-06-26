"""Vista funcional para carga y validacion de datos CSV."""

from collections.abc import Callable

import streamlit as st

from config.settings import CSV_EJEMPLO_PATH
from services.carga_datos_service import cargar_y_validar_csv, construir_estado_carga


def mostrar_carga_datos(limpiar_datos_sesion: Callable[[], None]) -> None:
    """Renderiza la vista de carga sin definir reglas de validacion."""
    st.title("Carga de datos")
    st.write(
        "Carga un archivo CSV con el contrato provisional de clientes o usa "
        "el archivo simulado incluido en el proyecto."
    )

    col_simulado, col_limpiar = st.columns(2)
    with col_simulado:
        if st.button("Usar CSV simulado", type="primary"):
            _procesar_archivo(CSV_EJEMPLO_PATH, CSV_EJEMPLO_PATH.name)
    with col_limpiar:
        if st.button("Limpiar datos de la sesion"):
            limpiar_datos_sesion()
            st.success("Datos de sesion eliminados.")

    uploader_key = f"archivo_csv_{st.session_state.get('uploader_reset_counter', 0)}"
    archivo = st.file_uploader("Selecciona un archivo CSV", type=["csv"], key=uploader_key)
    if archivo is not None and st.button("Procesar archivo seleccionado"):
        _procesar_archivo(archivo, archivo.name)

    _mostrar_estado_actual()


def _procesar_archivo(archivo, nombre_archivo: str) -> None:
    """Carga, valida y actualiza session_state sin reemplazar datos validos por invalidos."""
    df, resultado = cargar_y_validar_csv(archivo)
    estado_actualizado = construir_estado_carga(st.session_state.to_dict(), df, resultado, nombre_archivo)
    for clave, valor in estado_actualizado.items():
        st.session_state[clave] = valor

    if resultado["es_valido"] and df is not None:
        st.success("Archivo cargado y validado correctamente.")
    else:
        st.error(
            "El archivo tiene errores estructurales. Los datos activos validos anteriores se conservaron."
        )


def _mostrar_estado_actual() -> None:
    """Presenta datos cargados, errores, advertencias y resumen de calidad."""
    resultado = st.session_state.get("resultado_validacion")
    df = st.session_state.get("clientes_df")

    st.subheader("Estado de la carga")
    if st.session_state.get("ultimo_archivo_procesado"):
        st.write(
            f"Ultimo archivo procesado: `{st.session_state['ultimo_archivo_procesado']}`"
        )
    else:
        st.info("Aun no hay archivos procesados.")

    if st.session_state.get("nombre_archivo_activo"):
        st.write(f"Archivo activo: `{st.session_state['nombre_archivo_activo']}`")
    else:
        st.write("Archivo activo: ninguno.")

    if resultado:
        if resultado["es_valido"]:
            st.success("Resultado general: estructura valida.")
        else:
            st.error("Resultado general: estructura invalida.")

        _mostrar_lista("Errores estructurales", resultado.get("errores", []), "error")
        _mostrar_lista("Advertencias de calidad", resultado.get("advertencias", []), "warning")
        _mostrar_resumen(resultado.get("resumen", {}))

    if st.session_state.get("datos_cargados") and df is not None:
        st.subheader("Vista previa")
        st.write(f"Filas: `{len(df)}`")
        st.write(f"Columnas: `{len(df.columns)}`")
        st.dataframe(df.head(), use_container_width=True)
    else:
        st.info("No hay un DataFrame valido cargado en la sesion.")


def _mostrar_lista(titulo: str, items: list[str], tipo: str) -> None:
    """Muestra una lista de mensajes usando componentes de Streamlit."""
    st.subheader(titulo)
    if not items:
        st.write("Sin registros.")
        return

    for item in items:
        if tipo == "error":
            st.error(item)
        elif tipo == "warning":
            st.warning(item)
        else:
            st.write(item)


def _mostrar_resumen(resumen: dict) -> None:
    """Muestra metricas resumidas entregadas por los validadores."""
    st.subheader("Resumen de calidad")
    col_filas, col_columnas, col_duplicados = st.columns(3)
    col_filas.metric("Filas", resumen.get("filas", 0))
    col_columnas.metric("Columnas", resumen.get("columnas", 0))
    col_duplicados.metric("Duplicados de ID", resumen.get("duplicados_id", 0))

    faltantes = resumen.get("valores_faltantes_por_columna", {})
    st.write("Valores faltantes por columna")
    if faltantes:
        st.dataframe(
            [{"columna": columna, "faltantes": total} for columna, total in faltantes.items()],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No se encontraron valores faltantes.")
