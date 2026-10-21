from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from radical_stats import textos as T
from radical_stats.filters import filter_by_match, filter_by_period
from radical_stats.models import DataFrames
from radical_stats.partidos import agregar_match_id_a_frames, opciones_de_partidos
from radical_stats.validation import (
    validate_jammers,
    validate_partidos_repetidos,
    validate_penalties,
    validate_time,
)


@dataclass(frozen=True)
class Filtros:
    """Resultado de los filtros de la barra lateral de la página de equipo."""

    filtrados: DataFrames  # partidos y periodos seleccionados
    resto: DataFrames  # partidos NO seleccionados (mismos periodos), para comparar
    seleccionados: list[str]
    opciones: list[str]
    periodos: list[int]


def _reiniciar_si_vacio(key: str, opciones: list) -> None:
    """Callback: un filtro no puede quedar vacío; se marcan todas las opciones y se avisa."""
    if not st.session_state.get(key):
        st.session_state[key] = list(opciones)
        st.session_state[f"{key}_aviso"] = True


def _multiselect_no_vacio(label: str, opciones: list, key: str, aviso: str, **kwargs) -> list:
    """Multiselect que arranca con todo marcado y nunca queda vacío (avisa y vuelve a marcar todo)."""
    if key not in st.session_state:
        st.session_state[key] = list(opciones)
    seleccion = st.multiselect(
        label, options=opciones, key=key, on_change=_reiniciar_si_vacio, args=(key, opciones),
        placeholder=T.PLACEHOLDER_MULTISELECCION, **kwargs,
    )
    if st.session_state.pop(f"{key}_aviso", False) or not seleccion:
        st.warning(aviso)
        seleccion = list(opciones)
    return seleccion


def aplicar_filtros(frames: DataFrames, key_prefix: str = "", con_periodo: bool = True) -> Filtros:
    """Filtros de partido (y periodo) en la barra lateral; ninguno puede quedar vacío."""
    todos = agregar_match_id_a_frames(frames)
    opciones = opciones_de_partidos(frames)
    periodos_disponibles = (
        sorted(todos.jam_table["Period"].dropna().astype(int).unique().tolist())
        if "Period" in todos.jam_table.columns else []
    )
    with st.sidebar:
        st.header(T.FILTROS)
        seleccionados = _multiselect_no_vacio(
            T.FILTRO_PARTIDO, opciones, f"{key_prefix}_matches", T.AVISO_SIN_PARTIDOS,
            help=T.AYUDA_FILTRO_PARTIDO,
        )
        periodos = periodos_disponibles
        if con_periodo:
            periodos = _multiselect_no_vacio(
                T.FILTRO_PERIODO, periodos_disponibles, f"{key_prefix}_periods", T.AVISO_SIN_PERIODOS,
                format_func=T.periodo_etiqueta, help=T.AYUDA_FILTRO_PERIODO,
            )
    por_periodo = filter_by_period(todos, periodos)
    restantes = [o for o in opciones if o not in seleccionados]
    return Filtros(
        filtrados=filter_by_match(por_periodo, seleccionados),
        resto=filter_by_match(por_periodo, restantes),
        seleccionados=seleccionados,
        opciones=opciones,
        periodos=periodos,
    )


def apply_global_filters(frames: DataFrames, key_prefix: str = "") -> DataFrames:
    """Filtro de partidos (solo); las páginas que lo necesitan agregan su propio filtro de periodo."""
    return aplicar_filtros(frames, key_prefix, con_periodo=False).filtrados


def aplicar_estilo_ancho() -> None:
    """Contenido más ancho y compacto (para que la pestaña Resumen quepa en pantalla)."""
    st.markdown(
        """
<style>
div.block-container {
    max-width: 95%;
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def show_validation_warnings(frames: DataFrames) -> None:
    """Muestra avisos de calidad de datos sin bloquear la página."""
    for validate in (validate_partidos_repetidos, validate_jammers, validate_penalties, validate_time):
        warnings = validate(frames)
        if warnings:
            bullets = "\n".join(f"- {w}" for w in warnings)
            st.warning(f"{T.AVISOS_CALIDAD}\n\n{bullets}")


def show_empty_state() -> None:
    st.warning(T.SIN_DATOS_FILTROS)
