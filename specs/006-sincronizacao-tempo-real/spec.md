# Especificação da Funcionalidade: Sincronização em Tempo Real (WebSocket + Celery)

**Branch da Funcionalidade**: `006-sincronizacao-tempo-real`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: consumidor WebSocket `SyncRefreshConsumer` (`ws/sync/`), sinais `post_save`/`post_delete` que publicam mudanças de modelos no grupo `group_sync_refresh_channel`, tarefa Celery `debug_task`, configuração de Redis/Celery/Channels (`backend/settings/zasyncs.py`), páginas/rotas de demonstração (`/wstest/`, `/testws/`) e o lado cliente (`WebSocketManager`, `SyncStore`, `EventBus`, `TimerWorkerService`, `MessageStore` e componentes de mensagem)."

**Pré-requisitos**: `001-fundacao-projeto-django` (projeto, apps, modelo `Teste`, migração inicial), `003-regras-permissoes-globais` (tabela `rules_patterns_public` e permissões `list_`/`view_`), `004-crud-generico-menus` (`TesteCrud`), `005-api-rest-automatica` (endpoint `/api/<app>/<modelo>/`, serializer usado nas mensagens). A configuração do Vite fica em `007-frontend-vite-vue`; o roteamento de produção (Daphne/Nginx) fica em `011-docker-producao`.

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Receber mudanças de dados sem recarregar a página (Prioridade: P1)

Um usuário (anônimo ou autenticado) mantém a aplicação aberta no navegador. Quando um registro de um modelo sincronizável é criado, alterado ou excluído por qualquer meio (admin, API, CRUD, tarefa Celery), o navegador é avisado imediatamente, e o estado local (cache) é atualizado sem recarregar a página.

**Por que esta prioridade**: É o propósito central da funcionalidade (princípio VI da constituição): propagar mudanças de modelos aos navegadores em tempo real.

**Teste Independente**: Abrir duas abas em `/wstest/`, criar um `Teste` (via `/teste/`, admin ou `/testws/`) e observar em ambas uma mensagem "Sync Refresh!" com o `id` do registro, sem recarregar nenhuma aba.

**Cenários de Aceitação**:

1. **Dado** um navegador conectado em `/ws/sync/` e o modelo `utils.teste` registrado no cliente, **Quando** um `Teste` é salvo, **Então** o servidor publica uma mensagem `sync_refresh.message` com `action = "post_save"`, `id`, `app = "utils"`, `model = "teste"`, `created`, `timestamp` (ms) e `instance`, e o cliente emite o evento `sync-refresh` no `EventBus`.
2. **Dado** o mesmo cenário, **Quando** um `Teste` é excluído, **Então** a mensagem tem `action = "post_delete"` e o cliente remove o registro do cache local.
3. **Dado** um modelo cujo app **não** casa com a lista de apps permitidos (hoje apenas `^utils`) ou cujo modelo é `auditlog`/`metadata`, **Quando** uma instância é salva/excluída, **Então** nenhuma mensagem é publicada.
4. **Dado** um modelo sincronizável que define `ws_sync()` retornando falso, **Quando** a instância é salva, **Então** nenhuma mensagem é publicada.
5. **Dado** uma mensagem para um modelo **não registrado** no cliente, **Quando** ela chega, **Então** o cliente a ignora.

---

### História de Usuário 2 - Respeitar as permissões de visualização de cada usuário (Prioridade: P1)

O conteúdo da instância (`instance`) enviado no WebSocket só deve chegar a quem teria permissão de vê-la; os demais ainda são avisados da mudança (para poderem consultar a API, que impõe suas próprias permissões), mas sem o conteúdo.

**Por que esta prioridade**: Evita vazamento de dados pelo canal de tempo real, que é um canal único compartilhado por todos os clientes.

**Teste Independente**: Conectar um cliente anônimo, um usuário sem permissões e um superusuário e salvar um `Teste` (público para `list_`/`view_`); depois repetir com um modelo sem permissão pública.

**Cenários de Aceitação**:

1. **Dado** um cliente anônimo e um modelo com permissões públicas `<app>.detail_<modelo>` ou `<app>.view_<modelo>` (tabela `rules_patterns_public`), **Quando** a mensagem é entregue, **Então** `instance` é mantida.
2. **Dado** um cliente anônimo e um modelo sem permissões públicas, **Quando** a mensagem é entregue, **Então** `instance` é removida, mas `action`, `id`, `app`, `model`, `created` e `timestamp` permanecem.
3. **Dado** um usuário autenticado não superusuário, **Quando** a mensagem é entregue, **Então** `instance` é mantida somente se `has_perm('<app>.detail_<modelo>')` ou `has_perm('<app>.view_<modelo>')` for verdadeiro.
4. **Dado** um superusuário, **Quando** a mensagem é entregue, **Então** `instance` é sempre mantida.
5. **Dado** que a remoção de `instance` vale apenas para o destinatário em questão, **Quando** dois clientes com permissões diferentes recebem a mesma mudança, **Então** cada um recebe a versão correspondente à sua permissão (a remoção em um não afeta o outro).

---

### História de Usuário 3 - Manter o cache do cliente coerente (SyncStore) (Prioridade: P2)

O frontend mantém um cache normalizado por `app_model` → `id`, alimentado tanto pela API (busca paginada) quanto pelas mensagens do WebSocket, sem que dados antigos sobrescrevam dados mais novos.

**Por que esta prioridade**: Torna a sincronização útil para os componentes Vue, mas depende do canal (US1) funcionar.

**Teste Independente**: No console do navegador, usar `useSyncStore()` para chamar `fetchSync`/`syncModels` e verificar `data_cache['utils_teste']`; em seguida salvar um `Teste` e ver o cache ser atualizado.

**Cenários de Aceitação**:

1. **Dado** o modelo `utils.teste` registrado (feito por `App.vue`), **Quando** `fetchSync({app, model})` é chamado sem `id`, **Então** todas as páginas da listagem `/api/utils/teste/?page=N&o=id` são buscadas sequencialmente e gravadas em `data_cache['utils_teste']` com `__label__ = 'utils_teste'` e `timestamp_frontend`.
2. **Dado** um registro já no cache com `timestamp_frontend` maior ou igual ao de um valor recebido, **Quando** o valor mais antigo chega, **Então** ele é descartado.
3. **Dado** uma mensagem `post_save` sem `instance` (conteúdo negado/ausente), **Quando** o registro não está no cache ou está com `timestamp_frontend` menor que o `timestamp` da mensagem, **Então** o cliente busca o registro na API (`fetchSync` com `id`).
4. **Dado** `invalidateDataCache(['utils'], ['teste'])`, **Quando** `syncModels` refaz a busca e termina, **Então** os itens não reatualizados (`timestamp_frontend === -1`) são removidos por `cleanInvalidatedDataCache`.
5. **Dado** `fetchSync` com `force_fetch = false`, **Quando** já existe cache para a chave (ou item), **Então** o cache é devolvido sem requisição.
6. **Dado** `fetchSync` para um modelo ainda não registrado, **Então** ele é registrado automaticamente antes da busca.

---

### História de Usuário 4 - Conexão resiliente e medição de latência (Prioridade: P2)

A conexão WebSocket se mantém viva (ping periódico), reconecta sozinha após quedas com espera crescente e informa o desvio de relógio entre cliente e servidor.

**Por que esta prioridade**: Sem reconexão a sincronização para de funcionar após qualquer queda de rede ou reinício do servidor.

**Teste Independente**: Abrir `/wstest/`, derrubar o servidor ASGI e religá-lo; observar no console as tentativas de reconexão e o retorno da conexão (`wsConnected` volta a `true`).

**Cenários de Aceitação**:

1. **Dado** a conexão aberta, **Quando** o cliente envia `{"type":"ping","ping_now":<performance.now()>}`, **Então** o servidor responde `{"type":"pong","message":{"timestamp_server":<ms>,"ping_now":<eco>}}` ao próprio remetente, sem retransmitir ao grupo, e o `SyncStore` guarda em `lastServerSync` o objeto com `server_time_diff`.
2. **Dado** a conexão aberta, **Quando** passam 60 s, **Então** o cliente envia novo ping automaticamente.
3. **Dado** a conexão fechada, **Quando** o evento de fechamento ocorre, **Então** o cliente tenta reconectar até 10 vezes com espera de `1000 ms × 2^tentativa`, e zera o contador ao reconectar com sucesso.

---

### História de Usuário 5 - Demonstração do fluxo ponta a ponta com Celery (Prioridade: P3)

Uma página de demonstração (`/wstest/`) com um botão que chama `/testws/`; o servidor agenda uma tarefa Celery que cria um `Teste` 2 segundos depois, e a página mostra, via WebSocket, o aviso da criação.

**Por que esta prioridade**: Serve de verificação e exemplo de uso; não é necessária ao funcionamento dos demais recursos.

