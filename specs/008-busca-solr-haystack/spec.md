# Especificação da Funcionalidade: Infraestrutura de Busca Textual (Solr + Haystack)

**Branch da Funcionalidade**: `008-busca-solr-haystack`
**Criado em**: 2026-11-08
**Status**: Implementado (engenharia reversa)
**Entrada**: "Engenharia reversa do código existente: infraestrutura de busca textual com Apache Solr 9.7 (SolrCloud, ZooKeeper embutido) e Django Haystack — `backend/settings/solr.py`, `backend/haystack.py`, apps `haystack`/`celery_haystack`, configsets `solr/arq1_configset` e `solr/arq2_configset`, `_docker/prod/solr_cli.py`, `_docker/prod/wait-for-solr.sh`, blocos SOLR de `_docker/dev/start-dev.sh` e `_docker/prod/start.sh` e serviço `solr` dos compose de dev e prod."

> **Escopo importante**: o esqueleto entrega **somente a infraestrutura** de busca. Nenhum modelo está registrado para indexação (`MODELS_SOLR_DEFAULT` e `MODELS_SOLR_BACKENDARQ` são tuplas vazias) e não existe nenhum `search_indexes.py`. Portanto, **nada é indexado** e nenhuma tela/endpoint de busca existe. Quem derivar o projeto registra seus modelos e índices sobre esta base.

**Pré-requisitos (features anteriores)**: `001-fundacao-projeto-django` (configuração modular por `python-decouple`, `backend/settings/*`, Celery/Redis em `zasyncs.py`). O desenho dos contêineres (`010-docker-desenvolvimento`, `011-docker-producao`) cobre o restante do Docker; aqui só o serviço `solr` e o bloco SOLR dos scripts de partida.

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Subir o Solr junto com o ambiente e ter as coleções prontas (Prioridade: P1)

Como pessoa desenvolvedora/operadora, quero que, ao subir o ambiente Docker (dev ou prod) com `USE_SOLR` ligado, o Solr seja iniciado, o aplicativo espere por ele e as duas coleções (`<projeto>_arq1` e `<projeto>_arq2`) sejam criadas automaticamente com seus *configsets*, sem passos manuais.

**Por que esta prioridade**: sem Solr no ar e com coleções criadas, nenhuma indexação ou busca futura é possível; é o requisito mínimo da "infraestrutura de busca".

**Teste Independente**: subir `solr` + `app` com `USE_SOLR=True`; consultar `GET <SOLR_URL>/solr/admin/collections?action=LIST` e verificar que as duas coleções existem, cada uma com o schema do seu *configset*.

**Cenários de Aceitação**:

1. **Dado** `USE_SOLR=True` e o contêiner Solr ainda sem coleções, **quando** o script de partida do `app` executa o bloco SOLR, **então** ele aguarda o Solr responder, envia (upload) os *configsets* `arq1_configset` e `arq2_configset` e cria as coleções `<COMPOSE_PROJECT_NAME>_arq1` e `<COMPOSE_PROJECT_NAME>_arq2`.
2. **Dado** que as coleções já existem, **quando** o `app` reinicia, **então** o script NÃO recria as coleções nem reenvia *configsets* já presentes e informa que a coleção existe.
3. **Dado** `USE_SOLR` ausente ou diferente de `True`/`true`, **quando** o `app` inicia, **então** o bloco SOLR é ignorado e imprime "Solr support is not initialized.".
4. **Dado** que o Solr não responde HTTP 200 dentro da janela de espera, **quando** o bloco SOLR roda, **então** imprime "Solr is offline, not possible to connect." e o `app` continua a subir normalmente (sem abortar).
5. **Dado** `NUM_SHARDS`, `RF` e `MAX_SHARDS_PER_NODE` definidos, **quando** as coleções são criadas, **então** esses valores são usados como número de shards, fator de replicação e máximo de shards por nó (padrão 1/1/1).

---

### História de Usuário 2 - Proteger o Solr com autenticação básica (Prioridade: P1)

Como operador, quero que o Solr seja protegido por autenticação básica gerada automaticamente a partir das credenciais embutidas na `SOLR_URL`, sem que a senha apareça em arquivos versionados.

**Por que esta prioridade**: o Solr expõe a API administrativa (inclusive criar/apagar coleções); a constituição exige autenticação básica em produção.

