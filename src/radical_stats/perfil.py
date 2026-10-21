"""Perfil de una jugadora: cálculos y textos de resumen que presenta la página de jugadoras.

Todas las cifras por jugadora se devuelven junto con su n de jams. Los puntos efectivos se
usan siempre por jam y relativos al partido, nunca acumulados.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from radical_stats import config as cfg
from radical_stats import textos as T
from radical_stats.combinaciones import estadisticas_combinaciones
from radical_stats.lineups import ROLES, lineups_long
from radical_stats.metrics import (
    JAM_KEYS,
    jam_facts,
    penalty_code_counts,
    player_effectiveness,
    player_effectiveness_by_match,
    player_penalty_breakdown,
    player_penalty_summary,
)
from radical_stats.models import DataFrames

# Orden de desempate del rol principal.
_ROL_PRIORIDAD = {rol: i for i, rol in enumerate(ROLES)}
_IGUAL_UMBRAL = 0.005  # diferencias menores se describen como «igual»


@dataclass(frozen=True)
class PerfilJugadora:
    """Datos descriptivos de una jugadora en los jams filtrados."""

    player_number: str
    jams: int
    team_jams: int
    matches: int
    main_role: str | None
    main_role_jams: int
    roles_jams: dict[str, int]
    eff_rel: float  # puntos efectivos por jam relativos al partido (NaN si no hay dato)
    eff_ic: tuple[float, float]  # intervalo del 80 % (NaN si hay pocos jams)
    penalties: int
    penalties_per_jam: float
    team_penalties_per_jam: float

    @property
    def pct_team_jams(self) -> float:
        return 100 * self.jams / self.team_jams if self.team_jams else float("nan")

    @property
    def main_role_pct(self) -> float:
        return 100 * self.main_role_jams / self.jams if self.jams else float("nan")

    @property
    def single_role(self) -> bool:
        return sum(1 for n in self.roles_jams.values() if n > 0) == 1

    @property
    def low_sample(self) -> bool:
        return self.jams < cfg.MIN_JAMS_JUGADORA

    @property
    def penalties_diff(self) -> float:
        return self.penalties_per_jam - self.team_penalties_per_jam


def comparar_con_equipo(valor: float, equipo: float) -> tuple[float, str]:
    """Diferencia contra el equipo y su sentido: «mas», «menos» o «igual» (NaN -> «sin_dato»)."""
    if pd.isna(valor) or pd.isna(equipo):
        return float("nan"), "sin_dato"
    diferencia = float(valor) - float(equipo)
    if abs(diferencia) < _IGUAL_UMBRAL:
        return diferencia, "igual"
    return diferencia, "mas" if diferencia > 0 else "menos"


def main_role_of(roles_jams: dict[str, int]) -> tuple[str | None, int]:
    """Rol con más jams (desempate: Jammer, Pivot, Bloque). (None, 0) si no jugó."""
    jugados = {r: n for r, n in roles_jams.items() if n > 0}
    if not jugados:
        return None, 0
    rol = min(jugados, key=lambda r: (-jugados[r], _ROL_PRIORIDAD.get(r, 99)))
    return rol, jugados[rol]


def roles_con_jams(frames: DataFrames, player_number: str) -> list[str]:
    """Roles en los que la jugadora tuvo al menos 1 jam (determina qué pestañas se muestran)."""
    long = lineups_long(frames.lineups)
    player_number = str(player_number).strip()
    jugados = set(long.loc[long["Player_number"] == player_number, "Role"])
    return [r for r in ROLES if r in jugados]


def team_penalty_rate(frames: DataFrames) -> float:
    """Faltas totales divididas entre los jams-jugadora (una fila de lineups_long por jugadora y jam)."""
    jam_players = len(lineups_long(frames.lineups))
    return len(frames.penalty_tracker) / jam_players if jam_players else float("nan")


def player_profile(frames: DataFrames, player_number: str) -> PerfilJugadora:
    """Resumen numérico de una jugadora (jams, rol principal, efectividad y faltas)."""
    player_number = str(player_number).strip()
    long = lineups_long(frames.lineups)
    mine = long[long["Player_number"] == player_number]
    roles_jams = {r: int((mine["Role"] == r).sum()) for r in ROLES}
    main_role, main_jams = main_role_of(roles_jams)

    effectiveness = player_effectiveness(frames)
    eff_rel, ic = float("nan"), (float("nan"), float("nan"))
    if not effectiveness.empty:
        row = effectiveness[effectiveness["Player_number"] == player_number]
        if not row.empty:
            eff_rel = float(row["eff_rel_por_jam"].iloc[0])
            ic = (float(row["ic_bajo"].iloc[0]), float(row["ic_alto"].iloc[0]))

    pen = frames.penalty_tracker
    penalties = int((pen["Player_number"].astype(str).str.strip() == player_number).sum()) if not pen.empty else 0
    jams = len(mine)
    return PerfilJugadora(
        player_number=player_number,
        jams=jams,
        team_jams=len(long[JAM_KEYS].drop_duplicates()) if not long.empty else 0,
        matches=int(mine["match_id"].nunique()) if not mine.empty else 0,
        main_role=main_role,
        main_role_jams=main_jams,
        roles_jams=roles_jams,
        eff_rel=eff_rel,
        eff_ic=ic,
        penalties=penalties,
        penalties_per_jam=penalties / jams if jams else float("nan"),
        team_penalties_per_jam=team_penalty_rate(frames),
    )


def resumen_tres_frases(perfil: PerfilJugadora) -> list[str]:
    """Tres frases descriptivas, sin juicios: rol principal, efectivos relativos y faltas."""
    rol = T.ROLES.get(perfil.main_role, perfil.main_role)

    # 1. Rol principal (con aviso de muestra baja si corresponde).
    if perfil.main_role is None:
        primera = T.RESUMEN_SIN_JAMS
    elif perfil.low_sample and perfil.single_role:
        primera = T.RESUMEN_MUESTRA_BAJA_ROL_UNICO.format(minimo=cfg.MIN_JAMS_JUGADORA, n=perfil.jams, rol=rol)
    elif perfil.low_sample:
        primera = T.RESUMEN_MUESTRA_BAJA.format(
            minimo=cfg.MIN_JAMS_JUGADORA, n=perfil.jams, rol=rol, pct=T.fmt_pct(perfil.main_role_pct, 0)
        )
    elif perfil.single_role:
        primera = T.RESUMEN_ROL_UNICO.format(rol=rol, n=perfil.jams)
    else:
        primera = T.RESUMEN_ROL_PRINCIPAL.format(
            rol=rol, n=perfil.main_role_jams, jams=perfil.jams, pct=T.fmt_pct(perfil.main_role_pct, 0)
        )

    # 2. Puntos efectivos por jam relativos al partido, con su n.
    if pd.isna(perfil.eff_rel):
        segunda = T.RESUMEN_EFECTIVOS_SIN_DATO.format(n=perfil.jams)
    elif pd.isna(perfil.eff_ic[0]):
        segunda = T.RESUMEN_EFECTIVOS.format(valor=T.fmt_num(perfil.eff_rel, 2), n=perfil.jams)
    else:
        segunda = T.RESUMEN_EFECTIVOS_CON_INTERVALO.format(
            valor=T.fmt_num(perfil.eff_rel, 2),
            n=perfil.jams,
            bajo=T.fmt_num(perfil.eff_ic[0], 2),
            alto=T.fmt_num(perfil.eff_ic[1], 2),
        )

    # 3. Faltas por jam contra el equipo.
    diferencia, sentido = comparar_con_equipo(perfil.penalties_per_jam, perfil.team_penalties_per_jam)
    if sentido == "sin_dato":
        tercera = T.RESUMEN_FALTAS_SIN_DATO.format(n=perfil.jams)
    else:
        tercera = T.RESUMEN_FALTAS[sentido].format(
            tasa=T.fmt_num(perfil.penalties_per_jam, 2),
            faltas=perfil.penalties,
            n=perfil.jams,
            dif=T.fmt_num(abs(diferencia), 2),
            equipo=T.fmt_num(perfil.team_penalties_per_jam, 2),
        )
    return [primera, segunda, tercera]


# --- Jams de la jugadora con sus datos ----------------------------------------------


def _jam_player_rows(frames: DataFrames) -> pd.DataFrame:
    """Una fila por jugadora y jam con sus datos del jam y sus faltas (`pen`) en ese jam."""
    facts = jam_facts(frames)
    long = lineups_long(frames.lineups)
    columns = list(long.columns) + [c for c in facts.columns if c not in long.columns] + ["pen", "box_any"]
    if facts.empty or long.empty:
        return pd.DataFrame(columns=columns)
    rows = long.drop(columns=["match_id"]).merge(facts, on=JAM_KEYS, how="inner")
    pen = frames.penalty_tracker
    if not pen.empty:
        counts = (
            pen.assign(Player_number=pen["Player_number"].astype(str).str.strip())
            .groupby(JAM_KEYS + ["Player_number"]).size().rename("pen").reset_index()
        )
        rows = rows.merge(counts, on=JAM_KEYS + ["Player_number"], how="left")
    else:
        rows["pen"] = 0
    rows["pen"] = rows["pen"].fillna(0).astype(int)
    rows["box_any"] = (rows["Start_box"] + rows["Finish_box"]) > 0
    return rows


def _fila(metrica: str, valor: float, equipo: float, n: int, unidad: str, detalle: str = "") -> dict:
    diferencia = valor - equipo if pd.notna(valor) and pd.notna(equipo) else float("nan")
    return {
        "metrica": metrica, "valor": valor, "equipo": equipo,
        "diferencia": diferencia, "n": n, "unidad": unidad, "detalle": detalle,
    }


def role_table(frames: DataFrames, player_number: str, role: str) -> pd.DataFrame:
    """Cifras de la jugadora en un rol, cada una con su n y su diferencia contra el equipo.

    El «equipo» es el promedio de todas las jugadoras en ese mismo rol (incluida ella); en
    puntos en contra y lead rival del bloque es el promedio de todos los jams.
    """
    player_number = str(player_number).strip()
    rows = _jam_player_rows(frames)
    columns = ["metrica", "valor", "equipo", "diferencia", "n", "unidad", "detalle"]
    if rows.empty:
        return pd.DataFrame(columns=columns)
    team = rows[rows["Role"] == role]
    mine = team[team["Player_number"] == player_number]
    n = len(mine)
    if n == 0:
        return pd.DataFrame(columns=columns)
    all_jams = rows.drop_duplicates(subset=JAM_KEYS)
    out = [_fila("jams", n, np.nan, n, "conteo")]

    if role == "Jammer":
        for key, col in (("puntos_por_jam", "pts_for"),):
            out.append(_fila(key, mine[col].mean(), team[col].mean(), n, "num"))
        for key, col in (("lead_pct", "lead"), ("lead_perdido_pct", "lost"), ("call_off_pct", "call"),
                         ("sin_pase_inicial_pct", "nip")):
            out.append(_fila(key, 100 * mine[col].mean(), 100 * team[col].mean(), n, "pct"))
        out.append(
            _fila("caja_pct", 100 * mine["box_any"].mean(), 100 * team["box_any"].mean(), n, "pct",
                  T.DETALLE_N_DE.format(k=int(mine["box_any"].sum()), n=n))
        )
        out.append(_fila("eff_rel", mine["eff_rel"].mean(), team["eff_rel"].mean(), n, "num"))
    elif role == "Pivot":
        out.append(_fila("pts_for_rel", mine["pts_for_rel"].mean(), team["pts_for_rel"].mean(), n, "num"))
        out.append(_fila("pts_against_rel", mine["pts_against_rel"].mean(), team["pts_against_rel"].mean(), n, "num"))
        out.append(_fila("faltas_por_jam", mine["pen"].sum() / n, team["pen"].sum() / len(team), n, "num",
                         T.DETALLE_N_DE.format(k=int(mine["pen"].sum()), n=n)))
        out.append(_fila("star_pass", int(mine["star_pass"].sum()), np.nan, n, "conteo",
                         T.DETALLE_N_DE.format(k=int(mine["star_pass"].sum()), n=n)))
    elif role == "Bloque":
        out.append(_fila("pts_against", mine["pts_against"].mean(), all_jams["pts_against"].mean(), n, "num"))
        out.append(_fila("rival_lead_pct", 100 * mine["rival_lead"].mean(), 100 * all_jams["rival_lead"].mean(), n, "pct"))
        out.append(_fila("faltas_por_jam", mine["pen"].sum() / n, team["pen"].sum() / len(team), n, "num",
                         T.DETALLE_N_DE.format(k=int(mine["pen"].sum()), n=n)))
        out.append(_fila("caja_inicio_pct", 100 * mine["Start_box"].mean(), 100 * team["Start_box"].mean(), n, "pct",
                         T.DETALLE_N_DE.format(k=int(mine["Start_box"].sum()), n=n)))
    return pd.DataFrame(out, columns=columns)


def formatear_tabla_rol(table: pd.DataFrame) -> pd.DataFrame:
    """Tabla de rol lista para mostrar: columnas y valores en español (coma decimal)."""

    def _fmt(valor: float, unidad: str) -> str:
        if pd.isna(valor):
            return T.NO_APLICA if unidad == "conteo" else T.SIN_DATO
        if unidad == "conteo":
            return T.fmt_num(valor)
        return T.fmt_pct(valor) if unidad == "pct" else T.fmt_num(valor, 2)

    def _dif(valor: float, unidad: str) -> str:
        if pd.isna(valor):
            return T.NO_APLICA if unidad == "conteo" else T.SIN_DATO
        signo = "+" if valor > 0 else ""
        texto = T.fmt_num(valor, 1, " pp") if unidad == "pct" else T.fmt_num(valor, 2)
        return signo + texto

    out = pd.DataFrame(
        {
            T.COL_METRICA: table["metrica"].map(T.METRICAS_ROL),
            T.COL_VALOR: [_fmt(v, u) for v, u in zip(table["valor"], table["unidad"])],
            T.COL_DETALLE: table["detalle"],
            T.COL_PROMEDIO_EQUIPO: [_fmt(v, u) for v, u in zip(table["equipo"], table["unidad"])],
            T.COL_DIFERENCIA: [_dif(v, u) for v, u in zip(table["diferencia"], table["unidad"])],
            T.COL_N_JAMS: table["n"].map(T.fmt_num),
        }
    )
    return out


# --- Faltas -----------------------------------------------------------------------


def player_penalty_codes(frames: DataFrames, player_number: str, codes: pd.DataFrame) -> pd.DataFrame:
    """Faltas de la jugadora por código (nombre y descripción según Penalty_codes.csv)."""
    pen = frames.penalty_tracker
    mine = pen[pen["Player_number"].astype(str).str.strip() == str(player_number).strip()]
    only_mine = DataFrames(
        jam_table=frames.jam_table, lineups=frames.lineups, penalty_tracker=mine,
        player_names=frames.player_names, time=frames.time, rival_jam_table=frames.rival_jam_table,
    )
    return penalty_code_counts(only_mine, codes)


def penalty_box_cost(frames: DataFrames, player_number: str) -> dict:
    """Puntos en contra por jam cuando la jugadora arranca en caja contra cuando no.

    `valido` solo si hay al menos MIN_JAMS_CASO jams en cada caso.
    """
    player_number = str(player_number).strip()
    rows = _jam_player_rows(frames)
    mine = rows[rows["Player_number"] == player_number]
    en_caja = mine[mine["Start_box"] == 1]
    sin_caja = mine[mine["Start_box"] == 0]
    return {
        "n_con_caja": len(en_caja),
        "n_sin_caja": len(sin_caja),
        "con_caja": float(en_caja["pts_against"].mean()) if len(en_caja) else float("nan"),
        "sin_caja": float(sin_caja["pts_against"].mean()) if len(sin_caja) else float("nan"),
        "valido": len(en_caja) >= cfg.MIN_JAMS_CASO and len(sin_caja) >= cfg.MIN_JAMS_CASO,
    }


# --- Por partido ------------------------------------------------------------------


def player_match_table(frames: DataFrames, player_number: str) -> pd.DataFrame:
    """Por partido: jams, rol principal, efectivos por jam y relativos, faltas y minutos en pista."""
    player_number = str(player_number).strip()
    base = player_effectiveness_by_match(frames, player_number)
    minutes = player_penalty_breakdown(frames, player_number, "match_id")[["key", "minutes_on_track"]]
    long = lineups_long(frames.lineups)
    mine = long[long["Player_number"] == player_number]
    main_roles = {
        match: main_role_of({r: int((g["Role"] == r).sum()) for r in ROLES})[0]
        for match, g in mine.groupby("match_id")
    }
    out = base.merge(minutes.rename(columns={"key": "match_id"}), on="match_id", how="left")
    out["main_role"] = out["match_id"].map(main_roles)
    return out[["match_id", "jams", "main_role", "eff_por_jam", "eff_rel_por_jam", "penalties", "minutes_on_track"]]


# --- Con quién rinde ----------------------------------------------------------------


def pack_combinations(frames: DataFrames, player_number: str) -> pd.DataFrame:
    """Duplas y ternas del pack (Pivot + Bloques) que incluyen a la jugadora.

    Columnas: size (2 o 3), players (combinación ordenada), jams, eff_por_jam y eff_rel_por_jam.
    Solo combinaciones con al menos el mínimo de jams de su tamaño (config.MIN_JAMS_COMBINACION).
    """
    player_number = str(player_number).strip()
    columns = ["size", "players", "jams", "eff_por_jam", "eff_rel_por_jam"]
    parts = []
    for size in (2, 3):
        stats = estadisticas_combinaciones(frames, size, incluye=[player_number])
        stats = stats[stats["jams"] >= cfg.MIN_JAMS_COMBINACION[size]]
        parts.append(
            pd.DataFrame(
                {"size": size, "players": stats["combo"], "jams": stats["jams"],
                 "eff_por_jam": stats["eff"], "eff_rel_por_jam": stats["eff_rel"]}
            )
        )
    return pd.concat(parts, ignore_index=True)[columns]


def best_and_worst_combinations(combos: pd.DataFrame, size: int, k: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Las k mejores y k peores combinaciones de un tamaño por eff_rel_por_jam (sin repetir filas)."""
    subset = combos[combos["size"] == size].sort_values(
        ["eff_rel_por_jam", "jams"], ascending=[False, False]
    ).reset_index(drop=True)
    best = subset.head(k)
    worst = subset.drop(best.index).tail(k).sort_values("eff_rel_por_jam").reset_index(drop=True)
    return best.reset_index(drop=True), worst


