from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats import cache
from radical_stats import textos as T
from radical_stats.cache import clave_filtrado
from radical_stats.config import MIN_JAMS_CASO, MIN_JAMS_COMBINACION, MIN_JAMS_JUGADORA
from radical_stats.data_loader import load_data, load_penalty_codes
from radical_stats.filters import filter_by_period
from radical_stats.lineups import count_incomplete_jams
from radical_stats.metrics import SIN_ROL, player_penalty_breakdown
from radical_stats.perfil import (
    best_and_worst_combinations,
    formatear_tabla_rol,
    pack_combinations,
    penalty_box_cost,
    player_match_table,
    player_penalty_codes,
    resumen_tres_frases,
    role_table,
    roles_con_jams,
)
from radical_stats.ui import apply_global_filters, show_empty_state, show_validation_warnings

st.title(T.JUGADORAS_TITULO)

frames = load_data()
show_validation_warnings(frames)
filtered = apply_global_filters(frames, key_prefix="player")

period_options = sorted(filtered.jam_table["Period"].dropna().astype(int).unique().tolist())
with st.sidebar:
    selected_periods = st.multiselect(
        T.FILTRO_PERIODO,
        options=period_options,
        default=period_options,
        format_func=T.periodo_etiqueta,
        help=T.AYUDA_FILTRO_PERIODO,
        placeholder=T.PLACEHOLDER_MULTISELECCION,
        key="player_periods",
    )
filtered = filter_by_period(filtered, selected_periods)

incomplete_jams = count_incomplete_jams(filtered.lineups)
if incomplete_jams:
    st.info(T.JAMS_INCOMPLETOS_JUGADORAS.format(n=incomplete_jams))

clave = clave_filtrado(filtered)
overview = cache.vista_general_jugadoras(filtered, clave)
if overview.empty:
    show_empty_state()
    st.stop()

names = filtered.player_names.copy()
names["Player_number"] = names["Player_number"].astype(str).str.strip()
number_to_name = dict(zip(names["Player_number"], names["Name"]))


def _label(number: str) -> str:
    """Nombre y número siempre (hay dos «Medusa»)."""
    return f"{number_to_name.get(number, '#' + number)} (#{number})"


overview["label"] = overview["Player_number"].map(_label)
overview = overview.sort_values(["jams", "label"], ascending=[False, True]).reset_index(drop=True)
label_to_number = dict(zip(overview["label"], overview["Player_number"]))

with st.expander(T.COMO_LEER_TITULO):
    for line in T.COMO_LEER_LINEAS:
        st.markdown(f"- {line.format(minimo=MIN_JAMS_JUGADORA)}")

selected_label = st.selectbox(
    T.SELECCIONAR_JUGADORA, overview["label"].tolist(), placeholder=T.PLACEHOLDER_SELECCION
)
player_number = label_to_number[selected_label]
profile = cache.perfil_jugadora(filtered, clave, player_number)

# --- Tarjetas -----------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    T.TARJETA_JAMS,
    T.fmt_num(profile.jams),
    delta=T.TARJETA_JAMS_DELTA.format(pct=T.fmt_pct(profile.pct_team_jams, 0)),
    delta_color="off",
    delta_arrow="off",
)
c2.metric(T.TARJETA_PARTIDOS, T.fmt_num(profile.matches))
c3.metric(
    T.TARJETA_ROL,
    T.ROLES.get(profile.main_role, T.SIN_ROL_PRINCIPAL),
    delta=T.TARJETA_ROL_DELTA.format(pct=T.fmt_pct(profile.main_role_pct, 0)),
    delta_color="off",
    delta_arrow="off",
)
rate_diff = profile.penalties_diff
c4.metric(
    T.TARJETA_FALTAS_POR_JAM,
    T.fmt_num(profile.penalties_per_jam, 2),
    delta=T.TARJETA_FALTAS_DELTA.format(
        signo="+" if rate_diff > 0 else "",
        dif=T.fmt_num(rate_diff, 2),
        equipo=T.fmt_num(profile.team_penalties_per_jam, 2),
    ),
    delta_color="off",
    delta_arrow="off",
    help=T.TARJETA_FALTAS_AYUDA,
)