**Teste Independente**: após o start com `IS_ZK_EMBEDDED=True`, uma requisição a `/solr/admin/collections?action=LIST` **sem** credenciais retorna 401 e **com** `usuário:senha` retorna 200.

**Cenários de Aceitação**:

1. **Dado** `SOLR_URL=http://usuario:senha@host:8983` e `IS_ZK_EMBEDDED=True`, **quando** `solr_cli.py` roda com `--embedded_zk`, **então** gera `security.json` (BasicAuth, `blockUnknown: true`, usuário com papel `admin`, hash sha256 com sal no formato Solr) e o grava em `/security.json` no ZooKeeper embutido (porta 9983).
2. **Dado** que `/security.json` já existe no ZooKeeper, **quando** o script roda de novo, **então** o nó é atualizado (`set`) em vez de criado, e a senha continua a mesma (novo sal).
3. **Dado** uma `SOLR_URL` sem usuário/senha ou fora do padrão, **quando** o script roda com `--embedded_zk`, **então** aborta com código de saída `-1` e mensagem explicando o formato exigido.
4. **Dado** `IS_ZK_EMBEDDED` diferente de `True`/`true`, **quando** o script roda, **então** NÃO aplica segurança (apenas cria as coleções).

---

### História de Usuário 3 - Configuração Django/Haystack com duas coleções roteadas (Prioridade: P1)

Como desenvolvedor da aplicação, quero que o Django já esteja configurado com Haystack, `celery-haystack` e duas conexões Solr (`default` e `backendarq`), um roteador que decide a coleção por modelo e um processador de sinais assíncrono, de modo que registrar um modelo (e escrever seu `SearchIndex`) seja o único passo para indexá-lo.

**Por que esta prioridade**: é a base de código sobre a qual toda indexação futura se apoia; também falha cedo (na carga do processador de sinais) quando a configuração das coleções é inválida.

**Teste Independente**: com `SOLR_COLLECTIONS=a_arq1,a_arq2`, importar `backend.haystack` funciona e `DefaultRouter().for_write()` retorna `a_arq1`; com `SOLR_COLLECTIONS=a_arq1,a_arq1` a importação levanta `ValueError`; com uma só coleção, as configurações já falham com `IndexError`.

**Cenários de Aceitação**:

1. **Dado** `SOLR_COLLECTIONS` com duas coleções distintas, **quando** o Django inicia, **então** `HAYSTACK_CONNECTIONS` possui as conexões `default` (primeira coleção) e `backendarq` (segunda coleção), cada uma com `BATCH_SIZE=1000` e `TIMEOUT=600`.
2. **Dado** `SOLR_COLLECTIONS` cujas duas primeiras coleções sejam iguais ou vazias (ex.: `a,a` ou `a,`), **quando** `backend.haystack` é importado (ao instanciar o processador de sinais), **então** é levantado `ValueError` com a mensagem "SOLR_COLLECTIONS must contain at least two distinct collections…". Com uma só coleção ou string vazia, o carregamento de `backend/settings/solr.py` já falha com `IndexError` (que antecede a validação).
3. **Dado** que nenhum modelo está registrado em `MODELS_SOLR_*`, **quando** qualquer modelo é salvo ou excluído, **então** nenhuma tarefa de indexação é enfileirada e nenhuma conexão com o Solr é aberta.
4. **Dado** um modelo adicionado a `MODELS_SOLR_DEFAULT` (ou `MODELS_SOLR_BACKENDARQ`) com índice `CelerySearchIndex`, **quando** uma instância é salva, **então** uma tarefa `update` é enfileirada no Celery (após o *commit* da transação); ao excluir, uma tarefa `delete`.

---

### História de Usuário 4 - Schemas gerenciados prontos para o domínio de documentos (Prioridade: P2)

Como desenvolvedor, quero *configsets* versionados no repositório com campos básicos do Haystack e análise de texto em português, para que a indexação futura use stemming/stopwords pt-BR e suporte campos de filtro (na coleção `arq2`).

**Por que esta prioridade**: sem schema adequado a busca em português é ruim, mas pode ser ajustado depois de a infraestrutura estar de pé.

**Teste Independente**: após criar as coleções, `GET /solr/<colecao>/schema/fields` lista os campos esperados de cada coleção.

**Cenários de Aceitação**:

1. **Dado** a coleção `*_arq1`, **quando** o schema é consultado, **então** existem `id` (chave única), `_version_`, `_text_`, `django_ct`, `django_id`, `last_update`, `text` (tipo `text_pt`) e `at` (inteiro, padrão 0).
2. **Dado** a coleção `*_arq2`, **quando** o schema é consultado, **então** existem os mesmos campos básicos **exceto `at`**, mais `conta_classe_logica`, `conta_classe_estrutural`, `tipo` (strings), `ano` (inteiro) e `data` (data).
3. **Dado** um texto em português enviado ao campo `text`, **quando** indexado, **então** passa por remoção de HTML, tokenização padrão, minúsculas, remoção de *stopwords* pt (`lang/stopwords_pt.txt`) e *stemmer* `brazilianStem`.
4. **Dado** o handler `/select`, **quando** uma consulta é feita sem parâmetros, **então** usa `edismax`, `df=text`, `q.op=AND`, `rows=50`.

---

### História de Usuário 5 - Ambiente de desenvolvimento acessível do host (Prioridade: P3)

Como desenvolvedor que roda o Django **fora** do contêiner (IDE no host), quero que a URL do Solr aponte automaticamente para `localhost:8983` quando `DEBUG` está ligado, para usar o Solr do Compose sem editar o `.env`.

**Por que esta prioridade**: conveniência de desenvolvimento; não afeta o funcionamento no contêiner.

**Teste Independente**: com `DEBUG=True` e `FOLDER_DEBUG_CONTAINER` diferente da pasta do projeto, `settings.HAYSTACK_CONNECTIONS["default"]["URL"]` começa com `http://<usuario>:<senha>@localhost:8983/solr/`.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR` (execução no host), **quando** as configurações carregam, **então** `SOLR_URL` mantém `esquema://usuario:senha` e troca o host por `localhost:8983`.
2. **Dado** execução dentro do contêiner (`FOLDER_DEBUG_CONTAINER == PROJECT_DIR`) ou `DEBUG=False`, **quando** carregam, **então** `SOLR_URL` permanece como definida (host do serviço Compose).
3. **Dado** o Compose de dev, **quando** o Solr sobe, **então** as portas `8983` (HTTP) e `9983` (ZooKeeper embutido) ficam publicadas no host; em prod, nenhuma é publicada.

---

### Casos de Borda

