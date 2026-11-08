# Pesquisa e Decisões Técnicas: Sincronização em Tempo Real

**Branch**: `006-sincronizacao-tempo-real` | **Data**: 2026-11-08

## Decisões

### D1 — Um único grupo de canal para todos os clientes

- **Decisão**: todos os consumidores entram em `group_sync_refresh_channel`; a filtragem (permissões e modelos registrados) é feita no momento da entrega (servidor, por destinatário) e no cliente (modelos registrados).
- **Justificativa**: simplicidade; o servidor publica uma vez por mudança, independentemente do número de clientes; o filtro por destinatário permite que a mesma mensagem seja entregue com ou sem `instance`.
- **Alternativas**: grupos por modelo/usuário (mais eficiente, exige gestão de assinaturas); um grupo por permissão (exige recalcular ao mudar permissões).

### D2 — Publicar via sinais Django (`post_save`/`post_delete`), não nas views

- **Decisão**: um único receptor (`signal_post_syncrefresh`, `dispatch_uid="signal_post_syncrefresh"`) cobre admin, API, CRUD, shell e tarefas Celery.
- **Justificativa**: qualquer origem de escrita é propagada (princípio VI). `async_to_sync(channel_layer.group_send)` permite chamar do código síncrono.
- **Alternativas**: publicar nas views/serializers (perde escritas fora da API); `transaction.on_commit` (evitaria a corrida descrita adiante, mas não é usado).

### D3 — Lista branca de apps por expressão regular

- **Decisão**: `regex_applabels_permitidos = [re.compile(r"^utils")]`, comparada com `inst._meta.label` (`app_label.NomeDoModelo`); exclusão explícita de `auditlog` e `metadata` por `model_name`.
- **Justificativa**: impede que todo modelo do projeto (inclusive logs de auditoria e metadados, de alto volume) gere tráfego; o esqueleto sincroniza só `utils.Teste`. Para sincronizar outros apps, adiciona-se o padrão à lista.
- **Alternativas**: registro por decorador/atributo no modelo; usar `ws_sync()` em cada modelo (existe como gancho adicional).

### D4 — Serialização pelo serializer da API

- **Decisão**: `ApiViewSetConstrutor.get_viewset_for_model(model).serializer_class(inst).data`, com gancho `ws_serialize()` para sobrescrever.
- **Justificativa**: o cliente recebe exatamente o mesmo formato da API REST, e o cache do `SyncStore` mistura dados da API e do WebSocket sem conversão.
- **Alternativas**: `model_to_dict`; serializer dedicado.

### D5 — Redis único para broker, Channel Layer e cache

- **Decisão**: `REDIS_HOST/REDIS_PORT` alimentam `CELERY_BROKER_URL`, `CHANNEL_LAYERS` e `CACHES`; resultados do Celery em `django-db`.
- **Justificativa**: um só serviço de apoio por ambiente (princípios II e III); resultados em banco permitem auditar tarefas no admin.
- **Alternativas** (comentadas em `zasyncs.py`): cache em arquivo (`FileBasedCache`), `LocMemCache`/`DummyCache` conforme `DEBUG`.

### D6 — Protocolo mínimo de ping/pong com `timestamp_server`

- **Decisão**: o servidor responde ping com `timestamp_server` (ms) e eco de `ping_now`; o cliente calcula `server_time_diff` assumindo latência simétrica.
- **Justificativa**: heartbeat de 60 s mantém a conexão ativa através de proxies e fornece desvio de relógio.
- **Alternativas**: ping/pong nativo do WebSocket (já feito pelo Daphne), NTP no cliente.

### D7 — Cache normalizado no cliente com `timestamp_frontend`

- **Decisão**: `data_cache[app_model][id]`; `timestamp_frontend` impede sobrescrever dado novo por antigo (comentário no código: "evita sobrescrever dados mais recentes no cache que podem ter sido atualizados via WebSocket"); `-1` marca invalidação e `cleanInvalidatedDataCache` remove sobras.
- **Justificativa**: busca paginada concorrente com mensagens WS não pode regredir o estado.
- **Alternativas**: versionamento por `updated_at` do servidor; refetch completo a cada mensagem.

### D8 — Timer em Web Worker

- **Decisão**: `TimerWorkerService` cria um Worker via `Blob` para ticks que não sofrem estrangulamento de abas em segundo plano.
- **Justificativa**: `setInterval` na thread principal é limitado (≥1 s) em abas inativas; cronômetros precisam de precisão.
- **Alternativas**: `setInterval` simples; `requestAnimationFrame`.

### D9 — Tarefa de demonstração `debug_task` e rotas `/testws/`, `/wstest/`

