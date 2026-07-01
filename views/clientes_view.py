"""Vista de consulta de clientes almacenados en SQLite."""

from typing import Any

import pandas as pd
import streamlit as st

from config.settings import COLUMNAS_CLIENTES_TABLA, COLUMNAS_ORDEN_CLIENTES
from services.cliente_service import (
    contar_resultados,
    filtrar_clientes,
    formatear_abandono,
    obtener_cliente_por_id,
    obtener_opciones_filtro,
    ordenar_clientes,
    preparar_tabla_clientes,
)
from services.fuente_datos_service import cargar_clientes_desde_sqlite


ABANDONO_OPCIONES = {
    "Todos": None,
    "Permanece": 0,
    "Abandonó": 1,
}


def mostrar_clientes() -> None:
    """Renderiza busqueda, filtros, resultados y ficha de clientes."""
    st.title("Clientes")
    st.write("Consulta clientes almacenados en la base de datos SQLite.")
    st.caption("Fuente de datos: vista `comportamiento_cliente` de SQLite.")

    try:
        df = cargar_clientes_desde_sqlite()
    except FileNotFoundError as exc:
        st.warning(str(exc))
        return
    except RuntimeError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.info("La base de datos no contiene clientes disponibles.")
        return

    st.metric("Total de clientes disponibles", len(df))

    termino = st.text_input("Buscar por ID o nombre", placeholder="Ejemplo: CXM0001 o Ana")
    ciudades = st.multiselect("Ciudad", obtener_opciones_filtro(df, "ciudad"))
    tipos_contrato = st.multiselect(
        "Tipo de contrato",
        obtener_opciones_filtro(df, "tipo_contrato"),
    )
    planes = st.multiselect("Plan", obtener_opciones_filtro(df, "plan"))
    abandono_label = st.selectbox("Estado de abandono", list(ABANDONO_OPCIONES.keys()))

    col_orden, col_sentido = st.columns(2)
    with col_orden:
        columna_orden = st.selectbox("Ordenar por", COLUMNAS_ORDEN_CLIENTES)
    with col_sentido:
        sentido = st.radio("Sentido", ["Ascendente", "Descendente"], horizontal=True)

    resultados = filtrar_clientes(
        df,
        termino=termino,
        ciudades=ciudades,
        tipos_contrato=tipos_contrato,
        planes=planes,
        abandono=ABANDONO_OPCIONES[abandono_label],
    )
    resultados = ordenar_clientes(
        resultados,
        columna_orden,
        ascendente=sentido == "Ascendente",
    )

    _mostrar_resultados(resultados)
    _mostrar_ficha_cliente(df, resultados)


def _mostrar_resultados(resultados: pd.DataFrame) -> None:
    """Muestra cantidad y tabla de resultados."""
    st.subheader("Resultados")
    total = contar_resultados(resultados)
    st.write(f"Clientes encontrados: `{total}`")

    if total == 0:
        st.warning("No hay clientes que coincidan con la busqueda y filtros seleccionados.")
        return

    tabla = preparar_tabla_clientes(resultados, COLUMNAS_CLIENTES_TABLA)
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def _mostrar_ficha_cliente(df: pd.DataFrame, resultados: pd.DataFrame) -> None:
    """Permite seleccionar un cliente de los resultados y muestra su ficha."""
    if resultados.empty or "id_cliente" not in resultados.columns:
        return

    st.subheader("Ficha de cliente")
    opciones = resultados.apply(_crear_etiqueta_cliente, axis=1).tolist()
    seleccion = st.selectbox("Selecciona un cliente", opciones)
    id_cliente = seleccion.split(" - ", maxsplit=1)[0]
    cliente = obtener_cliente_por_id(df, id_cliente)

    if cliente is None:
        st.warning("No fue posible recuperar el cliente seleccionado.")
        return

    _renderizar_ficha(cliente)


def _crear_etiqueta_cliente(fila: pd.Series) -> str:
    """Crea etiqueta legible para seleccionar un cliente."""
    return f"{fila.get('id_cliente', '')} - {fila.get('nombre', '')}"


def _renderizar_ficha(cliente: dict[str, Any]) -> None:
    """Muestra los campos principales de un cliente."""
    campos = [
        ("ID", cliente.get("id_cliente")),
        ("Nombre", cliente.get("nombre")),
        ("Edad", cliente.get("edad")),
        ("Ciudad", cliente.get("ciudad")),
        ("Región", cliente.get("region")),
        ("Antiguedad en meses", cliente.get("antiguedad_meses")),
        ("Tipo de contrato", cliente.get("tipo_contrato")),
        ("Plan", cliente.get("plan")),
        ("Monto mensual", cliente.get("monto_mensual")),
        ("Cantidad de servicios", cliente.get("cantidad_servicios")),
        ("Reclamos ultimos 6 meses", cliente.get("reclamos_ultimos_6_meses")),
        ("Pagos atrasados", cliente.get("pagos_atrasados")),
        ("Dias sin uso", cliente.get("dias_sin_uso")),
        ("Satisfaccion", cliente.get("satisfaccion")),
        ("Estado de abandono", formatear_abandono(cliente.get("abandono"))),
    ]

    for etiqueta, valor in campos:
        if valor is not None and not pd.isna(valor):
            st.write(f"**{etiqueta}:** {valor}")
