# Contrato: Scripts e Processos

## Scripts de raiz

| Script | Uso | Efeito |
|---|---|---|
| `./upprod.sh [nome]` | `nome` padrão `startprod1` | `sudo docker compose -p <nome> --env-file _docker/prod/.env_prod_compose --progress=plain -f _docker/prod/docker-compose.yaml up --build -d` |
| `./dprod.sh [nome]` | idem | `sudo docker compose -p <nome> --env-file _docker/prod/.env_prod_compose -f _docker/prod/docker-compose.yaml down` e, depois, `sudo chown -R $(whoami):$(whoami) .` |

Executar sempre na raiz do repositório. Códigos de saída: os do `docker compose` (`upprod.sh`) e do `chown` (`dprod.sh`).

## Scripts dentro da imagem (`/var/project/backend/`)

| Script | Entradas | Saída/efeito |
|---|---|---|
| `start.sh` | env do contêiner (ver `ambiente-e-compose.md`) | CMD da imagem; sequência: `change_env_file` → `migrate` → Solr → `sleep 3` → Celery → `sleep 3` → Gunicorn (bg) → `sleep 3` → Daphne (bg) → `sleep 5` → Nginx (fg, `daemon off`) |
| `start_gunicorn.sh` | — | `exec gunicorn backend.wsgi:application`, bind `unix:/var/project/backend/run/gunicorn.sock`, 9 workers, timeout 300 s, `max-requests` 1000, log `info`, `--user $(whoami)`, logs `gunicorn_access.log`/`gunicorn_error.log` |
| `start_daphne.sh` | — | `daphne -u /var/project/backend/run/daphne.sock backend.asgi:application --access-log .../daphne_access.log -v1`; até 5 tentativas, `sleep 5` entre elas; `exit 1` ao esgotar |
| `genkey.py` | — | imprime 50 caracteres aleatórios (`SystemRandom`) de `abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)` |
| `wait-for-pg.sh <url>` | URL `psql` | laço infinito (10 s) até `psql <url> -c '\l \q' \| grep backend \| wc -l` ≠ 0; **não é chamado** por `start.sh` |
| `wait-for-solr.sh <url>` | URL base do Solr (feature 008) | até 7 tentativas (1 s) em `<url>/solr/admin/collections?action=LIST`; **sai com 1 se HTTP 200, 2 se falhar** |
| `solr_cli.py` | `-u -c -s -rf -ms [--embedded_zk]` (feature 008) | cria segurança e coleções |

### Mensagens de log marcantes

`====> StartPRD...`, `[ENV FILE] change .env file...`, `Solr configurations`, `running Solr script`, `Connecting to Solr...`, `Assuming embedded ZooKeeper instalation...`, `Solr is offline, not possible to connect.`, `Solr support is not initialized.`, `Iniciando: BACKEND.wsgi. base: /var/project/backend`, `Iniciando: BACKEND.asgi. base: /var/project/backend`, `Falha ao iniciar Daphne, tentativa N de 5`, `Iniciando NGINX...`.

## Comando do Celery

```text
celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=backendredis \
  --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log
```

## Build da imagem

Contexto: raiz do repositório. Argumentos relevantes: nenhum `ARG`. Comando de coleta: `python3 manage.py collectstatic --noinput --clear --settings=backend.settings.fake --no-default-ignore`.

## Arquivos de log gerados (volume `logs`)

`backend_logger.log` (Django), `gunicorn_access.log`, `gunicorn_error.log`, `daphne_access.log`, `nginx-access.log`, `nginx-error.log`, `celery/*.log` e `celery/*.pid`.
