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
from services.fuente_datos_service import cargar_clientes_desde_sqlite
from utils.ui_helpers import msg_advertencia, msg_error, msg_info


def mostrar_analisis() -> None:
    """Renderiza tablas resumen y conclusiones descriptivas simples."""
    st.title("Analisis")
    st.markdown(
        "Tablas resumen y conclusiones descriptivas por contrato, ciudad y plan. "
        "Complementa el Dashboard con detalle por categoria. "
        "Los resultados describen patrones observados, sin inferencias causales."
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
            "No se pudieron cargar los datos para el analisis.",
            causa=str(exc),
            accion="Verifica que la base de datos sea valida y vuelve a intentarlo.",
        )
        return

    if df.empty:
        msg_info(
            "No hay datos disponibles para analizar.",
            causa="La tabla de clientes esta vacia.",
            accion="Ejecuta `python scripts/generate_data.py --n 2500` para generar datos sinteticos.",
        )
        return

    st.caption(f"Clientes analizados: {len(df):,}".replace(",", "."))

    resumen_contrato = calcular_abandono_por_categoria(df, "tipo_contrato")
    resumen_ciudad = calcular_abandono_por_categoria(df, "ciudad")
    resumen_plan = calcular_abandono_por_categoria(df, "plan")

    _mostrar_tablas(resumen_contrato, resumen_ciudad, resumen_plan)
    st.divider()
    _mostrar_comparacion_metricas(df)
    st.divider()
    _mostrar_conclusiones(resumen_contrato, resumen_ciudad, resumen_plan, df)


def _mostrar_tablas(
    resumen_contrato: pd.DataFrame,
    resumen_ciudad: pd.DataFrame,
    resumen_plan: pd.DataFrame,
) -> None:
    """Muestra tablas resumen por categorias principales."""
    st.subheader("Tasas de abandono por categoria")
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.caption("Por tipo de contrato")
        _mostrar_tabla_resumen(resumen_contrato, "tipo_contrato")
    with col_2:
        st.caption("Por ciudad")
        _mostrar_tabla_resumen(resumen_ciudad, "ciudad")
    with col_3:
        st.caption("Por plan")
        _mostrar_tabla_resumen(resumen_plan, "plan")


def _mostrar_tabla_resumen(df: pd.DataFrame, columna: str) -> None:
    """Muestra una tabla con nombres legibles."""
    if df.empty:
        msg_info(
            "Sin datos para esta categoria.",
            accion="Verifica que la base de datos tenga clientes con esta columna completa.",
        )
        return

    tabla = df.rename(
        columns={
            columna: ETIQUETAS_COLUMNAS_ANALISIS.get(columna, columna),
            "total_clientes": "Total clientes",
            "clientes_abandonaron": "Abandonaron",
            "tasa_abandono": "Tasa abandono (%)",
        }
    )
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _mostrar_comparacion_metricas(df: pd.DataFrame) -> None:
    """Muestra comparacion de metricas promedio por estado de abandono."""
    st.subheader("Comparacion de metricas por estado de abandono")
    st.markdown(
        "Promedios de satisfaccion, reclamos, pagos atrasados y dias sin uso "
        "separados entre clientes que permanecen y clientes que abandonaron."
    )
    tablas = [
        ("Satisfaccion (1-5)", calcular_satisfaccion_promedio_por_abandono(df)),
        ("Reclamos ultimos 6 meses", calcular_reclamos_promedio_por_abandono(df)),
        ("Pagos atrasados", calcular_pagos_atrasados_promedio_por_abandono(df)),
        ("Dias sin uso", calcular_dias_sin_uso_promedio_por_abandono(df)),
    ]
    resumen = []
    for metrica, datos in tablas:
        for fila in datos.to_dict("records"):
            resumen.append(
                {
                    "Metrica": metrica,
                    "Estado": fila.get("estado_abandono"),
                    "Promedio": round(float(fila.get("promedio", 0)), 2),
                }
            )

    if not resumen:
        msg_info(
            "No hay datos suficientes para comparar metricas por abandono.",
            accion="Verifica que la base de datos contenga clientes en ambos estados (0 y 1).",
        )
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
    st.markdown(
        "Observaciones automaticas basadas en los datos. "
        "Describen patrones presentes en la muestra, no relaciones causales."
    )
    conclusiones = []

    conclusiones.extend(_conclusion_mayor_tasa(resumen_contrato, "tipo_contrato", "contrato"))
    conclusiones.extend(_conclusion_mayor_tasa(resumen_ciudad, "ciudad", "ciudad"))
    conclusiones.extend(_conclusion_mayor_tasa(resumen_plan, "plan", "plan"))
    conclusiones.extend(_conclusion_diferencia(df, "satisfaccion", "satisfaccion promedio"))
    conclusiones.extend(_conclusion_diferencia(df, "reclamos_ultimos_6_meses", "reclamos promedio"))

    if not conclusiones:
        msg_info(
            "No hay datos suficientes para generar conclusiones descriptivas.",
            accion="Verifica que la base de datos tenga clientes con valores validos en las columnas clave.",
        )
        return

    for conclusion in conclusiones:
        st.markdown(f"- {conclusion}")


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
        "Este resultado sugiere una asociacion descriptiva: la diferencia de "
        f"{etiqueta} entre quienes abandonaron y quienes permanecen es "
        f"{diferencia:.2f} puntos."
    ]
