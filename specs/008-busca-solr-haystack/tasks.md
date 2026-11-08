---
description: "Lista de tarefas para reconstruir a infraestrutura de busca textual (Solr + Haystack)"
---

# Tarefas: Infraestrutura de Busca Textual (Solr + Haystack)

**Entrada**: Documentos de design em `/specs/008-busca-solr-haystack/`
**Pré-requisitos**: plan.md (obrigatório), spec.md, research.md, data-model.md, contracts/ (4 arquivos); features `001-fundacao-projeto-django` (settings modulares, `zenv.py`, Celery) concluída.

**Testes**: incluídos (princípio VIII da constituição) — pytest sem Solr real, arquivo `backend/test_solr_haystack.py`.

**Organização**: tarefas agrupadas por história de usuário (US1…US5). **Todas as tarefas estão desmarcadas**: este documento é um roteiro de reconstrução.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US5 conforme `spec.md`
- Detalhes de cada item: seções numeradas do `plan.md` ("Detalhamento de Implementação") e `contracts/`.

## Convenções de Caminhos

Aplicação web Django: `backend/` (código), `solr/` (configsets), `_docker/dev` e `_docker/prod` (infra), raiz (`pyproject.toml`, `.gitignore`).

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: dependências e ignorados.

- [ ] T001 Adicionar a `pyproject.toml` as dependências `django-haystack = "^3.4.0"`, `celery-haystack = {git = "https://github.com/LeandroJatai/celery-haystack.git"}`, `pysolr = "^3.11.0"` e `kazoo = "^2.11.0"` (plan §1); rodar `poetry lock` e `poetry install`
- [ ] T002 [P] Adicionar `security.json` ao `.gitignore` (FR-026)
- [ ] T003 [P] Confirmar que `requests` (usado por `_docker/prod/solr_cli.py`) está instalado como dependência transitiva (não é declarado no `pyproject.toml`, research item 16)

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: Django carrega com Haystack/`celery_haystack` configurados.

**⚠️ CRÍTICO**: nenhuma história pode ser validada sem esta fase.

- [ ] T004 Registrar `"haystack"` e `"celery_haystack"` em `DJANGO_THIRD_PARTY_APPS` de `backend/settings/apps.py` (após `django_celery_results`, antes de `drf_spectacular`) (FR-005)
- [ ] T005 [P] Adicionar o logger `"haystack"` (handlers `backend_logger_file` e `console`, `level=LOGGING_ROOT_LEVEL`, `propagate=False`) em `backend/settings/logs.py`
- [ ] T006 Garantir em `backend/settings/project.py` a linha `from .solr import *  # noqa: F403` entre `middleware` e `zasyncs` (princípio I)

**Ponto de Controle**: `python manage.py check` passa após T007+ (US3).

---

## Fase 3: História de Usuário 3 - Configuração Django/Haystack com duas coleções roteadas (Prioridade: P1) 🎯 MVP

**Objetivo**: settings Haystack, roteador e processador de sinais assíncrono.

**Teste Independente**: `import backend.haystack` com duas coleções distintas funciona; com `a,a` levanta `ValueError`; salvar um modelo não enfileira tarefas.

### Testes da História de Usuário 3

- [ ] T007 [P] [US3] Criar `backend/test_solr_haystack.py` com testes: `test_haystack_connections` (duas conexões, `BATCH_SIZE=1000`, `TIMEOUT=600`, URLs terminando nas coleções), `test_validacao_colecoes` (`importlib.reload` com `SOLR_COLLECTIONS="a,a"` → `ValueError`), `test_router_sem_hints`, `test_router_modelo_nao_registrado`, `test_router_modelos_registrados` (monkeypatch das tuplas), `test_processor_ignora_modelos_nao_registrados` (quickstart §7)

### Implementação da História de Usuário 3

