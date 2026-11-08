# Plano de Implementação: Infraestrutura de Busca Textual (Solr + Haystack)

**Branch**: `008-busca-solr-haystack` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/008-busca-solr-haystack/spec.md`

**Nota**: Documento de engenharia reversa — descreve o que **já existe** no repositório.

## Resumo

Entrega a infraestrutura de busca: serviço Solr 9.7 (SolrCloud + ZooKeeper embutido) nos compose de dev e prod; configuração Django/Haystack com duas conexões (`default` → `<projeto>_arq1`, `backendarq` → `<projeto>_arq2`); roteador e processador de sinais próprios (`backend/haystack.py`) apoiados em `celery-haystack` para indexação assíncrona; dois *configsets* versionados em `solr/`; e o utilitário `_docker/prod/solr_cli.py` (+ `wait-for-solr.sh`) que, na partida do `app`, envia *configsets*, cria coleções e aplica BasicAuth ao Solr. Nenhum modelo é registrado para indexação — o esqueleto só prepara o terreno.

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (imagem-base 3.14), Bash, XML (Solr), JSON (security.json)

**Dependências Principais**: `django-haystack` 3.4.0 (^3.4.0), `celery-haystack` 1.1.0 (fork git `LeandroJatai/celery-haystack`), `pysolr` 3.11.0 (^3.11.0), `kazoo` 2.11.0 (^2.11.0, ZooKeeper), `requests` 2.34.2 (dependência transitiva, **não** declarada no `pyproject.toml`), `celery` 5.7.0; imagem Docker `solr:9.7`

**Armazenamento**: índices Solr em volume Docker `solr9_data` (`/var/solr`); *configsets* em `solr9_configsets`; configurações no `.env` (sem tabelas novas no PostgreSQL)

**Testes**: pytest + pytest-django (`DJANGO_SETTINGS_MODULE = backend.settings`); nenhum teste existente cobre a feature — ver `quickstart.md` para os propostos

**Plataforma Alvo**: Contêineres Linux (Docker Compose dev/prod); execução opcional do Django no host (dev)

**Tipo de Projeto**: aplicação web (backend Django) + infraestrutura de serviços

**Metas de Desempenho**: `BATCH_SIZE=1000` por lote de indexação, `TIMEOUT=600` s por requisição Solr, `HAYSTACK_ITERATOR_LOAD_PER_QUERY=100`

**Restrições**: Solr fixado em 9.7 (9.8 causa erro, ver comentário nos compose); credenciais alfanuméricas na `SOLR_URL`; duas coleções distintas obrigatórias; portas 8983/9983 publicadas só em dev

**Escala/Escopo**: 2 coleções, 1 shard, fator de replicação 1 por padrão; 0 modelos indexados

## Verificação da Constituição

| Princípio | Gate | Situação |
|---|---|---|
| I. Backend modular por apps | Configuração em módulo temático `backend/settings/solr.py` (reunido por `project.py`); apps `haystack`/`celery_haystack` em `apps.py`; módulo `backend/haystack.py` | ✅ Atendido |
| II. Config por ambiente, sem segredos | `USE_SOLR`, `SOLR_URL`, `SOLR_COLLECTIONS` via `python-decouple`; `security.json` no `.gitignore`; padrões `startdev1`/`startprod1` são valores de exemplo | ✅ Atendido (senha embutida na URL é risco registrado em `research.md`) |
| III. Paridade dev/prod via Docker | Mesmo serviço `solr:9.7` e mesmo bloco SOLR nos dois `start*.sh`; `COMPOSE_PROJECT_NAME` prefixa contêiner e coleções | ✅ Atendido |
| IV. API REST gerada | Sem endpoints novos | ➖ N/A |
| V. Frontend Vite | Sem impacto | ➖ N/A |
| VI. Tempo real e assíncrono | Indexação só por `celery-haystack` (`CelerySignalProcessor`) | ✅ Atendido |
| VII. Português do Brasil | Docs/specs em pt-BR; identificadores técnicos em inglês; mensagens dos scripts mistas (inglês/pt-BR) | ⚠️ Justificado: mensagens de console dos scripts herdadas em inglês (ver `research.md`) |
| VIII. Qualidade verificável | Sem testes hoje; `quickstart.md` e `tasks.md` propõem testes pytest e `ruff` | ⚠️ Justificado: lacuna conhecida da linha de base, coberta por tarefas |

Restrições: Solr 9.7 SolrCloud com ZooKeeper embutido e BasicAuth gerada por `solr_cli.py` — atendidas.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/008-busca-solr-haystack/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── configuracao-django-haystack.md
│   ├── solr-cli-e-scripts.md
│   ├── configsets-solr.md
│   └── docker-solr.md
├── spec.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── haystack.py                 # CelerySignalProcessor, DefaultRouter, MODELS_SOLR_*
└── settings/
    ├── apps.py                 # "haystack", "celery_haystack" em DJANGO_THIRD_PARTY_APPS
    ├── logs.py                 # logger "haystack"
    ├── project.py              # from .solr import *
    └── solr.py                 # USE_SOLR, SOLR_URL, SOLR_COLLECTIONS, HAYSTACK_*
solr/
├── arq1_configset/conf/        # managed-schema.xml, solrconfig.xml, protwords.txt, stopwords.txt, synonyms.txt, lang/stopwords_{en,es,pt}.txt
└── arq2_configset/conf/        # idem (schema com campos extras)
_docker/
├── dev/
│   ├── docker-compose.yaml     # serviço solr + volumes + variáveis do app
│   └── start-dev.sh            # bloco "## SOLR" + chaves SOLR_* no .env
└── prod/
    ├── docker-compose.yaml     # serviço solr (sem portas publicadas)
    ├── start.sh                # bloco "## SOLR" + chaves SOLR_* no .env
    ├── solr_cli.py             # SolrClient + segurança no ZK embutido
    └── wait-for-solr.sh        # sondagem de disponibilidade
pyproject.toml                  # django-haystack, celery-haystack (git), pysolr, kazoo
.gitignore                      # security.json
```

