import numpy as np
import pandas as pd
import pytest

from radical_stats import config
from radical_stats.data_loader import load_data
from radical_stats.metrics import (
    effective_by_jam,
    player_effectiveness,
    player_effectiveness_by_match,
)
from radical_stats.models import DataFrames


def _synthetic_frames(jams_per_match: int = 20) -> DataFrames:
    """Dos partidos: A (eff +5 en todos los jams) y B (eff -5). La jugadora 9 solo juega B."""
    jam_rows, rival_rows, lineup_rows = [], [], []
    for date, rival, ours, theirs in (("2026-01-01", "A", 8, 3), ("2026-02-01", "B", 2, 7)):
        fecha = pd.Timestamp(date).date()
        for jam in range(1, jams_per_match + 1):
            base = {"Date": fecha, "Period": 1, "Jam": jam}
            flags = {"Lost": 0, "Lider": 0, "Call": 0, "No_initial_pass": 0, "Star_pass": 0}
            jam_rows.append({**base, "Rival": rival, "Jammer": 1, "Total_points": ours, **flags})
            rival_rows.append({**base, "Rival": rival, "Total_points": theirs, **flags})
            others = [9, 6, 7, 8] if rival == "B" else [2, 3, 4, 5]
            lineup_rows.append(
                {**base, "Rival": rival, "Jammer": 1, "Pivot": others[0],
                 "Block_1": others[1], "Block_2": others[2], "Block_3": others[3]}
            )
    return DataFrames(
        jam_table=pd.DataFrame(jam_rows),
        lineups=pd.DataFrame(lineup_rows),
        penalty_tracker=pd.DataFrame(columns=["Date", "Period", "Jam", "Player_number", "Penalty_code", "Rival"]),
        player_names=pd.DataFrame({"Player_number": [], "Name": []}),
        time=pd.DataFrame(columns=["Date", "Period", "Jam", "Time", "Rival"]),
        rival_jam_table=pd.DataFrame(rival_rows),
    )


def test_eff_rel_promedia_cero_por_partido_en_datos_reales() -> None:
    eff = effective_by_jam(load_data())
    assert len(eff) == 151
    assert eff.groupby("match_id")["eff_rel"].mean().abs().max() < 1e-9
    assert eff["eff"].sum() == -236


def test_jugadora_que_solo_juega_el_partido_malo() -> None:
    frames = _synthetic_frames()
    eff = effective_by_jam(frames)
    assert eff.groupby("match_id")["eff_rel"].mean().abs().max() < 1e-9

    out = player_effectiveness(frames).set_index("Player_number")
    mala = out.loc["9"]
    assert mala["jams"] == 20
    assert mala["eff_por_jam"] == pytest.approx(-5)  # muy negativo
    assert mala["eff_rel_por_jam"] == pytest.approx(0, abs=1e-9)  # pero normal para ese partido
    # La jammer juega todos los jams: no hay jams sin ella, no hay con_y_sin.
    assert np.isnan(out.loc["1", "con_y_sin"])
    # Sin ella en el partido B hay 0 jams; en A no jugó: no hay partido válido.
    assert np.isnan(mala["con_y_sin"])


def test_con_y_sin_y_ajuste_por_jammer_sinteticos() -> None:
    frames = _synthetic_frames()
    out = player_effectiveness(frames).set_index("Player_number")
    # Las jugadoras 2-5 juegan todo el partido A, que no tiene jams sin ellas.
    assert np.isnan(out.loc["2", "con_y_sin"])
    # Misma jammer en todos los jams: el ajuste equivale a centrar por partido.
    assert out.loc["9", "eff_ajustada_jammer"] == pytest.approx(0, abs=1e-9)
    assert np.isnan(out.loc["1", "eff_ajustada_jammer"])  # la jammer no tiene ajuste


def test_marca_de_muestra_baja_y_bootstrap_reproducible() -> None:
    frames = _synthetic_frames(jams_per_match=config.MIN_JAMS_JUGADORA - 1)
    out = player_effectiveness(frames)
    # La jammer juega los dos partidos (18 jams); todas las demás tienen muestra baja.
    assert out.set_index("Player_number")["muestra_baja"].drop("1").all()
    assert not out.set_index("Player_number").loc["1", "muestra_baja"]
    assert len(out) == 9  # nunca se oculta a nadie
    again = player_effectiveness(frames)
    pd.testing.assert_frame_equal(out, again)


def test_mamba_datos_reales() -> None:
    frames = load_data()
    mamba = player_effectiveness(frames).set_index("Player_number").loc["240"]
    assert mamba["jams"] == 91
    assert mamba["eff_por_jam"] == pytest.approx(-2.54, abs=0.02)
    assert mamba["eff_rel_por_jam"] == pytest.approx(-0.74, abs=0.02)
    assert not mamba["muestra_baja"]
    assert mamba["ic_bajo"] < mamba["eff_rel_por_jam"] < mamba["ic_alto"]


def test_toda_jugadora_tiene_su_n_de_jams() -> None:
    out = player_effectiveness(load_data())
    assert out["jams"].notna().all() and (out["jams"] > 0).all()
    assert out["muestra_baja"].tolist() == (out["jams"] < config.MIN_JAMS_JUGADORA).tolist()
    por_rol = player_effectiveness(load_data(), por_rol=True)
    assert por_rol["jams"].sum() == out["jams"].sum()


def test_tabla_por_partido_de_la_jugadora() -> None:
    table = player_effectiveness_by_match(load_data(), "240")
    assert table["jams"].sum() == 91
    assert table["penalties"].sum() == 9
    assert len(table) == 4