- **Decisão**: um fluxo mínimo (HTTP → Celery → banco → sinal → WebSocket → UI) que valida toda a cadeia.
- **Justificativa**: serve de teste de fumaça do ambiente e de exemplo de uso.

## Particularidades, dívidas técnicas e riscos observados

Recomendação geral: **o estado atual é replicar para fidelidade**; a coluna "Recomendação" indica o que uma versão endurecida deveria fazer.

| # | Observação (confirmada no código) | Risco | Recomendação |
|---|-----------------------------------|-------|--------------|
| 1 | `SyncRefreshConsumer.receive`: para qualquer mensagem que não seja `ping` (e `command` com `command`), o JSON do cliente é retransmitido ao grupo inteiro (`group_send` com tipo `sync_refresh_message`). Qualquer cliente, inclusive anônimo, pode enviar mensagens a todos os conectados (spam/amplificação). O tipo externo é `sync_refresh_message` (underscore), distinto de `sync_refresh.message` (ponto), então o `SyncStore` **não** aplica essas mensagens ao cache; porém outros listeners de `message` do `WebSocketManager` as veem | Segurança/abuso (DoS por amplificação, conteúdo arbitrário a terceiros) | **Corrigir**: remover a retransmissão (cliente só envia `ping`/comandos autorizados). Replicar na reconstrução fiel |
| 2 | Em `receive`, o bloco `command` valida apenas a presença de `command`; nenhum comando é executado (variáveis `app`, `model`, `params`, `user` não usadas). O handler `command_result` nunca é acionado por nenhum emissor | Código morto / API enganosa | Replicar; documentar como reservado, ou implementar comandos com permissão |
| 3 | `json.loads(text_data)` está fora do `try`: JSON inválido derruba a conexão com exceção; já erro dentro do `try` envia `command_result` com `error` mas **continua** e retransmite | Robustez | **Corrigir**: mover o parse para o `try` e `return` após erro |
| 4 | Em `sync_refresh_message`, a permissão é aplicada com `del message["instance"]` e depois `send(json.dumps(event))`. Confirmado: `message` **é** `event["message"]`, então a remoção vale. Cada consumidor recebe sua cópia (Redis serializa por destinatário; `InMemoryChannelLayer` usa `deepcopy`), portanto remover para um não afeta outros | Nenhum (era uma dúvida) | Replicar. Sugestão de clareza: construir um novo dicionário sem `instance` |
| 5 | Permissão `detail_<modelo>` não existe (só `list_`, `view_`, `add_`, `change_`, `delete_`), logo a checagem de `detail_` é sempre falsa e vale `view_`; para autenticados são duas chamadas `has_perm` | Código redundante | Replicar |
| 6 | O usuário do `scope` e o cache de permissões do Django são avaliados na conexão; revogações de permissão só valem após reconectar. Conexões longas mantêm acesso a `instance` | Segurança (janela de acesso) | **Corrigir** (opcional): reavaliar por mensagem sem cache ou desconectar ao mudar permissões |
| 7 | `message["instance"]` é calculado no sinal **antes** do commit (sem `transaction.on_commit`): o cliente pode consultar a API e não ver o registro ainda (corrida), e uma transação revertida ainda publica | Consistência | **Corrigir**: `transaction.on_commit(lambda: ...)` |
| 8 | O sinal serializa e publica **de forma síncrona** no caminho do `save()`; Redis indisponível ⇒ cada save espera até `socket_connect_timeout = 5` s antes de logar o erro (o save não falha). `group_send` ocorre mesmo em `loaddata`/importações em massa | Desempenho/latência | Replicar; considerar enfileirar a publicação (Celery) |
| 9 | `regex_applabels_permitidos = [r"^utils"]` usa `re.match` em `_meta.label` (`utils.Teste`): também casaria apps cujo rótulo comece com `utils` (ex.: `utilsfoo`). Exclusão `auditlog`/`metadata` por `model_name` é redundante para `auditlog` (outro app) e necessária para `utils.Metadata` | Falso positivo futuro | Replicar; usar `^utils\.` ao ampliar |
| 10 | `action = "post_save" if "created" in kwargs else "post_delete"`: depende de `post_delete` nunca enviar `created`; `inst.id` é usado (modelos sem `id` caem no `except` genérico e nada é publicado) | Acoplamento | Replicar |
| 11 | `/testws/` é público, executa efeito colateral em GET (cria registros via Celery) e não tem limitação de taxa; `/wstest/<slug>` aceita qualquer `slug` mas o Vue só roteia `/wstest/` | Abuso / demonstração em produção | **Corrigir**: restringir/remover em produção (ex.: só `DEBUG`/superusuário). Replicar na reconstrução fiel |
| 12 | `debug_task` não está em `backend/utils/tasks.py`, então `autodiscover_tasks(related_name='tasks')` não a encontra; ela é registrada no worker de forma incidental, porque o `DjangoWorkerFixup` do Celery executa as verificações de sistema, que importam o URLconf → `backend.utils.views` → `backend.utils.services.tasks` (verificado: após `django.setup()` sozinho a tarefa não está registrada; após `app.loader.import_default_modules()` está) | Fragilidade (task "não registrada") se o import mudar | Replicar o layout (`services/tasks.py`); para robustez, importar o módulo em `UtilsConfig.ready()` ou usar `autodiscover_tasks(..., related_name="services.tasks")` |
| 13 | `SyncStore.handleSyncMessage` em `post_delete` faz `delete this.data_cache[key][id]` sem verificar `data_cache[key]` ⇒ `TypeError` se o modelo ainda não foi carregado; não emite evento `sync-refresh` em deleções (só em `post_save`) | Erro no cliente | **Corrigir**: guardar `if (this.data_cache[key])`; emitir evento para delete |
| 14 | `timestamp_frontend` mistura relógios: `fetchSync` usa `Date.now()` do cliente e o WS usa o `timestamp` do servidor; `server_time_diff` é calculado mas não usado para compensar | Atualizações podem ser descartadas/aceitas indevidamente com relógios dessincronizados | **Corrigir**: compensar com `lastServerSync.server_time_diff` |
| 15 | Normalização de objetos aninhados em `UPDATE_DATA_CACHE` só ocorre para valores que já trazem `__label__`; o serializer da API não emite `__label__` (grep nulo no backend), logo o ramo está dormente. Além disso, `__label__.split('_')` assume `app_model` sem underscores adicionais, e `registerModels` é chamado em duplicidade | Código dormente | Replicar |
| 16 | `fetchSync` muta o objeto `params` recebido (arrays viram string), a recursão de páginas perde o `force_fetch` explícito (usa padrão `true`) e `only_first_page`; promessas rejeitadas (`403/404`) não são tratadas em `handleSyncMessage` | Efeitos colaterais/erros silenciosos | Replicar; tratar rejeição ao endurecer |
| 17 | Na recursão, o `timestamp_frontend` de cada página é diferente (nova chamada = novo `Date.now()`); o `inject('EventBus')` no `state()` só funciona se a store for criada dentro de um componente/contexto de app (`App.vue` o faz) | Fragilidade | Replicar; garantir que `useSyncStore()` seja chamado em `setup` |
| 18 | `WsTest.vue` registra `bus.on('sync-refresh', ...)` em `onMounted` sem `off` ao desmontar ⇒ vazamento/duplicação de tratadores; `AlertMessage` remove da store por timeout, mas o botão de fechar (`data-bs-dismiss`) só oculta o elemento (a mensagem permanece na store) | Vazamento menor | **Corrigir**: `onUnmounted(() => bus.off(...))`; fechar via `removeMessage` |
| 19 | `MessageStore.js` usa aspas duplas e ponto e vírgula, fora do padrão ESLint/Prettier do projeto (aspas simples, sem `;`); `AlertMessage` usa `defineProps` importado de `vue` (desnecessário em `<script setup>`) | Estilo | Replicar (ou normalizar com `npm run lint`) |
| 20 | `TimerWorkerService`: `queue` nunca é usada de fato (o worker é criado no construtor) e a URL do Blob não é revogada; `startLocalCronometro` passa callback vazio; `UPDATE_DATA_CACHE_CRONOMETRO` não é usada | Código morto | Replicar |
| 21 | `CORS`/`ALLOWED_HOSTS` abertos e **sem validação de origem** no WebSocket (`AuthMiddlewareStack` sem `AllowedHostsOriginValidator`): site de terceiro pode abrir a conexão usando o cookie de sessão do usuário (CSWSH) e receber `instance` conforme as permissões dele | Segurança | **Corrigir**: envolver com `AllowedHostsOriginValidator` ao restringir `ALLOWED_HOSTS` |
| 22 | O `connect` captura exceções e não fecha explicitamente; sem Redis, o handshake não é aceito (conexão recusada) e o cliente entra no ciclo de reconexão | Comportamento aceitável | Replicar |
| 23 | `WebSocketManager`: `emit('connected')` e demais ocorrem; `send` com socket fechado reagenda uma tentativa única baseada no atraso; `onclose` sempre dispara `handleReconnect` (inclusive em fechamento intencional); sem `close()` público | Limitações | Replicar |
