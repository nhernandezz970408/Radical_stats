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
from radical_stats.combinaciones import (
    etiquetas_combinacion,
    matriz_duplas,
    mejores_y_peores,
)
from radical_stats.config import MIN_JAMS_COMBINACION
from radical_stats.data_loader import load_data
from radical_stats.filters import filter_by_period
from radical_stats.ui import apply_global_filters, show_empty_state, show_validation_warnings

st.title(T.ALINEACIONES_TITULO)
st.caption(T.ALINEACIONES_INTRO)

frames = load_data()
show_validation_warnings(frames)
filtered = apply_global_filters(frames, key_prefix="combos")

period_options = sorted(filtered.jam_table["Period"].dropna().astype(int).unique().tolist())
with st.sidebar:
    selected_periods = st.multiselect(
        T.FILTRO_PERIODO,
        options=period_options,
        default=period_options,
        format_func=T.periodo_etiqueta,
        help=T.AYUDA_FILTRO_PERIODO,
        placeholder=T.PLACEHOLDER_MULTISELECCION,
        key="combos_periods",
    )
filtered = filter_by_period(filtered, selected_periods)
filter_key = clave_filtrado(filtered)


names = filtered.player_names.copy()
names["Player_number"] = names["Player_number"].astype(str).str.strip()
number_to_name = dict(zip(names["Player_number"], names["Name"]))

# --- Controles ----------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
size = c1.selectbox(
    T.SELECTOR_TAMANO,
    options=list(T.TAMANOS_COMBINACION),
    index=1,
    format_func=T.TAMANOS_COMBINACION.get,
)
default_min = MIN_JAMS_COMBINACION[size]
minimum = c2.number_input(
    T.MINIMO_JAMS,
    min_value=1,
    max_value=60,
    value=default_min,
    step=1,
    key=f"combos_min_{size}",
    help=T.AYUDA_MINIMO.format(
        valores=", ".join(f"{T.TAMANOS_COMBINACION[k].lower()} {v}" for k, v in MIN_JAMS_COMBINACION.items())
    ),
)
jammer_options = cache.jammers(filtered, filter_key)
jammer = c3.selectbox(
    T.FILTRO_JAMMER,
    options=jammer_options,
    index=None,
    format_func=lambda n: f"{number_to_name.get(n, '#' + n)} (#{n})",
    placeholder=T.FILTRO_JAMMER_TODAS,
    help=T.AYUDA_FILTRO_JAMMER,
)
player_options = sorted(number_to_name, key=lambda n: number_to_name[n])
includes = st.multiselect(
    T.FILTRO_INCLUYE,
    options=player_options,
    format_func=lambda n: f"{number_to_name[n]} (#{n})",
    placeholder=T.PLACEHOLDER_MULTISELECCION,
    help=T.AYUDA_FILTRO_INCLUYE,
)
order_col, bajas_col = st.columns(2)
order_by = order_col.selectbox(T.ORDENAR_POR, [T.ORDEN_JAMS, T.ORDEN_EFECTIVOS])
show_low = bajas_col.checkbox(T.MOSTRAR_BAJAS, value=True)

stats = cache.combinaciones(
    filtered, filter_key, size, size == 5, int(minimum), jammer, tuple(includes)
)
st.info(T.NOTA_NO_INDEPENDIENTES)
if stats.empty:
    show_empty_state() if filtered.lineups.empty else st.info(T.SIN_COMBINACIONES_PAGINA)
    st.stop()

stats = stats.copy()
stats["Combinación"] = stats["combo"].map(lambda c: etiquetas_combinacion(c, number_to_name))
stats["intervalo"] = stats.apply(
    lambda r: T.SIN_DATO if pd.isna(r["ic_bajo"]) else f"{T.fmt_num(r['ic_bajo'], 2)} a {T.fmt_num(r['ic_alto'], 2)}",
    axis=1,
)
over_minimum = stats["jams"] >= minimum

# --- (a) Tabla ----------------------------------------------------------------------
st.subheader(T.TABLA_COMBINACIONES)
table = stats if show_low else stats[over_minimum]
if order_by == T.ORDEN_EFECTIVOS:
    # La muestra baja va siempre al final: no se ordena a nadie «mejor» por pocos jams.
    table = (
        table.assign(_baja=table["jams"] < minimum)
        .sort_values(["_baja", "eff_rel"], ascending=[True, False])
        .drop(columns="_baja")
    )
else:
    table = table.sort_values(["jams", "eff_rel"], ascending=[False, False])
shown = table[list(T.COLUMNAS_COMBINACIONES)].rename(columns=T.COLUMNAS_COMBINACIONES)
sample_col = T.COLUMNAS_COMBINACIONES["muestra"]


def _grey_low_sample(row: pd.Series) -> list[str]:
    style = "color: #9AA5B1" if row[sample_col] == T.MUESTRA_CORTA_BAJA else ""
    return [style] * len(row)


numeric = {
    "jams": 0, "partidos": 0, "pts_for": 2, "pts_against": 2, "eff": 2, "eff_rel": 2, "faltas_por_jam": 2,
}
styler = shown.style.apply(_grey_low_sample, axis=1)
for key, decimals in numeric.items():
    styler = styler.format(lambda v, d=decimals: T.fmt_num(v, d), subset=[T.COLUMNAS_COMBINACIONES[key]])
for key in ("rival_lead_pct", "caja_pct"):
    styler = styler.format(T.fmt_pct, subset=[T.COLUMNAS_COMBINACIONES[key]])
st.dataframe(styler, use_container_width=True, hide_index=True)
st.caption(T.NOTA_ORDEN_MUESTRA_BAJA)

