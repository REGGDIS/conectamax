"""Vista complementaria de analisis descriptivo."""

import pandas as pd
import plotly.express as px
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
from services.segmentacion_service import COLUMNAS_SEGMENTACION, segmentar_clientes_kmeans
from utils.ui_helpers import msg_advertencia, msg_error, msg_info


COLORES_CLUSTER = {
    "Clúster 1": "#5b8dee",
    "Clúster 2": "#55c2a5",
    "Clúster 3": "#f2b84b",
}

COLORES_ABANDONO = {"Permanece": "#2ecc71", "Abandonó": "#e74c3c"}

VARIABLES_BOXPLOT = {
    "satisfaccion": "Satisfacción",
    "reclamos_ultimos_6_meses": "Reclamos en los últimos 6 meses",
    "pagos_atrasados": "Pagos atrasados",
    "dias_sin_uso": "Días sin uso",
    "monto_mensual": "Monto mensual",
    "antiguedad_meses": "Antigüedad en meses",
}

VARIABLES_CORRELACION = {
    "antiguedad_meses": "Antigüedad en meses",
    "monto_mensual": "Monto mensual",
    "cantidad_servicios": "Cantidad de servicios",
    "reclamos_ultimos_6_meses": "Reclamos últimos 6 meses",
    "pagos_atrasados": "Pagos atrasados",
    "dias_sin_uso": "Días sin uso",
    "satisfaccion": "Satisfacción",
    "abandono": "Abandono",
}

ETIQUETAS_COLUMNAS_SEGMENTACION = {
    "cluster": "Clúster",
    "total_clientes": "Total clientes",
    "clientes_abandonaron": "Clientes abandonaron",
    "tasa_abandono": "Tasa abandono",
    "antiguedad_meses": "Antigüedad meses",
    "monto_mensual": "Monto mensual",
    "cantidad_servicios": "Cantidad servicios",
    "reclamos_ultimos_6_meses": "Reclamos últimos 6 meses",
    "pagos_atrasados": "Pagos atrasados",
    "dias_sin_uso": "Días sin uso",
    "satisfaccion": "Satisfacción",
}


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
    _mostrar_distribucion_boxplot(df)
    st.divider()
    _mostrar_matriz_correlacion(df)
    st.divider()
    _mostrar_conclusiones(resumen_contrato, resumen_ciudad, resumen_plan, df)
    st.divider()
    _mostrar_segmentacion_kmeans(df)


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