- [ ] T008 [US3] Criar `backend/settings/solr.py` conforme plan §3: `USE_SOLR`, `SOLR_URL` (padrão `http://startdev1:startdev1@startdev1-solr:8983`), `HAYSTACK_SIGNAL_PROCESSOR`, `SOLR_COLLECTIONS` (padrão `backend_arq1,backend_arq2`), `SEARCH_BACKEND`, `HAYSTACK_ROUTERS`, `HAYSTACK_ITERATOR_LOAD_PER_QUERY=100`, `HAYSTACK_CONNECTIONS` (`default` e `backendarq`, `BATCH_SIZE=1000`, `TIMEOUT=600`, `EXCLUDED_INDEXES=[]`) (FR-001…FR-003)
- [ ] T009 [US3] Criar `backend/haystack.py` conforme plan §4: `DEFAULT_ALIAS`, `BACKENDARQ_ALIAS`, validação com `ValueError`, `MODELS_SOLR_DEFAULT = ()`, `MODELS_SOLR_BACKENDARQ = ()`, `CelerySignalProcessor` (`enqueue_save`/`enqueue_delete`) e `DefaultRouter` (`for_write`/`for_read`/`for_rw`) (FR-007…FR-010)
- [ ] T010 [US3] Verificar `python manage.py check` e `pytest backend/test_solr_haystack.py -k "connections or validacao or router or processor"`

**Ponto de Controle**: configuração Django funcional; nenhum modelo indexado (SC-004, SC-005).

---

## Fase 4: História de Usuário 4 - Schemas gerenciados (Prioridade: P2)

**Objetivo**: *configsets* `arq1` e `arq2` versionados.

**Teste Independente**: parse dos XML confere campos; após criar coleções, `/schema/fields` lista os campos (quickstart §2).

### Testes da História de Usuário 4

- [ ] T011 [P] [US4] Adicionar em `backend/test_solr_haystack.py` o teste `test_schemas_xml` (campos esperados de cada `managed-schema.xml`, `uniqueKey=id`, `text_pt` com `brazilianStem`; `at` só em arq1; `tipo/ano/data/conta_classe_*` só em arq2)

### Implementação da História de Usuário 4

- [ ] T012 [P] [US4] Criar `solr/arq1_configset/conf/` com `managed-schema.xml` (derivado do `_default` do Solr 9.x + campos de `contracts/configsets-solr.md` coluna `arq1`, tipo `text_pt`), `solrconfig.xml` (`_default` + `/select` com `rows=50`, `df=text`, `edismax`, `lowercaseOperators=true`, `q.op=AND`; `spellchecker.field=text`; `hl.fragsize=512`), `protwords.txt`, `stopwords.txt`, `synonyms.txt`, `lang/stopwords_en.txt`, `lang/stopwords_es.txt`, `lang/stopwords_pt.txt`
- [ ] T013 [P] [US4] Criar `solr/arq2_configset/conf/` com os mesmos arquivos, mudando: schema (sem `at`; com `conta_classe_logica`, `conta_classe_estrutural`, `tipo`, `ano`, `data`), `spellchecker.field=_text_`, `hl.fragsize=100`
- [ ] T014 [US4] Rodar `pytest backend/test_solr_haystack.py -k schemas`

**Ponto de Controle**: *configsets* prontos para upload (SC-006).

---

## Fase 5: História de Usuário 1 - Solr no ambiente com coleções criadas automaticamente (Prioridade: P1)

**Objetivo**: serviço Solr nos Compose, espera e provisionamento de coleções na partida.

**Teste Independente**: `docker compose up` com `USE_SOLR=True` resulta em duas coleções listadas (quickstart §1–2).

### Testes da História de Usuário 1

- [ ] T015 [P] [US1] Adicionar em `backend/test_solr_haystack.py`: `test_solrclient_nomes`, `test_zip_configset` (carregar `_docker/prod/solr_cli.py` com `importlib.util.spec_from_file_location`; executar a partir da raiz), `test_create_collection_requests` (monkeypatch de `requests.get/post`)

### Implementação da História de Usuário 1

