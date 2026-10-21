from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from radical_stats import equipo, graficos
from radical_stats.data_loader import load_data, load_penalty_codes
from radical_stats.filters import filter_by_match
from radical_stats.jugadoras import etiqueta_jugadora, etiquetas_jugadoras, mapa_nombres
from radical_stats.metrics import effective_by_jam, penalty_code_counts
from radical_stats.partidos import agregar_match_id_a_frames
from test_effectiveness import _synthetic_frames

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "pages" / "1_Estadisticas_de_Equipo.py"
SIN_TIEMPO = "2026-08-08 | Rock and Roller Queens"


def test_kpis_reales() -> None:
    kpis = equipo.kpis_equipo(load_data())
    assert kpis["jams"] == 151
    assert kpis["pts_for"] == pytest.approx(2.96, abs=0.005)
    assert kpis["pts_against"] == pytest.approx(4.52, abs=0.005)
    assert kpis["diff"] == pytest.approx(-1.56, abs=0.005)
    assert kpis["lead_pct"] == pytest.approx(35.1, abs=0.05)
    assert kpis["rival_lead_pct"] == pytest.approx(51.7, abs=0.05)
    assert kpis["penalties"] == 131
    assert kpis["penalties_per_jam"] == pytest.approx(131 / 151)


def test_tarjetas_con_diferencia_contra_el_resto() -> None:
    frames = agregar_match_id_a_frames(load_data())
    uno = filter_by_match(frames, ["2025-11-01 | Pacha Mamis"])
    resto = filter_by_match(frames, [m for m in sorted(set(frames.jam_table["match_id"])) if "Pacha" not in m])
    sin_resto = equipo.tarjetas_resumen(uno)
    con_resto = equipo.tarjetas_resumen(uno, resto)
    assert all(t.delta is None for t in sin_resto)
    assert all(t.delta is not None for t in con_resto)
    en_contra = next(t for t in con_resto if t.etiqueta == "Puntos en contra por jam")
    assert en_contra.valor == "2,10" and en_contra.delta_color == "inverse"
    assert en_contra.delta.startswith("-3,30")


def test_resumen_por_partido() -> None:
    resumen = equipo.resumen_por_partido(load_data())
    assert len(resumen) == 4 and resumen["jams"].sum() == 151
    assert resumen["pts_for"].sum() == 447 and resumen["pts_against"].sum() == 683
    assert resumen["penalties"].sum() == 131
    mostrado = equipo.formatear_resumen_partidos(resumen)
    assert list(mostrado.columns) == ["Rival", "Fecha", "Marcador", "Jams (n)", "Diferencia por jam", "Faltas"]
    assert "140 - 84" in mostrado["Marcador"].tolist()


def test_el_acumulado_por_tiempo_se_reinicia_en_cada_partido() -> None:
    tiempo, sin_tiempo = equipo.efectivos_por_tiempo(load_data())
    assert tiempo["match_id"].nunique() == 3
    primero = tiempo.sort_values(["match_id", "Period", "Jam"]).groupby("match_id")["inicio_min"].first()
    assert (primero < 0.01).all()  # el primer punto de cada partido está en 0 minutos
    assert tiempo.groupby("match_id")["inicio_min"].max().max() < 46  # no se acumula entre partidos
    assert (tiempo.groupby("match_id")["inicio_min"].apply(lambda s: s.is_monotonic_increasing)).all()


def test_un_partido_sin_tiempo_se_avisa_en_vez_de_omitirse() -> None:
    _, sin_tiempo = equipo.efectivos_por_tiempo(load_data())
    assert sin_tiempo == [SIN_TIEMPO]
    assert equipo.etiqueta_partido(SIN_TIEMPO) == "Rock and Roller Queens (2026-08-08)"


def test_titulo_segun_la_seleccion_de_partidos() -> None:
    opciones = ["a", "b", "c", "d"]
    assert equipo.titulo_equipo(opciones, opciones, "X") == "Estadísticas de equipo: general"
    assert equipo.titulo_equipo(["b"], opciones, "Pacha Mamis") == "Estadísticas de equipo vs Pacha Mamis"
    assert equipo.titulo_equipo(["a", "b"], opciones, None) == "Estadísticas de equipo (2 partidos)"
    assert equipo.titulo_equipo(["a", "b", "c"], opciones) == "Estadísticas de equipo (3 partidos)"


