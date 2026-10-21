import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from radical_stats import data_loader, validation
from radical_stats.data_loader import load_data
from radical_stats.models import DataFrames
from radical_stats.partidos import (
    agregar_match_id,
    crear_match_id,
    opciones_de_partidos,
    partidos_con_claves_repetidas,
    partir_match_id,
)
from test_effectiveness import _synthetic_frames

ROOT = Path(__file__).resolve().parents[1]
FECHA_A = pd.Timestamp("2026-01-01").date()
PEN_COLUMNS = ["Date", "Period", "Jam", "Player_number", "Penalty_code", "Rival"]


def _con(frames: DataFrames, **cambios) -> DataFrames:
    """Copia de frames con las tablas indicadas reemplazadas."""
    datos = {
        "jam_table": frames.jam_table, "lineups": frames.lineups, "penalty_tracker": frames.penalty_tracker,
        "player_names": frames.player_names, "time": frames.time, "rival_jam_table": frames.rival_jam_table,
    }
    datos.update(cambios)
    return DataFrames(**datos)


def _penalizacion(jugadora: str, codigo: str = "D", jam: int = 1) -> dict:
    return {"Date": FECHA_A, "Period": 1, "Jam": jam, "Player_number": jugadora, "Penalty_code": codigo, "Rival": "A"}


# --- match_id --------------------------------------------------------------------------


def test_match_id_se_crea_en_un_solo_lugar() -> None:
    df = pd.DataFrame({"Date": [FECHA_A], "Rival": ["A"]})
    assert crear_match_id(df).tolist() == ["2026-01-01 | A"]
    assert agregar_match_id(df)["match_id"].tolist() == ["2026-01-01 | A"]
    assert partir_match_id("2026-01-01 | A") == ("2026-01-01", "A")
    assert partir_match_id("sin separador") == ("sin separador", "")
    ya_tiene = agregar_match_id(df)
    assert agregar_match_id(ya_tiene) is ya_tiene


def test_opciones_de_partidos_reales() -> None:
    assert opciones_de_partidos(load_data()) == [
        "2025-11-01 | Pacha Mamis",
        "2025-11-02 | Violet Attack",
        "2025-11-03 | Fuego Latino",
        "2026-08-08 | Rock and Roller Queens",
    ]


def test_dos_partidos_con_la_misma_fecha_y_rival_se_avisan_en_vez_de_mezclarse() -> None:
    frames = _synthetic_frames()
    assert partidos_con_claves_repetidas(frames) == []
    assert validation.validate_partidos_repetidos(frames) == []
    repetido = pd.concat([frames.jam_table, frames.jam_table[frames.jam_table["Rival"] == "A"]], ignore_index=True)
    mezclado = _con(frames, jam_table=repetido)
    assert partidos_con_claves_repetidas(mezclado) == ["2026-01-01 | A"]
    avisos = validation.validate_partidos_repetidos(mezclado)
    assert len(avisos) == 1 and "2026-01-01 | A" in avisos[0] and "misma fecha y rival" in avisos[0]


# --- Chequeos sintéticos -----------------------------------------------------------------------


def test_chequeo_jams_por_partido() -> None:
    frames = _synthetic_frames()
    assert validation.chequeo_jams_por_partido(frames).cantidad == 0
    sin_uno = frames.rival_jam_table.iloc[1:]
    chequeo = validation.chequeo_jams_por_partido(_con(frames, rival_jam_table=sin_uno))
    assert chequeo.cantidad == 1 and chequeo.estado == "Aviso"
    fila = chequeo.filas.iloc[0]
    assert fila["jam_table"] == 20 and fila["rival"] == 19 and fila["lineups"] == 20
    assert chequeo.detalle["jams"].tolist() == [20, 20]


def test_chequeo_claves_duplicadas_en_cada_tabla() -> None:
    frames = _synthetic_frames()
    assert validation.chequeo_claves_duplicadas(frames).cantidad == 0
    for tabla, nombre in (("jam_table", "Tabla de jams"), ("rival_jam_table", "Tabla de jams del rival"),
                          ("lineups", "Alineaciones")):
        original = getattr(frames, tabla)
        duplicada = pd.concat([original, original.iloc[[0]]], ignore_index=True)
        chequeo = validation.chequeo_claves_duplicadas(_con(frames, **{tabla: duplicada}))
        assert chequeo.cantidad == 2 and set(chequeo.filas["Tabla"]) == {nombre}
    tiempos = pd.DataFrame({"Date": [FECHA_A] * 2, "Period": [1, 1], "Jam": [1, 1], "Time": [30, 31], "Rival": ["A", "A"]})
    assert validation.chequeo_claves_duplicadas(_con(frames, time=tiempos)).filas["Tabla"].tolist() == ["Tiempos"] * 2


