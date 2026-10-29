# Despliegue del sistema multiagente de IA

Guía de B13 (ADR-09 y ADR-10). El servidor es la instancia `tg2-servidor` (EC2 m7i-flex.large,
us-east-1, Ubuntu 24.04), con el grupo de seguridad `tg2-web`, y responde en
`https://tg2-multiagente.duckdns.org`. Los comandos de tu equipo se corren en WSL, desde la carpeta
del proyecto.

## Qué corre

| Servicio | Imagen | Qué hace |
|---|---|---|
| `proxy` | `deploy/Dockerfile.proxy` (Node 24 → `caddy:2.11`) | HTTPS automático, la web (OVT simulada, widget y consola), `/api` y `/health` al backend, límites de cuerpo y cabeceras de seguridad (`deploy/Caddyfile`) |
| `backend` | `Dockerfile` (`python:3.12-slim`; etapas de uv, construcción y ejecución) | La API; una o más réplicas |
| `chromadb` | `chromadb/chroma:1.5.9` | La base de conocimiento |
| `postgres` | `postgres:16` | Conversaciones, casos, interacciones y checkpoints |
| `generar-realsit` | la del backend | Genera una vez la base sintética de RealSit en su volumen |

Volúmenes con nombre: `postgres-data`, `chroma-data`, `caddy-data`, `caddy-config` y
`datos-sinteticos` (montado en solo lectura en el backend). Sobreviven a reinicios y a
`docker compose down`; solo `down -v` los borra (RNF-15).

## Configuración

- **Secretos:** solo en tu `.env`, que se copia sin cambios. Nunca entra en una imagen
  (`.dockerignore`) ni en git (`.gitignore`). En el servidor queda con permisos 600.
- **Lo no secreto:** en `deploy/servidor.env` (versionado), que tiene prioridad sobre el `.env`:
  el dominio, la OVT simulada encendida, la vigencia, el umbral y los pesos de la confianza.
- **Lo que arma Compose** (`docker-compose.yml`): la conexión a PostgreSQL (con `POSTGRES_USER`,
  `POSTGRES_PASSWORD` y `POSTGRES_DB` del `.env`) y a Chroma, la ruta de RealSit y el origen
  permitido (`https://<dominio>`).
  - La contraseña de PostgreSQL debe usar solo letras, números, `-` o `_`, porque va dentro de
    una URL. Si el `.env` copiado trae la de desarrollo (`realtix_dev`), PostgreSQL solo escucha
    en `127.0.0.1` del servidor; aun así, conviene cambiarla en el `.env` antes del primer
    despliegue (después habría que cambiarla también dentro de la base).
- **Modo de evaluación y fallas inyectables:** apagados por defecto, aunque el `.env` diga otra
  cosa. Solo los enciende `./deploy/desplegar.sh --evaluacion`, durante una corrida (A9).

## Preparar el servidor (una vez)

Lo hace Rodolfo, porque lleva `sudo`:

1. **Encender la instancia:** EC2 → Instancias → `tg2-servidor` → Estado de la instancia →
   Iniciar.
2. **Actualizar DuckDNS:** la IP pública cambia cada vez que la instancia se detiene y se vuelve
   a encender. En https://www.duckdns.org, pega la «Dirección IPv4 pública» en
   `tg2-multiagente` y pulsa «update ip».
3. **Revisar `tg2-web`:**
   - SSH (22) desde «Mi IP»; si cambió la IP de tu casa, edita esa regla;
   - HTTP (80) y HTTPS (443) desde `0.0.0.0/0`. El 80 lo usa Let's Encrypt.
4. **Instalar Docker:**
   ```bash
   ssh -i ~/.ssh/tg2-ec2.pem ubuntu@tg2-multiagente.duckdns.org 'sudo bash -s' < deploy/preparar_servidor.sh
   ```
5. **Copiar el `.env`:**
   ```bash
   scp -i ~/.ssh/tg2-ec2.pem .env ubuntu@tg2-multiagente.duckdns.org:/home/ubuntu/realtix/.env
   ssh -i ~/.ssh/tg2-ec2.pem ubuntu@tg2-multiagente.duckdns.org 'chmod 600 /home/ubuntu/realtix/.env'
   ```

Luego, sin `sudo`: el código llega con una llave de despliegue de solo lectura, creada en el
servidor y agregada al repositorio con `gh` por Rodolfo. Nunca se usan sus credenciales.

