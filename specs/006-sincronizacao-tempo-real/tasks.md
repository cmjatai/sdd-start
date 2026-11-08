---

description: "Lista de tarefas para reconstruir a funcionalidade 006-sincronizacao-tempo-real"
---

# Tarefas: Sincronização em Tempo Real (WebSocket + Celery)

**Entrada**: Documentos de design em `/specs/006-sincronizacao-tempo-real/`

**Pré-requisitos**: plan.md (obrigatório), spec.md, research.md, data-model.md, contracts/ (`websocket-sync.md`, `http-celery-frontend.md`); features 001 a 005 concluídas (projeto Django, `Teste`, regras de permissão, CRUD, API gerada). A configuração do Vite (007) deve existir para a parte de frontend; o roteamento Daphne/Nginx de produção é da feature 011.

**Testes**: Incluídos (constituição, princípio VIII). Nenhuma tarefa está marcada: este arquivo é um roteiro de reconstrução.

**Organização**: Tarefas agrupadas por história de usuário. As seções "Detalhamento de Implementação" do `plan.md` (§1–§9) trazem o algoritmo de cada arquivo.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1 a US5 (ver `spec.md`)
- Inclua os caminhos exatos dos arquivos nas descrições

## Convenções de Caminhos

- Backend: `backend/` (app `backend/utils`); frontend: `_frontend/src/`; templates: `_templates/`; testes: `backend/utils/tests.py` ou `_tests/`

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: Dependências e configuração base

- [ ] T001 Garantir em `pyproject.toml` as dependências `channels ^4.3.2`, `channels-redis ^4.3.0`, `daphne ^4.2.3`, `celery ^5.7.0`, `django-celery-beat ^2.9.0`, `django-celery-results ^2.6.0`, `redis ^8.1.0` e atualizar `poetry.lock` (`poetry lock`)
- [ ] T002 [P] Em `backend/settings/apps.py`, registrar `"daphne"` (primeiro item) e `"channels"` em `DJANGO_CORE_APPS`, e `"django_celery_beat"`, `"django_celery_results"` em `DJANGO_THIRD_PARTY_APPS`; `BACKEND_APPS = ["backend.eauth", "backend.utils"]`
- [ ] T003 [P] Em `backend/settings/project.py`, definir `ASGI_APPLICATION = "backend.asgi.application"` e `from .zasyncs import *  # noqa: F403`
- [ ] T004 [P] Garantir que `_frontend/` tenha as dependências `pinia`, `vue`, `axios`, `lodash` (global `_` injetado — feature 007) e confirmar o alias `~@`

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: Infraestrutura Redis/Celery/Channels e ASGI que DEVE existir antes de qualquer história

**⚠️ CRÍTICO**: Nenhuma história pode começar antes desta fase

- [ ] T005 Criar `backend/settings/zasyncs.py` conforme `plan.md` §1: `REDIS_HOST` (padrão `startdev1-redis`), `REDIS_PORT` (6379), host `localhost` em `DEBUG` fora do contêiner, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND = "django-db"`, `CELERY_CACHE_BACKEND = "django-cache"`, `CELERY_BEAT_SCHEDULER`, `CHANNEL_LAYERS` (`RedisChannelLayer`, `socket_timeout=None`, `socket_connect_timeout=5`) e `CACHES` (`RedisCache`)
- [ ] T006 [P] Criar `backend/celery.py` (`Celery('backend')`, `config_from_object('django.conf:settings', namespace='CELERY')`, `autodiscover_tasks(lambda: settings.INSTALLED_APPS)`) e exportar `celery_app` em `backend/__init__.py`
- [ ] T007 [P] Criar `backend/utils/routing.py` com `websocket_urlpatterns = [path("ws/sync/", consumers.SyncRefreshConsumer.as_asgi())]`
- [ ] T008 Criar `backend/asgi.py` com `ProtocolTypeRouter` (`http: ASGIHandler()`, `websocket: AuthMiddlewareStack(URLRouter(backend_routing.websocket_urlpatterns))`), `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')` e `django.setup()` (depende de T007)
- [ ] T009 [P] Garantir `backend/utils/apps.py` com `UtilsConfig` (`name="backend.utils"`, `label="utils"`, `default_auto_field = BigAutoField`) e `ready()` importando `from .services import signals, signals_syncrefresh` (+ `__all__`); criar `backend/utils/services/__init__.py` e `backend/utils/services/signals.py` vazios
- [ ] T010 [P] Confirmar o modelo `Teste` (feature 001: `teste = CharField(max_length=100, verbose_name=_("Teste"))`, `ordering=("teste",)`) e a regra `(Teste, __base__, set(__base_view__))` em `backend/globalrules/map_rules.py` (feature 003), gerando `rules_patterns_public["utils:teste"]`