def test_chequeo_partidos_sin_time() -> None:
    frames = _synthetic_frames()
    assert validation.chequeo_partidos_sin_time(frames).cantidad == 2
    tiempos = pd.DataFrame({"Date": [FECHA_A], "Period": [1], "Jam": [1], "Time": [30], "Rival": ["A"]})
    chequeo = validation.chequeo_partidos_sin_time(_con(frames, time=tiempos))
    assert chequeo.cantidad == 1 and chequeo.filas["Rival"].tolist() == ["B"]


def test_chequeo_nombres_sin_nombre_y_repetidos() -> None:
    frames = _synthetic_frames()
    nombres = pd.DataFrame({"Player_number": ["1", "2", "3", "4", "5", "6", "7", "8"],
                            "Name": ["Ana", "Medusa", "Medusa", "Eva", "Fe", "Gus", "Hi", "Ix"]})
    chequeo = validation.chequeo_nombres(_con(frames, player_names=nombres))
    problemas = dict(zip(chequeo.filas["Player_number"], chequeo.filas["Problema"]))
    assert problemas == {"2": "Nombre repetido", "3": "Nombre repetido", "9": "Sin nombre"}  # la 9 juega y no tiene nombre
    todos = pd.DataFrame({"Player_number": list("123456789"), "Name": list("abcdefghi")})
    assert validation.chequeo_nombres(_con(frames, player_names=todos)).cantidad == 0


def test_chequeo_valores_faltantes_en_lineups() -> None:
    frames = _synthetic_frames()
    assert validation.chequeo_valores_faltantes(frames).cantidad == 0
    lineups = frames.lineups.astype({"Pivot": object, "Block_1": object, "Block_2": object}).copy()
    lineups.loc[0, "Pivot"] = "?"
    lineups.loc[1, "Block_1"] = ""
    lineups.loc[2, "Block_2"] = np.nan
    lineups.loc[2, "Pivot"] = "?"  # una fila con dos valores faltantes cuenta una vez
    chequeo = validation.chequeo_valores_faltantes(_con(frames, lineups=lineups))
    assert chequeo.cantidad == 3


def test_chequeo_faltas_unknown() -> None:
    frames = _synthetic_frames()
    pen = pd.DataFrame([_penalizacion("3", "Unknown"), _penalizacion("4", "unknown"),
                        _penalizacion("5", "D"), _penalizacion("6", "")], columns=PEN_COLUMNS)
    assert validation.chequeo_faltas_unknown(_con(frames, penalty_tracker=pen)).cantidad == 3
    assert validation.chequeo_faltas_unknown(frames).cantidad == 0


def test_chequeo_faltas_fuera_de_pista() -> None:
    frames = _synthetic_frames()
    pen = pd.DataFrame([_penalizacion("3"), _penalizacion("99")], columns=PEN_COLUMNS)  # 3 juega; 99 no
    chequeo = validation.chequeo_faltas_fuera_de_pista(_con(frames, penalty_tracker=pen))
    assert chequeo.cantidad == 1 and chequeo.filas["Player_number"].tolist() == ["99"]
    assert len(validation.validate_penalties(_con(frames, penalty_tracker=pen))) == 1


def test_chequeo_jammer_distinta() -> None:
    frames = _synthetic_frames()
    assert validation.chequeo_jammer(frames).cantidad == 0
    lineups = frames.lineups.copy()
    lineups.loc[:2, "Jammer"] = 77
    chequeo = validation.chequeo_jammer(_con(frames, lineups=lineups))
    assert chequeo.cantidad == 3 and set(chequeo.filas["Jammer_lineups"]) == {"77"}
    assert len(validation.validate_jammers(_con(frames, lineups=lineups))) == 3


def test_chequeos_vacios_no_fallan() -> None:
    vacia = pd.DataFrame(columns=["Date", "Period", "Jam", "Rival"])
    frames = DataFrames(jam_table=vacia, lineups=vacia, penalty_tracker=vacia,
                        player_names=pd.DataFrame({"Player_number": [], "Name": []}),
                        time=vacia, rival_jam_table=vacia)
    chequeos = validation.chequeos_calidad(frames)
    assert [c.cantidad for c in chequeos] == [0] * 8


# --- Datos reales -----------------------------------------------------------------------


def test_datos_reales_totales() -> None:
    frames = load_data()
    assert len(frames.jam_table) == 151 and len(frames.rival_jam_table) == 151 and len(frames.lineups) == 151
    assert len(opciones_de_partidos(frames)) == 4
    assert validation.jams_por_partido_total(frames)["jams"].tolist() == [40, 45, 38, 28]
    assert len(frames.penalty_tracker) == 131
    nombres = frames.player_names
    assert len(nombres) == 18 and nombres["Name"].notna().all() and (nombres["Name"].str.strip() != "").all()


