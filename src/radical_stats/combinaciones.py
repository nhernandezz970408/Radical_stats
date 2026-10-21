"""Combinaciones de jugadoras (duplas, ternas, cuartetos y quintetos) y sus estadísticas.

La unidad de análisis es el pack: por jam, las jugadoras con Role Pivot o Bloque, sin importar
la posición de planilla ni el orden. Con `incluir_jammer` se usan las cinco jugadoras del jam.
Cada jam aporta a varias combinaciones a la vez, así que las filas no son independientes.
"""

from __future__ import annotations

from itertools import combinations

import pandas as pd

from radical_stats import config as cfg
from radical_stats import textos as T
from radical_stats.jugadoras import etiqueta_jugadora, nombres_repetidos
from radical_stats.lineups import lineups_long
from radical_stats.metrics import (
    JAM_KEYS,
    _bootstrap_interval,
    box_state_by_jam,
    jam_facts,
    penalties_by_jam,
)
from radical_stats.models import DataFrames

PACK_ROLES = ("Pivot", "Bloque")


def _orden_jugadora(numero: str) -> tuple[int, str]:
    return (len(numero), numero)


def combos_por_jam(long: pd.DataFrame, tamano: int, incluir_jammer: bool = False) -> pd.DataFrame:
    """Una fila por jam y combinación de `tamano` jugadoras (columna `combo`, tupla ordenada).

    Usa el pack (Pivot y Bloque) o, con `incluir_jammer`, las jugadoras de los cinco roles. Un
    jam con menos jugadoras válidas que `tamano` no aporta a ese tamaño; los valores «?» ya
    fueron descartados por `lineups_long`, así que el jam aporta solo con las jugadoras válidas.
    """
    columns = JAM_KEYS + ["match_id", "combo"]
    if long.empty:
        return pd.DataFrame(columns=columns)
    pool = long if incluir_jammer else long[long["Role"].isin(PACK_ROLES)]
    rows = []
    for (fecha, periodo, jam, match_id), grupo in pool.groupby(JAM_KEYS + ["match_id"], sort=False):
        jugadoras = sorted(set(grupo["Player_number"]), key=_orden_jugadora)
        if len(jugadoras) < tamano:
            continue
        for combo in combinations(jugadoras, tamano):
            rows.append((fecha, periodo, jam, match_id, combo))
    return pd.DataFrame(rows, columns=columns)


