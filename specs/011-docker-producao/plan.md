# Plano de Implementação: Docker para Produção

**Branch**: `011-docker-producao` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/011-docker-producao/spec.md`

## Resumo

Pilha de produção em um único `docker-compose.yaml` com quatro serviços (`redis`, `solr`, `db`, `app`). O serviço `app` usa uma imagem imutável (`_docker/prod/Dockerfile`) que embute o backend Django, o frontend Vite já compilado, os estáticos coletados (`collectstatic` com `backend.settings.fake`), o Nginx e os scripts de inicialização. Em runtime, `start.sh` gera/persiste a `SECRET_KEY`, reescreve `backend_data/.env` a partir das variáveis de ambiente do Compose, migra o banco, prepara o Solr, inicia Celery, Gunicorn (WSGI, socket unix), Daphne (ASGI/WebSocket, socket unix) e, em primeiro plano, o Nginx (porta 80). Dois scripts de raiz (`upprod.sh`, `dprod.sh`) são a interface de subida/descida. O Django detecta o modo de produção pela existência de `backend_data/.env`.

## Contexto Técnico

**Linguagem/Versão**: Bash (scripts), Python 3.14 (imagem-base `python:3.14.10-bookworm`; projeto exige `>=3.12,<4.0`), configuração Nginx, YAML Compose.

**Dependências Principais**: Docker Compose v2; imagem-base `leandrojatai/building_foundation:0003` (traz Poetry, Node.js 26, Nginx, cliente PostgreSQL 18, Java/Tesseract/LibreOffice — feature 010); `gunicorn ^26.2.0`, `daphne ^4.2.3`, `celery ^5.7.0`, `python-decouple ^3.8`, `dj-database-url ^3.1.2`, `django-vite ^3.2.0`; imagens `redis:bookworm`, `solr:9.7`, `pgvector/pgvector:0.8.7-pg18-bookworm`.

**Armazenamento**: PostgreSQL 18 (volume `dbdata`), Redis (`redis_data`), Solr (`solr9_data`, `solr9_configsets`), volumes do app `data`, `media`, `logs`. SQLite apenas no build (`fake.py`).

**Testes**: validação operacional (ver `quickstart.md`); `bash -n` nos scripts, `nginx -t` na imagem, `docker compose config`; pytest existente não cobre esta feature (não há testes automatizados dos artefatos Docker).

**Plataforma Alvo**: servidor Linux com Docker.

**Tipo de Projeto**: infraestrutura/serviço-web (contêiner único de aplicação + serviços de apoio).

**Metas de Desempenho**: Gunicorn com 9 workers, `--timeout 300`, `--max-requests 1000`; Nginx com 1 worker e 1024 conexões; estáticos com `gzip_static` e cache de 7 dias.

**Restrições**: upload até 4 GB (`client_max_body_size 4G`); timeouts de proxy 75s/600s; sem portas auxiliares publicadas; build sem acesso ao PostgreSQL.

**Escala/Escopo**: uma instância por projeto Compose; múltiplas instâncias variando `COMPOSE_PROJECT_NAME` e `APP_PORT`.

## Verificação da Constituição

| Princípio | Gate | Status |
|---|---|---|
| I. Backend modular | Nenhum app novo; configurações novas (`fake.py`) ficam em `backend/settings/` e `zenv.py` já existente | Atendido |
| II. Configuração por ambiente, sem segredos | Segredos vêm de variáveis de ambiente/`backend_data/.env`; `SECRET_KEY` gerada no primeiro start e persistida no volume; `.env_prod_compose` traz apenas valores de exemplo `startprod1` (documentados como "customizar para produção!") | Atendido (com ressalvas em `research.md`) |
| III. Paridade dev/prod via Docker | Mesmos serviços de apoio (PostgreSQL 18 pgvector, Redis, Solr 9.7) e mesma imagem-base; prefixo `COMPOSE_PROJECT_NAME`; scripts `upprod.sh`/`dprod.sh` | Atendido |
| IV. API REST gerada | Fora do escopo; Nginx apenas encaminha `/api` ao Gunicorn | N/A |
| V. Frontend Vite integrado | Build `npm run build` na imagem; manifesto lido de `STATIC_ROOT` | Atendido |
| VI. Tempo real e assíncrono | Daphne atende `/ws/`; Celery iniciado pelo `start.sh`; Redis com healthcheck | Atendido |
| VII. Português do Brasil | Mensagens de `start_daphne.sh`/`start_gunicorn.sh` em PT-BR; `start.sh` mistura PT/EN (herança) | Atendido com ressalva menor |
| VIII. Qualidade verificável | Sem testes automatizados para artefatos Docker; validação por `quickstart.md` e tarefas de verificação | Justificado (infraestrutura) |
| Restrição "Segurança" | `ALLOWED_HOSTS=["*"]` e CORS `*` abertos no esqueleto | Justificado (documentado como débito) |
| Restrição "Mídia" | `/mediaredirect/` `internal`, alias em `backend_media/media/` | Atendido |

Reverificação pós-design: sem novas violações.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/011-docker-producao/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ambiente-e-compose.md
│   ├── scripts-e-processos.md
│   └── nginx.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
upprod.sh                          # sobe a pilha
dprod.sh                           # derruba a pilha + chown
_docker/prod/
├── .env_prod_compose              # variáveis do Compose (exemplo)
├── Dockerfile                     # imagem do app
├── docker-compose.yaml            # redis, solr, db, app
├── start.sh                       # entrypoint (CMD)
├── start_gunicorn.sh              # WSGI em socket unix
├── start_daphne.sh                # ASGI em socket unix
├── wait-for-pg.sh                 # (desativado em start.sh)
├── wait-for-solr.sh               # feature 008 (usado no bloco Solr)
├── solr_cli.py                    # feature 008
├── genkey.py                      # gera SECRET_KEY
└── nginx/
    ├── backend_docker.conf        # server {} e upstreams -> /etc/nginx/conf.d/
    └── nginx_docker.conf          # nginx.conf -> /etc/nginx/nginx.conf
backend/settings/
├── fake.py                        # settings só para collectstatic no build
├── zenv.py                        # detecção de produção (backend_data/.env)
├── project.py                     # SITE_URL, CSRF_TRUSTED_ORIGINS, DATABASES
└── frontend.py                    # STATIC_ROOT, DJANGO_VITE
```

