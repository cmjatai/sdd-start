# Contrato: Ambiente, Compose, Portas e Volumes

## Variáveis de interpolação (`_docker/prod/.env_prod_compose`)

| Variável | Valor de exemplo | Uso |
|---|---|---|
| `APP_PORT` | `9001` | porta publicada no host → 80 do `app`; também compõe o padrão de `SITE_URL` |
| `POSTGRES_PASSWORD` / `POSTGRES_USER` / `POSTGRES_DB` | `startprod1` | credenciais do `db` e do `DATABASE_URL_PRD` |
| `SOLR_PASSWORD` | `startprod1` | senha no `SOLR_URL` |
| `SOLR_DB` | `startprod1` | **não utilizada** |
| `SITE_URL` | `http://192.168.15.9:9001` | origem pública (CSRF); em produção usar o domínio real, ex.: `https://meusite.com.br` |
| `SOLR_USER` | (não definida; padrão `startprod1`) | usuário no `SOLR_URL` |
| `COMPOSE_PROJECT_NAME` | (definida via `-p` em `upprod.sh`/`dprod.sh`; padrão `startprod1`) | prefixo de nomes |

O arquivo começa com o comentário `# customizar para produção!`. Valores `startprod1` são exemplos (nunca usar em produção real).

## Serviços do Compose (`_docker/prod/docker-compose.yaml`)

| Serviço | Imagem | `restart` | Rede | Portas publicadas |
|---|---|---|---|---|
| `redis` | `redis:bookworm` | `always` | `app-net` | nenhuma (`6379:6379` comentada) |
| `solr` | `solr:9.7` | `always` | `app-net` | nenhuma (`8983:8983` comentada) |
| `db` | `pgvector/pgvector:0.8.7-pg18-bookworm` | `always` | `app-net` | nenhuma (`5433:5432` comentada) |
| `app` | build `_docker/prod/Dockerfile` (contexto = raiz do repositório) | `always` | `app-net` | `${APP_PORT:-9001}:80` |

- Healthcheck `redis`: `["CMD", "redis-cli", "ping"]`, `interval: 5s`, `timeout: 10s`, `retries: 10`.
- `db`: `command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]`; `PGDATA=/var/lib/postgresql/data/`.
- `solr`: `command: bin/solr start -c -f` (modo SolrCloud com ZooKeeper embutido).
- `app.depends_on`: `db: service_started`, `redis: service_healthy`, `solr: service_started`.
- `app.user`: `"root:root"`.

## Variáveis de ambiente do contêiner `app`

| Variável | Valor |
|---|---|
| `DEBUG` | `'False'` |
| `USE_SOLR` | `'True'` |
| `SOLR_COLLECTIONS` | `${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2` |
| `SOLR_URL` | `http://${SOLR_USER}:${SOLR_PASSWORD}@${COMPOSE_PROJECT_NAME}-solr:8983` (padrões `startprod1`) |
| `IS_ZK_EMBEDDED` | `'True'` |
| `TZ` | `America/Sao_Paulo` |
| `COMPOSE_PROJECT_NAME` | nome do projeto |
| `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB` | iguais ao `db` |
| `SITE_URL` | `${SITE_URL:-http://localhost:${APP_PORT:-9001}}` |

Variáveis definidas na imagem: `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `ROOT_HOME=/var/project`, `HOME=/var/project/backend`.

Variáveis opcionais lidas por `start.sh`: `DATABASE_URL`, `REDIS_HOST`, `DJANGO_VITE_DEV_MODE`, `FOLDER_DEBUG_CONTAINER`, `APP_PORT`, `NUM_SHARDS` (1), `RF` (1), `MAX_SHARDS_PER_NODE` (1).

## Volumes

| Nome | Ponto de montagem | Serviço |
|---|---|---|
| `dbdata` | `/var/lib/postgresql/data/` | `db` |
| `redis_data` | `/data` | `redis` |
| `solr9_data` | `/var/solr` | `solr` |
| `solr9_configsets` | `/opt/solr/server/solr/configsets` | `solr` |
| `data` | `/var/project/backend_data` | `app` |
| `media` | `/var/project/backend_media` | `app` |
| `logs` | `/var/project/backend/logs` | `app` |

Rede: `app-net` (`driver: bridge`). Hostnames internos: `<projeto>-redis`, `<projeto>-solr` (porta 8983), `<projeto>-db` (porta 5432), `<projeto>-app`.

## Porta

| Contêiner | Porta | Protocolo | Observação |
|---|---|---|---|
| `app` | 80 | TCP (HTTP/WebSocket) | `EXPOSE 80/tcp`; publicada em `APP_PORT` |

## Variáveis lidas pelo Django em produção

`SECRET_KEY`, `DEBUG`, `DATABASE_URL_PRD`, `SITE_URL`, `DJANGO_VITE_DEV_MODE`, `USE_SOLR`, `SOLR_URL`, `SOLR_COLLECTIONS`, `REDIS_HOST`, `REDIS_PORT` (padrão 6379), `FOLDER_DEBUG_CONTAINER`, `LOGGING_ROOT_LEVEL` (padrão `INFO` com `DEBUG` falso), `GOOGLE_RECAPTCHA_SITE_KEY`/`GOOGLE_RECAPTCHA_SECRET_KEY` (padrão vazio).