def test_chequeos_reales_devuelven_el_conteo_de_hoy() -> None:
    chequeos = {c.clave: c for c in validation.chequeos_calidad(load_data())}
    assert list(chequeos) == ["jams_por_partido", "claves_duplicadas", "partidos_sin_time", "nombres",
                              "valores_faltantes", "faltas_unknown", "faltas_fuera_de_pista", "jammer"]
    esperado = {"jams_por_partido": 0, "claves_duplicadas": 0, "partidos_sin_time": 1, "nombres": 2,
                "valores_faltantes": 1, "faltas_unknown": 25, "faltas_fuera_de_pista": 1, "jammer": 0}
    assert {k: c.cantidad for k, c in chequeos.items()} == esperado
    assert {k: c.estado for k, c in chequeos.items()}["jammer"] == "OK"

    assert chequeos["partidos_sin_time"].filas["Rival"].tolist() == ["Rock and Roller Queens"]
    assert sorted(chequeos["nombres"].filas["Player_number"]) == ["10", "2"]
    assert set(chequeos["nombres"].filas["Name"]) == {"Medusa"}
    falta = chequeos["valores_faltantes"].filas.iloc[0]
    assert (str(falta["Date"]), falta["Period"], falta["Jam"]) == ("2026-08-08", 2, 12)
    fuera = chequeos["faltas_fuera_de_pista"].filas.iloc[0]
    assert (str(fuera["Date"]), fuera["Period"], fuera["Jam"], fuera["Player_number"]) == ("2025-11-02", 1, 19, "17")


# --- Página de calidad de datos -------------------------------------------------------------


def test_la_pagina_de_calidad_muestra_los_avisos_de_hoy() -> None:
    at = AppTest.from_file(str(ROOT / "pages/4_Calidad_de_Datos.py"), default_timeout=90).run()
    assert not at.exception
    assert any("5 de 8 chequeos tienen avisos" in w.value for w in at.warning)
    tarjetas = {}
    for m in at.markdown:
        titulo, separador, resto = m.value.partition("** :")
        if separador and titulo.startswith("**"):
            tarjetas[titulo[2:]] = resto
    assert len(tarjetas) == 8
    esperado = {
        "Jams por partido y periodo": ("OK", 0),
        "Claves (fecha, periodo, jam) duplicadas": ("OK", 0),
        "Partidos sin tiempos": ("Aviso", 1),
        "Nombres de jugadoras": ("Aviso", 2),
        "Valores «?» o vacíos en las alineaciones": ("Aviso", 1),
        "Faltas sin código": ("Aviso", 25),
        "Faltas de una jugadora que no estaba en pista": ("Aviso", 1),
        "Jammer distinta entre alineaciones y jams": ("OK", 0),
    }
    for titulo, (estado, cantidad) in esperado.items():
        assert f"**{estado}**] · Filas afectadas: {cantidad}" in tarjetas[titulo], titulo


# --- Caché según la fecha de modificación -------------------------------------------------


def test_la_firma_cambia_cuando_cambia_un_archivo(tmp_path: Path) -> None:
    (tmp_path / "a.xlsx").write_bytes(b"1")
    (tmp_path / "b.csv").write_bytes(b"2")
    (tmp_path / "ignorado.txt").write_bytes(b"3")
    firma = data_loader.firma_datos(tmp_path)
    assert [f[0] for f in firma] == ["a.xlsx", "b.csv"]
    assert data_loader.firma_datos(tmp_path) == firma
    nuevo = (tmp_path / "a.xlsx").stat().st_mtime + 5
    os.utime(tmp_path / "a.xlsx", (nuevo, nuevo))
    assert data_loader.firma_datos(tmp_path) != firma


def test_un_excel_actualizado_se_recarga_sin_reiniciar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for archivo in data_loader.DATA_DIR.glob("*.*"):
        if archivo.is_file():
            shutil.copy(archivo, tmp_path / archivo.name)
    monkeypatch.setattr(data_loader, "DATA_DIR", tmp_path)
    assert len(data_loader.load_data().jam_table) == 151
    assert len(data_loader.load_data().jam_table) == 151  # segunda lectura: viene de la caché

    ruta = tmp_path / "Jam_table.xlsx"
    pd.read_excel(ruta).iloc[:-1].to_excel(ruta, index=False)
    nuevo = ruta.stat().st_mtime + 5
    os.utime(ruta, (nuevo, nuevo))
    assert len(data_loader.load_data().jam_table) == 150  # se recargó sin limpiar la caché
