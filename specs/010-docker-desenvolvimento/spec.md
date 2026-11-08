# Especificação da Funcionalidade: Ambiente Docker de Desenvolvimento e Imagem-Base

**Branch da Funcionalidade**: `010-docker-desenvolvimento`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: imagem-base `building_foundation:0003` (`_docker/foundation/Dockerfile`), ambiente de desenvolvimento em Docker Compose (`_docker/dev/`: `.env_dev_compose`, `Dockerfile.Dev`, `Dockerfile.Dev.Front`, `docker-compose.yaml`, `start-dev.sh`, `recreate_db.sh`), scripts de raiz (`rdev.sh`, `uupdev.sh`, `ddev.sh`, `startfront-dev.sh`, `libreoffice_entrypoint.sh`), `backend/.dockerignore`, `.github/dependabot.yml` e a lógica de execução em contêiner × host nos settings (`FOLDER_DEBUG_CONTAINER`, `DEBUG_RUNNING_CONTAINER`)."

**Pré-requisitos (features)**: `001-fundacao-projeto-django` (settings divididos e `zenv.py`), `006-sincronizacao-tempo-real` (Redis/Channels/Celery), `007-frontend-vite-vue` (Vite), `008-busca-solr-haystack` (detalhes do Solr e de `solr_cli.py`), `009-midia-arquivos-avatar` (`backend_media`). A produção é tratada em `011-docker-producao`.

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Subir todo o ambiente de desenvolvimento com um comando (Prioridade: P1)

Uma pessoa desenvolvedora, com Docker instalado e um `backend/.env` contendo apenas `SECRET_KEY`, executa `./rdev.sh` na raiz do repositório e obtém, sem etapas manuais adicionais, PostgreSQL (pgvector), Redis, Solr, o servidor Vite com HMR e a aplicação Django em `runserver`, todos conectados por uma rede interna.

**Por que esta prioridade**: é a razão de existir da funcionalidade (princípio III da constituição: paridade e "um único comando por ambiente"). Sem ela o esqueleto não roda.

**Teste Independente**: com a imagem-base disponível, executar `./rdev.sh` e verificar `docker ps` (cinco contêineres `startdev1-*`), `curl -I http://localhost:9099/` e `http://localhost:5173/`.

**Cenários de Aceitação**:

1. **Dado** um clone limpo, o `backend/.env` com `SECRET_KEY` e Docker funcionando, **Quando** executo `./rdev.sh`, **Então** o Compose derruba o projeto anterior (se existir), ajusta o dono dos arquivos do repositório ao usuário atual e sobe, com `up --build -d`, os serviços `redis`, `solr`, `front`, `db` e `appdev` com os contêineres `startdev1-redis`, `startdev1-solr`, `startdev1-front`, `startdev1-db` e `startdev1-appdev`.
2. **Dado** o ambiente no ar, **Quando** acesso `http://localhost:9099`, **Então** a aplicação Django responde (porta interna 9000 publicada em `APP_PORT`, padrão 9099).
3. **Dado** o ambiente no ar, **Quando** edito um arquivo Python do backend ou um arquivo do frontend, **Então** a alteração é refletida sem reconstruir imagens (código montado por volume; `runserver` recarrega; Vite faz HMR em `http://localhost:5173`).
4. **Dado** que só quero subir/atualizar sem derrubar, **Quando** executo `./uupdev.sh`, **Então** o Compose executa apenas `up --build -d` com saída `--progress=plain`.
5. **Dado** o ambiente no ar, **Quando** executo `./ddev.sh`, **Então** os contêineres são removidos (volumes nomeados preservados) e o dono dos arquivos do repositório é devolvido ao usuário atual.

---

### História de Usuário 2 - Bootstrap automático do backend no contêiner `appdev` (Prioridade: P1)

Ao iniciar, o contêiner `appdev` prepara sozinho o `backend/.env`, aplica as migrações, inicializa o Solr (quando habilitado), inicia o worker Celery e coloca o servidor de desenvolvimento no ar.

**Por que esta prioridade**: é o que transforma os contêineres de apoio em um backend utilizável sem passos manuais; sem isso o banco ficaria sem esquema e o Celery sem worker.

**Teste Independente**: com `backend/.env` contendo só `SECRET_KEY`, subir o ambiente e inspecionar o `.env` (chaves acrescentadas), `docker logs startdev1-appdev` (migrações, bloco Solr, Celery e `runserver`) e `logs/celery/`.