**Decisão de Estrutura**: toda a infraestrutura de produção fica isolada em `_docker/prod/`; apenas dois scripts na raiz e três módulos de settings tocam o código Django. Nenhum modelo novo.

## Rastreamento de Complexidade

Sem violações. (As ressalvas de segurança estão em `research.md`.)

## Detalhamento de Implementação

### 1. Variáveis do Compose — `_docker/prod/.env_prod_compose`

Arquivo `KEY=VALUE` passado por `--env-file` (usado só para interpolação no Compose, não é `env_file` do contêiner). Conteúdo, nesta ordem: comentário `# customizar para produção!`; `APP_PORT=9001`; `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB` = `startprod1`; `SOLR_PASSWORD=startprod1`, `SOLR_DB=startprod1`; comentário explicando que `SITE_URL` deve ser o domínio real (exemplo `https://meusite.com.br`); `SITE_URL=http://192.168.15.9:9001`. Não define `SOLR_USER` (o Compose usa o padrão `startprod1`) e `SOLR_DB` não é referenciado em nenhum lugar.

### 2. Scripts de raiz

- `upprod.sh`: `COMPOSE_PROJECT_NAME=${1:-startprod1}` e `sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/prod/.env_prod_compose --progress=plain -f _docker/prod/docker-compose.yaml up --build -d` (sem quebra de linha final no arquivo; executável).
- `dprod.sh`: mesmo nome/padrão; `sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file ... -f ... down`; depois `USER=\`whoami\``, `GROUP=\`whoami\``, `sudo chown -R $USER:$GROUP .`.

### 3. `_docker/prod/docker-compose.yaml`

Serviços e opções (todos em `networks: [app-net]`, rede `driver: bridge`):