# --- Resumen en tres frases ---------------------------------------------------------
st.subheader(T.RESUMEN_TITULO)
sentences = resumen_tres_frases(profile)
if profile.low_sample:
    st.markdown(f"**{sentences[0]}**")
    for sentence in sentences[1:]:
        st.markdown(f":gray[{sentence}]")
else:
    for sentence in sentences:
        st.markdown(sentence)

# --- Pestañas -----------------------------------------------------------------------
roles_played = roles_con_jams(filtered, player_number)
tab_labels = [T.PESTANAS_ROL[r] for r in roles_played] + [
    T.PESTANA_FALTAS,
    T.PESTANA_POR_PARTIDO,
    T.PESTANA_CON_QUIEN,
]
tabs = st.tabs(tab_labels)
tab_by_label = dict(zip(tab_labels, tabs))

for role in roles_played:
    with tab_by_label[T.PESTANAS_ROL[role]]:
        role_jams = profile.roles_jams[role]
        if role_jams < MIN_JAMS_JUGADORA:
            st.caption(T.MUESTRA_BAJA_ROL.format(minimo=MIN_JAMS_JUGADORA, n=role_jams))
        st.dataframe(
            formatear_tabla_rol(role_table(filtered, player_number, role)),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(T.NOTA_COMPARACION_BLOQUE if role == "Bloque" else T.NOTA_COMPARACION_ROL)

with tab_by_label[T.PESTANA_FALTAS]:
    codes = player_penalty_codes(filtered, player_number, load_penalty_codes())
    if codes.empty:
        st.info(T.SIN_FALTAS_JUGADORA)
    else:
        st.markdown(f"**{T.FALTAS_POR_CODIGO_JUGADORA}**")
        codes["pct_txt"] = codes["pct"].map(T.fmt_pct)
        chart = (
            alt.Chart(codes)
            .mark_bar(color="#C2272D")
            .encode(
                x=alt.X("penalties:Q", title=T.EJE_FALTAS, axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("nombre_es:N", sort=codes["nombre_es"].tolist(), title=T.EJE_CODIGO),
                tooltip=[
                    alt.Tooltip("nombre_es:N", title=T.TOOLTIP_CODIGO),
                    alt.Tooltip("penalties:Q", title=T.FALTAS),
                    alt.Tooltip("pct_txt:N", title=T.TOOLTIP_PORCENTAJE_FALTAS),
                    alt.Tooltip("descripcion_es:N", title=T.TOOLTIP_DESCRIPCION),
                ],
            )
        )
        st.altair_chart(chart, use_container_width=True)

        def _show_breakdown(title: str, by: str, label) -> None:
            breakdown = player_penalty_breakdown(filtered, player_number, by)
            st.markdown(f"**{title}**")
            if breakdown.empty:
                st.info(T.SIN_FALTAS_CODIGO)
                return
            breakdown["key"] = breakdown["key"].map(label)
            shown = breakdown.copy()
            for col in ("jams", "penalties"):
                shown[col] = shown[col].map(T.fmt_num)
            for col, decimals in (("penalties_per_jam", 2), ("minutes_on_track", 1), ("penalties_per_10min", 2)):
                shown[col] = shown[col].map(lambda v, d=decimals: T.fmt_num(v, d) if pd.notna(v) else T.SIN_DATO)
            st.dataframe(shown.rename(columns=T.COLUMNAS_DESGLOSE_FALTAS), use_container_width=True, hide_index=True)

        _show_breakdown(T.FALTAS_POR_PARTIDO_JUGADORA, "match_id", str)
        _show_breakdown(T.FALTAS_POR_ROL_JUGADORA, "Role", lambda r: T.SIN_ROL if r == SIN_ROL else T.ROLES.get(r, r))
        st.caption(T.NOTA_MINUTOS_EN_PISTA)

    st.markdown(f"**{T.COSTO_FALTAS}**")
    cost = penalty_box_cost(filtered, player_number)
    if cost["valido"]:
        st.markdown(
            T.COSTO_FALTAS_TEXTO.format(
                con=T.fmt_num(cost["con_caja"], 2), n_con=cost["n_con_caja"],
                sin=T.fmt_num(cost["sin_caja"], 2), n_sin=cost["n_sin_caja"],
            )
        )
    else:
        st.info(
            T.COSTO_FALTAS_INSUFICIENTE.format(
                minimo=MIN_JAMS_CASO, n_con=cost["n_con_caja"], n_sin=cost["n_sin_caja"]
            )
        )
    st.caption(T.NOTA_COSTO_CAJA)

with tab_by_label[T.PESTANA_POR_PARTIDO]:
    by_match = player_match_table(filtered, player_number)
    if by_match.empty:
        st.info(T.SIN_EFECTIVIDAD)
    else:
        by_match["main_role"] = by_match["main_role"].map(lambda r: T.ROLES.get(r, T.SIN_DATO))
        for col in ("jams", "penalties"):
            by_match[col] = by_match[col].map(T.fmt_num)
        for col, decimals in (("eff_por_jam", 2), ("eff_rel_por_jam", 2), ("minutes_on_track", 1)):
            by_match[col] = by_match[col].map(lambda v, d=decimals: T.fmt_num(v, d) if pd.notna(v) else T.SIN_DATO)
        st.dataframe(
            by_match[list(T.POR_PARTIDO_COLUMNAS)].rename(columns=T.POR_PARTIDO_COLUMNAS),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(T.NOTA_ACUMULADO)
        st.caption(T.NOTA_MINUTOS_EN_PISTA)

with tab_by_label[T.PESTANA_CON_QUIEN]:
    st.caption(T.CON_QUIEN_INTRO.format(minimo_dupla=MIN_JAMS_COMBINACION[2], minimo_terna=MIN_JAMS_COMBINACION[3]))
    combos = pack_combinations(filtered, player_number)
    if combos.empty:
        st.info(T.SIN_COMBINACIONES_JUGADORA.format(minimo=MIN_JAMS_COMBINACION[2]))
        st.caption(T.CON_QUIEN_SOLO_PACK)
    else:
        def _combo_label(players: tuple) -> str:
            return " + ".join(_label(p) for p in players if p != player_number)

        for size, best_title, worst_title in (
            (2, T.MEJORES_DUPLAS, T.PEORES_DUPLAS),
            (3, T.MEJORES_TERNAS, T.PEORES_TERNAS),
        ):
            best, worst = best_and_worst_combinations(combos, size)
            for title, table in ((best_title, best), (worst_title, worst)):
                st.markdown(f"**{title}**")
                if table.empty:
                    st.caption(T.SIN_COMBINACIONES_JUGADORA.format(minimo=MIN_JAMS_COMBINACION[size]))
                    continue
                shown = pd.DataFrame(
                    {
                        T.COL_COMBINACION: table["players"].map(_combo_label),
                        T.COL_N_JAMS: table["jams"].map(T.fmt_num),
                        T.COL_RELATIVOS: table["eff_rel_por_jam"].map(lambda v: T.fmt_num(v, 2)),
                        T.COL_EFECTIVOS: table["eff_por_jam"].map(lambda v: T.fmt_num(v, 2)),
                    }
                )
                st.dataframe(shown, use_container_width=True, hide_index=True)

# --- Todas las jugadoras ------------------------------------------------------------
st.subheader(T.TODAS_JUGADORAS_TITULO)
everyone = overview.copy()
everyone["main_role"] = everyone["main_role"].map(lambda r: T.ROLES.get(r, T.SIN_DATO))
everyone = everyone.sort_values("label")[list(T.TODAS_JUGADORAS_COLUMNAS)].rename(
    columns=T.TODAS_JUGADORAS_COLUMNAS
)
jams_col, sample_col = T.TODAS_JUGADORAS_COLUMNAS["jams"], T.TODAS_JUGADORAS_COLUMNAS["muestra"]
numeric_cols = [T.TODAS_JUGADORAS_COLUMNAS[c] for c in ("eff_rel_por_jam", "pts_against_por_jam", "penalties_per_jam")]


def _grey_low_sample(row: pd.Series) -> list[str]:
    style = "color: #9AA5B1" if row[sample_col] == T.MUESTRA_CORTA_BAJA else ""
    return [style] * len(row)


styled = (
    everyone.style.format(precision=2, decimal=",", na_rep=T.SIN_DATO, subset=numeric_cols)
    .format(precision=0, subset=[jams_col])
    .apply(_grey_low_sample, axis=1)
)
st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption(T.TODAS_JUGADORAS_NOTA.format(minimo=MIN_JAMS_JUGADORA))
st.download_button(
    T.DESCARGAR_CSV,
    data=everyone.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
    file_name=T.NOMBRE_ARCHIVO_CSV,
    mime="text/csv",
)