# --- Todas las jugadoras ------------------------------------------------------------


def players_overview(frames: DataFrames) -> pd.DataFrame:
    """Una fila por jugadora: jams, rol principal, efectivos relativos, puntos en contra, faltas y muestra.

    La columna `muestra` vale «Baja» u «Ok» según MIN_JAMS_JUGADORA.
    """
    long = lineups_long(frames.lineups)
    columns = ["Player_number", "jams", "main_role", "eff_rel_por_jam", "pts_against_por_jam",
               "penalties_per_jam", "muestra"]
    if long.empty:
        return pd.DataFrame(columns=columns)
    roles = long.groupby(["Player_number", "Role"]).size().unstack(fill_value=0).reindex(columns=ROLES, fill_value=0)
    main = roles.apply(lambda r: main_role_of(r.to_dict())[0], axis=1).rename("main_role")
    eff = player_effectiveness(frames)
    eff = eff.set_index("Player_number")[["eff_rel_por_jam", "pts_against_por_jam"]] if not eff.empty else None
    out = roles.sum(axis=1).rename("jams").to_frame().join(main)
    if eff is not None:
        out = out.join(eff)
    else:
        out["eff_rel_por_jam"] = np.nan
        out["pts_against_por_jam"] = np.nan
    out = out.join(player_penalty_summary(frames).set_index("Player_number")[["penalties_per_jam"]])
    out["muestra"] = np.where(out["jams"] < cfg.MIN_JAMS_JUGADORA, T.MUESTRA_CORTA_BAJA, T.MUESTRA_CORTA_OK)
    out.index.name = "Player_number"
    return out.reset_index()[columns]
