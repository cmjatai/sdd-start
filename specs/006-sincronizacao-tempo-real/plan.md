# Plano de Implementação: Sincronização em Tempo Real (WebSocket + Celery)

**Branch**: `006-sincronizacao-tempo-real` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/006-sincronizacao-tempo-real/spec.md`

## Resumo

Propagar, em tempo real, as mudanças de modelos Django aos navegadores. No servidor: sinais `post_save`/`post_delete` publicam uma mensagem no grupo de Channels `group_sync_refresh_channel` (Redis); o `SyncRefreshConsumer` (`ws/sync/`) entrega a mensagem a cada cliente removendo `instance` de quem não tem permissão de visualização. No cliente: `WebSocketManager` (conexão, heartbeat, reconexão) alimenta o `SyncStore` (cache normalizado, busca paginada, invalidação) que emite `sync-refresh` no `EventBus`. Inclui a tarefa Celery `debug_task` e as rotas `/testws/` e `/wstest/` como demonstração ponta a ponta com o modelo `Teste` (feature 001).

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (`requires-python = ">=3.12,<4.0"`); JavaScript ES modules (Vue 3.5)

**Dependências Principais**: Django >= 6, < 7 (6.0.10 instalado); `channels ^4.3.2`, `channels-redis ^4.3.0`, `daphne ^4.2.3`; `celery ^5.7.0`, `django-celery-beat ^2.9.0`, `django-celery-results ^2.6.0`, `redis ^8.1.0`; Pinia, Vue 3, axios, lodash (`_` global injetado pelo Vite — feature 007); `drfautoapi` (feature 005)

**Armazenamento**: Redis (broker Celery, Channel Layer, cache); PostgreSQL (resultados Celery em `django-db`, modelo `Teste`)

**Testes**: `pytest` + `pytest-django` (não há testes existentes desta funcionalidade; ver `quickstart.md` e `tasks.md`); `ruff` (E, F, I); ESLint/Prettier no frontend

**Plataforma Alvo**: servidor Linux (Docker); `runserver` com Daphne em desenvolvimento (`daphne` é o primeiro app de `INSTALLED_APPS`), Daphne em socket Unix atrás do Nginx em produção (feature 011); navegadores modernos (WebSocket, Web Worker, `Blob`)

**Tipo de Projeto**: aplicação web (backend Django + frontend Vite/Vue)

**Metas de Desempenho**: propagação em < 1 s em rede local (SC-001); ping a cada 60 s

**Restrições**: ASGI obrigatório para WebSocket; Redis disponível; `socket_connect_timeout = 5` s; reconexão máx. 10 tentativas

**Escala/Escopo**: um grupo de canal global; 1 modelo sincronizado (`Teste`); 1 rota WebSocket; 2 rotas HTTP de demonstração

## Verificação da Constituição

*PORTÃO (gate): Deve passar antes da pesquisa da Fase 0. Reverifique após o design da Fase 1.*

| Princípio | Gate | Situação |
|-----------|------|----------|
| I. Backend Django modular | Código no app `utils` (`consumers.py`, `routing.py`, `services/signals_syncrefresh.py`, `services/tasks.py`), configuração em módulo temático `settings/zasyncs.py`, registro de sinais em `UtilsConfig.ready()` | ✅ Atendido |
| II. Configuração por ambiente | `REDIS_HOST`/`REDIS_PORT` via `python-decouple`; nenhum segredo | ✅ Atendido |
| III. Paridade dev/prod | Mesma configuração Redis/Channels/Celery nos dois ambientes; diferença só pelo host (`.env`) e pelo servidor (Daphne/Nginx em prod, feature 011) | ✅ Atendido |
| IV. API REST gerada, permissões por modelo | A `instance` usa o serializer gerado pela API; permissão pelas regras de `globalrules` (`list_`/`view_`) | ✅ Atendido |
| V. Frontend Vite integrado | Comunicação apenas por `/api/` e `/ws/sync/`; componentes/estado em `_frontend/src`; alias `~@`; estilo ESLint (com exceções registradas em `research.md` item 19) | ⚠️ Atendido com exceção de estilo em `MessageStore.js` (replicada por fidelidade) |
| VI. Tempo real e assíncrono | Grupo `group_sync_refresh_channel`, permissão por usuário, Celery com broker Redis, resultados em banco e agendador `django_celery_beat` | ✅ Atendido |
| VII. PT-BR | Mensagens de log/erro em português; `gettext_lazy` nos logs dos sinais | ✅ Atendido |
| VIII. Qualidade verificável | Sem testes hoje; `tasks.md` inclui testes pytest (consumidor com `WebsocketCommunicator`, sinais, views) | ⚠️ Lacuna conhecida: testes a criar (tarefas de teste) |

Reavaliação pós-design: sem violações novas. Riscos de segurança (retransmissão aberta, ausência de validação de origem) estão registrados em `research.md` e na seção "Segurança" das Restrições da constituição (`ALLOWED_HOSTS`/CORS abertos no esqueleto).

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/006-sincronizacao-tempo-real/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── websocket-sync.md
│   └── http-celery-frontend.md
├── spec.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── asgi.py                                  # ProtocolTypeRouter + AuthMiddlewareStack
├── celery.py                                # app Celery 'backend'
├── __init__.py                              # exporta celery_app
├── settings/
│   ├── zasyncs.py                           # Redis, Celery, CHANNEL_LAYERS, CACHES
│   ├── apps.py                              # daphne, channels, django_celery_*
│   └── project.py                           # ASGI_APPLICATION, importa zasyncs
└── utils/
    ├── apps.py                              # UtilsConfig.ready() registra sinais
    ├── consumers.py                         # SyncRefreshConsumer
    ├── routing.py                           # websocket_urlpatterns
    ├── models.py                            # Teste (ref. feature 001)
    ├── urls.py                              # testws/, wstest/<slug>
    ├── views.py                             # testws, wstest_index (+ TesteCrud, MediaPublicView de outras features)
    └── services/
        ├── signals.py                       # (vazio)
        ├── signals_syncrefresh.py           # sinais → group_send
        └── tasks.py                         # debug_task

_templates/
└── wstest_index.html                        # extends base.html + <router-view>

_frontend/src/
├── App.vue                                  # initialize() + registerModels('utils', ['teste'])
├── main.js                                  # app.provide('EventBus', EventBus) (detalhes em 007)
├── js/
│   ├── EventBus.js
│   ├── routers.js                           # rota /wstest/ (index_link)
│   ├── stores/
│   │   ├── MessageStore.js
│   │   └── pinea/SyncStore.js
│   └── utils/
│       ├── ws/WebSocketManager.js
│       └── timer/TimerWorkerService.js
├── components/utils/message/
│   ├── Alert.vue
│   ├── AlertMessage.vue
│   └── DisplayMessage.vue
└── views/WsTest.vue

_tests/ (ou backend/utils/tests.py)          # testes a criar (ver tasks.md)
```

