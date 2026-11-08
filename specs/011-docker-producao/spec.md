# Especificação da Funcionalidade: Docker para Produção

**Branch da Funcionalidade**: `011-docker-producao`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: ambiente de produção em Docker (`_docker/prod/`: `Dockerfile`, `docker-compose.yaml`, `.env_prod_compose`, `start.sh`, `start_gunicorn.sh`, `start_daphne.sh`, `wait-for-pg.sh`, configuração do Nginx), scripts de raiz `upprod.sh`/`dprod.sh`, configuração `backend/settings/fake.py` e detecção do ambiente de produção em `backend/settings/zenv.py`."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Subir toda a pilha de produção com um único comando (Prioridade: P1)

Quem opera o sistema ajusta o arquivo `_docker/prod/.env_prod_compose` (porta, credenciais, `SITE_URL`), executa `./upprod.sh [nome]` na raiz do repositório e, sem nenhuma etapa manual adicional, obtém o sistema completo (aplicação, banco PostgreSQL, Redis e Solr) funcionando e acessível em `http://<host>:<APP_PORT>`.

**Por que esta prioridade**: sem a subida automatizada não há produção; é o valor central da funcionalidade e a "interface oficial" definida pela constituição (Princípio III).

**Teste Independente**: em uma máquina com Docker, executar `./upprod.sh` e abrir `http://localhost:9001/`; a página inicial do sistema deve responder e o contêiner `startprod1-app` deve estar em execução.

**Cenários de Aceitação**:

1. **Dado** um repositório recém-clonado com `backend/.env` contendo ao menos `SECRET_KEY`, **Quando** `./upprod.sh` é executado sem argumento, **Então** o projeto Compose `startprod1` é construído e iniciado em segundo plano, com contêineres `startprod1-redis`, `startprod1-solr`, `startprod1-db` e `startprod1-app`.
2. **Dado** que a pilha subiu, **Quando** o navegador acessa `http://localhost:${APP_PORT}` (padrão `9001`), **Então** a requisição chega ao Nginx na porta 80 do contêiner `app` e a aplicação responde.
3. **Dado** que `./upprod.sh meusite` foi executado, **Quando** os contêineres são listados, **Então** todos têm o prefixo `meusite-` (o nome do projeto Compose é o primeiro argumento do script).

---

### História de Usuário 2 - Imagem imutável com frontend compilado e estáticos coletados (Prioridade: P1)

A imagem de produção contém o código-fonte, as dependências Python de execução (sem os grupos de desenvolvimento, teste e documentação), o frontend já compilado pelo Vite e os arquivos estáticos já coletados, de modo que nenhum código é montado como volume e nada é compilado em tempo de execução.

**Por que esta prioridade**: garante que o ambiente de produção seja reprodutível e rápido para iniciar, e diferencia produção (imagem imutável) de desenvolvimento (código montado) — Princípio III.

**Teste Independente**: `docker compose -f _docker/prod/docker-compose.yaml build app` conclui com sucesso e, dentro da imagem, existem `/var/project/backend/collectedstatic/frontend/.vite/manifest.json` e `/var/project/backend/collectedstatic/frontend/service-worker.js`.

**Cenários de Aceitação**:

1. **Dado** a imagem-base da feature 010, **Quando** a imagem de produção é construída, **Então** as dependências Python são instaladas sem os grupos `dev`, `test` e `docs`, o frontend é compilado com `npm run build` e `collectstatic` é executado com `--settings=backend.settings.fake`.
2. **Dado** que o build não tem banco PostgreSQL disponível, **Quando** `collectstatic` roda, **Então** ele usa a configuração `backend.settings.fake` (SQLite descartável, `DEBUG=False`, Vite fora do modo de desenvolvimento) e o arquivo `db.sqlite3` resultante é removido da imagem.
3. **Dado** a imagem pronta, **Quando** o contêiner inicia, **Então** não há necessidade de acesso à internet nem de compilação de frontend.

---

### História de Usuário 3 - Inicialização automática e ordenada do contêiner da aplicação (Prioridade: P1)