**Cenários de Aceitação**:

1. **Dado** um `backend/.env` apenas com `SECRET_KEY`, **Quando** o contêiner inicia, **Então** `start-dev.sh` acrescenta ao arquivo as chaves `DATABASE_URL_DEV`, `SOLR_COLLECTIONS`, `SOLR_URL`, `DEBUG`, `DJANGO_VITE_DEV_MODE`, `REDIS_HOST`, `FOLDER_DEBUG_CONTAINER`, `COMPOSE_PROJECT_NAME` e `TZ` com valores derivados do nome do projeto e das variáveis do Compose.
2. **Dado** um `.env` que já possui essas chaves com outros valores, **Quando** o contêiner inicia, **Então** os valores existentes são sobrescritos pelos calculados (a chave é atualizada, não duplicada).
3. **Dado** o banco vazio, **Quando** o contêiner inicia, **Então** `manage.py migrate` é executado (confirmando automaticamente eventuais perguntas com `yes`) e as regras globais são aplicadas (feature 003).
4. **Dado** `USE_SOLR=True` (valor definido no Compose), **Quando** o Solr responde, **Então** as coleções `<projeto>_arq1` e `<projeto>_arq2` são criadas/verificadas via `solr_cli.py` (detalhes na feature 008); se o Solr não responder em 60 s, o script informa "Solr is offline, not possible to connect." e segue adiante.
5. **Dado** o fim do bootstrap, **Quando** o script chega ao final, **Então** um worker Celery (1 processo, fila `celery`) é iniciado em segundo plano e `runserver 0.0.0.0:9000` fica em primeiro plano como processo principal do contêiner.

---

### História de Usuário 3 - Várias instâncias independentes na mesma máquina (Prioridade: P2)

A pessoa desenvolvedora executa `./rdev.sh outroprojeto` para criar uma segunda instância isolada (contêineres, rede, volumes, banco e coleções Solr próprios).

**Por que esta prioridade**: permite trabalhar em dois derivados/branches em paralelo; é requisito da constituição, mas não bloqueia o uso básico.

**Teste Independente**: subir `./rdev.sh startdev1` e `./rdev.sh startdev2` (com portas publicadas ajustadas) e verificar `docker ps` e que os dados são distintos.

**Cenários de Aceitação**:

1. **Dado** o argumento `startdev2`, **Quando** executo `./rdev.sh startdev2`, **Então** o projeto Compose chama-se `startdev2` e os contêineres são `startdev2-redis|solr|front|db|appdev`, com volumes nomeados e rede prefixados pelo projeto.
2. **Dado** nenhum argumento, **Quando** executo qualquer script de raiz, **Então** o nome padrão é `startdev1`.
3. **Dado** o nome `startdev2`, **Quando** o contêiner `appdev` inicia, **Então** `REDIS_HOST`, `SOLR_URL`, `SOLR_COLLECTIONS` e `DATABASE_URL_DEV` usam os hosts `startdev2-redis`, `startdev2-solr`, `startdev2-db` e coleções `startdev2_arq1`/`startdev2_arq2`.
4. **Dado** que as portas `5433`, `6379`, `8983`, `9983` e `5173` são fixas no Compose, **Quando** duas instâncias sobem simultaneamente sem ajuste, **Então** haverá conflito de portas (só `APP_PORT` é parametrizável) — ver Casos de Borda.

---

### História de Usuário 4 - Rodar o `runserver` no host contra os serviços do Docker (Prioridade: P2)

A pessoa desenvolvedora (por exemplo, usando o depurador do VS Code, `debug_toolbar` ou notebooks) executa `python manage.py runserver` diretamente no host, mantendo banco, Redis e Solr nos contêineres.

**Por que esta prioridade**: melhora a depuração e a produtividade, mas é opcional frente ao fluxo 100% em contêiner.

