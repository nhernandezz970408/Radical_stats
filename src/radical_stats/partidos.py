"""Identificador de partido (match_id) en un solo lugar.

Un partido se identifica por su fecha y su rival: «2025-11-01 | Pacha Mamis». Si dos partidos
distintos compartieran fecha y rival, sus filas se mezclarían bajo el mismo match_id; por eso
`partidos_con_claves_repetidas` los detecta para avisar en vez de mezclarlos en silencio.
"""

from __future__ import annotations

import pandas as pd

from radical_stats.models import DataFrames

SEPARADOR = " | "
JAM_KEYS = ["Date", "Period", "Jam"]


def crear_match_id(df: pd.DataFrame) -> pd.Series:
    """match_id de cada fila a partir de Date y Rival."""
    return df["Date"].astype(str) + SEPARADOR + df["Rival"].astype(str)


def agregar_match_id(df: pd.DataFrame) -> pd.DataFrame:
    """Copia de df con la columna match_id (si ya la tiene o le faltan Date o Rival, la devuelve igual)."""
    if df.empty or "match_id" in df.columns or "Date" not in df.columns or "Rival" not in df.columns:
        return df
    return df.assign(match_id=crear_match_id(df))


def agregar_match_id_a_frames(frames: DataFrames) -> DataFrames:
    """Todas las tablas con match_id."""
    return DataFrames(
        jam_table=agregar_match_id(frames.jam_table),
        lineups=agregar_match_id(frames.lineups),
        penalty_tracker=agregar_match_id(frames.penalty_tracker),
        player_names=frames.player_names,
        time=agregar_match_id(frames.time),
        rival_jam_table=agregar_match_id(frames.rival_jam_table),
    )


def partir_match_id(match_id: str) -> tuple[str, str]:
    """«2025-11-01 | Pacha Mamis» -> («2025-11-01», «Pacha Mamis»); sin separador, (match_id, «»)."""
    fecha, _, rival = str(match_id).partition(SEPARADOR)
    return fecha, rival


def opciones_de_partidos(frames: DataFrames) -> list[str]:
    """match_id de cada partido de Jam_table, ordenados."""
    jam = frames.jam_table
    if jam.empty or "Date" not in jam.columns or "Rival" not in jam.columns:
        return []
    partidos = jam[["Date", "Rival"]].dropna().drop_duplicates()
    return sorted(crear_match_id(partidos).tolist())


def partidos_con_claves_repetidas(frames: DataFrames) -> list[str]:
    """Partidos cuyo Jam_table repite (Period, Jam): señal de dos partidos con la misma fecha y rival."""
    jam = agregar_match_id(frames.jam_table)
    if jam.empty or "match_id" not in jam.columns:
        return []
    repetidos = jam[jam.duplicated(subset=["match_id", "Period", "Jam"], keep=False)]
    return sorted(repetidos["match_id"].unique().tolist())
