# Radical Stats

Streamlit app to analyze roller derby team and player statistics with match-level filters.

## Project structure

```text
.
├── app.py
├── pages/
│   ├── 1_Team_Statistics.py
│   └── 2_Player_Statistics.py
├── src/radical_stats/
│   ├── data_loader.py
│   ├── filters.py
│   ├── metrics.py
│   ├── models.py
│   └── ui.py
├── data/
└── requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Current pages

- Team Statistics: KPIs, points by jam, penalties by player.
- Player Statistics: player selector, role distribution, penalties per jam.

## Notes

- Match filter uses `Date` + `Rival` as match identifier.
- If new match summaries are added into current Excel sources, they will be available automatically.
