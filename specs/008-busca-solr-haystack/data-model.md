# Modelo de Dados: Infraestrutura de Busca Textual (Solr + Haystack)

**Não há tabelas novas nem migrações** nesta funcionalidade: `haystack` e `celery_haystack` não definem modelos Django persistidos (`celery_haystack` só fornece tarefas Celery; os resultados das tarefas usam `django_celery_results`, já existente — ver 001/`zasyncs.py`). Abaixo estão as estruturas de dados relevantes: configuração, registro de modelos, documentos Solr, `security.json` e estado em volumes.

## 1. Configuração (`backend/settings/solr.py`)

| Chave | Tipo | Origem | Padrão | Observação |
|---|---|---|---|---|
| `USE_SOLR` | bool | env/`.env` | `False` | Não consultado por código Django; usado pelos scripts Bash via ambiente |
| `SOLR_URL` | str | env/`.env` | `http://startdev1:startdev1@startdev1-solr:8983` | `esquema://usuario:senha@host[:porta]`; reescrita para `…@localhost:8983` em debug no host |
| `SOLR_COLLECTIONS` | str | env/`.env` | `backend_arq1,backend_arq2` | Lista separada por vírgula; usam-se só os dois primeiros itens |
| `HAYSTACK_SIGNAL_PROCESSOR` | str | fixo | `backend.haystack.CelerySignalProcessor` | |
| `SEARCH_BACKEND` | str | fixo | `haystack.backends.solr_backend.SolrEngine` | |
| `HAYSTACK_ROUTERS` | list[str] | fixo | `["backend.haystack.DefaultRouter"]` | |
| `HAYSTACK_ITERATOR_LOAD_PER_QUERY` | int | fixo | `100` | |
| `HAYSTACK_CONNECTIONS` | dict | derivado | ver abaixo | |

```python
HAYSTACK_CONNECTIONS = {
    "default":    {"ENGINE": SEARCH_BACKEND, "URL": f"{SOLR_URL}/solr/{colecoes[0]}", "BATCH_SIZE": 1000, "TIMEOUT": 600, "EXCLUDED_INDEXES": []},
    "backendarq": {"ENGINE": SEARCH_BACKEND, "URL": f"{SOLR_URL}/solr/{colecoes[1]}", "BATCH_SIZE": 1000, "TIMEOUT": 600, "EXCLUDED_INDEXES": []},
}
```

## 2. Registro de modelos indexáveis (`backend/haystack.py`)

| Constante | Tipo | Valor atual | Função |
|---|---|---|---|
| `DEFAULT_ALIAS` | str | 1ª coleção de `SOLR_COLLECTIONS` | Alias devolvido pelo roteador para modelos "default" |
| `BACKENDARQ_ALIAS` | str | 2ª coleção | Alias para modelos "backendarq" |
| `MODELS_SOLR_DEFAULT` | `tuple[type[Model], ...]` | `()` | Modelos indexados na coleção 1 |
| `MODELS_SOLR_BACKENDARQ` | `tuple[type[Model], ...]` | `()` | Modelos indexados na coleção 2 |

Regras: um modelo em `MODELS_SOLR_BACKENDARQ` → coleção 2; em `MODELS_SOLR_DEFAULT` → coleção 1; em nenhuma → ignorado. Um modelo não deve constar nas duas (a de `BACKENDARQ` vence no roteador).

### Comportamentos (sinais)

| Evento | Processamento |
|---|---|
| `post_save` de qualquer modelo | `enqueue_save`: retorna se `sender` não estiver nas tuplas; senão `enqueue("update", …)` → roteador `for_write(instance=…)` → conexões → se o índice for `CelerySearchIndex` e `should_update(instance)` → `enqueue_task` (Celery, `transaction.on_commit`) |
| `post_delete` de qualquer modelo | `enqueue("delete", …)` → roteador devolve `None` para modelos não registrados ⇒ nada enfileirado |

Hoje (tuplas vazias) ambos resultam em **nenhuma tarefa**.

## 3. Documento Solr (esquema lógico por coleção)

### Campos comuns (`arq1` e `arq2`)

| Campo | Tipo Solr | indexed | stored | multiValued | Outros |
|---|---|---|---|---|---|
| `id` | `string` | sim | sim | não | `required="true"`; `<uniqueKey>id</uniqueKey>` |
| `_version_` | `plong` | não | não | — | controle otimista |
| `_text_` | `text_general` | sim | não | sim | catch-all; sem `copyField` ativo |
| `django_ct` | `string` | sim | sim | não | `app_label.model` (Haystack) |
| `django_id` | `string` | sim | sim | não | PK do objeto Django |
| `last_update` | `pdate` | sim | sim | — | `default="NOW"`, `docValues` |
| `text` | `text_pt` | sim | sim | não | texto principal pesquisável |

### Campos específicos

| Coleção | Campo | Tipo | Opções |
|---|---|---|---|
| `arq1` | `at` | `pint` | `required=false`, `docValues`, `default="0"`, não multivalorado |
| `arq2` | `conta_classe_logica` | `string` | `docValues`, não multivalorado |
| `arq2` | `conta_classe_estrutural` | `string` | `docValues` |
| `arq2` | `tipo` | `string` | `docValues` |
| `arq2` | `ano` | `pint` | `required=false`, `docValues` |
| `arq2` | `data` | `pdate` | `required=false`, `docValues` |

Campos dinâmicos herdados do `_default` (`*_i`, `*_s`, `*_l`, `*_t`, `*_dt`, `*_ws`, `*_txt`, `random_*`, etc.) permanecem. A cadeia `add-unknown-fields-to-the-schema` cria campos desconhecidos automaticamente.

### Tipo `text_pt`

`charFilter htmlStrip` → `tokenizer standard` → `lowercase` → `stop` (`ignoreCase=true`, `words=lang/stopwords_pt.txt`, `format=snowball`) → `brazilianStem`.

## 4. `security.json` (estrutura gerada)

```json
{
  "authentication": {"blockUnknown": true, "class": "solr.BasicAuthPlugin",
    "credentials": {"<usuario>": "<base64 sha256(sha256(sal+senha))> <base64 sal>"},
    "forwardCredentials": false, "realm": "Solr Login"},
  "authorization": {"class": "solr.RuleBasedAuthorizationPlugin",
    "permissions": [{"name": "security-edit", "role": "admin"}],
    "user-role": {"<usuario>": "admin"}}
}
```

Gravado em arquivo local (`security.json`, ignorado pelo git) e no nó ZooKeeper `/security.json`.

## 5. Estado em volumes Docker

| Volume | Ponto de montagem (contêiner `solr`) | Conteúdo |
|---|---|---|
| `solr9_data` | `/var/solr` | Dados de índice, logs, ZooKeeper embutido |
| `solr9_configsets` | `/opt/solr/server/solr/configsets` | *Configsets* base do Solr |

## 6. Dicionário interno do `SolrClient` (por coleção)

| Chave | Exemplo (`COMPOSE_PROJECT_NAME=startdev1`) |
|---|---|
| `COLLECTION_NAME` | `startdev1_arq1` |
| `CONFIGSET_NAME` | `arq1_configset` |
| `CONFIGSET_PATH` | `./solr/arq1_configset/conf` |
| `FORCE` | `True` se a coleção está em `-rc`, senão `False` |

## 7. Migrações

Nenhuma.
