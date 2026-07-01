"""Helpers de UI compartidos — patron de mensajes: que paso / por que / que hacer.

Uso:
    from utils.ui_helpers import msg_info, msg_exito, msg_advertencia, msg_error

    msg_error(
        "No se pudo cargar el archivo.",
        causa="El formato no es CSV valido.",
        accion="Verifica que el archivo tenga extension .csv y vuelve a cargarlo.",
    )
"""
from __future__ import annotations

import streamlit as st


def _componer(titulo: str, causa: str | None, accion: str | None) -> str:
    partes = [titulo]
    if causa:
        partes.append(f"**Por que:** {causa}")
    if accion:
        partes.append(f"**Que hacer:** {accion}")
    return "  \n".join(partes)


def msg_info(titulo: str, *, causa: str | None = None, accion: str | None = None) -> None:
    st.info(_componer(titulo, causa, accion))


def msg_exito(titulo: str, *, causa: str | None = None, accion: str | None = None) -> None:
    st.success(_componer(titulo, causa, accion))


def msg_advertencia(titulo: str, *, causa: str | None = None, accion: str | None = None) -> None:
    st.warning(_componer(titulo, causa, accion))


def msg_error(titulo: str, *, causa: str | None = None, accion: str | None = None) -> None:
    st.error(_componer(titulo, causa, accion))