**Teste Independente**: Com Redis, worker Celery e servidor ASGI no ar, abrir `/wstest/` e clicar no botão; aparecem uma mensagem de sucesso imediata e, ~2 s depois, uma mensagem informativa de `sync-refresh`.

**Cenários de Aceitação**:

1. **Dado** `/testws/` acessado por GET, **Quando** a requisição é atendida, **Então** a resposta JSON traz `message = "ultimo cadastrado. task chamada para criar novo"` e `teste` (último `Teste` por `id`, ou um `Teste` vazio se não houver) e a tarefa `debug_task` é agendada com `countdown=2`.
2. **Dado** a tarefa executada pelo worker na fila `celery`, **Quando** ela roda, **Então** cria um `Teste` com `teste = str(random())` (o que dispara a US1) e retorna `"result of teste <id>"`.
3. **Dado** `/wstest/` (com ou sem `slug` sem pontos), **Quando** acessada, **Então** o template `wstest_index.html` é renderizado com a rota Vue `index_link` (`WsTest.vue`).
4. **Dado** uma mensagem inserida no `MessageStore` com `timeout`, **Quando** o tempo expira, **Então** a mensagem some da lista exibida (`DisplayMessage`, canto inferior direito).

---

### Casos de Borda

- **Qualquer cliente pode disparar mensagens a todos**: para qualquer mensagem que não seja `ping` (e para `command` com `command` informado), o consumidor retransmite o JSON recebido a todos os conectados (tipo externo `sync_refresh_message`, com underscore). O `SyncStore` só trata o tipo `sync_refresh.message` (com ponto), portanto não aplica tais mensagens ao cache, mas outros listeners do `WebSocketManager` as recebem.
- **`command` sem valor**: a mensagem `{"type":"command"}` retorna `command_result` com `error: "Comando não especificado"` e **não** é retransmitida; com `command` preenchido nada é executado (não há comandos implementados) e a mensagem é retransmitida.
- **JSON inválido** no `receive`: `json.loads` fica fora do `try`, a exceção sobe e a conexão é encerrada pelo Channels.
- **Erro dentro do `try` do `receive`** (ex.: JSON que não é objeto): o cliente recebe `command_result` com `error`, mas o fluxo continua e ainda tenta retransmitir.
- **Remoção de `instance`**: a remoção é feita no dicionário `event["message"]` (mesmo objeto que é serializado em seguida), portanto vale de fato; cada destinatário recebe sua própria cópia (serialização do Redis/`deepcopy` do layer em memória).
- **Permissões congeladas na conexão**: o usuário é resolvido uma vez no `connect`; mudanças de permissão só valem após reconexão. A permissão `detail_<modelo>` não existe no projeto (apenas `list_`, `view_`, `add_`, `change_`, `delete_`), então na prática vale `view_`.
- **Sem Redis**: o salvamento do modelo não falha (erro capturado e logado), mas a publicação aguarda até 5 s de timeout de conexão; o `connect` do consumidor captura a exceção, loga e **não** aceita a conexão.
- **Exclusão sem cache**: `post_delete` para um modelo registrado cujo cache ainda não foi criado gera `TypeError` no cliente (`data_cache[key]` indefinido).
- **Mensagem sem `instance`** (negada ou falha de serialização): o cliente precisa buscar na API, que aplica as permissões da API; se o usuário não tiver acesso, a promessa é rejeitada sem tratamento.
- **Modelo sem viewset da API ou sem `id`**: a publicação envia `instance = null` (erro de serialização é logado) ou é abandonada (erro capturado).
- **`/testws/` é público e altera dados via GET**: qualquer pessoa agenda criação de registros.
- **`/wstest/<slug>`**: o Django aceita qualquer `slug` sem ponto, mas o roteador Vue só conhece `/wstest/`; outros `slug`s caem no 404 do Vue.
- **Limite de reconexão**: após 10 falhas consecutivas o cliente desiste até que a página seja recarregada.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE expor um endpoint WebSocket em `ws/sync/` atendido por `SyncRefreshConsumer`, com autenticação por sessão do Django (`AuthMiddlewareStack`), aceitando conexões de anônimos e de autenticados.
- **FR-002**: Ao conectar, o consumidor DEVE entrar no grupo `group_sync_refresh_channel` (`room_name = "sync_refresh_channel"`, prefixo `group_`) e aceitar a conexão; ao desconectar DEVE sair do grupo.
- **FR-003**: O consumidor DEVE responder a `{"type":"ping","ping_now":X}` com `{"type":"pong","message":{"timestamp_server":<time.time()*1000>,"ping_now":X}}` apenas ao remetente.
- **FR-004**: Para mensagens recebidas que não sejam `ping` (e que não sejam `command` sem `command`), o consumidor DEVE retransmitir o JSON recebido ao grupo como `{"type":"sync_refresh_message","message":<json>}`; `command` sem valor DEVE responder `command_result` com `error = "Comando não especificado"` sem retransmitir. (Comportamento replicado do código atual; ver `research.md` sobre o risco.)
- **FR-005**: O sistema DEVE publicar no grupo, a cada `post_save` e `post_delete` de modelo cujo `_meta.label` case com `^utils` (lista `regex_applabels_permitidos`) e cujo `model_name` não seja `auditlog` nem `metadata`, uma mensagem `{"type":"sync_refresh.message","message":{action,id,app,model,created,timestamp,instance}}`.
- **FR-006**: O sistema DEVE respeitar os ganchos opcionais do modelo: `ws_sync()` (falso ⇒ não publicar) e `ws_serialize()` (retorno verdadeiro ⇒ usado como `instance`; senão usa-se o `serializer_class` do viewset gerado por `ApiViewSetConstrutor.get_viewset_for_model`).
- **FR-007**: Falhas de serialização DEVEM ser logadas e a mensagem publicada com `instance = null`; qualquer outra falha na publicação DEVE ser logada e NÃO DEVE impedir o salvamento/exclusão do registro.
- **FR-008**: Na entrega a cada cliente (`sync_refresh_message`), o sistema DEVE remover `instance` quando o destinatário não tiver permissão: anônimo ⇒ somente se `rules_patterns_public["<app>:<modelo>"]` contiver `<app>.detail_<modelo>` ou `<app>.view_<modelo>`; autenticado não superusuário ⇒ `has_perm` de `detail_` ou `view_`; superusuário ⇒ sempre permitido.
- **FR-009**: Em erro ao entregar, o consumidor DEVE enviar `{"type":"error","error":"<texto>"}` ao cliente.
- **FR-010**: O registro dos sinais DEVE ocorrer em `UtilsConfig.ready()` (importando `signals` e `signals_syncrefresh`), com `dispatch_uid="signal_post_syncrefresh"`.
- **FR-011**: O sistema DEVE usar Redis como broker do Celery (`redis://REDIS_HOST:REDIS_PORT`), como Channel Layer (`channels_redis.core.RedisChannelLayer`, `socket_timeout = None`, `socket_connect_timeout = 5`) e como cache (`django.core.cache.backends.redis.RedisCache`); resultados do Celery em `django-db`, cache do Celery em `django-cache` e agendador `django_celery_beat.schedulers.DatabaseScheduler`.
- **FR-012**: `REDIS_HOST` (padrão `startdev1-redis`) e `REDIS_PORT` (padrão `6379`) DEVEM vir de variáveis de ambiente; em `DEBUG` fora do contêiner (`FOLDER_DEBUG_CONTAINER != PROJECT_DIR`) o host DEVE ser `localhost`.
- **FR-013**: O sistema DEVE disponibilizar a tarefa Celery `debug_task` (fila `celery`, `bind=True`) que cria um `Teste` com número aleatório e retorna `"result of teste <id>"`.
- **FR-014**: O sistema DEVE disponibilizar `GET /testws/` (nome `testws`) que agenda `debug_task` com `countdown=2` e devolve JSON com `message` e o último `Teste` (`model_to_dict`), e `GET /wstest/<slug>` (nome `wstest_index`, `slug` = `[^.]*`) que renderiza `wstest_index.html`.
- **FR-015**: O cliente DEVE conectar em `ws(s)://<host>/ws/sync/` (conforme o protocolo da página), enviar ping a cada 60 s e ao abrir, reconectar com backoff exponencial `1000 ms × 2^tentativa` até 10 tentativas e emitir os eventos `connected`, `disconnected`, `error` e `message`.
- **FR-016**: O cliente DEVE converter o `pong` em objeto com `pong`, `ping`, `timestamp_server` e `server_time_diff = (Date.now() − timestamp_server) − (pong_now − ping_now)/2`.
- **FR-017**: `useSyncStore().initialize()` DEVE ser chamado uma única vez em `App.vue`, que também DEVE registrar `registerModels('utils', ['teste'])`.
- **FR-018**: O `SyncStore` DEVE processar apenas mensagens `sync_refresh.message` de modelos registrados; em `post_save` DEVE emitir `sync-refresh` `{app, model, id}` no `EventBus` e atualizar o cache (com `instance`) ou buscar via API (sem `instance`); em `post_delete` DEVE remover do cache.
- **FR-019**: O cache DEVE ser indexado por `<app>_<modelo>` → `id`, cada item com `__label__` e `timestamp_frontend`, e DEVE descartar atualizações com `timestamp_frontend` menor ou igual ao do item em cache.
- **FR-020**: `fetchSync` DEVE paginar automaticamente (seguindo `pagination.next_page`) a menos que `only_first_page` seja verdadeiro, usar `page = 1` e `o = 'id'` como padrão quando não houver `id`, e juntar parâmetros do tipo lista com vírgula.
- **FR-021**: O `SyncStore` DEVE oferecer `invalidateDataCache`, `cleanInvalidatedDataCache`, `invalidateCacheItems`, `registerModels`, `syncModels`, `sendSyncMessage` (só envia se conectado) e as ações de cronômetro local (`startLocalCronometro`/`stopLocalCronometro` via `TimerWorkerService`).
- **FR-022**: O frontend DEVE oferecer um `EventBus` singleton (`on`, `off`, `emit`), fornecido por `app.provide('EventBus', ...)`, e um `MessageStore` (Pinia) com `messages`, `addMessage`, `shiftMessage`, `removeMessage` exibido por `DisplayMessage`/`AlertMessage`, removendo automaticamente mensagens com `timeout`.
- **FR-023**: O sistema NÃO DEVE sincronizar modelos de outros apps além de `utils` enquanto a lista `regex_applabels_permitidos` não for ampliada; `Teste` é o único modelo sincronizado hoje.

