"""Servicios puros para segmentacion de clientes mediante K-Means."""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


COLUMNAS_SEGMENTACION = [
    "antiguedad_meses",
    "monto_mensual",
    "cantidad_servicios",
    "reclamos_ultimos_6_meses",
    "pagos_atrasados",
    "dias_sin_uso",
    "satisfaccion",
]

COLUMNAS_EXCLUIDAS_ENTRENAMIENTO = {
    "abandono",
    "nivel_riesgo",
    "probabilidad_churn",
}


def validar_columnas_segmentacion(df: pd.DataFrame | None) -> list[str]:
    """Devuelve las columnas requeridas que no estan presentes."""
    if df is None:
        return list(COLUMNAS_SEGMENTACION)
    return [columna for columna in COLUMNAS_SEGMENTACION if columna not in df.columns]


def preparar_variables_segmentacion(df: pd.DataFrame | None) -> pd.DataFrame:
    """Prepara las variables numericas usadas para entrenar K-Means."""
    if df is None:
        raise ValueError("No se recibieron datos para segmentar clientes.")

    faltantes = validar_columnas_segmentacion(df)
    if faltantes:
        detalle = ", ".join(faltantes)
        raise ValueError(f"Faltan columnas requeridas para segmentacion: {detalle}")
    if df.empty:
        raise ValueError("No hay registros suficientes para segmentar clientes.")

    features = df.loc[:, COLUMNAS_SEGMENTACION].copy(deep=True)
    for columna in COLUMNAS_SEGMENTACION:
        features[columna] = pd.to_numeric(features[columna], errors="coerce")
        if features[columna].isna().all():
            raise ValueError(
                "La columna requerida para segmentacion no contiene valores numericos validos: "
                f"{columna}"
            )
        features[columna] = features[columna].fillna(features[columna].median())

    return features


def escalar_variables_segmentacion(features: pd.DataFrame | None) -> pd.DataFrame:
    """Escala variables con StandardScaler conservando indice y columnas."""
    if features is None:
        return pd.DataFrame(columns=COLUMNAS_SEGMENTACION)
    if features.empty:
        return pd.DataFrame(columns=features.columns, index=features.index)

    scaler = StandardScaler()
    escaladas = scaler.fit_transform(features)
    return pd.DataFrame(escaladas, columns=features.columns, index=features.index)


def generar_clusters(
    features_escaladas: pd.DataFrame | None,
    n_clusters: int = 3,
    random_state: int = 42,
    n_init: int = 10,
) -> pd.Series:
    """Ejecuta K-Means y devuelve etiquetas internas conservando el indice."""
    if features_escaladas is None or features_escaladas.empty:
        raise ValueError("No hay registros suficientes para generar clusters.")
    if len(features_escaladas) < n_clusters:
        raise ValueError(
            "No hay clientes suficientes para generar "
            f"{n_clusters} clusters: se recibieron {len(features_escaladas)}."
        )

    modelo = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    etiquetas = modelo.fit_predict(features_escaladas)
    return pd.Series(etiquetas, index=features_escaladas.index, name="cluster_id")


def segmentar_clientes_kmeans(
    df: pd.DataFrame | None,
    n_clusters: int = 3,
    random_state: int = 42,
    n_init: int = 10,
) -> dict[str, pd.DataFrame | list[str]]:
    """Orquesta preparacion, escalado, clustering y tablas descriptivas."""
    if df is None:
        raise ValueError("No se recibieron datos para segmentar clientes.")

    features = preparar_variables_segmentacion(df)
    features_escaladas = escalar_variables_segmentacion(features)
    etiquetas = generar_clusters(features_escaladas, n_clusters, random_state, n_init)

    segmentado = df.copy(deep=True)
    segmentado["cluster_id"] = etiquetas.astype(int)
    segmentado["cluster"] = segmentado["cluster_id"].map(lambda valor: f"Clúster {int(valor) + 1}")

    conteo = calcular_conteo_clusters(segmentado)
    resumen = calcular_resumen_clusters(segmentado)
    tasa_abandono = calcular_tasa_abandono_por_cluster(segmentado)

    return {
        "clientes_segmentados": segmentado,
        "conteo_clusters": conteo,
        "resumen_clusters": resumen,
        "tasa_abandono_clusters": tasa_abandono,
        "descripciones": describir_clusters(resumen),
    }


