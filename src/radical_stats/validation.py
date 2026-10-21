from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from radical_stats import textos as T
from radical_stats.jugadoras import mapa_nombres, nombres_repetidos
from radical_stats.lineups import ROLE_COLS, lineups_long
from radical_stats.models import DataFrames
from radical_stats.partidos import agregar_match_id, partidos_con_claves_repetidas

JAM_KEYS = ["Date", "Period", "Jam"]


def _clean(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def jammer_mismatches(frames: DataFrames) -> pd.DataFrame:
    """Jams donde la Jammer de Lineups difiere de la de Jam_table."""
    jam, lineups = frames.jam_table, frames.lineups
    if jam.empty or lineups.empty:
        return pd.DataFrame(columns=JAM_KEYS)
    left = jam[JAM_KEYS + ["Jammer"]].assign(Jammer=_clean(jam["Jammer"]))
    right = lineups[JAM_KEYS + ["Jammer"]].assign(Jammer=_clean(lineups["Jammer"]))
    merged = left.merge(right, on=JAM_KEYS, how="inner", suffixes=("_jam_table", "_lineups"))
    return merged[merged["Jammer_jam_table"] != merged["Jammer_lineups"]]


def penalties_off_track(frames: DataFrames) -> pd.DataFrame:
    """Faltas de jugadoras que no están en la alineación de ese jam."""
    pen, lineups = frames.penalty_tracker, frames.lineups
    if pen.empty or lineups.empty:
        return pd.DataFrame(columns=JAM_KEYS + ["Player_number"])
    present = lineups_long(lineups)[JAM_KEYS + ["Player_number"]].assign(_present=True)
    checked = pen.assign(Player_number=_clean(pen["Player_number"])).merge(
        present, on=JAM_KEYS + ["Player_number"], how="left"
    )
    return checked[checked["_present"].isna()].drop(columns="_present")


def matches_without_time(frames: DataFrames) -> list[tuple]:
    """Partidos (Date, Rival) de Jam_table sin filas en Time."""
    jam, time = frames.jam_table, frames.time
    if jam.empty:
        return []
    matches = set(map(tuple, jam[["Date", "Rival"]].dropna().drop_duplicates().to_numpy()))
    if not time.empty:
        matches -= set(map(tuple, time[["Date", "Rival"]].dropna().drop_duplicates().to_numpy()))
    return sorted(matches, key=str)


def validate_jammers(frames: DataFrames) -> list[str]:
    bad = jammer_mismatches(frames)
    return [
        T.AVISO_JAMMER.format(
            fecha=r.Date, periodo=r.Period, jam=r.Jam,
            jammer_jams=r.Jammer_jam_table, jammer_alineaciones=r.Jammer_lineups,
        )
        for r in bad.itertuples()
    ]


def validate_penalties(frames: DataFrames) -> list[str]:
    bad = penalties_off_track(frames)
    return [
        T.AVISO_FALTA.format(jugadora=r.Player_number, fecha=r.Date, periodo=r.Period, jam=r.Jam)
        for r in bad.itertuples()
    ]


def validate_time(frames: DataFrames) -> list[str]:
    return [
        T.AVISO_SIN_TIEMPO.format(fecha=date, rival=rival)
        for date, rival in matches_without_time(frames)
    ]


def validate_all(frames: DataFrames) -> list[str]:
    return validate_jammers(frames) + validate_penalties(frames) + validate_time(frames)


def validate_partidos_repetidos(frames: DataFrames) -> list[str]:
    """Avisos de partidos que repiten jams (posibles partidos distintos con la misma fecha y rival)."""
    return [T.AVISO_PARTIDO_REPETIDO.format(partido=m) for m in partidos_con_claves_repetidas(frames)]


# --- Chequeos de la página de calidad de datos ---------------------------------------


@dataclass(frozen=True)
class Chequeo:
    """Resultado de un chequeo: cuántas filas están afectadas y cuáles son."""

    clave: str
    titulo: str
    descripcion: str
    cantidad: int
    filas: pd.DataFrame
    detalle: pd.DataFrame | None = None  # tabla de referencia que se muestra aunque el estado sea OK

    @property
    def estado(self) -> str:
        return T.ESTADO_OK if self.cantidad == 0 else T.ESTADO_AVISO


def _chequeo(clave: str, filas: pd.DataFrame, detalle: pd.DataFrame | None = None) -> Chequeo:
    titulo, descripcion = T.CHEQUEOS[clave]
    return Chequeo(clave, titulo, descripcion, len(filas), filas.reset_index(drop=True), detalle)


_TABLAS_UNA_FILA_POR_JAM = (
    ("jam_table", T.TABLA_JAMS),
    ("rival_jam_table", T.TABLA_JAMS_RIVAL),
    ("lineups", T.TABLA_ALINEACIONES),
    ("time", T.TABLA_TIEMPOS),
)


def jams_por_partido(frames: DataFrames) -> pd.DataFrame:
    """Jams por partido y periodo en Jam_table, Rival_Jam_table y Lineups (columnas jam_table, rival, lineups)."""
    columns = ["match_id", "Period", "jam_table", "rival", "lineups"]
    partes = []
    for nombre, tabla in (("jam_table", frames.jam_table), ("rival", frames.rival_jam_table), ("lineups", frames.lineups)):
        tabla = agregar_match_id(tabla)
        if tabla.empty or "match_id" not in tabla.columns:
            continue
        partes.append(tabla.groupby(["match_id", "Period"]).size().rename(nombre))
    if not partes:
        return pd.DataFrame(columns=columns)
    out = pd.concat(partes, axis=1).fillna(0).astype(int).reset_index()
    for nombre in columns[2:]:
        if nombre not in out.columns:
            out[nombre] = 0
    return out[columns]


def jams_por_partido_total(frames: DataFrames) -> pd.DataFrame:
    """Jams de cada partido en Jam_table (40, 45, 38 y 28 con los datos de hoy)."""
    jam = agregar_match_id(frames.jam_table)
    if jam.empty:
        return pd.DataFrame(columns=["match_id", "jams"])
    return jam.groupby("match_id").size().rename("jams").reset_index()


def chequeo_jams_por_partido(frames: DataFrames) -> Chequeo:
    """Los jams por partido y periodo deben ser iguales en las tres tablas."""
    conteos = jams_por_partido(frames)
    distintos = conteos[(conteos["jam_table"] != conteos["rival"]) | (conteos["jam_table"] != conteos["lineups"])]
    return _chequeo("jams_por_partido", distintos, detalle=jams_por_partido_total(frames))


def claves_duplicadas(frames: DataFrames) -> pd.DataFrame:
    """Filas con (Date, Period, Jam) repetida en las tablas que deben tener una fila por jam."""
    partes = []
    for atributo, nombre in _TABLAS_UNA_FILA_POR_JAM:
        tabla = getattr(frames, atributo)
        if tabla.empty:
            continue
        repetidas = tabla[tabla.duplicated(subset=JAM_KEYS, keep=False)]
        partes.append(repetidas[JAM_KEYS].assign(Tabla=nombre))
    if not partes:
        return pd.DataFrame(columns=["Tabla"] + JAM_KEYS)
    return pd.concat(partes, ignore_index=True)[["Tabla"] + JAM_KEYS]


def chequeo_claves_duplicadas(frames: DataFrames) -> Chequeo:
    return _chequeo("claves_duplicadas", claves_duplicadas(frames))


def chequeo_partidos_sin_time(frames: DataFrames) -> Chequeo:
    sin_tiempo = pd.DataFrame(matches_without_time(frames), columns=["Date", "Rival"])
    return _chequeo("partidos_sin_time", sin_tiempo)


def problemas_de_nombres(frames: DataFrames) -> pd.DataFrame:
    """Jugadoras (de alineaciones y faltas) sin nombre en Player_names y nombres repetidos."""
    nombres = frames.player_names
    mapa = mapa_nombres(nombres)
    en_uso = set(lineups_long(frames.lineups)["Player_number"]) if not frames.lineups.empty else set()
    if not frames.penalty_tracker.empty:
        en_uso |= set(frames.penalty_tracker["Player_number"].astype(str).str.strip())
    sin_nombre = pd.DataFrame(
        [{"Player_number": n, "Name": "", "Problema": T.PROBLEMA_SIN_NOMBRE} for n in sorted(en_uso - set(mapa))],
        columns=["Player_number", "Name", "Problema"],
    )
    repetidos = nombres_repetidos(mapa)
    duplicados = pd.DataFrame(
        [{"Player_number": n, "Name": nombre, "Problema": T.PROBLEMA_NOMBRE_REPETIDO}
         for n, nombre in mapa.items() if nombre in repetidos],
        columns=["Player_number", "Name", "Problema"],
    )
    duplicados = duplicados.sort_values(
        ["Name", "Player_number"], key=lambda col: col.map(lambda v: (len(str(v)), str(v)))
    )
    return pd.concat([sin_nombre, duplicados], ignore_index=True)


def chequeo_nombres(frames: DataFrames) -> Chequeo:
    return _chequeo("nombres", problemas_de_nombres(frames))


def valores_faltantes_lineups(frames: DataFrames) -> pd.DataFrame:
    """Filas de Lineups con «?» o vacíos en Jammer, Pivot o Bloques."""
    lineups = frames.lineups
    if lineups.empty:
        return pd.DataFrame(columns=JAM_KEYS)
    texto = lineups[ROLE_COLS].apply(lambda col: col.astype(str).str.strip().str.lower())
    faltante = texto.isin(["?", "", "nan", "none", "<na>"]).any(axis=1)
    return lineups.loc[faltante, JAM_KEYS + ROLE_COLS]


def chequeo_valores_faltantes(frames: DataFrames) -> Chequeo:
    return _chequeo("valores_faltantes", valores_faltantes_lineups(frames))


def faltas_unknown(frames: DataFrames) -> pd.DataFrame:
    """Faltas cuyo código es «Unknown» o está vacío."""
    pen = frames.penalty_tracker
    if pen.empty:
        return pd.DataFrame(columns=JAM_KEYS + ["Player_number", "Penalty_code"])
    codigo = pen["Penalty_code"].astype(str).str.strip().str.lower()
    return pen.loc[codigo.isin(["unknown", "", "nan"]), JAM_KEYS + ["Player_number", "Penalty_code"]]


def chequeo_faltas_unknown(frames: DataFrames) -> Chequeo:
    return _chequeo("faltas_unknown", faltas_unknown(frames))


def chequeo_faltas_fuera_de_pista(frames: DataFrames) -> Chequeo:
    filas = penalties_off_track(frames)
    return _chequeo("faltas_fuera_de_pista", filas[[c for c in JAM_KEYS + ["Player_number", "Penalty_code"] if c in filas]])


def chequeo_jammer(frames: DataFrames) -> Chequeo:
    return _chequeo("jammer", jammer_mismatches(frames))


def chequeos_calidad(frames: DataFrames) -> list[Chequeo]:
    """Todos los chequeos de la página de calidad de datos, en orden."""
    return [
        chequeo_jams_por_partido(frames),
        chequeo_claves_duplicadas(frames),
        chequeo_partidos_sin_time(frames),
        chequeo_nombres(frames),
        chequeo_valores_faltantes(frames),
        chequeo_faltas_unknown(frames),
        chequeo_faltas_fuera_de_pista(frames),
        chequeo_jammer(frames),
    ]
