"""Única fuente de textos visibles de la interfaz (español de Colombia).

Los nombres internos de columnas de los DataFrames y de los archivos Excel
siguen en inglés; aquí solo viven los textos que ve la persona usuaria.
"""

from __future__ import annotations

import math

# --- Aplicación y navegación -------------------------------------------------
NOMBRE_APP = "Radical Stats"
TITULO_APP = "Panel de estadísticas de Radical Stats"
SUBTITULO_APP = (
    "Analiza el rendimiento del equipo y de las jugadoras. "
    "Usa el menú lateral para cambiar de página."
)
PAGINA_INICIO = "Inicio"
PAGINA_EQUIPO = "Estadísticas de equipo"
PAGINA_JUGADORAS = "Estadísticas de jugadoras"
INICIO_VISTAS = (
    "### Vistas disponibles\n"
    "- **Estadísticas de equipo**: métricas del equipo por partido y acumuladas.\n"
    "- **Estadísticas de jugadoras**: detalle de cada jugadora seleccionada.\n"
    "- **Alineaciones**: duplas, ternas, cuartetos y quintetos.\n"
    "- **Calidad de datos**: chequeos de los Excel antes de mirar los gráficos.\n\n"
    "Fuente de datos: resúmenes en Excel dentro de `data/`."
)

# --- Filtros globales --------------------------------------------------------
FILTROS = "Filtros"
FILTRO_PARTIDO = "Partido"
AYUDA_FILTRO_PARTIDO = "Filtra las estadísticas por uno o más partidos."
PLACEHOLDER_MULTISELECCION = "Elige una o más opciones"
PLACEHOLDER_SELECCION = "Elige una opción"
SIN_DATOS_FILTROS = "No hay datos para los filtros seleccionados."

# --- Glosario ----------------------------------------------------------------
PARTIDO = "Partido"
FECHA = "Fecha"
PERIODO = "Periodo"
JAM = "Jam"
ALINEACION = "Alineación"
PACK = "Pack"
JUGADORA = "Jugadora"
EQUIPO = "Equipo"
RIVAL = "Rival"
FALTAS = "Faltas"
CAJA = "Caja"
LEAD = "Lead"
LEAD_PERDIDO = "Lead perdido"
CALL_OFF = "Call-off"
SIN_PASE_INICIAL = "Sin pase inicial"
STAR_PASS = "Star pass"
LESION = "Lesión"
PUNTOS_A_FAVOR = "Puntos a favor"
PUNTOS_EN_CONTRA = "Puntos en contra"
PUNTOS_EFECTIVOS = "Puntos efectivos"
PUNTOS_TOTALES = "Puntos totales"
DEFINICION_PUNTOS_EFECTIVOS = (
    "Puntos efectivos = puntos a favor menos puntos en contra."
)

# Roles (clave interna de lineups.ROLES -> texto visible).
ROLES = {"Jammer": "Jammer", "Pivot": "Pivot", "Bloque": "Bloque"}

# Columnas de las tablas de jams mostradas a la persona usuaria.
COLUMNAS_TABLA_JAMS = {
    "Date": FECHA,
    "Period": PERIODO,
    "Jam": JAM,
    "Jammer": "Jammer",
    "Lost": LEAD_PERDIDO,
    "Lider": LEAD,
    "Call": CALL_OFF,
    "Injury": LESION,
    "No_initial_pass": SIN_PASE_INICIAL,
    "Total_points": PUNTOS_TOTALES,
    "Star_pass": STAR_PASS,
    "Rival": RIVAL,
    "Team": EQUIPO,
    "match_id": PARTIDO,
}

# --- Estadísticas de equipo --------------------------------------------------
EQUIPO_TITULO = "Estadísticas de equipo"
INFORMACION_GENERAL = "Información general"
FILTRO_PERIODO = "Filtro de periodo"
AYUDA_FILTRO_PERIODO = "Filtra las métricas y los gráficos por periodo."

KPI_JAMS_TOTALES = "Jams totales"
KPI_PUNTOS_TOTALES = PUNTOS_TOTALES
KPI_PROMEDIO_PUNTOS = "Promedio de puntos por jam"
KPI_LEAD = "Jams con Lead"
KPI_CALL_OFF = "Jams con Call-off"
KPI_SIN_PASE_INICIAL = "Jams sin pase inicial"
KPI_FALTAS_TOTALES = "Faltas totales"
KPI_NUMERO_JUGADORAS = "Número de jugadoras"

TITULO_PUNTOS_POR_JAM = "Puntos por jam"
TITULO_FALTAS_POR_JUGADORA = "Faltas por jugadora"
TITULO_PUNTOS_EFECTIVOS_POR_JAM = "Puntos efectivos por jam"
TITULO_PUNTOS_EFECTIVOS_POR_TIEMPO = "Puntos efectivos por tiempo"
TITULO_PUNTOS_EFECTIVOS_JUGADORA = "Puntos efectivos por jam por jugadora"
TITULO_RESUMEN_ALINEACIONES = "Resumen de alineaciones"
GENERAL = "General"

