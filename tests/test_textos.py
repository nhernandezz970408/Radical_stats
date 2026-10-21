from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from radical_stats import textos as T

ROOT = Path(__file__).resolve().parents[1]
PAGINAS = [
    "app.py",
    "pages/1_Estadisticas_de_Equipo.py",
    "pages/2_Estadisticas_de_Jugadoras.py",
]


def _textos_publicos():
    for nombre, valor in vars(T).items():
        if nombre.startswith("_") or not nombre.isupper():
            continue
        yield nombre, valor


def test_ninguna_clave_de_textos_esta_vacia() -> None:
    claves = list(_textos_publicos())
    assert claves
    for nombre, valor in claves:
        if isinstance(valor, dict):
            assert valor, nombre
            for v in valor.values():
                partes = v if isinstance(v, tuple) else (v,)
                assert all(p.strip() for p in partes if isinstance(p, str)), nombre
                assert any(isinstance(p, str) for p in partes), nombre
        elif isinstance(valor, (tuple, list)):
            assert valor and all(isinstance(v, str) and v.strip() for v in valor), nombre
        else:
            assert isinstance(valor, str) and valor.strip(), nombre


def test_formatos_numericos_en_espanol() -> None:
    assert T.fmt_num(2.964, 2) == "2,96"
    assert T.fmt_num(1234.5, 1) == "1.234,5"
    assert T.fmt_num(447) == "447"
    assert T.fmt_pct(35.1) == "35,1 %"
    assert T.periodo_etiqueta(1) == "1.er periodo"
    assert T.periodo_etiqueta(2) == "2.º periodo"


@pytest.mark.parametrize("pagina", PAGINAS)
def test_las_paginas_se_importan_sin_error(pagina: str) -> None:
    at = AppTest.from_file(str(ROOT / pagina), default_timeout=60).run()
    assert not at.exception