### Entidades-Chave

- **Teste**: modelo de demonstração (campo `teste`, texto até 100 caracteres) em `utils`; único modelo sincronizado (ver `001-fundacao-projeto-django`).
- **Mensagem de sincronização**: evento do servidor com `action`, `id`, `app`, `model`, `created`, `timestamp` e `instance` (opcional conforme permissão).
- **Grupo de canal `group_sync_refresh_channel`**: canal único ao qual todos os clientes WebSocket pertencem.
- **Cache de sincronização (cliente)**: dicionário `data_cache[app_model][id]` com `__label__` e `timestamp_frontend`.
- **Mensagem de interface (cliente)**: `{id, type, title?, text, timeout?}` exibida no canto da tela.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Após salvar um `Teste`, 100% dos clientes conectados e registrados recebem a mudança em menos de 1 segundo em condições normais de rede local.
- **SC-002**: Nenhuma mensagem entregue a um cliente sem permissão de visualização contém o campo `instance` (verificável por teste com anônimo, sem permissão e superusuário).
- **SC-003**: Após queda e retorno do servidor em até ~34 minutos acumulados de espera (soma das esperas 2 s…1024 s = 2046 s), o cliente reconecta sem recarregar a página.
- **SC-004**: O fluxo `/testws/` → Celery → `Teste` criado → aviso no navegador conclui em cerca de 2 segundos mais o tempo de execução da tarefa.
- **SC-005**: Um erro de Redis ou de serialização nunca impede salvar ou excluir um `Teste` (a operação de banco sempre conclui).
- **SC-006**: Atualizações antigas nunca sobrescrevem itens mais novos no cache do cliente (verificável por `timestamp_frontend`).

## Premissas

- Redis, worker Celery e servidor ASGI (Daphne via `runserver` em desenvolvimento) estão disponíveis (ver `010-docker-desenvolvimento` e `011-docker-producao`).
- A configuração do Vite (alias `~@`, injeção global de `_` = lodash usada pelo `SyncStore`) pertence a `007-frontend-vite-vue`; aqui apenas se assume que existe.
- O endpoint `/api/<app>/<modelo>/` (feature 005) retorna listas paginadas com `results` e `pagination.next_page` e aceita os parâmetros `page` e `o`.
- A autenticação por sessão e o `AuthStore` (`loginStatus()` em `App.vue`) pertencem a `002-autenticacao-usuarios-auditoria`.
- O projeto roda hoje sem testes automatizados para consumidor, sinais ou `SyncStore`; o roteiro de testes sugerido está em `quickstart.md`.
- Os comportamentos "estranhos" descritos em Casos de Borda são o estado atual e são replicados para fidelidade; recomendações de correção estão em `research.md`.