EJE_JAM = JAM
EJE_PUNTOS = "Puntos"
EJE_JUGADORA = JUGADORA
EJE_FALTAS = FALTAS
EJE_PUNTOS_EFECTIVOS = PUNTOS_EFECTIVOS
EJE_TIEMPO_TRANSCURRIDO = "Tiempo transcurrido (minutos)"
TOOLTIP_MINUTOS = "Minutos transcurridos"
EJE_VALOR = "Valor"
EJE_ALINEACION = ALINEACION
TOOLTIP_METRICA = "Métrica"
TOOLTIP_VALOR = "Valor"

# Prefijos para las etiquetas del eje de jams, p. ej. "J12-P2".
PREFIJO_JAM = "J"
PREFIJO_PERIODO = "-P"

SIN_PUNTOS_POR_JAM = "No hay datos de puntos por jam para el periodo seleccionado."
SIN_FALTAS = "No hay datos de faltas para el periodo seleccionado."
FALTAN_JAMS_RIVAL = (
    "Faltan los datos de jams del rival. Agrégalos en `Rival_Jam_table.xlsx`."
)
SIN_PUNTOS_EFECTIVOS = "No hay datos de puntos efectivos para los filtros seleccionados."
SIN_TIEMPOS = "No hay datos de tiempo para los filtros seleccionados."
SIN_PUNTOS_EFECTIVOS_POR_TIEMPO = (
    "No hay datos de puntos efectivos por tiempo para los filtros seleccionados."
)
SIN_ALINEACIONES = "No hay datos de alineaciones para los filtros seleccionados."
SIN_PUNTOS_EFECTIVOS_JUGADORA = (
    "No hay datos de puntos efectivos por jugadora para los filtros seleccionados."
)
SIN_COMBINACIONES = (
    "No se encontraron combinaciones de alineación válidas para los filtros seleccionados."
)

ORDENAR_ALINEACIONES = "Ordenar alineaciones por"
ORDEN_JAMS_JUGADOS = "Jams jugados"
ORDEN_PUNTOS_EFECTIVOS = "Puntos efectivos totales"
METRICA_JAMS_JUGADOS = "Jams jugados"
METRICA_PUNTOS_EFECTIVOS = PUNTOS_EFECTIVOS

# Efectividad por jugadora
NOTA_ACUMULADO = (
    "El acumulado depende de los minutos jugados y del rival; "
    "por eso usamos puntos por jam relativos al partido."
)
SELECTOR_METRICA_EFECTIVIDAD = "Métrica"
MUESTRA_BAJA = "Muestra baja"
METRICA_RELATIVOS = "Relativos al partido"
METRICA_POR_JAM = "Por jam"
METRICA_CON_Y_SIN = "Con y sin ella"
METRICA_AJUSTADOS_JAMMER = "Ajustados por jammer"
# etiqueta -> (columna, frase de ayuda, título del eje, ¿lleva barra de error?)
METRICAS_EFECTIVIDAD = {
    METRICA_RELATIVOS: (
        "eff_rel_por_jam",
        "Puntos efectivos por jam menos el promedio de su partido: quita el efecto de enfrentar "
        "a un rival fuerte o débil. La barra de error es el intervalo del 80 % (bootstrap de sus jams).",
        "Puntos efectivos por jam, relativos al partido",
        True,
    ),
    METRICA_POR_JAM: (
        "eff_por_jam",
        "Promedio simple de puntos efectivos por jam; no corrige por el rival ni por el partido.",
        "Puntos efectivos por jam",
        False,
    ),
    METRICA_CON_Y_SIN: (
        "con_y_sin",
        "Puntos efectivos por jam con ella en pista menos sin ella, calculado dentro de cada "
        "partido (con al menos 5 jams sin ella) y promediado según sus jams.",
        "Diferencia de puntos efectivos por jam (con menos sin ella)",
        False,
    ),
    METRICA_AJUSTADOS_JAMMER: (
        "eff_ajustada_jammer",
        "Solo Pivot y Bloque: puntos efectivos del jam menos el promedio de los jams del mismo "
        "partido con la misma jammer, para no heredar los puntos de la jammer con la que patina.",
        "Puntos efectivos por jam, ajustados por jammer",
        False,
    ),
}
ETIQUETA_N_JAMS = "n = {n}"
LEYENDA_MUESTRA_BAJA = "En gris: muestra baja (menos de {minimo} jams). Siempre se muestra el n de jams."
JUGADORAS_SIN_DATO_METRICA = (
    "{k} jugadora(s) no tienen dato para esta métrica (sin dato); aparecen en la tabla."
)
TOOLTIP_JAMS_N = "Jams (n)"
TOOLTIP_INTERVALO = "Intervalo del 80 %"
TOOLTIP_MUESTRA = "Muestra"
TABLA_EFECTIVIDAD = "Detalle por jugadora"
COLUMNAS_EFECTIVIDAD = {
    "label": JUGADORA,
    "jams": "Jams (n)",
    "eff_por_jam": "Puntos efectivos por jam",
    "eff_rel_por_jam": "Efectivos relativos al partido",
    "pts_for_por_jam": "Puntos a favor por jam",
    "pts_against_por_jam": "Puntos en contra por jam",
    "pts_for_rel_por_jam": "A favor relativos al partido",
    "pts_against_rel_por_jam": "En contra relativos al partido",
    "con_y_sin": "Con y sin ella",
    "eff_ajustada_jammer": "Ajustados por jammer",
    "intervalo": "Intervalo del 80 %",
    "muestra": "Muestra",
}
EFECTIVIDAD_POR_PARTIDO = "Puntos efectivos por partido"
COLUMNAS_EFECTIVIDAD_PARTIDO = {
    "match_id": PARTIDO,
    "jams": "Jams (n)",
    "eff_por_jam": "Puntos efectivos por jam",
    "eff_rel_por_jam": "Efectivos relativos al partido",
    "penalties": FALTAS,
    "muestra": "Muestra",
}
SIN_EFECTIVIDAD = "No hay datos de puntos efectivos por jugadora para los filtros seleccionados."

