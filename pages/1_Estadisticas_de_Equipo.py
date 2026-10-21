from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats import cache, equipo, graficos
from radical_stats import textos as T
from radical_stats.cache import clave_filtrado
from radical_stats.config import MIN_JAMS_JUGADORA, MIN_JAMS_REGLA
from radical_stats.data_loader import load_data, load_penalty_codes
from radical_stats.lineups import count_incomplete_jams
from radical_stats.metrics import effective_by_jam, penalty_code_counts
from radical_stats.ui import aplicar_estilo_ancho, aplicar_filtros, show_empty_state, show_validation_warnings

aplicar_estilo_ancho()
frames = load_data()
show_validation_warnings(frames)
filtros = aplicar_filtros(frames, key_prefix="team")
datos = filtros.filtrados
clave = clave_filtrado(datos)

st.title(equipo.titulo_equipo(filtros.seleccionados, filtros.opciones, equipo.rival_unico(datos)))
if datos.jam_table.empty:
    show_empty_state()
    st.stop()
incompletos = count_incomplete_jams(datos.lineups)
if incompletos:
    st.info(T.JAMS_INCOMPLETOS_EQUIPO.format(n=incompletos))

tab_resumen, tab_jams, tab_faltas, tab_combinaciones = st.tabs(
    [T.PESTANA_EQ_RESUMEN, T.PESTANA_EQ_JAMS, T.PESTANA_EQ_FALTAS, T.PESTANA_EQ_COMBINACIONES]
)

with tab_resumen:
    resto = filtros.resto if not filtros.resto.jam_table.empty else None
    tarjetas = equipo.tarjetas_resumen(datos, resto)
    for fila in (tarjetas[:4], tarjetas[4:]):
        for columna, t in zip(st.columns(4), fila):
            columna.metric(t.etiqueta, t.valor, delta=t.delta, delta_color=t.delta_color, help=t.ayuda)
    izquierda, derecha = st.columns([3, 2])
    with izquierda:
        st.markdown(f"**{T.TABLA_POR_PARTIDO}**")
        resumen = equipo.resumen_por_partido(datos)
        st.dataframe(equipo.formatear_resumen_partidos(resumen), hide_index=True, use_container_width=True)
    with derecha:
        st.markdown(f"**{T.LO_QUE_MAS_SE_NOTA}**")
        frases = equipo.frases_lo_que_mas_se_nota(datos)
        for frase in frases:
            st.markdown(f"- {frase}")
        if not frases:
            st.caption(T.SIN_FRASES.format(minimo=MIN_JAMS_REGLA))

with tab_jams:
    st.caption(T.DEFINICION_PUNTOS_EFECTIVOS)
    efectivos = effective_by_jam(datos)
    if efectivos.empty:
        st.info(T.FALTAN_JAMS_RIVAL)
    else:
        st.subheader(T.TITULO_EFECTIVOS_POR_JAM_PANELES)
        st.altair_chart(graficos.grafico_efectivos_por_jam(efectivos))
        st.subheader(T.TITULO_EFECTIVOS_POR_TIEMPO_PANELES)
        por_tiempo, sin_tiempo = equipo.efectivos_por_tiempo(datos)
        if sin_tiempo:
            partidos = ", ".join(equipo.etiqueta_partido(m) for m in sin_tiempo)
            st.warning(T.AVISO_SIN_TIEMPO_PARTIDOS.format(partidos=partidos))
        if por_tiempo.empty:
            st.info(T.SIN_TIEMPOS)
        else:
            st.altair_chart(graficos.grafico_efectivos_por_tiempo(por_tiempo))
            st.caption(T.NOTA_TIEMPO_POR_PARTIDO)

with tab_faltas:
    por_jugadora = equipo.faltas_por_jugadora_y_rol(datos)
    st.subheader(T.TITULO_FALTAS_JUGADORA_ROL)
    if por_jugadora.empty:
        st.info(T.SIN_FALTAS)
    else:
        st.altair_chart(graficos.grafico_faltas_por_jugadora_rol(por_jugadora), use_container_width=True)
    izquierda, derecha = st.columns(2)
    with izquierda:
        st.subheader(T.TITULO_FALTAS_PERIODO)
        st.altair_chart(graficos.grafico_faltas_barras(equipo.faltas_por_periodo(datos), T.EJE_PERIODO), use_container_width=True)
    with derecha:
        st.subheader(T.TITULO_FALTAS_PARTIDO)
        st.altair_chart(graficos.grafico_faltas_barras(equipo.faltas_por_partido(datos), T.EJE_PARTIDO), use_container_width=True)
    st.subheader(T.TITULO_COSTO_CAJA)
    st.caption(T.DEFINICION_CAJA)
    costo = equipo.tabla_costo_caja(datos)
    if costo.empty:
        st.info(T.SIN_COSTO_CAJA)
    else:
        st.dataframe(costo, hide_index=True, use_container_width=True)
        st.caption(T.NOTA_COSTO_CAJA)
    st.subheader(T.TITULO_FALTAS_POR_CODIGO)
    codigos = penalty_code_counts(datos, load_penalty_codes())
    if codigos.empty:
        st.info(T.SIN_FALTAS_CODIGO)
    else:
        st.altair_chart(graficos.grafico_faltas_por_codigo(codigos), use_container_width=True)
        sin_codigo = codigos[codigos["code"] == "Unknown"]
        if not sin_codigo.empty:
            st.caption(T.NOTA_SIN_CODIGO.format(
                n=T.fmt_num(int(sin_codigo["penalties"].iloc[0])), total=T.fmt_num(int(codigos["penalties"].sum())),
                pct=T.fmt_pct(float(sin_codigo["pct"].iloc[0]))))

with tab_combinaciones:
    st.subheader(T.RESUMEN_TERNAS_TITULO)
    st.caption(T.RESUMEN_TERNAS_INTRO)
    ternas = cache.top_ternas(datos, clave)
    if ternas.empty:
        st.info(T.SIN_ALINEACIONES)
    else:
        st.dataframe(ternas, hide_index=True, use_container_width=True)
    try:
        st.page_link("pages/3_Alineaciones.py", label=T.ENLACE_ALINEACIONES)
    except Exception:  # la página no está registrada (p. ej. al ejecutar esta página sola)
        st.caption(T.ENLACE_ALINEACIONES_SIN_NAVEGACION)
    st.subheader(T.TITULO_PUNTOS_EFECTIVOS_JUGADORA)
    st.info(T.NOTA_ACUMULADO)
    efectividad = cache.efectividad_jugadoras(datos, clave)
    if efectividad.empty:
        st.info(T.SIN_EFECTIVIDAD)
    else:
        metrica = st.selectbox(T.SELECTOR_METRICA_EFECTIVIDAD, list(T.METRICAS_EFECTIVIDAD), key="team_eff_metric")
        columna, ayuda, eje, con_ic = T.METRICAS_EFECTIVIDAD[metrica]
        st.caption(ayuda)
        st.altair_chart(graficos.grafico_efectividad_jugadoras(efectividad, columna, metrica, eje, con_ic), use_container_width=True)
        st.caption(T.LEYENDA_MUESTRA_BAJA.format(minimo=MIN_JAMS_JUGADORA))
        sin_dato = int(efectividad[columna].isna().sum())
        if sin_dato:
            st.caption(T.JUGADORAS_SIN_DATO_METRICA.format(k=sin_dato))
        st.markdown(f"**{T.TABLA_EFECTIVIDAD}**")
        st.dataframe(equipo.tabla_detalle_efectividad(efectividad), hide_index=True, use_container_width=True)