Ao iniciar, o contêiner `app` prepara a configuração (gerando e persistindo a `SECRET_KEY` na primeira vez), aplica as migrações, prepara as coleções Solr (quando habilitado), e inicia na ordem: Celery → Gunicorn → Daphne → Nginx (em primeiro plano).

**Por que esta prioridade**: sem esta orquestração a imagem não serve requisições; ela concentra a lógica de "subir do zero com um comando" da constituição.

**Teste Independente**: subir a pilha e verificar nos logs a sequência de mensagens (`====> StartPRD...`, migrações, "Solr configurations", "Iniciando: BACKEND.wsgi", "Iniciando: BACKEND.asgi", "Iniciando NGINX...") e a existência de `backend_data/secret.key` e `backend_data/.env` no volume `data`.

**Cenários de Aceitação**:

1. **Dado** um volume `data` vazio, **Quando** o contêiner inicia pela primeira vez, **Então** uma `SECRET_KEY` aleatória de 50 caracteres é gerada, gravada em `backend_data/secret.key` e escrita em `backend_data/.env` junto com as demais variáveis (banco, Solr, Redis, `DEBUG`, `SITE_URL` etc.).
2. **Dado** um volume `data` já inicializado, **Quando** o contêiner reinicia, **Então** a mesma `SECRET_KEY` é reutilizada (sessões e tokens permanecem válidos) e as variáveis do `.env` são reescritas com os valores do ambiente atual do contêiner.
3. **Dado** `USE_SOLR=True` (valor definido no Compose de produção), **Quando** o Solr responde, **Então** as coleções de `SOLR_COLLECTIONS` são criadas/configuradas antes do Celery iniciar.
4. **Dado** que todos os serviços foram iniciados, **Quando** o Nginx entra em primeiro plano, **Então** ele passa a ser o processo que mantém o contêiner vivo.

---

### História de Usuário 4 - Roteamento do Nginx: estáticos, mídia protegida, WebSocket, API e aplicação (Prioridade: P2)

O Nginx é o único ponto de entrada (porta 80 do contêiner): serve diretamente estáticos e arquivos especiais, delega a entrega de mídia protegida via `X-Accel-Redirect`, encaminha `/ws/` ao Daphne e todo o restante ao Gunicorn, com cabeçalhos CORS abertos nas rotas `/api`.

**Por que esta prioridade**: define o desempenho e a segurança de entrega; depende da pilha (US1–US3) em execução.

**Teste Independente**: com a pilha no ar, `curl -I http://localhost:9001/static/frontend/favicon.ico` retorna `200` com `Cache-Control: public`; `curl -I http://localhost:9001/mediaredirect/qualquer` retorna `404` (location interna); `curl -i -X OPTIONS http://localhost:9001/api/` retorna `204` com `Access-Control-Allow-Origin: *`.

**Cenários de Aceitação**:

1. **Dado** a pilha no ar, **Quando** `/robots.txt`, `/favicon.ico`, `/service-worker.js` ou `/manifest.json` são requisitados, **Então** o Nginx os serve diretamente de `collectedstatic` (os dois últimos de `collectedstatic/frontend/`), sem passar pela aplicação.
2. **Dado** um arquivo em `/static/...`, **Quando** é requisitado, **Então** é servido de `collectedstatic/` com `gzip_static on`, `expires 7d`, `Pragma: public` e `Cache-Control: public`.
3. **Dado** que a aplicação responde com `X-Accel-Redirect: /mediaredirect/<caminho>`, **Quando** o Nginx recebe essa resposta, **Então** ele entrega o arquivo de `/var/project/backend_media/media/` com cabeçalhos de não-cache; requisições diretas do cliente a `/mediaredirect/` são recusadas (location `internal`).
4. **Dado** uma conexão WebSocket em `/ws/sync/`, **Quando** o cliente faz o upgrade, **Então** o Nginx a encaminha ao Daphne com `Upgrade`/`Connection: upgrade`.
5. **Dado** uma requisição a `/api...`, **Quando** o método é `OPTIONS`, **Então** a resposta é `204` com cabeçalhos CORS de preflight; para os demais métodos a requisição segue ao Gunicorn com cabeçalhos CORS abertos (`*`) na resposta.
6. **Dado** qualquer outra rota (`/`), **Quando** requisitada, **Então** vai ao Gunicorn (`try_files $uri @proxy_to_app`).
7. **Dado** um upload de até 4 GB, **Quando** enviado, **Então** o Nginx não o recusa por tamanho (`client_max_body_size 4G`).

