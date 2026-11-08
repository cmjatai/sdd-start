# Plano de Implementação: Ambiente Docker de Desenvolvimento e Imagem-Base

**Branch**: `010-docker-desenvolvimento` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/010-docker-desenvolvimento/spec.md`

## Resumo

Fornecer um ambiente de desenvolvimento reprodutível por Docker Compose (PostgreSQL 18 + pgvector, Redis, Solr 9.7, Vite em Node 26 e a aplicação Django em `runserver`), uma imagem-base compartilhada com dev/prod (`building_foundation:0003`) e scripts de raiz que operam várias instâncias via `COMPOSE_PROJECT_NAME`. O contêiner `appdev` roda `_docker/dev/start-dev.sh`, que ajusta `backend/.env`, migra o banco, prepara o Solr, inicia um worker Celery e sobe o `runserver` na porta 9000. Os settings reconhecem se o Django roda no contêiner ou no host (`FOLDER_DEBUG_CONTAINER`) e trocam hosts/portas de banco, Redis e Solr para `localhost` quando rodam no host.

## Contexto Técnico

**Linguagem/Versão**: Python 3.14.10 (imagem-base; projeto exige `>=3.12,<4.0`), Bash, Dockerfile, YAML do Compose, Node 26 (`node:26.13.0-bookworm` no `front`; NodeSource `setup_26.x` na base)

**Dependências Principais**: Docker Engine + Compose v2; imagens `python:3.14.10-bookworm`, `node:26.13.0-bookworm`, `redis:bookworm`, `solr:9.7`, `pgvector/pgvector:0.8.7-pg18-bookworm`; Poetry (instalado por `pip3 install poetry`, sem versão fixada); Ghostscript 10.08.0; jbig2enc 0.32; LibreOffice, OpenJDK 17, Tesseract (`por`), `postgresql-client-18`; Celery 5 (`celery multi`)

**Armazenamento**: PostgreSQL 18 (volume `dbdata`), Redis (`redis_data`), Solr (`solr9_data`, `solr9_configsets`), mídia em `/mnt/volumes/backend_media` (bind mount)

**Testes**: validação operacional (`docker compose ps`, `curl`, `docker logs`); não há testes `pytest` específicos desta infraestrutura. Checagens estáticas sugeridas: `bash -n` nos scripts, `docker compose config`, `yamllint` do dependabot (ver `quickstart.md`)

**Plataforma Alvo**: host Linux com Docker e `sudo`; contêineres Debian bookworm

**Tipo de Projeto**: infraestrutura de desenvolvimento (serviço web + serviços de apoio)

**Metas de Desempenho**: N/A (primeira subida dominada pelo build; subida subsequente em segundos a poucos minutos, com Solr aguardando até 60 s)

**Restrições**: um único comando por ambiente; nenhum segredo versionado além de padrões de dev (`startdev1`); portas fixas 5433/6379/8983/9983/5173; contexto de build = raiz do repositório

**Escala/Escopo**: 5 serviços, 1 imagem-base, 2 imagens de dev, 4 scripts de raiz, 3 scripts em `_docker/dev/`

## Verificação da Constituição

*PORTÃO (gate): deve ser aprovado antes da pesquisa da Fase 0. Reavaliar após o design da Fase 1.*

| Princípio | Avaliação | Observação |
|---|---|---|
| I. Backend Django modular | Atendido / N/A | Esta funcionalidade não adiciona apps; apenas empacota e executa o `backend` existente. |
| II. Configuração por ambiente, sem segredos no repositório | Atendido com ressalva | `.env` é ignorado pelo Git e `SECRET_KEY` precisa existir previamente (não é gerada em dev). `_docker/dev/.env_dev_compose` é versionado com **senhas de exemplo de desenvolvimento**; aceitável para dev, deve ser trocado em derivados. |
| III. Paridade dev × prod via Docker | Atendido | Mesma imagem-base, mesmos serviços de apoio (PG 18 pgvector, Redis, Solr 9.7); `COMPOSE_PROJECT_NAME` prefixa contêineres/hosts/bancos/coleções; scripts de raiz. Ressalva: portas fixas dificultam instâncias simultâneas sem ajuste. |
| IV. API REST gerada | N/A | Sem endpoints novos. |
| V. Frontend Vite integrado ao Django | Atendido | Serviço `front` com HMR; `DJANGO_VITE_DEV_MODE=True` gravado no `.env`. |
| VI. Tempo real e assíncrono por padrão | Atendido | Redis publicado, worker Celery iniciado em `start-dev.sh`, Solr indexado via Celery (feature 008). |
| VII. Português do Brasil | Atendido | `TZ=America/Sao_Paulo`; mensagens dos scripts em inglês/portugês misturados (legado), documentação em pt-BR. |
| VIII. Qualidade verificável | Atendido com ressalva | Sem testes `pytest` de infraestrutura; validação por `quickstart.md`. Dependabot configurado, porém com YAML defeituoso (ver `research.md`). |

Reavaliação pós-design: sem novas violações.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/010-docker-desenvolvimento/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── docker-compose-dev.md      # serviços, portas, volumes, rede, variáveis do Compose
│   └── scripts-e-ambiente.md      # CLI dos scripts, chaves do backend/.env, imagem-base
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
.
├── _docker/
│   ├── foundation/
│   │   └── Dockerfile                 # imagem-base building_foundation:0003
│   ├── dev/
│   │   ├── .env_dev_compose           # APP_PORT, POSTGRES_*, SOLR_*, SITE_URL
│   │   ├── Dockerfile.Dev             # imagem do appdev
│   │   ├── Dockerfile.Dev.Front       # imagem do front (Vite)
│   │   ├── docker-compose.yaml        # redis, solr, front, db, appdev
│   │   ├── start-dev.sh               # bootstrap do appdev (CMD)
│   │   └── recreate_db.sh             # legado (stormdb/sddstart)
│   └── prod/                          # (feature 011; start-dev.sh reutiliza wait-for-solr.sh e solr_cli.py)
├── rdev.sh  uupdev.sh  ddev.sh        # scripts de raiz do ambiente dev
├── startfront-dev.sh                  # npm install + npm run dev
├── libreoffice_entrypoint.sh          # wrapper headless (sem uso)
├── backend/
│   ├── .dockerignore                  # (sem efeito: contexto é a raiz)
│   └── settings/{zenv,project,solr,zasyncs,medias}.py   # lógica contêiner × host
└── .github/dependabot.yml
```