def _mostrar_distribucion_boxplot(df: pd.DataFrame) -> None:
    """Muestra boxplot dinamico de variables segun estado de abandono."""
    st.subheader("Distribución de variables según estado de abandono")
    st.markdown(
        "Este gráfico compara clientes que permanecen y clientes que abandonaron. "
        "La línea central representa la mediana, la caja contiene el 50 % central "
        "de los datos y los puntos fuera de los bigotes pueden representar valores "
        "atípicos. Las diferencias observadas son descriptivas y no implican causalidad."
    )

    variable = st.selectbox(
        "Variable a comparar",
        list(VARIABLES_BOXPLOT.keys()),
        format_func=formatear_etiqueta_variable,
    )

    try:
        datos = preparar_datos_boxplot(df, variable)
    except ValueError as exc:
        msg_advertencia(
            "No fue posible construir el gráfico de caja.",
            causa=str(exc),
            accion=(
                "Verifica que la base de datos contenga la variable seleccionada "
                "y la columna `abandono`."
            ),
        )
        return

    if datos.empty or datos["estado_abandono"].nunique() < 2:
        msg_info(
            "No hay datos suficientes para comparar la distribución por estado de abandono.",
            accion="Selecciona otra variable o verifica que existan valores validos para ambos estados.",
        )
        return

    etiqueta = formatear_etiqueta_variable(variable)
    fig = px.box(
        datos,
        x="estado_abandono",
        y=variable,
        color="estado_abandono",
        points="outliers",
        color_discrete_map=COLORES_ABANDONO,
        title=f"Distribución de {etiqueta} según estado de abandono",
        labels={"estado_abandono": "Estado de abandono", variable: etiqueta},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def preparar_datos_boxplot(df: pd.DataFrame | None, variable: str) -> pd.DataFrame:
    """Prepara datos numericos para comparar distribuciones por abandono."""
    columnas_resultado = ["estado_abandono", variable]
    if variable not in VARIABLES_BOXPLOT:
        raise ValueError(f"La variable seleccionada no esta permitida: {variable}")
    if df is None or df.empty:
        return pd.DataFrame(columns=columnas_resultado)
    if variable not in df.columns:
        raise ValueError(f"La base de datos no contiene la variable seleccionada: {variable}")
    if "abandono" not in df.columns:
        raise ValueError("La base de datos no contiene la columna requerida: abandono")

    datos = df.loc[:, [variable, "abandono"]].copy(deep=True)
    datos[variable] = pd.to_numeric(datos[variable], errors="coerce")
    datos["abandono"] = pd.to_numeric(datos["abandono"], errors="coerce")
    datos = datos.dropna(subset=[variable, "abandono"])
    datos = datos[datos["abandono"].isin([0, 1])].copy()
    datos["estado_abandono"] = datos["abandono"].map({0: "Permanece", 1: "Abandonó"})
    return datos.loc[:, columnas_resultado].reset_index(drop=True)


def formatear_etiqueta_variable(variable: str) -> str:
    """Devuelve una etiqueta legible para variables del boxplot."""
    return VARIABLES_BOXPLOT.get(variable, variable)


def _mostrar_matriz_correlacion(df: pd.DataFrame) -> None:
    """Muestra matriz de correlacion de Pearson y relaciones con abandono."""
    st.subheader("Matriz de correlación de Pearson")
    st.markdown(
        "Pearson mide la relación lineal entre variables numéricas. El coeficiente "
        "varía entre -1 y 1: valores cercanos a 1 indican relación positiva, "
        "valores cercanos a -1 indican relación negativa y valores cercanos a 0 "
        "indican poca relación lineal. Correlación no implica causalidad; "
        "`abandono` se interpreta como una variable binaria 0/1 para este análisis "
        "descriptivo."
    )

    try:
        matriz = preparar_matriz_correlacion(df)
    except ValueError as exc:
        msg_advertencia(
            "No fue posible calcular la matriz de correlación.",
            causa=str(exc),
            accion=(
                "Verifica que existan al menos dos variables numéricas válidas "
                "en la base de datos."
            ),
        )
        return

    matriz_presentacion = _renombrar_matriz_correlacion(matriz).round(2)
    fig = px.imshow(
        matriz_presentacion,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz de correlación de Pearson",
        labels={"x": "Variable", "y": "Variable", "color": "Correlación"},
        aspect="auto",
    )
    fig.update_traces(text=matriz_presentacion.values, texttemplate="%{text:.2f}")
    fig.update_layout(coloraxis_cmid=0, height=650)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Matriz de coeficientes Pearson redondeada a 2 decimales.")
    tabla = matriz_presentacion.reset_index().rename(columns={"index": "Variable"})
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    _mostrar_correlaciones_abandono(matriz)
    st.markdown(
        "La correlación describe asociación lineal y no demuestra causalidad. "
        "Una correlación baja no descarta relaciones no lineales. Estos resultados "
        "complementan, pero no reemplazan, el modelo de churn."
    )


def preparar_matriz_correlacion(df: pd.DataFrame | None) -> pd.DataFrame:
    """Prepara y calcula matriz de correlacion de Pearson."""
    if df is None:
        raise ValueError("No se recibieron datos para calcular correlaciones.")
    if df.empty:
        raise ValueError("No hay datos disponibles para calcular correlaciones.")

    columnas = [columna for columna in VARIABLES_CORRELACION if columna in df.columns]
    if len(columnas) < 2:
        raise ValueError("Se requieren al menos 2 variables disponibles para calcular correlaciones.")

    datos = df.loc[:, columnas].copy(deep=True)
    columnas_validas = []
    for columna in columnas:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
        if not datos[columna].isna().all():
            columnas_validas.append(columna)

    if len(columnas_validas) < 2:
        raise ValueError("Se requieren al menos 2 variables numéricas válidas para calcular correlaciones.")

    return datos.loc[:, columnas_validas].corr(method="pearson")


def calcular_correlaciones_abandono(matriz: pd.DataFrame | None) -> pd.DataFrame:
    """Construye tabla ordenada de correlaciones descriptivas con abandono."""
    columnas = ["variable", "coeficiente", "direccion"]
    if matriz is None or matriz.empty or "abandono" not in matriz.columns:
        return pd.DataFrame(columns=columnas)

    filas = []
    for variable, coeficiente in matriz["abandono"].drop(labels=["abandono"], errors="ignore").items():
        if pd.isna(coeficiente):
            continue
        filas.append(
            {
                "variable": VARIABLES_CORRELACION.get(variable, variable),
                "coeficiente": float(coeficiente),
                "direccion": _clasificar_direccion_correlacion(float(coeficiente)),
                "_orden": abs(float(coeficiente)),
            }
        )

    if not filas:
        return pd.DataFrame(columns=columnas)

    resultado = pd.DataFrame(filas).sort_values("_orden", ascending=False, kind="mergesort")
    return resultado.loc[:, columnas].reset_index(drop=True)


def _mostrar_correlaciones_abandono(matriz: pd.DataFrame) -> None:
    """Muestra tabla ordenada de correlaciones con abandono."""
    st.subheader("Correlaciones con abandono")
    correlaciones = calcular_correlaciones_abandono(matriz)
    if correlaciones.empty:
        msg_info(
            "No hay datos suficientes para calcular correlaciones con abandono.",
            accion="Verifica que `abandono` y otras variables numéricas tengan valores válidos.",
        )
        return

    tabla = correlaciones.copy()
    tabla["coeficiente"] = tabla["coeficiente"].round(2)
    tabla = tabla.rename(
        columns={
            "variable": "Variable",
            "coeficiente": "Coeficiente de correlación con abandono",
            "direccion": "Dirección",
        }
    )
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _renombrar_matriz_correlacion(matriz: pd.DataFrame) -> pd.DataFrame:
    """Aplica etiquetas legibles a ambos ejes de la matriz."""
    return matriz.rename(index=VARIABLES_CORRELACION, columns=VARIABLES_CORRELACION)


def _clasificar_direccion_correlacion(coeficiente: float) -> str:
    if coeficiente > 0.10:
        return "Positiva"
    if coeficiente < -0.10:
        return "Negativa"
    return "Sin relación lineal clara"


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


def _mostrar_segmentacion_kmeans(df: pd.DataFrame) -> None:
    """Muestra segmentacion no supervisada de clientes mediante K-Means."""
    st.subheader("Segmentación de clientes con K-Means")
    st.markdown(
        "K-Means agrupa clientes con patrones numéricos similares mediante una "
        "técnica no supervisada. Los clústeres no son categorías comerciales "
        "definitivas y su número no implica mayor o menor riesgo. La variable "
        "`abandono` no se usa para formar los grupos; solo se utiliza después "
        "para describir la tasa observada en cada clúster."
    )

    try:
        resultado = segmentar_clientes_kmeans(df)
    except ValueError as exc:
        msg_advertencia(
            "No fue posible segmentar clientes con K-Means.",
            causa=str(exc),
            accion=(
                "Verifica que existan al menos 3 clientes y que las variables "
                "numericas requeridas sean validas."
            ),
        )
        return

    _ = resultado["clientes_segmentados"]
    conteo = resultado["conteo_clusters"]
    resumen = resultado["resumen_clusters"]
    tasa_abandono = resultado["tasa_abandono_clusters"]
    descripciones = resultado["descripciones"]

    _mostrar_metricas_clusters(conteo)
    _mostrar_grafico_clusters(conteo)
    _mostrar_resumen_clusters(resumen)
    _mostrar_tasa_abandono_clusters(tasa_abandono)
    _mostrar_descripciones_clusters(descripciones)


def _mostrar_metricas_clusters(conteo: pd.DataFrame) -> None:
    """Muestra indicadores de cantidad de clientes por cluster."""
    st.subheader("Clientes por clúster")
    columnas = st.columns(3)
    for indice in range(3):
        cluster = f"Clúster {indice + 1}"
        columnas[indice].metric(
            f"Clientes en {cluster}",
            _formatear_entero(_total_cluster(conteo, cluster)),
        )


def _mostrar_grafico_clusters(conteo: pd.DataFrame) -> None:
    """Muestra grafico de distribucion de clientes por cluster."""
    datos = _completar_conteo_clusters(conteo)
    fig = px.bar(
        datos,
        x="cluster",
        y="total_clientes",
        color="cluster",
        text="total_clientes",
        color_discrete_map=COLORES_CLUSTER,
        title="Distribución de clientes por clúster K-Means",
        labels={"cluster": "Clúster", "total_clientes": "Clientes"},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _mostrar_resumen_clusters(resumen: pd.DataFrame) -> None:
    """Muestra tabla de promedios por cluster."""
    st.subheader("Promedios por clúster")
    if resumen.empty:
        msg_info(
            "No hay datos suficientes para mostrar promedios por clúster.",
            accion="Verifica que las variables de segmentación tengan valores válidos.",
        )
        return

    columnas = ["cluster"] + [columna for columna in COLUMNAS_SEGMENTACION if columna in resumen.columns]
    tabla = resumen.loc[:, columnas].copy()
    for columna in COLUMNAS_SEGMENTACION:
        if columna in tabla.columns:
            tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce").round(2)
    tabla = tabla.rename(columns=ETIQUETAS_COLUMNAS_SEGMENTACION)
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _mostrar_tasa_abandono_clusters(tasa_abandono: pd.DataFrame) -> None:
    """Muestra tasa real de abandono observada por cluster."""
    st.subheader("Tasa real de abandono por clúster")
    st.markdown(
        "Esta tasa se calcula después de formar los grupos. `abandono` no se utilizó "
        "para entrenar K-Means; la comparación es descriptiva y no causal."
    )
    if tasa_abandono.empty:
        msg_info(
            "No hay datos suficientes para calcular tasa de abandono por clúster.",
            accion="Verifica que la columna `abandono` tenga valores válidos 0 o 1.",
        )
        return

    tabla = tasa_abandono.loc[
        :,
        ["cluster", "total_clientes", "clientes_abandonaron", "tasa_abandono"],
    ].copy()
    tabla["tasa_abandono"] = pd.to_numeric(
        tabla["tasa_abandono"],
        errors="coerce",
    ).map(_formatear_porcentaje)
    tabla = tabla.rename(columns=ETIQUETAS_COLUMNAS_SEGMENTACION)
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _mostrar_descripciones_clusters(descripciones: list[str]) -> None:
    """Muestra descripciones prudentes generadas por el servicio."""
    st.subheader("Lectura descriptiva de los clústeres")
    if not descripciones:
        msg_info(
            "No hay descripciones disponibles para los clústeres.",
            accion="Verifica que el resumen de segmentación tenga datos suficientes.",
        )
        return

    for descripcion in descripciones:
        st.markdown(f"- {descripcion}")


def _completar_conteo_clusters(conteo: pd.DataFrame) -> pd.DataFrame:
    """Asegura presencia visual de los tres clusters iniciales."""
    filas = []
    for indice in range(3):
        cluster = f"Clúster {indice + 1}"
        filas.append({"cluster": cluster, "total_clientes": _total_cluster(conteo, cluster)})
    return pd.DataFrame(filas)


def _total_cluster(conteo: pd.DataFrame, cluster: str) -> int:
    """Obtiene el total de clientes de un cluster; devuelve 0 si no existe."""
    if conteo.empty or "cluster" not in conteo.columns or "total_clientes" not in conteo.columns:
        return 0
    fila = conteo.loc[conteo["cluster"] == cluster, "total_clientes"]
    if fila.empty:
        return 0
    return int(fila.iloc[0])


def _formatear_entero(valor: float | int) -> str:
    """Formatea enteros con separador de miles."""
    return f"{int(valor):,}".replace(",", ".")


def _formatear_porcentaje(valor: float | int) -> str:
    """Formatea porcentajes con dos decimales."""
    return f"{float(valor):.2f}%"
