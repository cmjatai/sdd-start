# Quickstart: validar o Docker de Produção

Pré-requisitos: Docker + Compose v2, `sudo`, imagem-base `leandrojatai/building_foundation:0003` disponível (feature 010) e `backend/.env` com ao menos `SECRET_KEY` (necessário para o `collectstatic` do build — ver `research.md` R18/R19). Execute tudo na raiz do repositório.

## 1. Verificações estáticas (sem subir nada)

```bash
bash -n upprod.sh dprod.sh _docker/prod/start.sh _docker/prod/start_gunicorn.sh _docker/prod/start_daphne.sh _docker/prod/wait-for-pg.sh
python3 _docker/prod/genkey.py | wc -c        # 51 (50 caracteres + quebra de linha)
docker compose --env-file _docker/prod/.env_prod_compose -f _docker/prod/docker-compose.yaml config -q
```

## 2. Subir

```bash
./upprod.sh                 # projeto startprod1
# outra instância: ./upprod.sh outra (troque antes APP_PORT em .env_prod_compose, pois o script usa sempre esse arquivo)
docker ps --format '{{.Names}} {{.Ports}}'
```

Esperado: `startprod1-redis`, `startprod1-solr`, `startprod1-db`, `startprod1-app`; somente o `app` mostra `0.0.0.0:9001->80/tcp`.

## 3. Acompanhar a inicialização

```bash
docker logs -f startprod1-app
```

Sequência esperada: `====> StartPRD...` → `[ENV FILE] change .env file...` → saída do `migrate` → `Solr configurations` … → Celery iniciado → `Iniciando: BACKEND.wsgi` → `Iniciando: BACKEND.asgi` → `Iniciando NGINX...`.

## 4. Conferir configuração gerada e processos

```bash
docker exec startprod1-app bash -c 'ls -l /var/project/backend_data; grep -E "^(DEBUG|SITE_URL|REDIS_HOST|DJANGO_VITE_DEV_MODE|FOLDER_DEBUG_CONTAINER) " /var/project/backend_data/.env'
docker exec startprod1-app bash -c 'ps aux | grep -E "celery|gunicorn|daphne|nginx" | grep -v grep | wc -l'
docker exec startprod1-app ls /var/project/backend/run /var/project/backend/collectedstatic/frontend/.vite
```

Esperado: `secret.key` e `.env` presentes (não imprima a `SECRET_KEY`); `DEBUG = False`; `DJANGO_VITE_DEV_MODE = False`; `gunicorn.sock` e `daphne.sock` em `run/`; `manifest.json` em `collectedstatic/frontend/.vite`.

## 5. Testar o Nginx

```bash
curl -I http://localhost:9001/                          # 200 ou 302 (aplicação)
curl -I http://localhost:9001/robots.txt                # 200
curl -I http://localhost:9001/favicon.ico               # 200
curl -I http://localhost:9001/service-worker.js         # 200
curl -I http://localhost:9001/manifest.json             # 200
curl -I http://localhost:9001/static/frontend/favicon.ico   # 200, Cache-Control: public, Expires ~7d
curl -I http://localhost:9001/mediaredirect/x           # 404 (internal)
curl -i -X OPTIONS http://localhost:9001/api/           # 204 + Access-Control-Allow-Origin: *
curl -I http://localhost:9001/api/                      # resposta do Django + CORS
```

WebSocket (feature 006): abrir a aplicação autenticada no navegador e verificar em "Rede" a conexão `ws://localhost:9001/ws/sync/` (101 Switching Protocols).

## 6. Persistência da `SECRET_KEY`

```bash
docker exec startprod1-app sha256sum /var/project/backend_data/secret.key
docker restart startprod1-app
docker exec startprod1-app sha256sum /var/project/backend_data/secret.key   # igual
```

## 7. Derrubar e subir novamente

```bash
./dprod.sh        # down (+ chown -R do diretório atual); volumes permanecem
docker volume ls | grep startprod1
./upprod.sh       # dados e SECRET_KEY preservados
```

Para remover tudo, inclusive dados: `sudo docker compose -p startprod1 --env-file _docker/prod/.env_prod_compose -f _docker/prod/docker-compose.yaml down -v`.

## 8. Teste das settings (Django)

Com `backend_data/.env` existente (dentro do contêiner):

```bash
docker exec startprod1-app python3 -c "import django,os;os.environ['DJANGO_SETTINGS_MODULE']='backend.settings';django.setup();from django.conf import settings as s;print(s.DEBUG,s.DJANGO_VITE['default']['dev_mode'],s.CSRF_TRUSTED_ORIGINS,s.DATABASES['default']['HOST'])"
```

Esperado: `False False ['<SITE_URL>'] startprod1-db`.

Testes pytest: não existem para os artefatos Docker. Sugestão de teste automatizado (a criar): em `_tests/`, um teste que importe `backend.settings.fake` com `SECRET_KEY` e `DATABASE_URL_PRD` definidos no ambiente e verifique `DEBUG is False`, `ENGINE == "django.db.backends.sqlite3"` e `DJANGO_VITE["default"]["dev_mode"] is False`. Rode também `ruff check .` (não deve haver alterações em Python além de `fake.py`).
