---

description: "Lista de tarefas para reconstruir o Docker de Produção"
---

# Tarefas: Docker para Produção

**Entrada**: Documentos de design em `/specs/011-docker-producao/`

**Pré-requisitos**: plan.md, spec.md, research.md, data-model.md, contracts/ (`ambiente-e-compose.md`, `scripts-e-processos.md`, `nginx.md`); features 001, 006–010 concluídas (imagem-base, Solr, frontend, mídia).

**Testes**: validações por comando (`bash -n`, `docker compose config`, `nginx -t`, `curl`) e, quando possível, um teste pytest de `backend.settings.fake`.

**Organização**: tarefas agrupadas por história de usuário. Todas as tarefas começam **desmarcadas** (roteiro de reconstrução).

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US6 (ver spec.md)

## Convenções de Caminhos

Raiz do repositório; infraestrutura em `_docker/prod/`; settings em `backend/settings/`.

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

- [ ] T001 Criar a pasta `_docker/prod/nginx/` e confirmar a existência da imagem-base `leandrojatai/building_foundation:0003` (feature 010, `_docker/foundation/Dockerfile`) e de `solr_cli.py`/`wait-for-solr.sh` (feature 008) em `_docker/prod/`
- [ ] T002 [P] Criar `_docker/prod/.env_prod_compose` conforme `contracts/ambiente-e-compose.md` (comentário "customizar para produção!", `APP_PORT=9001`, `POSTGRES_*`, `SOLR_PASSWORD`, `SOLR_DB` = `startprod1`, comentário e `SITE_URL=http://192.168.15.9:9001`)
- [ ] T003 [P] Criar `_docker/prod/genkey.py` com `generate_secret()` (50 caracteres, `random.SystemRandom`, alfabeto `abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)`) e `__main__` que imprime

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: configurações Django necessárias antes de construir a imagem.

- [ ] T004 Garantir em `backend/settings/zenv.py` a detecção de produção: `production = Path(__file__).parents[3] / "backend_data" / ".env"` → `.exists()`; `AutoConfig(search_path=<parents[3]/"backend_data"> if production else None)`; `DEBUG` com padrão `False`; `BASE_DIR`, `PROJECT_DIR`, `FOLDER_DEBUG_CONTAINER` (plan.md §8)
- [ ] T005 Garantir em `backend/settings/project.py`: `SECRET_KEY = config("SECRET_KEY")`, `ALLOWED_HOSTS = ["*"]`, `SITE_URL = config("SITE_URL", default="http://192.168.15.9:9001")`, `CSRF_TRUSTED_ORIGINS = [SITE_URL]`, `SESSIONS_COOKIE_SECURE = not DEBUG` (nome idêntico ao original) e `DATABASES["default"]` por `DATABASE_URL_DEV`/`DATABASE_URL_PRD` via `dj_database_url.parse`
- [ ] T006 [P] Garantir em `backend/settings/frontend.py`: `STATIC_ROOT = PROJECT_DIR / "collectedstatic"`, `DJANGO_VITE_ASSETS_PATH`, `STATICFILES_DIRS` e `DJANGO_VITE` com `manifest_path` em `STATIC_ROOT/frontend/.vite/manifest.json` fora do modo dev
- [ ] T007 Criar `backend/settings/fake.py` (`from .project import *  # noqa: F403`; `DEBUG = False`; `DJANGO_VITE_DEV_MODE = False`; SQLite em `PROJECT_DIR/db.sqlite3`; `DJANGO_VITE` com `manifest_path = DJANGO_VITE_ASSETS_PATH / "frontend" / ".vite" / "manifest.json"`)
- [ ] T008 [P] Teste pytest em `_tests/test_settings_fake.py`: com `SECRET_KEY` e `DATABASE_URL_PRD` no ambiente, importar `backend.settings.fake` e verificar `DEBUG is False`, engine SQLite e `DJANGO_VITE["default"]["dev_mode"] is False`; rodar `pytest _tests/test_settings_fake.py` e `ruff check backend/settings`

**Ponto de Controle**: settings prontas para o build e para o runtime de produção.

---

## Fase 3: História de Usuário 2 - Imagem imutável (Prioridade: P1) 🎯 MVP (parte 1)

**Meta**: imagem com dependências, frontend compilado e estáticos coletados.

**Teste Independente**: `docker compose -f _docker/prod/docker-compose.yaml build app` conclui; a imagem contém `collectedstatic/frontend/.vite/manifest.json`.

