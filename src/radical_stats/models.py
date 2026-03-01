from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class DataFrames:
    jam_table: pd.DataFrame
    lineups: pd.DataFrame
    penalty_tracker: pd.DataFrame
    player_names: pd.DataFrame
    time: pd.DataFrame
    rival_jam_table: pd.DataFrame = field(default_factory=pd.DataFrame)