---

### História de Usuário 5 - Persistência, múltiplas instâncias e desligamento (Prioridade: P2)

Dados do banco, Redis, Solr, `backend_data`, mídia e logs ficam em volumes nomeados que sobrevivem a `down`/`up`. Várias instâncias independentes podem coexistir variando o nome do projeto e `APP_PORT`. `./dprod.sh [nome]` derruba a pilha e devolve a propriedade dos arquivos do diretório ao usuário.

**Por que esta prioridade**: garante continuidade dos dados em atualizações e a paridade multi-instância (Princípio III).

**Teste Independente**: subir, criar dados, executar `./dprod.sh`, subir novamente e verificar que os dados e a `SECRET_KEY` permanecem.

**Cenários de Aceitação**:

1. **Dado** uma pilha em execução, **Quando** `./dprod.sh` é executado, **Então** `docker compose down` remove os contêineres e a rede, mas não os volumes nomeados.
2. **Dado** duas instâncias com nomes e `APP_PORT` diferentes, **Quando** ambas sobem, **Então** não há conflito de contêineres, volumes, hosts de rede, bancos nem coleções Solr (prefixados pelo nome do projeto).
3. **Dado** `./dprod.sh`, **Quando** a derrubada termina, **Então** é executado `sudo chown -R <usuário>:<grupo> .` no diretório corrente.

---

### História de Usuário 6 - Configuração de produção segura por padrão no Django (Prioridade: P3)

Em produção, o Django roda com `DEBUG=False`, lê toda a configuração do arquivo `backend_data/.env` (fora da árvore do código), conecta no banco por `DATABASE_URL_PRD`, lê o manifesto do Vite a partir de `STATIC_ROOT` (`collectedstatic`) e confia na origem `SITE_URL` para CSRF.

**Por que esta prioridade**: o comportamento já é obtido pelos scripts da US3; esta história formaliza as regras de configuração do código Django.

**Teste Independente**: com `backend_data/.env` presente, importar `backend.settings` e verificar `DEBUG is False`, `DJANGO_VITE["default"]["dev_mode"] is False`, `DATABASES["default"]` apontando para o host `<projeto>-db` e `CSRF_TRUSTED_ORIGINS == [SITE_URL]`.

**Cenários de Aceitação**:

1. **Dado** que `<raiz>/backend_data/.env` existe (a raiz é o pai da pasta do projeto, `/var/project` no contêiner), **Quando** as configurações são carregadas, **Então** o `python-decouple` busca as variáveis nessa pasta em vez de percorrer a árvore do código.
2. **Dado** `DEBUG=False`, **Quando** o banco é configurado, **Então** a variável `DATABASE_URL_PRD` é obrigatória (sem valor padrão) e é interpretada por `dj_database_url`.
3. **Dado** `SITE_URL=http://host:porta`, **Quando** um formulário é submetido por essa origem, **Então** a origem é aceita pelo CSRF.
4. **Dado** que `collectstatic` roda com `backend.settings.fake`, **Quando** o comando termina, **Então** o manifesto do Vite foi resolvido em `DJANGO_VITE_ASSETS_PATH/frontend/.vite/manifest.json` e os estáticos estão em `collectedstatic/`.

---

### Casos de Borda

