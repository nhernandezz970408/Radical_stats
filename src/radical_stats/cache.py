"""Cálculos pesados con st.cache_data (bootstrap y combinaciones).

Las funciones reciben los datos ya filtrados (`_frames`, que Streamlit no vuelve a hashear) y una
`clave` que los identifica: la firma de los archivos de data/, los partidos y los periodos. Si un
Excel cambia, la firma cambia y se recalcula.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from radical_stats import equipo, perfil
from radical_stats.combinaciones import estadisticas_combinaciones
from radical_stats.data_loader import firma_datos
from radical_stats.metrics import effective_by_jam
from radical_stats.models import DataFrames
from radical_stats.validation import Chequeo
from radical_stats.validation import chequeos_calidad as _chequeos_calidad


def clave_filtrado(frames: DataFrames) -> tuple:
    """Llave de caché de unos datos filtrados: firma de archivos, partidos y periodos presentes."""
    jam = frames.jam_table
    partidos = tuple(sorted(jam["match_id"].unique())) if "match_id" in jam.columns else ()
    periodos = tuple(sorted(jam["Period"].dropna().unique())) if "Period" in jam.columns else ()
    return (firma_datos(), partidos, periodos)


@st.cache_data(show_spinner=False)
def efectividad_jugadoras(_frames: DataFrames, clave: tuple) -> pd.DataFrame:
    return equipo.efectividad_jugadoras(_frames)


@st.cache_data(show_spinner=False)
def top_ternas(_frames: DataFrames, clave: tuple) -> pd.DataFrame:
    return equipo.top_ternas(_frames)


@st.cache_data(show_spinner=False)
def combinaciones(
    _frames: DataFrames, clave: tuple, tamano: int, incluir_jammer: bool,
    minimo: int, jammer: str | None, incluye: tuple,
) -> pd.DataFrame:
    return estadisticas_combinaciones(
        _frames, tamano, incluir_jammer=incluir_jammer, minimo=minimo,
        jammer=jammer, incluye=list(incluye) if incluye else None,
    )


@st.cache_data(show_spinner=False)
def jammers(_frames: DataFrames, clave: tuple) -> list[str]:
    jams = effective_by_jam(_frames)
    return sorted(jams["Jammer"].unique().tolist(), key=lambda x: (len(x), x)) if not jams.empty else []


@st.cache_data(show_spinner=False)
def vista_general_jugadoras(_frames: DataFrames, clave: tuple) -> pd.DataFrame:
    return perfil.players_overview(_frames)


@st.cache_data(show_spinner=False)
def perfil_jugadora(_frames: DataFrames, clave: tuple, numero: str) -> perfil.PerfilJugadora:
    return perfil.player_profile(_frames, numero)


@st.cache_data(show_spinner=False)
def chequeos_calidad(_frames: DataFrames, clave: tuple) -> list[Chequeo]:
    """Chequeos de calidad de datos; la caché se invalida cuando cambia algún archivo de data/."""
    return _chequeos_calidad(_frames)
