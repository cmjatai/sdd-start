# Pesquisa e Decisões Técnicas: Docker para Produção

## Decisões

### D1. Um único contêiner de aplicação com Nginx + Gunicorn + Daphne + Celery
- **Decisão**: `app` roda todos os processos (orquestrados por `start.sh`), com o Nginx em primeiro plano.
- **Justificativa**: simplicidade ("um comando por ambiente"), comunicação por sockets unix no mesmo sistema de arquivos, mesmas dependências para WSGI/ASGI/Celery.
- **Alternativas**: um contêiner por processo (isolamento e healthchecks por processo, mais Compose); supervisord/s6 (reinício automático de processos).

### D2. Dois servidores de aplicação: Gunicorn (WSGI) e Daphne (ASGI)
- **Decisão**: HTTP comum no Gunicorn (9 workers) e somente `/ws/` no Daphne.
- **Justificativa**: Gunicorn síncrono é maduro para HTTP; Channels exige ASGI para WebSocket (feature 006).
- **Alternativas**: Daphne/Uvicorn para tudo; Gunicorn com worker Uvicorn.

### D3. Sockets unix entre Nginx e aplicação
- **Decisão**: `/var/project/backend/run/gunicorn.sock` e `daphne.sock`.
- **Justificativa**: evita portas TCP internas e sobrecarga de rede local. **Alternativa**: portas TCP locais.

### D4. Estáticos coletados na build, servidos pelo Nginx
- **Decisão**: `collectstatic --no-default-ignore` no build; `--no-default-ignore` é necessário para copiar `frontend/.vite/manifest.json` (diretório iniciado por ponto, ignorado por padrão).
- **Justificativa**: imagem imutável; Nginx serve com `gzip_static` e `expires 7d`; o manifesto do Vite fica em `STATIC_ROOT` (`frontend.py`).
- **Alternativas**: WhiteNoise; volume compartilhado preenchido no start.

### D5. `backend.settings.fake` (SQLite) para o `collectstatic` do build
- **Decisão**: módulo de settings que reutiliza `project.py` e troca somente `DATABASES`, `DEBUG` e o caminho do manifesto Vite para `DJANGO_VITE_ASSETS_PATH`.
- **Justificativa**: durante o build não existe PostgreSQL; o manifesto ainda não está em `collectedstatic`.
- **Alternativas**: subir banco no build (complexo); `STATIC_ROOT` pré-gerado no host.

### D6. Detecção de produção pela existência de `backend_data/.env`
- **Decisão**: `zenv.py` verifica `Path(__file__).parents[3] / "backend_data" / ".env"`; se existir, o `decouple` usa essa pasta como `search_path`; senão procura `.env` a partir da pasta do módulo para cima (desenvolvimento e build).
- **Justificativa**: o `.env` de produção fica em volume, fora da imagem e da árvore do código, e sobrevive a reconstruções.
- **Alternativas**: variável `ENV=production`; só variáveis de ambiente (sem arquivo).

### D7. `SECRET_KEY` gerada no primeiro start e persistida
- **Decisão**: `genkey.py` + `backend_data/secret.key`; `start.sh` reescreve `SECRET_KEY` no `.env` a cada start.
- **Justificativa**: nenhum segredo no repositório (constituição, Princípio II) e chave estável entre reinícios.
- **Alternativas**: Docker secrets; variável de ambiente fornecida pelo operador.

### D8. `.env` ajustado por `sed`/regex a partir das variáveis do Compose
- **Decisão**: cada chave é substituída por regex `^CHAVE.+$` ou acrescentada se ausente; valores padrão com `${VAR:=padrão}`.
- **Justificativa**: o Django lê tudo de um arquivo (mesma mecânica do desenvolvimento, `start-dev.sh`), permitindo que processos iniciados fora do `start.sh` (ex.: `docker exec`) leiam a mesma configuração.
- **Alternativas**: usar somente variáveis de ambiente do contêiner.

