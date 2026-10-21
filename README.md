# Radical Stats

Aplicación Streamlit para analizar estadísticas de roller derby del equipo y de las jugadoras, con filtros por partido.

## Estructura del proyecto

```text
.
├── app.py                              # Navegación (st.navigation) e inicio
├── pages/
│   ├── 1_Estadisticas_de_Equipo.py
│   ├── 2_Estadisticas_de_Jugadoras.py
│   ├── 3_Alineaciones.py
│   └── 4_Calidad_de_Datos.py
├── src/radical_stats/
│   ├── cache.py                        # Cálculos pesados con st.cache_data
│   ├── combinaciones.py                # Duplas, ternas, cuartetos y quintetos
│   ├── config.py                       # Mínimos de jams y parámetros del bootstrap
│   ├── data_loader.py                  # Carga de Excel (con caché según fecha de modificación)
│   ├── equipo.py                       # Cálculos de la página de equipo
│   ├── filters.py
│   ├── graficos.py                     # Gráficos Altair de la página de equipo
│   ├── jugadoras.py                    # Etiquetas de jugadora (nombre y número si se repite)
│   ├── lineups.py
│   ├── metrics.py
│   ├── models.py
│   ├── partidos.py                     # match_id en un solo lugar
│   ├── perfil.py                       # Cálculos del perfil de una jugadora
│   ├── textos.py                       # Única fuente de textos visibles
│   ├── ui.py
│   └── validation.py                   # Avisos y chequeos de calidad de datos
├── tests/
├── data/                               # Excel de entrada y Penalty_codes.csv
├── .github/workflows/tests.yml         # pytest y ruff en cada push y pull request
├── pyproject.toml                      # Dependencias, pytest y ruff
├── requirements.txt                    # Dependencias de ejecución
└── requirements-dev.txt                # Más pytest y ruff
```

## Ejecutar en local

Requiere Python 3.11 a 3.13 (`requires-python` en `pyproject.toml`; se probó en 3.13 y la integración continua también corre 3.11).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests y estilo

```bash
pip install -r requirements-dev.txt
pytest          # los tests usan los datos reales de data/
ruff check .    # estilo y errores comunes
```

`pyproject.toml` agrega `src/` al path de pytest, así que no hace falta `PYTHONPATH`. En GitHub, `.github/workflows/tests.yml` corre `ruff check .` y `pytest` en cada push y pull request (Python 3.11 y 3.13).

## Páginas

La navegación se define en `app.py` con `st.navigation` y `st.Page`, de modo que los títulos del menú llevan tildes aunque los archivos tengan nombres sin ellas.

- **Inicio**: descripción de la aplicación.
- **Estadísticas de equipo**: cuatro pestañas — Resumen (nosotras contra rival, resumen por partido y «Lo que más se nota»), Jams (puntos efectivos por jam y por tiempo), Faltas (por jugadora y rol, periodo, partido, costo de la caja y código) y Combinaciones (ternas más repetidas y efectivos por jugadora relativos al partido).
- **Alineaciones**: duplas, ternas, cuartetos y quintetos con jammer (ver «Alineaciones y combinaciones»).
- **Calidad de datos**: chequeos de los Excel con las filas afectadas descargables (ver «Calidad de datos»).
- **Estadísticas de jugadoras**: selector de jugadora, distribución de roles (en jams y en porcentaje) y tabla de todas las jugadoras.

## Textos y formatos en español

- Todos los textos visibles (títulos, etiquetas, ejes, tooltips, avisos, ayudas y mensajes de «sin datos») están en `src/radical_stats/textos.py`. Las páginas y `ui.py` solo importan de ahí.
- Los nombres internos de columnas de los DataFrames y de los archivos Excel siguen en inglés; las tablas que se muestran usan columnas en español (`COLUMNAS_TABLA_JAMS`, `COLUMNAS_TABLA_JUGADORAS`).
- `fmt_num` y `fmt_pct` formatean con coma decimal y punto de miles (por ejemplo `2,96` y `35,1 %`) en métricas, tablas y tooltips.
- **Limitación conocida:** los números de los *ejes* de los gráficos de Altair (marcas como `0.5`) los dibuja Vega con formato en inglés y no se localizan. Los valores de los tooltips sí se muestran con coma, porque se formatean antes de graficar. Tampoco se traducen los textos propios del navegador o de Streamlit (por ejemplo, el menú de acciones de las tablas).
- Las tablas muestran los números ya formateados como texto, por lo que su orden al hacer clic en una columna es alfabético.

