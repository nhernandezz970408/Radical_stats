from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from radical_stats.models import DataFrames

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Lineups.xlsx guarda Period como "periodo mod 2": 1 = primer periodo, 0 = segundo periodo.
LINEUPS_PERIOD_MAP = {1: 1, 0: 2}


def firma_datos(data_dir: Path | None = None) -> tuple:
    """Firma de los archivos de data/: (nombre, fecha de modificación, tamaño) de cada Excel y CSV.

    Se pasa como argumento a las funciones con st.cache_data: si un archivo cambia, la firma
    cambia y los datos se recargan sin reiniciar la app.
    """
    carpeta = DATA_DIR if data_dir is None else data_dir
    archivos = sorted([*carpeta.glob("*.xlsx"), *carpeta.glob("*.csv")])
    return tuple((a.name, a.stat().st_mtime_ns, a.stat().st_size) for a in archivos)


def load_data() -> DataFrames:
    """Carga las tablas; se vuelve a leer solo cuando cambia algún archivo de data/."""
    return _cargar_datos(firma_datos())


def load_penalty_codes() -> pd.DataFrame:
    """Códigos de falta con nombre y descripción en español (data/Penalty_codes.csv)."""
    return _cargar_codigos(firma_datos())


@st.cache_data(show_spinner=False)
def _cargar_datos(firma: tuple) -> DataFrames:
    """Lee y normaliza los Excel. `firma` solo sirve de llave de la caché (ver `firma_datos`)."""
    jam_table = pd.read_excel(DATA_DIR / "Jam_table.xlsx")
    rival_path = DATA_DIR / "Rival_Jam_table.xlsx"
    lineups = pd.read_excel(DATA_DIR / "Lineups.xlsx")
    penalty_tracker = pd.read_excel(DATA_DIR / "Penalty_tracker.xlsx")
    player_names = pd.read_excel(DATA_DIR / "Player_names.xlsx")
    time = pd.read_excel(DATA_DIR / "Time.xlsx")
    rival_jam_table = pd.read_excel(rival_path) if rival_path.exists() else pd.DataFrame()

    jam_table = _normalize_match_columns(jam_table)
    rival_jam_table = _normalize_match_columns(rival_jam_table)
    lineups = _normalize_match_columns(lineups)
    penalty_tracker = _normalize_match_columns(penalty_tracker)
    time = _normalize_match_columns(time)

    jam_table = _normalize_period(jam_table)
    rival_jam_table = _normalize_period(rival_jam_table)
    lineups = _normalize_period(lineups, mapping=LINEUPS_PERIOD_MAP)
    penalty_tracker = _normalize_period(penalty_tracker)
    time = _normalize_period(time)

    penalty_tracker["Player_number"] = penalty_tracker["Player_number"].astype(str).str.strip()
    player_names["Player_number"] = player_names["Player_number"].astype(str).str.strip()

    return DataFrames(
        jam_table=jam_table,
        lineups=lineups,
        penalty_tracker=penalty_tracker,
        player_names=player_names,
        time=time,
        rival_jam_table=rival_jam_table,
    )


@st.cache_data(show_spinner=False)
def _cargar_codigos(firma: tuple) -> pd.DataFrame:
    codes = pd.read_csv(DATA_DIR / "Penalty_codes.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    codes["code"] = codes["code"].str.strip()
    return codes


def _normalize_match_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.date
    if "Rival" in out.columns:
        out["Rival"] = out["Rival"].astype(str).str.strip()
    if "Team" in out.columns:
        out["Team"] = out["Team"].astype(str).str.strip()
    if "Team" in out.columns and "Rival" not in out.columns:
        out["Rival"] = out["Team"]
    return out


def _normalize_period(df: pd.DataFrame, mapping: dict[int, int] | None = None) -> pd.DataFrame:
    """Devuelve df con Period como entero 1/2.

    Con `mapping`, la codificación solo se traduce si la tabla contiene un 0 y todos
    sus valores son claves del mapeo (es decir, si no usa ya 1/2).
    """
    if "Period" not in df.columns:
        return df
    out = df.copy()
    period = pd.to_numeric(out["Period"], errors="coerce")
    values = set(period.dropna().astype(int).unique().tolist())
    if mapping is not None and 0 in values and values.issubset(mapping):
        period = period.map(mapping)
    out["Period"] = period.astype("Int64")
    return out
