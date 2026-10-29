#!/usr/bin/env bash
# Prepara tg2-servidor (Ubuntu 24.04) para el sistema multiagente de IA (B13).
#
# Instala Docker Engine y el complemento de Compose desde el repositorio oficial de Docker, agrega al
# usuario `ubuntu` al grupo `docker` y crea la carpeta del proyecto. Necesita `sudo`, así que lo
# ejecuta Rodolfo (CLAUDE.md, paradas) desde su equipo:
#
#   ssh -i ~/.ssh/tg2-ec2.pem ubuntu@<subdominio>.duckdns.org 'sudo bash -s' < deploy/preparar_servidor.sh
#
# Es idempotente: se puede repetir sin daño.
set -euo pipefail

# Huella publicada por Docker para la clave de su repositorio de apt (versión anterior de su guía de
# instalación, «apt-key fingerprint 0EBFCD88»). Antes de dar de alta el archivo se exige que traiga
# una sola clave principal y que sea esa (auditoría de seguridad).
HUELLA_DOCKER="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"

if [[ ${EUID} -ne 0 ]]; then
  echo "Este script necesita sudo." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q ca-certificates curl git gnupg

install -m 0755 -d /etc/apt/keyrings
clave=$(mktemp)
trap 'rm -f "${clave}"' EXIT
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o "${clave}"
# La huella de cada clave principal (la línea fpr que sigue a cada pub), no la de las subclaves.
huellas=$(gpg --show-keys --with-colons "${clave}" | awk -F: '/^pub:/ {p=1; next} p && /^fpr:/ {print $10; p=0}')
if [[ "${huellas}" != "${HUELLA_DOCKER}" ]]; then
  echo "La clave GPG de Docker no es la publicada (o trae otras claves); no se instala." >&2
  exit 1
fi
install -m 0644 "${clave}" /etc/apt/keyrings/docker.asc
# shellcheck source=/dev/null
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
usermod -aG docker ubuntu
install -d -o ubuntu -g ubuntu -m 700 /home/ubuntu/realtix

docker --version
docker compose version
echo "Listo: Docker instalado y /home/ubuntu/realtix creada."