**Decisão de Estrutura**: aplicação web Django monolítica; a lógica Python de busca fica em `backend/haystack.py` e `backend/settings/solr.py` (módulo temático, princípio I); artefatos de infraestrutura (*configsets*, CLI) ficam fora do pacote `backend` (`solr/`, `_docker/prod/`) porque são copiados para a imagem de produção (`ADD solr ${HOME}/solr`, `COPY _docker/prod/solr_cli.py ${HOME}`). Os testes propostos ficam em `backend/test_solr_haystack.py` (casa com `testpaths = ["**/tests.py", "**/test_*.py"]` do `pyproject.toml`).

## Rastreamento de Complexidade

Sem violações da constituição. As duas ressalvas (VII e VIII) estão justificadas na tabela de gates e tratadas em `research.md` / `tasks.md`.

## Detalhamento de Implementação

### 1. Dependências (`pyproject.toml`)

```toml
django-haystack = "^3.4.0"
celery-haystack = {git = "https://github.com/LeandroJatai/celery-haystack.git"}
pysolr = "^3.11.0"
kazoo = "^2.11.0"
```

`requests` é usado por `solr_cli.py` mas só vem transitivamente. Depois de editar: `poetry lock`/`poetry install`. O fork `celery-haystack` (1.1.0) é usado no lugar da versão do PyPI (motivo presumido: compatibilidade com Django 6; ver `research.md`).

### 2. Apps e logs

- `backend/settings/apps.py`: `"haystack"` e `"celery_haystack"` em `DJANGO_THIRD_PARTY_APPS`, após `django_celery_results` e antes de `drf_spectacular`.
- `backend/settings/logs.py`: logger `"haystack"` com handlers `["backend_logger_file", "console"]`, `level=LOGGING_ROOT_LEVEL`, `propagate=False`.
- `backend/settings/project.py`: `from .solr import *  # noqa: F403` (entre `middleware` e `zasyncs`).
- Tarefas do `celery_haystack` são descobertas por `app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)` em `backend/celery.py`. `celery-haystack` não é configurado por `CELERY_HAYSTACK_*` (usa os padrões: fila padrão, `COUNTDOWN=0`, `RETRY_DELAY=300`, `MAX_RETRIES=1`, `TRANSACTION_SAFE=True`).

### 3. `backend/settings/solr.py`

Algoritmo, na ordem:

1. `from .zenv import DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config`.
2. `USE_SOLR = config("USE_SOLR", default=False, cast=bool)`.
3. `SOLR_URL = config("SOLR_URL", default="http://startdev1:startdev1@startdev1-solr:8983")`.
4. `HAYSTACK_SIGNAL_PROCESSOR = "backend.haystack.CelerySignalProcessor"`.
5. Se `DEBUG` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR` (execução no host): `SOLR_URL = SOLR_URL.split("@")[0] + "@localhost:8983"`. (Há linha comentada alternativa com `haystack.signals.RealtimeSignalProcessor`.)
6. `SOLR_COLLECTIONS = config("SOLR_COLLECTIONS", default="backend_arq1,backend_arq2")` (string separada por vírgula).
7. `SEARCH_BACKEND = "haystack.backends.solr_backend.SolrEngine"`; `HAYSTACK_ROUTERS = ["backend.haystack.DefaultRouter"]`; `HAYSTACK_ITERATOR_LOAD_PER_QUERY = 100`.
8. `HAYSTACK_CONNECTIONS`:

| Conexão | `URL` | Demais chaves |
|---|---|---|
| `default` | `"{SOLR_URL}/solr/{SOLR_COLLECTIONS.split(',')[0]}"` | `ENGINE=SEARCH_BACKEND`, `BATCH_SIZE=1000`, `TIMEOUT=600`, `EXCLUDED_INDEXES=[]` |
| `backendarq` | `"{SOLR_URL}/solr/{SOLR_COLLECTIONS.split(',')[1]}"` | idem |

Observação: `USE_SOLR` é definido mas **não é consultado** por código Django; só os scripts Bash o usam (via variável de ambiente do contêiner).

### 4. `backend/haystack.py`

Imports: `logging`, `celery_haystack.signals.CelerySignalProcessor`, `django.conf.settings`, `django.db.models.base.Model`, `haystack.constants.DEFAULT_ALIAS` (sobrescrito logo abaixo), `haystack.routers.DefaultRouter`; `logger = logging.getLogger(__name__)`.

Constantes de módulo:

```python
DEFAULT_ALIAS = settings.SOLR_COLLECTIONS.split(",")[0]
BACKENDARQ_ALIAS = settings.SOLR_COLLECTIONS.split(",")[1]   # IndexError se só houver 1 coleção
if not BACKENDARQ_ALIAS or not DEFAULT_ALIAS or BACKENDARQ_ALIAS == DEFAULT_ALIAS:
    raise ValueError("SOLR_COLLECTIONS must contain at least two distinct collections separated by a comma and defined in settings.SOLR_COLLECTIONS.")