### D9. Compose: dependências com condição apenas para Redis
- **Decisão**: `redis` com healthcheck e `service_healthy`; `db` e `solr` só `service_started`.
- **Justificativa**: o Solr é aguardado pelo `wait-for-solr.sh`; o banco não tem healthcheck (ver R3).

### D10. Imagem-base compartilhada com o desenvolvimento
- **Decisão**: `leandrojatai/building_foundation:0003` (feature 010) com Python, Poetry, Node, Nginx e utilitários.
- **Justificativa**: paridade dev/prod e build mais rápido. **Alternativa**: imagem multi-stage mais enxuta.

### D11. Múltiplas instâncias por `COMPOSE_PROJECT_NAME`
- **Decisão**: nomes de contêiner, hosts (`<nome>-db`, `<nome>-redis`, `<nome>-solr`) e coleções Solr derivam do nome do projeto; porta pública por `APP_PORT`.
- **Justificativa**: constituição, Princípio III.

### D12. Portas auxiliares não publicadas
- **Decisão**: `ports` de Redis/Solr/PostgreSQL comentados; só `APP_PORT:80` é publicada.
- **Justificativa**: superfície de ataque mínima; serviços acessíveis só pela rede `app-net`.

## Particularidades, dívidas técnicas e riscos observados

> Recomendação geral: o estado atual é **replicar** para fidelidade; a coluna "Recomendação" indica o que deve ser corrigido numa evolução.

