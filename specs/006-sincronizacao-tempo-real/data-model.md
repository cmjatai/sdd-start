# Modelo de Dados: Sincronização em Tempo Real

**Branch**: `006-sincronizacao-tempo-real` | **Data**: 2026-11-08

Esta funcionalidade **não cria tabelas novas**. Ela reutiliza o modelo `Teste` (app `utils`, criado em `001-fundacao-projeto-django`, migração `backend/utils/migrations/0001_initial.py`) como demonstração e usa as tabelas de apoio do Celery (`django_celery_beat`, `django_celery_results`) já fornecidas pelas bibliotecas. Abaixo, as estruturas de dados relevantes: o modelo `Teste`, a mensagem de sincronização, os grupos de canal, o estado do frontend e as configurações.

## 1. Modelo `Teste` (referência — definido em 001)

Arquivo: `backend/utils/models.py`

| Campo | Tipo | Opções |
|-------|------|--------|
| `id` | `BigAutoField` | PK automática (`default_auto_field = "django.db.models.BigAutoField"` em `UtilsConfig`) |
| `teste` | `CharField` | `max_length=100`, `verbose_name=_("Teste")`, sem `null`/`blank`/`default` (obrigatório em formulários) |

`Meta`: `verbose_name = _("Teste")`, `verbose_name_plural = _("Testes's")`, `ordering = ("teste",)`. `__str__` devolve `self.teste`. Sem relacionamentos, sem unicidade, sem permissões customizadas.

Regras de acesso (feature 003, `backend/globalrules/map_rules.py`): `(Teste, __base__, set(__base_view__))` no grupo Administrador do Sistema — o grupo recebe `list_`, `view_`, `add_`, `change_`, `delete_`; as permissões **públicas** da API são `utils.list_teste` e `utils.view_teste`. Daí `rules_patterns_public["utils:teste"] == {"utils.list_teste", "utils.view_teste"}`. O CRUD `TesteCrud` (`backend/utils/views.py`, `public = [RP_LIST, RP_VIEW]`) está montado em `^teste/` (feature 004).

Comportamentos (sinais): todo `post_save`/`post_delete` de `Teste` dispara `signal_post_syncrefresh` (ver `plan.md`, seção 3). Não há `save()` customizado nem ganchos `ws_sync()`/`ws_serialize()` implementados em `Teste` (são opcionais e hoje nenhum modelo os define).

Ganchos opcionais de modelo (contrato, não implementados em `Teste`):

| Método | Retorno | Efeito |
|--------|---------|--------|
| `ws_sync()` | `bool` | Se existir e retornar falso, a mudança não é publicada |
| `ws_serialize()` | `dict` ou falsy | Se retornar valor verdadeiro, é usado como `instance`; senão usa-se o serializer do viewset da API |

## 2. Mensagem de sincronização (servidor → cliente)

Construída em `backend/utils/services/signals_syncrefresh.py`:

| Chave | Tipo | Observação |
|-------|------|-----------|
| `action` | `"post_save"` \| `"post_delete"` | `post_save` se `"created" in kwargs` (o sinal `post_save` sempre envia `created`); caso contrário `post_delete` |
| `id` | inteiro | `inst.id` |
| `app` | string | `inst._meta.app_label` (ex.: `utils`) |
| `model` | string | `inst._meta.model_name` (ex.: `teste`) |
| `created` | bool | `kwargs.get("created", False)` |
| `timestamp` | número (ms, float) | `time.time() * 1000` no servidor |
| `instance` | objeto \| `null` | Dados serializados; removida na entrega (`del message["instance"]`) quando o destinatário não tem permissão |

Envelope enviado ao grupo: `{"type": "sync_refresh.message", "message": {...}}`. O Channels converte `.` em `_` e despacha para o método `sync_refresh_message` do consumidor, que serializa o `event` inteiro (`json.dumps(event)`) ao cliente: `{"type":"sync_refresh.message","message":{...}}`.

Conteúdo típico de `instance` para `Teste` (serializer gerado pela feature 005): `id`, `teste`, `__str__`, `metadata`, `link_detail_backend`.

## 3. Mensagens do protocolo cliente ↔ servidor

| Direção | Estrutura | Uso |
|---------|-----------|-----|
| cliente → servidor | `{"type":"ping","ping_now":<performance.now()>}` | Heartbeat/latência |
| servidor → cliente | `{"type":"pong","message":{"timestamp_server":<ms>,"ping_now":<eco>}}` | Resposta ao ping |
| cliente → servidor | `{"type":"command","command":"...","app":"...","model":"...","params":{}}` | Previsto; nada é executado |
| servidor → cliente | `{"type":"command_result","command":"","error":"Comando não especificado"}` | Quando `command` vazio |
| servidor → cliente | `{"type":"error","error":"<texto>"}` | Falha ao entregar `sync_refresh_message` |
| servidor → grupo | `{"type":"sync_refresh_message","message":<JSON do cliente>}` | Retransmissão de mensagens quaisquer do cliente |

