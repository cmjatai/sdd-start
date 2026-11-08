# Contrato: `solr_cli.py`, `wait-for-solr.sh` e blocos SOLR dos scripts de partida

## `_docker/prod/solr_cli.py`

Executar **na raiz do projeto** (diretório onde existe `./solr/<sufixo>_configset/conf` e onde `security.json` será gravado). Dev: `/var/project/backend`; prod: `${HOME}` da imagem.

```text
python3 _docker/prod/solr_cli.py -u URL -c COLLECTIONS [-rc RECREATE] [-s N] [-rf N] [-ms N] [--embedded_zk]
```

| Argumento | Obrig. | Tipo | Padrão | Significado |
|---|---|---|---|---|
| `-u URL` | sim | str | — | `http(s)://[usuario:senha@]host[:porta]` |
| `-c COLLECTIONS` | sim | str CSV | — | Coleções a criar (`<projeto>_arqN`) |
| `-rc RECREATE` | não | str CSV | — | Coleções a apagar e recriar (`*` = todas as existentes) |
| `-s` | não | int | `1` | `numShards` |
| `-rf` | não | int | `1` | `replicationFactor` |
| `-ms` | não | int | `1` | `maxShardsPerNode` |
| `--embedded_zk` | não | flag | `False` | Gera e envia `security.json` ao ZooKeeper embutido |

### Códigos de saída

| Código | Situação |
|---|---|
| `0` | Fim normal (inclusive se coleção já existe ou criação falha — o script não propaga erro de criação) |
| `-1` (255) | URL fora do padrão / sem usuário-senha com `--embedded_zk`; falha ao enviar `security.json` ao ZK |
| 2 (argparse) | Argumentos obrigatórios ausentes |

### Fluxo

1. Parse dos argumentos.
2. Se `--embedded_zk`: `setup_embedded_zk(url)` → `re.match(URL_PATTERN)` → `create_security_file(usuario, senha)` → `upload_security_file(host)`.
3. `SolrClient(url, collections, recreate_collections)`: apaga coleções de `-rc`; monta a lista `COLLECTIONS`.
4. Para cada coleção: se `exists_collection` é falso → `create_collection(...)` (que antes chama `maybe_upload_configset`); caso contrário, imprime "Collection '…' exists.".

### Chamadas HTTP ao Solr (via `requests`, credenciais da própria URL)

| Operação | Método | URL (base = `-u`) |
|---|---|---|
| Listar *configsets* | GET | `/solr/admin/configs?action=LIST&omitHeader=true&wt=json` (resposta `configSets`) |
| Apagar *configset* | POST | `/solr/admin/configs?action=DELETE&name=<configset>&wt=json` |
| Enviar *configset* | POST (multipart `file`, zip, `application/octet-stream`) | `/solr/admin/configs?action=UPLOAD&name=<configset>&wt=json` |
| Listar coleções | GET | `/solr/admin/collections?action=LIST&wt=json` (resposta `collections`) |
| Criar coleção | POST | `/solr/admin/collections?action=CREATE&name=<col>&collection.configName=<configset>&numShards=<s>&replicationFactor=<rf>&maxShardsPerNode=<ms>&wt=json` |
| Apagar coleção | POST | `/solr/admin/collections?action=DELETE&name=<col>&wt=json` |
| Contar docs (não usado no fluxo) | GET | `/solr/<col>/select?q=*:*` |
| Apagar dados (não usado) | POST XML | `/solr/<col>/update?commitWithin=1000&overwrite=true&wt=json` com `<delete><query>*:*</query></delete>` |

### ZooKeeper

- Host: o da URL; porta fixa `9983` (ZK embutido do Solr).
- Nó: `/security.json` — `create` se não existir, senão `set`; relido e impresso.

### Regex da URL

`URL_PATTERN = "https?://(([a-zA-Z0-9]+):([a-zA-Z0-9]+)@)?([a-zA-Z0-9.-]+)(:[0-9]{4})?"` → grupos: `(credenciais, usuario, senha, host, :porta)`.

### Derivação de nomes (por coleção `c`)

`parts = c.split("_")` → `COLLECTION_NAME = parts[0]_parts[1]`; `CONFIGSET_NAME = parts[1]_configset`; `CONFIGSET_PATH = ./solr/<parts[1]>_configset/conf`.

### Algoritmo do hash de senha

`salt = os.urandom(32)` (via `secrets.token_bytes`); `d = sha256(salt + senha_utf8)`; `d = sha256(d)`; credencial = `b64(d) + " " + b64(salt)`.

## `_docker/prod/wait-for-solr.sh`

```text
bash wait-for-solr.sh <SOLR_URL_BASE>
```

| Item | Valor |
|---|---|
| Sonda | `curl -s -o /dev/null -I "<URL>/solr/admin/collections?action=LIST" -w '%{http_code}'` |
| Intervalo | `sleep 1` entre tentativas |
| Limite declarado | `RETRY_LIMIT=60` (efetivo ~7 por comparação textual `<`) |
| Saída `1` | HTTP 200 — Solr **online** ("Solr server is up!") |
| Saída `2` | Esgotadas as tentativas — falha ("Solr connection failed.") |

## Bloco `## SOLR` de `_docker/dev/start-dev.sh` e `_docker/prod/start.sh`

Entradas (ambiente; padrões): `USE_SOLR=False`, `SOLR_URL=http://startdev1:startdev1@${COMPOSE_PROJECT_NAME}-solr:8983`, `SOLR_COLLECTIONS=${COMPOSE_PROJECT_NAME}_arq1,${COMPOSE_PROJECT_NAME}_arq2`, `NUM_SHARDS=1`, `RF=1`, `MAX_SHARDS_PER_NODE=1`, `IS_ZK_EMBEDDED=True`.

Saídas no console: "Solr configurations" + quadro (URL, COLLECTION, NUM_SHARDS, REPLICATION FACTOR, MAX SHARDS PER NODE, ASSUME ZK EMBEDDED); "running Solr script"; "Connecting to Solr..."; "Assuming embedded ZooKeeper instalation..."; "Solr is offline, not possible to connect."; "Solr support is not initialized.".

| Ambiente | Chamada de espera | Chamada do CLI |
|---|---|---|
| dev (`start-dev.sh`) | `/bin/bash _docker/prod/wait-for-solr.sh $SOLR_URL` | `python3 _docker/prod/solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE $ZK_EMBEDDED` |
| prod (`start.sh`) | `/bin/bash wait-for-solr.sh $SOLR_URL` | `python3 solr_cli.py -u … (idem)` |

Pré-condição de execução: `CHECK_SOLR_RETURN == 1`. O padrão de `SOLR_URL` em prod usa `startprod1:startprod1@`. A URL (com senha) é impressa no console.

Chaves de `.env` reescritas por `change_env_file`: `SOLR_COLLECTIONS = …` e `SOLR_URL = …` (em dev: `backend/.env`; em prod: `${ROOT_HOME}/backend_data/.env`).

## Arquivo `security.json` gerado

Ver estrutura em `../data-model.md` §4. Local: diretório corrente; ignorado por `.gitignore`.
