# CLAUDE.md — sistema multiagente de IA para Realtix

Trabajo de grado de Rodolfo Angel Gilart Pulido y Dayanna Liceth Varón Puerto (director: MsC. Juan
Carlos Barrero Calixto). Rodolfo es el único operador. Realtix no participa en el desarrollo.
Este archivo resume las reglas; el detalle está en `docs/ESPECIFICACION_TECNICA.md`.

## Precedencia de fuentes

1. `docs/06_ADENDA_MARCO_JURIDICO_Y_PRUEBAS.md`, en lo normativo, la base de conocimiento y lo que
   el documento de grado promete medir.
2. `docs/ESPECIFICACION_TECNICA.md`.
3. Los FINAL de `docs/paquete/documentos/`, salvo lo que la especificación cambia (sección 2).
4. El resto de `docs/paquete/`, solo como referencia.

El material de referencia (las tres fuentes anteriores) no se modifica y los ganchos de estilo no lo
tocan; gitleaks sí lo revisa.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `src/agents/` | `graph.py`, `state.py`, `nodes/` (un archivo por nodo) y `prompts/` (versionados) |
| `src/services/` | Dominio sin LangGraph: confianza, liquidación, ICA, calendario, acceso, horario, resumen, minimización |
| `src/data/` | Modelos, esquema, `RealSitAdapter` y su implementación sintética; generador en `generar/` |
| `src/store/` | Almacén propio en PostgreSQL (SQLAlchemy Core) |
| `src/integrations/` | Fábrica de modelos, embeddings, Chroma, BM25 y RRF, LangSmith y anonimizador |
| `src/api/` | FastAPI, capa de acceso, puntos de acceso y modo de evaluación |
| `src/evaluacion/` | Ejecutor de escenarios, evaluadores, juez, RAGAS, métricas y reportes |
| `src/config.py`, `src/container.py` | Configuración (pydantic-settings) y contenedor de dependencias |
| `knowledge_base/` | Normas en Markdown por colección y su `fuentes.yaml` |
| `datos/` | Tarifas, calendario y regímenes por año gravable |
| `scripts/` | Curaduría, ingesta, trazabilidad y utilidades |
| `web/` | OVT simulada, widget y consola (Vite) |
| `deploy/` | Caddyfile, guía y scripts de despliegue |
| `tests/` | Unitarias, de contrato e integración; `escenarios/`, `componentes/` y `fixtures/` |
| `docs/` | Especificación, adenda, paquete, `decisiones/`, `resumenes/`, `cambios_para_documento.md` y demás |
| `reports/` | Resultados de las corridas |

## Lectura eficiente (sección 0.1)

- Al empezar un bloque, lee su sección 8 y solo las secciones que ella cite.
- No leas el paquete completo: los FINAL, cuando implementes un requerimiento; el código de 6.3.1,
  solo en B3.
- No leas archivos grandes completos si basta una parte; para la curaduría, escribe scripts en lugar
  de leer las normas; resume la salida de las pruebas.

## Protocolo de cada bloque (sección 0.2)

Rodolfo lanza cada bloque con una línea («Haz el bloque B7»). Es su primera vez con Claude Code:
mensajes en español claro, sin jerga; cuando tenga que hacer algo, pasos numerados con los comandos
exactos para copiar.

1. **Preparar:** `git switch main && git pull`; árbol limpio.
2. **Planear (modo plan):** sección 8 del bloque y lo que cite; plan breve con archivos, pruebas,
   riesgos y paradas. Es la única aprobación en un bloque sin paradas.
3. **Rama:** `bNN-tema`, desde `main`.
4. **Implementar:** commits pequeños, Conventional Commits y `Refs`.
5. **Probar:** unitarias y las del bloque, con la salida real resumida.
6. **Documentar:** `docs/resumenes/bNN.md` (qué se hizo, RF y RNF con nombre corto, cómo se
   verificó y cifras) y `docs/cambios_para_documento.md`.
7. **PR** con la plantilla (`.github/pull_request_template.md`).
8. **CI:** `gh pr checks --watch`; si falla, corregir y volver a subir.
9. **Revisión independiente:** un subagente con contexto limpio compara el diff con la sección 8
   del bloque, este archivo y la lista de chequeo del PR; se corrige lo que encuentre.
