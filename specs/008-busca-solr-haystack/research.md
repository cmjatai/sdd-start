# Pesquisa: Infraestrutura de Busca Textual (Solr + Haystack)

Decisões técnicas inferidas do código, dos comentários e dos arquivos de configuração (engenharia reversa).

## Decisões

### D1. Apache Solr 9.7 em modo SolrCloud com ZooKeeper embutido
- **Decisão**: imagem `solr:9.7`, comando `bin/solr start -c -f` (cloud, em primeiro plano); ZooKeeper embutido na porta 9983.
- **Justificativa**: coleções com *configsets* enviados via API (`/solr/admin/configs?action=UPLOAD`) e `security.json` no ZooKeeper exigem modo cloud; o ZK embutido dispensa um serviço adicional (esqueleto de nó único).
- **Alternativas**: Solr standalone com *cores* (sem API de *configsets* nem `security.json` no ZK); ZooKeeper externo (mais um contêiner, desnecessário para o esqueleto); Elasticsearch/pgvector (descartado: o ecossistema Haystack + Solr é a escolha do projeto).

### D2. Fixar a versão 9.7
- **Decisão**: manter `solr:9.7` com comentário "validar mudança para 9.8 pois está causando erro".
- **Justificativa**: a 9.8 apresentou erro (não detalhado no repositório).
- **Alternativas**: tag `latest`/9.8 — rejeitadas até validação.

### D3. Duas coleções (`arq1`, `arq2`) com *configsets* próprios e duas conexões Haystack
- **Decisão**: `default` → 1ª coleção, `backendarq` → 2ª coleção; modelos escolhem a coleção por `MODELS_SOLR_*`.
- **Justificativa**: permitir esquemas distintos (campos de filtro extras em `arq2`: `conta_classe_*`, `tipo`, `ano`, `data`) e isolamento de índices; o nome `arq` vem do projeto de origem do esqueleto (arquivos/documentos).
- **Alternativas**: uma coleção única com campos opcionais (menos isolamento); *cores* por app.

### D4. Nome da coleção `<COMPOSE_PROJECT_NAME>_arqN` e *configset* derivado do sufixo
- **Decisão**: `solr_cli.py` quebra o nome por `_`: `COLLECTION_NAME=c[0]_c[1]`, `CONFIGSET_NAME=c[1]_configset`.
- **Justificativa**: várias instâncias no mesmo Solr/host sem colisão (princípio III) reutilizando o mesmo *configset* por sufixo.
- **Alternativas**: *configset* com o mesmo nome da coleção (duplicaria uploads); mapeamento explícito por parâmetro.

### D5. Indexação assíncrona via `celery-haystack` (fork)
- **Decisão**: `HAYSTACK_SIGNAL_PROCESSOR = backend.haystack.CelerySignalProcessor`, que estende o processador do fork `LeandroJatai/celery-haystack`, filtrando modelos em `enqueue_save`.
- **Justificativa**: constituição, princípio VI (indexação sempre assíncrona); o filtro evita enfileirar tarefas para todo `post_save` do projeto. Fork provavelmente por compatibilidade com Django/Celery recentes (suposição: o repositório não documenta o motivo).
- **Alternativas**: `RealtimeSignalProcessor` do Haystack (síncrono; há linha comentada em `solr.py`); `celery-haystack` do PyPI.

### D6. Roteador por modelo
- **Decisão**: `DefaultRouter` próprio escolhe coleção por `instance`/`index`/`models`; modelos não registrados → `None` (ignorados).
- **Justificativa**: impede que modelos não indexáveis atinjam o Solr; centraliza a decisão no registro de duas tuplas.

### D7. Validação de coleções no import
- **Decisão**: `ValueError` se as duas primeiras coleções estiverem vazias ou iguais.
- **Justificativa**: falhar cedo, com mensagem clara, em vez de rotear tudo para a mesma coleção.