- **Primeiro start sem `backend_data/.env`**: `change_env_file` executa `sed -i` em arquivo inexistente (erro ignorado, o script não usa `set -e`) e o arquivo é criado pelo `echo ... >>` seguinte; só depois o Django passa a detectar o modo de produção.
- **Banco ainda não pronto**: o Compose usa `condition: service_started` para `db`; o `wait-for-pg.sh` existe mas está desativado (comentado) em `start.sh`. Se o PostgreSQL ainda não aceita conexões, `migrate` falha e o script **continua** subindo os demais processos.
- **Solr indisponível**: o `wait-for-solr.sh` esgota as tentativas, o script imprime "Solr is offline, not possible to connect." e a inicialização continua sem criar coleções. Com `USE_SOLR` diferente de `True`/`true`, imprime "Solr support is not initialized.".
- **Valores com `|`, `&` ou `\`** em senhas/URLs quebram a substituição por `sed` no `.env` (delimitador `|`).
- **`SITE_URL` não definida** no ambiente: o Compose usa `http://localhost:${APP_PORT:-9001}`; o código Django, se nenhuma variável existir, usa `http://192.168.15.9:9001`.
- **Processo auxiliar morto**: Celery, Gunicorn e Daphne são iniciados em segundo plano; apenas o Nginx mantém o contêiner vivo. Se um deles cair, nada o reinicia (Daphne tenta até 5 vezes só na partida).
- **`X-Forwarded-Proto: https` fixo** nos proxies: mesmo servido por HTTP simples (`http://host:9001`), o Django é informado de que a requisição é HTTPS pelo cabeçalho; o Django só o honra se `SECURE_PROXY_SSL_HEADER` estiver configurada (não está no código atual).
- **`/mediaredirect/`** acessado diretamente por um cliente: `404`/negado (location `internal`).
- **Diretório do projeto montado sem `package-lock.json` na imagem**: o `npm install` do build resolve versões dentro dos intervalos de `package.json` (build não reprodutível).
- **`dprod.sh` fora da raiz do repositório** aplica `chown -R` no diretório onde for executado.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE oferecer o script `upprod.sh [nome]` que executa `sudo docker compose -p <nome> --env-file _docker/prod/.env_prod_compose --progress=plain -f _docker/prod/docker-compose.yaml up --build -d`, com `<nome>` padrão `startprod1`.
- **FR-002**: O sistema DEVE oferecer o script `dprod.sh [nome]` que executa `docker compose ... down` (com o mesmo `-p`, `--env-file` e `-f`) e, em seguida, `sudo chown -R $(whoami):$(whoami) .`, sem remover volumes.
- **FR-003**: O arquivo `_docker/prod/.env_prod_compose` DEVE definir `APP_PORT` (9001), `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB` (todos `startprod1` como exemplo), `SOLR_PASSWORD`, `SOLR_DB` (`startprod1`) e `SITE_URL` (`http://192.168.15.9:9001`), com comentário "customizar para produção!".
- **FR-004**: O `docker-compose.yaml` DEVE definir os serviços `redis` (imagem `redis:bookworm`, healthcheck `redis-cli ping`, intervalo 5s, timeout 10s, 10 tentativas, volume `redis_data`), `solr` (imagem `solr:9.7`, comando `bin/solr start -c -f`, volumes `solr9_data` e `solr9_configsets`), `db` (imagem `pgvector/pgvector:0.8.7-pg18-bookworm`, `postgres -c shared_preload_libraries=pg_stat_statements`, volume `dbdata`) e `app` (build da imagem de produção), todos na rede bridge `app-net`, com `restart: always`.
- **FR-005**: Os nomes dos contêineres DEVEM seguir `${COMPOSE_PROJECT_NAME:-startprod1}-<serviço>` e as coleções Solr, o host de banco, o host do Redis e o host do Solr DEVEM derivar de `COMPOSE_PROJECT_NAME`.
- **FR-006**: As portas do Redis (6379), Solr (8983) e PostgreSQL (5433) NÃO DEVEM ser publicadas no host em produção; somente `${APP_PORT:-9001}:80` do serviço `app` DEVE ser publicado.
- **FR-007**: O serviço `app` DEVE executar como `root:root`, receber `DEBUG='False'`, `USE_SOLR='True'`, `IS_ZK_EMBEDDED='True'`, `TZ=America/Sao_Paulo`, `SOLR_COLLECTIONS`, `SOLR_URL` (com credenciais básicas), `COMPOSE_PROJECT_NAME`, `POSTGRES_*` e `SITE_URL`, e montar os volumes `data`→`/var/project/backend_data`, `media`→`/var/project/backend_media` e `logs`→`/var/project/backend/logs`.
- **FR-008**: O serviço `app` DEVE aguardar `db` e `solr` com `service_started` e `redis` com `service_healthy`.
- **FR-009**: A imagem de produção DEVE partir de `leandrojatai/building_foundation:0003`, definir `ROOT_HOME=/var/project` e `HOME=${ROOT_HOME}/backend`, criar `run`, `logs/celery`, `backend_data` e `backend_media`, instalar dependências com `poetry install --without dev,test,docs`, e compilar o frontend com `npm install` e `npm run build`.
- **FR-010**: A imagem DEVE adicionar os diretórios `_frontend`, `solr`, `drfautoapi`, `backend`, `_templates` e `_docker`, executar `python3 manage.py collectstatic --noinput --clear --settings=backend.settings.fake --no-default-ignore`, remover `db.sqlite3` e copiar as configurações do Nginx e os scripts (`start.sh`, `wait-for-pg.sh`, `wait-for-solr.sh`, `start_gunicorn.sh`, `start_daphne.sh`, `solr_cli.py`, `genkey.py`) para `${HOME}`, tornando os `.sh` executáveis.
- **FR-011**: A imagem DEVE criar o usuário de sistema `nginx` (`useradd -r --no-create-home -g root nginx`), definir `USER nginx`, expor `80/tcp`, declarar `VOLUME` para `backend_data`, `backend_media` e `logs` e usar `CMD ["/var/project/backend/start.sh"]`.
- **FR-012**: `start.sh` DEVE, ao iniciar, ler `backend_data/secret.key` se existir; caso contrário gerar uma chave com `python3 genkey.py` (50 caracteres de `abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)`, via `random.SystemRandom`) e persisti-la nesse arquivo.
- **FR-013**: `start.sh` DEVE reescrever `SECRET_KEY` em `backend_data/.env` e garantir, por substituição por expressão regular (ou acréscimo se ausente), as chaves `DATABASE_URL_PRD`, `SOLR_COLLECTIONS`, `SOLR_URL`, `DEBUG`, `DJANGO_VITE_DEV_MODE`, `REDIS_HOST`, `FOLDER_DEBUG_CONTAINER`, `COMPOSE_PROJECT_NAME`, `TZ` e `SITE_URL`, e colapsar três ou mais quebras de linha consecutivas.
- **FR-014**: `start.sh` DEVE executar `yes yes | python3 manage.py migrate`, depois o bloco Solr condicional a `USE_SOLR` (`True`/`true`) — com `wait-for-solr.sh` e `solr_cli.py` — e `sleep 3`.
- **FR-015**: `start.sh` DEVE remover `logs/celery/*.pid`, iniciar o Celery com `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 --hostname=backendredis --pidfile=./logs/celery/%n.pid --logfile=./logs/celery/%n%I.log`, aguardar 3 s, iniciar `start_gunicorn.sh` em segundo plano, aguardar 3 s, iniciar `start_daphne.sh` em segundo plano, aguardar 5 s e, por fim, executar `/usr/sbin/nginx -g "daemon off;"` em primeiro plano.
- **FR-016**: `start_gunicorn.sh` DEVE servir `backend.wsgi:application` em socket unix `/var/project/backend/run/gunicorn.sock`, com 9 workers, `--timeout 300`, `--max-requests 1000`, `--log-level info`, `--user` igual ao usuário corrente, logs de acesso e erro em `/var/project/backend/logs/gunicorn_access.log` e `gunicorn_error.log`, via `exec`.
- **FR-017**: `start_daphne.sh` DEVE servir `backend.asgi:application` em socket unix `/var/project/backend/run/daphne.sock` com `--access-log /var/project/backend/logs/daphne_access.log -v1`, repetindo até 5 vezes (com `sleep 5` entre tentativas) se o processo terminar com erro, e saindo com código 1 ao esgotar as tentativas.
- **FR-018**: `wait-for-pg.sh` DEVE bloquear em laço (10 s entre tentativas) até que `psql <url> -c '\l \q'` liste ao menos uma linha contendo `backend`; o script NÃO DEVE ser invocado por `start.sh` na versão atual (linha comentada).
- **FR-019**: `nginx/nginx_docker.conf` DEVE definir `user nginx root`, `worker_processes 1`, `worker_connections 1024`, `sendfile off`, `server_tokens off`, `keepalive_timeout 300`, `proxy_connect_timeout 75s`, `proxy_read_timeout 300s`, compressão gzip (nível 5, `gzip_proxied any`, `gzip_vary on`, tipos de texto/JS/XML/imagens) e incluir `/etc/nginx/conf.d/*.conf`.
- **FR-020**: `nginx/backend_docker.conf` DEVE declarar os upstreams `backend_leg_app_server` (`unix:/var/project/backend/run/gunicorn.sock`, `fail_timeout=0`) e `backend_channels_server` (`unix:/var/project/backend/run/daphne.sock`), ouvir na porta 80 com `client_max_body_size 4G` e logs em `/var/project/backend/logs/nginx-access.log` e `nginx-error.log`.
- **FR-021**: O Nginx DEVE servir `= /robots.txt` e `= /favicon.ico` de `collectedstatic/`, `= /service-worker.js` e `= /manifest.json` de `collectedstatic/frontend/`, e `/static/` de `collectedstatic/` com `gzip_static on`, `expires 7d`, `Pragma public` e `Cache-Control "public"`.
- **FR-022**: O Nginx DEVE expor `/mediaredirect/` como location `internal`, com alias `/var/project/backend_media/media/` e cabeçalhos `Pragma: no-cache`, `Cache-Control: no-cache`, `Expires 0`.
- **FR-023**: O Nginx DEVE encaminhar `/ws/` ao Daphne (HTTP/1.1, `Upgrade: $http_upgrade`, `Connection: upgrade`, `Host $host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto https`, `X-Forwarded-Host $server_name`), `/api` ao Gunicorn com cabeçalhos CORS abertos e resposta `204` a preflight `OPTIONS`, e `/` ao Gunicorn com `proxy_connect_timeout 75s` e `proxy_read_timeout 600s`.
- **FR-024**: `backend/settings/fake.py` DEVE importar todas as configurações de `project.py`, forçar `DEBUG = False` e `DJANGO_VITE_DEV_MODE = False`, usar SQLite em `PROJECT_DIR/db.sqlite3` e apontar o manifesto do Vite para `DJANGO_VITE_ASSETS_PATH/frontend/.vite/manifest.json`; DEVE ser usado apenas no `collectstatic` do build.
- **FR-025**: `backend/settings/zenv.py` DEVE considerar o ambiente como produção quando `<pai do projeto>/backend_data/.env` existe e, nesse caso, buscar o `.env` apenas em `backend_data`; `DEBUG` DEVE ter padrão `False`.
- **FR-026**: `backend/settings/project.py` DEVE ler `SITE_URL` (padrão `http://192.168.15.9:9001`), definir `CSRF_TRUSTED_ORIGINS = [SITE_URL]` e `DATABASES["default"]` a partir de `DATABASE_URL_PRD` quando `DEBUG` é falso (`DATABASE_URL_DEV` quando verdadeiro).
- **FR-027**: Com `DEBUG` falso, `backend/settings/frontend.py` DEVE definir `DJANGO_VITE_DEV_MODE` falso e ler o manifesto do Vite em `STATIC_ROOT/frontend/.vite/manifest.json` (`STATIC_ROOT = PROJECT_DIR / "collectedstatic"`).
- **FR-028**: O sistema NÃO DEVE gravar segredos reais no repositório; os valores `startprod1` em `.env_prod_compose` são apenas exemplo e DEVEM ser trocados em produção.