1. **Crear la llave en el servidor y agregarla** (desde tu equipo):
   ```bash
   ssh -i ~/.ssh/tg2-ec2.pem ubuntu@tg2-multiagente.duckdns.org \
     'test -f ~/.ssh/despliegue || ssh-keygen -q -t ed25519 -N "" -C tg2-servidor -f ~/.ssh/despliegue; cat ~/.ssh/despliegue.pub' > despliegue.pub
   gh repo deploy-key add despliegue.pub --title tg2-servidor   # de solo lectura, por defecto
   rm despliegue.pub
   ```
2. **Configurar GitHub y el repositorio en el servidor** (`ssh -i ~/.ssh/tg2-ec2.pem
   ubuntu@tg2-multiagente.duckdns.org`). La huella de GitHub debe ser
   `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`, la publicada en su documentación:
   ```bash
   ssh-keyscan -t ed25519 github.com > /tmp/github && ssh-keygen -lf /tmp/github
   cat /tmp/github >> ~/.ssh/known_hosts
   printf 'Host github.com\n  IdentityFile ~/.ssh/despliegue\n  IdentitiesOnly yes\n' > ~/.ssh/config
   chmod 600 ~/.ssh/config
   cd ~/realtix                     # ya tiene el .env: por eso se usa git init y no git clone
   git init -q -b main
   git remote add origin git@github.com:rgilartp/realtix-sistema-multiagente-ia.git
   git fetch -q origin && git checkout -q -B main origin/main
   ```

## Desplegar o actualizar

```bash
ssh -i ~/.ssh/tg2-ec2.pem ubuntu@tg2-multiagente.duckdns.org
cd ~/realtix
./deploy/desplegar.sh                     # main
./deploy/desplegar.sh --version v0.9.0    # una etiqueta
```

El script hace todo esto:

1. trae la versión;
2. construye las imágenes;
3. genera la base de RealSit si falta y comprueba su huella contra
   `src/data/huella_realsit.sha256`;
4. levanta Compose y espera la salud;
5. ejecuta la ingesta (idempotente: sin cambios no gasta);
6. verifica `https://tg2-multiagente.duckdns.org/health`.

## Prueba en el equipo

Con `DOMINIO=localhost` delante, la variable de la terminal gana sobre `deploy/servidor.env`, y
Caddy usa su autoridad local en lugar de pedir a Let's Encrypt el dominio real:

```bash
export DOMINIO=localhost
docker compose --env-file .env --env-file deploy/servidor.env --profile herramientas run --rm generar-realsit
docker compose --env-file .env --env-file deploy/servidor.env up -d --build --wait
curl -k https://localhost/health
```

## Una corrida de evaluación

```bash
./deploy/desplegar.sh --evaluacion        # antes de la corrida
# ... desde tu equipo: uv run python scripts/evaluar.py --corrida corrida-1 --api https://tg2-multiagente.duckdns.org ...
./deploy/desplegar.sh                     # al terminar: el modo de evaluación queda apagado
```

Si la instancia se reinicia en medio de una corrida, los contenedores vuelven con el modo de
evaluación encendido (`restart: unless-stopped` conserva su configuración). Por eso se corre
siempre `./deploy/desplegar.sh` sin la opción al terminar.

## Operación

- **Estado y registros:**
  ```bash
  docker compose -f docker-compose.yml -f deploy/compose.servidor.yml --env-file .env --env-file deploy/servidor.env ps
  docker compose -f docker-compose.yml -f deploy/compose.servidor.yml --env-file .env --env-file deploy/servidor.env logs --tail 50 backend
  ```
- **Dos réplicas** (RNF-02):
  ```bash
  docker compose -f docker-compose.yml -f deploy/compose.servidor.yml --env-file .env --env-file deploy/servidor.env up -d --wait --scale backend=2
  ```
- **Monitor:** `.github/workflows/monitor.yml` revisa `/health` cada 15 minutos en el horario
  hábil (lunes a viernes, de 8:00 a 16:45 en Bogotá), con la variable `DOMINIO` del repositorio.
  Fuera del horario no corre, para no agotar los 2.000 minutos mensuales de GitHub Actions del
  plan gratuito. La disponibilidad sale de `gh run list --workflow monitor.yml`. Si la instancia
  se apaga en horario hábil, el monitor falla y esas horas cuentan como no disponibles.
- **Chroma en el servidor:** no publica puerto; solo lo alcanza el backend por la red de Compose
  (`deploy/compose.servidor.yml`, ADR-26). Sus avisos de seguridad no tienen versión corregida.
- **Apagar para ahorrar créditos:** EC2 → Detener instancia. Al encenderla, actualiza DuckDNS
  (paso 2); Compose arranca solo (`restart: unless-stopped`).
- **Si el SSH falla:** casi siempre es la IP de tu casa. Actualiza la regla de SSH de `tg2-web`.
