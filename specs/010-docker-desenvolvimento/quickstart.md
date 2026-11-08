# Início Rápido: validar o ambiente Docker de desenvolvimento

**Funcionalidade**: `010-docker-desenvolvimento`

## 0. Pré-requisitos

```bash
docker --version && docker compose version        # Compose v2
sudo -v                                            # os scripts usam sudo
ls -ld /mnt/volumes/backend_media || sudo mkdir -p /mnt/volumes/backend_media
docker image inspect leandrojatai/building_foundation:0003 >/dev/null 2>&1 || echo "imagem-base ausente (ver passo 1)"
printf 'SECRET_KEY = %s\n' "$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')" > backend/.env   # só se ainda não existir
```

> `backend/.env` é ignorado pelo Git; `start-dev.sh` NÃO gera `SECRET_KEY`. Não sobrescreva um `.env` existente.

## 1. (Opcional) Construir a imagem-base localmente

```bash
docker build -t building_foundation:0003 _docker/foundation
docker tag building_foundation:0003 leandrojatai/building_foundation:0003
docker run --rm building_foundation:0003 bash -c 'python3 --version; node --version; psql --version; gs --version; jbig2 --version 2>&1 | head -1; tesseract --version | head -1; tesseract --list-langs | grep por; poetry --version; java -version 2>&1 | head -1'
```

Esperado: Python 3.14.x, Node v26.x, `psql` 18, `gs` 10.08.0, jbig2enc 0.32, Tesseract com `por`, Poetry, OpenJDK 17.

## 2. Subir o ambiente

```bash
./rdev.sh                # ou ./rdev.sh startdev2
docker compose -p startdev1 --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml ps
docker ps --format '{{.Names}}\t{{.Ports}}'
```

Esperado: `startdev1-redis`, `startdev1-solr`, `startdev1-front`, `startdev1-db`, `startdev1-appdev` em execução; portas `6379`, `8983`/`9983`, `5173`, `5433→5432`, `9099→9000`.

## 3. Verificar o bootstrap

```bash
docker logs -f startdev1-appdev           # "[ENV FILE] change .env file...", migrações, "Solr configurations", celery multi, runserver
grep -E '^(DATABASE_URL_DEV|SOLR_URL|SOLR_COLLECTIONS|DEBUG|DJANGO_VITE_DEV_MODE|REDIS_HOST|FOLDER_DEBUG_CONTAINER|COMPOSE_PROJECT_NAME|TZ)\b' backend/.env | sed -E 's#(://[^:]+:)[^@]+@#\1***@#'
grep -c '^DEBUG ' backend/.env            # deve ser 1 (sem duplicatas)
docker exec startdev1-appdev python3 manage.py showmigrations | grep -c '\[ \]'    # esperado: 0 pendentes
ls logs/celery                              # celery1.pid, celery1.log...
docker exec startdev1-appdev celery -A backend inspect ping    # um worker responde
```

Esperado no log: bloco "Solr configurations" com `COLLECTION: startdev1_arq1,startdev1_arq2` e ou a criação das coleções ou "Solr is offline, not possible to connect." (se o Solr demorar mais de 60 s).

## 4. Acessar serviços

```bash
curl -sI http://localhost:9099/ | head -1         # aplicação Django
curl -sI http://localhost:5173/ | head -1         # Vite
curl -s 'http://localhost:8983/solr/admin/info/system?wt=json' -o /dev/null -w '%{http_code}\n'   # 200 ou 401 (autenticação; ver feature 008)
docker exec startdev1-db psql -U startdev1 -d startdev1 -c "select extname from pg_available_extensions where extname='vector';"
docker exec startdev1-redis redis-cli ping        # PONG
```

## 5. Execução híbrida (`runserver` no host)

```bash
poetry install && python manage.py runserver 0.0.0.0:9000     # com o ambiente Docker no ar e DEBUG=True no .env
```

Esperado no console: `Running in debug mode with local database settings.`, `Database host: localhost`, `Database port: 5433`. Verifique também `python manage.py shell -c "from django.conf import settings as s; print(s.CELERY_BROKER_URL, s.MEDIA_ROOT)"` → `redis://localhost:6379` e `/mnt/volumes/backend_media/media`.

## 6. Várias instâncias

```bash
# ajuste antes as portas fixas (5433, 6379, 8983, 9983, 5173) e APP_PORT para a 2ª instância
./rdev.sh startdev2
docker ps --format '{{.Names}}' | sort            # startdev1-* e startdev2-*
```

## 7. Derrubar

```bash
./ddev.sh [nome]
docker ps --filter name=startdev1 -q | wc -l      # 0
stat -c '%U' backend/.env                          # usuário atual (não root)
```

## 8. Checagens estáticas (sem subir o ambiente)

```bash
bash -n rdev.sh uupdev.sh ddev.sh startfront-dev.sh _docker/dev/start-dev.sh _docker/dev/recreate_db.sh libreoffice_entrypoint.sh
docker compose --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml config -q
python3 -c "import yaml;d=yaml.safe_load(open('.github/dependabot.yml'));print(len(d['updates']))"   # estado atual: 1 (só a última chave sobrevive); corrigido: 6
```

## 9. Testes automatizados relacionados

- Não há testes `pytest` específicos desta infraestrutura. Testes sugeridos (a criar em `_tests/` ou `backend/tests.py`):
  - `settings` com `DEBUG=True` e `FOLDER_DEBUG_CONTAINER` diferente de `PROJECT_DIR` → `DATABASES["default"]["HOST"] == "localhost"` e `PORT == 5433` (usar `importlib.reload` com `monkeypatch.setenv`);
  - `SOLR_URL` termina em `@localhost:8983` no modo host e mantém o host original no modo contêiner;
  - `REDIS_HOST == "localhost"` no modo host;
  - teste de *shell* do `change_env_file` em um diretório temporário do projeto (sem `/tmp`), verificando idempotência e ausência de chaves duplicadas.
- Suíte existente: `pytest` e `ruff check .` (princípio VIII) devem continuar passando no contêiner: `docker exec startdev1-appdev pytest -q`.