MODELS_SOLR_DEFAULT = ()
MODELS_SOLR_BACKENDARQ = ()
```

Classe `CelerySignalProcessor(CelerySignalProcessor)` (mesmo nome da base):

- `enqueue_save(self, sender, instance, **kwargs)`: se `sender not in (MODELS_SOLR_BACKENDARQ + MODELS_SOLR_DEFAULT)` → `return`; senão `self.enqueue("update", instance, sender, **kwargs)`.
- `enqueue_delete(self, sender, instance, **kwargs)`: `self.enqueue("delete", instance, sender, **kwargs)` (a filtragem acontece no roteador).

Classe `DefaultRouter(DefaultRouter)`:

- `for_write(**hints)` e `for_read(**hints)` delegam a `for_rw(**hints)`.
- `for_rw(**hints)`:
  1. sem *hints* → `DEFAULT_ALIAS`;
  2. `"instance" in hints`: `m = hints["instance"]._meta.model`; `m in MODELS_SOLR_BACKENDARQ` → `BACKENDARQ_ALIAS`; `m not in MODELS_SOLR_DEFAULT` → `None`;
  3. `elif "index" in hints`: `m = hints["index"].model`, mesma regra;
  4. `elif "models" in hints`: `m = hints["models"]`; se `m` e não for `Model` → `m = m[0]`; mesma regra;
  5. fim → `DEFAULT_ALIAS`.

Como `ConnectionRouter` do Haystack aceita `str` ou iterável, o retorno de string é tratado como uma conexão; `None` descarta. Ver `research.md` sobre a discrepância alias × chave de conexão.

O módulo só é importado por `HAYSTACK_SIGNAL_PROCESSOR` (carregado pelo `haystack.apps`/`haystack.signals` ao iniciar o Django).

### 5. *Configsets* (`solr/arq{1,2}_configset/conf`)

Detalhes em `contracts/configsets-solr.md`. Ambos derivam do `_default` do Solr 9.x (`luceneMatchVersion` 9.9, schema gerenciado `managed-schema.xml` — sem `<schemaFactory>` explícito, vale o padrão gerenciado do Solr —, cadeia `add-unknown-fields-to-the-schema`). Customizações:

- Campos de domínio (seção "Django fields") conforme FR-012/FR-013.
- `fieldType text_pt` (htmlStrip → standard → lowercase → stop `lang/stopwords_pt.txt` snowball → `brazilianStem`).
- `/select`: `rows=50`, `df=text`, `defType=edismax`, `lowercaseOperators=true`, `q.op=AND`.
- `initParams` `/update/**,/query,/select,/spell`: `df=text`.
- Diferenças `arq2` × `arq1`: campos extras/ausente no schema; `spellchecker.field=_text_` (arq1: `text`); `hl.fragsize=100` (arq1: 512). O restante (inclusive `solrconfig.xml`) é idêntico exceto linhas em branco.

### 6. `_docker/prod/solr_cli.py`

Executado da raiz do projeto (dev: `/var/project/backend`; prod: `${HOME}` com cópia de `solr/`). Estrutura:

- `logging.basicConfig()`.
- `SECURITY_FILE_TEMPLATE`: JSON com `authentication` (`blockUnknown: true`, `class: solr.BasicAuthPlugin`, `credentials: {user: "<hash> <sal>"}`, `forwardCredentials: false`, `realm: "Solr Login"`) e `authorization` (`class: solr.RuleBasedAuthorizationPlugin`, `permissions: [{"name":"security-edit","role":"admin"}]`, `user-role: {user: "admin"}`), preenchido por `%` com `(usuario, hash, sal, usuario)`.
- `URL_PATTERN = "https?://(([a-zA-Z0-9]+):([a-zA-Z0-9]+)@)?([a-zA-Z0-9.-]+)(:[0-9]{4})?"`.
- `solr_hash_password(password, salt=None) -> (cypher_b64, salt_b64)`: sal = `secrets.token_bytes(32)` (ou `b64decode(salt)`); `digest = sha256(salt + password.utf8)`; `digest = sha256(digest)`; retorna base64 de ambos.
- `create_security_file(username, password)`: grava `security.json` no diretório corrente.
- `upload_security_file(zk_host)`: `KazooClient(hosts=f"{zk_host}:9983")`, `start()`, `set`/`create` de `/security.json` conforme `exists`, relê e imprime, `stop()`; em exceção imprime e `sys.exit(-1)`.
- `class SolrClient` com *templates* de URL (`LIST_CONFIGSETS`, `DELETE_CONFIGSET`, `UPLOAD_CONFIGSET`, `LIST_COLLECTIONS`, `CREATE_COLLECTION`, `DELETE_COLLECTION`, `DELETE_DATA`, `QUERY_DATA`, e outras não usadas) e lista de classe `COLLECTIONS = []`:
  - `__init__(url, collections, recreate_collections)`: divide por `,`; se `recreate_collections`, chama `delete_collection(c)` para cada; para cada coleção: `c.split("_")` → dicionário `{COLLECTION_NAME: f"{c[0]}_{c[1]}", CONFIGSET_NAME: f"{c[1]}_configset", CONFIGSET_PATH: f"./solr/{c[1]}_configset/conf", FORCE: <está em recreate>}` anexado a `COLLECTIONS`.
  - `get_num_docs`, `list_collections` (`dic["collections"]`; em erro imprime e devolve `0`), `exists_collection`.
  - `zip_configset`: zip `ZIP_DEFLATED` em memória (`BytesIO`) de `rglob("*")` com caminhos relativos a `conf/`.
  - `maybe_upload_configset`: lista *configsets*; se existe e `FORCE` → `POST DELETE_CONFIGSET`; se não existe ou `FORCE` → `POST UPLOAD_CONFIGSET` multipart (`file`, `application/octet-stream`); senão imprime "O <nome> já presente no servidor, NÃO enviando.".
  - `create_collection(collection_dict, shards=1, replication_factor=1, max_shards_per_node=1)`: `maybe_upload_configset` e `POST CREATE_COLLECTION`; imprime sucesso/erro; devolve `bool`.
  - `delete_collection(name)`: `"*"` → todas as listadas; `POST DELETE_COLLECTION`.
  - `delete_index_data(name)`: `POST` XML `<delete><query>*:*</query></delete>` (não usado).
- `setup_embedded_zk(solr_url)`: `re.match(URL_PATTERN, url)`; com usuário+senha+host → `create_security_file` + `upload_security_file(host)`; caso contrário imprime e `sys.exit(-1)`.
- `__main__`: `argparse` com `-u`, `-c` (obrigatórios, `nargs=1`), `-rc`, `-s`, `-rf`, `-ms` (`nargs="?"`, `int`, padrão 1), `--embedded_zk`; se `--embedded_zk` → `setup_embedded_zk(url)`; instancia `SolrClient`; para cada coleção em `client.COLLECTIONS`, se não existe → `create_collection(...)`, senão imprime "Collection ... exists."; bloco `if False:` com `rebuild_index` é código morto.

### 7. `_docker/prod/wait-for-solr.sh`

Parâmetro `$1` = URL base. `RETRY_COUNT=0`, `RETRY_LIMIT=60`; `while [[ $RETRY_COUNT < $RETRY_LIMIT ]]` (comparação lexicográfica → ~7 iterações); em cada passo incrementa, imprime a URL, executa `curl -s -o /dev/null -I "$SOLR_URL/solr/admin/collections?action=LIST" -w '%{http_code}'`; `200` → `echo "Solr server is up!"` e `exit 1`; senão `sleep 1`. Ao fim: `echo "Solr connection failed."` e `exit 2`.

### 8. Bloco SOLR dos *start scripts*

Em `_docker/dev/start-dev.sh` (depois de `python3 manage.py migrate`) e `_docker/prod/start.sh` (idem):

1. Função `change_env_file` (já coberta em 010/011) reescreve no `.env` as chaves `SOLR_COLLECTIONS = ${SOLR_COLLECTIONS:=${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2}` e `SOLR_URL = ${SOLR_URL:=http://<startdev1|startprod1>:<idem>@${COMPOSE_PROJECT_NAME}-solr:8983}`.
2. Variáveis: `USE_SOLR=${USE_SOLR:=False}`, `SOLR_URL`, `SOLR_COLLECTIONS`, `NUM_SHARDS=${NUM_SHARDS:=1}`, `RF=${RF:=1}`, `MAX_SHARDS_PER_NODE=${MAX_SHARDS_PER_NODE:=1}`, `IS_ZK_EMBEDDED=${IS_ZK_EMBEDDED:=True}`.
3. Se `USE_SOLR` ∈ {`True`,`true`}: imprime o quadro de configuração; executa `/bin/bash _docker/prod/wait-for-solr.sh $SOLR_URL` (prod: `wait-for-solr.sh $SOLR_URL`); `CHECK_SOLR_RETURN=$?`; se `== 1`: define `ZK_EMBEDDED="--embedded_zk"` quando `IS_ZK_EMBEDDED` ∈ {`True`,`true`} e roda `python3 _docker/prod/solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED` (prod: `python3 solr_cli.py ...`); senão imprime "Solr is offline, not possible to connect.".
4. Se desligado: "Solr support is not initialized.".
5. Em seguida o script remove os `.pid` do Celery e inicia o Celery (fora do escopo; 010/011).

### 9. Serviço `solr` nos Compose

Detalhes em `contracts/docker-solr.md`. Dev: `container_name: ${COMPOSE_PROJECT_NAME:-startdev1}-solr`, `restart: on-failure`, rede `appdev-net`, portas `8983:8983` e `9983:9983`. Prod: `container_name: ${COMPOSE_PROJECT_NAME:-startprod1}-solr`, `restart: always`, rede `app-net`, portas comentadas. Em ambos: `image: solr:9.7 # validar mudança para 9.8 pois está causando erro`, `command: bin/solr start -c -f`, volumes `solr9_data:/var/solr` e `solr9_configsets:/opt/solr/server/solr/configsets` (declarados em `volumes:`); o `app` tem `depends_on` do `solr` (prod: `condition: service_started`) e variáveis `USE_SOLR: 'True'`, `SOLR_COLLECTIONS`, `SOLR_URL: http://${SOLR_USER:-<padrão>}:${SOLR_PASSWORD:-<padrão>}@${COMPOSE_PROJECT_NAME:-<padrão>}-solr:8983`, `IS_ZK_EMBEDDED: 'True'`.

### 10. Ignorados pelo git

`.gitignore` contém `security.json` (gerado na raiz de execução do `solr_cli.py`).