**Ponto de Controle**: Fundação pronta — o servidor ASGI sobe e `ws/sync/` está roteado

---

## Fase 3: História de Usuário 1 - Receber mudanças sem recarregar (Prioridade: P1) 🎯 MVP

**Objetivo**: Salvar/excluir um modelo sincronizável publica a mudança no grupo e o cliente a recebe e reage.

**Teste Independente**: Conectar um cliente WebSocket, salvar um `Teste` e receber `sync_refresh.message`.

### Testes da História de Usuário 1

- [ ] T011 [P] [US1] Teste de consumidor em `backend/utils/tests.py`: com `CHANNEL_LAYERS` em memória e `WebsocketCommunicator(SyncRefreshConsumer.as_asgi(), "/ws/sync/")`, conectar e verificar aceitação (sem `pytest-asyncio`: usar `async_to_sync`; `@pytest.mark.django_db(transaction=True)`)
- [ ] T012 [P] [US1] Testes de sinais em `backend/utils/tests.py`: `Teste.objects.create(...)` ⇒ mensagem com `action="post_save"`, `created=True`, `app="utils"`, `model="teste"`, `timestamp`; `delete()` ⇒ `post_delete`; `Metadata` e modelos fora de `^utils` não publicam; `ws_sync()` falso não publica; falha de `group_send` não impede o `save()`

### Implementação da História de Usuário 1

- [ ] T013 [US1] Criar `backend/utils/consumers.py` com `SyncRefreshConsumer`: `__init__` (import tardio de `rules_patterns_public`), `connect` (grupo `group_sync_refresh_channel`, `accept`), `disconnect` (`group_discard`) — ver `plan.md` §4 e `contracts/websocket-sync.md`
- [ ] T014 [US1] Criar `backend/utils/services/signals_syncrefresh.py` (`regex_applabels_permitidos = [re.compile(r"^utils")]`, exclusão `auditlog`/`metadata`, ganchos `ws_sync()`/`ws_serialize()`, montagem de `message`, serialização via `ApiViewSetConstrutor.get_viewset_for_model(...).serializer_class(inst).data`, `async_to_sync(channel_layer.group_send)` com `type="sync_refresh.message"`, tratamento de erros com `gettext_lazy`) e o receptor `signal_post_syncrefresh` com `dispatch_uid="signal_post_syncrefresh"` — `plan.md` §3
- [ ] T015 [US1] Implementar em `SyncRefreshConsumer.sync_refresh_message` o envio básico `await self.send(text_data=json.dumps(event))` e o tratamento de erro (`{"type":"error","error":...}`) (as permissões entram na US2)
- [ ] T016 [US1] Criar `_frontend/src/js/EventBus.js` (`on`, `off`, `emit`; `export default new EventBus()`) e fornecê-lo em `_frontend/src/main.js` com `app.provide('EventBus', EventBus)` e `app.config.globalProperties.$EventBus`
- [ ] T017 [US1] Criar `_frontend/src/js/utils/ws/WebSocketManager.js` (conexão, `on`/`emit`, `onmessage` com conversão de `pong`; reconexão/heartbeat são completados na US4) — `plan.md` §7
- [ ] T018 [US1] Criar `_frontend/src/js/stores/pinea/SyncStore.js` com `state` (`wsManager`, `wsConnected`, `lastServerSync`, `models`, `data_cache`, `eventBus: inject('EventBus')`), `initialize()`, `registerModels`, `handleSyncMessage` (ignora modelos não registrados; `post_delete` remove do cache; `post_save` emite `sync-refresh` e atualiza/busca) e `UPDATE_DATA_CACHE`/`DELETE_DATA_CACHE`
- [ ] T019 [US1] Em `_frontend/src/App.vue`, chamar `useSyncStore().initialize()` e `registerModels('utils', ['teste'])` (além de `DisplayMessage`, `<slot />` e `#modalApp`)

**Ponto de Controle**: Mudanças em `Teste` chegam ao navegador e disparam `sync-refresh`

---

## Fase 4: História de Usuário 2 - Respeitar permissões de visualização (Prioridade: P1)

**Objetivo**: Remover `instance` das mensagens entregues a quem não pode ver o modelo.

**Teste Independente**: Anônimo, usuário sem permissão e superusuário recebem a mesma mudança com e sem `instance`.

### Testes da História de Usuário 2

- [ ] T020 [P] [US2] Testes em `backend/utils/tests.py`: anônimo + `Teste` (público) ⇒ com `instance`; anônimo + modelo sem permissão pública ⇒ sem `instance` (usar `rules_patterns_public` via monkeypatch); usuário comum sem `view_teste` ⇒ sem `instance`; usuário com `utils.view_teste` ⇒ com `instance`; superusuário ⇒ sempre com `instance`; dois clientes simultâneos com permissões diferentes recebem versões diferentes

### Implementação da História de Usuário 2

