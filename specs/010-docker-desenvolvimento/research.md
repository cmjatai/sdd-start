# Pesquisa e Decisões Técnicas: Ambiente Docker de Desenvolvimento

**Funcionalidade**: `010-docker-desenvolvimento` | **Data**: 2026-11-08

## Decisões

### D1 — Imagem-base única e pesada (`building_foundation:0003`)

- **Decisão**: concentrar Python 3.14, LibreOffice, Java, Tesseract, PostgreSQL 18 client, Ghostscript 10.08.0, jbig2enc 0.32, Node 26 e Poetry em uma imagem-base versionada por sufixo numérico (`0003`), publicada em `leandrojatai/building_foundation:0003` e usada como `FROM` em dev (`Dockerfile.Dev`) e prod (`_docker/prod/Dockerfile`).
- **Justificativa**: compilar Ghostscript/jbig2enc e instalar LibreOffice leva muito tempo; separar a base reduz drasticamente o tempo de build das imagens de aplicação e garante paridade dev × prod (constituição, princípio III). Compilação e limpeza na mesma camada evitam carregar o código-fonte na imagem final.
- **Alternativas**: instalar tudo em cada imagem (lento e redundante); usar pacotes apt do Ghostscript (versão mais antiga, sem controle da versão); *multi-stage build* (descartado por praticidade de publicar a base).

### D2 — Código por *bind mount* e dependências embutidas na imagem

- **Decisão**: `appdev` e `front` montam a raiz do repositório em `/var/project/backend`; a imagem só carrega as dependências Python (instaladas a partir de `pyproject.toml` copiado para `/var/project/backend_dev`).
- **Justificativa**: edição ao vivo com recarregamento do `runserver` e HMR do Vite sem reconstruir imagens. Instalar a partir de um diretório separado (`backend_dev`) evita que o *bind mount* oculte o `pyproject.toml` usado no build e permite cache de camada.
- **Alternativas**: `COPY` do código (exige rebuild a cada alteração); virtualenv no volume (mais lento, mistura host × contêiner).

### D3 — Poetry sem virtualenv

- **Decisão**: `POETRY_VIRTUALENVS_CREATE=false` na base e `poetry install --no-root -C <dir>` na imagem de dev.
- **Justificativa**: em contêiner o isolamento já existe; as dependências ficam no Python do sistema, acessíveis por `python3 manage.py` e `celery` sem ativar ambiente.

### D4 — Instâncias múltiplas via `COMPOSE_PROJECT_NAME` e nomes de contêiner previsíveis

- **Decisão**: `-p <nome>` nos scripts; `container_name: ${COMPOSE_PROJECT_NAME:-startdev1}-<serviço>`; hosts de rede, `DATABASE_URL_DEV`, `REDIS_HOST`, `SOLR_URL` e coleções derivam do nome.
- **Justificativa**: o nome do contêiner serve como hostname DNS na rede do Compose; `start-dev.sh` grava esses hosts no `backend/.env`, mantendo a configuração coerente com o projeto escolhido.
- **Alternativas**: usar nomes de serviço (`db`, `redis`) como host — colidiriam em redes compartilhadas e não carregariam o nome da instância nas coleções Solr.

### D5 — Mesmo `backend/.env` serve ao contêiner e ao host

- **Decisão**: a distinção é feita em tempo de execução comparando `FOLDER_DEBUG_CONTAINER` (gravado como `/var/project/backend`) com `PROJECT_DIR` real; se diferirem e `DEBUG=True`, o Django usa `localhost` + portas publicadas (banco 5433; Redis 6379; Solr 8983).
- **Justificativa**: permite depurar no host (VS Code, `debug_toolbar`, notebooks) sem editar o `.env`. É por isso que Redis, Solr e PostgreSQL têm portas publicadas em dev (e não em prod, onde estão comentadas).
- **Alternativas**: dois arquivos `.env`; variável explícita `RUNNING_ON_HOST`.

### D6 — `.env` reescrito por `sed` + `declare -A` em vez de *templating*

- **Decisão**: `change_env_file` usa regex por chave e acrescenta chaves faltantes.
- **Justificativa**: preserva as demais linhas do `.env` (segredos, comentários) e é idempotente; evita dependência de `envsubst`/Python.

### D7 — Solr em dev com autenticação na URL e SolrCloud embutido

- **Decisão**: `solr:9.7`, `bin/solr start -c -f`; URL `http://usuário:senha@<p>-solr:8983`; `IS_ZK_EMBEDDED=True`; portas 8983 e 9983 publicadas.
- **Justificativa**: paridade com produção (SolrCloud com ZooKeeper embutido). Detalhes de coleções e segurança na feature `008-busca-solr-haystack`.

### D8 — Celery em modo `multi` com um worker