| Serviço | `container_name` | Imagem/Build | Itens-chave |
|---|---|---|---|
| `redis` | `${COMPOSE_PROJECT_NAME:-startprod1}-redis` | `redis:bookworm` | `restart: always`; healthcheck `["CMD","redis-cli","ping"]` interval 5s, timeout 10s, retries 10; volume `redis_data:/data`; `ports` comentado (`6379:6379`) |
| `solr` | `...-solr` | `solr:9.7` (comentário: validar 9.8 pois causa erro) | `command: bin/solr start -c -f`; volumes `solr9_data:/var/solr`, `solr9_configsets:/opt/solr/server/solr/configsets`; `ports` comentado (`8983:8983`) |
| `db` | `...-db` | `pgvector/pgvector:0.8.7-pg18-bookworm` | env `POSTGRES_PASSWORD/USER/DB` (`${VAR:-startprod1}`), `PGDATA: /var/lib/postgresql/data/`; volume `dbdata:/var/lib/postgresql/data/`; `command: ["postgres","-c","shared_preload_libraries=pg_stat_statements"]`; `ports` comentado (`5433:5432`) |
| `app` | `...-app` | build `context: ../../.`, `dockerfile: _docker/prod/Dockerfile` | `user: "root:root"`; `restart: always`; ambiente e volumes da FR-007; `depends_on` db/solr `service_started`, redis `service_healthy`; `ports: "${APP_PORT:-9001}:80"` |

Ambiente do `app`: `DEBUG: 'False'`, `USE_SOLR: 'True'`, `SOLR_COLLECTIONS: ${P}_arq1,${P}_arq2`, `SOLR_URL: http://${SOLR_USER:-startprod1}:${SOLR_PASSWORD:-startprod1}@${P}-solr:8983`, `IS_ZK_EMBEDDED: 'True'`, `TZ: America/Sao_Paulo`, `COMPOSE_PROJECT_NAME: ${P}`, `POSTGRES_*`, `SITE_URL: ${SITE_URL:-http://localhost:${APP_PORT:-9001}}` (`P` = `${COMPOSE_PROJECT_NAME:-startprod1}`). Volumes top-level: `dbdata`, `data`, `media`, `logs`, `solr9_data`, `solr9_configsets`, `redis_data`.

### 4. `_docker/prod/Dockerfile` (ordem exata)

1. `FROM leandrojatai/building_foundation:0003`.
2. `ENV LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `DEBIAN_FRONTEND=noninteractive`, `ROOT_HOME=/var/project`, `HOME=${ROOT_HOME}/backend`.
3. `RUN mkdir -p` de `${HOME}/run`, `${HOME}/logs/celery`, `${ROOT_HOME}/backend_data`, `${ROOT_HOME}/backend_media`; `WORKDIR ${HOME}`.
4. `COPY manage.py ${HOME}`; `COPY py* ${HOME}` (casa somente `pyproject.toml`; `poetry.lock` NÃO é copiado) e `RUN poetry install --without dev,test,docs`.
5. `#COPY package-lock.json ${HOME}` (comentado); `COPY package.json ${HOME}`; `COPY vite.config.js ${HOME}`; `ADD _frontend ${HOME}/_frontend`; `RUN npm install`; `RUN npm run build` (gera `_frontend/dist/frontend`, ver feature 007).
6. `ADD solr`, `drfautoapi`, `backend`, `_templates`, `_docker` para `${HOME}/<nome>`.
7. `RUN python3 manage.py collectstatic --noinput --clear --settings=backend.settings.fake --no-default-ignore` e `RUN rm -rf ${HOME}/db.sqlite3`.
8. `COPY _docker/prod/nginx/backend_docker.conf /etc/nginx/conf.d/.` e `COPY _docker/prod/nginx/nginx_docker.conf /etc/nginx/nginx.conf`.
9. `COPY` de `start.sh`, `wait-for-pg.sh`, `wait-for-solr.sh`, `start_gunicorn.sh`, `start_daphne.sh`, `solr_cli.py`, `genkey.py` para `${HOME}`; `RUN chmod +x` nos cinco `.sh`.
10. `RUN useradd -r --no-create-home -g root nginx` (comentário: Debian não possui o usuário `nginx`); `USER nginx`; `ENV DEBIAN_FRONTEND=teletype`; `EXPOSE 80/tcp`; `VOLUME ["${ROOT_HOME}/backend_data", "${ROOT_HOME}/backend_media", "${HOME}/logs"]`; `CMD ["/var/project/backend/start.sh"]`.

### 5. `_docker/prod/start.sh`

Estrutura (bash, sem `set -e`):