**Decisão de Estrutura**: infraestrutura concentrada em `_docker/<ambiente>/` com scripts de conveniência na raiz; o contexto de build do Compose é a raiz (`context: ../../.`) e o código é montado por volume em `/var/project/backend`, de modo que as imagens de dev não copiam o código (apenas `pyproject.toml`).

## Rastreamento de Complexidade

Sem violações dos princípios. Ressalvas (portas fixas, senhas de exemplo versionadas, `.dockerignore` ineficaz, `dependabot.yml` com chave duplicada) estão em `research.md`.

---

## Detalhamento de Implementação

### 1. Imagem-base — `_docker/foundation/Dockerfile`

Construída a partir do diretório `_docker/foundation` (contexto = pasta). Camadas, nesta ordem:

1. `FROM python:3.14.10-bookworm`; `ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/root`; `WORKDIR ${HOME}`.
2. **Apt** (`--no-install-recommends`, comentários `# RUN0_PACKAGES`, `# LIBRE_PACKAGES`, `# java e tesseract` dentro do `RUN`; ao fim `apt-get clean && rm -rf /var/lib/apt/lists/*`):
   - Base: `apt-utils apt-file libpq-dev build-essential pkg-config autoconf automake libtool libleptonica-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev libcairo2-dev software-properties-common graphviz graphviz-dev procps nmap git vim curl jq pngquant poppler-utils tzdata nginx ca-certificates gnupg wget`.
   - LibreOffice: `libreoffice libreoffice-writer libreoffice-java-common libreoffice-core libreoffice-common ure hyphen-pt-br fonts-opensymbol fonts-dejavu fonts-dejavu-core fonts-dejavu-extra fonts-droid-fallback fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-lmodern fonts-lyx fonts-sil-gentium fonts-texgyre fonts-tlwg-purisa fonts-liberation fontconfig`.
   - `openjdk-17-jdk-headless tesseract-ocr tesseract-ocr-por`.
