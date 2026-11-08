# Contrato: Serviço `solr` nos Docker Compose (dev e prod)

O restante dos arquivos Compose (serviços `app`, `db`, `redis`, `front`, redes) é coberto por `010-docker-desenvolvimento` e `011-docker-producao`; aqui só o necessário ao Solr.

## Serviço `solr`

| Item | Dev (`_docker/dev/docker-compose.yaml`) | Prod (`_docker/prod/docker-compose.yaml`) |
|---|---|---|
| `container_name` | `${COMPOSE_PROJECT_NAME:-startdev1}-solr` | `${COMPOSE_PROJECT_NAME:-startprod1}-solr` |
| `image` | `solr:9.7` — comentário `# validar mudança para 9.8 pois está causando erro` | idem |
| `restart` | `on-failure` | `always` |
| `command` | `bin/solr start -c -f` | idem |
| `volumes` | `solr9_data:/var/solr`; `solr9_configsets:/opt/solr/server/solr/configsets` | idem |
| `ports` | `8983:8983` (HTTP/Admin UI), `9983:9983` (ZooKeeper embutido) | **comentadas** (`#ports: - "8983:8983"`) — só rede interna |
| `networks` | `appdev-net` | `app-net` |

Volumes nomeados declarados no bloco `volumes:` do arquivo: `solr9_data`, `solr9_configsets` (junto a `redis_data`, `dbdata` etc.).

## Variáveis do serviço `app` relacionadas ao Solr

| Variável | Dev | Prod |
|---|---|---|
| `USE_SOLR` | `'True'` | `'True'` |
| `SOLR_COLLECTIONS` | `${COMPOSE_PROJECT_NAME:-startdev1}_arq1,${COMPOSE_PROJECT_NAME:-startdev1}_arq2` | `${COMPOSE_PROJECT_NAME:-startprod1}_arq1,…_arq2` |
| `SOLR_URL` | `http://${SOLR_USER:-startdev1}:${SOLR_PASSWORD:-startdev1}@${COMPOSE_PROJECT_NAME:-startdev1}-solr:8983` | `http://${SOLR_USER:-startprod1}:${SOLR_PASSWORD:-startprod1}@${COMPOSE_PROJECT_NAME:-startprod1}-solr:8983` |
| `IS_ZK_EMBEDDED` | `'True'` | `'True'` |
| `depends_on` | `front`, `db`, `redis`, `solr` | `db` (`service_started`), `redis` (`service_healthy`), `solr` (`service_started`) |

## Portas

| Porta | Protocolo | Uso | Publicada em |
|---|---|---|---|
| 8983 | HTTP | API/Admin do Solr (`/solr/...`) | dev apenas |
| 9983 | ZooKeeper | ZK embutido (`/security.json`) — usado por `solr_cli.py` via `kazoo` (dentro da rede Compose acessa-se `<projeto>-solr:9983`) | dev apenas |

## Arquivos copiados para a imagem de produção (`_docker/prod/Dockerfile`)

- `ADD solr ${HOME}/solr` (pasta dos *configsets*);
- `COPY _docker/prod/wait-for-solr.sh ${HOME}` e `COPY _docker/prod/solr_cli.py ${HOME}`; `chmod +x ${HOME}/wait-for-solr.sh`.

Em dev, o código é montado como volume (`../../.:/var/project/backend`), portanto `solr/` e `_docker/prod/*` já estão disponíveis na raiz do projeto.

## Endereços de acesso (README)

`localhost:8983` (Solr) e `localhost:9983` (ZooKeeper embutido) em dev.