- **Nada é indexado no esqueleto**: `MODELS_SOLR_DEFAULT = ()` e `MODELS_SOLR_BACKENDARQ = ()`; sem `search_indexes.py`. `CelerySignalProcessor.enqueue_save` retorna antes de enfileirar para qualquer modelo; `enqueue_delete` consulta o roteador, que devolve `None` para modelos não registrados (nenhuma tarefa é criada).
- **`ValueError` na importação**: `backend/haystack.py` valida as coleções no *import*; como só é importado via `HAYSTACK_SIGNAL_PROCESSOR`, o erro aparece quando o Haystack instancia o processador de sinais (início do Django com `haystack` instalado), não ao ler as configurações. Só cobre coleções iguais/vazias; com uma única coleção o `IndexError` de `split(",")[1]` ocorre antes (em `solr.py`).
- **Nome das coleções e *configset***: o nome é `<COMPOSE_PROJECT_NAME>_arq1` / `_arq2`; o *configset* é derivado do **segundo segmento** do nome separado por `_` (`arq1_configset`). Um `COMPOSE_PROJECT_NAME` contendo `_` quebra a derivação (o script usa só os dois primeiros segmentos).
- **Código de retorno invertido de `wait-for-solr.sh`**: retorna `1` quando o Solr está **online** e `2` quando falha; os scripts de partida só executam `solr_cli.py` se o retorno for `1`.
- **Janela de espera real**: o laço do `wait-for-solr.sh` compara com `[[ $RETRY_COUNT < $RETRY_LIMIT ]]` (comparação lexicográfica de texto), portanto na prática faz cerca de 7 tentativas (~7 s), e não 60 s.
- **Credenciais na URL**: `SOLR_USER` não é definida no `.env`; o Compose usa `${SOLR_USER:-startdev1}` / `${SOLR_PASSWORD:-startdev1}` (prod: `startprod1`) e a `SOLR_URL` embute `usuario:senha@host`. A regex `URL_PATTERN` do `solr_cli.py` só aceita usuário e senha **alfanuméricos** (caracteres como `_`, `@`, `%` fazem o casamento falhar e o script aborta com `-1` se `--embedded_zk`).
- **Execução no host**: a troca para `localhost:8983` descarta o host original e fixa a porta `8983`.
- **`security.json`** é gerado na raiz do diretório de execução e é ignorado pelo git (`.gitignore`); contém hash, não a senha em claro.
- **Versão do Solr**: a imagem é `solr:9.7`; há comentário no Compose "validar mudança para 9.8 pois está causando erro" — NÃO atualizar sem validar.
- **Persistência**: dados em `solr9_data` (`/var/solr`) e *configsets* em `solr9_configsets`; remover os volumes recria tudo do zero na próxima partida.
- **Dependência do roteador**: o roteador devolve o nome da **coleção** (ex.: `startdev1_arq1`) e não as chaves `default`/`backendarq` de `HAYSTACK_CONNECTIONS`; por isso, hoje, qualquer consulta de leitura via `SearchQuerySet()` e qualquer escrita para um modelo registrado resultaria em `ImproperlyConfigured` (chave inexistente). Latente porque nada usa busca ainda (ver `research.md`).

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE ler `USE_SOLR` (bool, padrão `False`), `SOLR_URL` (padrão `http://startdev1:startdev1@startdev1-solr:8983`) e `SOLR_COLLECTIONS` (padrão `backend_arq1,backend_arq2`) por `python-decouple`, em `backend/settings/solr.py`, reexportados por `backend/settings/project.py`.
- **FR-002**: O sistema DEVE definir `HAYSTACK_CONNECTIONS` com as conexões `default` (URL `<SOLR_URL>/solr/<1ª coleção>`) e `backendarq` (URL `<SOLR_URL>/solr/<2ª coleção>`), motor `haystack.backends.solr_backend.SolrEngine`, `BATCH_SIZE=1000`, `TIMEOUT=600` e `EXCLUDED_INDEXES` vazio.
- **FR-003**: O sistema DEVE definir `HAYSTACK_SIGNAL_PROCESSOR = "backend.haystack.CelerySignalProcessor"`, `HAYSTACK_ROUTERS = ["backend.haystack.DefaultRouter"]` e `HAYSTACK_ITERATOR_LOAD_PER_QUERY = 100`.
- **FR-004**: Com `DEBUG=True` e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR`, o sistema DEVE reescrever `SOLR_URL` para `<esquema://usuario:senha>@localhost:8983`.
- **FR-005**: Os apps `haystack` e `celery_haystack` DEVEM estar em `INSTALLED_APPS` (`DJANGO_THIRD_PARTY_APPS` de `backend/settings/apps.py`), e o logger `haystack` DEVE estar configurado em `backend/settings/logs.py`.
- **FR-006**: As dependências `django-haystack` (^3.4.0), `celery-haystack` (fork `https://github.com/LeandroJatai/celery-haystack.git`, via git) e `pysolr` (^3.11.0) DEVEM constar no `pyproject.toml`; `kazoo` (^2.11.0) é exigido pelo `solr_cli.py`.
- **FR-007**: `backend/haystack.py` DEVE calcular `DEFAULT_ALIAS` e `BACKENDARQ_ALIAS` a partir das duas primeiras coleções de `SOLR_COLLECTIONS` e DEVE levantar `ValueError` se alguma estiver vazia ou se forem iguais.
- **FR-008**: `backend/haystack.py` DEVE expor `MODELS_SOLR_DEFAULT` e `MODELS_SOLR_BACKENDARQ` (tuplas, vazias no esqueleto) como ponto único de registro de modelos indexáveis.
- **FR-009**: `CelerySignalProcessor.enqueue_save` DEVE enfileirar a ação `update` somente para modelos presentes em `MODELS_SOLR_BACKENDARQ + MODELS_SOLR_DEFAULT`; `enqueue_delete` DEVE enfileirar `delete` delegando ao roteador a decisão.
- **FR-010**: `DefaultRouter` (`for_write`, `for_read`, `for_rw`) DEVE devolver o alias da coleção `backendarq` para modelos de `MODELS_SOLR_BACKENDARQ`, o alias padrão para os de `MODELS_SOLR_DEFAULT` e para chamadas sem *hints*, e `None` para modelos não registrados.
- **FR-011**: Os *configsets* `solr/arq1_configset/conf` e `solr/arq2_configset/conf` DEVEM conter `managed-schema.xml`, `solrconfig.xml`, `protwords.txt`, `stopwords.txt`, `synonyms.txt` e `lang/stopwords_{en,es,pt}.txt`.
- **FR-012**: O schema de ambas as coleções DEVE declarar `id` (string, obrigatório, chave única), `_version_` (plong), `_text_` (text_general, multivalorado, não armazenado), `django_ct`, `django_id` (string), `last_update` (pdate, padrão `NOW`) e `text` (`text_pt`, armazenado).
- **FR-013**: O schema de `arq1` DEVE declarar adicionalmente `at` (pint, padrão `0`); o de `arq2` NÃO DEVE declarar `at` e DEVE declarar `conta_classe_logica`, `conta_classe_estrutural`, `tipo` (string, docValues), `ano` (pint) e `data` (pdate).
- **FR-014**: O tipo `text_pt` DEVE aplicar `htmlStrip`, tokenizador `standard`, `lowercase`, `stop` com `lang/stopwords_pt.txt` (formato snowball) e `brazilianStem`.
- **FR-015**: Os `solrconfig.xml` DEVEM diferir somente em: `arq2` usa `_text_` como campo do corretor ortográfico (`spellchecker`, DirectSolrSpellChecker) e `hl.fragsize=100` no fragmentador `gap`; `arq1` usa `text` e `hl.fragsize=512`. Ambos mantêm `/select` com `df=text`, `edismax`, `q.op=AND`, `rows=50`.
- **FR-016**: `_docker/prod/solr_cli.py` DEVE aceitar `-u URL` e `-c COLLECTIONS` (obrigatórios), `-rc` (recriar), `-s`, `-rf`, `-ms` (inteiros, padrão 1) e `--embedded_zk`.
- **FR-017**: `solr_cli.py` DEVE, para cada coleção inexistente, enviar o *configset* (zip em memória do diretório `./solr/<sufixo>_configset/conf`) se ainda não existir no Solr (ou se `FORCE`) e criar a coleção via API Collections com `numShards`, `replicationFactor` e `maxShardsPerNode`.
- **FR-018**: `solr_cli.py` DEVE, com `-rc`, apagar as coleções indicadas (`*` apaga todas) antes de recriá-las e reenviar seus *configsets*.
- **FR-019**: Com `--embedded_zk`, `solr_cli.py` DEVE extrair usuário/senha/host da URL com `URL_PATTERN`, gerar `security.json` (BasicAuth + RuleBasedAuthorization, `security-edit` somente para `admin`, `blockUnknown: true`, `realm: "Solr Login"`) e enviá-lo ao ZooKeeper `<host>:9983` como `/security.json` (criar ou atualizar), saindo com `-1` em qualquer falha.
- **FR-020**: O hash de senha DEVE seguir o padrão Solr: `base64(sha256(sha256(sal + senha)))` e `base64(sal)` com sal aleatório de 32 bytes, gravado como `"<hash> <sal>"`.
- **FR-021**: `_docker/prod/wait-for-solr.sh <SOLR_URL>` DEVE sondar `GET <SOLR_URL>/solr/admin/collections?action=LIST` (HEAD via `curl -I`, 1 s entre tentativas), encerrar com código `1` ao obter HTTP 200 e com `2` ao esgotar as tentativas.
- **FR-022**: Os scripts `_docker/dev/start-dev.sh` e `_docker/prod/start.sh` DEVEM, quando `USE_SOLR` for `True`/`true`, imprimir a configuração (URL, coleções, `NUM_SHARDS`, `RF`, `MAX_SHARDS_PER_NODE`, `IS_ZK_EMBEDDED`), aguardar o Solr e, se o retorno for `1`, executar `solr_cli.py -u $SOLR_URL -c $SOLR_COLLECTIONS -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE [--embedded_zk]`; padrões: `NUM_SHARDS=1`, `RF=1`, `MAX_SHARDS_PER_NODE=1`, `IS_ZK_EMBEDDED=True`, `USE_SOLR=False`.
- **FR-023**: Os scripts de partida DEVEM manter no `.env` do projeto (`backend/.env` em dev; `backend_data/.env` em prod) as chaves `SOLR_COLLECTIONS` e `SOLR_URL` coerentes com `COMPOSE_PROJECT_NAME`.
- **FR-024**: Os arquivos Compose de dev e prod DEVEM declarar o serviço `solr` com imagem `solr:9.7`, comando `bin/solr start -c -f`, contêiner `${COMPOSE_PROJECT_NAME:-<padrão>}-solr`, volumes nomeados `solr9_data:/var/solr` e `solr9_configsets:/opt/solr/server/solr/configsets`, e o serviço `app` DEVE depender dele e receber `USE_SOLR=True`, `SOLR_COLLECTIONS`, `SOLR_URL` (com `${SOLR_USER}`/`${SOLR_PASSWORD}`) e `IS_ZK_EMBEDDED=True`.
- **FR-025**: Em dev, o Compose DEVE publicar as portas `8983:8983` e `9983:9983` do Solr; em prod, as portas NÃO DEVEM ser publicadas (acesso apenas pela rede interna `app-net`).
- **FR-026**: O `security.json` gerado NÃO DEVE ser versionado (entrada no `.gitignore`).
- **FR-027**: A indexação NÃO DEVE ser síncrona: o processador de sinais DEVE usar `celery-haystack` (tarefa Celery, `transaction.on_commit`), conforme o princípio VI da constituição.