**Decisão de Estrutura**: aplicação web com backend e frontend no mesmo repositório. O código do servidor vive no app `utils` (`backend/utils`) e a configuração em `backend/settings/zasyncs.py`; o frontend vive em `_frontend/src`. A configuração do Vite (007) e o roteamento Daphne/Nginx (011) são apenas citados.

## Rastreamento de Complexidade

Sem violações da constituição que exijam justificativa (as duas ressalvas acima estão registradas como dívida técnica em `research.md`).

---

## Detalhamento de Implementação

### 1. Configuração de infraestrutura — `backend/settings/zasyncs.py`

Importado por `backend/settings/project.py` com `from .zasyncs import *  # noqa: F403`. Conteúdo:

```python
from .zenv import DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config

REDIS_HOST = config("REDIS_HOST", cast=str, default="startdev1-redis")
REDIS_PORT = config("REDIS_PORT", cast=int, default=6379)
if DEBUG:
    if FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
        REDIS_HOST = "localhost"

CELERY_BROKER_URL = "redis://{}:{}".format(REDIS_HOST, REDIS_PORT)
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CHANNEL_LAYERS = {"default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [{"address": CELERY_BROKER_URL,
                          "socket_timeout": None, "socket_connect_timeout": 5}]},
}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache",
                      "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}"}}
```

Mantém, como comentários, as alternativas de cache (`FileBasedCache`, `LocMemCache`/`DummyCache`). Em `backend/settings/apps.py`, `DJANGO_CORE_APPS` começa com `"daphne"`, depois `"channels"`; `DJANGO_THIRD_PARTY_APPS` inclui `django_celery_beat` e `django_celery_results`; `BACKEND_APPS = ["backend.eauth", "backend.utils"]`. Em `project.py`: `ASGI_APPLICATION = "backend.asgi.application"`.