### Entidades-Chave

- **Projeto Compose**: instância nomeada (`startprod1` por padrão) que prefixa contêineres, volumes e rede.
- **Imagem `app` de produção**: imagem imutável com código, dependências, frontend compilado, estáticos coletados, Nginx configurado e scripts de inicialização.
- **Volumes nomeados**: `dbdata`, `data` (`backend_data`: `.env` e `secret.key`), `media`, `logs`, `solr9_data`, `solr9_configsets`, `redis_data`.
- **Arquivo `backend_data/.env`**: configuração de runtime gerada/atualizada pelo `start.sh`.
- **Sockets unix** `gunicorn.sock` e `daphne.sock` em `/var/project/backend/run/`.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Com a imagem-base disponível e `backend/.env` criado, um único comando (`./upprod.sh`) leva a pilha a responder HTTP `200`/`302` na porta `APP_PORT` sem nenhuma etapa manual.
- **SC-002**: Em reinícios do contêiner `app`, a `SECRET_KEY` em `backend_data/.env` é idêntica à de `backend_data/secret.key` em 100% das execuções.
- **SC-003**: Nenhuma porta além de `APP_PORT` é publicada no host (`docker ps` mostra apenas `0.0.0.0:<APP_PORT>->80/tcp`).
- **SC-004**: Dois projetos Compose com nomes e `APP_PORT` distintos funcionam simultaneamente sem erro de conflito de nome/porta/volume.
- **SC-005**: `curl -I` em `/static/<arquivo existente>` retorna `200` com `Cache-Control: public` e `Expires` ≈ 7 dias; em `/mediaredirect/x` retorna `404`.
- **SC-006**: O `collectstatic` no build conclui sem acesso a PostgreSQL e a imagem final não contém `db.sqlite3` na raiz do projeto.
- **SC-007**: `docker compose down` seguido de `up` preserva dados do banco, mídia, logs e `backend_data` (volumes nomeados mantidos).
- **SC-008**: Após o start, os processos `celery`, `gunicorn` (9 workers + mestre), `daphne` e `nginx` estão em execução dentro do contêiner `app`.

