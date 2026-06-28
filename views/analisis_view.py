"""Vista complementaria de analisis descriptivo."""

import pandas as pd
import streamlit as st

from config.settings import ETIQUETAS_COLUMNAS_ANALISIS
from services.analisis_service import (
    calcular_abandono_por_categoria,
    calcular_dias_sin_uso_promedio_por_abandono,
    calcular_pagos_atrasados_promedio_por_abandono,
    calcular_reclamos_promedio_por_abandono,
    calcular_satisfaccion_promedio_por_abandono,
)


def mostrar_analisis() -> None:
    """Renderiza tablas resumen y conclusiones descriptivas simples."""
    st.title("Análisis")
    st.write("Resumen descriptivo complementario al dashboard, sin inferencias causales.")

    df = st.session_state.get("clientes_df")
    if not st.session_state.get("datos_cargados") or df is None or df.empty:
        st.info("No hay datos cargados para analizar.")
        st.write("Ve al modulo `Carga de datos` y carga un CSV valido para continuar.")
        return

    st.write(f"Archivo activo: `{st.session_state.get('nombre_archivo_activo', 'No informado')}`")
    st.write(f"Clientes analizados: `{len(df)}`")

    resumen_contrato = calcular_abandono_por_categoria(df, "tipo_contrato")
    resumen_ciudad = calcular_abandono_por_categoria(df, "ciudad")
    resumen_plan = calcular_abandono_por_categoria(df, "plan")

    _mostrar_tablas(resumen_contrato, resumen_ciudad, resumen_plan)
    _mostrar_comparacion_metricas(df)
    _mostrar_conclusiones(resumen_contrato, resumen_ciudad, resumen_plan, df)


def _mostrar_tablas(
    resumen_contrato: pd.DataFrame,
    resumen_ciudad: pd.DataFrame,
    resumen_plan: pd.DataFrame,
) -> None:
    """Muestra tablas resumen por categorias principales."""
    st.subheader("Tablas resumen")
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.write("Por tipo de contrato")
        _mostrar_tabla_resumen(resumen_contrato, "tipo_contrato")
    with col_2:
        st.write("Por ciudad")
        _mostrar_tabla_resumen(resumen_ciudad, "ciudad")
    with col_3:
        st.write("Por plan")
        _mostrar_tabla_resumen(resumen_plan, "plan")


def _mostrar_tabla_resumen(df: pd.DataFrame, columna: str) -> None:
    """Muestra una tabla con nombres legibles."""
    if df.empty:
        st.info("Sin datos suficientes.")
        return

    tabla = df.rename(
        columns={
            columna: ETIQUETAS_COLUMNAS_ANALISIS.get(columna, columna),
            "total_clientes": "Total clientes",
            "clientes_abandonaron": "Clientes abandonaron",
            "tasa_abandono": "Tasa abandono (%)",
        }
    )
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _mostrar_comparacion_metricas(df: pd.DataFrame) -> None:
    """Muestra comparacion de metricas promedio por estado de abandono."""
    st.subheader("Comparación por estado de abandono")
    tablas = [
        ("Satisfacción", calcular_satisfaccion_promedio_por_abandono(df)),
        ("Reclamos últimos 6 meses", calcular_reclamos_promedio_por_abandono(df)),
        ("Pagos atrasados", calcular_pagos_atrasados_promedio_por_abandono(df)),
        ("Días sin uso", calcular_dias_sin_uso_promedio_por_abandono(df)),
    ]
    resumen = []
    for metrica, datos in tablas:
        for fila in datos.to_dict("records"):
            resumen.append(
                {
                    "Métrica": metrica,
                    "Estado": fila.get("estado_abandono"),
                    "Promedio": fila.get("promedio"),
                }
            )

    if not resumen:
        st.info("No hay datos suficientes para comparar metricas por abandono.")
        return

    st.dataframe(pd.DataFrame(resumen), use_container_width=True, hide_index=True)


def _mostrar_conclusiones(
    resumen_contrato: pd.DataFrame,
    resumen_ciudad: pd.DataFrame,
    resumen_plan: pd.DataFrame,
    df: pd.DataFrame,
) -> None:
    """Muestra conclusiones descriptivas automaticas simples."""
    st.subheader("Conclusiones descriptivas")
    conclusiones = []

    conclusiones.extend(_conclusion_mayor_tasa(resumen_contrato, "tipo_contrato", "contrato"))
    conclusiones.extend(_conclusion_mayor_tasa(resumen_ciudad, "ciudad", "ciudad"))
    conclusiones.extend(_conclusion_mayor_tasa(resumen_plan, "plan", "plan"))
    conclusiones.extend(_conclusion_diferencia(df, "satisfaccion", "satisfacción promedio"))
    conclusiones.extend(_conclusion_diferencia(df, "reclamos_ultimos_6_meses", "reclamos promedio"))

    if not conclusiones:
        st.info("No hay datos suficientes para generar conclusiones descriptivas.")
        return

    for conclusion in conclusiones:
        st.write(f"- {conclusion}")


def _conclusion_mayor_tasa(df: pd.DataFrame, columna: str, etiqueta: str) -> list[str]:
    """Construye una conclusion sobre la mayor tasa de abandono observada."""
    if df.empty or columna not in df.columns:
        return []
    fila = df.iloc[0]
    return [
        "En los datos analizados se observa que el "
        f"{etiqueta} `{fila[columna]}` presenta la mayor tasa de abandono "
        f"({float(fila['tasa_abandono']):.2f}%)."
    ]


def _conclusion_diferencia(df: pd.DataFrame, columna: str, etiqueta: str) -> list[str]:
    """Construye una conclusion de diferencia promedio por estado de abandono."""
    if columna == "satisfaccion":
        datos = calcular_satisfaccion_promedio_por_abandono(df)
    elif columna == "reclamos_ultimos_6_meses":
        datos = calcular_reclamos_promedio_por_abandono(df)
    else:
        return []

    if datos.empty or len(datos) < 2:
        return []

    promedios = {int(fila["abandono"]): float(fila["promedio"]) for fila in datos.to_dict("records")}
    if 0 not in promedios or 1 not in promedios:
        return []

    diferencia = promedios[1] - promedios[0]
    return [
        "Este resultado sugiere una asociación descriptiva: la diferencia de "
        f"{etiqueta} entre quienes abandonaron y quienes permanecen es "
        f"{diferencia:.2f} puntos."
    ]