**Teste Independente**: com o ambiente no ar, executar `python manage.py runserver` no host e ver no console "Running in debug mode with local database settings." com host `localhost` e porta `5433`.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e `FOLDER_DEBUG_CONTAINER` diferente do diretório do projeto (caso do host), **Quando** o Django carrega os settings, **Então** o banco usa `localhost:5433`, o Redis usa `localhost` (porta `REDIS_PORT`, 6379) e o Solr usa `localhost:8983` (mantendo as credenciais da URL).
2. **Dado** o mesmo `.env` dentro do contêiner (onde o projeto está em `/var/project/backend` e `FOLDER_DEBUG_CONTAINER` aponta para esse mesmo caminho), **Quando** o Django carrega os settings, **Então** são usados os hosts de rede interna (`<projeto>-db:5432`, `<projeto>-redis`, `<projeto>-solr:8983`).
3. **Dado** `DEBUG=True` rodando no host, **Quando** a mídia é configurada, **Então** `MEDIA_ROOT` é `/mnt/volumes/backend_media/media` (o mesmo diretório do host que o contêiner monta em `/var/project/backend_media`).

---

### História de Usuário 5 - Construir e publicar a imagem-base `building_foundation:0003` (Prioridade: P2)

Um mantenedor constrói localmente (ou publica em um registro) a imagem-base com Python 3.14, LibreOffice, Java, Tesseract, PostgreSQL 18 client, Ghostscript, jbig2enc, Node 26 e Poetry, que serve de `FROM` para as imagens de desenvolvimento e de produção.

**Por que esta prioridade**: as imagens `Dockerfile.Dev` e de produção dependem dela (`leandrojatai/building_foundation:0003`), mas ela raramente muda e normalmente é apenas baixada do registro.

**Teste Independente**: `docker build -t building_foundation:0003 _docker/foundation` e, dentro da imagem, `python3 --version` (3.14.x), `node --version` (v26), `psql --version` (18), `gs --version` (10.08.0), `jbig2 --version`, `tesseract --version`, `poetry --version`.

**Cenários de Aceitação**:

1. **Dado** acesso à internet, **Quando** construo a imagem, **Então** ela contém os pacotes apt listados, LibreOffice (writer, core, common, java-common), Java 17 headless, Tesseract com idioma `por`, cliente PostgreSQL 18, Ghostscript 10.08.0 compilado, jbig2enc 0.32, Node 26.x e Poetry configurado para **não** criar virtualenv.
2. **Dado** a imagem construída, **Quando** a marco com `docker tag building_foundation:0003 <repo>/building_foundation:0003` e envio com `docker push`, **Então** os `Dockerfile` de dev e prod podem referenciá-la.
3. **Dado** a imagem final, **Quando** inicio um contêiner sem comando, **Então** o comando padrão é `python3`.

---

### História de Usuário 6 - Frontend com HMR em contêiner próprio ou no host (Prioridade: P3)

O servidor Vite roda no serviço `front` (Node 26) com a pasta do projeto montada, ou diretamente no host via `./startfront-dev.sh`.

**Por que esta prioridade**: o Django já serve páginas; o Vite agrega HMR e é um complemento do fluxo principal (feature 007).

**Teste Independente**: abrir `http://localhost:5173/` e conferir que o Vite responde; ou executar `./startfront-dev.sh` no host.

**Cenários de Aceitação**:

1. **Dado** o ambiente no ar, **Quando** o contêiner `front` inicia, **Então** executa `/var/project/backend/startfront-dev.sh` (`npm install` seguido de `npm run dev`) como usuário não-root `backend` (uid/gid 1001) e publica a porta 5173.
2. **Dado** o host com Node 26, **Quando** executo `./startfront-dev.sh`, **Então** o mesmo par de comandos roda fora do Docker.

---

### História de Usuário 7 - Manutenção: atualizações automáticas de dependências e utilitários legados (Prioridade: P3)

O repositório configura o Dependabot (npm, pip, docker e docker-compose) e mantém utilitários auxiliares (`recreate_db.sh`, `libreoffice_entrypoint.sh`, `backend/.dockerignore`).

**Por que esta prioridade**: qualidade e manutenção contínuas; não afeta o funcionamento do ambiente.

**Teste Independente**: ler `.github/dependabot.yml` e verificar os ecossistemas e diretórios declarados; avaliar se o YAML é válido para o GitHub.

**Cenários de Aceitação**:

1. **Dado** `.github/dependabot.yml`, **Quando** o GitHub o processa, **Então** deveria haver atualizações semanais para `npm` (`/`), `pip` (`/`), `docker` (`/_docker/dev`, `/_docker/prod`) e `docker-compose` (`/_docker/dev`, `/_docker/prod`) — o arquivo atual repete a chave `updates:` (ver Casos de Borda e `research.md`).
2. **Dado** o script `recreate_db.sh`, **Quando** executado, **Então** tenta recriar um banco `sddstart` no contêiner `stormdb` (legado; não corresponde ao Compose atual).