# Costo de la caja
TITULO_COSTO_CAJA = "Costo de la caja"
DEFINICION_CAJA = (
    "Jugadoras en caja al inicio del jam = número de jugadoras nuestras que empiezan el jam "
    "en la caja (se agrupa en 0, 1 y 2 o más)."
)
NOTA_COSTO_CAJA = (
    "n es el número de jams de cada grupo. Los promedios no están ajustados por partido "
    "ni por jammer; con pocos jams por grupo, interprétalos con cautela."
)
SIN_COSTO_CAJA = "No hay datos suficientes para calcular el costo de la caja."
CAJA_GRUPOS = {0: "0", 1: "1", 2: "2 o más"}
COLUMNAS_COSTO_CAJA = {
    "box_start_group": "Jugadoras en caja al inicio del jam",
    "jams": "Jams (n)",
    "points_for": "Puntos a favor por jam",
    "points_against": "Puntos en contra por jam",
    "effective": "Puntos efectivos por jam",
    "rival_lead_pct": "% de Lead rival",
}

# Faltas por código
TITULO_FALTAS_POR_CODIGO = "Faltas por código"
SIN_CODIGO = "Sin código"
EJE_CODIGO = "Código"
TOOLTIP_CODIGO = "Código"
TOOLTIP_DESCRIPCION = "Descripción"
TOOLTIP_PORCENTAJE_FALTAS = "% de las faltas"
NOTA_SIN_CODIGO = (
    "{n} de {total} faltas ({pct}) no tienen código registrado y aparecen como "
    "«Sin código». Las descripciones vacías están pendientes de confirmar por el cuerpo técnico."
)
SIN_FALTAS_CODIGO = "No hay faltas para los filtros seleccionados."

# Tabla de alineaciones
COLUMNAS_TABLA_ALINEACIONES = {
    "Lineup": ALINEACION,
    "jams_played": "Jams jugados",
    "effective_points": PUNTOS_EFECTIVOS,
    "penalties": FALTAS,
    "penalties_per_jam": "Faltas por jam",
    "muestra": "Muestra",
}
NOTA_FALTAS_ALINEACION = (
    "Faltas = faltas del equipo en los jams de esa alineación; faltas por jam = faltas / jams jugados."
)

TOOLTIP_PUNTOS_NUESTROS = PUNTOS_A_FAVOR
TOOLTIP_PUNTOS_RIVAL = PUNTOS_EN_CONTRA
EXPANDER_DATOS_EQUIPO = "Ver datos filtrados del equipo"

# --- Estadísticas de jugadoras -----------------------------------------------
JUGADORAS_TITULO = "Estadísticas de jugadoras"
SELECCIONAR_JUGADORA = "Selecciona una jugadora"
METRICA_JAMS_JUGADOS_JUGADORA = "Jams jugados"
METRICA_JAMS_COMO_JAMMER = "Jams como Jammer"
METRICA_FALTAS = FALTAS
METRICA_FALTAS_POR_JAM = "Faltas por jam"
METRICA_FALTAS_POR_10MIN = "Faltas por 10 min en pista"
SIN_DATO = "sin dato"
NO_APLICA = "—"
SIN_ROL = "Fuera de la alineación"
FALTAS_DE_LA_JUGADORA = "Faltas de la jugadora"
FALTAS_POR_ROL = "Faltas por rol"
FALTAS_POR_PERIODO = "Faltas por periodo"
FALTAS_POR_PARTIDO = "Faltas por partido"
NOTA_MINUTOS_EN_PISTA = (
    "Los minutos en pista suman la duración de los jams jugados según la tabla de tiempos; "
    "las faltas por 10 minutos solo usan jams con tiempo. Un partido sin tiempos aparece como «sin dato». "
    "El rol de una falta es el que tenía la jugadora en el jam en que ocurrió."
)
COLUMNAS_DESGLOSE_FALTAS = {
    "key": "Grupo",
    "jams": "Jams jugados",
    "penalties": FALTAS,
    "penalties_per_jam": "Faltas por jam",
    "minutes_on_track": "Minutos en pista",
    "penalties_per_10min": "Faltas por 10 min en pista",
}
DISTRIBUCION_ROLES = "Distribución de roles"
JAMS_POR_ROL = "Jams por rol"
PORCENTAJE_JAMS_POR_ROL = "Porcentaje de jams por rol"
TOOLTIP_ROL = "Rol"
TOOLTIP_JAMS = "Jams"
TOOLTIP_PORCENTAJE = "Porcentaje"
TABLA_TODAS_JUGADORAS = "Tabla de todas las jugadoras"
COLUMNAS_TABLA_JUGADORAS = {
    "player_label": JUGADORA,
    "jams_played": "Jams jugados",
    "jams_as_jammer": "Jams como Jammer",
    "penalties": FALTAS,
    "penalties_per_jam": "Faltas por jam",
    "penalties_per_10min": "Faltas por 10 min en pista",
}

