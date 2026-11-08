# Contrato: WebSocket `ws/sync/`

**Feature**: `006-sincronizacao-tempo-real` | Arquivos: `backend/utils/routing.py`, `backend/utils/consumers.py`, `backend/asgi.py`

## Endpoint

| Item | Valor |
|------|-------|
| URL | `ws://<host>/ws/sync/` (`wss://` quando a página é `https:`) |
| Rota | `path("ws/sync/", consumers.SyncRefreshConsumer.as_asgi())` em `websocket_urlpatterns` (`backend/utils/routing.py`) |
| Autenticação | Sessão do Django via `AuthMiddlewareStack` (cookie de sessão); anônimos são aceitos (`scope["user"]` anônimo) |
| Origem | Sem `AllowedHostsOriginValidator` (nenhuma validação de origem) |
| Grupo | `group_sync_refresh_channel` |
| Subprotocolos / parâmetros | Nenhum |
| Roteamento de produção | `/ws/` → Daphne (Nginx) — ver `011-docker-producao` |

`backend/asgi.py`:

```python
application = ProtocolTypeRouter({
    "http": ASGIHandler(),
    "websocket": AuthMiddlewareStack(URLRouter(backend_routing.websocket_urlpatterns)),
})
```

Ordem importante: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')` e `django.setup()` ocorrem após `import backend.utils.routing` (no topo do arquivo); por isso `consumers.py` só importa `rules_patterns_public` (que importa modelos) dentro de `SyncRefreshConsumer.__init__`, evitando carregar modelos antes do `django.setup()` (inferência do código).

## Ciclo de vida

1. **connect**: `group_add("group_sync_refresh_channel", channel_name)` e `accept()`. Falha ⇒ log `Erro ao conectar no SyncRefreshConsumer: ...` e a conexão não é aceita.
2. **disconnect**: `group_discard(...)`; falha é logada.
3. **receive**: ver abaixo.

## Mensagens cliente → servidor

### `ping`

```json
{"type": "ping", "ping_now": 12345.6}
```

Resposta (somente ao remetente; não retransmite):

```json
{"type": "pong", "message": {"timestamp_server": 1762627728000.123, "ping_now": 12345.6}}
```

`timestamp_server = time.time() * 1000`; `ping_now` é eco (`""` se ausente).

### `command`

```json
{"type": "command", "command": "", "app": "utils", "model": "teste", "params": {}}
```

- `command` vazio/ausente ⇒ resposta ao remetente `{"type":"command_result","command":"","error":"Comando não especificado"}` e **fim** (não retransmite).
- `command` preenchido ⇒ nenhuma execução; cai na retransmissão (abaixo).

### Qualquer outro JSON

Retransmitido a todo o grupo (inclusive ao remetente):

```python
await self.channel_layer.group_send(
    "group_sync_refresh_channel", {"type": "sync_refresh_message", "message": jdata}
)
```

Cada cliente recebe `{"type":"sync_refresh_message","message": <jdata>}` (note o **underscore**; o `SyncStore` não o trata). Passa pelo mesmo filtro de permissão de `instance` usando `message.app`/`message.model` fornecidos pelo cliente.

### Erros

- Corpo que não é JSON ⇒ `json.JSONDecodeError` não capturado ⇒ a conexão é encerrada.
- Exceção no `try` (ex.: JSON que não é objeto) ⇒ `{"type":"command_result","command":"","error":"<str(e)>"}` e o fluxo segue para a retransmissão.

## Mensagens servidor → cliente

### Mudança de modelo (`sync_refresh.message`)

Origem: `backend/utils/services/signals_syncrefresh.py` (`group_send` com `type = "sync_refresh.message"`; despachado ao método `sync_refresh_message`).

```json
{
  "type": "sync_refresh.message",
  "message": {
    "action": "post_save",
    "id": 7,
    "app": "utils",
    "model": "teste",
    "created": true,
    "timestamp": 1762627728000.123,
    "instance": {"id": 7, "teste": "0.123", "__str__": "0.123", "metadata": null, "link_detail_backend": ""}
  }
}
```

| Campo | Descrição |
|-------|-----------|
| `action` | `post_save` ou `post_delete` |
| `id` | PK do objeto |
| `app` / `model` | `app_label` / `model_name` |
| `created` | `true` apenas em criação (`post_save`); `false` em edição e exclusão |
| `timestamp` | Milissegundos (servidor) |
| `instance` | Serialização do objeto, ou `null`; **ausente** quando o destinatário não tem permissão |

Regra de permissão por destinatário (em `sync_refresh_message`): `perm_detail = "<app>.detail_<model>"`, `perm_view = "<app>.view_<model>"`, `perms_publicas = rules_patterns_public.get("<app>:<model>", set())`.

| Destinatário | `instance` mantida se |
|--------------|----------------------|
| Anônimo, sem permissões públicas para o modelo | nunca |
| Anônimo, com permissões públicas | `perm_detail` ou `perm_view` ∈ `perms_publicas` |
| Autenticado não superusuário | `has_perm(perm_detail)` ou `has_perm(perm_view)` |
| Superusuário | sempre |

A remoção é `del message["instance"]` (silenciando `KeyError`) e em seguida `send(json.dumps(event))`; como `message` é o mesmo objeto de `event["message"]`, a remoção vale para o que é enviado.

### Outras mensagens

| Mensagem | Quando |
|----------|--------|
| `{"type":"error","error":"<texto>"}` | Exceção em `sync_refresh_message` |
| `{"type":"command_result","command":...,"result":...}` | Handler `command_result(event)`: só se alguém enviar evento `command_result` ao grupo (hoje ninguém envia) |

## Comportamento do cliente (`WebSocketManager`)

| Item | Valor |
|------|-------|
| Reconexão | até `maxReconnectAttempts = 10`; atraso `reconnectInterval (1000) × 2^tentativa` (2 s, 4 s … 1024 s); contador zerado em `onopen` |
| Heartbeat | ping imediato ao abrir e a cada `heartbeatInterval = 60000` ms |
| `ping` recebido do servidor | responde `{"type":"pong","pong_now":...}` (o servidor atual nunca envia `ping`) |
| `pong` recebido | emite `message` com `{type:'pong', pong, ping, timestamp_server, server_time_diff}` |
| Eventos emitidos | `connected`, `disconnected`, `error`, `message` (via `on(evento, cb)`) |
| Envio com socket fechado | reagenda uma única tentativa após `1000 × 2^reconnectAttempts` ms; descarta se ainda não aberto |