def estadisticas_combinaciones(
    frames: DataFrames,
    tamano: int,
    incluir_jammer: bool = False,
    minimo: int | None = None,
    jammer: str | None = None,
    incluye: list[str] | None = None,
) -> pd.DataFrame:
    """Estadísticas por combinación de `tamano` jugadoras, ordenadas por jams.

    Columnas: combo, tamano, jams, partidos, pts_for, pts_against, eff, eff_rel (por jam, relativo
    al partido), rival_lead_pct, faltas_por_jam (faltas del equipo), caja_pct (% de jams con caja),
    ic_bajo / ic_alto (intervalo del 80 % de eff_rel, con al menos BOOTSTRAP_MIN_JAMS jams) y muestra.

    - `minimo`: jams mínimos para la etiqueta Muestra (por defecto el de config para el tamaño).
    - `jammer`: solo jams con esa jammer nuestra (para comparar con la misma jammer).
    - `incluye`: solo combinaciones que contienen a todas esas jugadoras.
    Muestra vale «Baja» (jams bajo el mínimo), «Un partido» (apareció en un solo partido) u «Ok».
    """
    minimo = cfg.MIN_JAMS_COMBINACION.get(tamano, 3) if minimo is None else minimo
    columns = ["combo", "tamano", "jams", "partidos", "pts_for", "pts_against", "eff", "eff_rel",
               "rival_lead_pct", "faltas_por_jam", "caja_pct", "ic_bajo", "ic_alto", "muestra"]
    combos = combos_por_jam(lineups_long(frames.lineups), tamano, incluir_jammer)
    facts = jam_facts(frames)
    if combos.empty or facts.empty:
        return pd.DataFrame(columns=columns)

    jams = (
        facts[JAM_KEYS + ["match_id", "Jammer", "pts_for", "pts_against", "eff", "eff_rel", "rival_lead"]]
        .merge(penalties_by_jam(frames), on=JAM_KEYS, how="left")
        .merge(box_state_by_jam(frames)[JAM_KEYS + ["has_box"]], on=JAM_KEYS, how="left")
    )
    jams["has_box"] = jams["has_box"].fillna(False).astype(bool)
    rows = combos.drop(columns=["match_id"]).merge(jams, on=JAM_KEYS, how="inner")
    if jammer is not None:
        rows = rows[rows["Jammer"] == str(jammer).strip()]
    if incluye:
        buscadas = [str(p).strip() for p in incluye]
        rows = rows[rows["combo"].map(lambda c: all(p in c for p in buscadas))]
    if rows.empty:
        return pd.DataFrame(columns=columns)

    records = []
    for combo, grupo in rows.groupby("combo", sort=False):
        bajo, alto = _bootstrap_interval(grupo["eff_rel"].to_numpy(dtype=float))
        n_partidos = int(grupo["match_id"].nunique())
        if len(grupo) < minimo:
            muestra = T.MUESTRA_CORTA_BAJA
        elif n_partidos == 1:
            muestra = T.MUESTRA_UN_PARTIDO
        else:
            muestra = T.MUESTRA_CORTA_OK
        records.append(
            {
                "combo": combo,
                "tamano": tamano,
                "jams": len(grupo),
                "partidos": n_partidos,
                "pts_for": grupo["pts_for"].mean(),
                "pts_against": grupo["pts_against"].mean(),
                "eff": grupo["eff"].mean(),
                "eff_rel": grupo["eff_rel"].mean(),
                "rival_lead_pct": 100 * grupo["rival_lead"].mean(),
                "faltas_por_jam": grupo["penalties"].mean(),
                "caja_pct": 100 * grupo["has_box"].mean(),
                "ic_bajo": bajo,
                "ic_alto": alto,
                "muestra": muestra,
            }
        )
    return pd.DataFrame(records, columns=columns).sort_values(
        ["jams", "eff_rel"], ascending=[False, False]
    ).reset_index(drop=True)


def mejores_y_peores(stats: pd.DataFrame, minimo: int, k: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las k mejores y k peores por eff_rel entre las combinaciones que superan el mínimo.

    Las «peores» no repiten filas que ya salieron en las «mejores».
    """
    elegibles = stats[stats["jams"] >= minimo].sort_values(
        ["eff_rel", "jams"], ascending=[False, False]
    ).reset_index(drop=True)
    mejores = elegibles.head(k)
    peores = elegibles.drop(mejores.index).tail(k).sort_values("eff_rel").reset_index(drop=True)
    return mejores.reset_index(drop=True), peores


def etiquetas_combinacion(combo: tuple, nombres: dict[str, str]) -> str:
    """Nombres de las jugadoras de una combinación unidos con « + » (con número si el nombre se repite)."""
    repetidos = nombres_repetidos(nombres)
    return " + ".join(etiqueta_jugadora(p, nombres, repetidos) for p in combo)


def matriz_duplas(stats_duplas: pd.DataFrame, minimo: int) -> pd.DataFrame:
    """Duplas en formato jugadora x jugadora (simétrico): a, b, eff_rel, jams y si está bajo el mínimo."""
    if stats_duplas.empty:
        return pd.DataFrame(columns=["a", "b", "eff_rel", "jams", "bajo_minimo"])
    registros = []
    for fila in stats_duplas.itertuples():
        a, b = fila.combo
        for x, y in ((a, b), (b, a)):
            registros.append(
                {"a": x, "b": y, "eff_rel": fila.eff_rel, "jams": fila.jams, "bajo_minimo": fila.jams < minimo}
            )
    return pd.DataFrame(registros)
