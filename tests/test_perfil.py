from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from radical_stats import config
from radical_stats.data_loader import load_data
from radical_stats.lineups import lineups_long
from radical_stats.perfil import (
    PerfilJugadora,
    best_and_worst_combinations,
    comparar_con_equipo,
    formatear_tabla_rol,
    main_role_of,
    pack_combinations,
    penalty_box_cost,
    player_profile,
    players_overview,
    resumen_tres_frases,
    role_table,
    roles_con_jams,
    team_penalty_rate,
)
from test_effectiveness import _synthetic_frames

ROOT = Path(__file__).resolve().parents[1]


def _perfil(**cambios) -> PerfilJugadora:
    base = dict(
        player_number="17", jams=91, team_jams=151, matches=4, main_role="Pivot", main_role_jams=70,
        roles_jams={"Jammer": 1, "Pivot": 70, "Bloque": 20}, eff_rel=0.68, eff_ic=(-0.18, 1.58),
        penalties=21, penalties_per_jam=21 / 91, team_penalties_per_jam=0.17,
    )
    base.update(cambios)
    return PerfilJugadora(**base)


# --- Resumen en tres frases -------------------------------------------------------


def test_resumen_normal_tiene_tres_frases_descriptivas() -> None:
    frases = resumen_tres_frases(_perfil())
    assert len(frases) == 3
    assert "Pivot" in frases[0] and "70 de sus 91 jams" in frases[0] and "77 %" in frases[0]
    assert "Muestra baja" not in frases[0]
    assert "0,68" in frases[1] and "n = 91" in frases[1] and "-0,18 a 1,58" in frases[1]
    assert "0,23 faltas por jam" in frases[2] and "21 faltas en 91 jams" in frases[2]
    assert "más que el promedio del equipo (0,17)" in frases[2]


def test_resumen_muestra_baja_abre_con_el_aviso() -> None:
    perfil = _perfil(
        jams=6, main_role_jams=4, roles_jams={"Jammer": 0, "Pivot": 4, "Bloque": 2},
        eff_ic=(np.nan, np.nan), penalties=0, penalties_per_jam=0.0,
    )
    frases = resumen_tres_frases(perfil)
    assert frases[0].startswith("Muestra baja: menos de 10 jams")
    assert "n = 6" in frases[0] and "Pivot" in frases[0]
    assert "n = 6 jams" in frases[1] and "intervalo" not in frases[1]
    assert "menos que el promedio del equipo" in frases[2]


def test_resumen_con_rol_unico() -> None:
    normal = resumen_tres_frases(
        _perfil(main_role="Bloque", main_role_jams=87, jams=87, roles_jams={"Jammer": 0, "Pivot": 0, "Bloque": 87})
    )
    assert normal[0] == "Jugó solo como Bloque (87 jams)."
    baja = resumen_tres_frases(
        _perfil(main_role="Bloque", main_role_jams=3, jams=3, roles_jams={"Jammer": 0, "Pivot": 0, "Bloque": 3})
    )
    assert baja[0] == "Muestra baja: menos de 10 jams (n = 3). Jugó solo como Bloque."


def test_resumen_sin_dato_de_efectivos_y_faltas_iguales() -> None:
    frases = resumen_tres_frases(
        _perfil(eff_rel=np.nan, penalties_per_jam=0.17, penalties=15, team_penalties_per_jam=0.17)
    )
    assert "No hay datos de puntos efectivos" in frases[1] and "n = 91" in frases[1]
    assert "igual que el promedio del equipo" in frases[2]


def test_el_umbral_de_muestra_baja_viene_de_config() -> None:
    assert _perfil(jams=config.MIN_JAMS_JUGADORA).low_sample is False
    assert _perfil(jams=config.MIN_JAMS_JUGADORA - 1).low_sample is True


# --- Comparaciones contra el equipo -------------------------------------------------


def test_comparar_con_equipo() -> None:
    dif, sentido = comparar_con_equipo(0.23, 0.17)
    assert dif == pytest.approx(0.06) and sentido == "mas"
    dif, sentido = comparar_con_equipo(0.10, 0.17)
    assert dif == pytest.approx(-0.07) and sentido == "menos"
    assert comparar_con_equipo(0.171, 0.17)[1] == "igual"
    assert comparar_con_equipo(np.nan, 0.17)[1] == "sin_dato"


def test_faltas_del_equipo_son_faltas_entre_jams_jugadora() -> None:
    frames = load_data()
    assert team_penalty_rate(frames) == pytest.approx(131 / len(lineups_long(frames.lineups)))
    profile = player_profile(frames, "17")
    assert profile.penalties == 21 and profile.jams == 91
    assert profile.penalties_diff == pytest.approx(21 / 91 - team_penalty_rate(frames))


