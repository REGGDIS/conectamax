"""Vista funcional para carga y validacion de datos CSV."""

from collections.abc import Callable

import streamlit as st

from config.settings import COLUMNAS_OBLIGATORIAS, COLUMNAS_OPCIONALES, CSV_EJEMPLO_PATH
from services.carga_datos_service import cargar_y_validar_csv, construir_estado_carga
from services.limpieza_service import preparar_datos
from utils.ui_helpers import msg_error, msg_exito, msg_info


def mostrar_carga_datos(limpiar_datos_sesion: Callable[[], None]) -> None:
    """Renderiza la vista de carga sin definir reglas de validacion."""
    st.title("Carga de datos")
    st.markdown(
        "Importa un archivo CSV de clientes para validarlo, revisar su calidad, "
        "limpiarlo y preparar una version lista para descargar. "
        "Los modulos **Clientes**, **Dashboard** y **Analisis** utilizan la base "
        "de datos SQLite mediante la vista `comportamiento_cliente`. "
        "El modulo **Prediccion** tambien utiliza SQLite y el modelo entrenado, "
        "independientemente del CSV que cargues aqui."
    )

    with st.expander("Ver formato CSV esperado"):
        st.markdown("**Columnas obligatorias** (el archivo debe contenerlas todas):")
        st.code(", ".join(COLUMNAS_OBLIGATORIAS))
        st.markdown("**Columnas opcionales** (se usan si estan presentes):")
        st.code(", ".join(COLUMNAS_OPCIONALES))
        st.markdown(
            "- La columna `abandono` acepta solo los valores `0` (permanece) o `1` (abandono).  \n"
            "- La columna `satisfaccion` debe estar en el rango 1–5.  \n"
            "- Puedes usar el archivo simulado incluido como referencia de formato."
        )

    col_simulado, col_limpiar = st.columns(2)
    with col_simulado:
        if st.button("Usar CSV simulado", type="primary"):
            _procesar_archivo(CSV_EJEMPLO_PATH, CSV_EJEMPLO_PATH.name)
    with col_limpiar:
        if st.button("Limpiar datos de la sesion"):
            limpiar_datos_sesion()
            msg_exito("Datos de sesion eliminados.", accion="Puedes cargar un nuevo archivo cuando quieras.")

    uploader_key = f"archivo_csv_{st.session_state.get('uploader_reset_counter', 0)}"
    archivo = st.file_uploader("Selecciona un archivo CSV", type=["csv"], key=uploader_key)
    if archivo is not None and st.button("Procesar archivo seleccionado"):
        _procesar_archivo(archivo, archivo.name)

    _mostrar_estado_actual()
    _mostrar_preparacion_avanzada()


