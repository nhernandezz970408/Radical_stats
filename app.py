from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats import textos as T

st.set_page_config(
    page_title=T.NOMBRE_APP,
    page_icon=":bar_chart:",
    layout="wide",
)


def inicio() -> None:
    st.title(T.TITULO_APP)
    st.caption(T.SUBTITULO_APP)
    st.markdown(T.INICIO_VISTAS)


navegacion = st.navigation(
    [
        st.Page(inicio, title=T.PAGINA_INICIO, url_path="inicio", default=True),
        st.Page("pages/1_Estadisticas_de_Equipo.py", title=T.PAGINA_EQUIPO, url_path="equipo"),
        st.Page(
            "pages/2_Estadisticas_de_Jugadoras.py",
            title=T.PAGINA_JUGADORAS,
            url_path="jugadoras",
        ),
        st.Page("pages/3_Alineaciones.py", title=T.PAGINA_ALINEACIONES, url_path="alineaciones"),
        st.Page("pages/4_Calidad_de_Datos.py", title=T.PAGINA_CALIDAD, url_path="calidad"),
    ]
)
navegacion.run()