def test_frases_con_su_n_y_sin_reglas_de_muestra_corta() -> None:
    frases = equipo.frases_lo_que_mas_se_nota(load_data())
    assert len(frases) == 3 and all("n = " in f for f in frases)
    assert "35,1 %" in frases[0] and "51,7 %" in frases[0]
    assert "n = 78" in frases[1]
    assert "2.º periodo" in frases[2]
    assert equipo.frases_lo_que_mas_se_nota(_synthetic_frames(jams_per_match=4)) == []  # 8 jams < 10


def test_etiquetas_de_jugadora_con_numero_si_el_nombre_se_repite() -> None:
    nombres = mapa_nombres(load_data().player_names)
    assert etiqueta_jugadora("10", nombres) == "Medusa (#10)"
    assert etiqueta_jugadora("2", nombres) == "Medusa (#2)"
    assert etiqueta_jugadora("17", nombres) == "Arca"
    assert etiqueta_jugadora("999", nombres) == "#999"
    assert etiquetas_jugadoras(["10", "17"], nombres) == {"10": "Medusa (#10)", "17": "Arca"}


def test_las_tablas_de_faltas_usan_etiquetas_con_numero() -> None:
    frames = load_data()
    por_jugadora = equipo.faltas_por_jugadora_y_rol(frames)
    assert por_jugadora["penalties"].sum() == 131
    assert {"Jammer", "Pivot", "Bloque", "Fuera de la alineación"} >= set(por_jugadora["rol"])
    assert equipo.faltas_por_periodo(frames)["penalties"].sum() == 131
    por_partido = equipo.faltas_por_partido(frames)
    assert len(por_partido) == 4 and por_partido["penalties"].sum() == 131


def test_los_graficos_son_validos() -> None:
    frames = load_data()
    tiempo, _ = equipo.efectivos_por_tiempo(frames)
    efectividad = equipo.efectividad_jugadoras(frames)
    graficos_listos = [
        graficos.grafico_efectivos_por_jam(effective_by_jam(frames)),
        graficos.grafico_efectivos_por_tiempo(tiempo),
        graficos.grafico_faltas_por_jugadora_rol(equipo.faltas_por_jugadora_y_rol(frames)),
        graficos.grafico_faltas_barras(equipo.faltas_por_periodo(frames), "Periodo"),
        graficos.grafico_faltas_por_codigo(penalty_code_counts(frames, load_penalty_codes())),
        graficos.grafico_efectividad_jugadoras(efectividad, "eff_rel_por_jam", "Relativos", "Eje", True),
    ]
    for grafico in graficos_listos:
        assert grafico.to_dict()  # el esquema Vega-Lite es válido


def test_la_pagina_de_equipo_es_corta() -> None:
    assert len(PAGINA.read_text(encoding="utf-8").splitlines()) < 150


def test_pagina_de_equipo_titulos_y_filtro_vacio() -> None:
    at = AppTest.from_file(str(PAGINA), default_timeout=90).run()
    assert not at.exception
    assert at.title[0].value == "Estadísticas de equipo: general"
    assert [t.label for t in at.tabs] == ["Resumen", "Jams", "Faltas", "Combinaciones"]

    partidos = at.sidebar.multiselect[0]
    todos = list(partidos.options)
    partidos.set_value([todos[0]]).run()
    assert at.title[0].value.startswith("Estadísticas de equipo vs ")
    at.sidebar.multiselect[0].set_value(todos[:2]).run()
    assert at.title[0].value == "Estadísticas de equipo (2 partidos)"

    at.sidebar.multiselect[0].set_value([]).run()
    assert not at.exception
    assert len(at.sidebar.multiselect[0].value) == len(todos)  # se marcaron todos de nuevo
    assert at.title[0].value == "Estadísticas de equipo: general"
    assert any("no puede quedar vacío" in w.value for w in at.warning)


def test_la_pagina_avisa_del_partido_sin_tiempo() -> None:
    at = AppTest.from_file(str(PAGINA), default_timeout=90).run()
    assert any("Rock and Roller Queens (2026-08-08)" in w.value and "tiempo" in w.value for w in at.warning)
