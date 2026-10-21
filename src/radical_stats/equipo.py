"""Cálculos de la página de equipo: KPIs, resumen por partido, frases automáticas y tablas.

No dibuja nada: los gráficos viven en `graficos.py` y la página solo une las piezas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from radical_stats import config as cfg
from radical_stats import textos as T
from radical_stats.combinaciones import estadisticas_combinaciones, etiquetas_combinacion
from radical_stats.jugadoras import etiquetas_jugadoras, mapa_nombres
from radical_stats.metrics import (
    JAM_KEYS,
    SIN_ROL,
    box_cost_table,
    box_state_by_jam,
    effective_by_jam,
    penalties_with_role,
    player_effectiveness,
)
from radical_stats.models import DataFrames
from radical_stats.partidos import agregar_match_id, partir_match_id

# --- Títulos y etiquetas ----------------------------------------------------------------


def titulo_equipo(seleccionados: list[str], opciones: list[str], rival: str | None = None) -> str:
    """Título según los partidos marcados: general, vs. un rival o «(N partidos)»."""
    n = len(seleccionados)
    if n == 0 or n == len(opciones):
        return T.TITULO_EQUIPO_GENERAL
    if n == 1 and rival:
        return T.TITULO_EQUIPO_VS.format(rival=rival)
    if n == 1:
        return T.EQUIPO_TITULO
    return T.TITULO_EQUIPO_VARIOS.format(n=n)


def rival_unico(frames: DataFrames) -> str | None:
    """El rival de los jams filtrados si hay uno solo; si no, None."""
    if frames.jam_table.empty or "Rival" not in frames.jam_table.columns:
        return None
    rivales = frames.jam_table["Rival"].dropna().astype(str).unique()
    return rivales[0] if len(rivales) == 1 else None


def etiqueta_partido(match_id: str) -> str:
    """«2025-11-01 | Pacha Mamis» -> «Pacha Mamis (2025-11-01)»."""
    fecha, rival = partir_match_id(match_id)
    return f"{rival} ({fecha})" if rival else str(match_id)


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


# --- KPIs y tarjetas -------------------------------------------------------------------


def kpis_equipo(frames: DataFrames) -> dict[str, float]:
    """KPIs nosotras contra rival por jam. Vacío si no hay jams.

    Puntos a favor y en contra salen de Jam_table y Rival_Jam_table; el lead del rival, de
    Rival_Jam_table; las faltas, del Penalty_tracker (una falta = una fila).
    """
    jam, rival = frames.jam_table, frames.rival_jam_table
    if jam.empty:
        return {}
    n = len(jam)
    has_rival = not rival.empty
    pts_for = float(_num(jam["Total_points"]).mean())
    pts_against = float(_num(rival["Total_points"]).mean()) if has_rival else float("nan")
    penalties = len(frames.penalty_tracker)
    return {
        "jams": n,
        "pts_for": pts_for,
        "pts_against": pts_against,
        "diff": pts_for - pts_against,
        "total_for": float(_num(jam["Total_points"]).sum()),
        "total_against": float(_num(rival["Total_points"]).sum()) if has_rival else float("nan"),
        "lead_pct": 100 * float(_num(jam["Lider"]).mean()),
        "rival_lead_pct": 100 * float(_num(rival["Lider"]).mean()) if has_rival else float("nan"),
        "call_pct": 100 * float(_num(jam["Call"]).mean()),
        "nip_pct": 100 * float(_num(jam["No_initial_pass"]).mean()),
        "penalties": penalties,
        "penalties_per_jam": penalties / n,
    }


@dataclass(frozen=True)
class Tarjeta:
    etiqueta: str
    valor: str
    delta: str | None
    delta_color: str  # "normal", "inverse" u "off" (convención de st.metric)
    ayuda: str


# (etiqueta, clave, tipo, color del delta): «inverse» cuando menos es mejor.
_TARJETAS = (
    (T.TARJETA_PUNTOS_A_FAVOR, "pts_for", "num", "normal"),
    (T.TARJETA_PUNTOS_EN_CONTRA, "pts_against", "num", "inverse"),
    (T.TARJETA_DIFERENCIA, "diff", "num", "normal"),
    (T.TARJETA_LEAD_NUESTRO, "lead_pct", "pct", "normal"),
    (T.TARJETA_LEAD_RIVAL, "rival_lead_pct", "pct", "inverse"),
    (T.TARJETA_CALL_OFF, "call_pct", "pct", "off"),
    (T.TARJETA_SIN_PASE_INICIAL, "nip_pct", "pct", "off"),
    (T.TARJETA_FALTAS_EQUIPO_POR_JAM, "penalties_per_jam", "num", "inverse"),
)


def tarjetas_resumen(frames: DataFrames, resto: DataFrames | None = None) -> list[Tarjeta]:
    """Tarjetas nosotras contra rival; con `resto` agrega la diferencia contra los demás partidos."""
    actual = kpis_equipo(frames)
    previo = kpis_equipo(resto) if resto is not None else {}
    tarjetas = []
    for etiqueta, clave, tipo, color in _TARJETAS:
        valor = actual.get(clave, float("nan"))
        texto = T.fmt_pct(valor) if tipo == "pct" else T.fmt_num(valor, 2)
        delta = None
        if previo and pd.notna(valor) and pd.notna(previo.get(clave)):
            dif = valor - previo[clave]
            dif_txt = T.fmt_num(dif, 1, " pp") if tipo == "pct" else T.fmt_num(dif, 2)
            delta = T.DELTA_VS_RESTO.format(valor=("+" if dif > 0 else "") + dif_txt)
        tarjetas.append(
            Tarjeta(etiqueta, texto if pd.notna(valor) else T.SIN_DATO, delta, color,
                    T.AYUDA_TARJETA_JAMS.format(n=actual.get("jams", 0)))
        )
    return tarjetas


# --- Resumen por partido y frases ----------------------------------------------------------


def resumen_por_partido(frames: DataFrames) -> pd.DataFrame:
    """Una fila por partido: rival, fecha, puntos a favor y en contra, jams, diferencia por jam y faltas."""
    columns = ["match_id", "Rival", "Date", "pts_for", "pts_against", "jams", "diff_per_jam", "penalties"]
    jam = agregar_match_id(frames.jam_table)
    if jam.empty:
        return pd.DataFrame(columns=columns)
    out = jam.assign(_pts=_num(jam["Total_points"])).groupby("match_id").agg(
        Rival=("Rival", "first"), Date=("Date", "first"), pts_for=("_pts", "sum"), jams=("Jam", "size")
    )
    rival = agregar_match_id(frames.rival_jam_table)
    out["pts_against"] = (
        rival.assign(_pts=_num(rival["Total_points"])).groupby("match_id")["_pts"].sum()
        if not rival.empty else np.nan
    )
    pen = agregar_match_id(frames.penalty_tracker)
    out["penalties"] = pen.groupby("match_id").size() if not pen.empty else 0
    out["penalties"] = out["penalties"].fillna(0).astype(int)
    out["diff_per_jam"] = (out["pts_for"] - out["pts_against"]) / out["jams"]
    return out.reset_index().sort_values("Date").reset_index(drop=True)[columns]


def formatear_resumen_partidos(resumen: pd.DataFrame) -> pd.DataFrame:
    """Tabla de resumen por partido lista para mostrar (marcador «a favor - en contra», coma decimal)."""
    marcador = resumen.apply(
        lambda r: f"{T.fmt_num(r['pts_for'])} - {T.SIN_DATO if pd.isna(r['pts_against']) else T.fmt_num(r['pts_against'])}",
        axis=1,
    )
    shown = resumen.assign(
        marcador=marcador,
        Date=resumen["Date"].astype(str),
        jams=resumen["jams"].map(T.fmt_num),
        diff_per_jam=resumen["diff_per_jam"].map(lambda v: T.SIN_DATO if pd.isna(v) else T.fmt_num(v, 2)),
        penalties=resumen["penalties"].map(T.fmt_num),
    )
    return shown[list(T.COLUMNAS_RESUMEN_PARTIDOS)].rename(columns=T.COLUMNAS_RESUMEN_PARTIDOS)


def frases_lo_que_mas_se_nota(frames: DataFrames) -> list[str]:
    """Hasta 3 frases generadas por reglas, cada una con su n; una regla con menos de MIN_JAMS_REGLA jams no sale.

    Reglas: (i) brecha de lead, (ii) costo de la caja (0 contra 1 o más jugadoras en caja al
    inicio del jam) y (iii) el periodo con peor diferencia por jam.
    """
    minimo = cfg.MIN_JAMS_REGLA
    frases = []
    kpis = kpis_equipo(frames)

    if kpis and kpis["jams"] >= minimo and pd.notna(kpis["rival_lead_pct"]):
        frases.append(
            T.FRASE_LEAD.format(
                nuestro=T.fmt_pct(kpis["lead_pct"]), rival=T.fmt_pct(kpis["rival_lead_pct"]),
                brecha=T.fmt_num(kpis["lead_pct"] - kpis["rival_lead_pct"], 1, " pp"), n=kpis["jams"],
            )
        )

    eff = effective_by_jam(frames)
    if eff.empty:
        return frases
    con_caja = eff.merge(box_state_by_jam(frames)[JAM_KEYS + ["box_start"]], on=JAM_KEYS, how="inner")
    sin, con = con_caja[con_caja["box_start"] == 0], con_caja[con_caja["box_start"] >= 1]
    if len(sin) >= minimo and len(con) >= minimo:
        frases.append(
            T.FRASE_CAJA.format(
                sin=T.fmt_num(sin["pts_against"].mean(), 2), n_sin=len(sin),
                con=T.fmt_num(con["pts_against"].mean(), 2), n_con=len(con),
            )
        )

    por_periodo = eff.groupby("Period")["eff"].agg(["mean", "size"])
    if len(por_periodo) >= 2 and (por_periodo["size"] >= minimo).all():
        peor = por_periodo["mean"].idxmin()
        otro = por_periodo["mean"].idxmax()
        frases.append(
            T.FRASE_PERIODO.format(
                peor=T.periodo_etiqueta(peor), valor_peor=T.fmt_num(por_periodo.loc[peor, "mean"], 2),
                n_peor=int(por_periodo.loc[peor, "size"]), otro=T.periodo_etiqueta(otro),
                valor_otro=T.fmt_num(por_periodo.loc[otro, "mean"], 2), n_otro=int(por_periodo.loc[otro, "size"]),
            )
        )
    return frases[:3]


# --- Jams y tiempo ---------------------------------------------------------------------------


def efectivos_por_tiempo(frames: DataFrames) -> tuple[pd.DataFrame, list[str]]:
    """Puntos efectivos por jam con el tiempo de juego REINICIADO en cada partido.

    `inicio_min` es el minuto de juego (suma de la duración de los jams anteriores del mismo
    partido) en que empieza el jam. Devuelve también los partidos que tienen jams pero ninguna
    fila en Time, para avisar en vez de omitirlos sin decir nada.
    """
    eff = effective_by_jam(frames)
    if eff.empty:
        return eff, []
    time = frames.time
    if time.empty:
        return eff.iloc[0:0].assign(Time=[], inicio_min=[]), sorted(eff["match_id"].unique())
    tiempos = time[JAM_KEYS + ["Time"]].assign(Time=_num(time["Time"])).drop_duplicates(subset=JAM_KEYS)
    union = eff.merge(tiempos, on=JAM_KEYS, how="inner").sort_values(["match_id", "Period", "Jam"])
    union["inicio_min"] = (union.groupby("match_id")["Time"].cumsum() - union["Time"]) / 60.0
    faltan = sorted(set(eff["match_id"]) - set(union["match_id"]))
    return union.reset_index(drop=True), faltan


# --- Faltas ---------------------------------------------------------------------------------


def faltas_por_jugadora_y_rol(frames: DataFrames) -> pd.DataFrame:
    """Faltas por jugadora y rol que tenía en el jam de la falta (etiqueta con número si el nombre se repite)."""
    pen = penalties_with_role(frames)
    if pen.empty:
        return pd.DataFrame(columns=["label", "rol", "penalties", "total"])
    out = pen.groupby(["Player_number", "Role"]).size().rename("penalties").reset_index()
    etiquetas = etiquetas_jugadoras(out["Player_number"].unique().tolist(), mapa_nombres(frames.player_names))
    out["label"] = out["Player_number"].map(etiquetas)
    out["rol"] = out["Role"].map(lambda r: T.SIN_ROL if r == SIN_ROL else T.ROLES.get(r, r))
    out["total"] = out.groupby("Player_number")["penalties"].transform("sum")
    return out[["label", "rol", "penalties", "total"]].sort_values(["total", "label"], ascending=[False, True])


def _faltas_por(frames: DataFrames, columna: str, etiqueta) -> pd.DataFrame:
    jam = agregar_match_id(frames.jam_table)
    pen = agregar_match_id(frames.penalty_tracker)
    if jam.empty:
        return pd.DataFrame(columns=["grupo", "penalties", "jams", "per_jam", "per_jam_txt"])
    jams = jam.groupby(columna).size().rename("jams")
    faltas = pen.groupby(columna).size().rename("penalties") if not pen.empty else pd.Series(dtype=int)
    out = pd.concat([jams, faltas], axis=1).fillna(0).astype(int)
    out["per_jam"] = out["penalties"] / out["jams"]
    out["per_jam_txt"] = out["per_jam"].map(lambda v: T.fmt_num(v, 2))
    out["grupo"] = [etiqueta(k) for k in out.index]
    return out.reset_index(drop=True)


def faltas_por_periodo(frames: DataFrames) -> pd.DataFrame:
    """Faltas, jams y faltas por jam de cada periodo."""
    return _faltas_por(frames, "Period", T.periodo_etiqueta)


def faltas_por_partido(frames: DataFrames) -> pd.DataFrame:
    """Faltas, jams y faltas por jam de cada partido."""
    return _faltas_por(frames, "match_id", etiqueta_partido)


def tabla_costo_caja(frames: DataFrames) -> pd.DataFrame:
    """Tabla «Costo de la caja» lista para mostrar (vacía si no hay datos)."""
    costo = box_cost_table(frames)
    if costo.empty:
        return costo
    shown = costo.assign(
        box_start_group=costo["box_start_group"].map(T.CAJA_GRUPOS),
        jams=costo["jams"].map(T.fmt_num),
        rival_lead_pct=costo["rival_lead_pct"].map(T.fmt_pct),
    )
    for col in ("points_for", "points_against", "effective"):
        shown[col] = costo[col].map(lambda v: T.fmt_num(v, 2))
    return shown.rename(columns=T.COLUMNAS_COSTO_CAJA)


# --- Combinaciones y jugadoras ---------------------------------------------------------------


def top_ternas(frames: DataFrames, n: int = 3) -> pd.DataFrame:
    """Las n ternas del pack con más jams juntas, lista para mostrar (con su n)."""
    ternas = estadisticas_combinaciones(frames, 3)
    if ternas.empty:
        return ternas
    nombres = mapa_nombres(frames.player_names)
    top = ternas.sort_values(["jams", "eff_rel"], ascending=[False, False]).head(n).copy()
    top["Combinación"] = top["combo"].map(lambda c: etiquetas_combinacion(c, nombres))
    top["jams"] = top["jams"].map(T.fmt_num)
    top["eff_rel"] = top["eff_rel"].map(lambda v: T.fmt_num(v, 2))
    return top[list(T.COLUMNAS_TERNAS)].rename(columns=T.COLUMNAS_TERNAS)


def efectividad_jugadoras(frames: DataFrames) -> pd.DataFrame:
    """player_effectiveness con etiquetas (nombre y n de jams) y la columna de muestra para graficar."""
    efectividad = player_effectiveness(frames)
    if efectividad.empty:
        return efectividad
    etiquetas = etiquetas_jugadoras(efectividad["Player_number"].tolist(), mapa_nombres(frames.player_names))
    out = efectividad.assign(Player=efectividad["Player_number"].map(etiquetas))
    out["label"] = out.apply(
        lambda r: f"{r['Player']} ({T.ETIQUETA_N_JAMS.format(n=r['jams'])}"
        + (f", {T.MUESTRA_BAJA.lower()})" if r["muestra_baja"] else ")"),
        axis=1,
    )
    out["muestra"] = out["muestra_baja"].map({True: T.MUESTRA_BAJA, False: ""})
    out["intervalo"] = out.apply(
        lambda r: T.SIN_DATO if pd.isna(r["ic_bajo"]) else f"{T.fmt_num(r['ic_bajo'], 2)} a {T.fmt_num(r['ic_alto'], 2)}",
        axis=1,
    )
    return out


def tabla_detalle_efectividad(efectividad: pd.DataFrame) -> pd.DataFrame:
    """Tabla de detalle por jugadora (con su n) lista para mostrar."""
    detalle = efectividad.copy()
    detalle["jams"] = detalle["jams"].map(T.fmt_num)
    for col in ("eff_por_jam", "eff_rel_por_jam", "pts_for_por_jam", "pts_against_por_jam",
                "pts_for_rel_por_jam", "pts_against_rel_por_jam", "con_y_sin", "eff_ajustada_jammer"):
        detalle[col] = detalle[col].map(lambda v: T.SIN_DATO if pd.isna(v) else T.fmt_num(v, 2))
    return detalle[list(T.COLUMNAS_EFECTIVIDAD)].rename(columns=T.COLUMNAS_EFECTIVIDAD)
