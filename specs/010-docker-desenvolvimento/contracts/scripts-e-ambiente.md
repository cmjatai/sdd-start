# Contrato: Scripts, variáveis de ambiente e execução contêiner × host

## 1. CLI dos scripts de raiz

Todos executados da raiz do repositório, com argumento opcional `[nome]` (padrão `startdev1`) que vira `COMPOSE_PROJECT_NAME`/`-p`. Requerem `sudo` e Docker Compose v2.

| Script | Sequência | Efeitos colaterais |
|---|---|---|
| `./rdev.sh [nome]` | `down` → `chown -R $USER:$GROUP .` → `up --build -d` | Recria contêineres; corrige o dono dos arquivos |
| `./uupdev.sh [nome]` | `up --build -d --progress=plain` | Reconstrói e sobe sem derrubar; não faz `chown` |
| `./ddev.sh [nome]` | `down` → `chown -R $USER:$GROUP .` | Remove contêineres; volumes nomeados preservados |
| `./startfront-dev.sh` | `npm install` → `npm run dev` | Vite em `0.0.0.0:5173` (host ou contêiner `front`) |
| `_docker/dev/start-dev.sh` | ver seção 2 | CMD do `appdev`; não executar manualmente fora do contêiner |
| `_docker/dev/recreate_db.sh` | 3× `docker exec stormdb psql -U sddstart …` | **Legado**: contêiner/banco/usuário não existem no Compose atual |
| `libreoffice_entrypoint.sh` | `libreoffice --headless …` e limpeza de `/tmp/hsperfdata_root` | Sem uso nas imagens |

Códigos de saída: não tratados explicitamente (sem `set -e`); o código do contêiner `appdev` é o do `runserver`.

## 2. Fluxo do `start-dev.sh`

1. `change_env_file` (ver tabela abaixo).
2. `yes yes | python3 manage.py migrate`.
3. Solr (se `USE_SOLR` ∈ {`True`, `true`}): `bash _docker/prod/wait-for-solr.sh $SOLR_URL` (sucesso = código 1) → `python3 _docker/prod/solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE [--embedded_zk]`.
4. `rm ${HOME}/logs/celery/*.pid`.
5. `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=${COMPOSE_PROJECT_NAME}-redis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log`.
6. `sleep 3`; `yes yes | python3 manage.py runserver 0.0.0.0:9000`.

### Tabela de `change_env_file`

| Chave em `backend/.env` | Variável de ambiente consultada (`:=` padrão) | Padrão |
|---|---|---|
| `DATABASE_URL_DEV` | `DATABASE_URL` (com `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) | `postgresql://startdev1:startdev1@<nome>-db:5432/startdev1` |
| `SOLR_COLLECTIONS` | `SOLR_COLLECTIONS` | `<nome>_arq1,<nome>_arq2` |
| `SOLR_URL` | `SOLR_URL` | `http://startdev1:startdev1@<nome>-solr:8983` |
| `DEBUG` | `DEBUG` | `True` |
| `DJANGO_VITE_DEV_MODE` | `DJANGO_VITE_DEV_MODE` | `True` |
| `REDIS_HOST` | `REDIS_HOST` | `<nome>-redis` |
| `FOLDER_DEBUG_CONTAINER` | `FOLDER_DEBUG_CONTAINER` | `${HOME}` = `/var/project/backend` |
| `COMPOSE_PROJECT_NAME` | `COMPOSE_PROJECT_NAME` | (o próprio valor injetado) |
| `TZ` | `TZ` | `America/Sao_Paulo` |

Algoritmo por chave: `sed -i -E "s|^CHAVE.+$|CHAVE = valor|g"`; se nenhuma linha começar por `CHAVE`, anexa `CHAVE = valor`.

## 3. Variáveis lidas pelos settings (`python-decouple`)

| Variável | Arquivo | Padrão no código | Observação |
|---|---|---|---|
| `SECRET_KEY` | `backend/settings/project.py` | — (obrigatória) | Não gerada em dev |
| `DEBUG` | `zenv.py` | `False` | `True` em dev |
| `FOLDER_DEBUG_CONTAINER` | `zenv.py` | `__file__` | Caminho do projeto no contêiner |
| `DATABASE_URL_DEV` / `DATABASE_URL_PRD` | `project.py` | — | `DEV` se `DEBUG` |
| `REDIS_HOST`, `REDIS_PORT` | `zasyncs.py` | `startdev1-redis`, `6379` | |
| `USE_SOLR`, `SOLR_URL`, `SOLR_COLLECTIONS` | `solr.py` | `False`, `http://startdev1:startdev1@startdev1-solr:8983`, `backend_arq1,backend_arq2` | |
| `SITE_URL` | `project.py` | `http://192.168.15.9:9001` | também em `CSRF_TRUSTED_ORIGINS` |
| `DEBUG_TOOLBAR_ACTIVE` | `project.py` | `False` | só efetivo no host |

## 4. Matriz contêiner × host (com `DEBUG=True`)

| Aspecto | Contêiner `appdev` (`FOLDER_DEBUG_CONTAINER == PROJECT_DIR`) | Host (`FOLDER_DEBUG_CONTAINER != PROJECT_DIR`) |
|---|---|---|
| `PROJECT_DIR` | `/var/project/backend` | caminho local do clone |
| Banco | `DATABASE_URL_DEV` (`<nome>-db:5432`) | `HOST=localhost`, `PORT=5433` |
| Redis/Celery broker | `REDIS_HOST` (`<nome>-redis`):6379 | `localhost:REDIS_PORT` |
| Solr | `SOLR_URL` original | mesma URL com host trocado por `@localhost:8983` |
| `DEBUG_RUNNING_CONTAINER` | `True` | `False` (não consumido) |
| `MEDIA_ROOT` | `/var/project/backend_media/media` | `/mnt/volumes/backend_media/media` |
| `MEDIA_CACHE_ROOT` | `/var/project/backend_media/media_cache` | `/mnt/volumes/backend_media/media_cache` |
| Mensagens no console | — | `Running in debug mode with local database settings.` + host/porta |

## 5. Imagem-base: comandos de operação

```bash
# construir (a partir de _docker/foundation)
docker build -t building_foundation:0003 .
# publicar
docker login <repo> --username=<usuario>
docker tag building_foundation:0003 <repo>/building_foundation:0003
docker push <repo>/building_foundation:0003
```

Nome esperado pelos `Dockerfile` de dev/prod: `leandrojatai/building_foundation:0003` (para uso local sem registro, crie essa tag com `docker tag`).

## 6. Dependabot (`.github/dependabot.yml`)

| Ecossistema | Diretório | Intervalo |
|---|---|---|
| `npm` | `/` | `weekly` |
| `docker` | `/_docker/dev` | `weekly` |
| `docker` | `/_docker/prod` | `weekly` |
| `docker-compose` | `/_docker/dev` | `weekly` |
| `docker-compose` | `/_docker/prod` | `weekly` |
| `pip` | `/` | `weekly` |

Arquivo atual: `version: 2` + seis chaves `updates:` repetidas (defeito; forma correta = uma lista).

## 7. `backend/.dockerignore` (conteúdo, sem efeito prático)

`media`, `collected_static`, `.git`, `.gitignore`, `whoosh`, `bower`, `*.log`, `~*`, `*.pyc`, `.cache`, `.project`, `.env`, `.idea`.