def _procesar_archivo(archivo, nombre_archivo: str) -> None:
    """Carga, valida y actualiza session_state sin reemplazar datos validos por invalidos."""
    with st.spinner(f"Procesando '{nombre_archivo}'..."):
        df, resultado = cargar_y_validar_csv(archivo)
        estado_actualizado = construir_estado_carga(st.session_state.to_dict(), df, resultado, nombre_archivo)
    for clave, valor in estado_actualizado.items():
        st.session_state[clave] = valor

    if resultado["es_valido"] and df is not None:
        filas = resultado.get("resumen", {}).get("filas", len(df))
        columnas = resultado.get("resumen", {}).get("columnas", len(df.columns))
        msg_exito(
            f"'{nombre_archivo}' cargado correctamente.",
            causa=f"{filas} filas · {columnas} columnas detectadas.",
            accion="Explora la vista previa a continuacion o pasa a 'Preparacion avanzada' para limpiar los datos.",
        )
    else:
        msg_error(
            f"'{nombre_archivo}' no se pudo cargar.",
            causa="El archivo tiene errores estructurales que impiden su uso.",
            accion="Revisa los errores detallados a continuacion, corrige el archivo y vuelve a cargarlo. Los datos validos cargados anteriormente se conservan.",
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
        msg_info(
            "Aun no hay archivos procesados.",
            accion="Usa el boton 'Usar CSV simulado' o carga tu propio archivo .csv.",
        )

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
        msg_info(
            "No hay datos cargados en la sesion.",
            causa="Aun no se ha procesado ningun archivo CSV valido.",
            accion="Carga un archivo CSV usando los controles de arriba.",
        )


def _mostrar_preparacion_avanzada() -> None:
    """Permite ejecutar limpieza avanzada sin modificar el dataset original."""
    st.subheader("Preparacion avanzada")
    df = st.session_state.get("clientes_df")
    if not st.session_state.get("datos_cargados") or df is None or df.empty:
        msg_info(
            "No hay datos listos para preparar.",
            causa="La preparacion avanzada requiere un archivo CSV valido ya cargado.",
            accion="Primero carga y valida un archivo CSV en la seccion superior.",
        )
        return

    st.write("El dataset original cargado se conservara sin modificaciones.")
    if st.button("Preparar datos"):
        with st.spinner("Aplicando limpieza y generando variables derivadas..."):
            df_limpio, reporte = preparar_datos(df)
        st.session_state["clientes_df_limpio"] = df_limpio
        st.session_state["reporte_limpieza"] = reporte
        st.session_state["datos_preparados"] = True
        msg_exito(
            "Datos preparados correctamente.",
            causa=f"{reporte.get('filas_finales', len(df_limpio))} filas utiles tras la limpieza.",
            accion="Revisa el reporte a continuacion y descarga el CSV limpio si lo necesitas.",
        )

    reporte = st.session_state.get("reporte_limpieza")
    df_limpio = st.session_state.get("clientes_df_limpio")
    if st.session_state.get("datos_preparados") and reporte is not None and df_limpio is not None:
        _mostrar_reporte_limpieza(reporte)
        st.subheader("Vista previa del dataset limpio")
        st.dataframe(df_limpio.head(), use_container_width=True)
        st.download_button(
            "Descargar CSV limpio",
            data=df_limpio.to_csv(index=False).encode("utf-8"),
            file_name="clientes_preparados.csv",
            mime="text/csv",
        )


def _mostrar_reporte_limpieza(reporte: dict) -> None:
    """Muestra indicadores y detalles del reporte de limpieza."""
    st.subheader("Reporte de limpieza")
    col_ini, col_fin, col_elim, col_dup = st.columns(4)
    col_ini.metric("Filas iniciales", reporte.get("filas_iniciales", 0))
    col_fin.metric("Filas finales", reporte.get("filas_finales", 0))
    col_elim.metric("Filas eliminadas", reporte.get("filas_eliminadas", 0))
    col_dup.metric("Duplicados eliminados", reporte.get("duplicados_eliminados", 0))

    detalles = [
        {
            "indicador": "IDs vacios eliminados",
            "valor": reporte.get("ids_vacios_eliminados", 0),
        },
        {
            "indicador": "Abandono invalido eliminado",
            "valor": reporte.get("abandono_invalido_eliminado", 0),
        },
    ]
    st.dataframe(detalles, use_container_width=True, hide_index=True)

    _mostrar_dict_reporte("Valores no convertibles", reporte.get("valores_no_convertibles", {}))
    _mostrar_dict_reporte("Valores fuera de rango", reporte.get("valores_fuera_de_rango", {}))
    _mostrar_dict_reporte("Valores imputados", reporte.get("valores_imputados", {}))
    columnas_derivadas = reporte.get("columnas_derivadas", [])
    st.write("Columnas derivadas")
    st.write(", ".join(columnas_derivadas) if columnas_derivadas else "Sin columnas derivadas.")


def _mostrar_dict_reporte(titulo: str, valores: dict) -> None:
    """Muestra un diccionario del reporte como tabla simple."""
    st.write(titulo)
    registros = [{"columna": columna, "valor": valor} for columna, valor in valores.items()]
    if registros:
        st.dataframe(registros, use_container_width=True, hide_index=True)
    else:
        st.write("Sin registros.")


def _mostrar_lista(titulo: str, items: list[str], tipo: str) -> None:
    """Muestra una lista de mensajes usando componentes de Streamlit."""
    st.subheader(titulo)
    if not items:
        st.write("Sin problemas detectados.")
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