1. Banner amarelo `====> StartPRD...`; linha comentada de `wait-for-pg.sh`.
2. Função `change_env_file` (arquivo alvo `E=${ROOT_HOME}/backend_data/.env`):
   - `KEY` = conteúdo de `backend_data/secret.key` se existir; senão `python3 genkey.py` gravado em `secret.key`.
   - `sed -i -E "s|^SECRET_KEY.+$|\n|g" $E`; `echo "SECRET_KEY = $KEY" >> $E`.
   - `declare -A env_vars` (regex → linha completa, com valores padrão por `${VAR:=...}`): `^DATABASE_URL_PRD.+$` → `DATABASE_URL_PRD = ${DATABASE_URL:=postgresql://${POSTGRES_USER:=startprod1}:${POSTGRES_PASSWORD:=startprod1}@${COMPOSE_PROJECT_NAME}-db:5432/${POSTGRES_DB:=startprod1}}`; `^SOLR_COLLECTIONS.+$`; `^SOLR_URL.+$` (padrão `http://startprod1:startprod1@${COMPOSE_PROJECT_NAME}-solr:8983`); `^DEBUG.+$` (`False`); `^DJANGO_VITE_DEV_MODE.+$` (`False`); `^REDIS_HOST.+$` (`${COMPOSE_PROJECT_NAME}-redis`); `^FOLDER_DEBUG_CONTAINER.+$` (`${HOME}`); `^COMPOSE_PROJECT_NAME.+$`; `^TZ.+$` (`America/Sao_Paulo`); `^SITE_URL.+$` (`http://localhost:${APP_PORT:=9001}`).
   - `echo "" >> $E`; para cada regex: `sed -i -E "s|$regex|<linha>|g" $E`; `key=$(echo "<linha>" | cut -d' ' -f1)`; se `grep -q "^$key" $E` falhar, acrescentar a linha.
   - `echo "" >> $E` e `sed -i -E ':a;N;$!ba;s/\n{3,}/\n\n/g' $E`.
3. `yes yes | python3 manage.py migrate`.
4. Bloco Solr (detalhes de `solr_cli.py` e `wait-for-solr.sh` na feature 008): variáveis `USE_SOLR=${USE_SOLR:=False}`, `SOLR_URL`, `SOLR_COLLECTIONS`, `NUM_SHARDS=1`, `RF=1`, `MAX_SHARDS_PER_NODE=1`, `IS_ZK_EMBEDDED=True`; se `USE_SOLR` ∈ {`True`,`true`}: imprime configurações, executa `/bin/bash wait-for-solr.sh $SOLR_URL`; **quando o retorno é `1`** (o script sai com 1 em sucesso e 2 em falha) define `ZK_EMBEDDED="--embedded_zk"` se `IS_ZK_EMBEDDED` ∈ {`True`,`true`} e executa `python3 solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED`; senão "Solr is offline, not possible to connect."; se desabilitado, "Solr support is not initialized.".
5. `sleep 3`; `rm ${HOME}/logs/celery/*.pid`; (comentário com configuração `celery multi` de 16 workers); `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=backendredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log`.
6. `sleep 3`; `/bin/sh start_gunicorn.sh &`; `sleep 3`; `/bin/sh start_daphne.sh &`; `sleep 5`; `echo "Iniciando NGINX..."`; `/usr/sbin/nginx -g "daemon off;"`.

### 6. `start_gunicorn.sh` / `start_daphne.sh` / `genkey.py` / `wait-for-pg.sh`

- Gunicorn: variáveis `NAME="BACKEND.wsgi"`, `DJANGODIR`, `SOCKFILE=/var/project/backend/run/gunicorn.sock`, `USER=GROUP=\`whoami\``, `NUM_WORKERS=9`, `TIMEOUT=300`, `MAX_REQUESTS=1000`; cria o diretório do socket; `exec gunicorn backend.wsgi:application --name $NAME --log-level info --timeout $TIMEOUT --workers $NUM_WORKERS --max-requests $MAX_REQUESTS --user $USER --access-logfile .../gunicorn_access.log --error-logfile .../gunicorn_error.log --bind=unix:$SOCKFILE`.
- Daphne: `MAX_RETRIES=5`, `RETRY_COUNT=0`; laço `while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do daphne -u $SOCKFILE backend.asgi:application --access-log .../daphne_access.log -v1 && break; echo "Falha ao iniciar Daphne, tentativa N de 5"; incrementa; sleep 5; done`; se `RETRY_COUNT -eq MAX_RETRIES` imprime "Falha ao iniciar Daphne após 5 tentativas" e `exit 1`.
- `genkey.py`: função `generate_secret()` retorna 50 caracteres escolhidos por `random.SystemRandom().choice` do alfabeto `abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)`; `__main__` imprime o resultado.
- `wait-for-pg.sh`: `while true`, imprime "Esperando Database Setup", `COUNT_PG=\`psql $1 -c '\l \q' | grep backend | wc -l\``, sai do laço se `COUNT_PG` ≠ 0, `sleep 10`. (Filtra por `grep backend`, o que só funciona se o nome do banco contiver "backend"; por isso está desativado.)