10. **Fusionar** (sin parada pendiente y CI en verde): `gh pr merge --merge --delete-branch` y
    `git switch main && git pull`.
11. **Etiqueta**, si el bloque la lleva: `git tag -s vX.Y.Z -m "…"` y `git push origin vX.Y.Z`.
12. **Reportar y detenerse:** mensaje que empieza con `BLOQUE BNN TERMINADO`, de 5 líneas como
    máximo: qué quedó, enlace del PR, estado de la CI, gasto de API si lo hubo y lo que sigue.

Varios bloques en una sesión: protocolo completo para cada uno, en orden; solo el primero pasa por
el modo plan; los demás dejan el plan en la descripción del PR. Se detiene al final del último o en
la primera parada.

## Paradas (sección 0.3)

Mensaje que empieza con `PARADA:` y dice, en pasos numerados, qué hace Rodolfo y qué responde.

| Bloque | Cuándo | Qué hace Rodolfo |
|---|---|---|
| B1 | Al terminar | Crea `.env` desde `.env.example` |
| B2 | Antes del PR | Revisa las vistas lado a lado y hace el commit de verificación |
| B6 | Antes del PR | Revisa la hoja de referencias y hace el commit de aprobación |
| B13 | Al empezar el despliegue | Enciende el servidor, da el subdominio de DuckDNS y copia `.env` |
| B15 | Después de la corrida 2 | Califica la calibración con Dayanna, aplica la usabilidad, aprueba el umbral |
| Cualquiera | `sudo`, contradicción con la adenda o la especificación, o prueba que falla 3 veces seguidas | Ejecuta, decide o lo lleva al chat de desarrollo |

Fuera de esas paradas, no se pide confirmación.

## Reglas de trabajo

1. El proyecto se llama siempre «sistema multiagente de IA» y la empresa, «Realtix».
2. Solo datos sintéticos; ningún material no público de RealSit.
3. No inventar normas, tarifas, fechas ni resultados; todo dato tributario sale de `datos/` o de
   `knowledge_base/`, con su fuente.
4. Separación de capas: los nodos no tienen lógica tributaria, los servicios no conocen LangGraph y
   ningún agente toca SQL; todo pasa por `RealSitAdapter`.
5. Cada entrega lista los RF y RNF con su nombre corto (p. ej. «RF-AUT-02 · Restricción a predios
   propios»).
6. Probar antes de entregar y mostrar la salida real; nunca afirmar que algo funciona sin haberlo
   ejecutado.
7. Nunca commit ni push a `main`, ni `--no-verify` ni `--no-gpg-sign`; si la firma falla, es una
   parada.
8. No leer `.env` ni llaves privadas, ni imprimir secretos. Nunca se ejecutan comandos que
   muestren variables de entorno o la configuración resuelta (para validar Compose,
   `docker compose config -q`).
9. Fechas (sección 0.4): ninguna fecha exacta del trabajo en documentos, resúmenes, ADR, PR,
   commits, reportes ni informe; si hace falta, «octubre de 2026». Las fechas tributarias sí van.
   En resultados, el tiempo se registra como duración (ms). Si un escenario necesita un municipio
   distinto de Bogotá, se usa Medellín.
10. No modificar `docs/ESPECIFICACION_TECNICA.md` ni la adenda, salvo que Rodolfo lo pida
    expresamente; si algo debe cambiar, se propone en el PR.
11. Cifra de adopción de IA en Colombia: 7,5 % de las empresas (MinTIC, agosto de 2024), ninguna
    otra.
12. Ahorrar tokens (sección 0.1).
13. No cambiar una decisión de la sección 2 (ADR) sin consultarla.
14. Sobreajuste (A8, ADR-24): ningún texto, pregunta ni cifra de los escenarios va en prompts ni en
    código; cada corrección es general y trae su caso de regresión
    (`tests/test_evaluacion_sobreajuste.py` lo vigila).

## Convenciones

- **Ramas:** `b01-esqueleto`, `fix/tema`, `docs/tema`.
- **Commits:** `tipo(alcance): descripción` con tipos `feat`, `fix`, `test`, `docs`, `refactor`,
  `build`, `ci` y `chore`; descripción en español, en infinitivo, de 72 caracteres como máximo. Pie
  `Refs: RF-AUT-02 · Restricción a predios propios` cuando aplique, y `Co-Authored-By`.