3. **PostgreSQL 18 client**: `install -d /usr/share/postgresql-common/pgdg`; baixar `https://www.postgresql.org/media/keys/ACCC4CF8.asc` para `/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc`; criar `/etc/apt/sources.list.d/pgdg.list` com `deb [signed-by=...] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main`; `apt-get update && apt-get install -y --no-install-recommends postgresql-client-18`; limpar listas.
4. **Ghostscript**: em `/tmp/ghostscript`, `wget https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10080/ghostscript-10.08.0.tar.gz`, `tar vzxfp`, `./configure && make && make install`, e `rm -rf /tmp/ghostscript` na mesma camada.
5. **jbig2enc**: `git clone -b 0.32 --depth 1 https://github.com/agl/jbig2enc.git`; `./autogen.sh && ./configure && make && make install && ldconfig`; `rm -rf /tmp/jbig2enc`.
6. **Ajustes**: `fc-cache -fv`; `pip install --no-cache-dir --upgrade pip setuptools`; `rm -f /etc/nginx/conf.d/* /etc/nginx/sites-enabled/*`.
7. **Node 26**: `curl -fsSL https://deb.nodesource.com/setup_26.x | bash - && apt-get install -y nodejs`.
8. **Poetry**: `ENV POETRY_VIRTUALENVS_CREATE=false`; `RUN pip3 install poetry`.
9. `ENV DEBIAN_FRONTEND=teletype`; `CMD ["python3"]`.
10. Comentários finais com os comandos (tag local `building_foundation:0003`; para publicar: `docker login <repo> --username=<usuário>`, `docker tag building_foundation:0003 <repo>/building_foundation:0003`, `docker push <repo>/building_foundation:0003`).

Comandos de operação:

```bash
cd _docker/foundation
docker build -t building_foundation:0003 .
# uso local sem registro (os Dockerfile de dev/prod usam o prefixo leandrojatai/):
docker tag building_foundation:0003 leandrojatai/building_foundation:0003
```

### 2. Compose de desenvolvimento — `_docker/dev/docker-compose.yaml`

Invocação padrão: `docker compose -p <nome> --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml up --build -d`. Interpolação `${COMPOSE_PROJECT_NAME:-startdev1}` em todo `container_name`.

| Serviço | Imagem/Build | Contêiner | Portas | Volumes | Observações |
|---|---|---|---|---|---|
| `redis` | `redis:bookworm` | `<p>-redis` | `6379:6379` | `redis_data:/data` | `restart: on-failure` |
| `solr` | `solr:9.7` | `<p>-solr` | `8983:8983`, `9983:9983` | `solr9_data:/var/solr`, `solr9_configsets:/opt/solr/server/solr/configsets` | `command: bin/solr start -c -f`; comentário no YAML sobre validar mudança para 9.8 |
| `front` | build `context: ../../.`, `dockerfile: _docker/dev/Dockerfile.Dev.Front` | `<p>-front` | `5173:5173` | `../../.:/var/project/backend` | |
| `db` | `pgvector/pgvector:0.8.7-pg18-bookworm` | `<p>-db` | `5433:5432` | `dbdata:/var/lib/postgresql/data/` | env `POSTGRES_PASSWORD/USER/DB` (padrão `startdev1`), `PGDATA=/var/lib/postgresql/data/` |
| `appdev` | build `context: ../../.`, `dockerfile: _docker/dev/Dockerfile.Dev` | `<p>-appdev` | `${APP_PORT:-9099}:9000` | `/mnt/volumes/backend_media:/var/project/backend_media`, `../../.:/var/project/backend` | `depends_on: front, db, redis, solr` |

Variáveis de `appdev.environment`: `DEBUG: 'True'`, `USE_SOLR: 'True'`, `SOLR_COLLECTIONS: <p>_arq1,<p>_arq2`, `SOLR_URL: http://${SOLR_USER:-startdev1}:${SOLR_PASSWORD:-startdev1}@<p>-solr:8983`, `IS_ZK_EMBEDDED: 'True'`, `TZ: America/Sao_Paulo`, `COMPOSE_PROJECT_NAME`, `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB`. Rede: `appdev-net` com `driver: bridge`. Volumes nomeados: `solr9_data`, `solr9_configsets`, `redis_data`, `dbdata`. Todos os serviços: `restart: on-failure` e `networks: [appdev-net]`. Não há `healthcheck`.

