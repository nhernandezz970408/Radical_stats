from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from radical_stats import config
from radical_stats.combinaciones import (
    combos_por_jam,
    estadisticas_combinaciones,
    etiquetas_combinacion,
    matriz_duplas,
    mejores_y_peores,
)
from radical_stats.data_loader import load_data
from radical_stats.lineups import lineups_long
from test_effectiveness import _synthetic_frames

ROOT = Path(__file__).resolve().parents[1]
FECHA = pd.Timestamp("2026-03-01").date()


def _long(pack: dict[str, str], jammer: str | int = 9) -> pd.DataFrame:
    """lineups_long de un jam con la jammer y los valores del pack (Pivot, Block_1..3) dados."""
    fila = {"Date": FECHA, "Rival": "X", "Period": 1, "Jam": 1, "Jammer": jammer, **pack}
    return lineups_long(pd.DataFrame([fila]))


def test_jam_sintetico_produce_1_cuarteto_4_ternas_y_6_duplas() -> None:
    long = _long({"Pivot": 1, "Block_1": 2, "Block_2": 3, "Block_3": 4})
    assert len(combos_por_jam(long, 4)) == 1
    assert len(combos_por_jam(long, 3)) == 4
    assert len(combos_por_jam(long, 2)) == 6
    assert combos_por_jam(long, 4)["combo"].iloc[0] == ("1", "2", "3", "4")


def test_el_orden_y_la_posicion_de_planilla_no_importan() -> None:
    a = combos_por_jam(_long({"Pivot": 1, "Block_1": 2, "Block_2": 3, "Block_3": 4}), 3)
    b = combos_por_jam(_long({"Pivot": 3, "Block_1": 4, "Block_2": 1, "Block_3": 2}), 3)
    assert set(a["combo"]) == set(b["combo"])


def test_un_signo_de_pregunta_en_el_pack_no_produce_cuarteto_pero_si_ternas_y_duplas() -> None:
    long = _long({"Pivot": 1, "Block_1": 2, "Block_2": 3, "Block_3": "?"})
    assert combos_por_jam(long, 4).empty
    assert len(combos_por_jam(long, 3)) == 1
    assert len(combos_por_jam(long, 2)) == 3
    assert "?" not in {p for c in combos_por_jam(long, 2)["combo"] for p in c}


def test_jam_con_menos_jugadoras_que_el_tamano_no_aporta() -> None:
    long = _long({"Pivot": 1, "Block_1": "?", "Block_2": "?", "Block_3": "?"})
    for tamano in (2, 3, 4):
        assert combos_por_jam(long, tamano).empty  # el pack tiene una sola jugadora válida


def test_quinteto_con_jammer_usa_las_cinco() -> None:
    long = _long({"Pivot": 1, "Block_1": 2, "Block_2": 3, "Block_3": 4}, jammer=9)
    quintetos = combos_por_jam(long, 5, incluir_jammer=True)
    assert quintetos["combo"].tolist() == [("1", "2", "3", "4", "9")]
    assert combos_por_jam(long, 5).empty  # sin jammer el pack solo tiene 4


def test_combinaciones_distintas_en_datos_reales() -> None:
    long = lineups_long(load_data().lineups)
    assert combos_por_jam(long, 4)["combo"].nunique() == 78
    assert combos_por_jam(long, 3)["combo"].nunique() == 136
    assert combos_por_jam(long, 2)["combo"].nunique() == 80
    assert combos_por_jam(long, 5, incluir_jammer=True)["combo"].nunique() == 95


def test_terna_arca_mamba_patada_de_mula() -> None:
    stats = estadisticas_combinaciones(load_data(), 3)
    fila = stats[stats["combo"] == ("17", "240", "913")].iloc[0]
    assert fila["jams"] == 24
    assert fila["pts_for"] == pytest.approx(2.42, abs=0.005)
    assert fila["pts_against"] == pytest.approx(3.58, abs=0.005)
    assert fila["partidos"] == 4 and fila["muestra"] == "Ok"


def test_cuarteto_y_dupla_reales() -> None:
    frames = load_data()
    cuartetos = estadisticas_combinaciones(frames, 4)
    assert cuartetos[cuartetos["combo"] == ("3", "17", "487", "913")]["jams"].item() == 9
    duplas = estadisticas_combinaciones(frames, 2)
    assert duplas[duplas["combo"] == ("17", "240")]["jams"].item() == 53