def test_tabla_de_rol_compara_contra_el_equipo() -> None:
    frames = load_data()
    table = role_table(frames, "16", "Jammer").set_index("metrica")
    assert table.loc["jams", "valor"] == 61
    assert (table["n"] == 61).all()  # cada cifra con su n
    assert table.loc["puntos_por_jam", "diferencia"] == pytest.approx(
        table.loc["puntos_por_jam", "valor"] - table.loc["puntos_por_jam", "equipo"]
    )
    assert table.loc["lead_pct", "equipo"] == pytest.approx(35.1, abs=0.05)
    shown = formatear_tabla_rol(role_table(frames, "16", "Jammer"))
    assert "35,1 %" in shown["Promedio del equipo"].tolist()


# --- Pestañas por rol ---------------------------------------------------------------


def test_rol_sin_jams_no_tiene_pestana_ni_tabla() -> None:
    frames = load_data()
    assert roles_con_jams(frames, "913") == ["Pivot", "Bloque"]  # nunca fue jammer
    assert roles_con_jams(frames, "17") == ["Jammer", "Pivot", "Bloque"]
    assert roles_con_jams(frames, "10") == ["Bloque"]
    assert role_table(frames, "913", "Jammer").empty


def test_roles_en_datos_sinteticos() -> None:
    frames = _synthetic_frames()
    assert roles_con_jams(frames, "9") == ["Pivot"]
    assert roles_con_jams(frames, "1") == ["Jammer"]
    assert main_role_of({"Jammer": 0, "Pivot": 0, "Bloque": 0}) == (None, 0)
    assert main_role_of({"Jammer": 3, "Pivot": 3, "Bloque": 1}) == ("Jammer", 3)


@pytest.mark.parametrize("jugadora", ["17", "16", "913", "10"])
def test_la_pagina_muestra_solo_las_pestanas_con_jams(jugadora: str) -> None:
    frames = load_data()
    esperadas = {
        "17": ["Como jammer", "Como pivot", "Como bloque"],
        "16": ["Como jammer", "Como pivot", "Como bloque"],
        "913": ["Como pivot", "Como bloque"],
        "10": ["Como bloque"],
    }[jugadora]
    nombre = frames.player_names.set_index("Player_number")["Name"]
    # 10 es el segundo «Medusa»: el selector siempre trae nombre y número.
    etiqueta = f"{nombre.loc[jugadora]} (#{jugadora})"
    at = AppTest.from_file(str(ROOT / "pages/2_Estadisticas_de_Jugadoras.py"), default_timeout=90).run()
    at.selectbox[0].select(etiqueta).run()
    assert not at.exception
    etiquetas = [t.label for t in at.tabs]
    assert etiquetas == esperadas + ["Faltas", "Por partido", "Con quién rinde"]


# --- Costo de las faltas y combinaciones --------------------------------------------


def test_costo_de_faltas_exige_minimo_de_jams_en_cada_caso() -> None:
    frames = _synthetic_frames()
    cost = penalty_box_cost(frames, "9")
    assert cost["n_con_caja"] == 0 and cost["n_sin_caja"] == 20
    assert cost["valido"] is False
    assert np.isnan(cost["con_caja"])


def test_combinaciones_del_pack_con_minimo_de_jams() -> None:
    frames = _synthetic_frames()
    combos = pack_combinations(frames, "9")
    assert set(combos["size"]) == {2, 3}
    minimos = combos["size"].map(config.MIN_JAMS_COMBINACION)
    assert (combos["jams"] >= minimos).all()
    assert all("9" in c for c in combos["players"])
    best, worst = best_and_worst_combinations(combos, 2)
    assert len(best) == 3 and len(worst) == 0  # solo 3 duplas: no se repiten en «peores»

    corto = _synthetic_frames(jams_per_match=config.MIN_JAMS_COMBINACION[3] - 1)
    assert pack_combinations(corto, "9").empty


def test_tabla_de_todas_las_jugadoras() -> None:
    frames = load_data()
    overview = players_overview(frames).set_index("Player_number")
    assert (overview["jams"] <= len(frames.lineups)).all()
    assert overview.loc["10", "muestra"] == "Baja" and overview.loc["10", "jams"] == 3
    assert overview.loc["17", "muestra"] == "Ok" and overview.loc["17", "main_role"] == "Pivot"
    assert (overview["muestra"] == "Baja").tolist() == (overview["jams"] < config.MIN_JAMS_JUGADORA).tolist()