# --- (b) Barras con intervalo ----------------------------------------------------------
eligible = stats[over_minimum].copy()
st.subheader(T.GRAFICO_COMBINACIONES)
if eligible.empty:
    st.info(T.SIN_COMBINACIONES_SOBRE_MINIMO.format(minimo=int(minimum)))
else:
    eligible["etiqueta"] = eligible.apply(
        lambda r: f"{r['Combinación']} ({T.ETIQUETA_N_JAMS.format(n=r['jams'])}"
        + (f", {T.MUESTRA_UN_PARTIDO.lower()})" if r["muestra"] == T.MUESTRA_UN_PARTIDO else ")"),
        axis=1,
    )
    eligible = eligible.sort_values("eff_rel", ascending=False)
    eligible["color"] = eligible["eff_rel"].map(lambda v: "#1A9850" if v >= 0 else "#D73027")
    eligible["valor_txt"] = eligible["eff_rel"].map(lambda v: T.fmt_num(v, 2))
    eligible["jams_txt"] = eligible["jams"].map(T.fmt_num)
    order = eligible["etiqueta"].tolist()
    bars = (
        alt.Chart(eligible)
        .mark_bar()
        .encode(
            x=alt.X("eff_rel:Q", title=T.EJE_PUNTOS_EFECTIVOS),
            y=alt.Y("etiqueta:N", sort=order, title=T.ALINEACION, axis=alt.Axis(labelLimit=500)),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("Combinación:N", title=T.ALINEACION),
                alt.Tooltip("jams_txt:N", title=T.TOOLTIP_JAMS_N),
                alt.Tooltip("valor_txt:N", title=T.COLUMNAS_COMBINACIONES["eff_rel"]),
                alt.Tooltip("intervalo:N", title=T.TOOLTIP_INTERVALO),
                alt.Tooltip("muestra:N", title=T.TOOLTIP_MUESTRA),
            ],
        )
    )
    errors = (
        alt.Chart(eligible.dropna(subset=["ic_bajo"]))
        .mark_rule(color="#1F2933", strokeWidth=2)
        .encode(x="ic_bajo:Q", x2="ic_alto:Q", y=alt.Y("etiqueta:N", sort=order))
    )
    zero = alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(color="#1F2933").encode(x="zero:Q")
    st.altair_chart(
        alt.layer(bars, errors, zero).properties(height=max(240, 28 * len(eligible))),
        use_container_width=True,
    )
    st.caption(T.GRAFICO_COMBINACIONES_NOTA)

# --- (c) Mejores 5 y peores 5 ------------------------------------------------------------
if not eligible.empty:
    best, worst = mejores_y_peores(stats, int(minimum), k=5)
    best_col, worst_col = st.columns(2)
    for column, title, rows in ((best_col, T.MEJORES_5, best), (worst_col, T.PEORES_5, worst)):
        with column:
            st.subheader(title)
            summary = pd.DataFrame(
                {
                    T.COLUMNAS_COMBINACIONES["Combinación"]: rows["combo"].map(
                        lambda c: etiquetas_combinacion(c, number_to_name)
                    ),
                    T.COLUMNAS_COMBINACIONES["jams"]: rows["jams"].map(T.fmt_num),
                    T.COLUMNAS_COMBINACIONES["eff_rel"]: rows["eff_rel"].map(lambda v: T.fmt_num(v, 2)),
                    T.COLUMNAS_COMBINACIONES["muestra"]: rows["muestra"],
                }
            )
            st.dataframe(summary, use_container_width=True, hide_index=True)

# --- (d) Matriz de duplas ------------------------------------------------------------------
st.subheader(T.MATRIZ_DUPLAS)
if st.checkbox(T.MOSTRAR_MATRIZ):
    pair_min = MIN_JAMS_COMBINACION[2]
    pairs = cache.combinaciones(filtered, filter_key, 2, False, pair_min, jammer, tuple(includes))
    matrix = matriz_duplas(pairs, pair_min)
    if matrix.empty:
        st.info(T.SIN_COMBINACIONES_PAGINA)
    else:
        matrix["jugadora"] = matrix["a"].map(lambda n: number_to_name.get(n, f"#{n}"))
        matrix["con"] = matrix["b"].map(lambda n: number_to_name.get(n, f"#{n}"))
        matrix["valor_txt"] = matrix["eff_rel"].map(lambda v: T.fmt_num(v, 2))
        matrix["jams_txt"] = matrix["jams"].map(T.fmt_num)
        order = sorted(set(matrix["jugadora"]))
        heat = (
            alt.Chart(matrix)
            .mark_rect()
            .encode(
                x=alt.X("con:N", sort=order, title=None, axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("jugadora:N", sort=order, title=None),
                color=alt.condition(
                    "datum.bajo_minimo",
                    alt.value("#D0D5DB"),
                    alt.Color("eff_rel:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                              title=T.COLUMNAS_COMBINACIONES["eff_rel"]),
                ),
                tooltip=[
                    alt.Tooltip("jugadora:N", title=T.TOOLTIP_JUGADORA_A),
                    alt.Tooltip("con:N", title=T.TOOLTIP_JUGADORA_B),
                    alt.Tooltip("jams_txt:N", title=T.TOOLTIP_JAMS_N),
                    alt.Tooltip("valor_txt:N", title=T.COLUMNAS_COMBINACIONES["eff_rel"]),
                ],
            )
            .properties(height=max(300, 26 * len(order)))
        )
        st.altair_chart(heat, use_container_width=True)
        st.caption(T.MATRIZ_AYUDA.format(minimo=pair_min))