Handler `command_result(self, event)` existe no consumidor mas nenhum código envia eventos `command_result` ao grupo (código morto; ver `research.md`).

Detalhes completos em `contracts/websocket-sync.md`.

## 4. Grupo de canal

| Item | Valor |
|------|-------|
| `room_name` | `sync_refresh_channel` |
| Nome do grupo | `group_sync_refresh_channel` |
| Membros | Todos os consumidores `SyncRefreshConsumer` conectados |
| Backend | `channels_redis.core.RedisChannelLayer` |

## 5. Estado do frontend

### 5.1 `SyncStore` (`_frontend/src/js/stores/pinea/SyncStore.js`, id Pinia `syncStore`)

| Estado | Tipo inicial | Descrição |
|--------|--------------|-----------|
| `wsManager` | `null` | Instância de `WebSocketManager` (criada em `initialize()`) |
| `wsConnected` | `false` | `true` após `connected`, `false` após `disconnected` |
| `lastServerSync` | `null` | Último objeto `pong` convertido (inclui `server_time_diff`) |
| `models` | `{}` | `models[app][model] = Date.now()` — modelos registrados como sincronizáveis |
| `data_cache` | `{}` | `data_cache['<app>_<modelo>'][<id>] = item` |
| `eventBus` | `inject('EventBus')` | Barramento de eventos |

Item do cache: campos da instância + `__label__` (`'<app>_<modelo>'`, inserido se ausente) + `timestamp_frontend` (ms; `-1` = invalidado).

### 5.2 `MessageStore` (`_frontend/src/js/stores/MessageStore.js`, id `messageStore`)

| Estado | Tipo | Descrição |
|--------|------|-----------|
| `messages` | `[]` | Mensagens exibidas (mais novas primeiro) |
| `id` | `0` | Contador incremental para `message.id` |

Mensagem: `{ id, type ('success'|'info'|...), title?, text, timeout? (ms) }` — `type` vira a classe `alert-<type>` do Bootstrap.

### 5.3 `EventBus` (`_frontend/src/js/EventBus.js`)

Singleton com `events: { <nome>: [fn, ...] }`. Evento usado: `sync-refresh` com payload `{app, model, id}`.

### 5.4 `WebSocketManager` (`_frontend/src/js/utils/ws/WebSocketManager.js`)

Atributos: `url`, `ws`, `reconnectAttempts`, `maxReconnectAttempts = 10`, `reconnectInterval = 1000`, `heartbeatInterval = 60000`, `heartbeatTimer`, `listeners` (`Map<evento, fn[]>`).

### 5.5 `TimerWorkerService` (`_frontend/src/js/utils/timer/TimerWorkerService.js`)

Singleton com `worker` (Web Worker criado a partir de `Blob`), `callbacks` (`Map<timerId, fn>`) e `queue`. Mensagens do worker: `START_TIMER {timerId, interval}`, `STOP_TIMER {timerId}` → `TIMER_TICK {timerId, timestamp}`.

## 6. Configuração (sem segredos)

| Chave/variável | Padrão | Arquivo |
|----------------|--------|---------|
| `REDIS_HOST` | `startdev1-redis` (`localhost` em `DEBUG` fora do contêiner) | `backend/settings/zasyncs.py` |
| `REDIS_PORT` | `6379` | idem |
| `CELERY_BROKER_URL` | `redis://<REDIS_HOST>:<REDIS_PORT>` | idem |
| `CELERY_RESULT_BACKEND` | `django-db` | idem |
| `CELERY_CACHE_BACKEND` | `django-cache` | idem |
| `CELERY_BEAT_SCHEDULER` | `django_celery_beat.schedulers.DatabaseScheduler` | idem |
| `CHANNEL_LAYERS["default"]` | `RedisChannelLayer` com `hosts=[{address: CELERY_BROKER_URL, socket_timeout: None, socket_connect_timeout: 5}]` | idem |
| `CACHES["default"]` | `RedisCache` em `redis://<REDIS_HOST>:<REDIS_PORT>` | idem |
| `ASGI_APPLICATION` | `backend.asgi.application` | `backend/settings/project.py` |

## 7. Migrações

Nenhuma migração nova. `Teste` nasce na `0001_initial` do app `utils` (feature 001). As tabelas do Celery são criadas pelas migrações das bibliotecas `django_celery_beat` e `django_celery_results`.
