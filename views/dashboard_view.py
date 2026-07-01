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
from services.fuente_datos_service import cargar_clientes_desde_sqlite
from utils.ui_helpers import msg_advertencia, msg_error, msg_info

COLORES_ABANDONO = {"Permanece": "#2ecc71", "Abandonó": "#e74c3c"}


def mostrar_dashboard() -> None:
    """Renderiza indicadores, filtros y graficos descriptivos."""
    st.title("Dashboard")
    st.markdown(
        "Indicadores clave y graficos descriptivos sobre el comportamiento "
        "y abandono de los clientes. Usa los filtros para explorar segmentos especificos."
    )
    st.caption("Fuente de datos: vista `comportamiento_cliente` de SQLite.")

    try:
        df = cargar_clientes_desde_sqlite()
    except FileNotFoundError as exc:
        msg_advertencia(
            "No se encontro la base de datos.",
            causa=str(exc),
            accion="Ejecuta `python scripts/init_db.py` y `python scripts/generate_data.py` para crearla.",
        )
        return
    except RuntimeError as exc:
        msg_error(
            "No se pudieron cargar los datos del dashboard.",
            causa=str(exc),
            accion="Verifica que la base de datos sea valida y vuelve a intentarlo.",
        )
        return

    if df.empty:
        msg_info(
            "No hay datos disponibles para construir el dashboard.",
            causa="La tabla de clientes esta vacia.",
            accion="Ejecuta `python scripts/generate_data.py --n 2500` para generar datos sinteticos.",
        )
        return

    st.caption(f"Total de clientes en la base: {len(df):,}".replace(",", "."))

    filtrado = _mostrar_filtros(df)
    st.caption(f"Clientes analizados con filtros activos: {len(filtrado):,}".replace(",", "."))

    _mostrar_kpis(filtrado)

    if filtrado.empty:
        msg_advertencia(
            "No hay datos suficientes para graficar con los filtros seleccionados.",
            causa="La combinacion de filtros activos no devuelve ningun cliente.",
            accion="Amplia o limpia los filtros para ver los graficos.",
        )
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
    fila_1[1].metric("Permanecen", _formatear_entero(kpis["clientes_permanecen"]))
    fila_1[2].metric("Abandonaron", _formatear_entero(kpis["clientes_abandonaron"]))
    fila_1[3].metric("Tasa de abandono", _formatear_porcentaje(kpis["tasa_abandono"]))

    fila_2 = st.columns(4)
    fila_2[0].metric("Tasa de retencion", _formatear_porcentaje(kpis["tasa_retencion"]))
    fila_2[1].metric("Satisfaccion promedio", _formatear_promedio(kpis["satisfaccion_promedio"]))
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
            "Satisfaccion promedio segun estado de abandono",
        )
        _grafico_promedio_abandono(
            calcular_pagos_atrasados_promedio_por_abandono(df),
            "Pagos atrasados promedio segun estado de abandono",
        )
    with col_2:
        _grafico_tasa_categoria(df, "tipo_contrato", "Tasa de abandono por tipo de contrato")
        _grafico_tasa_categoria(df, "plan", "Tasa de abandono por plan")
        _grafico_promedio_abandono(
            calcular_reclamos_promedio_por_abandono(df),
            "Reclamos promedio segun estado de abandono",
        )
        _grafico_promedio_abandono(
            calcular_dias_sin_uso_promedio_por_abandono(df),
            "Dias sin uso promedio segun estado de abandono",
        )


def _grafico_conteo_abandono(df: pd.DataFrame) -> None:
    """Grafica clientes que permanecen frente a clientes que abandonaron."""
    datos = contar_por_abandono(df)
    if datos.empty:
        msg_info(
            "Sin datos para el grafico de permanencia vs. abandono.",
            accion="Ajusta los filtros para incluir clientes en ambos estados.",
        )
        return

    fig = px.bar(
        datos,
        x="estado_abandono",
        y="total_clientes",
        color="estado_abandono",
        color_discrete_map=COLORES_ABANDONO,
        title="Clientes que permanecen vs. clientes que abandonaron",
        labels={"estado_abandono": "Estado", "total_clientes": "Clientes"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _grafico_tasa_categoria(df: pd.DataFrame, columna: str, titulo: str) -> None:
    """Grafica tasa de abandono por categoria."""
    datos = calcular_abandono_por_categoria(df, columna)
    if datos.empty:
        msg_info(
            f"Sin datos para: {titulo.lower()}.",
            accion="Ajusta los filtros para incluir mas registros.",
        )
        return

    etiqueta_x = ETIQUETAS_COLUMNAS_ANALISIS.get(columna, columna)
    fig = px.bar(
        datos,
        x=columna,
        y="tasa_abandono",
        title=titulo,
        labels={columna: etiqueta_x, "tasa_abandono": "Tasa de abandono (%)"},
        color_discrete_sequence=["#5b8dee"],
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_promedio_abandono(datos: pd.DataFrame, titulo: str) -> None:
    """Grafica una metrica promedio segun abandono."""
    if datos.empty:
        msg_info(
            f"Sin datos para: {titulo.lower()}.",
            accion="Ajusta los filtros para incluir mas registros.",
        )
        return

    fig = px.bar(
        datos,
        x="estado_abandono",
        y="promedio",
        color="estado_abandono",
        color_discrete_map=COLORES_ABANDONO,
        title=titulo,
        labels={"estado_abandono": "Estado", "promedio": "Promedio"},
    )
    fig.update_layout(showlegend=False)
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
