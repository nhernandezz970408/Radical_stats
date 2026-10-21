"""Gráficos Altair de la página de equipo.

Cada función recibe DataFrames ya calculados (ver `equipo.py`) y devuelve el gráfico.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from radical_stats import textos as T
from radical_stats.equipo import etiqueta_partido

VERDE = "#1A9850"
ROJO = "#D73027"
GRIS = "#9AA5B1"
OSCURO = "#1F2933"
COLORES_ROL = {T.ROLES["Jammer"]: "#C2272D", T.ROLES["Pivot"]: "#4C78A8", T.ROLES["Bloque"]: "#E17C05", T.SIN_ROL: GRIS}
_COLOR_SIGNO = alt.condition("datum.eff >= 0", alt.value(VERDE), alt.value(ROJO))


def _ancho_panel(n_partidos: int, total: int = 1000, minimo: int = 170) -> int:
    return max(minimo, total // max(n_partidos, 1) - 60)


def _con_paneles(eff: pd.DataFrame) -> pd.DataFrame:
    return eff.assign(
        partido=eff["match_id"].map(etiqueta_partido),
        periodo=eff["Period"].map(T.periodo_etiqueta),
        eff_txt=eff["eff"].map(lambda v: T.fmt_num(v, 0)),
    )


def grafico_efectivos_por_jam(eff: pd.DataFrame) -> alt.Chart:
    """Barras verdes y rojas de puntos efectivos por jam, un panel por partido y periodo (sin mezclar partidos)."""
    datos = _con_paneles(eff)
    ancho = _ancho_panel(datos["match_id"].nunique())
    barras = (
        alt.Chart(datos)
        .mark_bar()
        .encode(
            x=alt.X("Jam:O", title=T.EJE_JAM, axis=alt.Axis(labelOverlap=True, labelAngle=0)),
            y=alt.Y("eff:Q", title=T.EJE_PUNTOS_EFECTIVOS),
            color=_COLOR_SIGNO,
            tooltip=[
                alt.Tooltip("partido:N", title=T.PARTIDO),
                alt.Tooltip("periodo:N", title=T.PERIODO),
                alt.Tooltip("Jam:Q", title=T.JAM),
                alt.Tooltip("pts_for:Q", title=T.TOOLTIP_PUNTOS_NUESTROS),
                alt.Tooltip("pts_against:Q", title=T.TOOLTIP_PUNTOS_RIVAL),
                alt.Tooltip("eff_txt:N", title=T.PUNTOS_EFECTIVOS),
            ],
        )
        .properties(width=ancho, height=130)
    )
    return barras.facet(
        column=alt.Column("partido:N", title=None, sort=sorted(datos["partido"].unique())),
        row=alt.Row("periodo:N", title=None),
    )


def grafico_efectivos_por_tiempo(eff_tiempo: pd.DataFrame) -> alt.Chart:
    """Puntos efectivos por jam contra el tiempo de juego, con el tiempo reiniciado y un panel por partido."""
    datos = _con_paneles(eff_tiempo).assign(
        inicio_txt=eff_tiempo["inicio_min"].map(lambda v: T.fmt_num(v, 2))
    )
    ancho = _ancho_panel(datos["match_id"].nunique(), minimo=200)
    tooltip = [
        alt.Tooltip("inicio_txt:N", title=T.TOOLTIP_MINUTOS),
        alt.Tooltip("periodo:N", title=T.PERIODO),
        alt.Tooltip("Jam:Q", title=T.JAM),
        alt.Tooltip("eff_txt:N", title=T.PUNTOS_EFECTIVOS),
    ]
    base = alt.Chart().encode(
        x=alt.X("inicio_min:Q", title=T.EJE_MINUTOS_DE_JUEGO), y=alt.Y("eff:Q", title=T.EJE_PUNTOS_EFECTIVOS)
    )
    capas = alt.layer(
        base.mark_line(color=OSCURO),
        base.mark_circle(size=60).encode(color=_COLOR_SIGNO, tooltip=tooltip),
    ).properties(width=ancho, height=220)
    return capas.facet(column=alt.Column("partido:N", title=None), data=datos)


def grafico_faltas_por_jugadora_rol(faltas: pd.DataFrame) -> alt.Chart:
    """Barras horizontales apiladas por rol: faltas de cada jugadora según su rol en el jam de la falta."""
    orden = faltas.drop_duplicates("label").sort_values("total", ascending=False)["label"].tolist()
    return (
        alt.Chart(faltas)
        .mark_bar()
        .encode(
            x=alt.X("penalties:Q", title=T.EJE_FALTAS, axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("label:N", sort=orden, title=T.EJE_JUGADORA),
            color=alt.Color(
                "rol:N", title=T.TOOLTIP_ROL_FALTA,
                scale=alt.Scale(domain=list(COLORES_ROL), range=list(COLORES_ROL.values())),
            ),
            tooltip=[
                alt.Tooltip("label:N", title=T.JUGADORA),
                alt.Tooltip("rol:N", title=T.TOOLTIP_ROL_FALTA),
                alt.Tooltip("penalties:Q", title=T.FALTAS),
            ],
        )
        .properties(height=max(220, 24 * len(orden)))
    )


def grafico_faltas_barras(faltas: pd.DataFrame, eje: str) -> alt.Chart:
    """Barras de faltas por grupo (periodo o partido) con las faltas por jam en el tooltip."""
    return (
        alt.Chart(faltas)
        .mark_bar(color="#C2272D")
        .encode(
            x=alt.X("grupo:N", title=eje, sort=faltas["grupo"].tolist(), axis=alt.Axis(labelAngle=0, labelLimit=160)),
            y=alt.Y("penalties:Q", title=T.EJE_FALTAS, axis=alt.Axis(tickMinStep=1)),
            tooltip=[
                alt.Tooltip("grupo:N", title=eje),
                alt.Tooltip("penalties:Q", title=T.FALTAS),
                alt.Tooltip("jams:Q", title=T.TOOLTIP_JAMS_N),
                alt.Tooltip("per_jam_txt:N", title=T.TOOLTIP_FALTAS_POR_JAM),
            ],
        )
        .properties(height=220)
    )


def grafico_faltas_por_codigo(codigos: pd.DataFrame) -> alt.Chart:
    """Barras horizontales de faltas por código (nombre en español; «Sin código» para Unknown)."""
    datos = codigos.assign(
        pct_txt=codigos["pct"].map(T.fmt_pct),
        label=codigos.apply(
            lambda r: r["nombre_es"] if r["code"] == "Unknown" else f"{r['nombre_es']} ({r['code']})", axis=1
        ),
    )
    return (
        alt.Chart(datos)
        .mark_bar(color="#C2272D")
        .encode(
            x=alt.X("penalties:Q", title=T.EJE_FALTAS, axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("label:N", sort=datos["label"].tolist(), title=T.EJE_CODIGO, axis=alt.Axis(labelLimit=400)),
            tooltip=[
                alt.Tooltip("label:N", title=T.TOOLTIP_CODIGO),
                alt.Tooltip("penalties:Q", title=T.FALTAS),
                alt.Tooltip("pct_txt:N", title=T.TOOLTIP_PORCENTAJE_FALTAS),
                alt.Tooltip("descripcion_es:N", title=T.TOOLTIP_DESCRIPCION),
            ],
        )
        .properties(height=max(200, 24 * len(datos)))
    )


def grafico_efectividad_jugadoras(efectividad: pd.DataFrame, columna: str, etiqueta: str, eje: str, con_ic: bool) -> alt.LayerChart:
    """Barras horizontales de una métrica de efectividad por jugadora, con el n de jams en la etiqueta.

    Gris para muestra baja; con `con_ic`, barras de error del 80 %.
    """
    datos = efectividad.dropna(subset=[columna]).sort_values(columna, ascending=False).copy()
    datos["value_txt"] = datos[columna].map(lambda v: T.fmt_num(v, 2))
    datos["jams_txt"] = datos["jams"].map(T.fmt_num)
    datos["color"] = datos.apply(lambda r: GRIS if r["muestra_baja"] else (VERDE if r[columna] >= 0 else ROJO), axis=1)
    orden = datos["label"].tolist()
    tooltip = [
        alt.Tooltip("Player:N", title=T.JUGADORA),
        alt.Tooltip("jams_txt:N", title=T.TOOLTIP_JAMS_N),
        alt.Tooltip("value_txt:N", title=etiqueta),
        alt.Tooltip("muestra:N", title=T.TOOLTIP_MUESTRA),
    ]
    if con_ic:
        tooltip.insert(3, alt.Tooltip("intervalo:N", title=T.TOOLTIP_INTERVALO))
    barras = (
        alt.Chart(datos)
        .mark_bar()
        .encode(
            x=alt.X(f"{columna}:Q", title=eje),
            y=alt.Y("label:N", sort=orden, title=T.EJE_JUGADORA, axis=alt.Axis(labelLimit=400)),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=tooltip,
        )
    )
    capas = [barras]
    if con_ic:
        capas.append(
            alt.Chart(datos.dropna(subset=["ic_bajo"]))
            .mark_rule(color=OSCURO, strokeWidth=2)
            .encode(x="ic_bajo:Q", x2="ic_alto:Q", y=alt.Y("label:N", sort=orden))
        )
    capas.append(alt.Chart(pd.DataFrame({"cero": [0]})).mark_rule(color=OSCURO).encode(x="cero:Q"))
    return alt.layer(*capas).properties(height=max(240, 30 * len(datos)))
