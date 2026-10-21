from __future__ import annotations

import pandas as pd

from radical_stats.partidos import crear_match_id

# Columnas de origen de Lineups.xlsx. Block_1/2/3 son posiciones de la planilla, no de la cancha.
ROLE_COLS = ["Jammer", "Pivot", "Block_1", "Block_2", "Block_3"]
ROLES = ["Jammer", "Pivot", "Bloque"]
_ROLE_PRIORITY = {"Jammer": 0, "Pivot": 1, "Bloque": 2}
_INVALID = {"", "0", "?", "nan", "none", "<na>"}
LONG_COLUMNS = [
    "Date", "Period", "Jam", "match_id", "Player_number", "Role", "Start_box", "Finish_box",
]


def _role_of(col: str) -> str:
    return "Bloque" if col.startswith("Block_") else col


def _clean_player(series: pd.Series) -> pd.Series:
    out = series.astype(str).str.strip()
    # Los números leídos como decimales (p. ej. 16.0) deben coincidir con la forma "16".
    return out.str.replace(r"^(\d+)\.0+$", r"\1", regex=True)


def lineups_long(lineups: pd.DataFrame) -> pd.DataFrame:
    """Una fila por jugadora por jam, con Role Jammer, Pivot o Bloque."""
    if lineups.empty:
        return pd.DataFrame(columns=LONG_COLUMNS)

    base = lineups[["Date", "Period", "Jam"]].copy()
    if "match_id" in lineups.columns:
        base["match_id"] = lineups["match_id"]
    else:
        base["match_id"] = crear_match_id(lineups)

    chunks = []
    for col in ROLE_COLS:
        if col not in lineups.columns:
            continue
        chunk = base.copy()
        chunk["Player_number"] = _clean_player(lineups[col])
        chunk["Role"] = _role_of(col)
        for box in ("Start", "Finish"):
            src = f"{col}_{box}_jam_Box"
            values = lineups[src] if src in lineups.columns else pd.Series(0, index=lineups.index)
            chunk[f"{box}_box"] = pd.to_numeric(values, errors="coerce").fillna(0).astype(int)
        chunks.append(chunk)

    long = pd.concat(chunks, ignore_index=True)
    long = long[~long["Player_number"].str.lower().isin(_INVALID)].copy()

    long["_priority"] = long["Role"].map(_ROLE_PRIORITY)
    long = (
        long.sort_values("_priority", kind="stable")
        .drop_duplicates(subset=["Date", "Period", "Jam", "Player_number"], keep="first")
        .drop(columns="_priority")
        .sort_values(["Date", "Period", "Jam"], kind="stable")
        .reset_index(drop=True)
    )
    return long[LONG_COLUMNS]


def count_incomplete_jams(lineups: pd.DataFrame, long: pd.DataFrame | None = None) -> int:
    """Jams que no tienen las cinco jugadoras (jammer + pivot + 3 bloques)."""
    if lineups.empty:
        return 0
    if long is None:
        long = lineups_long(lineups)
    keys = ["Date", "Period", "Jam"]
    total = len(lineups[keys].drop_duplicates())
    complete = long.groupby(keys).size().eq(5).sum() if not long.empty else 0
    return int(total - complete)
