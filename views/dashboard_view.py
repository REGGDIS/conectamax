"""Vista del dashboard descriptivo de abandono de clientes."""

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import ETIQUETAS_COLUMNAS_ANALISIS, OPCIONES_FILTRO_ABANDONO
from services.analisis_service import (
    aplicar_filtros_analisis,
    calcular_abandono_por_categoria,
    calcular_dias_sin_uso_promedio_por_abandono,
    calcular_kpis,
    calcular_pagos_atrasados_promedio_por_abandono,
    calcular_reclamos_promedio_por_abandono,
    calcular_satisfaccion_promedio_por_abandono,
    contar_por_abandono,
    obtener_opciones_filtro_analisis,
)


def mostrar_dashboard() -> None:
    """Renderiza indicadores, filtros y graficos descriptivos."""
    st.title("Dashboard")
    st.write("Panel descriptivo para revisar patrones generales asociados al abandono de clientes.")

    df = st.session_state.get("clientes_df")
    if not st.session_state.get("datos_cargados") or df is None or df.empty:
        st.info("No hay datos cargados para construir el dashboard.")
        st.write("Ve al modulo `Carga de datos` y carga un CSV valido para continuar.")
        return

    st.write(f"Archivo activo: `{st.session_state.get('nombre_archivo_activo', 'No informado')}`")
    st.write(f"Clientes disponibles antes de filtros: `{len(df)}`")

    filtrado = _mostrar_filtros(df)
    st.write(f"Clientes analizados con filtros activos: `{len(filtrado)}`")

    _mostrar_kpis(filtrado)
    if filtrado.empty:
        st.warning("No hay datos suficientes para graficar con los filtros seleccionados.")
        return

    _mostrar_graficos(filtrado)


def _mostrar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Muestra filtros generales y devuelve el DataFrame filtrado."""
    st.subheader("Filtros generales")
    col_ciudad, col_contrato = st.columns(2)
    with col_ciudad:
        ciudades = st.multiselect("Ciudad", obtener_opciones_filtro_analisis(df, "ciudad"))
    with col_contrato:
        tipos_contrato = st.multiselect(
            "Tipo de contrato",
            obtener_opciones_filtro_analisis(df, "tipo_contrato"),
        )

    col_plan, col_abandono = st.columns(2)
    with col_plan:
        planes = st.multiselect("Plan", obtener_opciones_filtro_analisis(df, "plan"))
    with col_abandono:
        abandono_label = st.selectbox("Estado de abandono", list(OPCIONES_FILTRO_ABANDONO.keys()))

    return aplicar_filtros_analisis(
        df,
        ciudades=ciudades,
        tipos_contrato=tipos_contrato,
        planes=planes,
        abandono=OPCIONES_FILTRO_ABANDONO[abandono_label],
    )


def _mostrar_kpis(df: pd.DataFrame) -> None:
    """Muestra indicadores principales del dashboard."""
    st.subheader("Indicadores principales")
    kpis = calcular_kpis(df)

    fila_1 = st.columns(4)
    fila_1[0].metric("Total de clientes", _formatear_entero(kpis["total_clientes"]))
    fila_1[1].metric("Clientes que permanecen", _formatear_entero(kpis["clientes_permanecen"]))
    fila_1[2].metric("Clientes que abandonaron", _formatear_entero(kpis["clientes_abandonaron"]))
    fila_1[3].metric("Tasa de abandono", _formatear_porcentaje(kpis["tasa_abandono"]))

    fila_2 = st.columns(4)
    fila_2[0].metric("Tasa de retención", _formatear_porcentaje(kpis["tasa_retencion"]))
    fila_2[1].metric("Satisfacción promedio", _formatear_promedio(kpis["satisfaccion_promedio"]))
    fila_2[2].metric("Monto mensual promedio", _formatear_monto(kpis["monto_mensual_promedio"]))
    fila_2[3].metric("Reclamos promedio", _formatear_promedio(kpis["reclamos_promedio"]))


def _mostrar_graficos(df: pd.DataFrame) -> None:
    """Muestra el conjunto minimo de graficos descriptivos."""
    st.subheader("Graficos descriptivos")
    col_1, col_2 = st.columns(2)
    with col_1:
        _grafico_conteo_abandono(df)
        _grafico_tasa_categoria(df, "ciudad", "Tasa de abandono por ciudad")
        _grafico_promedio_abandono(
            calcular_satisfaccion_promedio_por_abandono(df),
            "Satisfacción promedio según abandono",
        )
        _grafico_promedio_abandono(
            calcular_pagos_atrasados_promedio_por_abandono(df),
            "Pagos atrasados promedio según abandono",
        )
    with col_2:
        _grafico_tasa_categoria(df, "tipo_contrato", "Tasa de abandono por tipo de contrato")
        _grafico_tasa_categoria(df, "plan", "Tasa de abandono por plan")
        _grafico_promedio_abandono(
            calcular_reclamos_promedio_por_abandono(df),
            "Reclamos promedio según abandono",
        )
        _grafico_promedio_abandono(
            calcular_dias_sin_uso_promedio_por_abandono(df),
            "Días sin uso promedio según abandono",
        )


def _grafico_conteo_abandono(df: pd.DataFrame) -> None:
    """Grafica clientes que permanecen frente a clientes que abandonaron."""
    datos = contar_por_abandono(df)
    if datos.empty:
        st.info("No hay datos suficientes para comparar permanencia y abandono.")
        return

    fig = px.bar(
        datos,
        x="estado_abandono",
        y="total_clientes",
        title="Clientes que permanecen frente a clientes que abandonaron",
        labels={"estado_abandono": "Estado", "total_clientes": "Clientes"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_tasa_categoria(df: pd.DataFrame, columna: str, titulo: str) -> None:
    """Grafica tasa de abandono por categoria."""
    datos = calcular_abandono_por_categoria(df, columna)
    if datos.empty:
        st.info(f"No hay datos suficientes para mostrar {titulo.lower()}.")
        return

    fig = px.bar(
        datos,
        x=columna,
        y="tasa_abandono",
        title=titulo,
        labels={
            columna: ETIQUETAS_COLUMNAS_ANALISIS.get(columna, columna),
            "tasa_abandono": "Tasa de abandono (%)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_promedio_abandono(datos: pd.DataFrame, titulo: str) -> None:
    """Grafica una metrica promedio segun abandono."""
    if datos.empty:
        st.info(f"No hay datos suficientes para mostrar {titulo.lower()}.")
        return

    fig = px.bar(
        datos,
        x="estado_abandono",
        y="promedio",
        title=titulo,
        labels={"estado_abandono": "Estado", "promedio": "Promedio"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _formatear_entero(valor: float | int) -> str:
    """Formatea enteros con separador de miles."""
    return f"{int(valor):,}".replace(",", ".")


def _formatear_porcentaje(valor: float | int) -> str:
    """Formatea porcentajes con dos decimales."""
    return f"{float(valor):.2f}%"


def _formatear_promedio(valor: float | int) -> str:
    """Formatea promedios con dos decimales."""
    return f"{float(valor):.2f}"


def _formatear_monto(valor: float | int) -> str:
    """Formatea monto mensual con separador de miles."""
    return f"${float(valor):,.0f}".replace(",", ".")
