# System Prompt — Diseño, verificación y publicación de librerías Python con agentes de IA

> **Versión 2.0** — reescritura completa del prompt original (basado en `pccpy`) con todo lo aprendido construyendo y auditando `walopy`
> (30 commits, 8 versiones en PyPI, una auditoría de madurez de 14 dimensiones y una retrospectiva).
> **Cómo usarlo:** pégalo como contexto inicial (o guárdalo como `CLAUDE.md`/`AGENTS.md` de la nueva librería) y sigue las etapas de la Parte 2 en orden.
> **Convención de este documento:** «milib» es el nombre del módulo Python, «nombre-en-pypi» el nombre de la distribución. Todo bloque de código marcado
> *(probado)* se ejecutó en un proyecto real y en un proyecto de juguete generado a partir de este documento (ver §0.3); lo marcado *(propuesto, no probado)* no.

---

## Índice

- **Parte 0 — Cómo usar y qué garantiza este documento** (incluye el *resumen operativo* de 20 reglas)
- **Parte 1 — Conducta del agente** (evidencia, acciones que exigen permiso, git, CI, idioma, automatizar lo repetido)
- **Parte 2 — Ciclo de vida por etapas** (0 Alcance · 1 Scaffold · 2 Implementación · 3 Verificación · 4 Documentación · 5 PR y CI · 6 Release · 7 Post-release · 8 Auditoría)
- **Parte 3 — Plantillas canónicas** (estructura, `pyproject.toml`, `__init__.py`, Makefile, hooks, CI, publicación, scripts, tests, docs, CLAUDE.md…)
- **Parte 4 — Diseño de API, validación y numérica**
- **Parte 5 — Estrategia de pruebas**
- **Parte 6 — Release y PyPI** (flujo, errores, qué no hacer)
- **Parte 7 — Mantenimiento y seguridad**
- **Parte 8 — Auditoría, scorecard y retrospectiva**
- **Parte 9 — Catálogo de errores** (clases `C-nn` y tabla operativa)
- **Parte 10 — Anexos** (checklists, comandos, límites de este documento)

---

# Parte 0 — Cómo usar y qué garantiza este documento

## 0.1 Objetivo
Dejar que un agente de IA (y las personas que lo supervisan) lleve una librería Python desde la idea hasta PyPI y su mantenimiento, **con evidencia en cada etapa**
y sin repetir los errores ya cometidos. Cada regla tiene un origen (un fallo real) y, cuando es posible, una comprobación automática.

## 0.2 Principio rector
> Una regla que no se puede comprobar es una opinión; una regla que nadie probó contra el repo puede ser falsa; una cifra que no se recalculó no es un dato.
> **El comando es la fuente de verdad, no la memoria ni la documentación.**

## 0.3 Qué se probó de este documento
Las plantillas de la Parte 3 (Makefile, hooks, `settings.json`, scripts, `test_version`, `test_readme`, `test_idioma`, `test_trazabilidad`, `release-check`, `notas-release`) se
generaron en un proyecto de juguete (`milib`) a partir de este mismo texto y se ejecutaron: `make check-fast`, `make build`, `make release-check` con tag correcto e incorrecto,
y los hooks `SessionStart` y `Stop` (con y sin fallo inyectado). El resultado está en el Anexo 10.4. Lo que **no** se pudo probar (publicación real en PyPI/TestPyPI,
protección de ramas, `attestations`) está marcado «NO VERIFICADO» donde aparece.

## 0.4 Qué hacer cuando algo de este documento no encaja
Si el proyecto ya tiene convenciones distintas (idioma, gestor de entornos, layout), **respeta las del proyecto** y registra la desviación en `CLAUDE.md`. Si el proyecto
incumple una regla de este documento, **no la declares «no negociable»**: regístrala como deuda técnica con su evidencia.

## 0.5 Resumen operativo (lo esencial en 20 reglas)
1. **Evidencia:** ejecuta, mide y reporta lo real (✅/‼️), incluidos los fallos; lo no verificado es «NO VERIFICADO». Recalcula cada cifra.
2. **Permiso:** tag, release, PR, merge, push a otra rama, `--force` y cambios de workflows solo si la persona lo pide (con diff y `--force-with-lease` verificado).
3. **Idioma:** el del repo (si no es evidente, pregunta una vez); texto visible traducido, identificadores y claves de datos en inglés; el idioma tiene un test.
4. **Scaffold primero:** Makefile + hooks + CI + `py.typed` + tests base **antes** de la primera función. `make check` es la definición de «terminado».
5. **Un comando por gate:** el Makefile es la única definición; CI, publicación, docs y PR lo invocan.
6. **Versión en un solo sitio:** literal `__version__` en `__init__.py` + `[tool.setuptools.dynamic]`; **nunca** `importlib.metadata` en `__init__.py`; tras subirla, `make install`.
7. **Release:** consulta PyPI (`pip index versions`) → sube la versión → `make check` → `make release-check TAG=vX.Y.Z` → merge → **recién entonces** tag/release (lo crea la persona).
8. **Validación central:** todo argumento numérico pasa por `_utils.py`; **`isfinite` antes de comparar**; `bool` no es número; entrada vacía → `ValueError`; cotas `MAX_*`; registros validados; nada se recorta ni se fusiona en silencio.
9. **Referencia independiente:** cada resultado numérico se contrasta con una fuente externa, nunca con el propio código; caso a escala 10×; complejidad medida.
10. **Contrato de entradas** sobre todo `__all__` desde el día 1.
11. **Documentación ejecutable:** README y doctests son tests; `__all__` ↔ docs; `sphinx -W`; `examples/` se ejecutan.
12. **Cobertura por módulo:** global ≥ 85 % y ningún módulo < 70 %.
13. **Todo bug corregido deja tres huellas:** test que **falla en el tag anterior** (`make regresion`), ficha en el catálogo y, si es transferible, regla/playbook. Comprueba con mutación de una línea.
14. **No contaminar estado global:** gráficas sin tocar `rcParams` (test para todas); sin `except Exception` que oculte errores.
15. **Git:** ramas desde `origin/main` recién traído (`git fetch origin +refs/heads/main:refs/remotes/origin/main`); tras un *squash*, reiniciar la rama.
16. **CI:** lee el log completo; no cambies versiones de acciones «por intuición»; un re-run como máximo; limita la memoria al ejecutar código antiguo.
17. **Repeticiones → automatización:** si la persona pide lo mismo dos veces (changelog, «¿qué falta?», «¿docs al día?»), conviértelo en un comando.
18. **Reglas probadas:** cada regla de `CLAUDE.md` se ejecuta contra el repo y lleva etiqueta `[test]`/`[CI]`/`[comando]`/`[guía]`; si el repo la incumple es deuda, no «no negociable».
19. **Contradicciones:** busca activamente discrepancias entre docs, tests y código (comandos duplicados, cifras copiadas, reglas que el código no cumple).
20. **Auditoría:** scorecard de 14 dimensiones con criterio explícito para el 4 y media recalculada por un test; ante empate de la más rezagada, desempata por impacto observado.

---

# Parte 1 — Conducta del agente

## 1.1 Evidencia antes que afirmaciones
1. **Nada de suposiciones.** Lo no verificado se escribe «NO VERIFICADO». Separa **HECHO** (salida de un comando, contenido de un archivo, commit) de **INFERENCIA** y de **RECOMENDACIÓN**.
2. **Ejecuta y reporta resultados reales, incluidos los fallos.** Nunca resumas «todo pasa» sin haberlo corrido. Si algo se omitió, dilo.
3. **Recalcula cada cifra antes de escribirla** (`pytest`, `pip index versions`, `git ls-remote --tags`, `coverage`). Una cifra copiada de un documento anterior es la fuente de contradicciones
   (ejemplos reales: «0.2.4 se publicó» —no existía en PyPI—; «Versionado 4/5» con un tag ausente; «walopy 0.2.8» en una página medida con 0.3.0).
4. **Prueba cada regla y cada hook antes de adoptarlo**, ejecutándolo contra el repo: debe *pasar* en el estado actual y *señalar* el problema cuando se introduce (control negativo).
5. **Un test de regresión que no falla sin el arreglo no protege nada.** Comprueba contra la versión anterior y con una mutación de una línea (§5.4).
6. **Confirma la intención con un ejemplo** antes de implementar algo ambiguo (un error de especificación —«el árbol era de ROI, no de costos»— costó un rediseño).
7. **No hagas afirmaciones sobre servicios externos sin consultarlos** (PyPI: `pip index versions <paquete>`; GitHub: API/logs). Si no hay acceso, di «NO VERIFICADO».

## 1.2 Acciones que exigen petición explícita de la persona responsable
| Acción | Regla |
|---|---|
| Crear tag, release de GitHub, publicar en PyPI/TestPyPI | Solo si lo pide. Si el entorno no puede hacerlo (p. ej. sesiones web), entrega el comando/pasos y `make release-check` en verde. |
| Abrir un PR, hacer merge, borrar ramas | Solo si lo pide. «Haz el merge» autoriza ese merge, no el siguiente. Si pide «merge cuando el CI esté en verde», **verifica el CI del último commit** antes. |
| Push a una rama distinta de la asignada | Nunca sin permiso. |
| `git push --force` | Solo `--force-with-lease=<rama>:<sha-esperado>` y únicamente tras comprobar que el contenido remoto ya está fusionado (`git diff <remoto> <main>` vacío). |
| Cambiar workflows de CI/publicación | Muéstrale el diff. Si el cambio es consecuencia inevitable de otro (p. ej. versión dinámica), aíslalo en su propio commit. |
| Modificar `src/` durante una auditoría | Dile **qué y por qué** antes; si es un bug, repórtalo con su ficha en lugar de arreglarlo en silencio. Excepción: lo que la persona pidió explícitamente. |
| Cambiar la versión de una acción de GitHub | Nunca «por intuición»: verifica en los logs del CI qué versión usa y si funciona. (Un aviso de «Node.js 20 deprecated» es informativo; los jobs pasan.) |
| Saltar, deshabilitar o poner en cuarentena un test; commit vacío; cerrar y reabrir un PR para «reiniciar» el CI | Nunca. |

## 1.3 Idioma y comunicación
- Usa el idioma que ya use el repo (docstrings, mensajes, README, CHANGELOG, commits). Si no es evidente, **pregunta una vez** y regístralo en `CLAUDE.md`. Con el español fijado: todo texto que ve la persona usuaria
  (mensajes de error y avisos, docstrings, cabeceras de tablas, etiquetas de `summary()`, textos de gráficas, README, CHANGELOG, commits) va en español; **identificadores y claves de datos en inglés**.
- Distingue **claves de datos** (parte del contrato; no se traducen: `items[i]["class"]`) de **cabeceras de presentación** (`.rename(columns=…)` en `to_frame()`).
- Un reemplazo masivo (glosario) jamás se aplica a todo el árbol sin revisar el diff y correr la suite entera después de cada paso (cambió una clave de datos y un valor de ejemplo).
- Respuestas finales: breves, con lo medido (✅/‼️ una por una), las contradicciones halladas y lo no verificado.

## 1.4 Convierte lo que la persona repite en automatización
Minar las sesiones previas (`~/.claude/projects/<ruta>/*.jsonl`) antes de empezar; si no hay, dilo. En walopy las peticiones repetidas fueron:

| Petición repetida | Veces | Automatización |
|---|---|---|
| «Dame el changelog / el cuerpo del release» | 7 | `make notas-release VERSION=X.Y.Z` |
| «¿Qué falta?» / «¿Está todo listo?» | 8 | `make check` (estado real en una orden) |
| «¿La documentación está actualizada?» | 4 | tests de docs dentro de `make check` |
| «La versión vX ya está ocupada» | 2 | `pip index versions` antes de elegir versión + `make release-check` |
| «Falló el release» (logs truncados) | 6 | guarda de versión en `publish.yml`; ensayo en TestPyPI; leer el log **completo** |

## 1.5 Cuando falla el CI
1. Lee el log completo del job (no el resumen). Distingue: **fallo de este cambio** (arréglalo y empuja), **fallo de infraestructura** (el runner murió antes de ejecutar nada) y **fallo preexistente en la base**.
2. Un fallo «flaky» no es una causa raíz. Re-ejecuta un job a lo sumo una vez, solo si murió antes de correr tests; si falla de nuevo, es real.
3. Si el job ejecuta **código antiguo sin cotas** (p. ej. un test contra el tag anterior) puede agotar la memoria del runner (señal 143 / «runner received a shutdown signal»): limita la memoria del hijo (`RLIMIT_AS`, §3.8).
4. Antes de empujar un arreglo: corre los comandos del CI en local, relee tu diff buscando qué haría que el CI lo rechace, y empuja una sola vez.
5. Cada commit puede ejecutar el CI **dos veces** si hay triggers `push` y `pull_request` a la vez; restringe `push` a `main` o usa `concurrency` (*propuesto, no probado*).

## 1.6 Git y ramas
- Trabaja en la rama asignada. **Cada rama parte de `origin/main` recién traído:**
  `git fetch origin +refs/heads/main:refs/remotes/origin/main` (un `git fetch origin main` a secas puede dejar `origin/main` desactualizado y llevó a crear ramas sobre una base vieja dos veces) y comprueba
  `git merge-base --is-ancestor origin/main HEAD` (código 0).
- Tras un merge *squash*, la rama del PR ya está fusionada: reiníciala desde `origin/main` (`git checkout -B <rama> origin/main`). El trabajo nuevo es un PR nuevo, nunca se apila sobre una rama fusionada.
- Commits: un cambio lógico por commit, mensaje en el idioma del repo, con los *trailers* de atribución que indique el entorno. Workflows en commit aparte.
- Antes de mergear: CI en verde **en el último commit**, sin conflictos. Merge por *squash* si el repo lo usa.
- Tras abrir un PR, suscríbete a su actividad y atiende CI/revisiones hasta que se fusione o cierre; no sondees con `sleep`.

## 1.7 Cuándo preguntar
Pregunta solo lo que es de la persona: alcance (qué módulos **no** hacer: «ya existe otra librería»), idioma, cambios que rompen compatibilidad, nombre en PyPI, publicar o no.
Todo lo demás se decide con el convenio del repo y se anota. Registra cada decisión como `D-n` con su respuesta (p. ej. D-6: «traducir también columnas y etiquetas; romper compatibilidad en 0.3.0»).

## 1.8 Entornos de ejecución (Claude Code en la web y similares)
- Trabaja en la **rama asignada**; no abras PR, tag ni release salvo petición (en sesiones web el agente **no puede crear releases**: entrega el comando y `make release-check` en verde).
- Las herramientas de GitHub (MCP/`gh api`) sustituyen a la CLI `gh` cuando no está instalada; las notificaciones de un PR suscrito llegan como eventos, no se sondea.
- `CLAUDE_CODE_REMOTE=true` ya vale `true` en la sesión: para probar el comportamiento «local» de un hook usa `env -u CLAUDE_CODE_REMOTE`.
- Usa el directorio temporal de la sesión para scripts y venvs de prueba; no ensucies el repo con ellos.
- El contenedor es efímero: lo que importa se commitea y empuja a la rama asignada.

---

# Parte 2 — Ciclo de vida por etapas

Cada etapa tiene **entrada → acciones → salida (gate)**. No pases a la siguiente sin cumplir el gate.

