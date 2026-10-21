import pandas as pd

from radical_stats.data_loader import load_data, load_penalty_codes
from radical_stats.metrics import (
    box_cost_table,
    box_state_by_jam,
    penalties_by_jam,
    penalty_code_counts,
    player_penalty_breakdown,
    player_penalty_summary,
)
from radical_stats.models import DataFrames
from radical_stats.validation import validate_penalties

FECHA = pd.Timestamp("2026-01-01").date()


def _frames(lineups: list[dict], penalties: list[dict] | None = None) -> DataFrames:
    jams = pd.DataFrame(
        [{"Date": FECHA, "Period": r["Period"], "Jam": r["Jam"], "Rival": "X", "Total_points": 0, "Lider": 0}
         for r in lineups]
    )
    pen = pd.DataFrame(
        penalties or [], columns=["Date", "Period", "Jam", "Player_number", "Penalty_code", "Rival"]
    )
    return DataFrames(
        jam_table=jams,
        lineups=pd.DataFrame(lineups),
        penalty_tracker=pen,
        player_names=pd.DataFrame({"Player_number": [], "Name": []}),
        time=pd.DataFrame(columns=["Date", "Period", "Jam", "Time", "Rival"]),
        rival_jam_table=jams.copy(),
    )


def _lineup(jam: int, **extra) -> dict:
    row = {"Date": FECHA, "Rival": "X", "Period": 1, "Jam": jam,
           "Jammer": 1, "Pivot": 2, "Block_1": 3, "Block_2": 4, "Block_3": 5}
    row.update(extra)
    return row


def test_inicio_y_fin_en_caja_no_cuenta_doble() -> None:
    # La jugadora 3 empieza y termina el jam en caja; la 4 solo termina en caja.
    frames = _frames([_lineup(1, Block_1_Start_jam_Box=1, Block_1_Finish_jam_Box=1, Block_2_Finish_jam_Box=1)])
    state = box_state_by_jam(frames).iloc[0]
    assert state["box_start"] == 1
    assert state["box_start_group"] == 1
    assert bool(state["has_box"])


def test_box_start_agrupa_dos_o_mas() -> None:
    frames = _frames([_lineup(1, Block_1_Start_jam_Box=1, Block_2_Start_jam_Box=1, Block_3_Start_jam_Box=1)])
    state = box_state_by_jam(frames).iloc[0]
    assert state["box_start"] == 3
    assert state["box_start_group"] == 2


def test_jam_sin_caja() -> None:
    state = box_state_by_jam(_frames([_lineup(1)])).iloc[0]
    assert state["box_start"] == 0 and not bool(state["has_box"])


def test_penalties_by_jam_sintetico() -> None:
    pen = [
        {"Date": FECHA, "Period": 1, "Jam": 1, "Player_number": "3", "Penalty_code": "D", "Rival": "X"},
        {"Date": FECHA, "Period": 1, "Jam": 1, "Player_number": "3", "Penalty_code": "D", "Rival": "X"},
    ]
    out = penalties_by_jam(_frames([_lineup(1), _lineup(2)], pen))
    assert out.set_index("Jam")["penalties"].to_dict() == {1: 2, 2: 0}


def test_faltas_totales_reales() -> None:
    frames = load_data()
    assert len(frames.penalty_tracker) == 131
    assert penalties_by_jam(frames)["penalties"].sum() == 131
    assert player_penalty_summary(frames)["penalties"].sum() == 131


def test_costo_de_caja_reales() -> None:
    frames = load_data()
    cost = box_cost_table(frames)
    assert cost["jams"].sum() == 151
    assert cost["jams"].tolist() == [78, 54, 19]
    assert [round(v, 2) for v in cost["points_against"]] == [3.78, 5.39, 5.11]


def test_sin_dato_para_partido_sin_time() -> None:
    frames = load_data()
    breakdown = player_penalty_breakdown(frames, "1013", "match_id")  # solo jugó el 2026-08-08
    assert breakdown["minutes_on_track"].isna().all()
    assert breakdown["penalties_per_10min"].isna().all()
    assert breakdown["penalties"].sum() == 4


def test_codigos_de_falta() -> None:
    frames = load_data()
    codes = load_penalty_codes()
    assert set(frames.penalty_tracker["Penalty_code"]) <= set(codes["code"])
    assert len(codes) == 15
    counts = penalty_code_counts(frames, codes)
    assert counts["penalties"].sum() == 131
    unknown = counts[counts["code"] == "Unknown"].iloc[0]
    assert unknown["penalties"] == 25 and unknown["nombre_es"] == "Sin código"


def test_falta_fuera_de_alineacion_se_avisa_como_posible_error() -> None:
    avisos = validate_penalties(load_data())
    assert any("#17" in a and "jam 19" in a and "posible error de digitación" in a for a in avisos)