- [ ] T021 [US2] Completar `sync_refresh_message` em `backend/utils/consumers.py` com o cálculo de `detail_perm` (`rules_patterns_public.get(f"{app}:{model}", set())`; anônimo; `database_sync_to_async(u.has_perm)` para `detail_`/`view_`; superusuário) e `del message["instance"]` (silenciando `KeyError`) antes de `send` — `plan.md` §4

**Ponto de Controle**: Nenhum cliente sem permissão recebe `instance`

---

## Fase 5: História de Usuário 3 - Cache do cliente coerente (Prioridade: P2)

**Objetivo**: Cache normalizado, busca paginada e invalidação.

**Teste Independente**: `fetchSync` + mensagens WS mantêm `data_cache['utils_teste']` consistente.

### Testes da História de Usuário 3

- [ ] T022 [P] [US3] (Opcional, se adotar Vitest) Testes de `SyncStore` em `_frontend/`: descarte por `timestamp_frontend`, paginação (`pagination.next_page`), `invalidateDataCache` + `cleanInvalidatedDataCache`, `force_fetch=false`, auto-registro de modelo; caso contrário, validar manualmente conforme `quickstart.md`

### Implementação da História de Usuário 3

- [ ] T023 [US3] Completar `SyncStore.js`: `fetchSync` (parâmetros padrão `page=1`, `o='id'`, junção de arrays, `timestamp_frontend`, paginação recursiva por `pagination.next_page`, `force_fetch`/`only_first_page`), `syncModels`, `invalidateDataCache`, `cleanInvalidatedDataCache`, `invalidateCacheItems`, `sendSyncMessage`, normalização de objetos aninhados com `__label__` em `UPDATE_DATA_CACHE`, `UPDATE_DATA_CACHE_CRONOMETRO` — `plan.md` §8
- [ ] T024 [P] [US3] Criar `_frontend/src/js/utils/timer/TimerWorkerService.js` (Web Worker via `Blob`, `startTimer(timerId, callback, interval=1000)`, `stopTimer`, singleton) e as ações `startLocalCronometro`/`stopLocalCronometro` (500 ms) no `SyncStore`
- [ ] T025 [P] [US3] Confirmar `Resources.Utils.fetch` em `_frontend/src/js/utils/resources` (`GET /api/<app>/<model>/[id/][action/]?query`) — pertence à feature 007

**Ponto de Controle**: O cache reflete API + WebSocket sem regressão por dados antigos

---

## Fase 6: História de Usuário 4 - Conexão resiliente (Prioridade: P2)

**Objetivo**: Heartbeat, reconexão com backoff e métrica de latência.

**Teste Independente**: Reiniciar o servidor e ver a reconexão automática.

### Testes da História de Usuário 4

- [ ] T026 [P] [US4] Teste em `backend/utils/tests.py`: `ping` com `ping_now` ⇒ `pong` com `message.timestamp_server` numérico e `message.ping_now` igual; verificar que um segundo cliente não recebe nada

### Implementação da História de Usuário 4

- [ ] T027 [US4] Em `SyncRefreshConsumer.receive` (`backend/utils/consumers.py`): `json.loads`; ramo `ping` (responde `pong` e `return`); ramo `command` (valida `command`, responde `command_result` com `error="Comando não especificado"` e `return`); `except` enviando `command_result` com `error`; retransmissão `group_send` com `type="sync_refresh_message"`; e o handler `command_result` — `plan.md` §4 (replicar o comportamento descrito em `research.md`, item 1–3)
- [ ] T028 [US4] Completar `WebSocketManager.js`: `reconnectInterval=1000`, `maxReconnectAttempts=10`, `handleReconnect` (atraso `1000*2^tentativa`), `startHeartbeat`/`stopHeartbeat` (60 000 ms), ping ao abrir, `send` com reagendamento, `server_time_diff` no `pong`
- [ ] T029 [US4] Em `SyncStore.initialize()`, ligar `connected`/`disconnected` a `wsConnected` e `message` do tipo `pong` a `lastServerSync`

**Ponto de Controle**: A conexão se recupera sozinha e a latência é medida

---

## Fase 7: História de Usuário 5 - Demonstração ponta a ponta (Prioridade: P3)

**Objetivo**: `/wstest/` + `/testws/` + `debug_task` + mensagens de interface.

**Teste Independente**: Clicar no botão cria um `Teste` em ~2 s e exibe o aviso.

### Testes da História de Usuário 5

- [ ] T030 [P] [US5] Testes em `backend/utils/tests.py` com `django-webtest`/`client`: `GET /testws/` ⇒ 200 JSON (`message`, `teste`) e `debug_task.apply_async` chamado com `((), countdown=2)` (mock); `GET /wstest/` e `/wstest/abc` ⇒ 200 com template `wstest_index.html`; `debug_task.apply()` cria um `Teste` e retorna `result of teste <id>`; `reverse('backend.utils:testws')`