- **Decisão**: `celery multi start 1 ... -Q:1 celery -c:1 1`, desacoplado (daemon) antes do `runserver`.
- **Justificativa**: simplicidade em dev; a linha comentada com 16 workers documenta a topologia de produção usada no projeto de origem (filas `cq_arq`, `cq_core`, `cq_videos`, `cq_base`, `celery`).

### D9 — Usuário do `front` com uid 1001

- **Decisão**: usuário `backend` (uid/gid 1001) no `Dockerfile.Dev.Front`.
- **Justificativa**: `npm install` não roda como root e grava `node_modules` na pasta montada com dono compatível com o primeiro usuário comum do host (uid 1000/1001 típico); `rdev.sh` corrige dono ao final com `chown`.

## Particularidades, dívidas técnicas e riscos observados

Legenda da recomendação: **Replicar** = manter como está; **Corrigir** = a reconstrução idealmente deve corrigir. **O estado atual é replicar, para fidelidade ao código existente.**

| # | Observação (confirmada no código) | Risco | Recomendação |
|---|---|---|---|
| 1 | `start-dev.sh` NÃO gera `SECRET_KEY`; `backend/.env` (ignorado pelo Git) precisa tê-la antes. A produção, ao contrário, gera (`011`). | Falha de primeira execução para quem esquece; `settings.project` faz `config("SECRET_KEY")` sem *default*. | Replicar (documentado no README). Opcionalmente **corrigir** gerando a chave se ausente em dev. |
| 2 | `change_env_file` usa `sed -E "s\|regex\|valor\|g"` por chave; chaves ausentes são anexadas. O delimitador `\|` e os caracteres `&`/`\` em valores (ex.: senhas) quebram a substituição. | Corrupção do `.env` com senhas especiais. | Replicar; **corrigir** escapando valores ou usando outro mecanismo. |
| 3 | A regex `^DEBUG.+$` (e a verificação `grep "^DEBUG"`) casa por prefixo: uma linha `DEBUG_TOOLBAR_ACTIVE = …` descomentada seria sobrescrita por `DEBUG = True`. Atualmente está comentada. | Sobrescrita silenciosa de outras chaves iniciadas por `DEBUG`, `TZ`, `SOLR_URL`… | **Corrigir** ancorando com `^DEBUG[[:space:]]*=`. |
| 3b | Padrões de `DATABASE_URL_DEV` e `SOLR_URL` têm `\/` (escape para o `sed`); quando a chave é **anexada** (ausente), as barras invertidas vão literais ao arquivo. A variável consultada é `DATABASE_URL` (não `DATABASE_URL_DEV`). | URL inválida em `.env` sem a chave. | **Corrigir**. |
| 4 | `yes yes \| python3 manage.py migrate` confirma automaticamente qualquer pergunta (ex.: remover *content types* obsoletos). | Pode aceitar ações destrutivas sem revisão. | Replicar em dev; **corrigir** com `migrate --noinput` explícito. |
| 5 | Sem `set -e`, sem *healthcheck* e sem espera pelo PostgreSQL (existe `_docker/prod/wait-for-pg.sh`, não usado em dev). `depends_on` só ordena a criação. | Corrida na primeira subida: `migrate` pode falhar e `runserver` sobe mesmo assim. | Replicar; **corrigir** com *healthcheck* + `depends_on: condition: service_healthy` ou `wait-for-pg.sh`. |
| 6 | `rm ${HOME}/logs/celery/*.pid` e `celery multi start 1 … --hostname=${COMPOSE_PROJECT_NAME}-redis`: hostname do worker usa o sufixo `-redis` (nome herdado). Um worker, fila `celery`, concorrência 1. `logs/celery/` está no repositório montado. | Tarefas em outras filas (`cq_*`) não seriam consumidas em dev; hostname enganoso. | Replicar. |
| 7 | `wait-for-solr.sh` retorna `1` quando o Solr responde (sucesso) e `2` na falha; `start-dev.sh` testa `== 1`. | Convenção invertida, confusa. | Replicar (a lógica de `start.sh` de produção depende dela). |
| 8 | `recreate_db.sh` referencia contêiner `stormdb` e banco/usuário `sddstart`, sem bit de execução; não corresponde ao Compose atual (`<projeto>-db`, banco `startdev1`). O `DATABASE_URL_PRD` do `.env` de exemplo também cita `sddstart`. | Utilitário inoperante/legado. | **Corrigir** (parametrizar pelo projeto) ou remover; hoje replicar. |
| 9 | `.github/dependabot.yml` repete a chave `updates:` seis vezes. Em YAML, chaves duplicadas em um mapeamento são inválidas/ambíguas; os *parsers* comuns mantêm só a última (`pip`) ou rejeitam o arquivo, de modo que `npm`, `docker` e `docker-compose` podem não ser atualizados. Também não cobre `_docker/foundation`. | Atualizações automáticas ineficazes. | **Corrigir**: uma única lista `updates:` com seis itens (+ `docker` em `/_docker/foundation`). Replicar hoje. |
| 10 | `Dockerfile.Dev`: `COPY py*` casa somente `pyproject.toml` (`poetry.lock` começa com `po`); a linha `#COPY po*…` está comentada. Logo `poetry install` resolve dependências sem *lock* na imagem. | Builds não reprodutíveis, lentos; versões podem divergir do `poetry.lock` do repositório. | **Corrigir**: copiar também `poetry.lock`. Replicar hoje. |
| 11 | `backend/.dockerignore` fica em `backend/`, mas o `context` do Compose é a raiz; o Docker só lê `.dockerignore` na raiz do contexto. Não existe `.dockerignore` na raiz. Cita `whoosh`, `bower` (legado). | Sem efeito; todo o repositório (incl. `node_modules`, `.git`, `backend/.env`) é enviado ao *daemon* no build. | **Corrigir** movendo para a raiz e atualizando a lista. |
| 12 | `libreoffice_entrypoint.sh` não é copiado nem referenciado por nenhuma imagem e não é executável. | Código morto. | Replicar (ou remover). |
| 13 | `DEBUG_RUNNING_CONTAINER` é calculado em `project.py`, mas não é usado em lugar algum. | Código morto. | Replicar. |
| 14 | Em `Dockerfile.Dev` o `FROM` usa `leandrojatai/building_foundation:0003` (registro do autor); o comentário do foundation usa tag local `building_foundation:0003`. Quem reconstruir a base localmente precisa criar também a tag com o prefixo. | Confusão ao construir offline/derivar. | Replicar; documentar. |
| 15 | Portas fixas (`5433`, `6379`, `8983`, `9983`, `5173`) no Compose; só `APP_PORT` é variável; `SITE_URL` e `SOLR_DB` de `.env_dev_compose` não são usados. | Conflito ao subir 2 instâncias sem editar o YAML (README orienta ajuste manual). | **Corrigir** parametrizando portas. |
| 16 | Segredos de dev: `.env_dev_compose` é versionado com `POSTGRES_PASSWORD` e `SOLR_PASSWORD`; defaults `startdev1` no Compose e no `solr.py`; Redis e PostgreSQL publicados em todas as interfaces do host (`0.0.0.0`). | Exposição na rede local/firewall em máquinas compartilhadas. | Aceitável em dev; **corrigir** publicando em `127.0.0.1` se necessário. Nunca reutilizar em produção. |
| 17 | O contêiner `appdev` roda como **root** e escreve em arquivos do repositório montado; por isso `rdev.sh`/`ddev.sh` fazem `sudo chown -R usuário:usuário .`. `uupdev.sh` não faz. Os três scripts usam `sudo`. | Arquivos root no repositório; `chown -R .` percorre `node_modules` (lento). | Replicar. |
| 18 | `Dockerfile.Dev.Front` usa `node:26.13.0-bookworm` enquanto a base usa NodeSource `setup_26.x` (versão flutuante); `pip3 install poetry` e `pip install --upgrade pip setuptools` não têm versão fixa. | Builds da base não determinísticos. | **Corrigir** fixando versões; replicar hoje. |
| 19 | `solr:9.7` fixo, com comentário "validar mudança para 9.8 pois está causando erro"; `pgvector:0.8.7-pg18-bookworm` fixo. | Atualizações exigem validação. | Replicar. |
| 20 | `/mnt/volumes/backend_media` é caminho absoluto do host (hard-coded no Compose e em `medias.py` para execução no host). | Exige criar/permitir o diretório; não portátil para Windows/macOS. | Replicar; documentar. |
| 21 | Execução no host: `SOLR_URL.split("@")[0] + "@localhost:8983"` pressupõe credenciais; `DATABASES[...]["PORT"]=5433` é fixo (não segue a porta publicada se mudada); Redis mantém `REDIS_PORT`. | Quebra em URL sem `@` ou com porta personalizada. | Replicar. |
| 22 | `.vscode/` ignorado: configurações de *launch* (depuração no host) não são versionadas. | Cada dev recria as suas. | Replicar. |
| 23 | Mensagens e comentários do `start-dev.sh` misturam inglês e português; `SOLR_URL` padrão do script cita `startdev1:startdev1` (credencial de exemplo). | Cosmético. | Replicar. |
| 24 | O bloco `change_env_file` de `_docker/prod/start.sh` é uma variante do mesmo algoritmo (outro arquivo `backend_data/.env`, `DATABASE_URL_PRD`, `SITE_URL`, geração de `SECRET_KEY`); manter em sincronia (feature 011). | Divergência futura. | Replicar. |
