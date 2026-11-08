# Início Rápido: Validação da Sincronização em Tempo Real

**Branch**: `006-sincronizacao-tempo-real` | **Data**: 2026-11-08

## Pré-requisitos

- Ambiente de desenvolvimento no ar (`./rdev.sh [nome]` ou `./uupdev.sh [nome]`; ver `010-docker-desenvolvimento`) com Redis, PostgreSQL, `runserver` (Daphne) e worker Celery (iniciado por `_docker/dev/start-dev.sh` com `celery multi start ... -A backend -Q:1 celery`).
- `backend/.env` com `SECRET_KEY` (o script completa `REDIS_HOST`, `FOLDER_DEBUG_CONTAINER`, `DEBUG` etc.).
- Migrações aplicadas (`python manage.py migrate`), que criam a tabela de `Teste` e as de `django_celery_*`.

## 1. Verificação manual ponta a ponta

1. Abra duas abas em `http://localhost:9099/wstest/` (porta `APP_PORT` do dev). No console do navegador aparece `WebSocket conectado`.
2. Em uma aba, clique no botão com o contador. Resultado esperado:
   - imediatamente: alerta verde (`success`) com `ultimo cadastrado. task chamada para criar novo <valor do último Teste>` (some em 5 s);
   - ~2 s depois, em **ambas** as abas: alerta azul (`info`) `Sync Refresh!  sync-refresh <id>  utils teste` (some em 5 s).
3. Verifique o resultado no banco/admin: um novo `Teste` com número aleatório em `teste` (ex.: `/teste/` ou `/system/utils/teste/`).
4. Crie/edite/exclua um `Teste` por `/teste/` (CRUD) e veja novos alertas nas abas abertas (o `post_delete` não gera alerta, apenas remove do cache).

### Verificações diretas

```bash
curl -s http://localhost:9099/testws/           # JSON com "message" e "teste"; agenda a task (countdown=2)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9099/wstest/    # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9099/wstest/abc # 200 (slug sem ponto)
```

Cliente WebSocket de linha de comando (opcional; requer `websocat` ou equivalente):

```bash
websocat ws://localhost:9099/ws/sync/
{"type":"ping","ping_now":1}
# => {"type": "pong", "message": {"timestamp_server": ..., "ping_now": 1}}
{"type":"command"}
# => {"type": "command_result", "command": "", "error": "Comando não especificado"}
```

Em seguida, `curl http://localhost:9099/testws/` e observe, no terminal do `websocat` (anônimo), a mensagem `sync_refresh.message` com `instance` (o `Teste` tem leitura pública).

### Verificação de permissões

- Anônimo, modelo com leitura pública (`Teste`): `instance` presente.
- Modelo sem permissão pública (por exemplo, um modelo de `utils` ausente de `rules_patterns_public`, ou remova temporariamente o `set(__base_view__)` de `Teste` em `backend/globalrules/map_rules.py`): o anônimo recebe a mensagem **sem** `instance`; o superusuário logado recebe com `instance`.

### Verificação de reconexão

1. Com `/wstest/` aberta, reinicie o servidor ASGI (reinicie o contêiner da aplicação do ambiente de desenvolvimento).
2. No console: `WebSocket desconectado` → `Tentativa de reconexão 1` (após 2 s), `2` (4 s)... até reconectar (`WebSocket conectado`).
3. No console do navegador: `useSyncStore().wsConnected` volta a `true` e `useSyncStore().lastServerSync.server_time_diff` é numérico.

### Verificação do cache (console do navegador, com `pinia` acessível)

```js
const s = useSyncStore()
await s.fetchSync({ app: 'utils', model: 'teste' })   // preenche s.data_cache.utils_teste (todas as páginas)
s.invalidateDataCache(['utils'], ['teste'])           // timestamp_frontend = -1
s.syncModels([{ app: 'utils', models: ['teste'] }])   // refaz e remove itens que sumiram
```

## 2. Validações automáticas existentes

```bash
pytest                  # suíte atual (não há testes específicos desta feature)
ruff check .            # Python (E, F, I)
npm run lint            # ESLint/Prettier do frontend
```

## 3. Testes automatizados a criar (VIII — Qualidade verificável)

O projeto não possui `pytest-asyncio`; use `channels.testing.WebsocketCommunicator` dentro de `async_to_sync` (ou adicione `pytest-asyncio` ao grupo de testes). Use um layer em memória para não depender de Redis:

```python
from django.test import override_settings
CHANNEL_LAYERS_TEST = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
```

Teste com `@pytest.mark.django_db(transaction=True)` quando o consumidor consultar o banco (`has_perm`).

| Arquivo sugerido | Casos |
|------------------|-------|
| `backend/utils/tests.py` (ou `_tests/test_sync_realtime.py`) | 1. `ping` ⇒ `pong` com `timestamp_server` e `ping_now` ecoado, sem retransmissão para outro cliente. 2. `{"type":"command"}` ⇒ `command_result` com `error`. 3. Mensagem arbitrária é retransmitida como `sync_refresh_message` aos demais clientes (documenta o risco). 4. `post_save` de `Teste` ⇒ cliente anônimo recebe `sync_refresh.message` com `action="post_save"`, `created=true`, `app="utils"`, `model="teste"`, `instance` presente (público). 5. `delete()` ⇒ `action="post_delete"`. 6. Modelo sem permissão pública / usuário sem `view_` ⇒ sem `instance`; superusuário ⇒ com `instance`. 7. `ws_sync()` retornando `False` (via mock/monkeypatch na instância) ⇒ nada publicado. 8. Modelo `Metadata` e apps fora de `^utils` ⇒ nada publicado. 9. Falha em `get_channel_layer().group_send` (mock levantando exceção) ⇒ `save()` conclui sem erro. 10. `GET /testws/` ⇒ 200 JSON com as chaves `message`/`teste` e `debug_task.apply_async` chamado com `countdown=2` (mock). 11. `GET /wstest/` e `/wstest/qualquer` ⇒ 200 e template `wstest_index.html`. 12. `debug_task.apply()` (execução síncrona) cria um `Teste` e retorna `result of teste <id>`. 13. `reverse('backend.utils:testws')` / `wstest_index` resolvem (`app_name = "backend.utils"`). |

Frontend (sem suíte hoje; sugestão com Vitest, se adotado): `WebSocketManager` (backoff e heartbeat com timers falsos), `SyncStore.UPDATE_DATA_CACHE` (descarte de dado antigo), `handleSyncMessage` (ignora modelo não registrado; `post_delete`; `post_save` com e sem `instance`), `invalidateDataCache` + `cleanInvalidatedDataCache`, `MessageStore` (`addMessage` incrementa `id`, `unshift`, `removeMessage`).

## 4. Solução de problemas

| Sintoma | Causa provável |
|---------|---------------|
| Console: `Erro WebSocket` e reconexões infinitas | Servidor sem ASGI/Daphne ou Nginx sem `proxy_pass` de `/ws/` (ver 011); Redis fora do ar (o `connect` não aceita) |
| `/testws/` responde mas nada é criado | Worker Celery parado ou sem a tarefa registrada (`celery -A backend inspect registered`) ou fila diferente de `celery` |
| Mensagem chega sem `instance` | Usuário sem `view_`/`detail_` do modelo (esperado) |
| Salvar `Teste` demora ~5 s | Redis indisponível (`socket_connect_timeout = 5`); verifique `REDIS_HOST`/`FOLDER_DEBUG_CONTAINER` |
| Nada acontece ao salvar outro modelo | Apenas apps que casam com `^utils` são sincronizados (`regex_applabels_permitidos`) |
