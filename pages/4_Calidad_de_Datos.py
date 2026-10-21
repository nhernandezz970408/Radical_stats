from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats import cache
from radical_stats import textos as T
from radical_stats.data_loader import firma_datos, load_data
from radical_stats.ui import aplicar_estilo_ancho

aplicar_estilo_ancho()
st.title(T.CALIDAD_TITULO)
st.caption(T.CALIDAD_INTRO)

chequeos = cache.chequeos_calidad(load_data(), (firma_datos(),))
con_aviso = [c for c in chequeos if c.cantidad]
if con_aviso:
    st.warning(T.CALIDAD_RESUMEN.format(avisos=len(con_aviso), total=len(chequeos)))
else:
    st.success(T.CALIDAD_TODO_OK.format(total=len(chequeos)))

for chequeo in chequeos:
    with st.container(border=True):
        color = "green" if chequeo.cantidad == 0 else "orange"
        st.markdown(f"**{chequeo.titulo}** :{color}[**{chequeo.estado}**] · {T.CALIDAD_CANTIDAD.format(n=chequeo.cantidad)}")
        st.caption(chequeo.descripcion)
        if chequeo.detalle is not None:
            with st.expander(T.CALIDAD_DETALLE):
                st.dataframe(chequeo.detalle.rename(columns=T.COLUMNAS_CALIDAD), hide_index=True, use_container_width=True)
        if chequeo.filas.empty:
            continue
        filas = chequeo.filas.rename(columns=T.COLUMNAS_CALIDAD)
        st.dataframe(filas, hide_index=True, use_container_width=True)
        st.download_button(
            T.DESCARGAR_FILAS,
            data=filas.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name=f"calidad_{chequeo.clave}.csv",
            mime="text/csv",
            key=f"descarga_{chequeo.clave}",
        )
