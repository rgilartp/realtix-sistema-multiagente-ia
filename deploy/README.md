# Despliegue del sistema multiagente de IA

Guía de B13 (ADR-09 y ADR-10). El servidor es la instancia `tg2-servidor` (EC2 m7i-flex.large,
us-east-1, Ubuntu 24.04), con el grupo de seguridad `tg2-web`, y responde en
`https://tg2-multiagente.duckdns.org`. Los comandos de tu equipo se corren en WSL, desde la carpeta
del proyecto.

## Qué corre

| Servicio | Imagen | Qué hace |
|---|---|---|
| `proxy` | `deploy/Dockerfile.proxy` (Node 24 → `caddy:2.11`) | HTTPS automático, la web (OVT simulada, widget y consola), `/api` y `/health` al backend, límites de cuerpo y cabeceras de seguridad (`deploy/Caddyfile`) |
| `backend` | `Dockerfile` (`python:3.12-slim`, dos etapas) | La API; una o más réplicas |
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
    una URL.
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
servidor y agregada al repositorio con `gh`. Nunca se usan tus credenciales:

```bash
ssh -i ~/.ssh/tg2-ec2.pem ubuntu@tg2-multiagente.duckdns.org \
  'ssh-keygen -t ed25519 -N "" -C tg2-servidor -f ~/.ssh/despliegue && cat ~/.ssh/despliegue.pub' > despliegue.pub
gh repo deploy-key add despliegue.pub --title tg2-servidor   # de solo lectura, por defecto
rm despliegue.pub
```

En el servidor, `~/.ssh/config` usa esa llave para `github.com`. El repositorio se trae dentro de
`/home/ubuntu/realtix`, donde ya está el `.env`, con `git init`, `git remote add` y `git fetch`.

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

## Una corrida de evaluación

```bash
./deploy/desplegar.sh --evaluacion        # antes de la corrida
# ... desde tu equipo: uv run python scripts/evaluar.py --corrida corrida-1 --api https://tg2-multiagente.duckdns.org ...
./deploy/desplegar.sh                     # al terminar: el modo de evaluación queda apagado
```

## Operación

- **Estado y registros:**
  ```bash
  docker compose --env-file .env --env-file deploy/servidor.env ps
  docker compose --env-file .env --env-file deploy/servidor.env logs --tail 50 backend
  ```
- **Dos réplicas** (RNF-02):
  ```bash
  docker compose --env-file .env --env-file deploy/servidor.env up -d --wait --scale backend=2
  ```
- **Monitor:** `.github/workflows/monitor.yml` revisa `/health` cada 15 minutos con la variable
  `DOMINIO` del repositorio. La disponibilidad sale de `gh run list --workflow monitor.yml`.
  Mientras la instancia esté apagada, el monitor falla: esas horas cuentan como no disponibles.
- **Apagar para ahorrar créditos:** EC2 → Detener instancia. Al encenderla, actualiza DuckDNS
  (paso 2); Compose arranca solo (`restart: unless-stopped`).
- **Si el SSH falla:** casi siempre es la IP de tu casa. Actualiza la regla de SSH de `tg2-web`.
