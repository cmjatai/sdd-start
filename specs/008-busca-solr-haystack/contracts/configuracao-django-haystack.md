# Contrato: Configuração Django/Haystack e variáveis de ambiente

## Variáveis de ambiente (lidas por `python-decouple`)

| Variável | Onde é lida | Tipo | Padrão | Exemplo (dev) | Descrição |
|---|---|---|---|---|---|
| `USE_SOLR` | `backend/settings/solr.py`; scripts Bash `start-dev.sh`/`start.sh` | bool (Django) / texto `True`\|`true` (Bash) | `False` | `True` (fixado nos Compose) | Liga o provisionamento do Solr na partida (Bash); Django só a expõe como setting |
| `SOLR_URL` | `solr.py`; scripts; `solr_cli.py -u` | URL | `http://startdev1:startdev1@startdev1-solr:8983` | `http://startdev1:startdev1@startdev1-solr:8983` | Base do Solr **com credenciais** `usuario:senha@` (alfanuméricos) |
| `SOLR_COLLECTIONS` | `solr.py`; scripts; `solr_cli.py -c` | CSV | `backend_arq1,backend_arq2` | `startdev1_arq1,startdev1_arq2` | Exatamente duas coleções distintas `<projeto>_arq1,<projeto>_arq2` |
| `IS_ZK_EMBEDDED` | scripts Bash | texto | `True` | `True` | Se `True`/`true`, passa `--embedded_zk` ao `solr_cli.py` |
| `NUM_SHARDS` | scripts Bash | int | `1` | `1` | `-s` |
| `RF` | scripts Bash | int | `1` | `1` | `-rf` (fator de replicação) |
| `MAX_SHARDS_PER_NODE` | scripts Bash | int | `1` | `1` | `-ms` |
| `SOLR_USER` | Compose (`SOLR_URL`) | texto | `startdev1` (dev) / `startprod1` (prod) | — (não existe no `.env`) | Usuário embutido na `SOLR_URL` do `app` |
| `SOLR_PASSWORD` | Compose (`SOLR_URL`) | texto | `startdev1` / `startprod1` | — | Senha embutida na `SOLR_URL` |
| `COMPOSE_PROJECT_NAME` | Compose/scripts | texto | `startdev1`/`startprod1` | `startdev1` | Prefixo do contêiner `<nome>-solr` e das coleções |
| `DEBUG`, `FOLDER_DEBUG_CONTAINER` | `zenv.py` | — | — | — | Condicionam a troca para `localhost:8983` (ver abaixo) |

`backend/.env` (dev) contém `SOLR_URL` e `SOLR_COLLECTIONS` (reescritos por `start-dev.sh`). Em prod, o arquivo é `backend_data/.env`, reescrito por `start.sh`.

### Regra de reescrita da `SOLR_URL` (debug no host)

Condição: `DEBUG` verdadeiro **e** `FOLDER_DEBUG_CONTAINER != PROJECT_DIR`.
Efeito: `SOLR_URL = SOLR_URL.split("@")[0] + "@localhost:8983"`. Dentro do contêiner `FOLDER_DEBUG_CONTAINER=/var/project/backend == PROJECT_DIR` → sem reescrita.

## Settings Django expostas

| Setting | Valor |
|---|---|
| `HAYSTACK_CONNECTIONS["default"]["URL"]` | `<SOLR_URL>/solr/<1ª coleção>` |
| `HAYSTACK_CONNECTIONS["backendarq"]["URL"]` | `<SOLR_URL>/solr/<2ª coleção>` |
| `HAYSTACK_CONNECTIONS[*]["ENGINE"]` | `haystack.backends.solr_backend.SolrEngine` |
| `HAYSTACK_CONNECTIONS[*]["BATCH_SIZE"]` / `["TIMEOUT"]` / `["EXCLUDED_INDEXES"]` | `1000` / `600` / `[]` |
| `HAYSTACK_SIGNAL_PROCESSOR` | `backend.haystack.CelerySignalProcessor` |
| `HAYSTACK_ROUTERS` | `["backend.haystack.DefaultRouter"]` |
| `HAYSTACK_ITERATOR_LOAD_PER_QUERY` | `100` |
| `INSTALLED_APPS` | contém `haystack` e `celery_haystack` |
| `LOGGING["loggers"]["haystack"]` | handlers `backend_logger_file` + `console`, `propagate=False` |

## API Python do módulo `backend.haystack`

| Símbolo | Tipo | Contrato |
|---|---|---|
| `DEFAULT_ALIAS` | `str` | 1ª coleção de `SOLR_COLLECTIONS` |
| `BACKENDARQ_ALIAS` | `str` | 2ª coleção |
| `MODELS_SOLR_DEFAULT` | `tuple` | modelos → coleção 1 (vazia) |
| `MODELS_SOLR_BACKENDARQ` | `tuple` | modelos → coleção 2 (vazia) |
| `CelerySignalProcessor.enqueue_save(sender, instance, **kwargs)` | método | `update` apenas para modelos registrados |
| `CelerySignalProcessor.enqueue_delete(sender, instance, **kwargs)` | método | `delete` filtrado pelo roteador |
| `DefaultRouter.for_write(**hints)` / `for_read(**hints)` / `for_rw(**hints)` | métodos | `hints`: `instance`, `index` ou `models` → alias, `DEFAULT_ALIAS` (sem *hints*) ou `None` |

Erros: `ValueError("SOLR_COLLECTIONS must contain at least two distinct collections separated by a comma and defined in settings.SOLR_COLLECTIONS.")` na importação do módulo; `IndexError` se `SOLR_COLLECTIONS` tiver menos de 2 itens (já em `solr.py`).

## Endpoints HTTP

Nenhum endpoint Django, rota ou permissão nova. O Solr (`/solr/...`) é acessado diretamente pelos scripts e (futuramente) pelo Haystack/pysolr.

## Dependências (pyproject.toml)

`django-haystack = "^3.4.0"`, `celery-haystack = {git = "https://github.com/LeandroJatai/celery-haystack.git"}`, `pysolr = "^3.11.0"`, `kazoo = "^2.11.0"`.