- [ ] T009 [US2] Criar `_docker/prod/Dockerfile` (plan.md §4): `FROM leandrojatai/building_foundation:0003`, `ENV` (`LANG`, `LC_ALL`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `DEBIAN_FRONTEND=noninteractive`, `ROOT_HOME=/var/project`, `HOME=${ROOT_HOME}/backend`), `mkdir -p` de `run`, `logs/celery`, `backend_data`, `backend_media`, `WORKDIR ${HOME}`
- [ ] T010 [US2] No `_docker/prod/Dockerfile`: `COPY manage.py`, `COPY py*`, `RUN poetry install --without dev,test,docs`, `COPY package.json`, `COPY vite.config.js` (manter `#COPY package-lock.json ${HOME}` comentado), `ADD _frontend`, `RUN npm install`, `RUN npm run build`
- [ ] T011 [US2] No `_docker/prod/Dockerfile`: `ADD` de `solr`, `drfautoapi`, `backend`, `_templates`, `_docker`; `RUN python3 manage.py collectstatic --noinput --clear --settings=backend.settings.fake --no-default-ignore`; `RUN rm -rf ${HOME}/db.sqlite3`
- [ ] T012 [US2] No `_docker/prod/Dockerfile`: `COPY` das confs Nginx (`backend_docker.conf` → `/etc/nginx/conf.d/.`; `nginx_docker.conf` → `/etc/nginx/nginx.conf`) e dos scripts (`start.sh`, `wait-for-pg.sh`, `wait-for-solr.sh`, `start_gunicorn.sh`, `start_daphne.sh`, `solr_cli.py`, `genkey.py`) para `${HOME}`, `RUN chmod +x` nos cinco `.sh`
- [ ] T013 [US2] No `_docker/prod/Dockerfile`: `RUN useradd -r --no-create-home -g root nginx` (com o comentário sobre Debian), `USER nginx`, `ENV DEBIAN_FRONTEND=teletype`, `EXPOSE 80/tcp`, `VOLUME ["${ROOT_HOME}/backend_data", "${ROOT_HOME}/backend_media", "${HOME}/logs"]`, `CMD ["/var/project/backend/start.sh"]`
- [ ] T014 [US2] Validar o build (`docker compose --env-file _docker/prod/.env_prod_compose -f _docker/prod/docker-compose.yaml build app`) e checar na imagem `collectedstatic/frontend/.vite/manifest.json`, `collectedstatic/frontend/service-worker.js` e ausência de `/var/project/backend/db.sqlite3`

---

## Fase 4: História de Usuário 4 - Roteamento do Nginx (Prioridade: P2, necessário ao MVP)

**Meta**: Nginx como ponto único de entrada.

**Teste Independente**: `nginx -t` na imagem e `curl` do quickstart §5.

- [ ] T015 [P] [US4] Criar `_docker/prod/nginx/nginx_docker.conf` conforme `contracts/nginx.md` (seção "Configuração global")
- [ ] T016 [P] [US4] Criar `_docker/prod/nginx/backend_docker.conf`: upstreams `backend_leg_app_server` e `backend_channels_server`, `server` na porta 80, `client_max_body_size 4G`, logs em `/var/project/backend/logs/nginx-*.log`
- [ ] T017 [US4] Em `backend_docker.conf` adicionar as locations `= /robots.txt`, `= /favicon.ico`, `= /service-worker.js`, `= /manifest.json`, `/static/` (gzip_static, expires 7d, Pragma/Cache-Control public) e `/mediaredirect/` (`internal`, alias em `/var/project/backend_media/media/`, cabeçalhos de não-cache)
- [ ] T018 [US4] Em `backend_docker.conf` adicionar `/ws/`, `/api`, `/` e as locations nomeadas `@proxy_to_ws`, `@proxy_to_app`, `@proxy_to_app_api` (CORS aberto, preflight 204, `X-Forwarded-Proto https`, timeouts 75s/600s)
- [ ] T019 [US4] Validar sintaxe: `docker run --rm --entrypoint nginx <imagem> -t`; testar as rotas do quickstart §5 após o T028

---

## Fase 5: História de Usuário 3 - Inicialização do contêiner (Prioridade: P1) 🎯 MVP (parte 2)

**Meta**: `start.sh` prepara configuração, migra, prepara Solr e sobe todos os processos na ordem correta.

**Teste Independente**: quickstart §3, §4 e §6.

- [ ] T020 [US3] Criar `_docker/prod/start.sh` (executável, `#!/usr/bin/env bash`): banner amarelo `====> StartPRD...`, linha comentada de `wait-for-pg.sh` e a função `change_env_file` completa (secret.key, `sed` do `SECRET_KEY`, `declare -A env_vars` com as dez chaves, laço `sed`/`grep -q`/append, colapso de linhas em branco) — plan.md §5
- [ ] T021 [US3] Em `start.sh`: `change_env_file`; `yes yes | python3 manage.py migrate`; bloco Solr condicionado a `USE_SOLR` (`wait-for-solr.sh`, retorno `== 1` ⇒ `solr_cli.py` com `--embedded_zk` quando `IS_ZK_EMBEDDED`), mensagens de log do contrato
- [ ] T022 [US3] Em `start.sh`: `sleep 3`; `rm ${HOME}/logs/celery/*.pid`; linha `celery multi` comentada (16 workers) e a ativa (`start 1 ... --hostname=backendredis`); `sleep 3`; `/bin/sh start_gunicorn.sh &`; `sleep 3`; `/bin/sh start_daphne.sh &`; `sleep 5`; `echo "Iniciando NGINX..."`; `/usr/sbin/nginx -g "daemon off;"`
- [ ] T023 [P] [US3] Criar `_docker/prod/start_gunicorn.sh` (variáveis, `mkdir` do diretório do socket e `exec gunicorn` com as opções do contrato)
- [ ] T024 [P] [US3] Criar `_docker/prod/start_daphne.sh` (laço de até 5 tentativas com `sleep 5`, mensagens em PT-BR, `exit 1` ao esgotar)
- [ ] T025 [P] [US3] Criar `_docker/prod/wait-for-pg.sh` (laço com `psql $1 -c '\l \q' | grep backend | wc -l`, `sleep 10`), mantendo-o desativado em `start.sh`
- [ ] T026 [US3] Executar `bash -n` nos cinco scripts e `chmod +x` (git: modo executável em `start.sh`, `wait-for-pg.sh`, `wait-for-solr.sh`)