`_docker/dev/.env_dev_compose` (formato `CHAVE=valor`, sem espaços): `APP_PORT=9099`, `POSTGRES_PASSWORD=…`, `POSTGRES_USER=startdev1`, `POSTGRES_DB=startdev1`, linha em branco, `SOLR_PASSWORD=…`, `SOLR_DB=startdev1`, linha em branco, `SITE_URL=http://startdev1:9099`. Valores de senha são padrões de desenvolvimento (não replicar em produção). `SOLR_DB` e `SITE_URL` não são referenciados no compose de dev; `SOLR_USER` não existe (padrão `startdev1`).

### 3. Imagem do `appdev` — `_docker/dev/Dockerfile.Dev`

```text
FROM leandrojatai/building_foundation:0003
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
ENV ROOT_HOME=/var/project ; ENV HOME=${ROOT_HOME}/backend
RUN mkdir -p ${HOME}/logs/celery ${ROOT_HOME}/backend_dev ${ROOT_HOME}/backend_media   # (três RUN separados)
WORKDIR ${HOME}
#COPY po* /var/backend/backend_dev/poetry.lock          # comentado
COPY py* ${ROOT_HOME}/backend_dev/pyproject.toml        # glob py* = só pyproject.toml
RUN poetry install --no-root -C ${ROOT_HOME}/backend_dev/
ENV DEBIAN_FRONTEND=teletype
EXPOSE 9000/tcp
VOLUME ["${ROOT_HOME}/backend_media", "${HOME}"]
CMD ["/var/project/backend/_docker/dev/start-dev.sh"]
```

Observações: `poetry.lock` **não** é copiado (a linha está comentada), então a resolução ocorre no build; as dependências ficam instaladas globalmente (Poetry sem virtualenv). O código só aparece em tempo de execução pelo *bind mount*; por isso `start-dev.sh` precisa ter bit de execução no host (`-rwxrwxr-x`).

### 4. Imagem do `front` — `_docker/dev/Dockerfile.Dev.Front`

`FROM node:26.13.0-bookworm`; `LANG`/`LC_ALL=C.UTF-8`; `ROOT_HOME=/var/project`, `HOME=${ROOT_HOME}/backend`; `mkdir -p ${HOME}`; `addgroup --gid 1001 backend`; `adduser --home=${HOME} --uid 1001 --gid 1001 --disabled-password --comment "" --shell=/bin/bash backend`; `chown -R backend:backend ${HOME}`; `USER backend`; `WORKDIR ${HOME}`; `EXPOSE 5173/tcp`; `VOLUME ["${HOME}"]`; `CMD ["/var/project/backend/startfront-dev.sh"]`. Há linhas comentadas (`#ENV RUN1_PACKAGES bash vim`). O Vite escuta em `0.0.0.0:5173` com `watch.usePolling` (`vite.config.js`, feature 007).

### 5. Bootstrap — `_docker/dev/start-dev.sh`

Ordem de execução (sem `set -e`):

