# Contrato: Endpoints HTTP, tarefa Celery e configuração

**Feature**: `006-sincronizacao-tempo-real` | Arquivos: `backend/utils/urls.py`, `backend/utils/views.py`, `backend/utils/services/tasks.py`, `backend/celery.py`, `backend/settings/zasyncs.py`

## Endpoints HTTP (app `utils`, incluído na raiz por `backend/urls.py`: `path("", include("backend.utils.urls"))`)

`app_name = UtilsConfig.name` (`backend.utils`).

| Método | Rota (regex) | `name` | View | Permissão |
|--------|--------------|--------|------|-----------|
| GET | `^testws/` | `testws` | `views.testws` | Nenhuma (público) |
| GET | `^wstest/(?P<slug>[^.]*)$` | `wstest_index` | `views.wstest_index` | Nenhuma (público) |
| — | `^teste/` | (CRUD) | `TesteCrud.get_urls()` | Ver feature 004 (leitura pública: `RP_LIST`, `RP_VIEW`) |

### `GET /testws/`

- Efeito colateral: `debug_task.apply_async((), countdown=2)` (cria um `Teste` ~2 s depois).
- Resposta `200 application/json`:

```json
{
  "message": "ultimo cadastrado. task chamada para criar novo",
  "teste": {"id": 7, "teste": "0.5719..."}
}
```

`teste` = `model_to_dict(Teste.objects.order_by("id").last() or Teste())`; sem registros: `{"id": null, "teste": ""}`.
- Não exige autenticação nem valida CSRF (GET).

### `GET /wstest/<slug>`

- `slug` = qualquer texto sem ponto (inclusive vazio: `/wstest/`).
- Renderiza `_templates/wstest_index.html` (`{% extends 'base.html' %}`; bloco `base_content` contém `<router-view></router-view>`). O Vue Router (`_frontend/src/js/routers.js`) trata `/wstest/` (`name: 'index_link'`, `WsTest.vue`).
- `request` → `render(request, "wstest_index.html", {})`.

## Tarefa Celery

| Item | Valor |
|------|-------|
| Nome registrado | `backend.utils.services.tasks.debug_task` |
| Decorador | `@app.task(queue="celery", bind=True)` |
| Fila | `celery` (padrão do Celery) |
| Argumentos | nenhum |
| Efeito | `Teste(teste=str(random())).save()`; log `teste cadastrado <id> - <valor>` |
| Retorno | `"result of teste <id>"` (gravado em `django-db`) |
| Aplicação Celery | `backend/celery.py`: `Celery('backend')`, `config_from_object('django.conf:settings', namespace='CELERY')`, `autodiscover_tasks(lambda: settings.INSTALLED_APPS)`; exportada em `backend/__init__.py` como `celery_app` |

Worker (referência dos scripts Docker, feature 010/011): `celery multi start 1 -A backend -l INFO -Q:1 celery -c:1 1 ...`.

## Mensagens de interface (cliente)

`useMessageStore().addMessage({ type, title?, text, timeout? })`:

| Campo | Tipo | Uso |
|-------|------|-----|
| `type` | string | Sufixo da classe `alert-<type>` (`success`, `info`, `danger`...) |
| `title` | string (opcional) | Texto em `<strong>` |
| `text` | string | Corpo |
| `timeout` | número ms (opcional) | Remoção automática via `removeMessage(id)` |

Componentes: `DisplayMessage.vue` (contêiner fixo inferior direito, `z-index: 1000`), `AlertMessage.vue` (props `message: Object`, `id: String`), `Alert.vue` (registrado globalmente como `emf-alert`, `<slot/>` em `alert alert-info`).

## API do `SyncStore` (para componentes Vue)

| Ação | Assinatura | Descrição |
|------|------------|-----------|
| `initialize()` | `()` | Cria `WebSocketManager` uma única vez e liga os eventos |
| `registerModels` | `(app, models[])` | Marca modelos como sincronizáveis (`models[app][model] = Date.now()`) |
| `fetchSync` | `({app, model, id?, action?, params?, only_first_page=false, force_fetch=true})` | Busca em `/api/<app>/<model>/[id/][action/]?query` e preenche o cache; retorna `data_cache['<app>_<model>']` |
| `syncModels` | `([{app, models[], params?}], global_params={}, force_fetch=true)` | `fetchSync` para cada modelo e depois `cleanInvalidatedDataCache` |
| `invalidateDataCache` | `(apps[], models[])` | Marca todos os itens (modelos registrados) com `timestamp_frontend = -1` |
| `cleanInvalidatedDataCache` | `(app, model)` | Apaga itens com `timestamp_frontend === -1` |
| `invalidateCacheItems` | `(app, model, ids[])` | Apaga itens específicos |
| `sendSyncMessage` | `(message)` | Envia via WS se `wsConnected`; senão `console.warn` |
| `handleSyncMessage` | `({app, model, id, action, instance, timestamp})` | Processa mensagem do servidor (só modelos registrados) |
| `UPDATE_DATA_CACHE` / `DELETE_DATA_CACHE` / `UPDATE_DATA_CACHE_CRONOMETRO` | `({key, value})` | Mutações do cache |
| `startLocalCronometro` / `stopLocalCronometro` | `(id)` | Timer de 500 ms via `TimerWorkerService` (callback vazio) |

Evento `EventBus`: `sync-refresh` → `{app, model, id}` (emitido em todo `post_save` de modelo registrado, antes de atualizar/buscar).

## Variáveis de ambiente e configurações

| Variável | Padrão | Efeito |
|----------|--------|--------|
| `REDIS_HOST` | `startdev1-redis` | Host do Redis (broker Celery, Channel Layer, cache). Os scripts `_docker/*/start*.sh` gravam `REDIS_HOST = <COMPOSE_PROJECT_NAME>-redis` em `backend/.env` |
| `REDIS_PORT` | `6379` | Porta do Redis |
| `DEBUG` | `False` | Em `DEBUG`, se `FOLDER_DEBUG_CONTAINER != PROJECT_DIR`, `REDIS_HOST = "localhost"` |
| `FOLDER_DEBUG_CONTAINER` | caminho de `zenv.py` | Igualado a `${HOME}` nos scripts Docker (⇒ usa `REDIS_HOST` do `.env`) |

Chaves de `settings` (`backend/settings/zasyncs.py`, importadas por `project.py`): `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND = "django-db"`, `CELERY_CACHE_BACKEND = "django-cache"`, `CELERY_BEAT_SCHEDULER`, `CHANNEL_LAYERS`, `CACHES`. `INSTALLED_APPS` precisa de `daphne` (primeiro), `channels`, `django_celery_beat`, `django_celery_results` (`backend/settings/apps.py`); `ASGI_APPLICATION = "backend.asgi.application"`.

Portas: Redis `6379` (serviço Docker, ver 010/011). Daphne/Nginx e `proxy_pass` do `/ws/`: ver `011-docker-producao`.
