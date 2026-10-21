"""Etiquetas de jugadora comunes a gráficos y tablas.

Hay nombres repetidos (dos «Medusa», #2 y #10): el nombre solo no identifica a la jugadora.
"""

from __future__ import annotations

import pandas as pd


def mapa_nombres(player_names: pd.DataFrame) -> dict[str, str]:
    """Número de jugadora (texto) -> nombre, a partir de la tabla Player_names."""
    if player_names.empty:
        return {}
    numeros = player_names["Player_number"].astype(str).str.strip()
    return dict(zip(numeros, player_names["Name"]))


def nombres_repetidos(nombres: dict[str, str]) -> set[str]:
    """Nombres que pertenecen a más de una jugadora."""
    cuenta = pd.Series(list(nombres.values()), dtype="object").value_counts()
    return set(cuenta[cuenta > 1].index)


def etiqueta_jugadora(numero: str, nombres: dict[str, str], repetidos: set[str] | None = None) -> str:
    """Nombre de la jugadora; nombre y número si el nombre se repite; «#número» si no hay nombre."""
    numero = str(numero).strip()
    nombre = nombres.get(numero)
    if nombre is None:
        return f"#{numero}"
    repetidos = nombres_repetidos(nombres) if repetidos is None else repetidos
    return f"{nombre} (#{numero})" if nombre in repetidos else nombre


def etiquetas_jugadoras(numeros: list[str], nombres: dict[str, str]) -> dict[str, str]:
    """Etiqueta de cada número de la lista (calcula los nombres repetidos una sola vez)."""
    repetidos = nombres_repetidos(nombres)
    return {n: etiqueta_jugadora(n, nombres, repetidos) for n in numeros}