## Etapa 0 — Descubrimiento y alcance
- **Entrada:** la idea de la persona.
- **Acciones:** acotar el dominio y lo que **no** entra (librerías ya existentes); decidir idioma de docs y mensajes; elegir `nombre-en-pypi` y comprobar que está libre
  (`pip index versions nombre` → «no matching distribution»; también https://pypi.org/project/nombre/); fijar versión mínima de Python (≥ 3.9 salvo razón en contra); listar usuarios objetivo.
  Confirmar la **intención con un ejemplo concreto** de entrada y salida de la primera función.
- **Salida:** `CLAUDE.md` inicial con descripción, alcance, exclusiones, idioma y decisiones `D-n`.
- **Error típico:** implementar algo distinto de lo que se quería (H-01: árbol de costos en vez de ROI).

## Etapa 1 — Scaffold e infraestructura para agentes (antes de la primera función)
- **Acciones (en este orden):** estructura `src/` (§3.1) → `pyproject.toml` (§3.2) → `__init__.py` con `__version__` literal (§3.3) → `Makefile` (§3.4) → `.claude/settings.json` + hooks (§3.5) →
  CI y publicación (§3.6) → scripts (§3.7) → tests base (`conftest`, `test_version`, contrato, docs) (§3.8) → `CLAUDE.md`, `AGENTS.md`, plantilla de PR, CODEOWNERS (§3.10) → `.gitignore`.
  Después `make install && make check`.
- **Salida (gate):** `make check` termina con código 0 sobre el esqueleto; los hooks están probados; el wheel contiene `py.typed`; `make release-check TAG=v0.1.0` correcto.
- **Error típico:** dejar los gates «para después» → llegar a v0.2.8 con CI verde y 215 errores de ruff, 78 de mypy y 80 % de cobertura.

## Etapa 2 — Implementación de funcionalidad
Para **cada función pública nueva**:
1. Diseña la API (§4): entradas array-like, validación central, objeto de resultado, `to_frame()`/`summary()`, `plot()` perezoso.
2. Escribe primero el **test contra una referencia independiente** (publicación, cálculo manual, otra librería, fuerza bruta, simulación con ≥ 20 semillas), nunca contra el propio código.
3. Añade tests de casos borde (§5.2) y súmala a la tabla del **test de contrato**.
4. Implementa. Si anuncias una complejidad, mídela (§4.3 y §5.1).
5. Docstring completo (Parameters/Returns/Raises/Examples con doctest ejecutable), entrada en `__all__`, README, referencia Sphinx, CHANGELOG.
6. `make check-fast` (el hook `Stop` lo hace por ti si hay cambios).
- **Salida:** `make check` en verde. **Errores típicos:** validar solo parte de las rutas (C-14), NaN que pasa las comparaciones (C-09), tamaños sin cota (C-18).

## Etapa 3 — Verificación de calidad (gates)
Todos son jobs del CI **y** objetivos de `make` (§3.4). Gate = `make check` con código 0:
`lint` (el comando del CI, sin inventar un `--select` más estricto que falle en el repo) · `types` · `test` (incluye doctests, README y ejemplos) · `cov` (**global ≥ 85 % y ningún módulo público < 70 %**, por módulo) ·
`build` (`python -m build` + `twine check`) · `docs` (`sphinx -W`) · `examples` (se ejecutan) · `obsoletas` (grep del nombre antiguo, incluyendo `examples/`, CI y `LICENSE`) · `regresion` (los tests de bugs fallan en el tag anterior).
- Si ya hay módulos por debajo del mínimo, trátalos como **trinquete** (no pueden bajar) y regístralos como deuda; no declares la regla «no negociable» sobre un repo que ya la incumple.
- Un 90 % global puede esconder un módulo al 19 %: comprueba **por módulo**.

## Etapa 4 — Documentación
README con ejemplos que **se ejecutan como tests**; Sphinx con `-W`; un símbolo = una directiva autodoc canónica (§3.9); `CHANGELOG.md` con «Cambios que rompen compatibilidad»;
`CLAUDE.md` con el estado **medido** y los comandos reales; ejemplos en `examples/` ejecutados en CI. Gate: `make docs examples` + tests de documentación en verde.
Cada vez que la persona pregunta «¿está actualizada la documentación?», la respuesta es la salida de esos comandos, no una opinión.

## Etapa 5 — Pull request y CI
Rama desde `origin/main` (§1.6) → commits lógicos → `make check` en local → push → PR con la plantilla (§3.10) → suscripción a su actividad → arreglar CI/revisiones hasta verde →
merge **solo si lo pide**. Un fallo de CI es trabajo propio mientras el PR sea tuyo (§1.5).

## Etapa 6 — Release (ver Parte 6)
Elegir versión **comprobando PyPI** → subirla en **un solo sitio** (`__version__`) → CHANGELOG → `make install && make check` → `make release-check TAG=vX.Y.Z` → PR/merge → **tag y release después de que la versión
esté en `main`** (lo hace la persona si el entorno no puede) → `publish.yml` verifica y publica → comprobar `pip install nombre==X.Y.Z` en un venv limpio.

## Etapa 7 — Post-release y mantenimiento (ver Parte 7)
Verificar la instalación limpia; abrir deuda con lo pendiente; prueba semanal con las últimas dependencias; auditoría de dependencias; responder issues; política de deprecación.

## Etapa 8 — Auditoría y retrospectiva (cada 3–5 releases o antes de un 1.0)
Procedimiento de la Parte 8: línea base → fichas de bugs → scorecard con criterio explícito → reglas probadas → entregables. Produce `docs/retrospectiva/` y alimenta este documento.

---

# Parte 3 — Plantillas canónicas

> Los bloques **(probado)** vienen de archivos que corren en walopy y se regeneraron en el proyecto de juguete. Sustituye `milib` y `nombre-en-pypi`.

## 3.1 Estructura del repositorio

```
mi-libreria/
├── src/milib/
│   ├── __init__.py          # API pública (__all__) + __version__ literal (ÚNICA fuente de la versión)
│   ├── py.typed             # marcador PEP 561 (vacío) — debe estar en el wheel
│   ├── _utils.py            # validadores centrales y cotas de tamaño
│   └── modulo_a.py …
├── tests/
│   ├── conftest.py
│   ├── test_utils.py · test_version.py · test_contrato_entradas.py · test_readme.py · test_documentacion.py
│   ├── test_idioma.py · test_trazabilidad.py · test_ejemplos.py · test_complejidad.py
│   ├── regresiones.json     # manifiesto bug → tests que deben fallar en el tag anterior
│   └── test_<modulo>.py …
├── docs/
│   ├── source/ (conf.py, index.md, inicio_rapido.md, instalacion.md, changelog.md, rendimiento.md, referencia/*.rst)
│   ├── referencia/BUG_CATALOG.md · PLAYBOOK.md       # catálogo de bugs y checklist de madurez
│   └── retrospectiva/ (LESSONS_LEARNED, BUG_CATALOG, SCORECARD, PLAYBOOK, CLAUDE_MD_RULES, RESUMEN_EJECUTIVO)
├── examples/ (scripts ejecutables)      ├── benchmarks/ (semillas fijas)
├── scripts/ (comprobar_*.py, verificar_*.py, notas_release.py)
├── .claude/ (settings.json, hooks/session-start.sh, hooks/verify-before-stop.sh)
├── .github/ (workflows/ci.yml, workflows/publish.yml, PULL_REQUEST_TEMPLATE.md, ISSUE_TEMPLATE/, CODEOWNERS)
├── Makefile · pyproject.toml · README.md · CHANGELOG.md · CONTRIBUTING.md · SECURITY.md · CODE_OF_CONDUCT.md · LICENSE
└── CLAUDE.md · AGENTS.md · .gitignore
```

`.gitignore` mínimo: `__pycache__/ *.py[cod] *.egg-info/ dist/ build/ .eggs/ .mypy_cache/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage .coverage.* coverage.json docs/build/ docs/_build/ .venv/ venv/ .tox/ .nox/ .DS_Store`.
Comprueba: `git check-ignore -v dist/x docs/_build/x .coverage .venv/x`.

## 3.2 `pyproject.toml` canónico *(probado)*

```toml
[build-system]
requires = ["setuptools>=77.0.3", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "nombre-en-pypi"
dynamic = ["version"]                 # la versión vive SOLO en src/milib/__init__.py
description = "Una línea descriptiva"
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
license-files = ["LICENSE"]           # PEP 639; NO añadir el classifier de licencia (setuptools ≥ 77 los trata como incompatibles)
authors = [{ name = "TuNombre", email = "tu@email.com" }]
keywords = ["palabra1", "palabra2"]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Typing :: Typed",
]
dependencies = ["numpy>=1.22", "pandas>=1.4"]     # cotas INFERIORES probadas; sin cota superior salvo causa documentada

[project.optional-dependencies]
dev     = ["pytest>=7", "pytest-cov>=4", "pytest-timeout>=2", "ruff~=0.16.10", "mypy>=1.10,<3"]   # ruff con compatible-release: el lint no cambia solo
release = ["build", "twine", "pip-audit"]
docs    = ["sphinx>=7", "sphinx-rtd-theme>=2", "myst-parser>=2"]

[project.urls]
Homepage  = "https://github.com/Usuario/nombre-repo"
Issues    = "https://github.com/Usuario/nombre-repo/issues"
Changelog = "https://github.com/Usuario/nombre-repo/blob/main/CHANGELOG.md"

[tool.setuptools.dynamic]
version = {attr = "milib.__version__"}            # setuptools lee el literal sin importar el paquete

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
milib = ["py.typed"]

[tool.pytest.ini_options]
testpaths = ["tests", "src/milib"]                # src/milib: los doctests de los docstrings
addopts   = "-q --doctest-modules --import-mode=importlib"   # importlib: evita que un egg-info viejo en src/ falsee la versión
filterwarnings = [
    "error",                                      # un warning inesperado es un fallo
    # "ignore:<patrón de un aviso de TERCEROS>:DeprecationWarning",   # solo avisos ajenos, uno a uno y comentados
]

[tool.mypy]
ignore_missing_imports = true

[tool.ruff]
line-length    = 110
target-version = "py39"

[tool.ruff.lint]
select = ["F", "E9", "B", "I", "S"]               # bugs reales + imports + seguridad; el MISMO conjunto en CI, Makefile y publicación

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S311"]
"benchmarks/*" = ["S311"]

[tool.coverage.run]
source = ["milib"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

**Reglas críticas:**
- **La versión no se duplica.** `version` **no** está en `[project]`; es `dynamic` y se lee del literal de `__init__.py`. Dos copias («`__version__` debe coincidir con `version`») terminan desincronizadas.
- **Nunca `importlib.metadata.version()` en `__init__.py`:** los metadatos se escriben al instalar y no se refrescan; tras subir la versión, `__version__` sigue mostrando la anterior hasta reinstalar (reproducido; fue la causa de varias contradicciones). Tras subir la versión: `make install`.
- Los nombres de archivo de PyPI son **permanentes**: una vez subido `milib-0.1.0-py3-none-any.whl`, ese nombre queda bloqueado aunque se borre la release. La única salida es una versión nueva.
- `ruff` y `mypy` fijados con *compatible release* (`~=`, `<3`) para que el lint no cambie sin un commit.
- `filterwarnings = error` desde el primer día; los avisos de terceros se ignoran uno a uno y comentados.

## 3.3 `src/milib/__init__.py` canónico *(probado)*

```python
"""milib — descripción corta."""
from __future__ import annotations

from .modulo_a import ClaseA, funcion_a
from .modulo_b import ClaseB, funcion_b

__version__ = "0.1.0"  # fuente única de la versión; pyproject.toml la lee con [tool.setuptools.dynamic]

__all__ = ["ClaseA", "ClaseB", "funcion_a", "funcion_b"]
```
Imports internos siempre relativos (`from .modulo import X`). Todo símbolo de `__all__` se documenta (README + Sphinx) y entra en el test de contrato.

## 3.4 `Makefile` *(probado)* — única definición de cada gate
El CI, la documentación, los hooks y la plantilla de PR **invocan o copian literalmente** estos comandos. En walopy el mismo `ruff check` llegó a escribirse de **cuatro** formas distintas
(CI, publicación, plantilla de PR, «definición de terminado») y un cambio en `scripts/` pasaba el release y rompía el CI.

```makefile
# milib — comandos de verificación (los mismos que ejecuta el CI).
# `make check-fast` para iterar; `make check` antes de abrir un PR; `make release-check TAG=vX.Y.Z` antes de crear un tag.
PYTHON ?= python
MINIMO_COBERTURA_MODULO ?= 70

.PHONY: help install test cov lint types build docs examples obsoletas regresion mutaciones notas-release check-fast check release-check clean

help:
	@echo "Objetivos: install test cov lint types build docs examples obsoletas regresion mutaciones notas-release VERSION=X.Y.Z check-fast check release-check TAG=vX.Y.Z clean"

install:
	$(PYTHON) -m pip install -e ".[dev,release,docs]"

test:
	$(PYTHON) -m pytest

cov:
	$(PYTHON) -m pytest --cov=milib --cov-report=term-missing --cov-report=json
	$(PYTHON) scripts/comprobar_cobertura_modulos.py $(MINIMO_COBERTURA_MODULO)

lint:
	$(PYTHON) -m ruff check $(wildcard src tests benchmarks scripts examples)

types:
	$(PYTHON) -m mypy src/milib --ignore-missing-imports

build:
	rm -rf dist build
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

docs:
	$(PYTHON) -m sphinx -b html -W docs/source docs/build

examples:
	@for f in examples/*.py; do echo "== $$f"; MPLBACKEND=Agg PYTHONWARNINGS=error $(PYTHON) $$f > /dev/null || exit 1; done

obsoletas:
	@if grep -rn "PLACEHOLDER\|TU_USUARIO\|NOMBRE_ANTIGUO" . --include="*.py" --include="*.md" --include="*.toml" --include="*.yml" --exclude=CLAUDE.md --exclude=AGENTS.md --exclude-dir=.git --exclude-dir=.github --exclude-dir=auditoria --exclude-dir=referencia --exclude-dir=retrospectiva --exclude-dir=.claude --exclude-dir=build --exclude-dir=dist --exclude-dir=.venv; then echo "Se encontraron referencias obsoletas"; exit 1; else echo "Sin referencias obsoletas"; fi

# Los tests de regresión deben FALLAR en el tag anterior (necesita los tags de git).
regresion:
	@if git describe --tags --abbrev=0 > /dev/null 2>&1; then $(PYTHON) scripts/verificar_regresion.py --manifiesto tests/regresiones.json; else echo "OMITIDO: no hay tags de git (git fetch --tags)"; fi

# Mutación de una línea: cada test de regresión debe fallar si el bug vuelve.
mutaciones:
	$(PYTHON) scripts/verificar_mutaciones.py

check-fast: lint types test

check: lint types cov build docs examples obsoletas regresion

# Cuerpo del release a partir del CHANGELOG: make notas-release VERSION=0.3.0
notas-release:
	@test -n "$(VERSION)" || { echo "Uso: make notas-release VERSION=X.Y.Z"; exit 2; }
	@$(PYTHON) scripts/notas_release.py $(VERSION)

# El wheel construido debe tener la versión del tag: make release-check TAG=v0.3.0
release-check:
	@test -n "$(TAG)" || { echo "Uso: make release-check TAG=vX.Y.Z"; exit 2; }
	rm -rf dist build
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*
	$(PYTHON) scripts/comprobar_version_release.py $(TAG) dist

clean:
	rm -rf dist build docs/build .coverage coverage.json .pytest_cache .mypy_cache .ruff_cache
```

## 3.5 Permisos y hooks para agentes (`.claude/`) *(probado)*

`.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(make:*)",
      "Bash(python -m pytest:*)",
      "Bash(pytest:*)",
      "Bash(python -m ruff:*)",
      "Bash(ruff:*)",
      "Bash(python -m mypy:*)",
      "Bash(mypy:*)",
      "Bash(python -m build:*)",
      "Bash(python -m twine:*)",
      "Bash(python -m sphinx:*)",
      "Bash(sphinx-build:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)"
    ]
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/verify-before-stop.sh" }
        ]
      }
    ]
  }
}
```

`.claude/hooks/session-start.sh` — solo en entornos remotos (`CLAUDE_CODE_REMOTE=true`), síncrono, idempotente, sin preguntas:
```bash
#!/bin/bash
# SessionStart: prepara el entorno en Claude Code en la web. Síncrono, idempotente y sin preguntas.
# En local (CLAUDE_CODE_REMOTE distinto de "true") no hace nada.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PYTHON="${PYTHON:-python}"

# Instalación editable con extras de desarrollo, release y docs (instala solo lo que falte; repetirla es inocuo).
"$PYTHON" -m pip install --quiet --disable-pip-version-check -e ".[dev,release,docs]"

# `make regresion` necesita los tags de git; si no hay red no es un error de la sesión.
git fetch --tags --quiet origin 2>/dev/null || true

# Gráficas sin pantalla para todos los comandos de la sesión.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export MPLBACKEND=Agg' >> "$CLAUDE_ENV_FILE"
fi

echo "milib listo: $("$PYTHON" -c 'import milib; print(milib.__version__)')"
```

`.claude/hooks/verify-before-stop.sh` — corre `make check-fast` si hay cambios en código; si falla devuelve el error con **exit 2**; con `stop_hook_active=true` sale con 0 (evita bucles); sin cambios no corre nada:
```bash
#!/bin/bash
# Stop: si la sesión cambió código, tests o configuración, corre `make check-fast` y, si falla, devuelve el error
# al agente (exit 2) para que lo corrija antes de terminar.
# - stop_hook_active=true en la entrada → exit 0 (evita bucles).
# - Sin cambios en código/tests/pyproject → no ejecuta nada.
set -uo pipefail

PYTHON="${PYTHON:-python}"
ENTRADA="$(cat || true)"

ACTIVO="$(printf '%s' "$ENTRADA" | "$PYTHON" -c 'import json,sys
try:
    print("1" if json.load(sys.stdin).get("stop_hook_active") else "0")
except Exception:
    print("0")' 2>/dev/null || echo 0)"
if [ "$ACTIVO" = "1" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}" || exit 0
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || exit 0

# Cambios sin confirmar (incluye archivos nuevos) en código, tests, scripts, ejemplos, benchmarks o pyproject.
if ! git status --porcelain | grep -qE '^.. "?(src/|tests/|scripts/|examples/|benchmarks/|pyproject\.toml|Makefile)'; then
  exit 0
fi

command -v make > /dev/null 2>&1 || exit 0

SALIDA="$(make check-fast PYTHON="$PYTHON" 2>&1)"
ESTADO=$?
if [ "$ESTADO" -ne 0 ]; then
  {
    echo "make check-fast falló (código $ESTADO). Corrige el error antes de terminar:"
    echo
    printf '%s\n' "$SALIDA" | tail -n 60
  } >&2
  exit 2
fi
exit 0
```
`chmod +x .claude/hooks/*.sh`. **Prueba obligatoria de los hooks** (así se probaron):
1. `CLAUDE_CODE_REMOTE=true .claude/hooks/session-start.sh` → exit 0 y repetido también. *En una sesión web esa variable ya vale `true`; para probar el salto local usa `env -u CLAUDE_CODE_REMOTE` (exit 0 en milisegundos, sin salida).*
2. `python -m json.tool .claude/settings.json` → válido.
3. Stop, **en una copia del repo** (`cp -r`; haz commit de la copia para partir de árbol limpio): árbol limpio → exit 0 y `make` no se ejecuta (verifícalo con un `make` espía en el `PATH`); solo docs cambiados → no corre;
   cambio válido → corre y pasa; `import os` sin usar inyectado → **exit 2** con el error de ruff; test roto → exit 2 con el fallo de pytest; el mismo fallo con `{"stop_hook_active": true}` en stdin → exit 0 y no corre.

## 3.6 CI (`.github/workflows/ci.yml`) *(probado en walopy)*
Jobs: tests en **todas** las versiones de `classifiers` (`fail-fast: false`), mínimos de dependencias, calidad (ruff + mypy), cobertura (global y por módulo), regresión (`fetch-depth: 0`),
paquete (build + `twine check` + instalación de la rueda en un venv limpio + `py.typed` + obsoletas), docs (`sphinx -W`), auditoría de dependencias (`pip-audit`), últimas dependencias y benchmarks (programados).
Adapta las versiones mínimas del job `minimos` a las cotas inferiores de `pyproject.toml`.

```yaml
name: CI

on:
  push:
    branches: ["main", "claude/**", "feat/**", "fix/**"]
  pull_request:
    branches: ["main"]
  schedule:
    - cron: "17 5 * * 1"   # cada lunes: prueba contra las últimas versiones de las dependencias
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test:
    name: Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Instalar dependencias
        run: pip install -e ".[dev]"

      - name: Ejecutar tests
        run: pytest tests/ -q --tb=short

  minimos:
    name: Tests con dependencias mínimas (Python 3.9)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: Instalar versiones mínimas declaradas
        run: |
          pip install "numpy==1.22.0" "pandas==1.4.0" "matplotlib==3.5.0" "plotly==5.0.0" "pytest>=7" "pytest-cov>=4"
          pip install --no-deps -e .

      - name: Ejecutar tests
        run: pytest tests/ -q --tb=short

  calidad:
    name: Linter y tipos
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[dev]"

      - name: ruff
        run: make lint

      - name: mypy
        run: make types

  cobertura:
    name: Cobertura
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[dev]"

      - name: Cobertura global (mínimo 85 % en pyproject.toml)
        run: pytest --cov=milib --cov-report=term-missing --cov-report=json -q

      - name: Cobertura por módulo (mínimo 70 %)
        run: python scripts/comprobar_cobertura_modulos.py 70

  regresion:
    name: Los tests de regresión fallan en la versión anterior
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # necesita los tags para crear el worktree de la referencia

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[dev]"

      - name: verificar_regresion.py (manifiesto tests/regresiones.json)
        run: python scripts/verificar_regresion.py --manifiesto tests/regresiones.json --segundos 300

  paquete:
    name: Build y metadatos
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[release]"

      - name: Construir
        run: python -m build

      - name: Verificar metadatos
        run: twine check dist/*

      - name: Instalar la rueda en un entorno limpio
        run: |
          python -m venv /tmp/limpio
          /tmp/limpio/bin/pip install dist/*.whl
          cd /tmp && /tmp/limpio/bin/python -c "import milib, importlib.metadata as m; assert milib.__version__ == m.version('nombre-en-pypi'); print(milib.__version__)"
          test -f "$(/tmp/limpio/bin/python -c 'import milib, os; print(os.path.dirname(milib.__file__))')/py.typed"

      - name: Sin referencias obsoletas
        run: |
          if grep -rn "PLACEHOLDER\|TU_USUARIO\|NOMBRE_ANTIGUO" . --include="*.py" --include="*.md" --include="*.toml" --include="*.yml" --exclude=CLAUDE.md --exclude-dir=.git --exclude-dir=.github --exclude-dir=auditoria --exclude-dir=referencia --exclude-dir=retrospectiva --exclude=AGENTS.md; then
            echo "Se encontraron referencias obsoletas"; exit 1
          fi

  docs:
    name: Documentación (Sphinx -W)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[docs]"

      - name: Construir documentación
        run: sphinx-build -b html -W docs/source docs/build

  auditoria:
    name: Auditoría de dependencias
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install pip-audit

      - name: pip-audit de las dependencias del proyecto
        run: pip-audit .

  ultimas-versiones:
    name: Tests con las últimas dependencias
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - run: pip install --upgrade -e ".[dev]"

      - run: pytest tests/ -q --tb=short

  benchmarks:
    name: Benchmarks (informativo)
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e .

      - name: Medir
        run: python benchmarks/bench_core.py
```

## 3.7 Publicación (`.github/workflows/publish.yml`) *(probado en walopy; la guarda de versión solo en local)*
El job de publicación **repite tests y lint**, construye, ejecuta `twine check` y **comprueba que el wheel tiene la versión del tag** (`GITHUB_REF_NAME`) antes de subir. Respeta el trigger real (`release: published`).

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  verificar:
    name: Verificar antes de publicar
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[dev,release]"

      - name: Tests
        run: pytest tests/ -q --tb=short

      - name: Linter y tipos
        run: make lint types

  build:
    name: Build distribution
    needs: verificar
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: python -m pip install --upgrade build twine
      - run: python -m build
      - run: twine check dist/*

      - name: El wheel construido tiene la versión del tag
        # release published: GITHUB_REF_NAME es el tag (vX.Y.Z); un tag creado antes de subir la versión
        # produciría artefactos antiguos y PyPI respondería 400 File exists.
        run: python scripts/comprobar_version_release.py "$GITHUB_REF_NAME" dist

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish-pypi:
    name: Publish to PyPI
    needs: build
    runs-on: ubuntu-latest

    environment:
      name: pypi
      url: https://pypi.org/project/nombre-en-pypi/

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish package
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          attestations: false
```

**Sobre `attestations`:** no lo cambies sin probarlo. En walopy el arreglo del release v0.2.7 fue añadir `attestations: false` sin ver el error real (logs truncados): causa **NO VERIFICADA**. Habilitarlo es deseable
(procedencia) pero debe ensayarse primero en TestPyPI (§3.7.1).

**Configuración en pypi.org (una sola vez):** `https://pypi.org/manage/project/nombre-en-pypi/settings/publishing/` → añadir *Trusted Publisher*:
Owner = usuario/organización de GitHub · Repository = repo · Workflow = `publish.yml` · Environment = `pypi`. En GitHub → Settings → Environments → crear `pypi`.
Para un proyecto aún no publicado, PyPI ofrece «pending publisher» (función de PyPI; no probada en walopy).

### 3.7.1 Ensayo de publicación en TestPyPI *(propuesto, no probado)*
Los incidentes de release de walopy (v0.2.4 sin publicar, v0.2.2 «ocupada», v0.2.7 fallido) se debieron a configuración probada solo en producción. Un workflow manual evita tocar PyPI real:

```yaml
name: Ensayo en TestPyPI
on: workflow_dispatch
permissions: {contents: read, id-token: write}
jobs:
  ensayo:
    runs-on: ubuntu-latest
    environment: {name: testpypi, url: https://test.pypi.org/project/nombre-en-pypi/}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: python -m pip install build twine && python -m build && twine check dist/*
      - run: python scripts/comprobar_version_release.py "v$(python -c 'import milib; print(milib.__version__)')" dist
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          attestations: true
```
Requiere un *Trusted Publisher* propio en test.pypi.org y un `environment` `testpypi`. TestPyPI **también bloquea** nombres de archivo repetidos (comportamiento general de PyPI, no probado aquí): sube una versión de ensayo distinta (p. ej. `X.Y.Z.devN`) o usa `skip-existing: true`.

## 3.8 Scripts de verificación *(probados)*

`scripts/comprobar_cobertura_modulos.py` — falla si algún módulo está bajo el mínimo (un global alto puede esconder un módulo al 19 %):
```python
"""Falla si algún módulo de milib tiene una cobertura menor que el mínimo (por defecto 70 %).

Uso:  python -m pytest --cov=milib --cov-report=json -q && python scripts/comprobar_cobertura_modulos.py [minimo]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(minimo: float = 70.0, ruta: str = "coverage.json") -> int:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    bajos = {
        nombre: info["summary"]["percent_covered"]
        for nombre, info in datos["files"].items()
        if info["summary"]["percent_covered"] < minimo
    }
    for nombre, pct in sorted(bajos.items()):
        print(f"cobertura insuficiente: {nombre} = {pct:.1f} % (mínimo {minimo:g} %)")
    if not bajos:
        menor = min(i["summary"]["percent_covered"] for i in datos["files"].values())
        print(f"OK: todos los módulos >= {minimo:g} % (el menor tiene {menor:.1f} %)")
    return 1 if bajos else 0


if __name__ == "__main__":
    sys.exit(main(float(sys.argv[1]) if len(sys.argv) > 1 else 70.0))
```

`scripts/comprobar_version_release.py` — el wheel y el sdist deben tener la versión del tag (un tag creado antes de subir la versión produjo artefactos viejos y PyPI respondió `400 File exists`):
```python
"""Comprueba que la versión del wheel construido coincide con la del tag de release.

Uso::

    python scripts/comprobar_version_release.py v0.3.0 [directorio_dist]

Sale con código 0 si todos los artefactos de ``dist/`` (wheel y sdist) tienen la versión del tag y con 1 si no
coinciden o no hay artefactos. Un tag creado antes de subir la versión produce artefactos antiguos y PyPI
responde ``400 File exists``: esta comprobación lo detecta antes de publicar.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


def campo_del_wheel(ruta: Path, campo: str) -> str:
    with zipfile.ZipFile(ruta) as z:
        metadata = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
        m = re.search(rf"(?m)^{campo}: (\S+)$", z.read(metadata).decode("utf-8"))
    if m is None:
        raise ValueError(f"{ruta.name}: METADATA sin campo {campo}")
    return m.group(1)


def version_del_wheel(ruta: Path) -> str:
    return campo_del_wheel(ruta, "Version")


def main(tag: str, dist: str = "dist") -> int:
    esperada = tag[1:] if tag.startswith("v") else tag
    ruedas = sorted(Path(dist).glob("*.whl"))
    sdists = sorted(Path(dist).glob("*.tar.gz"))
    if not ruedas or not sdists:
        print(f"ERROR: faltan artefactos en {dist}/ (wheel: {len(ruedas)}, sdist: {len(sdists)}); ejecuta `python -m build`")
        return 1
    problemas = 0
    for rueda in ruedas:
        v = version_del_wheel(rueda)
        ok = v == esperada
        print(f"{'OK ' if ok else 'MAL'} {rueda.name}: versión {v} (tag {tag})")
        problemas += 0 if ok else 1
    for sdist in sdists:
        nombre = re.sub(r"[-_.]+", "_", campo_del_wheel(ruedas[0], "Name")).lower()
        ok = sdist.name == f"{nombre}-{esperada}.tar.gz"
        print(f"{'OK ' if ok else 'MAL'} {sdist.name} (se esperaba {nombre}-{esperada}.tar.gz)")
        problemas += 0 if ok else 1
    if problemas:
        print(f"ERROR: el tag {tag} no coincide con la versión construida; sube la versión en src/milib/__init__.py antes de crear el tag")
    return 1 if problemas else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:3]))
```

`scripts/notas_release.py` — imprime la sección del CHANGELOG para el cuerpo del release:
```python
"""Imprime las notas de un release a partir de ``CHANGELOG.md`` (la sección de esa versión).

Uso::

    python scripts/notas_release.py 0.3.0     # o v0.3.0
    make notas-release VERSION=0.3.0

Sale con código 1 si el CHANGELOG no tiene sección para esa versión.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def seccion(version: str, changelog: str) -> str | None:
    version = version[1:] if version.startswith("v") else version
    m = re.search(rf"(?ms)^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^---\s*$|^## \[|\Z)", changelog)
    return m.group(1).strip() if m else None


def main(version: str) -> int:
    texto = seccion(version, (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8"))
    if texto is None:
        print(f"ERROR: CHANGELOG.md no tiene una sección [{version}]", file=sys.stderr)
        return 1
    print(texto)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
```

`scripts/verificar_regresion.py` — ejecuta los tests **actuales** contra el código de un tag anterior (`git worktree`) y exige que los tests de cada bug **fallen**; los que pasan a propósito se declaran *guardas*.
Detalles aprendidos: ejecutar **sin `-x`** (resultado por test); quitar `match=` de `pytest.raises` en la copia de los tests (los mensajes cambian entre versiones y el test «fallaría» solo por el texto);
`ref` **por entrada** del manifiesto (si usara «el último tag», al publicar la versión con el arreglo todo pasaría); `pytest-timeout` para bloqueos; **límite de memoria** (`RLIMIT_AS`) porque el código antiguo no tiene cotas
y llegó a 7,7 GB matando al runner.
```python
"""Comprueba que los tests de regresión de un fix FALLAN contra una versión anterior del código.

Un test de regresión que también pasa sin el fix no protege nada. Este script crea un ``git worktree``
de la referencia indicada (por defecto el último tag), ejecuta los tests *actuales* contra el código
*de esa referencia* y muestra, por cada selector, si falló (detecta el bug), pasó (no lo detecta) o se
quedó colgado (también cuenta como detección).

Uso::

    python scripts/verificar_regresion.py [--ref v0.2.8] [--guardas FRAGMENTO ...] SEL [SEL ...]

``SEL`` es un selector de pytest (``tests/test_x.py::test_y`` o ``tests/test_x.py -k expresion``, entre comillas).
Sale con código 1 si algún test que no sea una guarda (``--guardas``) pasa en la referencia.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True  # noqa: S607
    ).stdout.strip()


def ultimo_tag() -> str:
    return _git("describe", "--tags", "--abbrev=0")


_MATCH = re.compile(r",\s*match=(?:r?\"[^\"\\n]*\"|r?'[^'\\n]*'|[A-Za-z_][\\w.]*)")


def copiar_tests_sin_match(destino: Path) -> Path:
    """Copia ``tests/`` quitando ``match=`` de ``pytest.raises``.

    Los mensajes de error cambiaron entre versiones (p. ej. al traducirlos): sin esto, un test fallaría
    en la referencia solo porque el texto de la excepción es distinto, no porque el bug esté presente.
    """
    nuevo = destino / "tests"
    shutil.copytree(RAIZ / "tests", nuevo, ignore=shutil.ignore_patterns("__pycache__"))
    for f in nuevo.glob("*.py"):
        f.write_text(_MATCH.sub("", f.read_text(encoding="utf-8")), encoding="utf-8")
    return nuevo


def _limitar_memoria(megabytes: int):
    """Devuelve una función para ``preexec_fn`` que limita el espacio de direcciones del proceso hijo.

    El código antiguo no tiene cotas de tamaño (ese es el bug): sin límite, ``monte_carlo_gg1(n=10**9)`` llega a
    7,7 GB y el sistema operativo mata el runner del CI. Con el límite falla con ``MemoryError`` (cuenta como detección).
    """
    def aplicar() -> None:
        import resource  # solo POSIX; se importa en el hijo

        limite = megabytes * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limite, limite))

    return aplicar


def ejecutar(selector: str, src_ref: Path, segundos: int, tests: Path, memoria_mb: int) -> tuple[str, list[str], int]:
    """Ejecuta ``selector`` contra ``src_ref``; devuelve (estado, tests que PASAN, tests que fallan).

    Requiere ``pytest-timeout`` (extra ``dev``): un test que no termina en 20 s falla, que cuenta como detección.
    ``estado`` es 'COLGADO' si se agota el tiempo total (cuenta como detección), 'SIN_TESTS' si no recoge
    ningún test y 'OK' en el resto. Se ejecuta *sin* ``-x`` para ver cada test por separado.
    """
    env = {**os.environ, "PYTHONPATH": str(src_ref), "MPLBACKEND": "Agg"}
    orden = [sys.executable, "-m", "pytest", *[a.replace("tests/", f"{tests}/", 1) if a.startswith("tests/") else a
                                              for a in shlex.split(selector)], "-o", "addopts=", "-o", "filterwarnings=",
             "-p", "no:cacheprovider", "-q", "-rA", "--no-header", "--tb=no", "--timeout=20"]
    try:
        r = subprocess.run(orden, cwd=RAIZ, env=env, capture_output=True, text=True, timeout=segundos, check=False,  # noqa: S603
                           preexec_fn=_limitar_memoria(memoria_mb) if memoria_mb and os.name == "posix" else None)
    except subprocess.TimeoutExpired:
        return "COLGADO", [], 0
    if r.returncode == 5:
        return "SIN_TESTS", [], 0
    pasan = [ln[7:].strip() for ln in r.stdout.splitlines() if ln.startswith("PASSED ")]
    fallan = sum(1 for ln in r.stdout.splitlines() if ln.startswith(("FAILED ", "ERROR ")))
    return "OK", pasan, fallan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("selectores", nargs="*")
    ap.add_argument("--manifiesto", default=None,
                    help="JSON con [{id, titulo, ref, selectores, guardas}] (p. ej. tests/regresiones.json)")
    ap.add_argument("--ref", default=None,
                    help="tag o commit de referencia para los selectores sueltos (por defecto, el último tag); "
                         "en el manifiesto cada entrada trae su propio ``ref``")
    ap.add_argument("--guardas", nargs="*", default=[],
                    help="fragmentos de nodeid de tests que PUEDEN pasar en la referencia (guardas de comportamiento)")
    ap.add_argument("--segundos", type=int, default=60, help="tiempo máximo por selector")
    ap.add_argument("--memoria-mb", type=int, default=4096,
                    help="límite de memoria virtual por selector (0 = sin límite); protege el runner del código sin cotas")
    args = ap.parse_args()

    # (id, ref, selector, guardas)
    tareas: list[tuple[str, str, str, list[str]]] = []
    if args.selectores:
        ref_suelto = args.ref or ultimo_tag()
        tareas += [("", ref_suelto, sel, args.guardas) for sel in args.selectores]
    if args.manifiesto:
        for entrada in json.loads(Path(args.manifiesto).read_text(encoding="utf-8")):
            ref_entrada = args.ref or entrada.get("ref") or ultimo_tag()
            tareas += [(entrada["id"], ref_entrada, sel, entrada.get("guardas", [])) for sel in entrada.get("selectores", [])]

    problemas = 0
    with tempfile.TemporaryDirectory() as tmp:
        raiz_tmp = Path(tmp)
        tests = copiar_tests_sin_match(raiz_tmp)
        arboles: dict[str, Path] = {}
        try:
            for ident, ref, sel, guardas_sel in tareas:
                if ref not in arboles:
                    arboles[ref] = raiz_tmp / f"ref{len(arboles)}"
                    _git("worktree", "add", "--detach", str(arboles[ref]), ref)
                estado, pasan, fallan = ejecutar(sel, arboles[ref] / "src", args.segundos, tests, args.memoria_mb)
                etiqueta = f"{ident} " if ident else ""
                if estado == "SIN_TESTS":
                    print(f"[MAL] {etiqueta}SIN_TESTS  {sel}")
                    problemas += 1
                    continue
                if estado == "COLGADO":
                    print(f"[OK ] {etiqueta}COLGADO ({ref})  {sel}  (el código anterior no termina)")
                    continue
                guardas = [t for t in pasan if any(g in t for g in guardas_sel)]
                sospechosos = [t for t in pasan if t not in guardas]
                marca = "MAL" if sospechosos or fallan == 0 else "OK "
                print(f"[{marca}] {etiqueta}{fallan} fallan, {len(guardas)} guardas, "
                      f"{len(sospechosos)} pasan sin deber en {ref}  {sel}")
                for t in sospechosos:
                    print(f"        pasa en {ref}: {t}")
                problemas += len(sospechosos) + (1 if fallan == 0 else 0)
        finally:
            for arbol in arboles.values():
                _git("worktree", "remove", "--force", str(arbol))
    if problemas:
        print(f"\n{problemas} problema(s): tests que no detectan el bug en su referencia (o selectores vacíos). "
              "Refuerza el test o decláralo guarda con \"guardas\".")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/verificar_mutaciones.py` — mutación manual de **una línea**: copia `src/`, reintroduce el bug y exige que los tests asociados fallen. Si un mutante **sobrevive**, el test no protege esa línea
(en walopy un mutante sobrevivió y reveló que el test de `rcParams` solo cubría 2 de 19 gráficas).
```python
"""Mutación manual de una línea: comprueba que cada test de regresión FALLA si el bug vuelve.

Para cada mutante copia ``src/`` a un directorio temporal, aplica un reemplazo de una línea que reintroduce el bug
y ejecuta los tests asociados contra esa copia. El mutante debe quedar «muerto» (algún test falla); si «sobrevive»,
el test no protege esa línea. Es un complemento de ``verificar_regresion.py`` (que compara con el tag anterior).

Uso::

    python scripts/verificar_mutaciones.py            # todos los mutantes
    python scripts/verificar_mutaciones.py MU-03 MU-07
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# (id, bug, archivo dentro de src/milib, línea original, línea mutada, selector de pytest)
# Cada mutante reintroduce UN bug corregido cambiando UNA línea; el selector apunta a su test de regresión.
MUTANTES = [
    ("MU-01", "W-01 NaN pasa la validación", "_utils.py",
     "if not np.isfinite(v) or v <= 0:", "if v <= 0:",
     "tests/test_regresion_validacion.py -k nan"),
    ("MU-02", "W-18 bool aceptado como número", "_utils.py",
     "if isinstance(value, (bool, np.bool_)):", "if False:",
     "tests/test_regresion_validacion.py -k bool"),
]


def ejecutar(mutante: tuple, base: Path) -> str:
    ident, _bug, archivo, viejo, nuevo, selector = mutante
    copia = base / ident / "src"
    shutil.copytree(RAIZ / "src", copia, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    ruta = copia / "milib" / archivo
    texto = ruta.read_text(encoding="utf-8")
    if texto.count(viejo) < 1:
        return "INVALIDO"
    ruta.write_text(texto.replace(viejo, nuevo, 1), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(copia), "MPLBACKEND": "Agg"}
    orden = [sys.executable, "-m", "pytest", *shlex.split(selector), "-o", "addopts=", "-o", "filterwarnings=",
             "-p", "no:cacheprovider", "-q", "--tb=no", "--timeout=30", "-x"]
    try:
        r = subprocess.run(orden, cwd=RAIZ, env=env, capture_output=True, text=True, timeout=300, check=False)  # noqa: S603
    except subprocess.TimeoutExpired:
        return "MUERTO"
    if r.returncode == 5:
        return "SIN_TESTS"
    return "SOBREVIVE" if r.returncode == 0 else "MUERTO"


def main(ids: list[str]) -> int:
    mutantes = [m for m in MUTANTES if not ids or m[0] in ids]
    problemas = 0
    with tempfile.TemporaryDirectory() as tmp:
        for m in mutantes:
            estado = ejecutar(m, Path(tmp))
            ok = estado == "MUERTO"
            print(f"[{'OK ' if ok else 'MAL'}] {m[0]} {estado:9s} {m[1]}")
            problemas += 0 if ok else 1
    if problemas:
        print(f"\n{problemas} mutante(s) sobreviven o son inválidos: el test no protege esa línea (o la línea cambió).")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

`tests/regresiones.json` — formato del manifiesto (una entrada por bug; `W-nn` coincide con la ficha del catálogo):
```json
[
  {"id": "W-01", "titulo": "cpm acepta duraciones NaN", "ref": "v0.2.8",
   "selectores": ["tests/test_regresion_validacion.py -k 'cpm_rechaza or pert_rechaza'"],
   "guardas": ["test_pert_rechaza_estimaciones_no_finitas"]},
  {"id": "W-24", "titulo": "CI sin gates", "ref": "v0.2.8", "selectores": [],
   "evidencia": "gate de CI; no es un test de pytest"}
]
```

## 3.9 Tests de plantilla y documentación

`tests/conftest.py` — semilla fija:
```python
"""Fixtures compartidas de la suite."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def rng() -> np.random.Generator:
    """Generador aleatorio con semilla fija para tests reproducibles."""
    return np.random.default_rng(12345)
```

`tests/test_version.py` — la versión es un literal y coincide con los metadatos instalados (detecta entornos obsoletos tras subirla):
```python
"""La versión tiene una sola fuente de verdad: el literal ``__version__`` de ``milib/__init__.py``.

``pyproject.toml`` la lee con ``[tool.setuptools.dynamic]``. No se usa ``importlib.metadata.version()`` en
``__init__.py``: los metadatos se congelan al instalar y, tras subir la versión, ``__version__`` seguiría mostrando
la anterior hasta reinstalar (C-24).
"""
from __future__ import annotations

import ast
import re
from importlib.metadata import version
from pathlib import Path

import milib

RAIZ = Path(__file__).resolve().parents[1]
INIT = RAIZ / "src" / "milib" / "__init__.py"


def test_version_coincide_con_metadatos():
    """Falla si los metadatos instalados están obsoletos (tras subir la versión: ``make install``)."""
    assert milib.__version__ == version("nombre-en-pypi"), "metadatos obsoletos: reinstala con `pip install -e .`"


def test_version_tiene_formato_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", milib.__version__)


def test_la_version_es_un_literal_en_init():
    """El literal es lo que setuptools lee sin importar el paquete; sin él la fuente única se rompe."""
    arbol = ast.parse(INIT.read_text(encoding="utf-8"))
    asignaciones = [
        n for n in arbol.body
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "__version__" for t in n.targets)
    ]
    assert len(asignaciones) == 1
    assert isinstance(asignaciones[0].value, ast.Constant) and isinstance(asignaciones[0].value.value, str)


def test_init_no_lee_la_version_de_los_metadatos():
    assert "importlib.metadata" not in INIT.read_text(encoding="utf-8")


def test_pyproject_toma_la_version_dinamicamente_de_init():
    texto = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in texto
    assert re.search(r'version\s*=\s*\{\s*attr\s*=\s*"milib\.__version__"\s*\}', texto)
    assert not re.search(r'(?m)^version\s*=\s*"\d', texto), "la versión no puede estar también como literal en pyproject.toml"
```

`tests/test_readme.py` — **los ejemplos del README son tests** (13 de 61 bloques de walopy usaban una API inexistente):
```python
"""Los ejemplos de código de la documentación son tests: todo bloque ```python debe ejecutarse sin error.

Los bloques de un archivo comparten el espacio de nombres (se ejecutan en orden, como los lee una persona).
"""
from __future__ import annotations

import io
import os
import re
import warnings
from contextlib import redirect_stdout
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")  # gráficas sin pantalla

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = [RAIZ / "README.md", *sorted((RAIZ / "docs" / "source").glob("*.md"))]
PATRON = re.compile(r"```python\n(.*?)```", re.S)


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda p: p.name)
def test_los_bloques_de_codigo_se_ejecutan(archivo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # algunos ejemplos guardan archivos (.png, .html)
    texto = archivo.read_text(encoding="utf-8")
    bloques = PATRON.findall(texto)
    espacio: dict = {}
    fallos = []
    for i, bloque in enumerate(bloques, 1):
        linea = texto[: texto.index(bloque)].count("\n") + 1
        try:
            with warnings.catch_warnings(), redirect_stdout(io.StringIO()):
                warnings.simplefilter("ignore")
                exec(compile(bloque, f"{archivo.name}[bloque {i}]", "exec"), espacio)  # noqa: S102
        except Exception as e:  # noqa: BLE001
            fallos.append(f"bloque {i} (línea ~{linea}): {type(e).__name__}: {str(e)[:100]}")
    assert not fallos, f"{archivo.name}:\n" + "\n".join(fallos)


def test_hay_bloques_en_el_readme():
    assert len(PATRON.findall((RAIZ / "README.md").read_text(encoding="utf-8"))) >= 1
```

`tests/test_documentacion.py` — cada símbolo de `__all__` está en Sphinx y cada función en el README; `CLAUDE.md` lista todos los módulos:
```python
"""La documentación no puede quedar atrás del código: cada símbolo público está documentado (R-13)."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import milib

RAIZ = Path(__file__).resolve().parents[1]
README = (RAIZ / "README.md").read_text(encoding="utf-8")
REFERENCIA = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "docs" / "source" / "referencia").glob("*.rst"))


@pytest.mark.parametrize("nombre", sorted(milib.__all__))
def test_simbolo_publico_en_la_referencia_sphinx(nombre):
    assert re.search(rf"milib\.{re.escape(nombre)}\b", REFERENCIA), f"{nombre} no está en docs/source/referencia"


@pytest.mark.parametrize("nombre", sorted(n for n in milib.__all__ if inspect.isfunction(getattr(milib, n))))
def test_funcion_publica_en_el_readme(nombre):
    assert re.search(rf"\b{re.escape(nombre)}\b", README), f"{nombre} no aparece en el README"


def test_claude_md_lista_todos_los_modulos():
    claude = (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
    modulos = [p.stem for p in (RAIZ / "src" / "milib").glob("*.py")]
    faltan = [m for m in modulos if f"`{m}.py`" not in claude]
    assert not faltan, f"CLAUDE.md no menciona: {faltan}"
```

`tests/test_idioma.py` — la política de idioma tiene un test (524 textos en inglés en v0.2.8; el test encontró 2 que escaparon a la traducción manual). Adapta `INGLES` si el idioma fijado es otro:
```python
"""Política de idioma (R-03): todo texto que ve la persona usuaria está en español.

Recorre con ``ast`` los mensajes de excepciones, los avisos (``warnings.warn``) y los docstrings de
``src/milib`` y falla si encuentra palabras que solo existen en inglés. Los identificadores, las claves de
datos, los encabezados de sección de numpydoc (``Parameters``, ``Returns``…) y las líneas de tipo
(``x : sequence of float``) quedan fuera a propósito.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import milib

SRC = Path(milib.__file__).resolve().parent  # el paquete importado (así `verificar_regresion.py` puede apuntarlo a un tag)

# Palabras que no existen en español y delatan texto en inglés (en minúsculas, palabra completa).
INGLES = frozenset(
    "the of and with for is are must should cannot from which when this that these those been being have has than then "
    "there their its".split()
)
CODIGO = re.compile(r"``.*?``")
PALABRA = re.compile(r"[A-Za-z'-]+")  # los términos con guion (Head-of-Line) cuentan como una palabra
TIPO_NUMPYDOC = re.compile(r"^[\w*,\s]+ : ")  # «x : sequence of float»: el tipo se escribe en inglés por convención
ENCABEZADOS = {"Parameters", "Returns", "Raises", "Examples", "Notes", "See Also", "References", "Yields", "Attributes"}


def _textos(arbol: ast.AST):
    """Genera (línea, texto) de mensajes de excepciones, avisos y docstrings."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                yield nodo.body[0].lineno, "doc", doc
        elif isinstance(nodo, ast.Raise) and isinstance(nodo.exc, ast.Call):
            for arg in nodo.exc.args:
                yield from ((m.lineno, "mensaje", m.value) for m in ast.walk(arg)
                            if isinstance(m, ast.Constant) and isinstance(m.value, str))
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            nombre = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if nombre == "warn" and nodo.args:
                yield from ((m.lineno, "aviso", m.value) for m in ast.walk(nodo.args[0])
                            if isinstance(m, ast.Constant) and isinstance(m.value, str))


def _prosa(texto: str, tipo: str) -> list[str]:
    """Líneas de prosa del texto (sin ejemplos ``>>>``, encabezados numpydoc ni líneas de código)."""
    if tipo != "doc":
        return [texto]
    prosa = []
    en_ejemplo = False
    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith(">>>") or s.startswith("..."):
            en_ejemplo = True
            continue
        if not s:
            en_ejemplo = False
            continue
        if en_ejemplo or s in ENCABEZADOS or set(s) <= {"-", "="} or TIPO_NUMPYDOC.match(s):
            continue
        prosa.append(s)
    return prosa


def encontrar_ingles(ruta: Path) -> list[str]:
    hallazgos = []
    for linea, tipo, texto in _textos(ast.parse(ruta.read_text(encoding="utf-8"))):
        for prosa in _prosa(texto, tipo):
            sin_codigo = CODIGO.sub(" ", prosa)
            palabras = {p.lower() for p in PALABRA.findall(sin_codigo)} & INGLES
            if palabras:
                hallazgos.append(f"{ruta.name}:{linea} ({tipo}) {sorted(palabras)} → {prosa[:70]!r}")
    return hallazgos


@pytest.mark.parametrize("ruta", sorted(SRC.glob("*.py")), ids=lambda r: r.name)
def test_textos_visibles_en_espanol(ruta):
    hallazgos = encontrar_ingles(ruta)
    assert not hallazgos, "Texto en inglés visible para la persona usuaria:\n" + "\n".join(hallazgos)


def test_el_detector_encuentra_ingles(tmp_path):
    """Control negativo: el detector debe señalar mensajes, avisos y docstrings en inglés."""
    f = tmp_path / "malo.py"
    f.write_text(
        'import warnings\n'
        'def g(x):\n'
        '    """Compute the value of x."""\n'
        '    if x < 0:\n'
        '        raise ValueError("x must be positive")\n'
        '    warnings.warn("this is not finite")\n',
        encoding="utf-8",
    )
    tipos = {h.split("(")[1].split(")")[0] for h in encontrar_ingles(f)}
    assert tipos == {"doc", "mensaje", "aviso"}


def test_el_detector_no_marca_espanol(tmp_path):
    f = tmp_path / "bueno.py"
    f.write_text(
        'def g(x):\n'
        '    """Calcula el valor de x.\n\n    Parameters\n    ----------\n    x : float\n        Valor positivo.\n    """\n'
        '    raise ValueError("x debe ser positivo")\n',
        encoding="utf-8",
    )
    assert encontrar_ingles(f) == []
```

`tests/test_trazabilidad.py` — cada bug del manifiesto tiene su ficha (la **fila** `| **W-nn** |`, no una mención cualquiera) y sus selectores apuntan a tests que existen:
```python
"""Trazabilidad bug → test de regresión → ficha del catálogo (R-16).

Cada bug corregido figura en ``tests/regresiones.json`` con su identificador ``W-nn``, la versión que
aún lo tenía (``ref``) y los selectores de pytest que lo cubren. Este test comprueba que el manifiesto es
coherente con el catálogo y con los tests. Que esos tests *fallan* en ``ref`` lo comprueba
``scripts/verificar_regresion.py`` (job ``regresion`` del CI).
"""
from __future__ import annotations

import ast
import json
import re
import shlex
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = json.loads((RAIZ / "tests" / "regresiones.json").read_text(encoding="utf-8"))
CATALOGO = (RAIZ / "docs" / "referencia" / "BUG_CATALOG.md").read_text(encoding="utf-8")
OPERADORES = {"and", "or", "not"}


def _nombres_de_test(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}


def _selectores():
    for entrada in MANIFIESTO:
        for sel in entrada.get("selectores", []):
            yield entrada["id"], sel


def test_identificadores_unicos_y_bien_formados():
    ids = [e["id"] for e in MANIFIESTO]
    assert all(re.fullmatch(r"W-\d{2}", i) for i in ids)
    assert ids == sorted(ids), "el manifiesto va ordenado por identificador"
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("entrada", MANIFIESTO, ids=lambda e: e["id"])
def test_cada_entrada_tiene_prueba_o_evidencia_y_version_de_referencia(entrada):
    assert entrada["titulo"].strip()
    assert re.fullmatch(r"v\d+\.\d+\.\d+", entrada["ref"]), "``ref`` es el tag que aún tenía el bug"
    assert entrada.get("selectores") or entrada.get("evidencia"), "sin selectores debe explicar la evidencia"


@pytest.mark.parametrize("ident", [e["id"] for e in MANIFIESTO])
def test_cada_bug_tiene_ficha_en_el_catalogo(ident):
    assert re.search(rf"(?m)^\| \*\*{ident}\*\* \|", CATALOGO), f"{ident} no tiene su fila de ficha en docs/referencia/BUG_CATALOG.md"


@pytest.mark.parametrize(("ident", "selector"), list(_selectores()), ids=lambda v: v if isinstance(v, str) else None)
def test_los_selectores_apuntan_a_tests_que_existen(ident, selector):
    """El archivo existe y cada palabra de la expresión ``-k`` aparece en el nombre de algún test."""
    partes = shlex.split(selector)
    archivo = RAIZ / partes[0].split("::")[0]
    assert archivo.is_file(), f"{ident}: {archivo} no existe"
    nombres = _nombres_de_test(archivo)
    if "::" in partes[0]:
        assert partes[0].split("::")[1].split("[")[0] in nombres
    if "-k" in partes:
        palabras = [p for p in re.split(r"[\s()]+", partes[partes.index("-k") + 1]) if p and p not in OPERADORES]
        for palabra in palabras:
            assert any(palabra in n for n in nombres), f"{ident}: «{palabra}» no coincide con ningún test de {archivo.name}"


def test_los_doctests_estan_activos():
    """R-15: los ejemplos de los docstrings se ejecutan en cada ``pytest`` (C-19)."""
    pyproject = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert "--doctest-modules" in pyproject
```

**Test de contrato de entradas** (esqueleto; en walopy barrió 70 funciones y halló 30 excepciones inesperadas, 2 bloqueos y 26 entradas basura aceptadas):
```python
"""Ninguna función pública acepta NaN/inf/None/str/bool/listas vacías en silencio, lanza una excepción distinta de
ValueError/TypeError ni se bloquea. Se sustituye UN argumento cada vez en una llamada válida de referencia."""
from __future__ import annotations

import copy
import inspect
import signal
import warnings

import numpy as np
import pytest

import milib

NAN, INF = float("nan"), float("inf")
BASE = {                                   # una llamada VÁLIDA por función pública (añade cada función nueva aquí)
    "funcion_a": dict(x=[1.0, 2.0, 3.0], alpha=0.5),
}
EXENTAS = set()                            # funciones que reciben callables/resultados: justifícalas con un comentario
ESCALARES_INVALIDOS = [NAN, INF, -INF, "abc", True, None]
LISTAS_INVALIDAS = [[], [NAN, 1.0], [INF, 1.0], ["x", 1.0], [None, 1.0]]
ACEPTADOS = set()                          # (función, argumento, valor) legítimos, cada uno con su razón

def _llamar(fn, kwargs, segundos=10):
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
    signal.alarm(segundos)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return "ok", fn(**kwargs)
    except TimeoutError:
        return "hang", None
    except BaseException as e:             # noqa: BLE001 - se inspecciona el tipo exacto
        return "exc", e
    finally:
        signal.alarm(0)

@pytest.mark.parametrize("nombre", sorted(BASE))
def test_contrato_de_entradas(nombre):
    fn, base = getattr(milib, nombre), BASE[nombre]
    fallos = []
    for arg, valor in base.items():
        malos = LISTAS_INVALIDAS if isinstance(valor, (list, tuple, np.ndarray)) else ESCALARES_INVALIDOS
        for malo in malos:
            if (nombre, arg, repr(malo)) in ACEPTADOS:
                continue
            kw = copy.deepcopy(base); kw[arg] = malo
            estado, res = _llamar(fn, kw)
            if estado == "hang" or (estado == "exc" and not isinstance(res, (ValueError, TypeError))) or estado == "ok":
                fallos.append(f"{nombre}({arg}={malo!r}) → {estado} {res!r}")
    assert not fallos, "\n".join(fallos)

def test_toda_funcion_publica_tiene_llamada_de_referencia():
    publicas = {n for n in milib.__all__ if inspect.isfunction(getattr(milib, n))}
    assert publicas - EXENTAS - set(BASE) == set()
```
*(Ajusta `None`: si un argumento admite `None` como «no indicado», no lo incluyas para él.)* En Windows no hay `SIGALRM`: usa `pytest-timeout`.

**`tests/test_utils.py`** — los validadores centrales llevan sus propios tests (sin ellos la capa de la que depende toda la API queda sin cobertura):
```python
"""Validadores centrales: NaN antes de comparar, bool rechazado, cotas y vacío."""
from __future__ import annotations

import numpy as np
import pytest

from milib._utils import as_1d, as_int_positive, as_nonneg, as_positive

NAN, INF = float("nan"), float("inf")


@pytest.mark.parametrize("malo", [NAN, INF, -INF, 0, -1.0, "abc", True, None])
def test_as_positive_rechaza_lo_invalido(malo):
    with pytest.raises((ValueError, TypeError)):
        as_positive(malo, "x")


@pytest.mark.parametrize("malo", [NAN, INF, -1.0, "abc", True, None])
def test_as_nonneg_rechaza_lo_invalido(malo):
    with pytest.raises((ValueError, TypeError)):
        as_nonneg(malo, "x")


def test_cero_es_valido_para_nonneg_pero_no_para_positive():
    assert as_nonneg(0, "x") == 0.0
    with pytest.raises(ValueError):
        as_positive(0, "x")


@pytest.mark.parametrize("malo", [1.5, True, "3", None])
def test_as_int_positive_exige_enteros_sin_bool(malo):
    with pytest.raises(TypeError):
        as_int_positive(malo, "n")


def test_as_int_positive_limites_y_cota():
    assert as_int_positive(np.int64(3), "n") == 3
    with pytest.raises(ValueError):
        as_int_positive(0, "n")
    with pytest.raises(ValueError, match="no puede superar"):
        as_int_positive(11, "n", max=10)


@pytest.mark.parametrize("malo", [[], [NAN, 1.0], [INF], [[1.0, 2.0], [3.0, 4.0]]])
def test_as_1d_rechaza_lo_invalido(malo):
    with pytest.raises(ValueError):
        as_1d(malo, "x")


def test_as_1d_acepta_lista_array_y_serie():
    pd = pytest.importorskip("pandas")
    for entrada in ([1, 2, 3], np.array([1.0, 2.0, 3.0]), pd.Series([1, 2, 3])):
        assert as_1d(entrada).tolist() == [1.0, 2.0, 3.0]
```

**Tests de gráficas (estado global):** una gráfica no debe modificar `matplotlib.rcParams`; el test recorre **todas** (las de `.plot()` y las de llamada directa):
```python
@pytest.mark.parametrize("nombre", sorted(RESULTADOS))
def test_plot_no_modifica_rcparams(nombre):
    antes = dict(plt.rcParams)
    RESULTADOS[nombre]().plot()
    plt.close("all")
    assert dict(plt.rcParams) == antes
```

**Test de complejidad / escala** (la complejidad anunciada se verifica; un `O(n²)` documentado era `O(n³)`):
```python
def test_algoritmo_n1000_es_rapido():
    t0 = time.perf_counter(); milib.algoritmo(datos(1000)); assert time.perf_counter() - t0 < 2.0   # margen amplio: no flaky
```
y la equivalencia con una versión directa/fuerza bruta en tamaños pequeños (`@pytest.mark.parametrize("semilla", range(100))`).

**Documentación Sphinx** *(probado)* — `docs/source/conf.py`:
```python
import milib

project   = "milib"
author    = "TuNombre"
language  = "es"
release   = milib.__version__            # NO `from importlib.metadata import version` (colisiona con la opción `version` de Sphinx)
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "myst_parser"]
html_theme = "sphinx_rtd_theme"
autodoc_member_order = "bysource"
napoleon_use_ivar = True                 # evita referencias cruzadas ambiguas con los atributos de los dataclasses
```
Patrón de `docs/source/referencia/<grupo>.rst`:
```rst
Nombre del grupo
================

.. autofunction:: milib.funcion_a

.. autoclass:: milib.ClaseA
   :members:
```
Reglas: **un símbolo = una directiva autodoc canónica**; si dos páginas lo documentan, la procesada primero lleva `:no-index:`; en docstrings numpy evita `shape (n,)` si existe un atributo `n` (referencia ambigua);
todas las directivas usan `milib.X` (nunca el nombre antiguo tras un renombre); verifica con `sphinx-build -W`. ReadTheDocs: conectar el repo → builds en cada push a `main`.

## 3.10 Archivos de proceso

**`CLAUDE.md` (plantilla)** — se escribe en la Etapa 0/1 y se mantiene **con cifras medidas**:
```markdown
# CLAUDE.md — milib
## Descripción            (qué es, usuarios, alcance y EXCLUSIONES, idioma, Python mínimo)
## Estado verificado (fecha, commit)   (tabla: tests, cobertura global/mínimo, lint, tipos, build, docs, regresiones — salida de `make check`)
## Mapa del código        (un renglón por módulo; `tests/test_documentacion.py` exige que estén todos)
## Comandos estándar      (`make …`, equivalentes directos, requisitos como `pytest-timeout` o `git fetch --tags`)
## Definición de «terminado»   (`make check` con código 0 + CHANGELOG + docs; «listo para release» solo tras `make release-check`)
## Reglas de trabajo      (cada una etiquetada [test] [CI] [comando] [guía]; sección 8.6)
## Hooks para agentes     (qué hacen .claude/settings.json y los dos hooks)
## Pendientes y deuda técnica (solo lo verificado: deuda | evidencia | estado)
## Política de no repetición
## Checklist de release
```
**`AGENTS.md`** (corto, apunta a `CLAUDE.md`):
```markdown
# AGENTS.md
Las instrucciones para agentes de IA están en [`CLAUDE.md`](CLAUDE.md).
make install · make check-fast (iterar) · make check (antes de abrir un PR)
Idioma: <el del repo>; identificadores en inglés.
```
**`.github/PULL_REQUEST_TEMPLATE.md`**:
```markdown
## Resumen
<!-- Qué cambia y por qué (1–3 puntos) -->

## Tipo de cambio
- [ ] Corrección de bug (con test de regresión que falla en el tag anterior, entrada `W-nn` en `tests/regresiones.json` y ficha en `docs/referencia/BUG_CATALOG.md`)
- [ ] Nueva funcionalidad
- [ ] Documentación / mantenimiento
- [ ] Cambio que rompe compatibilidad (documentado en CHANGELOG)

## Lista de verificación ("terminado")
- [ ] `make check` termina con código 0 (lint, tipos, tests, cobertura global y por módulo, build, docs, ejemplos, referencias obsoletas y regresiones)
- [ ] Funciones nuevas: test de caso borde (vacío, NaN/inf, n mínimo, degenerado) y símbolo documentado
- [ ] Si corrige un bug: `make regresion` y `make mutaciones` en verde (R-16)
- [ ] La rama parte de `origin/main` (`git merge-base --is-ancestor origin/main HEAD`, R-17)
- [ ] Si sube la versión: solo en `src/milib/__init__.py`, y `make release-check TAG=vX.Y.Z` correcto
- [ ] `CHANGELOG.md`, README y referencia Sphinx actualizados si aplica

## Plan de pruebas
<!-- Comandos ejecutados y resultado -->
```
**`.github/CODEOWNERS`** — `* @UsuarioGitHub` (la **protección de ramas** que exige su revisión se configura en GitHub, fuera del repo: NO verificable desde el repositorio).
**Plantillas de issues** (`bug.md`, `feature.md`): versión del paquete (`python -c "import milib; print(milib.__version__)"`), Python, SO, dependencias, reproducción mínima, traza.
**`SECURITY.md`**: versiones soportadas (la última), canal privado (aviso de seguridad de GitHub), plazo de acuse, alcance (bloqueos y consumo ilimitado de memoria por parámetros válidos cuentan como vulnerabilidad).
**`CONTRIBUTING.md`**: flujo (fork → rama desde `main` → `make install` → cambio con test de regresión → `make check` → PR), convenciones, cómo corregir un bug (manifiesto + ficha), cómo subir la versión.
**`CODE_OF_CONDUCT.md`**: Contributor Covenant.

---

# Parte 4 — Diseño de API, validación y numérica

## 4.1 Retornar objetos de resultado, no tuplas
```python
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

@dataclass
class MiResultado:
    values: np.ndarray
    params: dict = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        """Cabeceras de presentación en el idioma del repo; las CLAVES de datos no se traducen."""
        return pd.DataFrame({"punto": np.arange(1, len(self.values) + 1), "valor": self.values})

    def summary(self) -> str:
        lines = [f"Resultado: {len(self.values)} puntos"]
        lines += [f"  {k} = {v:.6g}" if isinstance(v, float) else f"  {k} = {v}" for k, v in self.params.items()]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()

    def plot(self, **kwargs):
        from .plotting import plot_result      # importación perezosa: matplotlib/plotly no se importan al hacer `import milib`
        return plot_result(self, **kwargs)
```
Si `to_frame()` se construye desde listas de diccionarios, traduce con `.rename(columns=…)` sin tocar las claves del diccionario (esas son contrato).

## 4.2 Validación: una sola capa de ingesta *(probado)*
**Todo argumento numérico de usuario pasa por `_utils.py`.** La trampa central: **`x <= 0` es `False` para NaN**, así que `if x <= 0: raise` deja pasar NaN; `inf` tampoco se rechaza. **Valida `isfinite` ANTES de comparar.**

```python
"""Validadores internos: única capa de ingesta numérica."""
from __future__ import annotations

from typing import Any

import numpy as np

MAX_SERVIDORES = 10**6      # cotas de tamaño: evitan cálculos de duración prácticamente infinita con parámetros absurdos
MAX_CLIENTES   = 10**7

def _to_float(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):            # bool es subclase de int: mmc(2, 3, True) se interpretaba como c=1
        raise TypeError(f"'{name}' debe ser un número, se recibió un booleano ({value!r}).")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise TypeError(f"'{name}' debe ser un número, se recibió {type(value).__name__!r}.") from None

def as_positive(value, name):
    v = _to_float(value, name)
    if not np.isfinite(v) or v <= 0:                   # isfinite primero
        raise ValueError(f"'{name}' debe ser un número finito y positivo, se recibió {value!r}.")
    return v

def as_nonneg(value, name):
    v = _to_float(value, name)
    if not np.isfinite(v) or v < 0:
        raise ValueError(f"'{name}' debe ser finito y >= 0, se recibió {value!r}.")
    return v

def as_int_positive(value, name, *, max=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"'{name}' debe ser un entero positivo, se recibió {type(value).__name__!r} = {value!r}.")
    v = int(value)
    if v < 1:
        raise ValueError(f"'{name}' debe ser >= 1, se recibió {value!r}.")
    if max is not None and v > max:
        raise ValueError(f"'{name}' no puede superar {max}, se recibió {value!r}.")
    return v

def as_1d(x, name="x") -> np.ndarray:
    """Acepta lista, ndarray o Series → array float 1-D, finito y no vacío."""
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"'{name}' debe ser 1-D.")
    if arr.size == 0:
        raise ValueError(f"'{name}' está vacío.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"'{name}' contiene NaN o infinitos.")
    return arr
```
Reglas derivadas (cada una nació de un bug real):
- **Entrada vacía → `ValueError`** con mensaje (no `ZeroDivisionError`/`IndexError`); política **uniforme** en toda la API.
- **Todo parámetro que dimensiona un cálculo lleva cota** (`MAX_*`) y toda búsqueda iterativa un límite de iteraciones (presupuesto ≤ 0 colgaba una bisección).
- **Listas de registros** (`list[dict]`): comprobar tipo, claves obligatorias (`items[0]: falta la clave 'x'`) y **duplicados** (nombres repetidos se fusionaban en silencio).
- **Nada se recorta, fusiona ni descarta en silencio:** cota alcanzada → `UserWarning`; dato fuera de horizonte → aviso y campo en el resultado (`past_due_releases`); caso degenerado válido (demanda 0) → aceptarlo.
- **Casos degenerados:** datos constantes (std = 0), n = 1, n = 2: definir y probar. Un solucionador con intervalo fijo (`hi = 100`) devuelve el extremo sin avisar: avisa.
- **Sin `except Exception` amplio** que oculte errores: expón un parámetro (`errors="collect"|"raise"`) y columna de error estable.
- Excepciones de usuario: `ValueError`/`TypeError` con mensaje accionable; `raise … from None` al traducir una excepción interna; nunca `KeyError`/`AttributeError`/`OverflowError` crudos por entrada del usuario.
- Dependencias **opcionales**: `try: import x except ImportError: raise ImportError("… pip install nombre-en-pypi[extra]") from None`, y test con `monkeypatch.setitem(sys.modules, "x", None)`.
  (En walopy matplotlib y plotly son dependencias obligatorias importadas de forma perezosa: no hay extras, y la regla quedó sin aplicar; si existen extras, es obligatoria.)

## 4.3 Numérica
- **Fórmulas directas con potencias/factoriales desbordan** (`a**n / n!` con n ≳ 143): usa recurrencias estables (Erlang-B), `lgamma` o logaritmos; prueba con 10× el tamaño típico (c = 150, 300, 1000).
- **`-0.0`:** `round(-1e-16, 10)` devuelve `-0.0` y aparece en tablas → `round(x, 10) + 0.0`.
- **Empates en heurísticas:** resuelve con tolerancia relativa (1e-12) y prueba la igualdad exacta con datos enteros; con decimales, un cambio en el orden de las sumas cambia el desempate.
- **Referencias externas imprecisas:** al contrastar con otra librería (p. ej. `scipy…fit`), si difiere en el 6.º decimal puede ser **la referencia** la menos precisa; fija constantes calculadas con `brentq` (1e-15) y documenta su origen.
- **Complejidad anunciada = complejidad medida** (tabla de tiempos n = 100/400/1000, aceleraciones como Taillard para NEH, sumas acumuladas en Wagner-Whitin). Corrige la documentación o el código, no ambos a medias.
- **Cálculo ≠ graficado:** las funciones de cálculo no tocan matplotlib; las de graficado reciben el objeto resultado.

## 4.4 Graficado *(patrón)*
```python
def plot_result(result, *, title=None, figsize=None):
    import matplotlib.pyplot as plt                    # importación perezosa
    with plt.rc_context({}):                           # o no tocar rcParams en absoluto; ambos pasan el test de rcParams
        fig, ax = plt.subplots(figsize=figsize or (10, 4))
        ax.plot(range(1, len(result.values) + 1), result.values, marker="o", ms=4, lw=1)
        ax.set_xlabel("Observación"); ax.grid(alpha=0.25)
        fig.suptitle(title or "Resultado", fontweight="bold")
        fig.tight_layout()
    return fig
```
- **No contaminar estado global** (`rcParams`, `warnings`): `plt.rc_context` / `warnings.catch_warnings()`; y un **test que compare `dict(plt.rcParams)` antes y después para cada gráfica**.
- Los textos de la gráfica (títulos, ejes, leyendas) están en el idioma del repo. No condiciones elementos visuales por propiedades incidentales del resultado (`if zones and panel.symmetric` ocultó bandas σ en cartas asimétricas).
- Una gráfica por resultado con `.plot()` **debe** tener su test de humo con backend `Agg`; un módulo de gráficas al 0 % de cobertura escondía un `plot()` roto.

## 4.5 Convenciones de código
Docstrings numpy (`Parameters`/`Returns`/`Raises`/`Examples` con doctest ejecutable; los encabezados de sección y los tipos pueden quedar en inglés por convención) · type hints en toda función pública ·
`from __future__ import annotations` en cada archivo (necesario para `X | None` en 3.9) · comentarios solo para el POR QUÉ · imports internos relativos · validar en la frontera del sistema, no para casos imposibles ·
`py.typed` en el wheel · `__all__` completo.

---

# Parte 5 — Estrategia de pruebas

## 5.1 Capas (todas corren en `make test`)
| Capa | Qué comprueba | Archivo(s) |
|---|---|---|
| Unitarias con **referencia independiente** | resultados contra publicación, cálculo manual, otra librería, fuerza bruta, simulación (≥ 20 semillas) | `test_<modulo>.py`, `test_referencias_externas.py` |
| **Contrato de entradas** | barrido argumento × valor patológico sobre todo `__all__` | `test_contrato_entradas.py` |
| Casos borde | vacío, NaN/inf, n mínimo, parámetros ausentes, std = 0, tamaños absurdos | `test_regresion_validacion.py` |
| Escala y complejidad | tamaño 10× el típico, tiempos acotados, equivalencia con versión directa | `test_complejidad.py`, `test_<modelo>_estable.py` |
| Documentación | ejemplos del README, doctests, `__all__` ↔ docs, CLAUDE.md ↔ módulos | `test_readme.py`, `test_documentacion.py`, doctests |
| Ejemplos | `examples/*.py` se ejecutan (un renombre los rompe en silencio) | `test_ejemplos.py` |
| Versión | literal, sin `importlib.metadata`, coincide con metadatos | `test_version.py` |
| Idioma | mensajes, avisos y docstrings en el idioma fijado | `test_idioma.py` |
| Gráficas | humo con `Agg` + `rcParams` intacto, todas | `test_plotting.py` |
| CLI | `--version`, ayuda, códigos de salida | `test_cli.py` |
| Trazabilidad | cada bug: ficha + selectores existentes + fallan en el tag anterior | `test_trazabilidad.py`, `make regresion` |

## 5.2 Casos borde obligatorios por función pública
Entrada vacía · NaN · ±inf · negativo · cero · `None` donde no se admite · `str`/`bool` · lista con un elemento · lista de longitud distinta en arreglos paralelos · duplicados · tamaño absurdo (1e7, 1e9) ·
dato constante · n = 1 y n = 2 · parámetro opcional ausente. Parametriza (`@pytest.mark.parametrize`), no copies tests.

## 5.3 Configuración
`filterwarnings = error` · `--doctest-modules --import-mode=importlib` · semilla en `conftest.py` · `pytest-timeout` (bloqueos) · cobertura `fail_under = 85` + script por módulo (≥ 70).
Higiene: sin `test_v026.py` (nombres por versión); archivos por tema; los tests de regresión llevan el ID del bug.

## 5.4 Todo bug corregido deja tres huellas (regla R-16)
1. **Un test de regresión que falla en el tag anterior**, registrado en `tests/regresiones.json` con su `ref` (`make regresion`). Si también pasa sin el arreglo, no protege nada
   (en walopy dos tests —`-0.0` y el fallback de `__version__`— pasaban con el código viejo).
2. **Una ficha `W-nn`** en `docs/referencia/BUG_CATALOG.md` (síntoma, causa raíz, solución, test, clase `C-nn`).
3. **Si la lección es transferible:** una línea en `PLAYBOOK.md` y, si cambia cómo se trabaja, una regla en `CLAUDE.md`.
Complemento: **mutación de una línea** (`make mutaciones`): reintroduce el bug cambiando una línea y exige que algún test falle. Al empezar un proyecto sin historial, usa la mutación como único control.

## 5.5 Tests que prueban detectores
Un test de lint/idioma/barrido lleva su **control negativo** dentro (una entrada mala que debe ser señalada) y se prueba contra una versión mala conocida (el test de idioma: 524 hallazgos en la versión antigua, 0 en la actual).

## 5.6 Validación contra la versión mínima y las últimas
Job con cotas inferiores exactas (`numpy==1.22.0`…; en local `uv venv --python 3.9`) y job semanal con `pip install --upgrade`. Un `filterwarnings` de terceros por versión mínima se comenta con su causa.
Tras subir la versión, reinstala **todos** los entornos locales (`uv pip install -e . --no-deps`): un venv con metadatos viejos falla `test_version` (detección real).

## 5.7 Estrategia ante timeouts y recursos
Tests de bloqueo con `signal.alarm`/`pytest-timeout`; tests contra código antiguo con `RLIMIT_AS`; tests de tiempo con margen amplio (2 s para algo que tarda 0,1 s) para no ser flaky en runners lentos.

---

# Parte 6 — Release y PyPI

## 6.1 Flujo (la persona responsable crea el tag/release si el agente no puede)
1. **Elegir versión comprobando PyPI:** `pip index versions nombre-en-pypi` (no reutilices ni asumas: v0.2.2 y v0.2.4 se «ocuparon»).
2. **Subir la versión solo en `src/milib/__init__.py`** y ejecutar `make install` (refresca los metadatos).
3. Entrada en `CHANGELOG.md` (con «Cambios que rompen compatibilidad» si aplica); `make notas-release VERSION=X.Y.Z` imprime el cuerpo del release.
4. `make check` (código 0) y `make release-check TAG=vX.Y.Z` (el **wheel construido** muestra la versión del tag; con un tag distinto debe fallar).
5. PR a `main`, CI verde, merge (los pide la persona).
6. **Después de que la versión esté en `main`:** GitHub → Releases → New release → tag `vX.Y.Z` apuntando a `main` → Publish. (Un tag creado antes de subir la versión, o antes del último push, produce artefactos viejos y `400 File exists`.)
7. `publish.yml` se dispara: verifica (tests/lint), construye, `twine check`, comprueba tag == wheel, publica.
8. **Post-release:** `pip install nombre-en-pypi==X.Y.Z` en un venv limpio + `python -c "import milib; print(milib.__version__)"`; ejecutar un ejemplo.
«Listo para release» **solo** tras construir el wheel y ver su versión.

## 6.2 Versionado
SemVer. En 0.x, un MINOR puede romper compatibilidad (documéntalo). PATCH: bugs, docs, cambios pequeños. MINOR: funciones nuevas, cambios de API. **Un tag por cada versión publicada.** Nunca reutilizar un número ya subido.
Política de deprecación (recomendada, no probada en walopy): `DeprecationWarning` durante ≥ 1 MINOR antes de eliminar.

## 6.3 Errores de publicación
| Síntoma | Causa | Solución |
|---|---|---|
| `400 File exists` / `This filename was previously used` | el archivo ya existió (aunque se haya borrado), o el tag/release se creó antes de subir la versión | incrementar la versión; `make release-check` antes de crear el tag |
| `invalid-publisher` | el *environment*, workflow, repo u owner no coinciden con el Trusted Publisher de pypi.org | revisar los cuatro campos en ambos lados |
| El job de publicación falla sin error visible | logs truncados / atestaciones / configuración | leer el log **completo** del paso; ensayar en TestPyPI; no cambiar `attestations` ni versiones de acciones por intuición |
| Versión «ya ocupada» | se eligió sin consultar PyPI | `pip index versions` primero |
| `build` falla con setuptools ≥ 77 por la licencia | classifier de licencia + `license = "MIT"` | quitar el classifier (PEP 639) |
| Tag apunta a un commit viejo | release creado antes del último push | crear el release solo con todo en `main` |
| Workflow lee `project.version` con `tomllib` y falla | la versión ahora es dinámica | usar `comprobar_version_release.py` sobre el wheel |

---

# Parte 7 — Mantenimiento y seguridad

- **Semanal:** job programado con las últimas dependencias y benchmarks (informativos). **Cada PR:** `pip-audit`.
- **Recomendado (no implementado en walopy, pendiente):** Dependabot (`pip` y `github-actions`), acciones fijadas por SHA, `attestations: true` (tras ensayo en TestPyPI), CodeQL/escaneo de secretos, `concurrency` en el CI.
- **Seguridad de la librería:** sin `eval`/`exec`/`pickle`/`subprocess` sobre entrada del usuario; consumo ilimitado de memoria o bloqueo por parámetros válidos **es** una vulnerabilidad (cotas `MAX_*`).
- **Issues:** responder en < 7 días (no medible hasta que haya actividad); plantillas; `good first issue`.
- **Línea base de rendimiento:** guardar los resultados de `benchmarks/` y compararlos entre versiones (pendiente en walopy).
- **Cada release:** actualizar `CLAUDE.md` (estado medido), `SCORECARD.md` si cambió algo, y el catálogo si hubo bugs.

---

# Parte 8 — Auditoría, scorecard y retrospectiva

## 8.1 Procedimiento (solo lectura primero)
1. **Línea base** — ejecuta y registra resultado **y tiempo**: instalación limpia (venv nuevo), tests, cobertura (global **y por módulo**), lint, tipos, build aislado, docs. Lista lo que existe: CLAUDE.md/AGENTS.md, `.claude/`, Makefile, pre-commit, CI, plantillas, CHANGELOG, CONTRIBUTING, `py.typed`, `examples/`.
2. **Historial** — `git log` clasificado (feature/fix/refactor/docs/ci). Para cada fix: ficha (síntoma, causa raíz, test de regresión existe/falta, clase de error). Los fixes sin test se marcan «falta» y se corrigen.
3. **Sesiones previas** — minar `~/.claude/projects/<ruta>/` buscando instrucciones repetidas y correcciones; si no hay, decirlo y continuar.
4. **Barrido de contrato** — entradas patológicas sobre toda la API; reportar excepciones inesperadas, bloqueos y entradas basura aceptadas.
5. **Infraestructura para agentes** — crear lo que falte y **probarlo** (Etapa 1).
6. **Auditoría** con los criterios de 8.2, scorecard (8.3), reglas probadas (8.6) y entregables (8.7).

## 8.2 Criterios de la auditoría (ya contrastados)
- El comando de lint del gate es **el que corre el CI** (no inventes un `--select` más estricto sin probarlo).
- Cobertura: global ≥ 85 % y ningún módulo público < 70 %, **por módulo**; los que ya estén por debajo son trinquete y deuda.
- Todo bug corregido tiene un test que falla si el bug vuelve (versión anterior + mutación de una línea).
- `examples/` se **ejecutan**; busca el nombre antiguo con grep en todo el repo (incluye `examples/`, CI y `LICENSE`), excluyendo CHANGELOG y el propio CLAUDE.md.
- Sphinx: un símbolo = una directiva canónica; `sphinx-build -W`.
- Dependencias opcionales con `ImportError` accionable y test; gráficas sin tocar `rcParams` (test para todas).
- «Listo para release» solo tras construir el wheel y ver su versión.
- Nunca poner a una acción de GitHub una versión «corregida» por intuición.
- **Busca contradicciones** entre documentos, tests y código (comandos distintos para el mismo gate; reglas que el código no cumple; cifras copiadas; scorecards con criterios distintos; changelogs que afirman lo que PyPI desmiente).

## 8.3 Scorecard — 14 dimensiones, escala 0–5 *(probado en walopy: media 3,71)*
0 ausente · 1 rudimentario · 2 funcional · 3 sólido (cumple **parte** del criterio del 4) · 4 maduro (cumple **todo** el criterio) · 5 excelente. **Un 4 exige todos los puntos; si falta uno, es 3.**
La media se calcula y se **comprueba con un test** que parsea la tabla (`tests/test_scorecard.py`).

| # | Dimensión | Criterio para el 4 (todo) | Para el 5 |
|---|---|---|---|
| 1 | Estructura del repositorio | layout `src/`; `pyproject` completo; LICENSE; `.gitignore` cubre build/dist/docs/_build/.coverage/cachés; `py.typed` en el wheel; CLAUDE.md, AGENTS.md, Makefile, CODEOWNERS | plantilla verificada en CI |
| 2 | Diseño de API pública | `__all__` completo y documentado (test); contrato de entradas sobre toda la API; resultados tipados; cambios incompatibles en CHANGELOG | política de deprecación |
| 3 | Validación de entradas | capa central; barrido de contrato sin excepciones inesperadas; cotas de tamaño; NaN antes de comparar | pruebas de propiedades |
| 4 | Corrección numérica | referencias independientes fijas; caso a escala ≥ 10×; complejidad verificada | cota de error por modelo |
| 5 | Suite de pruebas | cobertura global ≥ 85 % y todos los módulos ≥ 70 %; regresiones fallan en el tag anterior; mutantes de los fixes muertos | puntuación de mutación sistemática |
| 6 | Tipado estático | mypy sin errores; `py.typed` en el wheel | `--strict` en módulos centrales |
| 7 | Gestión de dependencias | cotas inferiores probadas; prueba periódica con las últimas; `pip-audit` en CI | bloqueo de herramientas + Dependabot |
| 8 | CI/CD | todos los gates en CI; matriz de todas las versiones de `classifiers`; publicación repite tests/lint y comprueba tag == wheel | acciones por SHA, `attestations`, `concurrency` |
| 9 | Documentación | `sphinx -W`; ejemplos del README como tests; `__all__` ↔ docs; doctests activos | tutoriales; docs versionadas |
| 10 | Rendimiento | benchmarks reproducibles **y** complejidad verificada **y** línea base guardada con comparación automática | regresión bloqueante en CI |
| 11 | Seguridad | `pip-audit` en CI; `SECURITY.md`; cotas de tamaño; **y** procedencia (`attestations`), actualización automática de dependencias y acciones por SHA | CodeQL/secretos; OpenSSF Scorecard |
| 12 | Versionado y releases | fuente única con test; guarda tag == wheel; CHANGELOG; **un tag por cada versión publicada en PyPI** | releases automatizados |
| 13 | Comunidad y contribución | CONTRIBUTING, plantillas, código de conducta, SECURITY, CODEOWNERS **y** evidencia de respuesta a issues < 7 días | `good first issue`, guía de revisión |
| 14 | Developer Experience | CLAUDE.md + AGENTS.md; un comando que ejecuta todo (`make check`); hooks de agente **probados**; ejemplos que se ejecutan | pre-commit; entorno reproducible |

**Dimensión más rezagada:** la de menor nota. **Si hay empate, nómbralas todas y desempata por impacto observado** (incidentes en el historial, mensajes de la persona sobre ese tema). En walopy empataron cuatro (Rendimiento, Seguridad,
Versionado/releases, Comunidad) y ganó Versionado: tres incidentes de publicación y ocho mensajes. **Acción de mayor impacto:** la que ataca la causa de los incidentes observados (ensayo de publicación en TestPyPI).

## 8.4 Niveles de madurez (Playbook)
| Nivel | Nombre | Criterio resumido (verificable con `make`) |
|---|---|---|
| 0→1 | Estructura básica | `src/`, `pyproject`, LICENSE, `.gitignore`, versión literal, `py.typed`, tests en venv limpio, Makefile |
| 1→2 | Calidad verificable | lint + tipos + cobertura por módulo + CI con todos los gates y matriz; regresiones que fallan en el tag anterior; mutación |
| 2→3 | Lista para producción | validación central + contrato; casos borde y a escala; docs con ejemplos ejecutados; doctests; idioma comprobado |
| 3→4 | Publicada y mantenida | SemVer, tag por versión, `release-check`, guarda en `publish.yml`, build + `twine check`, multi-versión, preparado para agentes |
| 4→5 | Excelencia sostenida | línea base de benchmarks, attestations, Dependabot, acciones por SHA, ensayo en TestPyPI, protección de ramas |

## 8.5 Fichas de bug y taxonomía
Ficha: **ID · síntoma · causa raíz · cómo se detectó · solución · archivo/commit · test de regresión (existe/falta + evidencia de que falla en el tag anterior) · ¿puede ocurrir en otras librerías? · clase `C-nn`.** Taxonomía en la Parte 9.

## 8.6 Reglas de `CLAUDE.md`: se prueban antes de adoptarlas
Una regla se declara «no negociable» solo si (1) responde a un fallo observado, (2) se comprueba con una orden o un test, (3) esa comprobación **pasa** en el repo y **señala** el problema cuando se introduce (control negativo).
Etiqueta cada regla: **`[test]`** la comprueba la suite · **`[CI]`** un job · **`[comando]`** una orden manual · **`[guía]`** criterio de revisión no mecánico. Documenta la prueba de cada regla (`CLAUDE_MD_RULES.md`):
regla · origen · comprobación · ¿pasa en el repo? · control negativo. Una regla que el repo incumple se registra como deuda; una regla inexacta se **corrige** (R-07 pedía `rc_context` y el código no lo usaba: se reescribió como «no modificar `rcParams`» con test para todas las gráficas).

Reglas base recomendadas (todas con su etiqueta; ver el origen de cada una en la Parte 9):
- **R-01** Cambios quirúrgicos `[guía]` · **R-02** Validar contra referencia independiente `[test]` · **R-03** Idioma en lo visible `[test]` · **R-04** Avances incrementales; tag **después** de subir la versión `[comando]`
- **R-05** Versión: literal en `__init__.py`, nunca `importlib.metadata` `[test]` · **R-06** Opcionales con mensaje `pip install` `[guía]` · **R-07** No modificar estado global (`rcParams`) `[test]`
- **R-08** Validación central, NaN antes de comparar, cotas de tamaño, registros validados `[test]` · **R-09** Checklist de renombre (`make obsoletas`) `[comando]` · **R-10** Leer el catálogo de bugs antes de validar `[guía]`
- **R-11** Casos borde obligatorios `[test]` · **R-12** CI en versión mínima `[CI]` · **R-13** Todo símbolo de `__all__` documentado y en el contrato `[test]` · **R-14** Complejidad anunciada con test de tiempo `[test]`
- **R-15** Ejemplos y doctests son tests `[test]` · **R-16** Todo bug corregido deja tres huellas `[test]` · **R-17** Cada rama parte de `origin/main` actualizado `[comando]` · **R-18** No cambiar versiones de acciones por intuición `[guía]`

## 8.7 Entregables (`docs/retrospectiva/`)
`LESSONS_LEARNED.md` (lecciones con evidencia, qué pasó/por qué/cómo evitarlo/dónde se automatizó; peticiones repetidas) · `BUG_CATALOG.md` (fichas del historial `H-nn`, bugs corregidos `W-nn`, defectos hallados `D-nn`, taxonomía) ·
`SCORECARD.md` (14 dimensiones con criterio, evidencia y media comprobada) · `PLAYBOOK.md` (checklist por nivel con comandos) · `CLAUDE_MD_RULES.md` (reglas probadas) · `RESUMEN_EJECUTIVO.md` (1 página: estado medido, pruebas de infraestructura ✅/‼️,
scorecard, rezagada y acción, contradicciones, NO VERIFICADO). **Antes de dar por buena cualquier cifra, recalcúlala.**

## 8.8 Informe final de una auditoría
Archivos creados/modificados · resultados de las pruebas de infraestructura (✅/‼️ una por una) · dimensión más rezagada y acción de mayor impacto (si hay empate, cuáles empatan y cómo se desempató) ·
contradicciones halladas entre docs, tests y código · qué NO se pudo verificar (protección de ramas de GitHub, causa exacta de fallos con logs perdidos, attestations, actividad de la comunidad).

---

# Parte 9 — Catálogo de errores

## 9.1 Taxonomía de clases (C-nn) con ejemplos reales
| Clase | Descripción | Prevención | Detección |
|---|---|---|---|
| **C-01 Validación de entrada faltante** | acepta datos inválidos; falla aguas abajo con error opaco | capa central; tests de entradas malformadas | contrato |
| **C-02 Caso degenerado no considerado** | demanda 0, datos constantes, n < 8 | listar degenerados al diseñar | tests parametrizados |
| **C-03 Import opcional sin mensaje** | `ImportError` crudo | mensaje `pip install …[extra]` | `monkeypatch.setitem(sys.modules, …, None)` |
| **C-04 CI/publicación que falla por el entorno** | pasa en local; falla por configuración externa | ensayo en TestPyPI; guardas | logs **completos** del CI |
| **C-05 Documentación desactualizada** | docs/CLAUDE.md apuntan al estado anterior | grep de obsoletos en CI; docs como tests | `make obsoletas` |
| **C-06 Efecto secundario de refactor** | validación nueva rompe una llamada interna válida | buscar llamadas internas; parámetro escape explícito | tests de integración |
| **C-07 Estado global** | gráficas cambian `rcParams` | `rc_context` o no tocarlo | test de `rcParams` por gráfica |
| **C-08 Versión en varios sitios** | se desincroniza | fuente única | test de versión |
| **C-09 NaN pasa las comparaciones** | `x <= 0` es `False` para NaN | `isfinite` antes de comparar | barrido con `nan`, `inf` |
| **C-10 Documentación con API inventada** | ejemplos nunca ejecutados | README como tests | ejecutar bloques |
| **C-11 Complejidad documentada ≠ real** | O(n²) anunciado, O(n³) real | medir | test de tiempo |
| **C-12 Desbordamiento por fórmula directa** | `a**n / n!` | recurrencias estables | prueba a escala 10× |
| **C-13 Duplicados fusionados en silencio** | lista de dicts volcada a `dict` | rechazar duplicados | test con nombres repetidos |
| **C-14 Validación solo en parte de las rutas** | capa central existe pero hay rutas sin ella | barrido sobre `__all__` | test de contrato |
| **C-15 Código sin test / CI que no verifica** | módulo al 0 %; gates ausentes | cobertura por módulo; gates en CI | `make cov`, `make check` |
| **C-16 Recorte o descarte silencioso** | cota fija o datos fuera de horizonte descartados | `UserWarning` o error | datos degenerados |
| **C-17 Funcionalidad sin documentar** | símbolos nuevos sin README/Sphinx | test `__all__` ↔ docs | `test_documentacion` |
| **C-18 Parámetros sin cota → bloqueo** | tamaños/presupuestos sin límite | `MAX_*`, límite de iteraciones | barrido 1e7/1e9 con timeout |
| **C-19 Doctests que nunca se ejecutan** | `--doctest-modules` desactivado | activarlo desde el primer ejemplo | test de configuración |
| **C-20 Ejemplo con borde numérico** | `100 < x < 130` falla si `x == 100.0` | mostrar valor redondeado | doctests |
| **C-21 Empates numéricos en heurísticas** | el desempate cambia con el orden de las sumas | tolerancia relativa; datos enteros en tests | comparar con versión directa |
| **C-22 Referencia externa menos precisa** | la otra librería difiere en el 6.º decimal | constantes con `brentq`, origen documentado | contraste cruzado |
| **C-23 Nombre que colisiona con una opción** | `from importlib.metadata import version` en `conf.py` | importar el módulo | `sphinx -W` |
| **C-24 Metadatos de instalación obsoletos** | egg-info viejo en `sys.path`; venvs sin reinstalar | `--import-mode=importlib`; reinstalar al subir versión | `test_version` |
| **C-25 Comprobación que coincide con su propio comando** | el grep de obsoletos se encuentra a sí mismo | excluir `.github/`, CLAUDE.md, retrospectiva | probar el paso en local |
| **C-26 `-0.0` en resultados** | `round(-1e-16, 10)` | `+ 0.0` | `copysign` en el test |
| **C-27 `!` en shell no detiene `set -e`** | `! grep …` no falla | `if grep …; then exit 1; fi` | forzar una coincidencia |
| **C-28 Rama desde base antigua / ref desactualizada** | conflictos; `origin/main` viejo | fetch con refspec; `merge-base --is-ancestor` | R-17 |
| **C-29 Captura amplia que oculta errores** | `except Exception` sin salida | parámetro `errors=` | test con función que lanza |
| **C-30 Política de texto sin comprobación** | «idioma X» sin test | `test_idioma` con control negativo | el propio test |
| **C-31 Reemplazo global sin contexto** | glosario cambia claves de datos | claves ≠ cabeceras; revisar diff | suite completa |
| **C-32 Test de regresión que no falla sin el fix** | protege nada | `make regresion` + `make mutaciones` | los scripts |
| **C-33 Versión congelada en metadatos de instalación** | `importlib.metadata` en `__init__` | literal + `dynamic` | `test_version` |
| **C-34 Un comando de verificación, varias variantes** | CI, publish, PR template, docs difieren | Makefile único | `grep` del comando |
| **C-35 Regla documentada que el código no cumple** | R-07 pedía `rc_context` | probar cada regla en el repo | `grep` + test del invariante |
| **C-36 Versión de release elegida sin mirar PyPI / tag antes de subir la versión** | `400 File exists`, saltos de versión | `pip index versions`; `release-check` | guarda en `publish.yml` |
| **C-37 Error de especificación** | se implementa lo pedido, no lo querido | confirmar con un ejemplo | revisión de la persona |
| **C-38 Ejecutar código antiguo sin cotas** | agota la memoria del runner (señal 143) | `RLIMIT_AS` en el hijo | log del runner |
| **C-39 Cifra o afirmación copiada** | CHANGELOG/SCORECARD que PyPI/git desmienten | recalcular al escribir; tests que parsean tablas | `pip index`, `git ls-remote` |
| **C-40 Test de detector demasiado laxo** | `W-nn` aceptado en cualquier parte del catálogo | exigir la fila de la ficha; probar borrando fichas | prueba en copia |

## 9.2 Errores frecuentes y soluciones (operativos)
| Error | Causa | Solución |
|---|---|---|
| `import milib` falla tras `pip install nombre-en-pypi` | `src/` tiene un nombre distinto al módulo | renombrar `src/viejo/` → `src/milib/` y actualizar imports |
| `import milib` desde otra carpeta usa código viejo | egg-info obsoleto en `src/` | `--import-mode=importlib`; `make install` |
| `__version__` no cambia tras subir la versión | metadatos congelados | literal en `__init__.py`; `make install` |
| Docs muestran el nombre antiguo del módulo | `.rst` con `autofunction:: viejo.X` | reemplazar en todos los `.rst`; `make obsoletas` |
| `sphinx -W` falla con referencias ambiguas | `autoclass` duplicado; `shape (n,)` con atributo `n` | `:no-index:` en la segunda; `napoleon_use_ivar = True` |
| Ejemplos de `examples/` dejan de funcionar tras un renombre | nadie los ejecutaba | `make examples` y `test_ejemplos.py` |
| `mmc`/funciones con factoriales dan `OverflowError` | fórmula directa | recurrencia estable |
| Un test «pasa» con el bug presente | no se probó contra el tag anterior | `make regresion`, `make mutaciones` |
| CI verde pero ruff/mypy rotos | el CI solo ejecutaba pytest | gates en el CI |
| El runner muere con código 143 | código sin cotas agotó la memoria | límite de memoria al hijo |
| `git fetch origin main` y `origin/main` sigue viejo | refspec implícito | `git fetch origin +refs/heads/main:refs/remotes/origin/main` |
| Conflictos al abrir el PR | rama creada desde una base antigua | R-17; reiniciar tras un squash |
| `ruff` distinto en local y en CI | versión sin fijar o comando distinto | `ruff~=X.Y`; `make lint` único |
| Hook `Stop` en bucle infinito | no respeta `stop_hook_active` | salir con 0 si es `true` |
| El CI corre dos veces por commit | triggers `push` y `pull_request` | `push` solo a `main` o `concurrency` (*no probado*) |

---

# Parte 10 — Anexos

## 10.1 Checklist de «terminado» para un PR
```bash
make check                       # lint, tipos, tests, cobertura global y por módulo, build, docs, ejemplos, obsoletas, regresión
make mutaciones                  # si se corrigió un bug
git merge-base --is-ancestor origin/main HEAD
make release-check TAG=vX.Y.Z    # solo si sube la versión
```

## 10.2 Checklist de release
- [ ] `pip index versions nombre-en-pypi` consultado; versión libre
- [ ] Versión subida **solo** en `src/milib/__init__.py`; `make install`
- [ ] Entrada en `CHANGELOG.md` (con «Cambios que rompen compatibilidad»)
- [ ] `make check` con código 0 (`make regresion` incluido)
- [ ] `make release-check TAG=vX.Y.Z` correcto (el wheel tiene la versión del tag; con otro tag falla)
- [ ] PR a `main`, CI verde en el último commit, merge
- [ ] Release de GitHub con tag `vX.Y.Z` apuntando a `main` **después** del merge (lo crea la persona responsable)
- [ ] `publish.yml` en verde; `pip install nombre-en-pypi==X.Y.Z` en un venv limpio; un ejemplo ejecutado
- [ ] `CLAUDE.md` con el estado medido actualizado

## 10.3 Comandos de verificación rápida
```bash
make install | check-fast | check | test | cov | lint | types | build | docs | examples | obsoletas | regresion | mutaciones | clean
make release-check TAG=vX.Y.Z      make notas-release VERSION=X.Y.Z
pip index versions nombre-en-pypi  git ls-remote --tags origin  git describe --tags --abbrev=0
unzip -l dist/*.whl | grep py.typed      python -m json.tool .claude/settings.json
git fetch origin +refs/heads/main:refs/remotes/origin/main && git merge-base --is-ancestor origin/main HEAD
```

## 10.4 Resultado de las pruebas de este documento
Las plantillas de la Parte 3 se extrajeron **del propio documento** a un proyecto de juguete (`milib`, distribución `nombre-en-pypi`, una función con validación central) y se ejecutaron:

| Prueba | Resultado |
|---|---|
| `make install` | ✅ exit 0 (43 s en un venv nuevo) |
| `make check-fast` (lint + tipos + tests) | ✅ exit 0; 50 tests pasan, 3 omitidos (manifiesto vacío) |
| `make check` (lint, tipos, cobertura 100 %, build, docs `-W`, ejemplos, obsoletas, regresión) | ✅ exit 0 en 11 s |
| `make build` → wheel con `py.typed`; nombres de archivo normalizados (`nombre_en_pypi-0.1.0…`) | ✅ |
| `make release-check TAG=v0.1.0` | ✅ exit 0 |
| `make release-check TAG=v0.1.1` | ✅ falla («el tag no coincide con la versión construida») |
| `make notas-release VERSION=0.1.0` / versión inexistente | ✅ imprime la sección / ✅ exit 2 |
| `make regresion` con un bug real presente en el tag anterior (`v0.0.1`) | ✅ `2 fallan, 0 pasan sin deber` |
| `make regresion` con un test independiente del bug (control negativo) | ✅ exit 2 y señala el test |
| `test_trazabilidad` con la ficha del bug / sin ella | ✅ pasa / ✅ falla |
| `make mutaciones` (2 mutantes) | ✅ ambos muertos |
| `SessionStart` remoto / local (`env -u CLAUDE_CODE_REMOTE`) / `settings.json` | ✅ exit 0 / ✅ exit 0 sin salida / ✅ JSON válido |
| `Stop`: árbol limpio · solo README · cambio válido · `import os` sin usar · test roto · `stop_hook_active=true` | ✅ exit 0 sin ejecutar `make` · ✅ exit 0 sin ejecutar · ✅ corre y pasa · ✅ exit 2 con `F401` · ✅ exit 2 con el fallo · ✅ exit 0 sin ejecutar |
| `ci.yml` y `publish.yml` | ✅ YAML válido (**no ejecutados en GitHub**) |

**Defectos que esta prueba encontró en el primer borrador de las plantillas (y ya están corregidos aquí):**
1. `ruff check src/ tests/ benchmarks/ scripts/ examples/` falla con `E902` si un directorio aún no existe → el Makefile usa `$(wildcard …)`; el CI y la publicación llaman a `make lint types` (una sola definición).
2. El esqueleto del test de contrato y el de `_utils.py` no pasaban `ruff` (orden de imports, varios imports en una línea).
3. `test_readme.py` importaba `matplotlib` sin que fuera dependencia del proyecto → ahora fija `MPLBACKEND=Agg` por entorno.
4. `test_version.py` y el paso de instalación limpia del CI consultaban los metadatos con el nombre del **módulo** (`milib`) cuando la **distribución** se llama `nombre-en-pypi` → `PackageNotFoundError`.
5. `comprobar_version_release.py` esperaba el sdist con el nombre del módulo; el sdist usa el nombre de la distribución normalizado con `_`.
6. Los validadores centrales no traían tests: con solo el test de contrato la cobertura quedaba en 75 % y `make cov` falló (el gate funcionó) → se añadió `tests/test_utils.py`.

No probado en el juguete: publicación real, `attestations`, `concurrency`, ejecución de los workflows en GitHub.

## 10.5 Límites de este documento (NO VERIFICADO)
- Publicación real en PyPI/TestPyPI con las plantillas de la Parte 3.6–3.7 y el ensayo de §3.7.1 (necesitan un publicador de confianza configurado fuera del repo).
- `attestations: true` con el publicador actual; efecto de `concurrency` sobre el doble disparo del CI.
- Protección de ramas y exigencia de revisión de CODEOWNERS (configuración de GitHub).
- Plantillas en Windows (`SIGALRM`, `RLIMIT_AS`, `make`): las plantillas asumen Linux/macOS.
- Dependabot, acciones por SHA, CodeQL y OpenSSF Scorecard: recomendados, no implementados en walopy.
- Las cifras de walopy citadas (30 commits, 70 funciones públicas, 524 textos, 1 288 tests, media 3,71) son de 2026-10-02 y se recalcularon ese día; no las reutilices como referencia sin recalcular las tuyas.

---

*Versión 2.0 — construida a partir de `pccpy` (v1) y `walopy` (v0.1.0 → v0.3.0 + infraestructura de agentes). Si la usas en otro proyecto y encuentras un fallo, añade la ficha a tu catálogo y propón el cambio aquí.*