### 7. Nginx — `_docker/prod/nginx/*.conf`

Detalhes de locations em `contracts/nginx.md`. Pontos de implementação: `nginx_docker.conf` substitui o `nginx.conf` da imagem (`user nginx root; worker_processes 1; error_log /var/log/nginx/error.log warn; pid /var/run/nginx.pid;` `events { worker_connections 1024; }` e `http {}` com `mime.types`, `log_format main`, `access_log /var/log/nginx/access.log main`, `sendfile off`, `server_tokens off`, `keepalive_timeout 300`, `proxy_connect_timeout 75s`, `proxy_read_timeout 300s`, gzip, `include /etc/nginx/conf.d/*.conf`). `backend_docker.conf` entra em `conf.d` e contém upstreams e o `server`.

### 8. Settings Django

- `backend/settings/zenv.py` (feature 001): `production = Path(__file__).parents[3] / "backend_data" / ".env"`; `production = production.exists()`; `config = AutoConfig(search_path=(Path(__file__).parents[3] / "backend_data") if production else None)`; `DEBUG = config("DEBUG", default=False, cast=bool)`; `BASE_DIR = Path(__file__).parents[1]`; `PROJECT_DIR = Path(__file__).parents[2]`; `FOLDER_DEBUG_CONTAINER = Path(config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str))`. No contêiner `parents[3]` = `/var/project`.
- `backend/settings/project.py`: `SECRET_KEY = config("SECRET_KEY")` (sem padrão); `ALLOWED_HOSTS = ["*"]`; `SITE_URL = config("SITE_URL", default="http://192.168.15.9:9001")`; `CSRF_TRUSTED_ORIGINS = [SITE_URL]`; `SESSIONS_COOKIE_SECURE = not DEBUG` (nome incorreto — o Django só reconhece `SESSION_COOKIE_SECURE`; sem efeito); `DATABASES = {"default": config("DATABASE_URL_DEV" if DEBUG else "DATABASE_URL_PRD", cast=db_url)}` (`db_url` = `dj_database_url.parse`).
- `backend/settings/frontend.py`: `STATIC_URL="static/"`, `STATIC_ROOT=PROJECT_DIR/"collectedstatic"`, `DJANGO_VITE_ASSETS_PATH=PROJECT_DIR/"_frontend"/"dist"`, `STATICFILES_DIRS=[DJANGO_VITE_ASSETS_PATH]` (+ `_frontend/src/assets` se `DEBUG`); `DJANGO_VITE_DEV_MODE = config(..., default=True) and DEBUG`; `DJANGO_VITE["default"] = {"dev_mode": ..., "manifest_path": (DJANGO_VITE_ASSETS_PATH if dev else STATIC_ROOT) / "frontend" / ".vite" / "manifest.json"}`.
- `backend/settings/fake.py`: `from .project import *`; `DEBUG = False`; `DJANGO_VITE_DEV_MODE = False`; `DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(PROJECT_DIR, "db.sqlite3")}}`; `DJANGO_VITE = {"default": {"dev_mode": False, "manifest_path": DJANGO_VITE_ASSETS_PATH / "frontend" / ".vite" / "manifest.json"}}` (manifesto lido do `dist`, pois o `collectstatic` ainda não gerou `collectedstatic`). Observação: `project.py` é importado antes e avalia `SECRET_KEY` e `DATABASE_URL_PRD` (ver `research.md`).

### 9. Interação com outras features

`/mediaredirect/` é o prefixo usado por `X-Accel-Redirect` em `backend/api/mixins.py` e `backend/utils/views.py` (feature 009); `/ws/sync/` vem de `backend/utils/routing.py` (feature 006); `solr_cli.py`/`wait-for-solr.sh` e `SOLR_*` (feature 008); `vite.config.js` gera `service-worker.js` e `manifest.json` do PWA em `_frontend/dist/frontend` (feature 007).