### Entidades-Chave

- **Coleção Solr** (`<COMPOSE_PROJECT_NAME>_arq1` e `_arq2`): índice de busca; `arq1` é a conexão `default`, `arq2` é a conexão `backendarq`.
- **Configset**: conjunto de arquivos de configuração (`managed-schema.xml`, `solrconfig.xml`, stopwords, synonyms, protwords) enviado ao Solr e compartilhado por uma coleção.
- **Documento indexado**: campos `id`, `django_ct`, `django_id`, `text`, `last_update` (+ específicos); hoje inexistente (nada é indexado).
- **Registro de modelos** (`MODELS_SOLR_DEFAULT`, `MODELS_SOLR_BACKENDARQ`): tuplas de classes de modelo que escolhem a coleção.
- **Credencial Solr** (`security.json`): usuário/hash/sal derivados da `SOLR_URL`.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Com `USE_SOLR=True`, após a partida do `app`, `collections?action=LIST` lista exatamente as duas coleções `<projeto>_arq1` e `<projeto>_arq2` em até o tempo de partida do Solr (sem intervenção manual).
- **SC-002**: Reiniciar o `app` 3 vezes seguidas mantém as duas coleções e NÃO duplica nem apaga dados (0 recriações sem `-rc`).
- **SC-003**: Com `IS_ZK_EMBEDDED=True`, 100 % das requisições ao Solr sem credenciais recebem 401 após o primeiro start e 100 % das com credenciais corretas recebem 200.
- **SC-004**: `import backend.haystack` com `SOLR_COLLECTIONS` inválida (duas coleções iguais ou uma delas vazia) levanta `ValueError` em 100 % dos casos; com uma só coleção ocorre `IndexError`; com duas coleções distintas, 0 erros.
- **SC-005**: Salvar/excluir qualquer instância de qualquer modelo do esqueleto enfileira 0 tarefas Celery de indexação.
- **SC-006**: O schema de cada coleção lista exatamente os campos descritos em FR-012/FR-013 (verificável por `/schema/fields`).
- **SC-007**: `USE_SOLR` desligado produz a mensagem "Solr support is not initialized." e nenhuma chamada HTTP ao Solr pelos scripts.
- **SC-008**: Várias instâncias com `COMPOSE_PROJECT_NAME` distintos não colidem em nomes de contêiner nem de coleção.