- [ ] T016 [US1] Criar `_docker/prod/wait-for-solr.sh` (plan §7; `exit 1` online, `exit 2` falha; manter a comparação `[[ $RETRY_COUNT < $RETRY_LIMIT ]]` para fidelidade) e `chmod +x`
- [ ] T017 [US1] Criar `_docker/prod/solr_cli.py` — parte do cliente (plan §6): `SolrClient` (templates de URL, `__init__`, `get_num_docs`, `list_collections`, `exists_collection`, `zip_configset`, `maybe_upload_configset`, `create_collection`, `delete_collection`, `delete_index_data`) e `__main__` com `argparse` (`-u`, `-c`, `-rc`, `-s`, `-rf`, `-ms`, `--embedded_zk`)
- [ ] T018 [P] [US1] Adicionar o serviço `solr` (imagem `solr:9.7` com o comentário "validar mudança para 9.8 pois está causando erro", `command: bin/solr start -c -f`, volumes `solr9_data`/`solr9_configsets`, portas `8983:8983` e `9983:9983`, rede `appdev-net`, `restart: on-failure`) e as variáveis `USE_SOLR`, `SOLR_COLLECTIONS`, `SOLR_URL`, `IS_ZK_EMBEDDED`, `depends_on: solr` no `app`, e os volumes nomeados em `_docker/dev/docker-compose.yaml` (`contracts/docker-solr.md`)
- [ ] T019 [P] [US1] Idem em `_docker/prod/docker-compose.yaml` (`restart: always`, portas comentadas, rede `app-net`, `depends_on: solr: condition: service_started`, padrões `startprod1`)
- [ ] T020 [P] [US1] Em `_docker/dev/start-dev.sh`: chaves `SOLR_COLLECTIONS` e `SOLR_URL` na função `change_env_file` e bloco `## SOLR` (plan §8) chamando `/bin/bash _docker/prod/wait-for-solr.sh` e `python3 _docker/prod/solr_cli.py ...`
- [ ] T021 [P] [US1] Em `_docker/prod/start.sh`: idem, usando `wait-for-solr.sh` e `solr_cli.py` no `${HOME}`; garantir no `_docker/prod/Dockerfile` as linhas `ADD solr ${HOME}/solr`, `COPY _docker/prod/wait-for-solr.sh ${HOME}`, `COPY _docker/prod/solr_cli.py ${HOME}` e `chmod +x` (detalhes de 011)
- [ ] T022 [US1] Subir o ambiente e executar a validação do quickstart §1–2 e §5 (idempotência, `-rc`, retorno do `wait-for-solr.sh`)

**Ponto de Controle**: duas coleções criadas e idempotentes (SC-001, SC-002, SC-007).

---

## Fase 6: História de Usuário 2 - Autenticação básica do Solr (Prioridade: P1)

**Objetivo**: `security.json` gerado e enviado ao ZooKeeper embutido.

**Teste Independente**: 401 sem credenciais e 200 com credenciais (quickstart §2).

### Testes da História de Usuário 2

- [ ] T023 [P] [US2] Adicionar em `backend/test_solr_haystack.py`: `test_solr_hash_password_formato`, `test_url_pattern_aceita_alfanumericos`, `test_url_pattern_rejeita_especiais`, `test_create_security_file` (usar `tmp_path` e `monkeypatch.chdir`), teste de `setup_embedded_zk` com URL inválida levantando `SystemExit`

### Implementação da História de Usuário 2

- [ ] T024 [US2] Completar `_docker/prod/solr_cli.py` (plan §6): `SECURITY_FILE_TEMPLATE`, `URL_PATTERN`, `solr_hash_password`, `create_security_file`, `upload_security_file` (kazoo, porta 9983, `/security.json` create/set), `setup_embedded_zk`, chamada condicionada a `--embedded_zk` antes do `SolrClient`
- [ ] T025 [US2] Validar quickstart §2 (401/200) e que `security.json` está ignorado pelo git (`git status` limpo)

**Ponto de Controle**: Solr protegido por BasicAuth (SC-003).

---

## Fase 7: História de Usuário 5 - Desenvolvimento acessível do host (Prioridade: P3)