---

### Casos de Borda

- **`SECRET_KEY` ausente**: `start-dev.sh` NÃO gera `SECRET_KEY` (diferente da produção). Sem a chave previamente em `backend/.env`, `manage.py migrate` falha (`decouple` levanta erro de configuração) e o `runserver` também; o contêiner fica em loop de reinício apenas se o processo terminar com código ≠ 0.
- **Arquivos `.env` são ignorados pelo Git** (`.gitignore`: `.env`); `_docker/dev/.env_dev_compose` NÃO é ignorado e é versionado (contém valores de exemplo de dev, inclusive senhas de desenvolvimento).
- **`backend/.env` ausente**: o script cria o arquivo (via `echo "" >>`) e acrescenta as chaves, mas sem `SECRET_KEY` o Django não inicia.
- **Ordem de inicialização**: `depends_on` apenas ordena o início dos contêineres; não há `healthcheck` em dev. Se o PostgreSQL ainda não aceita conexões quando `migrate` roda, a migração falha, o script não aborta (sem `set -e`) e o `runserver` sobe mesmo assim; basta reexecutar `uupdev.sh` ou reiniciar `appdev`.
- **Chave com regex por prefixo**: `^DEBUG.+$` também casaria uma linha `DEBUG_TOOLBAR_ACTIVE = ...` se ela estivesse descomentada (hoje está comentada com `#`), sobrescrevendo-a por `DEBUG = True`.
- **Chaves ausentes acrescentadas com barras escapadas**: os valores padrão de `DATABASE_URL_DEV` e `SOLR_URL` contêm `\/` (para o `sed`); quando a chave não existe e é anexada com `echo`, as barras invertidas são gravadas literalmente. Em `.env` que já têm as chaves isso não ocorre.
- **Valores com `|`, `&` ou `\`** (por exemplo, em senhas) quebram a substituição `sed` do `start-dev.sh`.
- **Arquivos pertencentes ao root**: o contêiner `appdev` roda como root e escreve no repositório montado (`backend/.env`, `logs/`, `__pycache__` desabilitado por `PYTHONDONTWRITEBYTECODE=1`); por isso `rdev.sh` e `ddev.sh` executam `sudo chown -R $USER:$GROUP .`. `uupdev.sh` NÃO faz o `chown`.
- **`logs/celery/*.pid` ausente**: o `rm` do início do bloco Celery emite erro inofensivo e o script continua.
- **Worker Celery não recarrega**: alterações em tarefas exigem reiniciar o contêiner `appdev` (o worker é um processo desacoplado do `runserver`).
- **Execução no host sem `DEBUG=True`**: a lógica de `localhost:5433`/Redis/Solr só vale com `DEBUG=True`; sem isso, `DATABASE_URL_PRD` é usado e os hosts não são trocados.
- **Solr no host sem credenciais na URL**: o código faz `SOLR_URL.split("@")[0] + "@localhost:8983"`; se a URL não tiver `@`, o resultado fica inválido (`http://hostx@localhost:8983`, sem credencial).
- **Várias instâncias**: apenas `APP_PORT` é variável; `5433`, `6379`, `8983`, `9983` e `5173` são fixos, então a segunda instância precisa de ajuste manual no `docker-compose.yaml`.
- **`SOLR_USER` não definido** no `.env_dev_compose`: o Compose usa `startdev1`; `SOLR_PASSWORD` vem do arquivo. `SOLR_DB` e `SITE_URL` do `.env_dev_compose` não são consumidos pelo `docker-compose.yaml` de dev.
- **`/mnt/volumes/backend_media`**: precisa existir (ou ser criado pelo Docker como root) no host; é o `bind mount` da mídia.
- **`.vscode/` é ignorado** pelo Git (configurações de depuração locais não são versionadas).
- **`libreoffice_entrypoint.sh`** não é copiado nem referenciado por nenhuma imagem (legado/morto).
- **`.dockerignore`** está em `backend/`, mas o contexto de build é a raiz do repositório; portanto não tem efeito.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**Imagem-base**

- **FR-001**: O repositório DEVE conter `_docker/foundation/Dockerfile` que constrói a imagem-base `building_foundation:0003` a partir de `python:3.14.10-bookworm`, com `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` e `HOME=/root`.
- **FR-002**: A imagem-base DEVE instalar os pacotes de sistema de compilação/mídia (incluindo `libpq-dev`, `build-essential`, `libleptonica-dev`, `poppler-utils`, `nginx`, `pngquant`, `graphviz`, `git`, `curl`, `jq`), o LibreOffice (writer/core/common/java-common, `hyphen-pt-br` e fontes), `openjdk-17-jdk-headless` e `tesseract-ocr` com `tesseract-ocr-por`, limpando o cache do APT.
- **FR-003**: A imagem-base DEVE instalar `postgresql-client-18` a partir do repositório PGDG (`bookworm-pgdg`), compatível com o servidor PostgreSQL 18 dos Compose.
- **FR-004**: A imagem-base DEVE compilar o Ghostscript 10.08.0 e o jbig2enc 0.32 a partir do código-fonte, removendo os diretórios de compilação na mesma camada.
- **FR-005**: A imagem-base DEVE instalar Node.js 26.x (repositório NodeSource) e o Poetry, com `POETRY_VIRTUALENVS_CREATE=false`, e DEVE remover as configurações padrão do Nginx (`/etc/nginx/conf.d/*` e `sites-enabled/*`).
- **FR-006**: O `Dockerfile` da imagem-base DEVE documentar, ao final, os comandos de `docker build`, `docker login`, `docker tag` e `docker push` e terminar com `CMD ["python3"]`.

**Compose e imagens de desenvolvimento**

- **FR-007**: `_docker/dev/docker-compose.yaml` DEVE definir os serviços `redis`, `solr`, `front`, `db` e `appdev`, a rede `appdev-net` (bridge) e os volumes nomeados `solr9_data`, `solr9_configsets`, `redis_data` e `dbdata`.
- **FR-008**: Todo `container_name` DEVE ser `${COMPOSE_PROJECT_NAME:-startdev1}-<serviço>` (`redis`, `solr`, `front`, `db`, `appdev`).
- **FR-009**: O serviço `db` DEVE usar `pgvector/pgvector:0.8.7-pg18-bookworm`, receber `POSTGRES_PASSWORD`, `POSTGRES_USER` e `POSTGRES_DB` (padrão `startdev1`) e publicar `5433:5432`.
- **FR-010**: O serviço `redis` DEVE usar `redis:bookworm` e publicar `6379:6379`; o serviço `solr` DEVE usar `solr:9.7` com `command: bin/solr start -c -f` e publicar `8983:8983` e `9983:9983`.
- **FR-011**: O serviço `appdev` DEVE ser construído com `_docker/dev/Dockerfile.Dev` (contexto na raiz do repositório), montar `../../.` em `/var/project/backend` e `/mnt/volumes/backend_media` em `/var/project/backend_media`, publicar `${APP_PORT:-9099}:9000`, depender de `front`, `db`, `redis` e `solr` e receber `DEBUG='True'`, `USE_SOLR='True'`, `SOLR_COLLECTIONS`, `SOLR_URL`, `IS_ZK_EMBEDDED='True'`, `TZ=America/Sao_Paulo`, `COMPOSE_PROJECT_NAME` e as variáveis `POSTGRES_*`.
- **FR-012**: O serviço `front` DEVE ser construído com `_docker/dev/Dockerfile.Dev.Front`, montar o projeto em `/var/project/backend` e publicar `5173:5173`.
- **FR-013**: Todos os serviços de infraestrutura e aplicação DEVEM usar `restart: on-failure` e a rede `appdev-net`.
- **FR-014**: `_docker/dev/.env_dev_compose` DEVE fornecer ao Compose `APP_PORT` (padrão do repositório `9099`), `POSTGRES_PASSWORD`, `POSTGRES_USER`, `POSTGRES_DB`, `SOLR_PASSWORD`, `SOLR_DB` e `SITE_URL`.
- **FR-015**: `Dockerfile.Dev` DEVE partir de `leandrojatai/building_foundation:0003`, definir `ROOT_HOME=/var/project` e `HOME=${ROOT_HOME}/backend`, criar `${HOME}/logs/celery`, `${ROOT_HOME}/backend_dev` e `${ROOT_HOME}/backend_media`, copiar `py*` (resulta apenas em `pyproject.toml`) para `${ROOT_HOME}/backend_dev/pyproject.toml`, instalar as dependências com `poetry install --no-root -C ${ROOT_HOME}/backend_dev/`, expor 9000 e ter por comando `/var/project/backend/_docker/dev/start-dev.sh`.
- **FR-016**: `Dockerfile.Dev.Front` DEVE partir de `node:26.13.0-bookworm`, criar o grupo e o usuário `backend` (uid/gid 1001) com home `/var/project/backend`, executar como esse usuário, expor 5173 e ter por comando `/var/project/backend/startfront-dev.sh`.

**Bootstrap (`start-dev.sh`)**

- **FR-017**: `start-dev.sh` DEVE, antes de tudo, executar a função `change_env_file` que, para cada uma das chaves `DATABASE_URL_DEV`, `SOLR_COLLECTIONS`, `SOLR_URL`, `DEBUG`, `DJANGO_VITE_DEV_MODE`, `REDIS_HOST`, `FOLDER_DEBUG_CONTAINER`, `COMPOSE_PROJECT_NAME` e `TZ`, substitui a linha existente em `backend/.env` (formato `CHAVE = valor`) por regex ou, se a chave não existir, a acrescenta ao final; valores vêm das variáveis de ambiente do contêiner ou, na ausência, dos padrões derivados de `COMPOSE_PROJECT_NAME`.
- **FR-018**: O script NÃO DEVE gerar `SECRET_KEY`; o `backend/.env` de desenvolvimento DEVE conter `SECRET_KEY` previamente.
- **FR-019**: O script DEVE executar `yes yes | python3 manage.py migrate` e, em seguida, o bloco Solr: se `USE_SOLR` for `True`/`true`, aguardar o Solr com `_docker/prod/wait-for-solr.sh` (até 60 tentativas) e, ao responder, executar `python3 _docker/prod/solr_cli.py` com URL, coleções, shards (`NUM_SHARDS`=1), fator de replicação (`RF`=1), máximo de shards por nó (`MAX_SHARDS_PER_NODE`=1) e `--embedded_zk` quando `IS_ZK_EMBEDDED` for verdadeiro; caso contrário, registrar "Solr support is not initialized.".
- **FR-020**: O script DEVE remover `${HOME}/logs/celery/*.pid`, iniciar `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1` com `--hostname=${COMPOSE_PROJECT_NAME}-redis`, `--pidfile=./logs/celery/%n.pid` e `--logfile=./logs/celery/%n%I.log`, aguardar 3 s e executar `yes yes | python3 manage.py runserver 0.0.0.0:9000` como processo principal.

**Scripts de raiz**

- **FR-021**: `rdev.sh [nome]` DEVE executar `docker compose -p <nome> ... down`, depois `chown -R <usuário>:<usuário> .` e, por fim, `up --build -d`; `uupdev.sh [nome]` DEVE executar somente `up --build -d` com `--progress=plain`; `ddev.sh [nome]` DEVE executar `down` seguido do `chown`. Todos usam `sudo docker compose -p <nome> --env-file _docker/dev/.env_dev_compose -f _docker/dev/docker-compose.yaml` e o nome padrão `startdev1`.
- **FR-022**: `startfront-dev.sh` DEVE executar `npm install` e `npm run dev`.
- **FR-023**: `recreate_db.sh` (legado) DEVE ser mantido documentado como utilitário que encerra conexões, remove e recria o banco `sddstart` no contêiner `stormdb`; NÃO corresponde ao Compose atual (`<projeto>-db`, banco `startdev1`).

**Execução em contêiner × host (settings)**

- **FR-024**: `backend/settings/zenv.py` DEVE expor `FOLDER_DEBUG_CONTAINER` (lido da variável de mesmo nome; padrão `__file__`) e `PROJECT_DIR`; `backend/settings/project.py` DEVE calcular `DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)`.
- **FR-025**: Com `DEBUG=True` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR` (execução no host), o sistema DEVE usar `HOST=localhost` e `PORT=5433` no banco (`DATABASES["default"]`), `REDIS_HOST="localhost"` e o host `localhost:8983` na `SOLR_URL` (preservando `usuário:senha@`).
- **FR-026**: O banco DEVE ser configurado por `DATABASE_URL_DEV` quando `DEBUG` for verdadeiro e por `DATABASE_URL_PRD` caso contrário.
- **FR-027**: A mídia DEVE usar `PROJECT_DIR.parent/backend_media/{media,media_cache}` e, com `DEBUG=True` fora de `/var/project`, `/mnt/volumes/backend_media/{media,media_cache}`.

**Manutenção**

- **FR-028**: `.github/dependabot.yml` DEVERIA declarar atualizações semanais de `npm` (`/`), `docker` (`/_docker/dev`, `/_docker/prod`), `docker-compose` (`/_docker/dev`, `/_docker/prod`) e `pip` (`/`) em **uma única** lista `updates:`; o arquivo atual repete a chave por bloco (defeito conhecido, replicado por fidelidade).
- **FR-029**: `backend/.dockerignore` DEVE listar `media`, `collected_static`, `.git`, `.gitignore`, `whoosh`, `bower`, `*.log`, `~*`, `*.pyc`, `.cache`, `.project`, `.env`, `.idea`.
- **FR-030**: `libreoffice_entrypoint.sh` DEVE existir como wrapper do `libreoffice` em modo headless (`--nologo --norestore --invisible --nolockcheck --nodefault --headless "$@"`) que remove `/tmp/hsperfdata_root` ao final; NÃO é usado pelas imagens atuais.
- **FR-031**: `.vscode/` DEVE permanecer ignorado pelo Git.

### Entidades-Chave

- **Projeto Compose (instância)**: identificado por `COMPOSE_PROJECT_NAME` (padrão `startdev1`); prefixa contêineres, hosts de rede, volumes e coleções Solr.
- **Imagem-base `building_foundation:0003`**: pré-requisito de runtime/ferramentas compartilhado por dev e prod.
- **Serviços**: `redis`, `solr`, `front`, `db`, `appdev`.
- **Rede `appdev-net`** e **volumes** `solr9_data`, `solr9_configsets`, `redis_data`, `dbdata`, mais o *bind mount* `/mnt/volumes/backend_media`.
- **`backend/.env` (dev)**: arquivo local, ignorado pelo Git, que reúne a configuração lida por `python-decouple`.
- **`.env_dev_compose`**: valores de interpolação do Compose.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Em um clone limpo com a imagem-base disponível e `backend/.env` contendo apenas `SECRET_KEY`, um único `./rdev.sh` resulta em cinco contêineres em execução e `http://localhost:9099/` respondendo, sem nenhuma outra edição manual.
- **SC-002**: Após o primeiro start, `backend/.env` contém exatamente uma linha para cada uma das nove chaves gerenciadas por `start-dev.sh` (sem duplicatas) e reexecuções do script são idempotentes.
- **SC-003**: `python manage.py showmigrations` no contêiner `appdev` não lista migrações pendentes após o start.
- **SC-004**: Executando `./rdev.sh startdev2` (com portas fixas ajustadas), os contêineres `startdev2-*` coexistem com `startdev1-*` e cada um enxerga apenas seus próprios banco, Redis e coleções Solr.
- **SC-005**: Com o ambiente no ar, `python manage.py runserver` no host conecta ao PostgreSQL em `localhost:5433` sem alterar o `backend/.env`.
- **SC-006**: A imagem-base construída reporta Python 3.14.x, Node v26.x, `psql` 18, Ghostscript 10.08.0 e Tesseract com o idioma `por`.
- **SC-007**: Uma alteração em arquivo Python/JS montado é refletida no navegador em segundos sem reconstruir imagens.
- **SC-008**: `./ddev.sh` remove os cinco contêineres e deixa os arquivos do repositório pertencentes ao usuário atual.

## Premissas

- Docker Engine com o plugin Compose v2 e permissão `sudo` estão disponíveis; os scripts usam `sudo docker compose`.
- A imagem `leandrojatai/building_foundation:0003` está acessível no registro ou foi construída/tagueada localmente com esse nome (o `FROM` do `Dockerfile.Dev` usa o prefixo `leandrojatai/`).
- O `backend/.env` de dev é criado manualmente com `SECRET_KEY`; `.env` NÃO é versionado (princípio II).
- A senha do Solr (`SOLR_PASSWORD`) e demais valores de `.env_dev_compose` são apenas padrões de desenvolvimento; a configuração de autenticação do Solr e as coleções são tratadas na feature `008-busca-solr-haystack`.
- O diretório `/mnt/volumes/backend_media` existe (ou será criado pelo Docker) no host.
- O host de desenvolvimento é Linux; scripts em Bash.
- Dependências Python do contêiner são resolvidas a partir de `pyproject.toml` sem `poetry.lock` (ver `research.md`).
- A parte de produção (`_docker/prod`, `dprod.sh`, `upprod.sh`) é escopo da feature `011-docker-producao`.
