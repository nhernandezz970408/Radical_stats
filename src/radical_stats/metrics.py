from __future__ import annotations

import numpy as np
import pandas as pd

from radical_stats import config as cfg
from radical_stats.lineups import ROLES, lineups_long
from radical_stats.models import DataFrames
from radical_stats.partidos import agregar_match_id, crear_match_id


def build_team_metrics(frames: DataFrames) -> pd.Series:
    jam = frames.jam_table.copy()
    lineups = frames.lineups.copy()
    if jam.empty:
        return pd.Series(dtype="float64")

    totals = {
        "total_jams": int(len(jam)),
        "total_points": float(jam["Total_points"].fillna(0).sum()),
        "avg_points_per_jam": float(jam["Total_points"].fillna(0).mean()),
        "lead_pct": _ratio_pct(jam["Lider"]),
        "call_pct": _ratio_pct(jam["Call"]),
        "no_initial_pass_pct": _ratio_pct(jam["No_initial_pass"]),
        "total_penalties": int(len(frames.penalty_tracker)),
        "total_players": _count_players(lineups),
    }
    return pd.Series(totals)


def build_player_table(frames: DataFrames) -> pd.DataFrame:
    long = lineups_long(frames.lineups)
    penalties = frames.penalty_tracker.copy()
    names = frames.player_names.copy()

    if long.empty:
        return pd.DataFrame()

    roles = (
        long.groupby(["Player_number", "Role"]).size().unstack(fill_value=0)
        .reindex(columns=ROLES, fill_value=0)
        .rename(columns={r: f"jams_as_{r.lower()}" for r in ROLES})
    )
    jams_played = long.groupby("Player_number").size()  # una fila por jugadora por jam
    out = roles.assign(jams_played=jams_played).reset_index()

    penalty_counts = (
        penalties["Player_number"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .rename_axis("Player_number")
        .reset_index(name="penalties")
    )

    out = out.merge(penalty_counts, on="Player_number", how="left").fillna({"penalties": 0})
    out["penalties"] = out["penalties"].astype(int)
    out["penalties_per_jam"] = (out["penalties"] / out["jams_played"].replace(0, pd.NA)).fillna(0.0)

    names["Player_number"] = names["Player_number"].astype(str).str.strip()
    out = out.merge(names, on="Player_number", how="left")
    out["player_label"] = out["Name"].fillna("#" + out["Player_number"]) + " (#" + out["Player_number"] + ")"

    out = out.sort_values(["jams_played", "penalties"], ascending=[False, False]).reset_index(drop=True)
    return out


def _count_players(lineups: pd.DataFrame) -> int:
    long = lineups_long(lineups)
    return int(long["Player_number"].nunique()) if not long.empty else 0


def _ratio_pct(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    return float(100 * s.mean())


# --- Faltas y caja -------------------------------------------------------------
#
# Definiciones:
# - Falta: una fila del Penalty_tracker (Date, Period, Jam, Player_number, Penalty_code).
# - Faltas por jam: faltas / jams en pista de la jugadora, del equipo o de la combinación.
# - box_start de un jam: número de jugadoras nuestras con Start_box = 1 (0, 1 o 2 o más).
# - Jam con caja: al menos una jugadora con Start_box o Finish_box = 1.

JAM_KEYS = ["Date", "Period", "Jam"]
SIN_ROL = "sin_rol"  # falta de una jugadora que no figura en la alineación de ese jam
BOX_START_MAX = 2  # el valor 2 agrupa "2 o más"


def _time_by_jam(frames: DataFrames) -> pd.DataFrame:
    """Duración (segundos) de cada jam con dato en Time; vacío si no hay."""
    time = frames.time
    if time.empty:
        return pd.DataFrame(columns=JAM_KEYS + ["Time"])
    out = time[JAM_KEYS + ["Time"]].copy()
    out["Time"] = pd.to_numeric(out["Time"], errors="coerce")
    return out.dropna(subset=["Time"]).drop_duplicates(subset=JAM_KEYS)


def penalties_by_jam(frames: DataFrames) -> pd.DataFrame:
    """Faltas por jam: una fila por jam de Jam_table con `penalties` (0 si no hubo)."""
    jams = frames.jam_table[JAM_KEYS].drop_duplicates()
    counts = frames.penalty_tracker.groupby(JAM_KEYS).size().rename("penalties").reset_index()
    out = jams.merge(counts, on=JAM_KEYS, how="left")
    out["penalties"] = out["penalties"].fillna(0).astype(int)
    return out.reset_index(drop=True)


def box_state_by_jam(frames: DataFrames) -> pd.DataFrame:
    """Estado de caja por jam: `box_start`, `box_start_group` (0, 1, 2+) y `has_box`.

    Cada jugadora cuenta una sola vez por jam (lineups_long ya la deduplica), así que
    quien empieza y termina el jam en caja no se cuenta doble.
    """
    long = lineups_long(frames.lineups)
    jams = frames.lineups[JAM_KEYS].drop_duplicates()
    if long.empty:
        return jams.assign(box_start=0, box_start_group=0, has_box=False).reset_index(drop=True)

    per_jam = (
        long.assign(any_box=(long["Start_box"] + long["Finish_box"]) > 0)
        .groupby(JAM_KEYS, as_index=False)
        .agg(box_start=("Start_box", "sum"), has_box=("any_box", "any"))
    )
    out = jams.merge(per_jam, on=JAM_KEYS, how="left")
    out["box_start"] = out["box_start"].fillna(0).astype(int)
    out["has_box"] = out["has_box"].fillna(False).astype(bool)
    out["box_start_group"] = out["box_start"].clip(upper=BOX_START_MAX)
    return out.reset_index(drop=True)


def box_cost_table(frames: DataFrames) -> pd.DataFrame:
    """Costo de la caja: por box_start (0, 1, 2+) jams y promedios por jam.

    Columnas: box_start_group, jams, points_for, points_against, effective, rival_lead_pct.
    No está ajustado por partido ni por jammer.
    """
    columns = ["box_start_group", "jams", "points_for", "points_against", "effective", "rival_lead_pct"]
    state = box_state_by_jam(frames)
    ours = frames.jam_table[JAM_KEYS + ["Total_points"]].drop_duplicates(subset=JAM_KEYS)
    rival = frames.rival_jam_table
    if state.empty or ours.empty or rival.empty:
        return pd.DataFrame(columns=columns)

    rival = rival[JAM_KEYS + ["Total_points", "Lider"]].drop_duplicates(subset=JAM_KEYS)
    merged = (
        state.merge(ours, on=JAM_KEYS, how="inner")
        .merge(rival, on=JAM_KEYS, how="inner", suffixes=("_for", "_against"))
    )
    merged["Total_points_for"] = pd.to_numeric(merged["Total_points_for"], errors="coerce").fillna(0)
    merged["Total_points_against"] = pd.to_numeric(merged["Total_points_against"], errors="coerce").fillna(0)
    merged["Lider"] = pd.to_numeric(merged["Lider"], errors="coerce").fillna(0)

    grouped = merged.groupby("box_start_group").agg(
        jams=("Jam", "size"),
        points_for=("Total_points_for", "mean"),
        points_against=("Total_points_against", "mean"),
        rival_lead_pct=("Lider", "mean"),
    )
    grouped["rival_lead_pct"] = grouped["rival_lead_pct"] * 100
    grouped["effective"] = grouped["points_for"] - grouped["points_against"]
    grouped = grouped.reindex(range(BOX_START_MAX + 1))
    grouped.index.name = "box_start_group"
    grouped = grouped.reset_index()
    grouped["jams"] = grouped["jams"].fillna(0).astype(int)
    return grouped[columns]


def penalties_with_role(frames: DataFrames) -> pd.DataFrame:
    """Faltas con el rol de la jugadora en el jam de la falta (SIN_ROL si no figura)."""
    pen = agregar_match_id(frames.penalty_tracker).copy()
    if pen.empty:
        return pen.assign(Role=pd.Series(dtype="object"), Time=pd.Series(dtype="float64"))
    pen["Player_number"] = pen["Player_number"].astype(str).str.strip()
    long = lineups_long(frames.lineups)[JAM_KEYS + ["Player_number", "Role"]]
    out = pen.merge(long, on=JAM_KEYS + ["Player_number"], how="left")
    out["Role"] = out["Role"].fillna(SIN_ROL)
    return out.merge(_time_by_jam(frames), on=JAM_KEYS, how="left")


def _rates(out: pd.DataFrame, jams_col: str) -> pd.DataFrame:
    """Agrega minutos en pista y tasas por jam y por 10 minutos a una tabla agrupada."""
    out["minutes_on_track"] = (out["seconds"] / 60).where(out["jams_timed"] > 0)
    out["penalties_per_10min"] = (out["penalties_timed"] / out["minutes_on_track"] * 10).where(
        out["minutes_on_track"] > 0
    )
    out["penalties_per_jam"] = (out["penalties"] / out[jams_col]).where(out[jams_col] > 0)
    return out.drop(columns=["seconds", "jams_timed", "penalties_timed"])


def _played_and_penalties(long: pd.DataFrame, pen: pd.DataFrame, by: str, jams_col: str) -> pd.DataFrame:
    played = long.groupby(by).agg(**{jams_col: ("Jam", "size")}, seconds=("Time", "sum"), jams_timed=("Time", "count"))
    totals = pen.groupby(by).size().rename("penalties")
    timed = pen[pen["Time"].notna()].groupby(by).size().rename("penalties_timed")
    return played.join(totals, how="outer").join(timed, how="outer").fillna(0)


def player_penalty_summary(frames: DataFrames) -> pd.DataFrame:
    """Faltas por jugadora: total, por jam, por 10 minutos en pista y por rol.

    Los minutos en pista suman la duración (Time) de los jams que jugó la jugadora; la
    tasa por 10 minutos usa solo los jams con dato en Time y es NaN si no hay ninguno.
    """
    long = lineups_long(frames.lineups).merge(_time_by_jam(frames), on=JAM_KEYS, how="left")
    pen = penalties_with_role(frames)

    out = _played_and_penalties(long, pen, "Player_number", "jams_played")
    by_role = (
        pen.groupby(["Player_number", "Role"]).size().unstack(fill_value=0)
        .reindex(columns=ROLES + [SIN_ROL], fill_value=0)
        .rename(columns={r: f"penalties_as_{r.lower()}" for r in ROLES + [SIN_ROL]})
    )
    out = out.join(by_role, how="left").fillna(0)
    out = _rates(out, "jams_played")
    keep_float = ["minutes_on_track", "penalties_per_10min", "penalties_per_jam"]
    for col in out.columns:
        if col not in keep_float:
            out[col] = out[col].astype(int)
    out["penalties_per_jam"] = out["penalties_per_jam"].fillna(0.0)
    out.index.name = "Player_number"
    return out.reset_index().sort_values(
        ["penalties", "Player_number"], ascending=[False, True]
    ).reset_index(drop=True)


def player_penalty_breakdown(frames: DataFrames, player_number: str, by: str) -> pd.DataFrame:
    """Faltas de una jugadora por `by` ("Role", "Period" o "match_id").

    Columnas: key, jams, penalties, penalties_per_jam, minutes_on_track, penalties_per_10min
    (las dos últimas son NaN si no hay jams con dato en Time).
    """
    player_number = str(player_number).strip()
    long = agregar_match_id(lineups_long(frames.lineups))
    long = long[long["Player_number"] == player_number].merge(_time_by_jam(frames), on=JAM_KEYS, how="left")
    pen = penalties_with_role(frames)
    pen = pen[pen["Player_number"] == player_number]

    out = _played_and_penalties(long, pen, by, "jams")
    out = _rates(out, "jams")
    out[["jams", "penalties"]] = out[["jams", "penalties"]].astype(int)
    out.index.name = "key"
    return out.reset_index()


def penalty_code_counts(frames: DataFrames, codes: pd.DataFrame) -> pd.DataFrame:
    """Faltas por código con nombre y descripción en español (según Penalty_codes.csv)."""
    pen = frames.penalty_tracker
    counts = (
        pen["Penalty_code"].astype(str).str.strip().value_counts()
        .rename_axis("code").reset_index(name="penalties")
    )
    out = counts.merge(codes, on="code", how="left")
    out["nombre_es"] = out["nombre_es"].fillna(out["code"])
    out["descripcion_es"] = out["descripcion_es"].fillna("")
    total = out["penalties"].sum()
    out["pct"] = out["penalties"] / total * 100 if total else 0.0
    return out.sort_values(["penalties", "code"], ascending=[False, True]).reset_index(drop=True)


# --- Puntos efectivos por jugadora ------------------------------------------------
#
# Los puntos efectivos acumulados dependen de los minutos jugados y del rival, así que se
# comparan por jam y relativos al promedio de su partido (eff_rel = eff - promedio del partido).


def effective_by_jam(frames: DataFrames) -> pd.DataFrame:
    """Una fila por jam con pts_for, pts_against, eff y valores relativos al partido.

    Une Jam_table y Rival_Jam_table por (Date, Period, Jam). Las columnas `*_rel` restan el
    promedio de ese partido (match_id = "Date | Rival") dentro de los datos recibidos.
    """
    columns = JAM_KEYS + ["match_id", "Jammer", "pts_for", "pts_against", "eff",
                          "eff_rel", "pts_for_rel", "pts_against_rel"]
    ours, rival = frames.jam_table, frames.rival_jam_table
    if ours.empty or rival.empty:
        return pd.DataFrame(columns=columns)

    left = ours[JAM_KEYS + ["Rival", "Jammer", "Total_points"]].drop_duplicates(subset=JAM_KEYS)
    right = rival[JAM_KEYS + ["Total_points"]].drop_duplicates(subset=JAM_KEYS)
    out = left.merge(right, on=JAM_KEYS, how="inner", suffixes=("_for", "_against"))
    out = out.rename(columns={"Total_points_for": "pts_for", "Total_points_against": "pts_against"})
    out["pts_for"] = pd.to_numeric(out["pts_for"], errors="coerce").fillna(0)
    out["pts_against"] = pd.to_numeric(out["pts_against"], errors="coerce").fillna(0)
    out["Jammer"] = out["Jammer"].astype(str).str.strip()
    out["match_id"] = crear_match_id(out)
    out["eff"] = out["pts_for"] - out["pts_against"]
    for col in ("eff", "pts_for", "pts_against"):
        rel = "eff_rel" if col == "eff" else f"{col}_rel"
        out[rel] = out[col] - out.groupby("match_id")[col].transform("mean")
    return out[columns].reset_index(drop=True)


def _bootstrap_interval(values: np.ndarray) -> tuple[float, float]:
    """Intervalo (config.BOOTSTRAP_NIVEL) del promedio por bootstrap; NaN con pocos jams."""
    if len(values) < cfg.BOOTSTRAP_MIN_JAMS:
        return np.nan, np.nan
    rng = np.random.default_rng(cfg.BOOTSTRAP_SEMILLA)
    idx = rng.integers(0, len(values), size=(cfg.BOOTSTRAP_REMUESTREOS, len(values)))
    means = values[idx].mean(axis=1)
    cola = (1 - cfg.BOOTSTRAP_NIVEL) / 2
    low, high = np.quantile(means, [cola, 1 - cola])
    return float(low), float(high)


def _with_and_without(group: pd.DataFrame, match_stats: pd.DataFrame) -> float:
    """Promedio ponderado por partido de eff con ella menos eff sin ella (NaN si no hay partido válido)."""
    diffs, weights = [], []
    for match_id, rows in group.groupby("match_id"):
        total_n, total_sum = match_stats.loc[match_id, ["n", "sum"]]
        n_with = len(rows)
        n_without = total_n - n_with
        if n_without < cfg.MIN_JAMS_SIN_ELLA:
            continue
        diffs.append(rows["eff"].mean() - (total_sum - rows["eff"].sum()) / n_without)
        weights.append(n_with)
    if not diffs:
        return np.nan
    return float(np.average(diffs, weights=weights))


def player_effectiveness(frames: DataFrames, por_rol: bool = False) -> pd.DataFrame:
    """Efectividad por jugadora (y por rol si `por_rol`), siempre con su n de jams.

    Columnas: jams, eff_por_jam, eff_rel_por_jam, pts_for_por_jam, pts_against_por_jam,
    pts_for_rel_por_jam, pts_against_rel_por_jam, con_y_sin, eff_ajustada_jammer,
    jams_ajuste, ic_bajo, ic_alto y muestra_baja.

    - con_y_sin: por partido, eff medio con ella menos eff medio sin ella (solo con al
      menos MIN_JAMS_SIN_ELLA jams sin ella); se promedia entre partidos ponderando por sus
      jams. Es NaN si ningún partido es válido.
    - eff_ajustada_jammer (solo Pivot y Bloque): eff del jam menos el promedio de eff de los
      jams del mismo partido con la misma jammer (o el del partido si ella tiene menos de
      MIN_JAMS_JAMMER jams). Es NaN si la jugadora no tiene jams de Pivot o Bloque.
    - ic_bajo / ic_alto: intervalo por bootstrap de eff_rel_por_jam (NaN con menos de
      BOOTSTRAP_MIN_JAMS jams).
    """
    keys = ["Player_number", "Role"] if por_rol else ["Player_number"]
    eff = effective_by_jam(frames)
    long = lineups_long(frames.lineups)
    if eff.empty or long.empty:
        return pd.DataFrame(columns=keys + ["jams"])

    jammer_n = eff.groupby(["match_id", "Jammer"])["eff"].transform("size")
    jammer_mean = eff.groupby(["match_id", "Jammer"])["eff"].transform("mean")
    match_mean = eff.groupby("match_id")["eff"].transform("mean")
    eff = eff.assign(eff_adj=eff["eff"] - jammer_mean.where(jammer_n >= cfg.MIN_JAMS_JAMMER, match_mean))
    match_stats = eff.groupby("match_id")["eff"].agg(n="size", sum="sum")

    rows = long[JAM_KEYS + ["Player_number", "Role"]].merge(eff, on=JAM_KEYS, how="inner")
    records = []
    for key, group in rows.groupby(keys):
        key = key if isinstance(key, tuple) else (key,)
        pack = group[group["Role"].isin(["Pivot", "Bloque"])]
        low, high = _bootstrap_interval(group["eff_rel"].to_numpy(dtype=float))
        records.append(
            {
                **dict(zip(keys, key)),
                "jams": len(group),
                "eff_por_jam": group["eff"].mean(),
                "eff_rel_por_jam": group["eff_rel"].mean(),
                "pts_for_por_jam": group["pts_for"].mean(),
                "pts_against_por_jam": group["pts_against"].mean(),
                "pts_for_rel_por_jam": group["pts_for_rel"].mean(),
                "pts_against_rel_por_jam": group["pts_against_rel"].mean(),
                "con_y_sin": _with_and_without(group, match_stats),
                "eff_ajustada_jammer": pack["eff_adj"].mean() if len(pack) else np.nan,
                "jams_ajuste": len(pack),
                "ic_bajo": low,
                "ic_alto": high,
                "muestra_baja": len(group) < cfg.MIN_JAMS_JUGADORA,
            }
        )
    return pd.DataFrame(records).sort_values("eff_rel_por_jam", ascending=False).reset_index(drop=True)


def player_effectiveness_by_match(frames: DataFrames, player_number: str) -> pd.DataFrame:
    """Por partido de una jugadora: jams, eff por jam, eff relativa y faltas."""
    player_number = str(player_number).strip()
    eff = effective_by_jam(frames)
    long = lineups_long(frames.lineups)
    long = long[long["Player_number"] == player_number][JAM_KEYS]
    played = long.merge(eff, on=JAM_KEYS, how="inner")
    out = played.groupby("match_id").agg(
        jams=("Jam", "size"), eff_por_jam=("eff", "mean"), eff_rel_por_jam=("eff_rel", "mean")
    )
    pen = penalties_with_role(frames)
    pen = pen[pen["Player_number"] == player_number].groupby("match_id").size().rename("penalties")
    out = out.join(pen, how="outer").fillna({"jams": 0, "penalties": 0})
    out[["jams", "penalties"]] = out[["jams", "penalties"]].astype(int)
    out.index.name = "match_id"
    return out.reset_index()


def jam_facts(frames: DataFrames) -> pd.DataFrame:
    """Un jam por fila: efectividad (effective_by_jam) más lead, call-off, star pass y lead rival."""
    eff = effective_by_jam(frames)
    if eff.empty:
        return eff
    ours = frames.jam_table[JAM_KEYS + ["Lider", "Lost", "Call", "No_initial_pass", "Star_pass"]]
    ours = ours.drop_duplicates(subset=JAM_KEYS).rename(
        columns={"Lider": "lead", "Lost": "lost", "Call": "call", "No_initial_pass": "nip", "Star_pass": "star_pass"}
    )
    rival = frames.rival_jam_table[JAM_KEYS + ["Lider"]].drop_duplicates(subset=JAM_KEYS)
    rival = rival.rename(columns={"Lider": "rival_lead"})
    out = eff.merge(ours, on=JAM_KEYS, how="left").merge(rival, on=JAM_KEYS, how="left")
    for col in ("lead", "lost", "call", "nip", "star_pass", "rival_lead"):
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out