### Implementação da História de Usuário 5

- [ ] T031 [P] [US5] Criar `backend/utils/services/tasks.py` com `debug_task` (`@app.task(queue="celery", bind=True)`, cria `Teste` com `str(random())`, log e retorno) — `plan.md` §6
- [ ] T032 [US5] Em `backend/utils/views.py` adicionar `wstest_index(request, slug)` e `testws(request)`; em `backend/utils/urls.py` as rotas `re_path(r"^testws/", views.testws, name="testws")` e `re_path(r"^wstest/(?P<slug>[^.]*)$", views.wstest_index, name="wstest_index")` (depende de T031)
- [ ] T033 [P] [US5] Criar `_templates/wstest_index.html` (`{% extends 'base.html' %}`, bloco `base_content` com `<router-view></router-view>`)
- [ ] T034 [P] [US5] Criar `_frontend/src/js/stores/MessageStore.js` (`messages`, `id`, `getMessages`, `addMessage`, `shiftMessage`, `removeMessage`)
- [ ] T035 [P] [US5] Criar `_frontend/src/components/utils/message/AlertMessage.vue`, `DisplayMessage.vue` e `Alert.vue` (registrar `emf-alert` em `_frontend/src/registerComponents.js`) — `plan.md` §9
- [ ] T036 [US5] Criar `_frontend/src/views/WsTest.vue` (botão que chama `/testws/` e adiciona mensagem `success`; `bus.on('sync-refresh')` filtrando `utils`/`teste` e adicionando mensagem `info`) e a rota `/wstest/` (`name: 'index_link'`) em `_frontend/src/js/routers.js` (depende de T034, T035)

**Ponto de Controle**: Fluxo completo HTTP → Celery → sinal → WebSocket → UI funcionando

---

## Fase 8: Acabamento e Preocupações Transversais

- [ ] T037 [P] Rodar `ruff check .` e corrigir (E, F, I) nos arquivos de `backend/utils/` e `backend/asgi.py`/`backend/celery.py`
- [ ] T038 [P] Rodar `npm run lint` e `npm run build`; corrigir avisos dos arquivos desta feature
- [ ] T039 Executar `pytest` e validar com `quickstart.md` (manual: duas abas em `/wstest/`, reinício do servidor)
- [ ] T040 [P] Atualizar `README.md` (endereços `/wstest/`, serviços Redis/Celery) caso falte, e registrar em `specs/006-sincronizacao-tempo-real/research.md` qualquer divergência encontrada na reconstrução
- [ ] T041 [P] Verificar que o Nginx de produção (feature 011) encaminha `/ws/` ao Daphne e que `start.sh` inicia o worker Celery (`-Q:1 celery`), apenas conferindo — sem alterar aqui

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências
- **Fundacional (Fase 2)**: depende da Fase 1 e das features 001–005; **bloqueia** todas as histórias
- **US1 e US2 (P1)**: US2 estende o consumidor criado em US1 (T021 depende de T013/T015)
- **US3 (P2)** depende de US1 (SyncStore base); **US4 (P2)** depende de US1 (consumidor e WebSocketManager base)
- **US5 (P3)**: depende de US1 para ver o efeito no navegador; o backend (T031–T033) é independente
- **Acabamento (Fase 8)**: depende das histórias desejadas

### Dentro de cada História

- Testes escritos antes da implementação (devem falhar primeiro)
- Consumidor/sinais antes do cliente; `SyncStore` antes de `WsTest.vue`

### Oportunidades de Paralelismo

- T002–T004, T006, T007, T009, T010 em paralelo
- Backend (T013–T015, T021, T027, T031–T033) em paralelo com frontend (T016–T019, T023–T025, T028, T034–T036), respeitando os arquivos compartilhados (`consumers.py`, `SyncStore.js`, `WebSocketManager.js` são editados em mais de uma história: executar em sequência)

---

## Estratégia de Implementação

### MVP Primeiro (US1 + US2)

1. Fases 1 e 2 (infraestrutura Redis/Channels/Celery/ASGI)
2. US1 (sinais + consumidor + cliente mínimo) e US2 (permissões)
3. **PARAR e VALIDAR**: abrir `ws/sync/`, salvar um `Teste` e conferir `instance` por perfil de usuário

### Entrega Incremental

1. US3 (cache completo) → validar com o console do navegador
2. US4 (ping/pong, heartbeat, reconexão) → derrubar e subir o servidor
3. US5 (demonstração) → fluxo `/wstest/`
4. Acabamento: lint, build, testes

### Observação de Fidelidade

Replicar os comportamentos descritos em `research.md` (retransmissão aberta, `detail_`, ausência de `on_commit`, etc.) para reproduzir o estado atual; correções recomendadas ficam como evolução posterior.