### 2. Celery — `backend/celery.py` e `backend/__init__.py`

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
```

`backend/__init__.py`: `from .celery import app as celery_app` e `__all__ = ('celery_app',)`.

### 3. Sinais — `backend/utils/services/signals_syncrefresh.py`

Algoritmo de `send_signal_for_websocket_sync_refresh(inst, **kwargs)`:

1. `action = "post_save" if "created" in kwargs else "post_delete"`; `created = kwargs.get("created", False)`.
2. Se `inst._meta.model_name in ("auditlog", "metadata")` ⇒ retorna.
3. Se algum `regex.match(inst._meta.label)` de `regex_applabels_permitidos` (lista de `re.compile`, valor `[r"^utils"]`) casar:
   1. Se `settings.DEBUG`: `logger.debug(f"start: {inst.id} {app_label}.{model_name}")`.
   2. `try:` — se `hasattr(inst, "ws_sync") and not inst.ws_sync()` ⇒ retorna.
   3. Importa `ApiViewSetConstrutor` de `drfautoapi.drfautoapi` (import tardio).
   4. `inst_serialize = inst.ws_serialize()` se existir o método.
   5. Monta `message = {"action", "id": inst.id, "app": app_label, "model": model_name, "created", "timestamp": time.time() * 1000, "instance": None}`.
   6. `try:` `message["instance"] = inst_serialize` se verdadeiro; senão `ApiViewSetConstrutor.get_viewset_for_model(inst._meta.model).serializer_class(inst).data`. `except Exception`: `logger.error(_("Erro ao serializar instância para sync_refresh: {}").format(e))`.
   7. `async_to_sync(get_channel_layer().group_send)("group_sync_refresh_channel", {"type": "sync_refresh.message", "message": message})`.
   8. `except Exception`: `logger.error(_("Erro signals_sync_refresh: {}").format(e))`.

Receptor:

```python
@receiver([post_save, post_delete], dispatch_uid="signal_post_syncrefresh")
def signal_post_syncrefresh(sender, instance, **kwargs):
    send_signal_for_websocket_sync_refresh(instance, **kwargs)
