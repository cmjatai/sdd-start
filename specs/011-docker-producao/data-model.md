# Modelo de Dados: Docker para Produção

**Não há tabelas, modelos Django nem migrações novos nesta funcionalidade.** As estruturas relevantes são de configuração e de infraestrutura.

## 1. Arquivo `backend_data/.env` (gerado por `start.sh`)

Localização no contêiner: `/var/project/backend_data/.env` (volume `data`). Formato `CHAVE = valor` (com espaços ao redor do `=`), lido pelo `python-decouple` quando `zenv.py` detecta produção.

| Chave | Origem (variável de ambiente do contêiner) | Padrão | Lida em |
|---|---|---|---|
| `SECRET_KEY` | `backend_data/secret.key` (gerada por `genkey.py`) | — (obrigatória) | `backend/settings/project.py` |
| `DATABASE_URL_PRD` | `DATABASE_URL` ou `postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@${COMPOSE_PROJECT_NAME}-db:5432/$POSTGRES_DB` | usuário/senha/banco `startprod1` | `project.py` (`dj_database_url`) |
| `SOLR_COLLECTIONS` | `SOLR_COLLECTIONS` | `${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2` | `settings/solr.py` |
| `SOLR_URL` | `SOLR_URL` | `http://startprod1:startprod1@${COMPOSE_PROJECT_NAME}-solr:8983` | `settings/solr.py` |
| `DEBUG` | `DEBUG` | `False` | `zenv.py` |
| `DJANGO_VITE_DEV_MODE` | `DJANGO_VITE_DEV_MODE` | `False` | `settings/frontend.py` |
| `REDIS_HOST` | `REDIS_HOST` | `${COMPOSE_PROJECT_NAME}-redis` | `settings/zasyncs.py` |
| `FOLDER_DEBUG_CONTAINER` | `FOLDER_DEBUG_CONTAINER` | `${HOME}` = `/var/project/backend` | `zenv.py` |
| `COMPOSE_PROJECT_NAME` | `COMPOSE_PROJECT_NAME` | o próprio nome | informativa |
| `TZ` | `TZ` | `America/Sao_Paulo` | informativa/sistema |
| `SITE_URL` | `SITE_URL` | `http://localhost:${APP_PORT:-9001}` | `project.py` |

Regras de reescrita: (a) linhas `SECRET_KEY...` existentes viram linha em branco e uma nova `SECRET_KEY = <chave>` é anexada; (b) para as demais, `sed -E "s|^CHAVE.+$|CHAVE = valor|g"` substitui; se `grep -q "^CHAVE"` não encontrar, a linha é anexada; (c) 3+ quebras de linha consecutivas colapsam em 2. Chaves não tratadas (ex.: `GOOGLE_RECAPTCHA_*`, `LOGGING_ROOT_LEVEL`, `REDIS_PORT`) permanecem como estão se o operador as adicionar manualmente ao volume.

## 2. Arquivo `backend_data/secret.key`

Texto de uma linha com 50 caracteres do alfabeto `abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)`. Criado uma única vez; lido nos starts seguintes.

## 3. Variáveis do Compose (`_docker/prod/.env_prod_compose`)

`APP_PORT`, `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB`, `SOLR_PASSWORD`, `SOLR_DB` (não usada), `SITE_URL`. Opcionais não presentes no arquivo: `SOLR_USER` (padrão `startprod1`), `COMPOSE_PROJECT_NAME`. Detalhes em `contracts/ambiente-e-compose.md`.

## 4. Volumes nomeados

| Volume | Montagem | Conteúdo |
|---|---|---|
| `dbdata` | `db:/var/lib/postgresql/data/` | dados do PostgreSQL |
| `redis_data` | `redis:/data` | persistência do Redis |
| `solr9_data` | `solr:/var/solr` | dados do Solr |
| `solr9_configsets` | `solr:/opt/solr/server/solr/configsets` | configsets (feature 008) |
| `data` | `app:/var/project/backend_data` | `.env`, `secret.key` |
| `media` | `app:/var/project/backend_media` | `media/` e `media_cache/` (feature 009) |
| `logs` | `app:/var/project/backend/logs` | logs do Django (`backend_logger.log`), Gunicorn, Daphne, Nginx e `celery/` |

## 5. Sistema de arquivos relevante na imagem

| Caminho | Descrição |
|---|---|
| `/var/project/backend` (`HOME`) | raiz do projeto (WORKDIR) |
| `/var/project/backend/collectedstatic/` | `STATIC_ROOT` (estáticos coletados e `frontend/.vite/manifest.json`) |
| `/var/project/backend/run/` | sockets `gunicorn.sock` e `daphne.sock` |
| `/var/project/backend/logs/celery/` | `.pid` e logs do Celery |
| `/var/project/backend_data/` | volume de configuração |
| `/var/project/backend_media/media/` | `MEDIA_ROOT`; alias de `/mediaredirect/` |
| `/etc/nginx/nginx.conf` e `/etc/nginx/conf.d/backend_docker.conf` | configuração do Nginx |

## 6. Processos (estado em execução no contêiner `app`)

`start.sh` (PID 1) → `celery multi` (1 worker, hostname `backendredis`) → `gunicorn` (mestre + 9 workers) → `daphne` → `nginx` (mestre + 1 worker). Sem transições de estado persistentes além da criação de `secret.key`/`.env`.

## 7. Migrações iniciais

Nenhuma criada por esta feature. `start.sh` aplica `migrate` de todas as features anteriores a cada start (`yes yes | python3 manage.py migrate`), o que também dispara a criação de permissões e grupos (feature 003).