## Premissas

- Pré-requisitos por pasta: `specs/001-fundacao-projeto-django` (configurações e `zenv.py`), `specs/007-frontend-vite-vue` (build do frontend e manifesto Vite), `specs/008-busca-solr-haystack` (Solr, `solr_cli.py`, `wait-for-solr.sh`, `security.json`), `specs/009-midia-arquivos-avatar` (entrega de mídia por `X-Accel-Redirect` para `/mediaredirect/`), `specs/006-sincronizacao-tempo-real` (rota `/ws/sync/`) e `specs/010-docker-desenvolvimento` (imagem-base `leandrojatai/building_foundation:0003`, `_docker/foundation/Dockerfile`).
- O host tem Docker e Docker Compose v2, `sudo` sem prompt interativo problemático e acesso à imagem-base (local ou em registro).
- O `backend/.env` de desenvolvimento existe no momento do build: como não há `.dockerignore` efetivo na raiz do contexto (o de `backend/.dockerignore` não é lido pelo Docker), `ADD backend` o inclui na imagem, e é ele que fornece `SECRET_KEY`/`DATABASE_URL_PRD` ao `collectstatic` do build (suposição inferida do comportamento de `python-decouple` quando `backend_data/.env` ainda não existe).
- A terminação TLS (HTTPS) é feita por um proxy externo à pilha; por isso os proxies fixam `X-Forwarded-Proto https`. A pilha em si escuta apenas HTTP.
- `ALLOWED_HOSTS` e CORS abertos são do esqueleto e DEVEM ser restringidos por quem derivar o projeto (constituição, "Segurança").
- Os scripts presumem a execução na raiz do repositório e um usuário com `sudo`.