| # | Observação (confirmada no código) | Risco / efeito | Recomendação |
|---|---|---|---|
| R1 | `.env_prod_compose` traz `POSTGRES_*`, `SOLR_PASSWORD`, `SOLR_DB` = `startprod1` e o comentário "customizar para produção!" | Senhas de exemplo públicas; se não trocadas, produção fica insegura. `SOLR_DB` não é usado; `SOLR_USER` (usado no `SOLR_URL` do Compose) não está no arquivo e cai em `startprod1` | Replicar; **corrigir** exigindo valores (`${VAR:?}`) ou gerando senhas |
| R2 | `SITE_URL` padrão `http://192.168.15.9:9001` em `project.py` e em `.env_prod_compose` (IP de rede local do autor) | Em outro ambiente, CSRF aceita só essa origem e links absolutos saem errados se não for ajustada | Replicar; **corrigir** com padrão neutro (`http://localhost:9001`) e exigência em produção |
| R3 | `wait-for-pg.sh` comentado em `start.sh`; filtra por `grep backend`; `depends_on` de `db` é `service_started` (sem healthcheck no `db`) | `migrate` pode falhar se o PostgreSQL ainda não aceita conexões; o script segue adiante mesmo assim (sem `set -e`). O filtro `grep backend` só funcionaria se o banco se chamasse algo com "backend" (resquício do projeto original; o comentário cita `backenddb`) | **Corrigir**: healthcheck `pg_isready` no `db` com `service_healthy`, ou reativar espera com filtro pelo `POSTGRES_DB` |
| R4 | `X-Forwarded-Proto https` fixo em `@proxy_to_ws`, `@proxy_to_app`, `@proxy_to_app_api` | Se o acesso é HTTP puro, o Django é informado de HTTPS (só tem efeito se `SECURE_PROXY_SSL_HEADER` estiver definido — não está no código). Também não há `X-Forwarded-Host` nos proxies HTTP (só no WebSocket) | Replicar; **corrigir** repassando `$scheme` ou documentando o TLS externo |
| R5 | `nginx_docker.conf`: `user nginx root`, `server_tokens off`, gzip, `keepalive_timeout 300`, `sendfile off`, 1 worker | `keepalive 300` mantém conexões ociosas por 5 min; `sendfile off` reduz desempenho de estáticos; 1 worker limita concorrência. Como o contêiner roda como `root`, o aviso de `user` é inócuo | Replicar; avaliar `worker_processes auto` e `sendfile on` |
| R6 | CORS `*` com `Access-Control-Allow-Credentials: true` nas rotas `/api` (e no preflight só `Allow-Origin *`) | Combinação `*` + credenciais é rejeitada por navegadores, mas expõe a API a qualquer origem em requisições sem credenciais; `try_files $uri @proxy_to_app_api` aplica o CORS também nas respostas de erro | Replicar (esqueleto aberto); **corrigir** restringindo à origem de `SITE_URL` (constituição, "Segurança") |
| R7 | `SECRET_KEY` em arquivo texto (`backend_data/secret.key`) no volume `data` e também em `.env` | Qualquer acesso ao volume expõe a chave; `echo $KEY` sem aspas pode sofrer *glob* por causa do `*` (presente no alfabeto) em casos raros | Replicar; **corrigir** com `printf '%s' "$KEY"`, permissões 600 e/ou Docker secrets |
| R8 | `SESSIONS_COOKIE_SECURE = not DEBUG` em `project.py` | Nome incorreto (o Django usa `SESSION_COOKIE_SECURE`): cookie de sessão não recebe `Secure` e `CSRF_COOKIE_SECURE` também não é definido | Replicar; **corrigir** para `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` (atenção: só funciona com HTTPS) |
| R9 | `package-lock.json` comentado no Dockerfile (`#COPY package-lock.json`) e `COPY py*` só copia `pyproject.toml` (não `poetry.lock`) | Builds não reprodutíveis: dependências npm e Python são resolvidas no momento do build (inclusive o `celery-haystack` do Git) | **Corrigir**: copiar `poetry.lock` e `package-lock.json` e usar `npm ci` |
| R10 | Celery inicia com `--hostname=backendredis`, 1 worker, 1 processo (`-c:1 1`), fila `celery`; linha comentada de 16 workers com filas `cq_*` | Nome de nó fixo "backendredis" (resquício do projeto original); só a fila padrão é consumida; `celery multi` em segundo plano sem supervisão | Replicar; parametrizar o nome por `COMPOSE_PROJECT_NAME` |
| R11 | Ordem: migrate → solr → `sleep 3` → celery → `sleep 3` → gunicorn → `sleep 3` → daphne → `sleep 5` → nginx | Sleeps fixos em vez de verificação de prontidão; Nginx pode subir antes de os sockets existirem (gera 502 transitório) | Replicar; **corrigir** com esperas pelos sockets |
| R12 | `dprod.sh` executa `sudo chown -R $USER:$GROUP .` no diretório corrente após o `down` | Altera a propriedade de **todo** o diretório onde o script for chamado; só é seguro na raiz do repositório. `upprod.sh` não tem `chown` | Replicar; **corrigir** limitando o `chown` aos artefatos necessários |
| R13 | Portas 6379/8983/5433 comentadas em produção | Positivo: não expostas. Ressalva: depuração exige `docker exec` | Replicar |
| R14 | `user: "root:root"` no Compose anula o `USER nginx` do Dockerfile; Celery, Gunicorn (`--user root`), Daphne e Nginx rodam como root | Superfície maior em caso de comprometimento; o usuário `nginx` criado no Dockerfile fica efetivamente só como grupo/usuário dos workers do Nginx (`user nginx root`) | Replicar; **corrigir** executando como usuário sem privilégio e ajustando permissões dos volumes |
| R15 | `wait-for-solr.sh` (feature 008): sai com `1` em sucesso e `2` em falha; usa `[[ $RETRY_COUNT < $RETRY_LIMIT ]]` (comparação lexicográfica de textos: com limite "60" o laço executa apenas 7 tentativas, verificado em bash) e `start.sh` compara `== 1` para "conectar" | Semântica invertida, mas coerente entre os dois; a janela efetiva de espera é ≈ 7 tentativas (~7 s), não 60 s; se o Solr demorar, as coleções não são criadas | Replicar; **corrigir** com `-lt` e códigos convencionais |
| R16 | O regex `^DEBUG.+$` também casa `DEBUG_TOOLBAR_ACTIVE...` no `.env`; o `sed -i` do `SECRET_KEY` substitui a linha por linha em branco; valores com `|`, `&` ou `\` quebram o `sed`; `FOLDER_DEBUG_CONTAINER` recebe `${HOME}` (= `/var/project/backend`) para igualar `PROJECT_DIR` | Efeitos colaterais no `.env` (linhas reescritas indevidamente, senhas com caracteres especiais quebram) | Replicar; **corrigir** com ancoragem `^DEBUG\s*=` e escape do valor |
| R17 | `USE_SOLR`, `IS_ZK_EMBEDDED`, `NUM_SHARDS`, `RF`, `MAX_SHARDS_PER_NODE` não são gravados no `.env` — só existem como variáveis de ambiente do contêiner; `USE_SOLR` é lido pelo `decouple` do ambiente | Um `docker exec python manage.py ...` herda o ambiente e funciona; processos sem o ambiente do contêiner não veem `USE_SOLR` | Replicar |
| R18 | `backend/.dockerignore` existe mas o contexto de build é a raiz do repositório (`context: ../../.`) e não há `.dockerignore` na raiz | O Docker ignora esse arquivo; `ADD backend` copia `backend/.env` (dev) e `backend/db.sqlite3` local para a imagem (**segredos de desenvolvimento dentro da imagem**) e o contexto inclui `node_modules`, `.git` etc. (build lento) | **Corrigir**: `.dockerignore` na raiz; porém hoje o `collectstatic` do build depende do `backend/.env` copiado para obter `SECRET_KEY` e `DATABASE_URL_PRD` (ver R19) |
| R19 | `fake.py` importa `project.py`, que lê `SECRET_KEY` e `DATABASE_URL_PRD` sem valor padrão | O build só funciona se `backend/.env` (ou variáveis `ENV`/`ARG`) fornecer essas chaves; um clone limpo sem `backend/.env` falha no `collectstatic` (a constituição exige `backend/.env` de desenvolvimento) | Replicar; **corrigir** passando valores fictícios em `fake.py`/`ENV` do Dockerfile |
| R20 | `ADD _frontend` + `npm run build` com `vite.config.js` que inclui o plugin ESLint com `failOnError: true`; `eslint.config.js` e `.prettierrc.json` não são copiados na imagem | O build do frontend pode falhar/alterar comportamento se o plugin depender do `eslint.config.js` (a verificar na reconstrução) | Verificar; se necessário copiar `eslint.config.js` |
| R21 | `start.sh` é o PID 1 (bash) e não repassa sinais; Gunicorn/Daphne/Celery são filhos em segundo plano | `docker stop` leva ao *kill* após o *timeout* e sem encerramento limpo do Celery (arquivos `.pid` obsoletos — por isso `rm logs/celery/*.pid` no start) | **Corrigir** com `trap`/init (`tini`) ou supervisor |
| R22 | `ALLOWED_HOSTS = ["*"]` | Aceita qualquer `Host` | Restringir ao domínio de `SITE_URL` (constituição) |
| R23 | Nginx `X-Accel-Redirect`: `/mediaredirect/` é `internal` e serve `/var/project/backend_media/media/` | Correto; depende de a aplicação gerar caminhos sem `private` (feature 009) | Replicar |
| R24 | Imagem Solr fixada em `9.7` (comentário: 9.8 causa erro); `pgvector:0.8.7-pg18-bookworm`; `redis:bookworm` sem versão fixa | `redis:bookworm` é flutuante | Replicar; fixar versão do Redis |
| R25 | `upprod.sh` e `dprod.sh` dependem de `sudo docker` e de a interpolação `${COMPOSE_PROJECT_NAME}` refletir o `-p` | Se o Compose não propagar o `-p` à interpolação, os nomes de contêiner/hosts caem no padrão `startprod1`; a validar | Replicar; passar `COMPOSE_PROJECT_NAME` também como variável de ambiente no script |
| R26 | `start.sh` mistura mensagens em português e inglês; a linha comentada de `wait-for-pg.sh` em `start.sh` traz credenciais/host de exemplo antigos (`backend_st1`, `backenddb`) | Ruído e resquícios | Replicar; limpar |