1. Banner em amarelo: `====> StartDEV...`.
2. **`change_env_file`** (arquivo de referência: `_docker/dev/start-dev.sh`):
   - Declara `declare -A env_vars` mapeando **regex da linha** → **linha nova** `CHAVE = valor`:
     | Regex | Linha gravada (valor = variável do ambiente `:=` padrão) |
     |---|---|
     | `^DATABASE_URL_DEV.+$` | `DATABASE_URL_DEV = ${DATABASE_URL:=postgresql://${POSTGRES_USER:=startdev1}:${POSTGRES_PASSWORD:=startdev1}@${COMPOSE_PROJECT_NAME}-db:5432/${POSTGRES_DB:=startdev1}}` (barras escapadas `\/` no código) |
     | `^SOLR_COLLECTIONS.+$` | `SOLR_COLLECTIONS = ${SOLR_COLLECTIONS:=${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2}` |
     | `^SOLR_URL.+$` | `SOLR_URL = ${SOLR_URL:=http://startdev1:startdev1@${COMPOSE_PROJECT_NAME}-solr:8983}` |
     | `^DEBUG.+$` | `DEBUG = ${DEBUG:=True}` |
     | `^DJANGO_VITE_DEV_MODE.+$` | `DJANGO_VITE_DEV_MODE = ${DJANGO_VITE_DEV_MODE:=True}` |
     | `^REDIS_HOST.+$` | `REDIS_HOST = ${REDIS_HOST:=${COMPOSE_PROJECT_NAME}-redis}` |
     | `^FOLDER_DEBUG_CONTAINER.+$` | `FOLDER_DEBUG_CONTAINER = ${FOLDER_DEBUG_CONTAINER:=${HOME}}` (HOME=`/var/project/backend`) |
     | `^COMPOSE_PROJECT_NAME.+$` | `COMPOSE_PROJECT_NAME = ${COMPOSE_PROJECT_NAME:=${COMPOSE_PROJECT_NAME}}` |
     | `^TZ.+$` | `TZ = ${TZ:=America/Sao_Paulo}` |
   - `echo "" >> backend/.env` (garante o arquivo e uma quebra de linha).
   - Para cada regex (ordem arbitrária do array associativo): `sed -i -E "s|$regex|<linha>|g" backend/.env`; `key=$(echo "<linha>" | cut -d' ' -f1)`; se `! grep -q "^$key" backend/.env`, anexa a linha com `echo >>`.
   - Final: `echo "" >> backend/.env` e `sed -i -E ':a;N;$!ba;s/\n{3,}/\n\n/g' backend/.env` (colapsa 3+ quebras de linha em 2).
   - Observação: `DATABASE_URL` (sem sufixo) é a variável de ambiente consultada, não `DATABASE_URL_DEV`.
3. `yes yes | python3 manage.py migrate`.
4. **Bloco Solr** (detalhado na feature 008): defaults `USE_SOLR=False`, `SOLR_URL`, `SOLR_COLLECTIONS`, `NUM_SHARDS=1`, `RF=1`, `MAX_SHARDS_PER_NODE=1`, `IS_ZK_EMBEDDED=True`. Se `USE_SOLR` é `True`/`true`: imprime a configuração; `/bin/bash _docker/prod/wait-for-solr.sh $SOLR_URL` (retorna **1 quando o Solr está no ar**, 2 em falha — semântica invertida); se `== 1`: define `ZK_EMBEDDED="--embedded_zk"` quando `IS_ZK_EMBEDDED` for verdadeiro e executa `python3 _docker/prod/solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED`; senão imprime "Solr is offline, not possible to connect.". Se `USE_SOLR` não é verdadeiro: "Solr support is not initialized.".
5. `rm ${HOME}/logs/celery/*.pid`.
6. Celery: `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=${COMPOSE_PROJECT_NAME}-redis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log` (há uma linha comentada com 16 workers e filas `cq_arq`, `cq_core`, `cq_videos`, `cq_base`, `celery`).
7. `sleep 3`; `yes yes | python3 manage.py runserver 0.0.0.0:9000` (primeiro plano).

### 6. Scripts de raiz

- `rdev.sh`: `COMPOSE_PROJECT_NAME=${1:-startdev1}`; `sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml down`; `USER=\`whoami\`; GROUP=\`whoami\``; `sudo chown -R $USER:$GROUP .`; `sudo docker compose -p ... up --build -d`.
- `uupdev.sh`: `... --env-file ... --progress=plain -f ... up --build -d`.
- `ddev.sh`: `down` seguido do `chown`.
- `startfront-dev.sh`: `npm install` e `npm run dev` (script npm `dev` = `vite`).
- Todos com bit de execução (`chmod +x`), shebang `#!/usr/bin/env bash`.
- `libreoffice_entrypoint.sh` (`#!/bin/sh`, sem bit de execução): executa `/usr/bin/libreoffice --nologo --norestore --invisible --nolockcheck --nodefault --headless "$@"` e remove `/tmp/hsperfdata_root` se existir.
- `_docker/dev/recreate_db.sh` (`#!/bin/bash`, sem bit de execução): três `docker exec stormdb psql -U sddstart -d postgres -c "..."` — terminar conexões (`pg_terminate_backend`) do banco `sddstart`, `DROP DATABASE IF EXISTS sddstart;` e `CREATE DATABASE sddstart WITH OWNER = sddstart ENCODING = 'UTF8' CONNECTION LIMIT = -1;`.