def calcular_conteo_clusters(df_segmentado: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula la cantidad de clientes asignados a cada cluster."""
    columnas = ["cluster_id", "cluster", "total_clientes"]
    if df_segmentado is None or df_segmentado.empty or "cluster_id" not in df_segmentado.columns:
        return pd.DataFrame(columns=columnas)

    datos = _normalizar_columnas_cluster(df_segmentado)
    conteo = datos.groupby(["cluster_id", "cluster"], dropna=False).size().reset_index(name="total_clientes")
    return conteo.loc[:, columnas].sort_values("cluster_id").reset_index(drop=True)


def calcular_resumen_clusters(df_segmentado: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula promedios de las variables de entrenamiento por cluster."""
    columnas = ["cluster_id", "cluster", "total_clientes"] + COLUMNAS_SEGMENTACION
    if df_segmentado is None or df_segmentado.empty or "cluster_id" not in df_segmentado.columns:
        return pd.DataFrame(columns=columnas)

    datos = _normalizar_columnas_cluster(df_segmentado)
    disponibles = [columna for columna in COLUMNAS_SEGMENTACION if columna in datos.columns]
    for columna in disponibles:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    resumen = datos.groupby(["cluster_id", "cluster"], dropna=False).agg(
        total_clientes=("cluster_id", "size"),
        **{columna: (columna, "mean") for columna in disponibles},
    )
    resumen = resumen.reset_index().sort_values("cluster_id").reset_index(drop=True)
    return resumen.loc[:, [columna for columna in columnas if columna in resumen.columns]]


def calcular_tasa_abandono_por_cluster(df_segmentado: pd.DataFrame | None) -> pd.DataFrame:
    """Calcula tasa real de abandono despues de asignar clusters."""
    columnas = ["cluster_id", "cluster", "total_clientes", "clientes_abandonaron", "tasa_abandono"]
    if (
        df_segmentado is None
        or df_segmentado.empty
        or "cluster_id" not in df_segmentado.columns
        or "abandono" not in df_segmentado.columns
    ):
        return pd.DataFrame(columns=columnas)

    datos = _normalizar_columnas_cluster(df_segmentado)
    datos["abandono"] = pd.to_numeric(datos["abandono"], errors="coerce")
    datos = datos[datos["abandono"].isin([0, 1])].copy()
    if datos.empty:
        return pd.DataFrame(columns=columnas)

    resumen = datos.groupby(["cluster_id", "cluster"], dropna=False)["abandono"].agg(
        total_clientes="count",
        clientes_abandonaron="sum",
    )
    resumen = resumen.reset_index()
    resumen["clientes_abandonaron"] = resumen["clientes_abandonaron"].astype(int)
    resumen["tasa_abandono"] = (
        resumen["clientes_abandonaron"] / resumen["total_clientes"] * 100
    ).astype(float)
    return resumen.loc[:, columnas].sort_values("cluster_id").reset_index(drop=True)


def describir_clusters(resumen: pd.DataFrame | None) -> list[str]:
    """Genera descripciones neutrales para los clusters."""
    if resumen is None or resumen.empty:
        return []

    descripciones = []
    for fila in resumen.sort_values("cluster_id").to_dict("records"):
        cluster = fila.get("cluster", f"Clúster {int(fila.get('cluster_id', 0)) + 1}")
        total = int(fila.get("total_clientes", 0))
        rasgos = _rasgos_destacados(fila, resumen)
        if rasgos:
            detalle = ", ".join(rasgos)
            descripciones.append(
                f"{cluster}: agrupa {total} clientes con valores relativos destacados en {detalle}. "
                "Estas similitudes son matematicas y no implican causalidad ni jerarquia entre clusters."
            )
        else:
            descripciones.append(
                f"{cluster}: agrupa {total} clientes con patrones numericos similares. "
                "El numero del cluster no representa mayor o menor riesgo."
            )
    return descripciones


def _normalizar_columnas_cluster(df: pd.DataFrame) -> pd.DataFrame:
    datos = df.copy(deep=True)
    datos["cluster_id"] = pd.to_numeric(datos["cluster_id"], errors="coerce").astype("Int64")
    if "cluster" not in datos.columns:
        datos["cluster"] = datos["cluster_id"].map(lambda valor: f"Clúster {int(valor) + 1}")
    return datos


def _rasgos_destacados(fila: dict, resumen: pd.DataFrame) -> list[str]:
    rasgos = []
    for columna in COLUMNAS_SEGMENTACION:
        if columna not in resumen.columns or pd.isna(fila.get(columna)):
            continue
        minimo = resumen[columna].min()
        maximo = resumen[columna].max()
        valor = fila[columna]
        if pd.isna(minimo) or pd.isna(maximo) or minimo == maximo:
            continue
        if valor == maximo:
            rasgos.append(f"mayor promedio de {columna}")
        elif valor == minimo:
            rasgos.append(f"menor promedio de {columna}")
    return rasgos[:3]