### Glosario

| Inglés | Español |
|---|---|
| Match | Partido |
| Period | Periodo («1.er periodo», «2.º periodo») |
| Lineup | Alineación |
| Player | Jugadora |
| Block | Bloque |
| Lider / Lost / Call / No_initial_pass / Star_pass | Lead / Lead perdido / Call-off / Sin pase inicial / Star pass |
| Penalties / Penalty box | Faltas / Caja |
| Effective points | Puntos efectivos (puntos a favor menos puntos en contra) |

## Página de equipo

La lógica vive en `src/radical_stats/equipo.py` (cálculos) y `src/radical_stats/graficos.py` (gráficos Altair que reciben DataFrames y devuelven el gráfico); la página solo une filtros, pestañas y llamadas.

- **Filtros:** partido y periodo en la barra lateral. Ninguno puede quedar vacío: si se vacía, se avisa y se vuelven a marcar todos (antes, un filtro vacío mostraba todo con el título «General»). El título depende de la selección: todos los partidos = «Estadísticas de equipo: general»; uno = «… vs <rival>»; varios = «… (N partidos)».
- **Resumen:** ocho tarjetas nosotras contra rival (puntos a favor y en contra por jam, diferencia por jam, % de Lead nuestro y del rival, % de Call-off, % sin pase inicial, faltas por jam). Si hay partidos sin seleccionar, cada tarjeta muestra la diferencia contra el resto de los partidos (mismos periodos). Tabla por partido (rival, fecha, marcador, jams, diferencia por jam y faltas) y «Lo que más se nota»: hasta 3 frases por reglas, cada una con su n (brecha de Lead, costo de la caja con 0 contra 1 o más jugadoras en caja al inicio y periodo con peor diferencia por jam). Una regla con menos de `MIN_JAMS_REGLA = 10` jams de muestra no se muestra.
- **Jams:** barras de puntos efectivos por jam en un panel por partido y periodo (sin mezclar partidos) y la línea de efectivos por tiempo. El tiempo de juego es la suma de la duración de los jams y **se reinicia en cada partido**; `inicio_min` es el minuto en que empieza el jam, así que el primer punto de cada partido está en 0. Un partido sin filas en `Time.xlsx` (hoy, 2026-08-08) se nombra en un aviso en vez de omitirse sin decir nada.
- **Faltas:** faltas por jugadora (barras apiladas por el rol que tenía en el jam de la falta), por periodo y por partido, la tabla «Costo de la caja» y las faltas por código.
- **Combinaciones:** las 3 ternas más repetidas con su n, el enlace a la página de alineaciones y los puntos efectivos por jugadora relativos al partido.
- **Etiquetas de jugadora:** `radical_stats.jugadoras` da el nombre, y nombre y número cuando el nombre se repite (dos «Medusa», #2 y #10). Se usa en todos los gráficos y tablas de la página de equipo y en las combinaciones.
- El CSS de la página está en `ui.aplicar_estilo_ancho`.

## Página de jugadoras

La página solo presenta; los cálculos viven en `src/radical_stats/perfil.py` (y en `metrics.py`). Se pensó para entender en 30 segundos cómo le fue a una jugadora sin sacar conclusiones falsas con pocos jams.

- **Filtros:** partido y periodo (barra lateral). El selector de jugadora muestra siempre nombre y número (hay dos «Medusa», #2 y #10).
- **Tarjetas:** jams jugados (y % de los jams del equipo), partidos jugados, rol principal (con su % de jams) y faltas por jam con la diferencia contra el promedio del equipo (faltas totales / jams-jugadora).
- **Resumen en tres frases** (`resumen_tres_frases`): reglas descriptivas sobre rol principal, puntos efectivos por jam relativos al partido (con su n y el intervalo del 80 %) y faltas por jam contra el equipo. Con menos de `MIN_JAMS_JUGADORA` jams, la primera frase abre con «Muestra baja: menos de 10 jams» y las demás se muestran atenuadas.
- **Pestañas por rol:** «Como jammer», «Como pivot» y «Como bloque» solo aparecen si la jugadora tuvo al menos 1 jam en ese rol. Cada cifra trae su n y su diferencia contra el promedio del equipo en ese rol (las diferencias de porcentajes están en puntos porcentuales, pp). Además hay «Faltas» (por código, partido y rol, y costo de sus faltas), «Por partido» y «Con quién rinde» (mejores y peores duplas y ternas del pack con al menos el mínimo de jams de su tamaño, `MIN_JAMS_COMBINACION`).
- **Costo de sus faltas:** puntos en contra por jam cuando arranca en caja contra cuando no, solo con al menos 5 jams en cada caso.
- **Todas las jugadoras:** tabla ordenable con jams, rol principal, efectivos relativos por jam, puntos en contra por jam, faltas por jam y la columna Muestra («Baja» u «Ok»). Las filas con muestra baja salen en gris y la tabla se puede descargar en CSV (separador `;` y coma decimal, para Excel en español).
- **Reglas:** nunca se muestra una cifra por jugadora sin su n de jams y nunca se ordena por una métrica acumulada.

## Alineaciones y combinaciones

El «Lineup summary» agrupaba por quinteto exacto (cinco jugadoras, jammer incluida): con 150 jams completos hay 95 quintetos distintos y el máximo se repite 6 veces, muy poco para concluir algo. El **pack** (Pivot más 3 Bloques, 4 patinadoras) sí se repite: 78 cuartetos distintos, 136 ternas y 80 duplas. La página **Alineaciones** y el módulo `src/radical_stats/combinaciones.py` usan el pack como unidad de análisis:

- `combos_por_jam(lineups_long, tamano, incluir_jammer=False)`: una fila por jam y combinación (`itertools.combinations` sobre las jugadoras del pack ordenadas, sin importar la posición de planilla). Un jam con menos jugadoras válidas que el tamaño no aporta a ese tamaño; los valores «?» ya los descarta `lineups_long`, así que un jam con un «?» en el pack no da cuarteto pero sí las ternas y duplas de las jugadoras válidas. Con `incluir_jammer` (quinteto) se usan las cinco jugadoras del jam.
- `estadisticas_combinaciones(frames, tamano, ...)`: por combinación, jams, partidos, puntos a favor y en contra por jam, efectivos por jam, efectivos relativos al partido, % de Lead rival, faltas del equipo por jam, % de jams con caja e intervalo del 80 % por bootstrap (1000 remuestreos, semilla fija, con 5 o más jams). Admite filtrar por jammer y por jugadoras incluidas.
- **Muestra:** «Baja» si los jams están bajo el mínimo del tamaño, «Un partido» si la combinación apareció en un solo partido, «Ok» en los demás casos. Mínimos por defecto (`config.MIN_JAMS_COMBINACION`): dupla 8, terna 5, cuarteto 3, quinteto 3; en la página se pueden cambiar.
- **Salidas:** tabla ordenable (con muestra baja siempre al final al ordenar por efectivos), barras de efectivos relativos con intervalo del 80 % solo para las que superan el mínimo, «Mejores 5» y «Peores 5» y una matriz opcional de duplas con las celdas bajo el mínimo en gris.
- **Los jams se cuentan en varias combinaciones a la vez** (cada jam aporta 4 ternas y 6 duplas), así que las filas no son independientes. Una combinación vista en varios partidos pesa más que una vista en uno solo.
- Los cálculos de la página usan `st.cache_data`.

## Definiciones de faltas y caja

Se calculan en `src/radical_stats/metrics.py`:

- **Falta**: una fila del `Penalty_tracker` (`Date`, `Period`, `Jam`, `Player_number`, `Penalty_code`). Hay 131 en total.
- **Faltas por jam**: faltas divididas entre los jams en pista de la jugadora, del equipo o de la combinación (`penalties_by_jam`, `player_penalty_summary`).
- **Faltas por 10 minutos en pista**: faltas / minutos × 10. Los minutos suman la duración (`Time.xlsx`) de los jams que jugó la jugadora, y solo cuentan los jams con tiempo. El partido de 2026-08-08 no tiene filas en `Time`, así que se muestra «sin dato» (no 0).
- **Rol de una falta**: el rol (Jammer, Pivot o Bloque) que tenía la jugadora en el jam de la falta, según `lineups_long`. Si la jugadora no figura en la alineación de ese jam, la falta se muestra como «Fuera de la alineación».
- **box_start** de un jam: número de jugadoras nuestras con `Start_box = 1`; se agrupa en 0, 1 y 2 o más (`box_state_by_jam`).
- **Jam con caja**: al menos una jugadora con `Start_box` o `Finish_box = 1`.

Las columnas `*_Start_jam_Box` y `*_Finish_jam_Box` de `Lineups.xlsx` son casillas de caja, **no faltas** (164 casillas frente a 131 faltas; quien empieza y termina el jam en caja marcaba dos casillas). Por eso ya no se usan como faltas: el antiguo gráfico «Penalties by Lineup» se eliminó. Las combinaciones muestran ahora las faltas reales del `Penalty_tracker` (faltas del equipo por jam) en los jams de cada una.

**Costo de la caja** (`box_cost_table`): por cada valor de `box_start` (0, 1 y 2 o más) muestra jams (n), puntos a favor por jam, puntos en contra por jam, puntos efectivos por jam y % de Lead rival. Con los datos actuales: 78 jams y 3,78 puntos en contra para 0; 54 y 5,39 para 1; 19 y 5,11 para 2 o más. No está ajustado por partido ni por jammer, y n es pequeño en cada grupo: son diferencias descriptivas, no efectos causales.

### Falta que no coincide con la alineación

La falta de 2025-11-02, 1.er periodo, jam 19, jugadora #17 no coincide con la alineación de ese jam. No se elimina: cuenta en todos los totales y aparece en los avisos de calidad de datos como posible error de digitación.

## Puntos efectivos por jugadora

El acumulado de puntos efectivos por jugadora engañaba: depende de los minutos jugados (el equipo promedia −1,56 por jam, así que quien juega más acumula más negativo), de un solo partido (Fuego Latino suma −249 de los −236 totales), de la jammer con la que patina una bloque y no mostraba el tamaño de la muestra. Por eso la página de equipo usa puntos efectivos **por jam** y **relativos al partido**. Se calculan en `src/radical_stats/metrics.py`:

- `effective_by_jam(frames)`: une `Jam_table` y `Rival_Jam_table` por (`Date`, `Period`, `Jam`) y da `pts_for`, `pts_against`, `eff = pts_for - pts_against`, `match_id` y `eff_rel = eff - promedio de eff de ese partido` (promedia 0 dentro de cada partido). El promedio se calcula con los datos que reciba la función, es decir, con los filtros de partido y periodo aplicados.
- `player_effectiveness(frames, por_rol=False)`: por jugadora (o por jugadora y rol), con su n de jams:
  - `eff_por_jam`, `eff_rel_por_jam`, `pts_for_por_jam`, `pts_against_por_jam` y sus versiones relativas al partido.
  - `con_y_sin`: por partido, eff medio con ella menos eff medio sin ella, solo si hay al menos 5 jams sin ella; se promedia entre partidos ponderando por sus jams. Es NaN si ningún partido es válido.
  - `eff_ajustada_jammer` (solo Pivot y Bloque): eff del jam menos el promedio de eff de los jams del mismo partido con la misma jammer; si esa jammer tiene menos de 3 jams en el partido, se usa el promedio del partido.
  - Intervalo del 80 % por bootstrap (1000 remuestreos de sus jams, semilla fija) sobre `eff_rel_por_jam`, con al menos 5 jams.
- `player_effectiveness_by_match(frames, jugadora)`: por partido, jams, eff por jam, eff relativa y faltas (se muestra en la página de jugadoras).

Los mínimos y parámetros están en `src/radical_stats/config.py` (`MIN_JAMS_JUGADORA = 10`, `MIN_JAMS_COMBINACION = {2: 8, 3: 5, 4: 3, 5: 3}` por tamaño de combinación, etc.). Por debajo del mínimo se marca «Muestra baja» (gris en los gráficos, etiqueta en las tablas), pero nunca se oculta.

**Cómo leerlo:** son diferencias descriptivas con pocos jams. Las barras de error del 80 % muestran cuánto puede moverse el promedio por azar; si cruzan el 0, no hay evidencia de que la jugadora sea mejor o peor que el promedio del partido. «Con y sin ella» y «Ajustados por jammer» no tienen barra de error.

## Códigos de falta

`data/Penalty_codes.csv` (columnas `code`, `nombre_es`, `descripcion_es`) cubre los 15 códigos presentes en el `Penalty_tracker`: D, X, M, B, F, P, C, H, I, L, A, G, E, N y `Unknown`. El gráfico de faltas por código lo usa.

- **Fuente:** la leyenda de la hoja «Penalties» de `data/Partidos/Match_*.xlsx`, donde cada código encabeza su nombre (por ejemplo `A` = High Block, `B` = Back Block, `D` = Direction). El mapeo se contrastó con la hoja «Penalty Summary» (orden de columnas) y con el `Penalty_tracker`: en `Match_1` coinciden B, L, H, P y X, y en `Match_3` coinciden G, A, M, D, X e I.
- `nombre_es` es la traducción al español del nombre que aparece en la planilla.
- `descripcion_es` solo se llena con las variantes que la leyenda lista bajo el código (C, D, N, P y X). En los demás códigos queda vacía: **pendiente de confirmar por el cuerpo técnico**. En particular, no se confirmó qué variantes agrupan `G` (la leyenda lista «Insubordination») e `I` (la leyenda lista «Star Pass Violation» y una línea «/ Interference» cortada).
- **`Unknown`:** 25 de las 131 faltas (19 %) no tienen código; se muestran como «Sin código».

## Cómo agregar un partido nuevo

1. **Agrega las filas del partido** (la fecha y el rival identifican el partido; no cambies los nombres de columnas) en los Excel de `data/`:
   - `Jam_table.xlsx`: una fila por jam de nuestro equipo (`Date`, `Rival`, `Period` 1 o 2, `Jam`, `Jammer`, `Total_points`, etc.).
   - `Rival_Jam_table.xlsx`: una fila por jam del rival (mismas claves; la columna `Team` es el rival).
   - `Lineups.xlsx`: una fila por jam con `Jammer`, `Pivot`, `Block_1` a `Block_3` y las columnas de caja. **Ojo:** aquí `Period` es `1` para el primer periodo y `0` para el segundo (ver «Codificación de Period»).
   - `Penalty_tracker.xlsx`: una fila por falta (`Player_number`, `Penalty_code`; `Unknown` si no se sabe el código).
   - `Time.xlsx`: duración en segundos de cada jam (opcional: sin él, el partido se avisa y no sale en el gráfico por tiempo ni en los minutos en pista).
   - `Player_names.xlsx`: solo si hay jugadoras nuevas.
   - `Penalty_codes.csv`: solo si aparece un código de falta nuevo.
2. **Guarda los archivos y recarga la página**: la app vuelve a leer los datos sola porque la caché usa la fecha de modificación de cada archivo; no hace falta reiniciarla.
3. **Abre «Calidad de datos»** y revisa que:
   - «Jams por partido y periodo» esté en OK (los mismos jams en jams, rival y alineaciones) y que el partido nuevo aparezca con los jams esperados;
   - «Claves duplicadas» esté en OK (si el partido repite fecha y rival con otro, sus filas se mezclarían);
   - «Jammer distinta» esté en OK y que «Faltas de una jugadora que no estaba en pista» y «Valores «?»» solo muestren lo que ya sabes que es un error de digitación;
   - «Partidos sin tiempos» y «Nombres de jugadoras» no traigan novedades inesperadas.
   Cada chequeo permite descargar sus filas afectadas en CSV para corregirlas en el Excel.

## Calidad de datos

La página **Calidad de datos** (`src/radical_stats/validation.py`, función `chequeos_calidad`) revisa los datos sin filtros y muestra para cada chequeo el estado (OK o Aviso), la cantidad de filas afectadas y esas filas, descargables en CSV. Con los datos de hoy:

| Chequeo | Estado | Filas |
|---|---|---|
| Jams por partido y periodo iguales entre jams, rival y alineaciones (40, 45, 38 y 28 jams por partido) | OK | 0 |
| Claves (fecha, periodo, jam) duplicadas en jams, rival, alineaciones o tiempos | OK | 0 |
| Partidos sin filas en `Time.xlsx` (Rock and Roller Queens, 2026-08-08) | Aviso | 1 |
| Jugadoras sin nombre y nombres repetidos (Medusa #2 y Medusa #10) | Aviso | 2 |
| Valores «?» o vacíos en `Lineups.xlsx` (2026-08-08, 2.º periodo, jam 12) | Aviso | 1 |
| Faltas con código `Unknown` (25 de 131) | Aviso | 25 |
| Faltas de una jugadora que no estaba en pista (2025-11-02, 1.er periodo, jam 19, jugadora 17) | Aviso | 1 |
| Jammer de las alineaciones distinta de la de la tabla de jams | OK | 0 |

La clave duplicada no se revisa en `Penalty_tracker.xlsx`, porque una jugadora puede tener varias faltas en un mismo jam.

### Identificador de partido (`match_id`)

`radical_stats.partidos` es el único lugar donde se arma el `match_id` («fecha | rival»). Si dos partidos distintos compartieran fecha y rival, sus filas quedarían bajo el mismo `match_id`; en ese caso se repetirían (`Period`, `Jam`) dentro del «partido», y la aplicación lo avisa (en todas las páginas y en la de calidad de datos) en lugar de mezclarlos en silencio.

### Caché

`load_data()` y `load_penalty_codes()` leen los archivos solo cuando cambia la firma de `data/` (nombre, fecha de modificación y tamaño de cada Excel y CSV; `data_loader.firma_datos`), así que un Excel actualizado se recarga sin reiniciar la app. Los cálculos pesados (bootstrap de efectividad, combinaciones, perfil de la jugadora y chequeos) están en `radical_stats.cache` con `st.cache_data` y usan esa misma firma, junto con los partidos y periodos filtrados, como llave.

## Definiciones de métricas

- **Puntos efectivos** (`eff`): puntos a favor menos puntos en contra de un jam. Se calculan uniendo `Jam_table` y `Rival_Jam_table` por (`Date`, `Period`, `Jam`).
- **Relativos al partido** (`eff_rel`): los puntos efectivos de un jam menos el promedio de puntos efectivos de su partido. Promedian 0 dentro de cada partido; quitan el efecto de enfrentar a un rival fuerte o débil.
- **Por jam, no acumulado:** el acumulado depende de los minutos jugados y del rival; por eso se comparan promedios por jam.
- **Con y sin ella:** por partido, el promedio de `eff` en los jams con la jugadora menos el promedio en los jams sin ella (solo si hay al menos 5 jams sin ella), ponderado por los jams de cada partido.
- **Ajustados por jammer:** para Pivot y Bloque, `eff` del jam menos el promedio de los jams del mismo partido con la misma jammer (o el del partido si la jammer tiene menos de 3 jams).
- **Caja:** `box_start` es el número de jugadoras nuestras con `Start_box = 1` al inicio del jam (0, 1 o 2 o más); un jam con caja tiene al menos una jugadora con `Start_box` o `Finish_box = 1`. Las casillas de caja **no son faltas**.
- **Falta:** una fila del `Penalty_tracker`. Faltas por jam = faltas / jams.
- **Muestra baja:** menos de `MIN_JAMS_JUGADORA = 10` jams en una jugadora, o menos del mínimo de su tamaño en una combinación (`MIN_JAMS_COMBINACION`: dupla 8, terna 5, cuarteto 3, quinteto 3). Se marca en gris o con la etiqueta «Baja», pero nunca se oculta.
- **Intervalo del 80 %:** bootstrap de 1000 remuestreos (semilla fija) de los jams de la jugadora o combinación, con al menos 5 jams.
- **Pack:** Pivot más los 3 Bloques (4 patinadoras); la Jammer va aparte.

## Codificación de Period en `Lineups.xlsx`

`Jam_table`, `Rival_Jam_table`, `Penalty_tracker` y `Time` guardan `Period` como `1` (primer periodo) y `2` (segundo periodo). `Lineups.xlsx`, en cambio, lo guarda como «periodo mod 2»: `1` = primer periodo y `0` = segundo periodo.

`load_data()` normaliza todas las tablas a `Period` entero 1/2 y traduce Lineups con el mapeo explícito `{1: 1, 0: 2}` (si Lineups ya usara 1/2, no se toca). El mapeo se verificó con los datos: con él, la `Jammer` de Lineups coincide con la de `Jam_table` en los 151 jams, y 130 de las 131 faltas caen sobre una jugadora de la alineación de ese jam. Sumar 1 a todo (`0 -> 1`, `1 -> 2`) cruza los dos periodos y rompe los cruces por (`Date`, `Period`, `Jam`).

`radical_stats.validation` revisa estas condiciones al cargar y la aplicación muestra avisos que no bloquean (Jammer distinta, faltas de jugadoras fuera de la alineación y partidos sin filas en `Time`).

## Modelo de roles

En `Lineups.xlsx`, `Block_1`, `Block_2` y `Block_3` son posiciones de la planilla, no de la cancha. Solo hay tres roles: Jammer, Pivot y Bloque. El pack es el Pivot más los 3 Bloques; la Jammer va aparte. `radical_stats.lineups.lineups_long` devuelve una fila por jugadora por jam (`Role`, `Start_box`, `Finish_box`) e ignora los valores `0`, `?`, vacíos y NaN. Los jams con valores faltantes se informan como incompletos, y los jams con el pack vacío no aportan combinaciones. No se infiere quién anotó tras un star pass porque ese dato no existe.

## Notas

- El filtro de partido usa `Date` + `Rival` como identificador.
- Si se agregan nuevos resúmenes de partidos a los Excel actuales, estarán disponibles automáticamente.
