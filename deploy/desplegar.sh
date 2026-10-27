#!/usr/bin/env bash
# Despliega el sistema multiagente de IA en tg2-servidor (B13; RNF-13 y RNF-15).
#
# En el servidor, dentro de /home/ubuntu/realtix:
#   ./deploy/desplegar.sh                      # la última versión de main, modo de evaluación apagado
#   ./deploy/desplegar.sh --version v0.9.0     # una etiqueta o una rama
#   ./deploy/desplegar.sh --evaluacion         # solo para una corrida (A9); al terminar, sin la opción
#
# Pasos: trae la versión con la llave de despliegue (solo lectura); construye las imágenes; genera
# la base sintética de RealSit si falta y comprueba su huella; levanta Compose y espera la salud;
# ejecuta la ingesta (idempotente: sin cambios no gasta) y verifica /health por HTTPS.
set -euo pipefail
cd "$(dirname "$0")/.."
ARGUMENTOS=("$@")

VERSION=main
EVALUACION=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      [[ $# -ge 2 ]] || { echo "--version necesita una rama o una etiqueta." >&2; exit 2; }
      VERSION="$2"; shift 2 ;;
    --evaluacion) EVALUACION=true; shift ;;
    -h | --help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "Falta el .env: cópialo con el comando scp de deploy/README.md." >&2
  exit 1
fi

echo "1/6 Versión: ${VERSION}"
git fetch --quiet --tags --prune origin
if git show-ref --verify --quiet "refs/remotes/origin/${VERSION}"; then
  git checkout --quiet -B "${VERSION}" "origin/${VERSION}"
else
  git checkout --quiet --detach "${VERSION}"
fi
git log --oneline -1
# El checkout pudo traer otra versión de este script, pero bash sigue leyendo la que abrió: se
# vuelve a ejecutar una vez, ya actualizado (el fetch y el checkout repetidos no cambian nada).
if [[ -z "${DESPLEGAR_ACTUALIZADO:-}" ]]; then
  DESPLEGAR_ACTUALIZADO=1 exec bash deploy/desplegar.sh "${ARGUMENTOS[@]}"
fi

DOMINIO=$(grep -E '^DOMINIO=' deploy/servidor.env | cut -d= -f2-)
export REALTIX_MODO_EVALUACION="${EVALUACION}"
# deploy/compose.servidor.yml quita el puerto de Chroma en el anfitrión (ADR-26).
compose=(docker compose -f docker-compose.yml -f deploy/compose.servidor.yml
  --env-file .env --env-file deploy/servidor.env)

echo "2/6 Imágenes"
"${compose[@]}" build --pull --quiet

echo "3/6 Base sintética de RealSit"
if ! "${compose[@]}" run --rm -T --no-deps --entrypoint test backend -f /realsit/realsit_sintetico.db; then
  "${compose[@]}" --profile herramientas run --rm generar-realsit
fi
huella=$("${compose[@]}" run --rm -T --no-deps --entrypoint python backend -c \
  "from src.data.huella import calcular_huella; print(calcular_huella('/realsit/realsit_sintetico.db'))" \
  | tr -d '\r')
if [[ "${huella}" != "$(cat src/data/huella_realsit.sha256)" ]]; then
  echo "La huella de la base sintética no coincide con src/data/huella_realsit.sha256." >&2
  echo "Para regenerarla: docker volume rm realtix_datos-sinteticos (con el backend detenido) y" >&2
  echo "vuelve a correr este script." >&2
  exit 1
fi
echo "Huella de RealSit: ${huella}"

echo "4/6 Servicios (modo de evaluación: ${EVALUACION})"
"${compose[@]}" up -d --wait --remove-orphans

echo "5/6 Ingesta"
"${compose[@]}" exec -T backend python scripts/ingestar.py

echo "6/6 /health por HTTPS en https://${DOMINIO}/health"
for _ in $(seq 1 30); do
  if curl -fsS --max-time 10 "https://${DOMINIO}/health"; then
    echo
    echo "Desplegado: $(git describe --tags --always) (modo de evaluación: ${EVALUACION})."
    exit 0
  fi
  sleep 10
done
echo "/health no respondió por HTTPS en 5 minutos: revisa '${compose[*]} logs proxy'." >&2
exit 1