### D8. `solr_cli.py` como utilitário de provisionamento idempotente
- **Decisão**: script Python (requests + kazoo) executado na partida; cria somente o que não existe; `-rc` recria; segurança aplicada pelo ZooKeeper.
- **Justificativa**: partida "do zero" com um comando (constituição, compatibilidade do esqueleto); o `security.json` precisa estar no ZK antes de o Solr bloquear usuários desconhecidos.
- **Alternativas**: `bin/solr auth enable` (exige acesso ao contêiner Solr); `solr-precreate` (não cria cloud/BasicAuth); Ansible/Helm.

### D9. Hash de senha no formato Solr
- **Decisão**: `base64(sha256(sha256(sal + senha)))` + `" " + base64(sal)`.
- **Justificativa**: formato exigido pelo `solr.BasicAuthPlugin` (Sha256AuthenticationProvider).

### D10. Credenciais embutidas na `SOLR_URL`
- **Decisão**: `http://usuario:senha@host:8983` serve simultaneamente a `requests`, `pysolr` (Haystack) e `curl`, e é a fonte do usuário/senha do `security.json`.
- **Justificativa**: uma única variável alimenta todos os consumidores.
- **Alternativas**: `SOLR_USER`/`SOLR_PASSWORD` separados no Django (hoje só existem no Compose).

### D11. Schema gerenciado a partir do `_default`
- **Decisão**: `managed-schema.xml` + `solrconfig.xml` do `_default` do Solr 9.x, com campos Haystack (`id`, `django_ct`, `django_id`, `text`, `last_update`) e `text_pt` com `brazilianStem`.
- **Justificativa**: busca em português (stopwords, stemming brasileiro, remoção de HTML); compatível com `haystack.backends.solr_backend` (`id`, `django_ct`, `django_id`).