# --- Avisos ------------------------------------------------------------------
AVISOS_CALIDAD = "Avisos de calidad de datos:"
JAMS_INCOMPLETOS_EQUIPO = (
    "{n} jam(s) tienen datos de alineación incompletos; se ignoran los valores "
    "faltantes y esos jams se excluyen de las alineaciones."
)
JAMS_INCOMPLETOS_JUGADORAS = (
    "{n} jam(s) tienen datos de alineación incompletos; se ignoran los valores faltantes."
)
AVISO_JAMMER = (
    "La Jammer de la tabla de alineaciones no coincide con la de la tabla de jams en "
    "{fecha}, periodo {periodo}, jam {jam} (tabla de jams: {jammer_jams}; "
    "alineaciones: {jammer_alineaciones})."
)
AVISO_FALTA = (
    "Falta de la jugadora #{jugadora} ({fecha}, periodo {periodo}, jam {jam}) "
    "sin estar en la alineación de ese jam (posible error de digitación)."
)
AVISO_SIN_TIEMPO = "El partido {fecha} vs {rival} no tiene filas en la tabla de tiempos."


# --- Formatos ----------------------------------------------------------------
_PERIODOS = {1: "1.er periodo", 2: "2.º periodo"}
_PERIODOS_FRASE = {1: "el 1.er periodo", 2: "el 2.º periodo"}
PERIODOS_SELECCIONADOS = "los periodos seleccionados"


def periodo_etiqueta(periodo: int) -> str:
    """Texto del periodo: «1.er periodo», «2.º periodo»."""
    return _PERIODOS.get(int(periodo), f"Periodo {int(periodo)}")


def periodo_frase(periodos: list[int]) -> str:
    """Frase para títulos: «el 1.er periodo» o «los periodos seleccionados»."""
    if len(periodos) == 1:
        return _PERIODOS_FRASE.get(int(periodos[0]), f"el periodo {int(periodos[0])}")
    return PERIODOS_SELECCIONADOS


def titulo_con_contexto(base: str, rival: str | None, periodos: list[int]) -> str:
    """Título «base - General» o «base vs rival [en periodo]»."""
    if not rival:
        return f"{base} - {GENERAL}"
    if periodos:
        return f"{base} vs {rival} en {periodo_frase(periodos)}"
    return f"{base} vs {rival}"


