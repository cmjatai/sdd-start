# Modelo de Dados: Ambiente Docker de Desenvolvimento

**Funcionalidade**: `010-docker-desenvolvimento`

**Não há tabelas, modelos Django nem migrações novas nesta funcionalidade.** As estruturas relevantes são de configuração e de infraestrutura, descritas abaixo. O banco `startdev1` (PostgreSQL 18 + pgvector) recebe o esquema das demais features por `manage.py migrate` no start do `appdev`.

## 1. Arquivo `backend/.env` (desenvolvimento)

Formato `CHAVE = valor` (espaços ao redor do `=` são aceitos por `python-decouple`). Ignorado pelo Git. Lido por `backend/settings/zenv.py` (`AutoConfig`).

| Chave | Origem | Valor típico em dev | Gerida por `start-dev.sh`? |
|---|---|---|---|
| `SECRET_KEY` | **manual** (obrigatória) | valor aleatório longo (nunca versionar) | Não |
| `DATABASE_URL_DEV` | script | `postgresql://startdev1:<senha>@startdev1-db:5432/startdev1` | Sim |
| `DATABASE_URL_PRD` | manual/legado | usada só com `DEBUG=False` | Não |
| `REDIS_HOST` | script | `startdev1-redis` | Sim |
| `REDIS_PORT` | manual | `6379` (padrão no settings) | Não |
| `FOLDER_DEBUG_CONTAINER` | script | `/var/project/backend` | Sim |
| `DEBUG` | script | `True` | Sim |
| `DJANGO_VITE_DEV_MODE` | script | `True` | Sim |
| `DEBUG_TOOLBAR_ACTIVE` | manual (comentada) | `False` | Não |
| `LOGGING_ROOT_LEVEL` | manual | `'INFO'` | Não |
| `GOOGLE_RECAPTCHA_SITE_KEY`, `GOOGLE_RECAPTCHA_SECRET_KEY` | manual | vazios em dev | Não |
| `SOLR_URL` | script | `http://startdev1:<senha>@startdev1-solr:8983` | Sim |
| `SOLR_COLLECTIONS` | script | `startdev1_arq1,startdev1_arq2` | Sim |
| `COMPOSE_PROJECT_NAME` | script | `startdev1` | Sim |
| `TZ` | script | `America/Sao_Paulo` | Sim |

Regras: após `change_env_file` cada chave gerida aparece uma vez (se já existia, a linha é substituída; se não, é anexada); `SECRET_KEY` e chaves não geridas permanecem intactas; três ou mais quebras de linha consecutivas são reduzidas a duas.

## 2. Arquivo `_docker/dev/.env_dev_compose` (interpolação do Compose)

| Variável | Padrão no arquivo | Usada em |
|---|---|---|
| `APP_PORT` | `9099` | `appdev.ports` (`${APP_PORT:-9099}:9000`) |
| `POSTGRES_PASSWORD` | senha de dev | `db.environment`, `appdev.environment` |
| `POSTGRES_USER` | `startdev1` | idem |
| `POSTGRES_DB` | `startdev1` | idem |
| `SOLR_PASSWORD` | senha de dev | composição de `SOLR_URL` em `appdev` |
| `SOLR_DB` | `startdev1` | não referenciada no compose |
| `SITE_URL` | `http://startdev1:9099` | não referenciada no compose |
| (ausente) `SOLR_USER` | — | `${SOLR_USER:-startdev1}` |
| (opcional) `COMPOSE_PROJECT_NAME` | definida por `-p` | prefixos |

## 3. Variáveis de ambiente injetadas no contêiner `appdev`

`DEBUG=True`, `USE_SOLR=True`, `SOLR_COLLECTIONS`, `SOLR_URL`, `IS_ZK_EMBEDDED=True`, `TZ=America/Sao_Paulo`, `COMPOSE_PROJECT_NAME`, `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB`; mais as do `Dockerfile.Dev`: `LANG`, `LC_ALL`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `ROOT_HOME=/var/project`, `HOME=/var/project/backend`, `POETRY_VIRTUALENVS_CREATE=false` (herdada). Opcionais lidos por `start-dev.sh` (sem valor no Compose): `DATABASE_URL`, `DJANGO_VITE_DEV_MODE`, `REDIS_HOST`, `FOLDER_DEBUG_CONTAINER`, `NUM_SHARDS`, `RF`, `MAX_SHARDS_PER_NODE`.

## 4. Infraestrutura nomeada (Compose)

| Tipo | Nome (com `-p startdev1`) | Conteúdo |
|---|---|---|
| Rede | `startdev1_appdev-net` (bridge) | DNS interno por nome de contêiner |
| Volume | `startdev1_dbdata` | dados do PostgreSQL |
| Volume | `startdev1_redis_data` | dados do Redis |
| Volume | `startdev1_solr9_data` | `/var/solr` |
| Volume | `startdev1_solr9_configsets` | `/opt/solr/server/solr/configsets` |
| *Bind mount* | `/mnt/volumes/backend_media` → `/var/project/backend_media` | mídia (`media/`, `media_cache/`) |
| *Bind mount* | raiz do repositório → `/var/project/backend` | código, `logs/`, `node_modules/`, `backend/.env` |
| Contêineres | `startdev1-redis`, `-solr`, `-front`, `-db`, `-appdev` | — |

Hostnames internos: `startdev1-db:5432`, `startdev1-redis:6379`, `startdev1-solr:8983`.

## 5. Estado de execução em disco gerado pelo `appdev`

- `logs/celery/celery1.pid`, `celery1.log`, `celery1-1.log` (padrões `%n.pid`, `%n%I.log`) — em `${HOME}/logs/celery` (repositório montado; `*.log` é ignorado pelo Git).
- `backend/.env` modificado.

## 6. Parâmetros da imagem-base (versões)

| Componente | Versão |
|---|---|
| Python | 3.14.10 (bookworm) |
| PostgreSQL client | 18 (PGDG) |
| Ghostscript | 10.08.0 (compilado, tag de release `gs10080`) |
| jbig2enc | 0.32 |
| Node.js | 26.x (NodeSource) |
| Java | OpenJDK 17 headless |
| Tesseract | pacote Debian + `tesseract-ocr-por` |
| Poetry | última disponível no PyPI no momento do build |

## 7. Dependabot (estrutura YAML)

Chaves por item: `package-ecosystem` (`npm`, `pip`, `docker`, `docker-compose`), `directory`, `schedule.interval: "weekly"`. Estrutura correta: uma lista única `updates:`; o arquivo atual a repete seis vezes (ver `research.md`, item 9).
