"""Parámetros de análisis en un único lugar."""

from __future__ import annotations

# Por debajo de estos mínimos de jams se marca "Muestra baja" (nunca se oculta).
MIN_JAMS_JUGADORA = 10
# Mínimo de jams por tamaño de combinación (2 dupla, 3 terna, 4 cuarteto, 5 quinteto con jammer).
MIN_JAMS_COMBINACION = {2: 8, 3: 5, 4: 3, 5: 3}
# Mínimo de jams en cada caso al comparar a una jugadora arrancando en caja contra no.
MIN_JAMS_CASO = 5

# Con y sin ella: jams mínimos sin la jugadora en un partido para usar ese partido.
MIN_JAMS_SIN_ELLA = 5
# Ajuste por jammer: jams mínimos de la jammer en el partido; si no, se usa el promedio del partido.
MIN_JAMS_JAMMER = 3

# Intervalo por bootstrap sobre los puntos efectivos relativos por jam.
BOOTSTRAP_REMUESTREOS = 1000
BOOTSTRAP_SEMILLA = 2025
BOOTSTRAP_NIVEL = 0.80
BOOTSTRAP_MIN_JAMS = 5

# Una regla de «Lo que más se nota» no se muestra con menos jams que estos.
MIN_JAMS_REGLA = 10