def fmt_num(valor: float, decimales: int = 0, sufijo: str = "") -> str:
    """Formatea un número al estilo colombiano: coma decimal y punto de miles."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    texto = f"{valor:,.{decimales}f}"
    texto = texto.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return f"{texto}{sufijo}"


def fmt_pct(valor: float, decimales: int = 1) -> str:
    """Porcentaje con coma decimal y espacio: «35,1 %»."""
    return fmt_num(valor, decimales, " %")


# --- Perfil de la jugadora ---------------------------------------------------------
MUESTRA_CORTA_BAJA = "Baja"
MUESTRA_CORTA_OK = "Ok"
FILTRO_PERIODO_JUGADORAS = FILTRO_PERIODO

TARJETA_JAMS = "Jams jugados"
TARJETA_JAMS_DELTA = "{pct} de los jams del equipo"
TARJETA_PARTIDOS = "Partidos jugados"
TARJETA_ROL = "Rol principal"
TARJETA_ROL_DELTA = "{pct} de sus jams"
TARJETA_FALTAS_POR_JAM = "Faltas por jam"
TARJETA_FALTAS_DELTA = "{signo}{dif} vs. equipo ({equipo})"
TARJETA_FALTAS_AYUDA = (
    "Faltas de la jugadora dividido entre sus jams. El promedio del equipo es el total de "
    "faltas dividido entre los jams-jugadora."
)
SIN_ROL_PRINCIPAL = "sin dato"

RESUMEN_TITULO = "Resumen en tres frases"
RESUMEN_SIN_JAMS = "No tiene jams en los filtros seleccionados."
RESUMEN_MUESTRA_BAJA = (
    "Muestra baja: menos de {minimo} jams (n = {n}). Su rol principal fue {rol} ({pct} de sus jams)."
)
RESUMEN_MUESTRA_BAJA_ROL_UNICO = (
    "Muestra baja: menos de {minimo} jams (n = {n}). Jugó solo como {rol}."
)
RESUMEN_ROL_PRINCIPAL = "Su rol principal es {rol}: {n} de sus {jams} jams ({pct})."
RESUMEN_ROL_UNICO = "Jugó solo como {rol} ({n} jams)."
RESUMEN_EFECTIVOS = (
    "Sus puntos efectivos por jam, relativos al partido, son {valor} (n = {n} jams)."
)
RESUMEN_EFECTIVOS_CON_INTERVALO = (
    "Sus puntos efectivos por jam, relativos al partido, son {valor} "
    "(n = {n} jams; intervalo del 80 %: {bajo} a {alto})."
)
RESUMEN_EFECTIVOS_SIN_DATO = (
    "No hay datos de puntos efectivos para sus jams (n = {n} jams)."
)
RESUMEN_FALTAS = {
    "mas": (
        "Tiene {tasa} faltas por jam ({faltas} faltas en {n} jams), {dif} más que el "
        "promedio del equipo ({equipo})."
    ),
    "menos": (
        "Tiene {tasa} faltas por jam ({faltas} faltas en {n} jams), {dif} menos que el "
        "promedio del equipo ({equipo})."
    ),
    "igual": (
        "Tiene {tasa} faltas por jam ({faltas} faltas en {n} jams), igual que el "
        "promedio del equipo ({equipo})."
    ),
}
RESUMEN_FALTAS_SIN_DATO = "No hay datos de faltas por jam (n = {n} jams)."

PESTANA_JAMMER = "Como jammer"
PESTANA_PIVOT = "Como pivot"
PESTANA_BLOQUE = "Como bloque"
PESTANA_FALTAS = "Faltas"
PESTANA_POR_PARTIDO = "Por partido"
PESTANA_CON_QUIEN = "Con quién rinde"
PESTANAS_ROL = {"Jammer": PESTANA_JAMMER, "Pivot": PESTANA_PIVOT, "Bloque": PESTANA_BLOQUE}

COL_METRICA = "Métrica"
COL_VALOR = "Valor"
COL_DETALLE = "Detalle"
COL_PROMEDIO_EQUIPO = "Promedio del equipo"
COL_DIFERENCIA = "Diferencia"
COL_N_JAMS = "Jams (n)"
DETALLE_N_DE = "{k} de {n} jams"
NOTA_COMPARACION_ROL = (
    "El promedio del equipo es el de todas las jugadoras en ese mismo rol (incluida ella). "
    "Los puntos relativos se miden contra el promedio del partido, por eso su referencia es 0. "
    "Las diferencias de porcentajes están en puntos porcentuales (pp)."
)
NOTA_COMPARACION_BLOQUE = (
    "Puntos en contra por jam y lead rival se comparan con el promedio de todos los jams del equipo; "
    "faltas por jam y caja, con el de todas las bloques. "
    "Las diferencias de porcentajes están en puntos porcentuales (pp)."
)
METRICAS_ROL = {
    "jams": "Jams en este rol",
    "puntos_por_jam": "Puntos por jam",
    "lead_pct": "% de Lead",
    "lead_perdido_pct": "% de Lead perdido",
    "call_off_pct": "% de Call-off",
    "sin_pase_inicial_pct": "% sin pase inicial",
    "caja_pct": "Jams que arranca o termina en caja (%)",
    "eff_rel": "Puntos efectivos por jam, relativos al partido",
    "pts_for_rel": "Puntos a favor por jam, relativos al partido",
    "pts_against_rel": "Puntos en contra por jam, relativos al partido",
    "faltas_por_jam": "Faltas por jam",
    "star_pass": "Jams con star pass en que fue pivot",
    "pts_against": "Puntos en contra por jam",
    "rival_lead_pct": "% de Lead rival cuando patina",
    "caja_inicio_pct": "Jams que arranca en caja (%)",
}
MUESTRA_BAJA_ROL = "Muestra baja en este rol: menos de {minimo} jams (n = {n})."

FALTAS_POR_CODIGO_JUGADORA = "Faltas por código"
FALTAS_POR_PARTIDO_JUGADORA = "Faltas por partido"
FALTAS_POR_ROL_JUGADORA = "Faltas por rol"
COSTO_FALTAS = "Costo de sus faltas"
COSTO_FALTAS_TEXTO = (
    "Puntos en contra por jam cuando arranca en caja: {con} (n = {n_con} jams); "
    "cuando no arranca en caja: {sin} (n = {n_sin} jams)."
)
COSTO_FALTAS_INSUFICIENTE = (
    "Datos insuficientes: se necesitan al menos {minimo} jams en cada caso "
    "(arranca en caja: n = {n_con}; no arranca en caja: n = {n_sin})."
)
SIN_FALTAS_JUGADORA = "La jugadora no tiene faltas en los filtros seleccionados."

POR_PARTIDO_COLUMNAS = {
    "match_id": PARTIDO,
    "jams": "Jams (n)",
    "main_role": "Rol principal",
    "eff_por_jam": "Puntos efectivos por jam",
    "eff_rel_por_jam": "Efectivos relativos al partido",
    "penalties": FALTAS,
    "minutes_on_track": "Minutos en pista",
}

CON_QUIEN_INTRO = (
    "Duplas y ternas del pack (Pivot y Bloques) en las que juega, con al menos {minimo_dupla} jams "
    "juntas (duplas) o {minimo_terna} (ternas). Se ordenan por puntos efectivos por jam relativos al partido; cada una muestra su n."
)
CON_QUIEN_SOLO_PACK = "Solo se calculan para jams en que ella juega en el pack (Pivot o Bloque)."
MEJORES_DUPLAS = "Mejores duplas"
PEORES_DUPLAS = "Peores duplas"
MEJORES_TERNAS = "Mejores ternas"
PEORES_TERNAS = "Peores ternas"
SIN_COMBINACIONES_JUGADORA = (
    "No hay combinaciones con al menos {minimo} jams juntas."
)
COL_COMBINACION = "Combinación"
COL_RELATIVOS = "Efectivos relativos al partido"
COL_EFECTIVOS = "Puntos efectivos por jam"

TODAS_JUGADORAS_TITULO = "Todas las jugadoras"
TODAS_JUGADORAS_COLUMNAS = {
    "label": JUGADORA,
    "jams": "Jams (n)",
    "main_role": "Rol principal",
    "eff_rel_por_jam": "Efectivos relativos por jam",
    "pts_against_por_jam": "Puntos en contra por jam",
    "penalties_per_jam": "Faltas por jam",
    "muestra": "Muestra",
}
TODAS_JUGADORAS_NOTA = (
    "Las filas en gris tienen muestra baja (menos de {minimo} jams). Haz clic en el título de "
    "una columna para ordenar. Orden inicial: alfabético por jugadora."
)
DESCARGAR_CSV = "Descargar tabla en CSV"
NOMBRE_ARCHIVO_CSV = "jugadoras.csv"

COMO_LEER_TITULO = "Cómo leer esta página"
COMO_LEER_LINEAS = (
    "**Relativo al partido:** a los puntos efectivos de cada jam se les resta el promedio de su "
    "partido; 0 significa igual al promedio de ese partido, así un rival fuerte no castiga a quien jugó contra él.",
    "**Por jam:** todas las cifras son promedios por jam, no acumulados, porque el acumulado "
    "depende de los minutos jugados y del rival, y haría ver peor a quien juega más.",
    "**Muestra baja:** con menos de {minimo} jams una cifra se mueve mucho por azar; se muestra "
    "atenuada o en gris, pero no se oculta.",
    "**n:** cada cifra por jugadora trae su número de jams; con n pequeño, interprétala con mucha cautela.",
    "**Intervalo del 80 %:** rango donde probablemente está el promedio real; si incluye el 0, no hay "
    "evidencia de diferencia con el promedio del partido.",
)

MUESTRA_UN_PARTIDO = "Un partido"


# --- Alineaciones y combinaciones ----------------------------------------------------
PAGINA_ALINEACIONES = "Alineaciones"
ALINEACIONES_TITULO = "Alineaciones y combinaciones"
ALINEACIONES_INTRO = (
    "La unidad de análisis es el pack (Pivot y Bloques) de cada jam, sin importar la posición de "
    "planilla ni el orden. En «Quinteto con jammer» se usan las cinco jugadoras del jam."
)
TAMANOS_COMBINACION = {2: "Dupla", 3: "Terna", 4: "Cuarteto", 5: "Quinteto con jammer"}
SELECTOR_TAMANO = "Tamaño de la combinación"
MINIMO_JAMS = "Mínimo de jams"
AYUDA_MINIMO = (
    "Por defecto según el tamaño ({valores}). Las combinaciones bajo el mínimo se marcan "
    "como «Baja» y no entran en el gráfico ni en mejores y peores."
)
FILTRO_JAMMER = "Solo jams con la jammer"
AYUDA_FILTRO_JAMMER = "Compara combinaciones con la misma jammer del equipo."
FILTRO_JAMMER_TODAS = "Todas las jammers"
FILTRO_INCLUYE = "Incluye a..."
AYUDA_FILTRO_INCLUYE = "Solo combinaciones que contienen a todas las jugadoras elegidas."
ORDENAR_POR = "Ordenar por"
ORDEN_JAMS = "Jams"
ORDEN_EFECTIVOS = "Efectivos relativos"
MOSTRAR_BAJAS = "Mostrar también las combinaciones con muestra baja"
NOTA_NO_INDEPENDIENTES = (
    "Los jams se cuentan en varias combinaciones a la vez (cada jam aporta 4 ternas y 6 duplas), "
    "así que las filas no son independientes. Una combinación vista en varios partidos pesa más "
    "que una vista en uno solo."
)
NOTA_ORDEN_MUESTRA_BAJA = (
    "Al ordenar por efectivos relativos, las combinaciones con muestra baja van siempre al final."
)
TABLA_COMBINACIONES = "Tabla de combinaciones"
COLUMNAS_COMBINACIONES = {
    "Combinación": "Combinación",
    "jams": "Jams (n)",
    "partidos": "Partidos",
    "pts_for": "Puntos a favor por jam",
    "pts_against": "Puntos en contra por jam",
    "eff": "Efectivos por jam",
    "eff_rel": "Efectivos relativos al partido",
    "rival_lead_pct": "% de Lead rival",
    "faltas_por_jam": "Faltas del equipo por jam",
    "caja_pct": "% de jams con caja",
    "intervalo": "Intervalo del 80 %",
    "muestra": "Muestra",
}
GRAFICO_COMBINACIONES = "Efectivos relativos por combinación"
GRAFICO_COMBINACIONES_NOTA = (
    "Solo combinaciones con al menos el mínimo de jams. Barras de error: intervalo del 80 %."
)
MEJORES_5 = "Mejores 5"
PEORES_5 = "Peores 5"
MATRIZ_DUPLAS = "Matriz de duplas"
MOSTRAR_MATRIZ = "Mostrar la matriz de duplas"
MATRIZ_AYUDA = (
    "Cada celda es la dupla de esas dos jugadoras en el pack: color por puntos efectivos relativos "
    "al partido, y el n de jams en el tooltip. En gris, las duplas bajo el mínimo ({minimo} jams)."
)
TOOLTIP_JUGADORA_A = "Jugadora"
TOOLTIP_JUGADORA_B = "Con"
SIN_COMBINACIONES_PAGINA = "No hay combinaciones para los filtros seleccionados."
SIN_COMBINACIONES_SOBRE_MINIMO = (
    "Ninguna combinación llega al mínimo de {minimo} jams con estos filtros."
)

# Resumen en la página de equipo
RESUMEN_TERNAS_TITULO = "Alineaciones más repetidas"
RESUMEN_TERNAS_INTRO = (
    "Las 3 ternas del pack (Pivot y Bloques) con más jams juntas, con su n."
)
COLUMNAS_TERNAS = {
    "Combinación": "Terna",
    "jams": "Jams (n)",
    "eff_rel": "Efectivos relativos al partido",
    "muestra": "Muestra",
}
ENLACE_ALINEACIONES = "Ver todas las alineaciones y combinaciones"
ENLACE_ALINEACIONES_SIN_NAVEGACION = "Abre la página «Alineaciones» para ver todas las combinaciones."


# --- Página de equipo (reorganizada en pestañas) -------------------------------------
TITULO_EQUIPO_GENERAL = "Estadísticas de equipo: general"
TITULO_EQUIPO_VS = "Estadísticas de equipo vs {rival}"
TITULO_EQUIPO_VARIOS = "Estadísticas de equipo ({n} partidos)"
AVISO_SIN_PARTIDOS = "El filtro de partidos no puede quedar vacío: se marcaron todos los partidos de nuevo."
AVISO_SIN_PERIODOS = "El filtro de periodo no puede quedar vacío: se marcaron todos los periodos de nuevo."

PESTANA_EQ_RESUMEN = "Resumen"
PESTANA_EQ_JAMS = "Jams"
PESTANA_EQ_FALTAS = "Faltas"
PESTANA_EQ_COMBINACIONES = "Combinaciones"

TARJETA_PUNTOS_A_FAVOR = "Puntos a favor por jam"
TARJETA_PUNTOS_EN_CONTRA = "Puntos en contra por jam"
TARJETA_DIFERENCIA = "Diferencia por jam"
TARJETA_LEAD_NUESTRO = "% de Lead nuestro"
TARJETA_LEAD_RIVAL = "% de Lead del rival"
TARJETA_CALL_OFF = "% de Call-off"
TARJETA_SIN_PASE_INICIAL = "% sin pase inicial"
TARJETA_FALTAS_EQUIPO_POR_JAM = "Faltas por jam"
AYUDA_TARJETA_JAMS = "Calculado con {n} jams."
DELTA_VS_RESTO = "{valor} vs. el resto de los partidos"

TABLA_POR_PARTIDO = "Resumen por partido"
COLUMNAS_RESUMEN_PARTIDOS = {
    "Rival": RIVAL,
    "Date": FECHA,
    "marcador": "Marcador",
    "jams": "Jams (n)",
    "diff_per_jam": "Diferencia por jam",
    "penalties": FALTAS,
}
LO_QUE_MAS_SE_NOTA = "Lo que más se nota"
SIN_FRASES = "Ninguna regla tiene todavía {minimo} jams de muestra con estos filtros."
FRASE_LEAD = (
    "El Lead fue nuestro en {nuestro} de los jams y del rival en {rival} "
    "(brecha de {brecha}; n = {n} jams)."
)
FRASE_CAJA = (
    "Con 0 jugadoras en caja al inicio del jam recibimos {sin} puntos por jam (n = {n_sin} jams); "
    "con 1 o más, {con} (n = {n_con} jams)."
)
FRASE_PERIODO = (
    "El periodo con peor diferencia por jam fue el {peor}: {valor_peor} (n = {n_peor} jams), "
    "frente a {valor_otro} (n = {n_otro} jams) en el {otro}."
)

AVISO_SIN_TIEMPO_PARTIDOS = (
    "No hay datos de tiempo (tabla de tiempos) de: {partidos}. "
    "Esos partidos no aparecen en el gráfico por tiempo."
)
TITULO_EFECTIVOS_POR_JAM_PANELES = "Puntos efectivos por jam"
TITULO_EFECTIVOS_POR_TIEMPO_PANELES = "Puntos efectivos por tiempo de juego"
EJE_MINUTOS_DE_JUEGO = "Minutos de juego al empezar el jam"
NOTA_TIEMPO_POR_PARTIDO = (
    "El tiempo de juego es la suma de la duración de los jams y se reinicia en cada partido."
)
TITULO_FALTAS_JUGADORA_ROL = "Faltas por jugadora y rol"
TITULO_FALTAS_PERIODO = "Faltas por periodo"
TITULO_FALTAS_PARTIDO = "Faltas por partido"
TOOLTIP_ROL_FALTA = "Rol en el jam"
TOOLTIP_FALTAS_POR_JAM = "Faltas por jam"
EJE_PERIODO = PERIODO
EJE_PARTIDO = PARTIDO


# --- Calidad de datos ----------------------------------------------------------------
PAGINA_CALIDAD = "Calidad de datos"
CALIDAD_TITULO = "Calidad de datos"
CALIDAD_INTRO = (
    "Revisa estos chequeos antes de mirar los gráficos: un error en los Excel se vería "
    "como una cifra rara en cualquier página. Usa todos los partidos, sin filtros."
)
CALIDAD_RESUMEN = "{avisos} de {total} chequeos tienen avisos."
CALIDAD_TODO_OK = "Los {total} chequeos están OK."
ESTADO_OK = "OK"
ESTADO_AVISO = "Aviso"
CALIDAD_CANTIDAD = "Filas afectadas: {n}"
CALIDAD_SIN_FILAS = "Sin filas afectadas."
CALIDAD_FILAS = "Filas afectadas"
CALIDAD_DETALLE = "Jams por partido (tabla de jams)"
DESCARGAR_FILAS = "Descargar filas afectadas (CSV)"
TABLA_JAMS = "Tabla de jams"
TABLA_JAMS_RIVAL = "Tabla de jams del rival"
TABLA_ALINEACIONES = "Alineaciones"
TABLA_TIEMPOS = "Tiempos"
PROBLEMA_SIN_NOMBRE = "Sin nombre"
PROBLEMA_NOMBRE_REPETIDO = "Nombre repetido"
# clave -> (título, descripción)
CHEQUEOS = {
    "jams_por_partido": (
        "Jams por partido y periodo",
        "Cada partido y periodo debe tener los mismos jams en la tabla de jams, la del rival y las alineaciones.",
    ),
    "claves_duplicadas": (
        "Claves (fecha, periodo, jam) duplicadas",
        "La clave no debe repetirse en jams, rival, alineaciones ni tiempos. Si se repite dentro de un "
        "partido, puede haber dos partidos con la misma fecha y rival mezclados.",
    ),
    "partidos_sin_time": (
        "Partidos sin tiempos",
        "Partidos con jams pero sin filas en la tabla de tiempos; no salen en el gráfico por tiempo "
        "ni en los minutos en pista.",
    ),
    "nombres": (
        "Nombres de jugadoras",
        "Jugadoras de las alineaciones o las faltas sin nombre en Player_names, y nombres repetidos "
        "(en los gráficos esas jugadoras llevan el número).",
    ),
    "valores_faltantes": (
        "Valores «?» o vacíos en las alineaciones",
        "Se ignoran esos valores y el jam se informa como incompleto en las páginas.",
    ),
    "faltas_unknown": (
        "Faltas sin código",
        "Faltas con código «Unknown»; se muestran como «Sin código».",
    ),
    "faltas_fuera_de_pista": (
        "Faltas de una jugadora que no estaba en pista",
        "La jugadora de la falta no figura en la alineación de ese jam (posible error de digitación).",
    ),
    "jammer": (
        "Jammer distinta entre alineaciones y jams",
        "La Jammer de las alineaciones debe coincidir con la de la tabla de jams.",
    ),
}
COLUMNAS_CALIDAD = {
    "Date": FECHA,
    "Period": PERIODO,
    "Jam": JAM,
    "Rival": RIVAL,
    "Tabla": "Tabla",
    "match_id": PARTIDO,
    "Player_number": "Jugadora (número)",
    "Name": "Nombre",
    "Problema": "Problema",
    "Penalty_code": "Código de falta",
    "Jammer": "Jammer",
    "Jammer_jam_table": "Jammer (tabla de jams)",
    "Jammer_lineups": "Jammer (alineaciones)",
    "Pivot": "Pivot",
    "Block_1": "Bloque (planilla 1)",
    "Block_2": "Bloque (planilla 2)",
    "Block_3": "Bloque (planilla 3)",
    "jam_table": "Jams (tabla de jams)",
    "rival": "Jams (tabla del rival)",
    "lineups": "Jams (alineaciones)",
    "jams": "Jams (n)",
}
AVISO_PARTIDO_REPETIDO = (
    "El partido {partido} repite jams (mismo periodo y número): puede haber dos partidos con la "
    "misma fecha y rival, y sus filas se estarían mezclando."
)