### 7. Lógica contêiner × host nos settings

Arquivos de referência: `backend/settings/zenv.py`, `project.py`, `solr.py`, `zasyncs.py`, `medias.py`.

- `zenv.py`: `config = AutoConfig(search_path=...)` (procura `.env` em `backend_data/` ao lado do projeto quando existir `…/backend_data/.env`; caso contrário o padrão do decouple, que encontra `backend/.env`); `DEBUG = config("DEBUG", default=False, cast=bool)`; `BASE_DIR = Path(__file__).parents[1]` (pasta `backend`); `PROJECT_DIR = Path(__file__).parents[2]` (raiz do repositório); `FOLDER_DEBUG_CONTAINER = Path(config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str))`.
- `project.py`: `DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)` (definido, mas **não consumido** em outro ponto do código); `DATABASES["default"] = config("DATABASE_URL_DEV" if DEBUG else "DATABASE_URL_PRD", cast=dj_database_url.parse)`; `if DEBUG and FOLDER_DEBUG_CONTAINER != PROJECT_DIR:` → `HOST="localhost"`, `PORT=5433` e três `print` informativos (`"Running in debug mode with local database settings."`, `"Database host:"`, `"Database port:"`). Também: `ALLOWED_HOSTS=["*"]`, `SITE_URL` (padrão `http://192.168.15.9:9001`), `DEBUG_TOOLBAR_ACTIVE` (somente efetivo no `runserver` do host, conforme comentário).
- `solr.py`: se `DEBUG` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR`: `SOLR_URL = SOLR_URL.split("@")[0] + "@localhost:8983"`.
- `zasyncs.py`: `REDIS_HOST` (padrão `startdev1-redis`), `REDIS_PORT` (padrão 6379); se `DEBUG` e host: `REDIS_HOST = "localhost"`; `CELERY_BROKER_URL = redis://{REDIS_HOST}:{REDIS_PORT}`.
- `medias.py`: `MEDIA_ROOT = PROJECT_DIR.parent / "backend_media" / "media"` e `MEDIA_CACHE_ROOT = … / "media_cache"`; se `DEBUG and "/var/project" not in str(PROJECT_DIR)`, `Path("/mnt/volumes")/"backend_media"/…`.
- Dentro do contêiner `FOLDER_DEBUG_CONTAINER=/var/project/backend` (gravado por `start-dev.sh`) é igual a `PROJECT_DIR` → modo contêiner. No host, o mesmo `.env` (montado) dá valores diferentes → modo host.

### 8. Arquivos auxiliares

- `backend/.dockerignore`: ver FR-029 (sem efeito, o contexto é a raiz e não existe `.dockerignore` na raiz).
- `.github/dependabot.yml`: `version: 2` e seis blocos `updates:` (npm `/`; docker `/_docker/dev`; docker `/_docker/prod`; docker-compose `/_docker/dev`; docker-compose `/_docker/prod`; pip `/`), cada um com `schedule.interval: "weekly"`. Reconstruir **com uma única chave `updates:`** contendo seis itens `- package-ecosystem:` (a versão corrigida é a recomendada; o estado atual replica a repetição).
- `.gitignore`: contém `.env` e `.vscode/`.
- Permissões: `chmod +x rdev.sh uupdev.sh ddev.sh startfront-dev.sh _docker/dev/start-dev.sh`.

### 9. Sequência de boot resultante

`rdev.sh` → `down` → `chown` → `up --build -d` → Compose constrói `front` e `appdev` → sobe `redis`, `solr`, `db`, `front` → `appdev` executa `start-dev.sh` → `.env` ajustado → `migrate` → Solr → Celery → `runserver :9000` (publicado em `APP_PORT`).
