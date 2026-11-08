# Início Rápido: validar a infraestrutura de busca (Solr + Haystack)

Pré-requisitos: Docker/Compose, `backend/.env` de dev criado (ver README), ambiente Poetry instalado (`poetry install`).

## 1. Subir o ambiente de desenvolvimento

```bash
./rdev.sh        # ou ./uupdev.sh (scripts de raiz — ver 010-docker-desenvolvimento)
```

No log do contêiner `app` esperar:

```text
Solr configurations
===================
URL: http://startdev1:startdev1@startdev1-solr:8983
COLLECTION: startdev1_arq1,startdev1_arq2
NUM_SHARDS: 1 ...
running Solr script
Waiting for Solr connection at ...
Solr server is up!
Connecting to Solr...
Assuming embedded ZooKeeper instalation...
Creating security.json file...
Uploading security.json file...
Collection 'startdev1_arq1' created succesfully
Collection 'startdev1_arq2' created succesfully
```

(Se o Solr demorar mais de ~7 s a subir: "Solr is offline, not possible to connect." — reinicie o `app`; ver `research.md` item 6.)

## 2. Verificar Solr, autenticação e coleções

```bash
# sem credenciais → 401 (após o primeiro start com IS_ZK_EMBEDDED=True)
curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8983/solr/admin/collections?action=LIST"

# com credenciais → 200 e as duas coleções
curl -s -u startdev1:startdev1 "http://localhost:8983/solr/admin/collections?action=LIST&wt=json"

# configsets enviados
curl -s -u startdev1:startdev1 "http://localhost:8983/solr/admin/configs?action=LIST&wt=json"   # arq1_configset, arq2_configset

# schema de cada coleção
curl -s -u startdev1:startdev1 "http://localhost:8983/solr/startdev1_arq1/schema/fields?fl=name" | grep -o '"name":"[a-z_]*"'
curl -s -u startdev1:startdev1 "http://localhost:8983/solr/startdev1_arq2/schema/fields?fl=name" | grep -o '"name":"[a-z_]*"'
```

Esperado: `arq1` com `at` e sem `tipo`; `arq2` com `tipo`, `ano`, `data`, `conta_classe_*` e sem `at`. Admin UI: `http://localhost:8983/solr/` (pede login).

Idempotência: reiniciar só o `app` (`docker compose -f _docker/dev/docker-compose.yaml restart app`) → "Collection … exists." e "O arqN_configset já presente no servidor, NÃO enviando." não aparece (o upload só é tentado ao criar coleção nova).

## 3. Verificar a configuração Django (no host ou no contêiner)

```bash
DJANGO_SETTINGS_MODULE=backend.settings python - <<'PY'
import django; django.setup()
from django.conf import settings
print(settings.HAYSTACK_CONNECTIONS["default"]["URL"])      # .../solr/<projeto>_arq1
print(settings.HAYSTACK_CONNECTIONS["backendarq"]["URL"])   # .../solr/<projeto>_arq2
from backend import haystack as h
print(h.DEFAULT_ALIAS, h.BACKENDARQ_ALIAS, h.MODELS_SOLR_DEFAULT, h.MODELS_SOLR_BACKENDARQ)
PY
```

No host (`DEBUG=True`, `FOLDER_DEBUG_CONTAINER` ≠ pasta do projeto) a URL deve conter `@localhost:8983`.

Verificação de "nada é indexado": criar/salvar/excluir qualquer registro (ex.: usuário) e confirmar que o Celery não recebe tarefas `celery_haystack.tasks.*`.

## 4. Verificar o `ValueError` de coleções

```bash
SOLR_COLLECTIONS=a_arq1,a_arq1 DJANGO_SETTINGS_MODULE=backend.settings python -c "import django; django.setup(); import backend.haystack"
# → ValueError: SOLR_COLLECTIONS must contain at least two distinct collections ...
```

## 5. Verificar o `solr_cli.py` isoladamente

```bash
python3 _docker/prod/solr_cli.py -u http://startdev1:startdev1@localhost:8983 -c startdev1_arq1,startdev1_arq2 -s 1 -rf 1 -ms 1 --embedded_zk
python3 _docker/prod/solr_cli.py -u http://startdev1:startdev1@localhost:8983 -c startdev1_arq1,startdev1_arq2 -rc startdev1_arq2   # recria só arq2
bash _docker/prod/wait-for-solr.sh http://startdev1:startdev1@localhost:8983; echo $?              # 1 = online, 2 = falha
```

Executar da raiz do repositório. `security.json` aparece na raiz (ignorado pelo git).

## 6. Produção

```bash
./upprod.sh       # ver 011-docker-producao
```

As portas 8983/9983 não são publicadas; acessar o Solr apenas por `docker exec` no contêiner `app` (`curl -u … http://<projeto>-solr:8983/solr/...`).

## 7. Testes automatizados

Nenhum teste existente cobre esta feature. Testes propostos (arquivo `backend/test_solr_haystack.py`, `pytest`, sem Solr real):

| Teste | Verifica |
|---|---|
| `test_solr_hash_password_formato` | `solr_hash_password("x", salt_b64)` é determinístico; hash e sal são base64 de 32 bytes; sal aleatório muda o hash |
| `test_url_pattern_aceita_alfanumericos` / `test_url_pattern_rejeita_especiais` | `URL_PATTERN` captura usuário/senha/host; `a_b:pw@h` não captura credenciais |
| `test_create_security_file(tmp_path, monkeypatch)` | `security.json` válido (JSON), usuário com papel `admin`, `blockUnknown` verdadeiro |
| `test_solrclient_nomes` | `SolrClient(url, "p_arq1,p_arq2", None)` gera `CONFIGSET_NAME == "arq1_configset"` e `CONFIGSET_PATH` esperado (limpar `COLLECTIONS`) |
| `test_zip_configset` | zip contém `managed-schema.xml` e `lang/stopwords_pt.txt` na raiz |
| `test_create_collection_requests(monkeypatch)` | com `requests` simulado: upload só quando o *configset* não existe; URL de CREATE com `numShards`, `replicationFactor`, `maxShardsPerNode` |
| `test_router_sem_hints` / `test_router_modelo_nao_registrado` | `DefaultRouter().for_write()` → `DEFAULT_ALIAS`; com `instance=<User>` → `None` (monkeypatch das tuplas) |
| `test_router_modelos_registrados` | modelo em `MODELS_SOLR_BACKENDARQ` → `BACKENDARQ_ALIAS`; em `MODELS_SOLR_DEFAULT` → `DEFAULT_ALIAS` |
| `test_processor_ignora_modelos_nao_registrados` | `enqueue_save` não chama `enqueue` para `User` |
| `test_validacao_colecoes` | `importlib.reload(backend.haystack)` com `settings.SOLR_COLLECTIONS="a,a"` → `ValueError` |
| `test_haystack_connections` | duas conexões, `BATCH_SIZE=1000`, `TIMEOUT=600`, URL termina com a coleção correspondente |
| `test_schemas_xml` | `managed-schema.xml` de cada configset: campos esperados (parse com `xml.etree`) |

Executar: `pytest backend/test_solr_haystack.py` e `ruff check .`.