## Premissas

- Pré-requisito: feature `001-fundacao-projeto-django` (estrutura de `settings` e `.env`) e o Celery/Redis configurados em `backend/settings/zasyncs.py`; os scripts Docker completos são cobertos por `010-docker-desenvolvimento` e `011-docker-producao`.
- O Solr roda em modo SolrCloud com ZooKeeper embutido (`bin/solr start -c`), porta 9983; segurança só é aplicada quando `IS_ZK_EMBEDDED=True`.
- Em dev os scripts rodam a partir da raiz do projeto no contêiner (`/var/project/backend`), onde existem `./solr/...` e `_docker/prod/*`; em prod, `solr_cli.py`, `wait-for-solr.sh` e a pasta `solr/` são copiados para `${HOME}` da imagem e executados a partir dela.
- A classe de índice (`SearchIndex`/`CelerySearchIndex`), o `text` com *template* e as tarefas de reindexação são responsabilidade de quem registrar modelos; o esqueleto não os traz.
- Os valores de exemplo `startdev1`/`startprod1` são padrões de desenvolvimento e DEVEM ser trocados via `SOLR_USER`/`SOLR_PASSWORD` em produção real.
- Nenhum teste automatizado cobre esta feature no repositório atual; os testes propostos estão em `quickstart.md`.