- **Fusión:** solo merge commit; la rama se borra. **Etiquetas:** `v0.1.0` (B5), `v0.5.0` (B9),
  `v0.9.0` (B13), `v1.0.0` (B16).
- **Código:** Python 3.12 con tipos en las firmas públicas; ruff; nombres del dominio en español y
  técnicos en inglés cuando sean convención; docstrings breves en español; dinero con `Decimal` y
  redondeo explícito; registros JSON con `id_conversacion` y sin datos personales.
- **Pruebas:** marcas `unit`, `integration` y `req("RF-… · nombre corto")`; la matriz sale de
  `scripts/trazabilidad.py`.
- **Dependencias:** versiones exactas en `pyproject.toml` y `uv.lock`: la estable más reciente con
  al menos 7 días en PyPI; `faker` fijo; `anthropic` menor que 2.0 (`langchain-anthropic` 1.7.6).
- **Clave de Anthropic del sistema multiagente de IA:** `REALTIX_ANTHROPIC_API_KEY`, nunca
  `ANTHROPIC_API_KEY`.
- **Imágenes de Docker:** nunca incluyen `.env`; `.dockerignore` lo excluye en B13.

## Comandos frecuentes

```bash
uv sync --all-groups
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run pre-commit run --all-files
docker compose up -d postgres chromadb
uv run python scripts/trazabilidad.py
```

## Decisiones (ADR, en `docs/decisiones/`)

- ADR-01: desarrollo con Claude Code en WSL 2 (Ubuntu 24.04), Docker Engine dentro de WSL.
- ADR-02: Sonnet 5.5 en el orquestador; Haiku 5.5 en IPU, ICA, general y OCR; Opus 5.5 solo juez.
- ADR-03: confianza, respuesta y escalamiento sin modelo.
- ADR-04: recuperación híbrida Chroma 1.5.9 + BM25; 8 por canal, RRF k = 60, 5 al prompt.
- ADR-05: RealSit en solo lectura (`mode=ro`); estado propio en PostgreSQL.
- ADR-06: tarifas y plazos por año gravable en `datos/`, con fuente.
- ADR-07: OVT simulada con token HMAC-SHA256.
- ADR-08: widget en iframe (React 19, Vite 8, Tailwind 4) y consola web.
- ADR-09: proxy Caddy con HTTPS automático y DuckDNS.
- ADR-10: EC2 m7i-flex.large en us-east-1, plan Free.
- ADR-11: registro propio de interacciones sin datos personales; LangSmith para trazas.
- ADR-12: modo humano: una conversación escalada ya no la atienden los agentes.
- ADR-13: si escala antes de la confianza, `nivel_confianza = 0.0` con su motivo.
- ADR-14: cuatro casos de enrutamiento sin transiciones nuevas (8 nodos, 8 transiciones).
- ADR-15: GitHub Flow en el plan gratuito: un PR por bloque, ganchos y CI.
- ADR-16: modo de evaluación con reloj inyectable y `X-Escenario-Id`, solo por configuración.
- ADR-17: confianza 0,4 / 0,4 / 0,2 y umbral 0,7; la falta de cobertura escala siempre.
- ADR-18: `POST /api/v1/escalamiento` es el botón; solo `nodo_escalamiento` registra casos.
- ADR-19: `plataforma_general` con manual de la OVT simulada y glosario con fuentes.
- ADR-20: predial 2026 con el Acuerdo 780 de 2020 y la resolución de rangos de 2026.
- ADR-21: usabilidad interna con SUS y evaluación heurística de los dos autores.
- ADR-22: respuestas de referencia de los autores, cada una con su fuente.
- ADR-23: tres campos auxiliares del turno en `AgentState` (marcas, respuesta final, descartadas).
- ADR-24: ajustes al plan de pruebas A1 a A9 (Wilson con n = escenarios, juez validado y
  congelado, verificador de referencias, regla contra el sobreajuste) y mejoras R1 a R4.
- ADR-25: correcciones del instrumento después de la corrida 1 (el juez y RAGAS ven herramientas,
  notas, recibo y aviso; juez v3 lista las afirmaciones sin fuente antes del veredicto; A4 con 3
  repeticiones; «Distrital»; fuga sin textos públicos).