**Objetivo**: URL do Solr para `localhost` em debug fora do contêiner.

**Teste Independente**: com `DEBUG=True` e `FOLDER_DEBUG_CONTAINER` diferente de `PROJECT_DIR`, a URL contém `@localhost:8983`.

- [ ] T026 [P] [US5] Adicionar em `backend/test_solr_haystack.py` teste que recarrega `backend.settings.solr` com `DEBUG`/`FOLDER_DEBUG_CONTAINER` simulados (monkeypatch de `backend.settings.zenv`) e verifica a reescrita da URL e sua ausência quando as pastas coincidem
- [ ] T027 [US5] Garantir em `backend/settings/solr.py` o bloco `if DEBUG: if FOLDER_DEBUG_CONTAINER != PROJECT_DIR: SOLR_URL = SOLR_URL.split("@")[0] + "@localhost:8983"` (plan §3, passo 5)
- [ ] T028 [US5] Validar quickstart §3 no host (porta 8983 publicada pelo Compose de dev)

**Ponto de Controle**: Django no host alcança o Solr do Compose.

---

## Fase 8: Acabamento e Preocupações Transversais

- [ ] T029 [P] Rodar `ruff check .` e corrigir apontamentos nos arquivos novos (`backend/haystack.py`, `backend/settings/solr.py`, `backend/test_solr_haystack.py`)
- [ ] T030 [P] Rodar `pytest` completo (sem regressões nas demais features)
- [ ] T031 [P] Atualizar `README.md` (linha da tabela de pastas: `solr/` → *configsets* das coleções `arq1` e `arq2`; endereços `localhost:8983`/`localhost:9983`)
- [ ] T032 Conferir `research.md` (itens 3, 6 e 8 são riscos conhecidos): se a decisão for **corrigir** em vez de replicar, atualizar esta especificação na mesma entrega (constituição, Fluxo de Desenvolvimento nº 3)
- [ ] T033 Executar o roteiro completo do `quickstart.md` do zero (volumes removidos) e confirmar SC-001…SC-008

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências.
- **Fundacional (Fase 2)**: depende da Fase 1; bloqueia as histórias.
- **US3 (Fase 3)**: depende da Fase 2; T008 (`solr.py`) antes de T009 (`haystack.py` lê `settings.SOLR_COLLECTIONS`).
- **US4 (Fase 4)**: independente de US3 (apenas arquivos em `solr/`); necessária antes de T022.
- **US1 (Fase 5)**: depende de US3 (variáveis/URLs), US4 (*configsets*) e T016/T017; T020/T021 dependem de T016 e T017.
- **US2 (Fase 6)**: estende `solr_cli.py` (T017 → T024); validação depende do ambiente de US1.
- **US5 (Fase 7)**: depende de T008.
- **Acabamento (Fase 8)**: depende de todas.

### Dentro de Cada História

- Testes antes da implementação (devem falhar primeiro); constantes/config antes de classes; scripts antes dos Compose/start.

### Oportunidades de Paralelismo

- T002, T003, T005; T012 e T013 (configsets); T018–T021 (Compose e scripts); testes T007, T011, T015, T023, T026 (mesmo arquivo — escrever em sequência ou em blocos separados).

---

## Estratégia de Implementação

### MVP Primeiro (US3)

1. Fases 1–2 → US3 (config Django + roteador): o projeto sobe com Haystack sem Solr real.
2. Validar `ValueError` e ausência de indexação.

### Entrega Incremental

1. US4 (*configsets*) → US1 (Solr + coleções) → US2 (segurança) → US5 (conveniência de debug).
2. A cada passo, rodar o trecho correspondente do `quickstart.md`.

### Notas

- Não registrar modelos em `MODELS_SOLR_*` nem criar `search_indexes.py`: o esqueleto entrega só a infraestrutura.
- Para fidelidade, replicar as particularidades de `research.md` (inclusive alias do roteador e laço do `wait-for-solr.sh`); correções são opcionais e exigem atualizar a spec.