```

Registro: `backend/utils/apps.py` — `UtilsConfig(AppConfig)` com `default_auto_field = "django.db.models.BigAutoField"`, `name = "backend.utils"`, `label = "utils"`, e em `ready()`: `AppConfig.ready(self)`; `from .services import signals, signals_syncrefresh`; `__all__ = [signals, signals_syncrefresh]` (evita F401 do ruff). `backend/utils/services/signals.py` e `__init__.py` existem vazios.

### 4. Consumidor — `backend/utils/consumers.py`

`class SyncRefreshConsumer(AsyncWebsocketConsumer)` (imports: `json`, `logging`, `time`, `database_sync_to_async`, `AsyncWebsocketConsumer`; `logger = logging.getLogger(__name__)`):

- `__init__(*args, **kwargs)`: importa `rules_patterns_public` de `backend.globalrules.map_rules` (import tardio), chama `super().__init__` e guarda em `self.rules_patterns_public`.
- `connect()`: `self.room_name = "sync_refresh_channel"`; `self.room_group_name = "group_%s" % self.room_name`; `group_add(room_group_name, channel_name)`; `accept()`; `except Exception` ⇒ `logger.error(f"Erro ao conectar no SyncRefreshConsumer: {e}")`.
- `disconnect(close_code)`: `group_discard(...)` com o mesmo tratamento de erro (`"Erro ao desconectar do SyncRefreshConsumer: {e}"`).
- `receive(text_data)`:
  1. `jdata = json.loads(text_data)` (fora do `try`).
  2. `try:` `type_msg = jdata.get("type", "")`.
     - `ping` ⇒ `send(json.dumps({"type":"pong","message":{"timestamp_server": time.time()*1000, "ping_now": jdata.get("ping_now","")}}))` e `return`.
     - `command` ⇒ lê `command`, `app`, `model`, `params` (padrão `{}`), `user = self.scope.get("user")`; se `not command` ⇒ envia `{"type":"command_result","command":command,"error":"Comando não especificado"}` e `return`.
  3. `except Exception as e:` loga `"Erro ao processar mensagem recebida no SyncRefreshConsumer: {e}"` e envia `{"type":"command_result","command": jdata.get("command",""),"error": str(e)}` (não retorna).
  4. `group_send(room_group_name, {"type": "sync_refresh_message", "message": jdata})`.
- `command_result(event)`: envia `{"type":"command_result","command": event["command"],"result": event["result"]}`.
- `sync_refresh_message(event)`:
  1. `message = event["message"]`; `app = message.get("app")`; `model = message.get("model")`; `u = self.scope.get("user")`.
  2. `key = f"{app}:{model}"`; `perms_publicas = self.rules_patterns_public.get(key, set())`; `perm_detail = f"{app}.detail_{model}"`; `perm_view = f"{app}.view_{model}"`.
  3. `if u.is_anonymous and not perms_publicas` ⇒ `detail_perm = False`; `elif u.is_anonymous` ⇒ `perm_detail in perms_publicas or perm_view in perms_publicas`; `elif not u.is_superuser` ⇒ `await database_sync_to_async(u.has_perm)(perm_detail)` e, se falso, o mesmo para `perm_view`; `else` ⇒ `True`.
  4. `try: if not detail_perm: del message["instance"]` `except KeyError: pass`.
  5. `await self.send(text_data=json.dumps(event))`.
  6. `except Exception` ⇒ loga e envia `{"type":"error","error":str(e)}`.

Há também logs `logger.debug` (`'passou sync_refresh_message'`, `Received message: ...`).

`rules_patterns_public` (`backend/globalrules/map_rules.py`): dicionário `"app:modelo"` → conjunto de strings `app + RP + modelo`, com `RP_LIST='.list_'`, `RP_VIEW='.view_'` etc. (feature 003).

### 5. Roteamento — `backend/utils/routing.py` e `backend/asgi.py`

```python
websocket_urlpatterns = [path("ws/sync/", consumers.SyncRefreshConsumer.as_asgi())]
```

`asgi.py`: `application = ProtocolTypeRouter({"http": ASGIHandler(), "websocket": AuthMiddlewareStack(URLRouter(backend_routing.websocket_urlpatterns))})`, com `django.setup()` antes (e `from django.core.handlers.asgi import ASGIHandler`; `from channels.auth import AuthMiddlewareStack`).

### 6. Tarefa e views — `backend/utils/services/tasks.py`, `backend/utils/views.py`, `backend/utils/urls.py`

- `debug_task`: `@app.task(queue="celery", bind=True) def debug_task(self)`: `teste = Teste(); teste.teste = str(random()); teste.save(); logger.info(f"teste cadastrado {teste.id} - {teste.teste}"); return f"result of teste {teste.id}"` (`logger = get_task_logger(__name__)`; `from backend.celery import app`).
- `wstest_index(request, slug)` → `render(request, "wstest_index.html", {})`.
- `testws(request)` → `teste = Teste.objects.order_by("id").last() or Teste()`; `debug_task.apply_async((), countdown=2)`; `JsonResponse(dict(message="ultimo cadastrado. task chamada para criar novo", teste=model_to_dict(teste)))`.
- `urls.py`: `re_path(r"^testws/", views.testws, name="testws")` e `re_path(r"^wstest/(?P<slug>[^.]*)$", views.wstest_index, name="wstest_index")` (além de `^teste/` e `^media/(?P<path>.*)$`, de outras features).
- `_templates/wstest_index.html`: `{% extends 'base.html' %}{% block base_content %}<router-view></router-view>{% endblock %}`. O diretório `_templates` está em `TEMPLATES["DIRS"]` (`backend/settings/frontend.py`).

### 7. Frontend — `WebSocketManager` (`_frontend/src/js/utils/ws/WebSocketManager.js`)

Classe exportada por padrão. Construtor: `protocol = location.protocol === 'https:' ? 'wss://' : 'ws://'`; `url = protocol + location.host + '/ws/sync/'`; `reconnectAttempts = 0`, `maxReconnectAttempts = 10`, `reconnectInterval = 1000`, `heartbeatInterval = 60000`, `listeners = new Map()`; chama `connect()`.

- `connect()`: `new WebSocket(url)`; `onopen` ⇒ zera tentativas, envia `ping` (`ping_now: performance.now()`), `startHeartbeat()`, `emit('connected')`; `onmessage` ⇒ `JSON.parse`; `type === 'ping'` ⇒ responde `pong`; `type === 'pong'` ⇒ emite `message` com `{type:'pong', pong, ping, timestamp_server, server_time_diff: (Date.now() - ts) - (pong_now - ping_now)/2}`; demais ⇒ `emit('message', data)`; `onclose` ⇒ `stopHeartbeat()`, `emit('disconnected')`, `handleReconnect()`; `onerror` ⇒ `console.error` e `emit('error', error)`.
- `handleReconnect()`: se `reconnectAttempts < max` ⇒ incrementa e `setTimeout(connect, reconnectInterval * 2 ** reconnectAttempts)`.
- `startHeartbeat()/stopHeartbeat()`: `setInterval` de 60 s enviando `ping` se `readyState === OPEN`.
- `send(data)`: envia `JSON.stringify` se aberto; senão reagenda uma vez com o mesmo atraso exponencial.
- `on(event, cb)` / `emit(event, data)` sobre `listeners`.

### 8. Frontend — `SyncStore` (`_frontend/src/js/stores/pinea/SyncStore.js`)

`defineStore('syncStore', {state, actions})` (sem getters). Importa `TimerWorkerService`, `WebSocketManager`, `Resources` (`~@/js/utils/resources`, `Resources.Utils.fetch` ⇒ `GET /api/<app>/<model>/[id/][action/]?query`), `inject` de `vue`; usa `_.each` (lodash global).

- `initialize()`: sai se já houver `wsManager`; cria `new WebSocketManager()`; `on('connected')` ⇒ `wsConnected = true`; `on('disconnected')` ⇒ `false`; `on('error')` ⇒ vazio; `on('message', data)`: `pong` ⇒ `lastServerSync = data`; `sync_refresh.message` ⇒ `handleSyncMessage(data.message)`.
- `UPDATE_DATA_CACHE({key, value})`:
  1. Se `value.timestamp_frontend` e há item antigo com `timestamp_frontend` e `value.timestamp_frontend <= antigo` ⇒ retorna.
  2. Se `value.__label__`: para cada propriedade objeto não nulo cujo `__label__` exista ⇒ divide por `_` em `[app, model]`, registra modelo, chama recursivamente `UPDATE_DATA_CACHE` e substitui o objeto por seu `id`; idem para arrays de objetos com `__label__` (vira array de ids). Senão: `value.__label__ = key`.
  3. `data_cache[key] ||= {}`; `data_cache[key][value.id] = value`.
- `DELETE_DATA_CACHE({key, value})`: apaga `data_cache[key][value.id]` se existir. `UPDATE_DATA_CACHE_CRONOMETRO`: grava sem checagem.
- `startLocalCronometro(id)` ⇒ `TimerWorkerService.startTimer(id, () => {}, 500)`; `stopLocalCronometro(id)` ⇒ `stopTimer(id)`.
- `fetchSync({app, model, id, action, params, only_first_page=false, force_fetch=true})`: auto-registra o modelo; se `!force_fetch` devolve cache (`id` ⇒ item; sem `id` ⇒ coleção) quando existir; monta `metadata = {app, model, id?, action?, params?}` (arrays de `params` viram `join(',')`); sem `id`: `params` padrão `{page: 1, o: 'id'}` e preenche `page`/`o` ausentes; `timestamp_frontend = Date.now()`; chama `Resources.Utils.fetch(metadata)`; `results = response.data.results ?? (Array.isArray(data) ? data : [data])`; para cada um `UPDATE_DATA_CACHE({key: 'app_model', value: {...value, timestamp_frontend}})`; se `!only_first_page && response.data.pagination?.next_page` ⇒ recursão com `params: {...params, page: next_page}`; retorna `data_cache[uri]`.
- `sendSyncMessage(message)`: envia se `wsManager && wsConnected`, senão `console.warn('WebSocket não conectado. Mensagem não enviada:', message)`.
- `handleSyncMessage({app, model, id, action, instance, timestamp})`: ignora se modelo não registrado; `key = app_model`; `inst = {...(instance||{}), timestamp_frontend: timestamp}`; `post_delete` ⇒ `delete data_cache[key][id]`; `post_save` ⇒ `eventBus.emit('sync-refresh', {app, model, id})`, depois: se `!inst.id` ⇒ (item em cache com `timestamp_frontend < timestamp` **ou** item ausente) ⇒ `fetchSync({app, model, id})`; senão `UPDATE_DATA_CACHE({key, value: inst})`.
- `invalidateDataCache(apps, models)`, `cleanInvalidatedDataCache(app, model)`, `invalidateCacheItems(app, model, ids)`: conforme o contrato.
- `registerModels(app, models)`: `models[app] ||= {}`; cada modelo ausente recebe `Date.now()`.
- `syncModels(apps_models_params, global_params={}, force_fetch=true)`: para cada `{app, models, params}` e modelo ⇒ `fetchSync({app, model, params: {...(params||{}), ...global_params}, force_fetch}).then(() => cleanInvalidatedDataCache(app, model))`.

### 9. Frontend — demais arquivos

- `EventBus.js`: classe com `events = {}`; `on`, `off` (remove a primeira ocorrência da função), `emit`; `export default new EventBus()`. Fornecido em `main.js` por `app.provide('EventBus', EventBus)` e `app.config.globalProperties.$EventBus = EventBus`.
- `TimerWorkerService.js`: classe com `worker`, `callbacks = new Map()`, `queue = []`; `init()` cria o Worker de `Blob` (`application/javascript`) cujo código mantém `Map` de `setInterval`; `START_TIMER` (limpa timer anterior, `interval || 1000`, posta `TIMER_TICK` com `timerId` e `Date.now()`), `STOP_TIMER`; `startTimer(timerId, callback, interval = 1000)`; `stopTimer(timerId)`; `export default new TimerWorkerService()`.
- `MessageStore.js`: `defineStore("messageStore", {state: {messages: [], id: 0}, getters: {getMessages}, actions: {addMessage(m){m.id = this.id++; this.messages.unshift(m)}, shiftMessage(){return this.messages.shift()}, removeMessage(id){this.messages = this.messages.filter(m => m.id !== id)}}})`.
- `AlertMessage.vue`: `<div class="alert fade show alert-dismissible" :class="['alert-' + message.type]" role="alert">` com `<strong v-if="message.title">`, texto e botão `btn-close` (`data-bs-dismiss="alert"`); `onMounted` agenda `removeMessage(props.message.id)` após `message.timeout` ms se houver.
- `DisplayMessage.vue`: `v-for` sobre `messageStore.getMessages` renderizando `AlertMessage` (`:id="\`alert-${message.id}\`"`), CSS `.display-message {position: fixed; bottom: 0; right: 0; z-index: 1000; padding: 1em 2em}`.
- `Alert.vue`: `div.alert.alert-info.fade.show.alert-dismissible` com `<slot />` e botão de fechar; registrado como `emf-alert` em `registerComponents.js`.
- `WsTest.vue`: `<script setup>`; `bus = inject('EventBus')`; `count = ref(1)`, `title = ref('WsTest!')`; botão `btn btn-primary` chama `increment` (`count++`; `fetch('/testws/')` ⇒ JSON ⇒ `messageStore.addMessage({type:'success', text: \`${data.message} ${data.teste.teste}\`, timeout: 5000})`); `onMounted` ⇒ `bus.on('sync-refresh', msg => ...)` filtrando `observer = {apps:['utils'], models:['teste']}` e adicionando `{type:'info', title:'Sync Refresh! ', text:\`sync-refresh ${id}  ${app} ${model}\`, timeout:5000}`.
- `App.vue`: `<slot /> <DisplayMessage /> <div id="modalApp" ref="modalApp" />`; no `<script setup>`: `const syncStore = useSyncStore(); syncStore.initialize(); const authStore = useAuthStore(); authStore.loginStatus(); ... syncStore.registerModels('utils', ['teste'])`.
- `routers.js`: rota `{path: '/wstest/', name: 'index_link', component: () => import('~@/views/WsTest.vue')}` antes do 404 (`/:pathMatch(.*)`).

### 10. Ordem e dependências de execução em tempo de execução

1. `django.setup()` → `UtilsConfig.ready()` registra o receptor.
2. Servidor ASGI sobe; navegador carrega `base.html` (Vite, feature 007) → `App.vue` → `initialize()` abre o WebSocket.
3. Escrita em `Teste` → sinal → `group_send` → Redis → consumidores → cliente → `SyncStore` → `EventBus`.
