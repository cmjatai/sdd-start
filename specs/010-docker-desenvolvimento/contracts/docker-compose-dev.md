# Contrato: Compose de desenvolvimento (serviços, portas, volumes, rede)

**Arquivo**: `_docker/dev/docker-compose.yaml` | **Variáveis**: `_docker/dev/.env_dev_compose` | **Projeto padrão**: `startdev1`

## Invocação

```bash
docker compose -p <nome> --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml <up --build -d | down>
```

Executada da **raiz do repositório** (os caminhos `--env-file`/`-f` são relativos a ela; os `context`/volumes do YAML são relativos à pasta do YAML: `../../.`).

## Serviços

| Serviço | Contêiner | Imagem / build | Porta host:contêiner | Rede | Reinício |
|---|---|---|---|---|---|
| `redis` | `<nome>-redis` | `redis:bookworm` | `6379:6379` | `appdev-net` | `on-failure` |
| `solr` | `<nome>-solr` | `solr:9.7` | `8983:8983`, `9983:9983` | `appdev-net` | `on-failure` |
| `front` | `<nome>-front` | build `_docker/dev/Dockerfile.Dev.Front` | `5173:5173` | `appdev-net` | `on-failure` |
| `db` | `<nome>-db` | `pgvector/pgvector:0.8.7-pg18-bookworm` | `5433:5432` | `appdev-net` | `on-failure` |
| `appdev` | `<nome>-appdev` | build `_docker/dev/Dockerfile.Dev` | `${APP_PORT:-9099}:9000` | `appdev-net` | `on-failure` |

`appdev.depends_on`: `front`, `db`, `redis`, `solr` (sem `healthcheck`/`condition`).

## Volumes

| Origem | Destino | Serviço |
|---|---|---|
| `redis_data` | `/data` | `redis` |
| `solr9_data` | `/var/solr` | `solr` |
| `solr9_configsets` | `/opt/solr/server/solr/configsets` | `solr` |
| `dbdata` | `/var/lib/postgresql/data/` | `db` |
| `../../.` (raiz do repositório) | `/var/project/backend` | `front`, `appdev` |
| `/mnt/volumes/backend_media` (host) | `/var/project/backend_media` | `appdev` |

Volumes nomeados e rede ficam prefixados pelo projeto (`<nome>_dbdata`, `<nome>_appdev-net`…). `down` não remove volumes nomeados (sem `-v`).

## Variáveis de interpolação do Compose

| Variável | Padrão no YAML | Efeito |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `startdev1` | prefixo de `container_name`, hosts, coleções Solr (`<nome>_arq1`, `<nome>_arq2`) |
| `APP_PORT` | `9099` | porta do host para a aplicação (porta interna fixa 9000) |
| `POSTGRES_PASSWORD` / `POSTGRES_USER` / `POSTGRES_DB` | `startdev1` | credenciais do `db` e do `appdev` |
| `SOLR_USER` | `startdev1` | usuário na `SOLR_URL` (não existe em `.env_dev_compose`) |
| `SOLR_PASSWORD` | `startdev1` | senha na `SOLR_URL` |

## Variáveis de ambiente fixas do `appdev`

`DEBUG='True'`, `USE_SOLR='True'`, `IS_ZK_EMBEDDED='True'`, `TZ=America/Sao_Paulo`, `SOLR_COLLECTIONS=<nome>_arq1,<nome>_arq2`, `SOLR_URL=http://<SOLR_USER>:<SOLR_PASSWORD>@<nome>-solr:8983`, `COMPOSE_PROJECT_NAME`, `POSTGRES_*`.

## Endereços de acesso (instância padrão)

| Serviço | URL / endereço no host | Dentro da rede Docker |
|---|---|---|
| Aplicação Django | `http://localhost:9099` | `startdev1-appdev:9000` |
| Vite (HMR) | `http://localhost:5173` | `startdev1-front:5173` |
| PostgreSQL | `localhost:5433` | `startdev1-db:5432` |
| Redis | `localhost:6379` | `startdev1-redis:6379` |
| Solr | `http://localhost:8983` | `startdev1-solr:8983` |
| ZooKeeper embutido | `localhost:9983` | `startdev1-solr:9983` |

## Contratos dos `Dockerfile`

| Imagem | `FROM` | Usuário | `EXPOSE` | `VOLUME` | `CMD` |
|---|---|---|---|---|---|
| `Dockerfile.Dev` (appdev) | `leandrojatai/building_foundation:0003` | root | `9000/tcp` | `/var/project/backend_media`, `/var/project/backend` | `/var/project/backend/_docker/dev/start-dev.sh` |
| `Dockerfile.Dev.Front` (front) | `node:26.13.0-bookworm` | `backend` (uid/gid 1001) | `5173/tcp` | `/var/project/backend` | `/var/project/backend/startfront-dev.sh` |
| `foundation/Dockerfile` | `python:3.14.10-bookworm` | root | — | — | `python3` |