def test_ninguna_combinacion_bajo_el_minimo_aparece_sin_muestra_baja() -> None:
    frames = load_data()
    for tamano, incluir in ((2, False), (3, False), (4, False), (5, True)):
        minimo = config.MIN_JAMS_COMBINACION[tamano]
        stats = estadisticas_combinaciones(frames, tamano, incluir_jammer=incluir)
        bajo = stats[stats["jams"] < minimo]
        assert (bajo["muestra"] == "Baja").all()
        assert not (stats[stats["jams"] >= minimo]["muestra"] == "Baja").any()
    # El mínimo se puede cambiar y la etiqueta lo respeta.
    stats = estadisticas_combinaciones(frames, 3, minimo=20)
    assert (stats[stats["jams"] < 20]["muestra"] == "Baja").all()


def test_muestra_un_partido_y_bootstrap_con_5_o_mas_jams() -> None:
    stats = estadisticas_combinaciones(load_data(), 3, minimo=1)
    un_partido = stats[stats["partidos"] == 1]
    assert (un_partido["muestra"] == "Un partido").all()
    assert stats[stats["jams"] < config.BOOTSTRAP_MIN_JAMS]["ic_bajo"].isna().all()
    asi = stats[stats["jams"] >= config.BOOTSTRAP_MIN_JAMS]
    assert (asi["ic_bajo"] <= asi["eff_rel"]).all() and (asi["eff_rel"] <= asi["ic_alto"]).all()


def test_filtros_por_jammer_e_incluye() -> None:
    frames = load_data()
    todas = estadisticas_combinaciones(frames, 3)
    con_arca = estadisticas_combinaciones(frames, 3, incluye=["17"])
    assert len(con_arca) < len(todas) and all("17" in c for c in con_arca["combo"])
    con_jammer = estadisticas_combinaciones(frames, 3, jammer="16")
    # La jammer 16 jugó 61 jams; cada uno aporta 4 ternas del pack (los jams completos).
    assert 0 < con_jammer["jams"].sum() <= 4 * 61
    assert con_jammer["jams"].sum() < todas["jams"].sum()


def test_mejores_y_peores_solo_entre_las_que_superan_el_minimo() -> None:
    stats = estadisticas_combinaciones(load_data(), 3)
    minimo = config.MIN_JAMS_COMBINACION[3]
    mejores, peores = mejores_y_peores(stats, minimo, k=5)
    assert len(mejores) == 5 and len(peores) == 5
    assert (mejores["jams"] >= minimo).all() and (peores["jams"] >= minimo).all()
    assert mejores["eff_rel"].min() >= peores["eff_rel"].max()
    assert not set(mejores["combo"]) & set(peores["combo"])


def test_etiquetas_con_numero_si_el_nombre_se_repite() -> None:
    nombres = {"2": "Medusa", "10": "Medusa", "17": "Arca"}
    assert etiquetas_combinacion(("10", "17"), nombres) == "Medusa (#10) + Arca"
    assert etiquetas_combinacion(("17", "99"), nombres) == "Arca + #99"


def test_matriz_de_duplas_es_simetrica_y_marca_bajo_minimo() -> None:
    stats = estadisticas_combinaciones(load_data(), 2)
    minimo = config.MIN_JAMS_COMBINACION[2]
    matriz = matriz_duplas(stats, minimo)
    assert len(matriz) == 2 * len(stats)
    assert (matriz["bajo_minimo"] == (matriz["jams"] < minimo)).all()


def test_estadisticas_sinteticas() -> None:
    stats = estadisticas_combinaciones(_synthetic_frames(), 4)
    assert len(stats) == 2  # un cuarteto por partido
    assert (stats["partidos"] == 1).all() and (stats["muestra"] == "Un partido").all()


def test_la_pagina_de_alineaciones_carga_con_cada_tamano() -> None:
    at = AppTest.from_file(str(ROOT / "pages/3_Alineaciones.py"), default_timeout=90).run()
    assert not at.exception
    for tamano in (2, 4, 5, 3):
        at.selectbox[0].select(tamano).run()
        assert not at.exception
    assert any("las filas no son independientes" in i.value for i in at.info)


def test_la_aplicacion_registra_la_pagina_de_alineaciones() -> None:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    assert not at.exception