### D12. Ajuste de URL para `localhost` em debug fora do contêiner
- **Decisão**: `DEBUG` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR` ⇒ host `localhost:8983`.
- **Justificativa**: rodar Django/pytest/IDE no host usando a porta publicada pelo Compose de dev. O mesmo critério é usado em `zasyncs.py` (Redis) e `project.py` (banco).

## Particularidades, dívidas técnicas e riscos observados

Legenda de recomendação: **Replicar** = reproduzir para fidelidade (estado atual); **Corrigir** = o que seria recomendado a quem quiser melhorar. Para fidelidade, o estado atual é **replicar**.

| # | Observação (confirmada no código) | Risco | Recomendação |
|---|---|---|---|
| 1 | Nenhum modelo em `MODELS_SOLR_DEFAULT`/`MODELS_SOLR_BACKENDARQ` (tuplas vazias) e inexistência de `search_indexes.py`: nada é indexado; só infraestrutura. | Esperar busca funcional no esqueleto | **Replicar** (é o escopo). Derivados registram modelos e criam `SearchIndex`. |
| 2 | `backend/haystack.py` levanta `ValueError` se as duas primeiras coleções de `SOLR_COLLECTIONS` forem iguais ou vazias (ex.: `a,a`, `a,`, `,b`), e é importado só via `HAYSTACK_SIGNAL_PROCESSOR`. Com **uma** coleção (ou string vazia) o erro real é `IndexError` (`split(",")[1]`), levantado antes, já em `backend/settings/solr.py` ao carregar as configurações (e de novo em `haystack.py`), portanto a mensagem do `ValueError` não aparece nesse caso. | Mensagem enganosa | **Replicar**; recomendação: validar o tamanho da lista antes de indexar. |
| 3 | **Alias × chave de conexão**: o roteador devolve o nome da *coleção* (`startdev1_arq1`/`_arq2`), mas `HAYSTACK_CONNECTIONS` tem as chaves `default` e `backendarq`. Verificado em execução: `connection_router.for_read()` → `startdev1_arq1`; `connections["startdev1_arq1"]` e `SearchQuerySet()` levantam `ImproperlyConfigured: The key 'startdev1_arq1' isn't an available connection`. | Qualquer busca/indexação real falha até alinhar chaves e aliases | **Replicar** hoje (latente: nada usa Haystack). **Corrigir** antes de registrar o primeiro modelo: o roteador deve devolver `"default"`/`"backendarq"` (ou as chaves de `HAYSTACK_CONNECTIONS` devem ser os nomes das coleções). |
| 4 | `from haystack.constants import DEFAULT_ALIAS` é sobrescrito por `DEFAULT_ALIAS = settings.SOLR_COLLECTIONS.split(",")[0]`; as classes `CelerySignalProcessor` e `DefaultRouter` reusam o nome da classe base importada (sombreamento). | Confusão de leitura; o import original é inútil | **Replicar** (funciona); recomendável renomear. |
| 5 | `wait-for-solr.sh` retorna **1 quando online** e **2 quando falha** (contra-intuitivo); `start.sh`/`start-dev.sh` só rodam `solr_cli.py` se retorno `== 1`. | Quem reutilizar o script e testar `$? == 0` nunca provisiona | **Replicar** (contrato interno); documentar. |
| 6 | Laço do `wait-for-solr.sh` usa `[[ $RETRY_COUNT < $RETRY_LIMIT ]]` (comparação de **texto**): para na 7ª tentativa (`"7" > "60"`), não em 60 s como o comentário diz. Verificado em Bash. | Solr lento (>~7 s) é considerado offline e as coleções não são criadas naquela partida | **Replicar**; **Corrigir** com `-lt`. |
| 7 | `SOLR_USER`/`SOLR_PASSWORD` não existem no `.env`; o Compose usa `${SOLR_USER:-startdev1}` (prod `startprod1`) e a `SOLR_URL` embute `usuario:senha@host`. Senha em texto na URL aparece em variáveis de ambiente, nos `echo "URL: $SOLR_URL"` dos scripts (log do contêiner) e no `.env`. | Vazamento de credencial em logs; padrões fracos | **Replicar**; **Corrigir** mascarando a URL nos logs e exigindo senha forte em produção. |
| 8 | `URL_PATTERN` exige usuário e senha alfanuméricos (`[a-zA-Z0-9]+`) e porta de exatamente 4 dígitos; caracteres especiais na senha (`_`, `@`, `%`, `-`) quebram o casamento: `setup_embedded_zk` aborta com `-1`. Verificado: `a_b:pw@h:8983` → sem usuário/senha. | Senhas fortes não suportadas | **Replicar**; **Corrigir** com `urllib.parse.urlsplit` + `unquote`. |
| 9 | `security.json` é escrito no diretório corrente (raiz), contém hash+sal da senha, é ignorado pelo git (`.gitignore`) mas permanece no disco e na imagem/volume montado. | Hash exposto localmente | **Replicar**; recomendável removê-lo após o upload. |
| 10 | O `security.json` é regenerado a cada partida (novo sal, mesma senha) e sobrescreve `/security.json` no ZooKeeper; a escrita é feita direto no ZK (não passa pela autenticação do Solr), então trocar a senha na `SOLR_URL` e reiniciar o `app` funciona sem passo extra. | Baixo | **Replicar**. |
| 11 | O primeiro `curl` do `wait-for-solr.sh` e as chamadas `requests` usam a URL com credenciais; antes de o `security.json` existir o Solr aceita sem autenticação; depois exige. Ordem: espera → ZK/`security.json` → cria coleções (já autenticadas pela URL). | Condição de corrida mínima se o Solr reiniciar entre as etapas | **Replicar**. |
| 12 | `SolrClient.COLLECTIONS = []` é atributo **de classe** (mutável compartilhado). | Duplicaria itens se o cliente fosse instanciado mais de uma vez no mesmo processo | **Replicar** (uso único por processo). |
| 13 | `SolrClient` divide o nome da coleção por `_`: um `COMPOSE_PROJECT_NAME` com `_` (ex.: `meu_proj_arq1`) gera `COLLECTION_NAME=meu_proj` e `CONFIGSET_NAME=proj_configset` (quebra). | Instâncias com `_` no nome do projeto não funcionam | **Replicar**; **Corrigir** usando `rsplit("_", 1)`. |
| 14 | Código morto/não usado em `solr_cli.py`: bloco `if False:` (reindexação com `rebuild_index`), constantes `STATUS_COLLECTION`, `STATUS_CORE`, `EXISTS_COLLECTION`, `OPTIMIZE_COLLECTION`, método `delete_index_data`, import `subprocess`. Mensagem "Collection '%s' exists." imprime o dicionário inteiro. `print("Error deleting collection '%s'", c)` usa vírgula em vez de `%`. | Ruído | **Replicar**; limpar é opcional. |
| 15 | `maybe_upload_configset` não trata falha do `GET configs` (se `configsets` não foi definido por exceção, ocorreria `NameError`/`UnboundLocalError`); respostas de upload/criação não validam código HTTP do upload. | Falha ruidosa ou silenciosa | **Replicar**; **Corrigir** com `raise_for_status`. |
| 16 | `requests` é dependência transitiva (não declarada em `pyproject.toml`); `solr_cli.py` roda no mesmo ambiente Poetry do app. | Quebra se a dependência transitiva sumir | **Corrigir** declarando `requests`. |
| 17 | `USE_SOLR` é definida em `solr.py` mas nenhum código Django a consulta; o liga/desliga real é a variável de ambiente lida pelos scripts Bash (`True`/`true`). Os Compose fixam `USE_SOLR: 'True'`. Com Solr desligado, `HAYSTACK_*` continuam configurados e o processador de sinais continua carregado (e levantando `ValueError` se `SOLR_COLLECTIONS` for inválida). | Interruptor enganoso | **Replicar**. |
| 18 | O default de `SOLR_COLLECTIONS` no Django é `backend_arq1,backend_arq2`, enquanto os scripts/`.env` usam `<COMPOSE_PROJECT_NAME>_arq1,…` (ex.: `startdev1_arq1`). | Divergência se o `.env` não existir | **Replicar**. |
| 19 | Os dois `solrconfig.xml` são quase idênticos (diferem em `spellchecker.field` e `hl.fragsize`); `arq1` usa `text`/512 e `arq2` usa `_text_`/100. O campo `_text_` não é armazenado e não há `copyField` ativo para ele (`<copyField source="*" dest="_text_"/>` comentado): o corretor ortográfico de `arq2` provavelmente não terá termos em `_text_`. O `df` dos *handlers* é `text` em ambos (não `_text_`). | Spellcheck de `arq2` sem efeito | **Replicar**; **Corrigir** habilitando `copyField` ou usando `text`. |
| 20 | Schema `arq1` tem `at` (pint, padrão 0) e comentário de `ano`; `arq2` tem `conta_classe_*`, `tipo`, `ano`, `data` sem `at`; campos `conta_classe_*` refletem o domínio contábil/arquivístico de origem e não têm uso no esqueleto. O `solrconfig.xml` mantém `add-unknown-fields-to-the-schema` (campos desconhecidos são criados automaticamente — *schemaless*). | Schema pode divergir do declarado | **Replicar**. |
| 21 | `HAYSTACK_CONNECTIONS` constrói URL com `SOLR_URL` já truncada (`split("@")[0] + "@localhost:8983"`): se a `SOLR_URL` não contiver `@` (sem credenciais), o resultado vira `http://solr:8983@localhost:8983` (host inválido). | Quebra em debug no host sem credenciais | **Replicar**; **Corrigir** com `urlsplit`. |
| 22 | Portas 8983/9983 abertas no host em dev; o ZooKeeper embutido (9983) **não** tem autenticação própria (o `security.json` protege o Solr, não o ZK). Em prod nenhuma é publicada. | Exposição local em dev | **Replicar** em dev. |
| 23 | `restart: on-failure` (dev) e `always` (prod); em prod o `app` usa `depends_on: solr: condition: service_started` (sem *healthcheck*), por isso o `wait-for-solr.sh` existe. | Dependência de janela curta (item 6) | **Replicar**; recomendável *healthcheck*. |
| 24 | Mensagens de console de `solr_cli.py`/scripts misturam inglês e português. | Princípio VII | **Replicar**. |
| 25 | O diretório `solr/` tem 2 × ~183 KB de configurações quase duplicadas, com um `lang/stopwords_{en,es,pt}.txt` herdado do Solr; `stopwords.txt`, `synonyms.txt` e `protwords.txt` são os modelos padrão (só comentários de licença). | Manutenção duplicada | **Replicar**. |
