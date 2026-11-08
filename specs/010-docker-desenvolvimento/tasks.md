# Tarefas: Ambiente Docker de Desenvolvimento e Imagem-Base

**Entrada**: Documentos de design em `/specs/010-docker-desenvolvimento/`

**Pré-requisitos**: plan.md (obrigatório), spec.md, research.md, data-model.md, contracts/ (`docker-compose-dev.md`, `scripts-e-ambiente.md`). Features anteriores `001`–`009` já implementadas (o backend, o frontend Vite, `_docker/prod/wait-for-solr.sh` e `_docker/prod/solr_cli.py` existem).

**Testes**: validação operacional conforme `quickstart.md`; testes `pytest` para a lógica contêiner × host (US4) e checagens estáticas (`bash -n`, `docker compose config`).

**Organização**: tarefas agrupadas por história de usuário. **Todas as tarefas começam desmarcadas** (roteiro de reconstrução).

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[US#]**: história de usuário a que pertence
- Caminhos relativos à raiz do repositório

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: estrutura de pastas e arquivos de ignore.

- [ ] T001 Criar as pastas `_docker/foundation/` e `_docker/dev/` (a pasta `_docker/prod/` pertence à feature 011)
- [ ] T002 [P] Garantir em `.gitignore` as entradas `.env` e `.vscode/` (e `*.log`); não ignorar `_docker/dev/.env_dev_compose`
- [ ] T003 [P] Criar `backend/.dockerignore` com `media`, `collected_static`, `.git`, `.gitignore`, `whoosh`, `bower`, `*.log`, `~*`, `*.pyc`, `.cache`, `.project`, `.env`, `.idea` (plan.md §8; ciente de que não tem efeito com o contexto na raiz — research.md item 11)
- [ ] T004 [P] Criar `.github/dependabot.yml` (`version: 2`) com atualizações `weekly` para `npm` (`/`), `docker` (`/_docker/dev`, `/_docker/prod`), `docker-compose` (`/_docker/dev`, `/_docker/prod`) e `pip` (`/`); recomendado usar **uma única** lista `updates:` (o código original repete a chave por bloco — research.md item 9)
- [ ] T005 [P] Criar `libreoffice_entrypoint.sh` na raiz (`#!/bin/sh`; `/usr/bin/libreoffice --nologo --norestore --invisible --nolockcheck --nodefault --headless "$@"`; remover `/tmp/hsperfdata_root` se existir) — sem bit de execução, sem uso nas imagens

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: imagem-base e configuração de ambiente exigidas por todas as histórias.

**⚠️ CRÍTICO**: nenhuma história pode ser validada sem a imagem-base e os settings preparados.

- [ ] T006 Criar `_docker/foundation/Dockerfile` conforme plan.md §1: `FROM python:3.14.10-bookworm`, `ENV` agrupadas, apt (RUN0_PACKAGES, LIBRE_PACKAGES, java/tesseract `por`), PostgreSQL 18 client via PGDG, Ghostscript 10.08.0, jbig2enc 0.32, `fc-cache`/pip/limpeza do nginx, Node 26 (NodeSource `setup_26.x`), `POETRY_VIRTUALENVS_CREATE=false` + `pip3 install poetry`, `DEBIAN_FRONTEND=teletype`, `CMD ["python3"]` e comentários finais de build/login/tag/push
- [ ] T007 [P] Criar `_docker/dev/.env_dev_compose` com `APP_PORT=9099`, `POSTGRES_PASSWORD`, `POSTGRES_USER=startdev1`, `POSTGRES_DB=startdev1`, `SOLR_PASSWORD`, `SOLR_DB=startdev1`, `SITE_URL=http://startdev1:9099` (senhas de exemplo de desenvolvimento; data-model.md §2)
- [ ] T008 [P] Em `backend/settings/zenv.py`, garantir `DEBUG`, `BASE_DIR`, `PROJECT_DIR` (`parents[2]`) e `FOLDER_DEBUG_CONTAINER = Path(config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str))` (plan.md §7)
- [ ] T009 Criar o `backend/.env` local de desenvolvimento apenas com `SECRET_KEY` (arquivo ignorado pelo Git; nunca versionar)
- [ ] T010 Construir e validar a base: `docker build -t building_foundation:0003 _docker/foundation` seguido de `docker tag building_foundation:0003 leandrojatai/building_foundation:0003`; conferir versões (quickstart §1)

**Ponto de Controle**: imagem-base disponível sob o nome `leandrojatai/building_foundation:0003`.

---

## Fase 3: História de Usuário 1 - Subir o ambiente com um comando (Prioridade: P1) 🎯 MVP

**Objetivo**: `./rdev.sh` sobe os cinco serviços e a aplicação responde em `APP_PORT`.

**Teste Independente**: `docker ps` mostra `startdev1-{redis,solr,front,db,appdev}` e `curl -I http://localhost:9099/` responde.

### Implementação

- [ ] T011 [US1] Criar `_docker/dev/docker-compose.yaml` com os serviços `redis`, `solr`, `front`, `db`, `appdev`, rede `appdev-net` (bridge) e volumes `solr9_data`, `solr9_configsets`, `redis_data`, `dbdata`, exatamente como em contracts/docker-compose-dev.md (`container_name: ${COMPOSE_PROJECT_NAME:-startdev1}-<serviço>`, `restart: on-failure`, portas, `depends_on`, variáveis de ambiente do `appdev`, `solr` com `command: bin/solr start -c -f`)
- [ ] T012 [P] [US1] Criar `_docker/dev/Dockerfile.Dev` conforme plan.md §3 (`FROM leandrojatai/building_foundation:0003`, `ROOT_HOME`/`HOME`, `mkdir` de `logs/celery`, `backend_dev`, `backend_media`, `COPY py* …/backend_dev/pyproject.toml`, `poetry install --no-root -C`, `EXPOSE 9000/tcp`, `VOLUME`, `CMD start-dev.sh`)
- [ ] T013 [P] [US1] Criar `_docker/dev/Dockerfile.Dev.Front` conforme plan.md §4 (`node:26.13.0-bookworm`, usuário `backend` uid/gid 1001, `EXPOSE 5173/tcp`, `CMD /var/project/backend/startfront-dev.sh`)
- [ ] T014 [P] [US1] Criar `rdev.sh` (down → `chown -R` → `up --build -d`), `uupdev.sh` (`up --build -d` com `--progress=plain`) e `ddev.sh` (down → `chown -R`) na raiz, com nome padrão `startdev1`, comando `sudo docker compose -p $COMPOSE_PROJECT_NAME --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml`; `chmod +x` (plan.md §6)
- [ ] T015 [US1] Criar `/mnt/volumes/backend_media` no host, se ausente, e validar `docker compose … config -q`
- [ ] T016 [US1] Executar `./rdev.sh` e validar os critérios SC-001 e SC-007 (quickstart §2 e §4); validar `./ddev.sh` (SC-008)

**Ponto de Controle**: o ambiente sobe e derruba com um comando.

---

## Fase 4: História de Usuário 2 - Bootstrap automático do `appdev` (Prioridade: P1)

**Objetivo**: `start-dev.sh` ajusta `.env`, migra, prepara o Solr, inicia Celery e `runserver`.

**Teste Independente**: com apenas `SECRET_KEY` no `.env`, o contêiner termina o bootstrap, `showmigrations` sem pendências e worker Celery responde.

### Implementação

- [ ] T017 [US2] Criar `_docker/dev/start-dev.sh` (shebang `#!/usr/bin/env bash`, `chmod +x`) com o banner e a função `change_env_file` (plan.md §5, passo 2): `declare -A env_vars` das nove chaves, `sed -i -E "s|regex|linha|g"`, anexação de chaves ausentes por `grep -q "^$key"`, `echo ""` inicial/final e colapso de quebras de linha com `sed -E ':a;N;$!ba;s/\n{3,}/\n\n/g'`
- [ ] T018 [US2] Em `_docker/dev/start-dev.sh`, acrescentar `yes yes | python3 manage.py migrate`
- [ ] T019 [US2] Em `_docker/dev/start-dev.sh`, acrescentar o bloco Solr (defaults `USE_SOLR=False`, `NUM_SHARDS=1`, `RF=1`, `MAX_SHARDS_PER_NODE=1`, `IS_ZK_EMBEDDED=True`; `wait-for-solr.sh` com sucesso = 1; `solr_cli.py` com `-u -c -s -rf -ms` e `--embedded_zk`; mensagens "Solr is offline…" e "Solr support is not initialized.") — detalhes na feature 008
- [ ] T020 [US2] Em `_docker/dev/start-dev.sh`, acrescentar `rm ${HOME}/logs/celery/*.pid`, o `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=${COMPOSE_PROJECT_NAME}-redis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log`, `sleep 3` e `yes yes | python3 manage.py runserver 0.0.0.0:9000`; manter comentada a variante de 16 workers
- [ ] T021 [US2] Validar o bootstrap (quickstart §3): `.env` com nove chaves sem duplicatas (SC-002), reexecução idempotente, migrações aplicadas (SC-003), `logs/celery/*` gerados, `celery inspect ping`
- [ ] T022 [P] [US2] Registrar nos comentários do script/README que `SECRET_KEY` não é gerada em dev (research.md item 1)

**Ponto de Controle**: `appdev` autossuficiente após `up`.

---

## Fase 5: História de Usuário 3 - Várias instâncias (Prioridade: P2)

**Objetivo**: instâncias isoladas por `COMPOSE_PROJECT_NAME`.

**Teste Independente**: `./rdev.sh startdev2` cria `startdev2-*` sem afetar `startdev1-*`.

- [ ] T023 [US3] Conferir que todo `container_name`, `SOLR_COLLECTIONS`, `SOLR_URL` e hosts em `_docker/dev/docker-compose.yaml` e em `change_env_file` usam `${COMPOSE_PROJECT_NAME:-startdev1}`/`${COMPOSE_PROJECT_NAME}`
- [ ] T024 [US3] Documentar (README, seção "Executando em desenvolvimento") que, para instâncias simultâneas, é preciso ajustar `APP_PORT` e as portas fixas `5433`, `6379`, `8983`, `9983`, `5173` (research.md item 15)
- [ ] T025 [US3] Validar com duas instâncias (quickstart §6): nomes distintos, bancos distintos, coleções `startdev2_arq1/arq2`

---

## Fase 6: História de Usuário 4 - `runserver` no host (Prioridade: P2)

**Objetivo**: o Django no host usa `localhost:5433`, Redis em `localhost` e Solr em `localhost:8983`.

**Teste Independente**: `python manage.py runserver` no host imprime host `localhost` e porta `5433`.

### Testes

- [ ] T026 [P] [US4] Criar teste `pytest` (ex.: `backend/tests.py` ou `_tests/test_ambiente_docker.py`) que, com `monkeypatch.setenv`, recarrega `backend.settings.project`/`solr`/`zasyncs` e verifica o modo host (`HOST=localhost`, `PORT=5433`, `SOLR_URL` terminando em `@localhost:8983`, `REDIS_HOST=localhost`) e o modo contêiner (`FOLDER_DEBUG_CONTAINER == PROJECT_DIR`, hosts originais)

### Implementação

- [ ] T027 [US4] Em `backend/settings/project.py`, definir `DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)`, `DATABASES["default"] = config("DATABASE_URL_DEV" if DEBUG else "DATABASE_URL_PRD", cast=db_url)` e o bloco `if DEBUG and FOLDER_DEBUG_CONTAINER != PROJECT_DIR:` com `HOST="localhost"`, `PORT=5433` e os três `print`
- [ ] T028 [P] [US4] Em `backend/settings/solr.py`, no modo host: `SOLR_URL = SOLR_URL.split("@")[0] + "@localhost:8983"`
- [ ] T029 [P] [US4] Em `backend/settings/zasyncs.py`, no modo host: `REDIS_HOST = "localhost"`; `CELERY_BROKER_URL = redis://{REDIS_HOST}:{REDIS_PORT}`
- [ ] T030 [P] [US4] Em `backend/settings/medias.py`, `MEDIA_ROOT`/`MEDIA_CACHE_ROOT` em `PROJECT_DIR.parent/backend_media/...` e, com `DEBUG` fora de `/var/project`, `/mnt/volumes/backend_media/...` (feature 009)
- [ ] T031 [US4] Validar execução híbrida (quickstart §5) e `DEBUG_TOOLBAR_ACTIVE` apenas no host

---

## Fase 7: História de Usuário 5 - Imagem-base publicável (Prioridade: P2)

**Objetivo**: base reconstruível e publicável.

- [ ] T032 [US5] Confirmar que o rodapé de `_docker/foundation/Dockerfile` documenta `docker build -t building_foundation:0003 .`, `docker login`, `docker tag` e `docker push` (plan.md §1, item 10)
- [ ] T033 [US5] Validar a imagem (quickstart §1): Python 3.14.x, Node 26, `psql` 18, `gs` 10.08.0, `jbig2`, `tesseract --list-langs` com `por`, Poetry, Java 17 (SC-006)
- [ ] T034 [P] [US5] Verificar que `/etc/nginx/conf.d/*` e `/etc/nginx/sites-enabled/*` foram removidos e que `CMD` é `python3`

---

## Fase 8: História de Usuário 6 - Frontend com HMR (Prioridade: P3)

**Objetivo**: Vite no contêiner `front` ou no host.

- [ ] T035 [P] [US6] Criar `startfront-dev.sh` na raiz (`#!/usr/bin/env bash`; `npm install`; `npm run dev`) com `chmod +x`
- [ ] T036 [US6] Validar que `http://localhost:5173/` responde no contêiner `front` e que `./startfront-dev.sh` funciona no host com Node 26; conferir `server.host '0.0.0.0'` e `watch.usePolling` em `vite.config.js` (feature 007)

---

## Fase 9: História de Usuário 7 - Manutenção e legados (Prioridade: P3)

**Objetivo**: utilitários e Dependabot registrados.

- [ ] T037 [P] [US7] Criar `_docker/dev/recreate_db.sh` (`#!/bin/bash`; três `docker exec stormdb psql -U sddstart -d postgres -c …`: `pg_terminate_backend`, `DROP DATABASE IF EXISTS sddstart;`, `CREATE DATABASE sddstart WITH OWNER = sddstart ENCODING = 'UTF8' CONNECTION LIMIT = -1;`) — legado; documentar que não corresponde ao Compose atual
- [ ] T038 [P] [US7] Validar `.github/dependabot.yml` (quickstart §8) e decidir entre replicar a chave `updates:` repetida ou corrigir para lista única (recomendado corrigir; incluir `docker` em `/_docker/foundation`)
- [ ] T039 [P] [US7] Registrar `.vscode/` no `.gitignore` e documentar a necessidade de `launch.json` local para depurar no host

---

## Fase 10: Acabamento e Preocupações Transversais

- [ ] T040 [P] Atualizar `README.md` (pré-requisitos, `backend/.env` com `SECRET_KEY`, scripts `rdev.sh`/`uupdev.sh`/`ddev.sh`, tabela de endereços, múltiplas instâncias, `startfront-dev.sh`)
- [ ] T041 [P] Rodar `bash -n` nos scripts e `docker compose … config -q` (quickstart §8)
- [ ] T042 [P] Rodar `ruff check .` e `pytest -q` (princípio VIII) dentro do contêiner `appdev`
- [ ] T043 Revisar os itens "Corrigir" de `research.md` (5, 10, 11, 15) e decidir quais aplicar; se aplicar, atualizar spec/plan na mesma entrega
- [ ] T044 Executar a validação completa do `quickstart.md`
- [ ] T045 Confirmar que nenhum segredo real foi versionado (somente padrões `startdev1`) e que `backend/.env` permanece ignorado

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências.
- **Fundacional (Fase 2)**: depende da Fase 1; **bloqueia** todas as histórias (T006/T010 precisam preceder T012 e T016).
- **US1 (Fase 3)** e **US2 (Fase 4)** formam o MVP; US2 só é validável com US1 (os contêineres) e requer T009 (`SECRET_KEY`).
- **US3, US4, US5, US6, US7**: dependem de US1; US4 (T027–T030) é independente do Compose e pode ser feita em paralelo.
- **Acabamento (Fase 10)**: após as histórias desejadas.

### Dependências entre Tarefas

- T011 depende de T007, T012 e T013; T016 depende de T010–T015 e de T017–T020 (o `CMD` do `appdev` executa `start-dev.sh`).
- T018–T020 dependem de T017 (mesmo arquivo, sequenciais).
- T021 depende de T016.

### Oportunidades de Paralelismo

T002–T005; T007–T008; T012–T014; T028–T030; T035, T037–T039; T040–T042.

---

## Estratégia de Implementação

1. **MVP**: Fases 1–4 (US1 + US2): imagem-base, Compose, imagens de dev, scripts de raiz e `start-dev.sh`.
2. **Incremento**: US3 (instâncias), US4 (host), US5 (publicação da base).
3. **Complementos**: US6 (frontend) e US7 (manutenção).
4. **Acabamento**: documentação, validações estáticas e do quickstart.
5. Reproduzir o estado atual por fidelidade (inclusive as particularidades de `research.md`); aplicar correções somente por decisão explícita (T043).