---

## Fase 6: História de Usuário 1 - Subir a pilha com um comando (Prioridade: P1) 🎯 MVP (final)

**Meta**: `./upprod.sh` entrega a pilha completa.

**Teste Independente**: quickstart §2.

- [ ] T027 [US1] Criar `_docker/prod/docker-compose.yaml` com os serviços `redis`, `solr`, `db`, `app`, rede `app-net` (bridge) e volumes top-level (`dbdata`, `data`, `media`, `logs`, `solr9_data`, `solr9_configsets`, `redis_data`) conforme `contracts/ambiente-e-compose.md` (portas auxiliares comentadas, `user: "root:root"`, `depends_on` com condições)
- [ ] T028 [P] [US1] Criar `upprod.sh` na raiz (executável): `COMPOSE_PROJECT_NAME=${1:-startprod1}` + `sudo docker compose -p ... --env-file _docker/prod/.env_prod_compose --progress=plain -f _docker/prod/docker-compose.yaml up --build -d`
- [ ] T029 [US1] Validar `docker compose ... config -q`, subir com `./upprod.sh` e executar quickstart §2–§5 (HTTP 200/302 em `APP_PORT`, contêineres com prefixo do projeto)

---

## Fase 7: História de Usuário 5 - Persistência, múltiplas instâncias e desligamento (Prioridade: P2)

**Teste Independente**: quickstart §6 e §7.

- [ ] T030 [P] [US5] Criar `dprod.sh` na raiz (executável): `down` com o mesmo `-p`/`--env-file`/`-f`, depois `USER=\`whoami\``, `GROUP=\`whoami\``, `sudo chown -R $USER:$GROUP .`
- [ ] T031 [US5] Validar persistência: `./dprod.sh` seguido de `./upprod.sh` mantém `secret.key` (mesmo `sha256sum`), banco e mídia; validar duas instâncias (`./upprod.sh outra` com `APP_PORT` diferente) sem conflitos

---

## Fase 8: História de Usuário 6 - Configuração Django de produção (Prioridade: P3)

**Teste Independente**: quickstart §8 e teste pytest do T008.

- [ ] T032 [US6] Verificar dentro do contêiner `DEBUG False`, `dev_mode False`, `CSRF_TRUSTED_ORIGINS == [SITE_URL]`, host do banco `<projeto>-db` (quickstart §8)
- [ ] T033 [US6] Verificar que, com `SITE_URL` alterada em `.env_prod_compose` e `./upprod.sh` reexecutado, o `backend_data/.env` reflete o novo valor e o login por formulário na nova origem passa no CSRF

---

## Fase 9: Acabamento e Preocupações Transversais

- [ ] T034 [P] Documentar em `README.md` (seção "Executando em produção") o fluxo `./upprod.sh`/`./dprod.sh`, a necessidade de trocar `startprod1` e `SITE_URL`, e o aviso de `ALLOWED_HOSTS`/CORS abertos
- [ ] T035 [P] Registrar nas notas do projeto as dívidas de `research.md` (R1–R26) sem alterá-las, para fidelidade
- [ ] T036 Rodar `ruff check .` e `pytest` (suite completa) para garantir que nenhuma regressão foi introduzida pelas settings

---

## Dependências e Ordem de Execução

- Preparação (T001–T003) → Fundacional (T004–T008) → US2 (T009–T014, requer Nginx e scripts presentes para o `COPY`: T015–T016 e T020–T025 devem existir antes do T014) → US4 → US3 → US1.
- Na prática: criar arquivos na ordem T001–T008, T015–T018, T020–T025, T027–T028, T030, depois **construir** (T009–T014) e validar (T019, T026, T029, T031–T033).
- T028 e T030 são independentes entre si; T023–T025 são paralelos; T015 e T016 são paralelos.
- US5 e US6 só podem ser validadas após a pilha de US1 no ar.

## Estratégia de Implementação

1. **MVP**: Fases 1–6 (settings + imagem + Nginx + start.sh + Compose + `upprod.sh`) entregam a pilha funcional.
2. Em seguida `dprod.sh` e a validação de persistência (US5) e a verificação das settings (US6).
3. Acabamento (documentação e regressão).
4. Replicar as particularidades de `research.md` para fidelidade; correções são evoluções separadas com atualização desta especificação.
