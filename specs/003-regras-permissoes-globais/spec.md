# Especificação da Funcionalidade: Regras e Permissões Globais

**Branch da Funcionalidade**: `003-regras-permissoes-globais`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: app `backend/globalrules/` (constantes de permissão, tabela de regras por grupo, sinais `post_migrate` que criam a permissão `list_<modelo>`, sincronizam grupos e reajustam sequências de ids), `backend/api/permissions.py` (classes de permissão do DRF), uso das permissões públicas pela API e pelo consumer WebSocket, verificações de permissão em templates e menus YAML e o contrato de permissões consumido pelo CRUD genérico."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Permissão `list_<modelo>` e grupos sincronizados a cada `migrate` (Prioridade: P1)

Quem mantém o sistema declara, em um único arquivo de regras (`backend/globalrules/map_rules.py`), quais grupos existem e quais permissões cada grupo tem sobre cada modelo. Ao rodar `migrate`, o sistema cria a permissão adicional `list_<modelo>` (além de `add`/`change`/`delete`/`view`) para todo modelo de todo app, cria os grupos declarados e atribui a eles exatamente as permissões declaradas.

**Por que esta prioridade**: é a base de toda autorização do projeto (API, CRUD, menus, WebSocket). Sem ela nenhuma outra história funciona.

**Teste Independente**: rodar `python manage.py migrate` em um banco limpo e verificar, no shell/admin, que existe a permissão `eauth.list_user`, o grupo "Administrador do Sistema" e que este grupo possui as permissões `list/view/add/change/delete` de `User`, `Teste` e `Metadata` e a permissão `eauth.menu_1` (`menu_administracao`).

**Cenários de Aceitação**:

1. **Dado** um banco vazio, **Quando** `migrate` termina, **Então** existe a permissão `list_<modelo>` para cada modelo de cada app instalado (inclusive modelos de apps do Django, como `auth.group`) com o nome "Visualizaçao da lista de <verbose_name_plural>".
2. **Dado** o grupo "Administrador do Sistema" já criado, **Quando** um administrador adiciona manualmente uma permissão extra ao grupo e `migrate` roda novamente, **Então** o grupo volta a ter somente as permissões declaradas em `map_rules.py` (a permissão extra é removida).
3. **Dado** `GROUP_VISITANTE = ''`, **Quando** `migrate` roda, **Então** nenhum grupo é criado para o visitante (nome vazio é ignorado).
4. **Dado** que `migrate` roda mais de uma vez, **Quando** os sinais são reexecutados, **Então** não há duplicação de permissões, grupos nem erros.

---

### História de Usuário 2 - API REST respeita permissões por modelo e permissões públicas (Prioridade: P1)

Um cliente da API (anônimo ou autenticado) só acessa `/api/<app>/<modelo>/` se tiver as permissões correspondentes ao método HTTP; modelos podem declarar leitura pública (sem login) na tabela de regras.

**Por que esta prioridade**: é a fronteira de segurança dos dados expostos automaticamente (Constituição, princípio IV).

**Teste Independente**: com `Teste` declarado com permissões públicas `list`/`view`, fazer `GET /api/utils/teste/` sem autenticação (200) e `POST` sem autenticação (401/403); `GET /api/eauth/user/` sem autenticação (401/403) e com usuário do grupo administrador (200).

**Cenários de Aceitação**:

1. **Dado** um modelo com `list` e `view` públicas (`utils.teste`), **Quando** um anônimo faz `GET`, `HEAD` ou `OPTIONS`, **Então** a resposta é permitida sem credenciais.
2. **Dado** o mesmo modelo, **Quando** um anônimo faz `POST`, `PUT`, `PATCH` ou `DELETE`, **Então** o acesso é negado (as permissões `add`/`change`/`delete` não são públicas).
3. **Dado** um modelo sem permissões públicas (`eauth.user`, `utils.metadata`), **Quando** um usuário autenticado sem as permissões faz `GET`, **Então** recebe 403; **Quando** possui `list_<modelo>` **e** `view_<modelo>`, **Então** recebe 200.
4. **Dado** um superusuário, **Quando** acessa qualquer recurso, **Então** é permitido (`has_perms` retorna verdadeiro).

---

### História de Usuário 3 - Visibilidade de menus e áreas administrativas por permissão (Prioridade: P2)

Os templates e os menus declarativos (YAML) exibem ou ocultam itens conforme as permissões do usuário, incluindo a permissão de menu `menu_administracao` (código `menu_1`) declarada no modelo `User`.

**Por que esta prioridade**: afeta a experiência e a descoberta de funcionalidades, mas não a segurança dos dados (as views continuam protegidas).

**Teste Independente**: renderizar a página inicial como superusuário (menu de administração visível) e como usuário comum (menu de administração oculto).

**Cenários de Aceitação**:

1. **Dado** um superusuário autenticado, **Quando** a página base é renderizada, **Então** o bloco `perms.menu_administracao` mostra o menu de `menus/menu_administracao.yaml`.
2. **Dado** um item de menu YAML com `check_permission`, **Quando** o usuário não possui a permissão (`user.has_perm(<valor>)` falso), **Então** a `url` do item é anulada e o item não fica ativo (ou, em item sem `url`, os `children` são removidos).
3. **Dado** um usuário comum do grupo "Administrador do Sistema", **Quando** a página é renderizada, **Então** — particularidade do código atual — o menu de administração **não** aparece, pois a verificação usa um nome de permissão sem `app_label` (ver Casos de Borda).

---

### História de Usuário 4 - Contrato de permissões para CRUD e WebSocket (Prioridade: P2)

O CRUD genérico (feature 004) e o consumer de tempo real (feature 006) consomem os prefixos de permissão `RP_*` e a tabela de permissões públicas para decidir acesso a listagem, detalhe, criação, edição e exclusão, e quais mensagens de sincronização incluem a instância alterada.

**Por que esta prioridade**: sem este contrato as demais features não conseguem montar os nomes de permissão de forma consistente.

**Teste Independente**: importar `RP_LIST`, `RP_VIEW`, `RP_ADD`, `RP_CHANGE`, `RP_DELETE` e `rules_patterns_public` e verificar que `rules_patterns_public['utils:teste'] == {'utils.list_teste', 'utils.view_teste'}`.

**Cenários de Aceitação**:

1. **Dado** o prefixo `RP_LIST == '.list_'`, **Quando** o CRUD monta a permissão para o modelo `eauth.user`, **Então** obtém `eauth.list_user`.
2. **Dado** um anônimo conectado ao WebSocket e uma mensagem de mudança de `utils.teste`, **Quando** o consumer repassa a mensagem, **Então** a instância é mantida (modelo com `view` pública); para `eauth.user` a instância é removida da mensagem.
3. **Dado** um usuário autenticado não superusuário, **Quando** recebe mensagem de mudança, **Então** a instância só é mantida se ele tiver `<app>.detail_<modelo>` ou `<app>.view_<modelo>`.

---

### História de Usuário 5 - Sequências de ids consistentes após `migrate` (Prioridade: P3)

Após cada `migrate`, as sequências de chave primária (`id`) das tabelas gerenciadas no PostgreSQL são realinhadas ao maior `id` existente, evitando colisões de chave após cargas/restaurações de dados com ids explícitos.

**Por que esta prioridade**: é uma rede de segurança operacional; o sistema funciona sem ela em bancos novos.

**Teste Independente**: inserir um registro com `id` explícito maior que a sequência, rodar `migrate` e criar um novo registro sem falha de chave duplicada.

**Cenários de Aceitação**:

1. **Dado** uma tabela com `id` máximo 50 e sequência em 5, **Quando** `migrate` roda, **Então** a próxima inserção recebe `id = 51`.
2. **Dado** uma tabela sem sequência vinculada ao `id`, **Quando** `migrate` roda, **Então** a sequência `<tabela>_id_seq` é recriada e vinculada.
3. **Dado** qualquer erro durante o ajuste (tabela sem `id`, banco não PostgreSQL), **Quando** `migrate` roda, **Então** o erro é ignorado silenciosamente e o `migrate` continua.

---

### Casos de Borda

- `GROUP_VISITANTE = ''` (e qualquer grupo com nome falso) é ignorado por `_config_group`: não cria grupo nem atribui permissões; `rules_group_visitante` existe apenas como ponto de extensão com lista de regras vazia.
- `update_groups` executa `group.permissions.clear()` e reatribui tudo a cada `migrate`: alterações manuais nas permissões de grupos gerenciados são sempre perdidas.
- Se uma permissão declarada não existe (`Permission.DoesNotExist`) a exceção interrompe a associação das regras restantes **daquele grupo**, é registrada em log/`print` e o `migrate` continua; se o `ContentType` do modelo não existe, o modelo é ignorado silenciosamente.
- `create_proxy_permissions` usa o mesmo `dispatch_uid` (`django.contrib.auth.management.create_permissions`) do receptor nativo do Django; como é registrado antes, **substitui** a criação padrão de permissões do `django.contrib.auth` (o receptor nativo é descartado).
- A criação de `list_<modelo>` altera em memória `Meta.permissions` de cada modelo (acrescenta `list_<modelo>`), com ordem não determinística (usa `set`).
- `reset_id_model` usa `pg_get_serial_sequence` (somente PostgreSQL) e engole qualquer exceção (`except:` nu); em SQLite ou tabela sem `id` nada acontece.
- A verificação `{% if perms.menu_administracao %}` do template base resolve para `user.has_module_perms('menu_administracao')` (não existe app com esse rótulo): só é verdadeira para superusuários ativos. Do mesmo modo `check_permission: menu_administracao` nos YAML chama `user.has_perm('menu_administracao')` (sem `app_label`), verdadeiro apenas para superusuários; o nome real da permissão é `eauth.menu_1`. `_templates/crud/list_tabaux.html` usa `perms.eauth.menu_administracao` (também inexistente: o código é `menu_1`).
- A permissão `<app>.detail_<modelo>` consultada pelo consumer WebSocket não é criada por nenhum código; na prática vale `view_<modelo>`.
- O WebSocket sempre repassa a mensagem; apenas a chave `instance` é removida quando o usuário não tem permissão (o evento "algo mudou em `app:modelo`" continua visível a todos).
- Na API, `GET`/`HEAD`/`OPTIONS` exigem **ambas** `list_<modelo>` e `view_<modelo>` (`has_perms` exige todas); só é público se ambas estiverem em `perms_publicas`. Uma pública apenas parcial exige login e a outra permissão.
- Modelos não listados em `rules_patterns` (por exemplo `auth.group`) não têm entrada em `rules_patterns_public`; exigem permissões normais.
- `ContainerPermission` não é usada em lugar algum do código atual (código morto) e acessa `view.queryset.model` (falha se a view não tiver `queryset`).
- `globalrules/models.py` e `views.py` estão vazios e `urls.py` tem `urlpatterns = []`; `models.py` precisa existir para que o app emita `post_migrate` (exige `models_module`).

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O pacote `backend.globalrules` DEVE expor as constantes de prefixo `RP_LIST='.list_'`, `RP_VIEW='.view_'`, `RP_ADD='.add_'`, `RP_CHANGE='.change_'`, `RP_DELETE='.delete_'`.
- **FR-002**: O pacote DEVE declarar `GROUP_ADM_ADMIN = _('Administrador do Sistema')`, `GROUP_VISITANTE = ''`, `BACKEND_GROUPS = [GROUP_ADM_ADMIN]`, `menu_administracao = 'menu_1'`, `action_1 = 'orcamento_1'` e `PERMS_FOR_USERS = ((menu_administracao, _('Mostrar Menu 1')), (action_1, _('Ação 1')))`.
- **FR-003**: `VARS` DEVE capturar todas as variáveis de módulo cujo nome começa com `GROUP_`, `action_` ou `menu_`; `PERMS_FOR_USERS_DICT` DEVE ser `dict(PERMS_FOR_USERS)` atualizado com `VARS`; `MAP_GROUPS_AND_PERMS` DEVE ser o resultado de `dict2attr(PERMS_FOR_USERS_DICT)` (dicionário com acesso por atributo, ex.: `MAP_GROUPS_AND_PERMS.GROUP_ADM_ADMIN`).
- **FR-004**: `PERMS_FOR_USERS` DEVE ser usado como `Meta.permissions` do modelo `User` (feature 002), gerando as permissões `eauth.menu_1` e `eauth.orcamento_1`.
- **FR-005**: `backend/globalrules/map_rules.py` DEVE definir `rules_patterns = [rules_group_adm_admin, rules_group_visitante]`, onde cada grupo é `{"group": <nome>, "rules": [(modelo, perms, perms_publicas), ...]}`.
- **FR-006**: O grupo administrador DEVE ter regras para `User` (`__base__ + [menu_administracao]`, sem públicas), `Teste` (`__base__`, públicas `{RP_LIST, RP_VIEW}`) e `Metadata` (`__base__`, sem públicas), com `__base__ = [RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE]`.
- **FR-007**: `rules_patterns_public` DEVE ser um dicionário `"app_label:model_name"` → conjunto de permissões completas (`"<app_label><prefixo><model_name>"`, ex.: `utils.list_teste`), união das `perms_publicas` de todos os grupos; toda chave de modelo presente em alguma regra DEVE existir, mesmo com conjunto vazio.
- **FR-008**: Após cada `migrate`, para cada app com `models_module`, o sistema DEVE garantir a existência das permissões padrão do Django mais as de `Meta.permissions` mais `list_<modelo>` (nome: "Visualizaçao da lista de <verbose_name_plural>") para cada modelo, inclusive modelos proxy (resolvendo o `ContentType` do proxy).
- **FR-009**: A criação de permissões DEVE rejeitar (log de erro + `ValidationError`) nomes de permissão maiores que o `max_length` do campo `Permission.name`.
- **FR-010**: Após o `migrate` do app `globalrules`, o sistema DEVE, para cada grupo de `rules_patterns` com nome não vazio, obter/criar o `Group`, limpar suas permissões e associar as permissões declaradas; prefixos `RP_*` (iniciam com `.` e terminam com `_`) DEVEM ser convertidos em `<prefixo-sem-ponto><model_name>` e os demais valores usados como `codename` literal.
- **FR-011**: A atribuição de permissões NÃO DEVE interromper o `migrate` por erro: exceções são registradas (`logger.error` e `print`) e o processamento segue.
- **FR-012**: `Rules` DEVE oferecer `groups_add_user(user, groups_name)` e `groups_remove_user(user, groups_name)` (aceitam nome único ou lista; ignoram nomes vazios; criam o grupo se necessário).
- **FR-013**: Após o `migrate` de cada app, o sistema DEVE chamar `reset_id_model` para cada modelo `managed`, realinhando a sequência do `id` com `setval(pg_get_serial_sequence(...), coalesce(max(id),1), max(id) IS NOT NULL)` e recriando a sequência `<tabela>_id_seq` quando não houver vínculo; qualquer exceção DEVE ser ignorada.
- **FR-014**: A classe `BackendModelPermissions` (`backend/api/permissions.py`) DEVE ser a classe de permissão padrão do DRF (`REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']`) e mapear `GET/OPTIONS/HEAD` → `list_` + `view_`, `POST` → `add_`, `PUT/PATCH` → `change_`, `DELETE` → `delete_`.
- **FR-015**: `BackendModelPermissions.has_permission` DEVE: liberar views com `_ignore_model_permissions`; obter o queryset (`get_queryset()` ou `.queryset`) com `assert` de existência; calcular as permissões exigidas; liberar sem autenticação quando todas as exigidas estão em `rules_patterns_public["app:modelo"]`; caso contrário exigir usuário autenticado com `has_perms(perms)`.
- **FR-016**: `ContainerPermission` DEVE definir `view.permission_required` com as permissões exigidas pelo método e sempre retornar `True` (delegando a decisão à view).
- **FR-017**: O consumer WebSocket (`SyncRefreshConsumer`) DEVE usar `rules_patterns_public` e as permissões `<app>.detail_<modelo>`/`<app>.view_<modelo>` para decidir se a chave `instance` permanece na mensagem (ver `contracts/permissoes.md`).
- **FR-018**: O template base (`_templates/base.html`) DEVE exibir o menu de administração dentro de `{% if perms.menu_administracao %}`; os menus YAML DEVEM suportar a chave opcional `check_permission` avaliada com `user.has_perm(...)`.
- **FR-019**: O contrato com o CRUD genérico DEVE ser: `PermissionRequiredContainerCrudMixin.has_permission` libera a view se `permission_required` for vazio (view pública) ou se o usuário tiver **qualquer uma** das permissões; os nomes são montados por `permission(rad)` = `<app_label><rad><model_name>` para prefixos terminados em `_` (detalhes na feature 004).
- **FR-020**: O app DEVE se chamar `globalrules` (label) com `name = 'backend.globalrules'`, `default_auto_field = BigAutoField`, `verbose_name = _('Regras e Permissões para a Aplicação')`, e `__init__.py` DEVE conter `default_app_config = 'backend.globalrules.apps.AppConfig'` (exigido por `_tests/test_initials.py`).
- **FR-021**: `backend.globalrules` DEVE ser o último app do projeto em `INSTALLED_APPS`, de modo que seus sinais `post_migrate` rodem depois dos demais apps do projeto.

### Entidades-Chave

- **Regra de grupo** (`rules_group_*`): dicionário `{group, rules}` associando um grupo a regras por modelo.
- **Regra de modelo**: tupla `(modelo, perms, perms_publicas)` — permissões do grupo e permissões liberadas publicamente na API/WebSocket.
- **Permissões públicas** (`rules_patterns_public`): mapa derivado `app:modelo` → conjunto de permissões sem exigência de login.
- **Permissão** / **Grupo** / **ContentType** (`django.contrib.auth`/`contenttypes`): tabelas reutilizadas; não há tabelas novas.
- **Constantes de permissão** (`RP_*`, `PERMS_FOR_USERS`, `MAP_GROUPS_AND_PERMS`): vocabulário compartilhado pelo restante do código.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Após `migrate` em banco vazio, 100% dos modelos dos apps instalados possuem a permissão `list_<modelo>`.
- **SC-002**: Após `migrate`, o grupo "Administrador do Sistema" possui exatamente 16 permissões: 5 de `User` + `eauth.menu_1`, 5 de `Teste` e 5 de `Metadata`.
- **SC-003**: Executar `migrate` duas ou mais vezes consecutivas produz o mesmo estado de grupos/permissões e nenhuma exceção.
- **SC-004**: `GET /api/utils/teste/` sem credenciais retorna 200; `POST` sem credenciais retorna 401/403; `GET /api/eauth/user/` sem credenciais retorna 401/403.
- **SC-005**: `rules_patterns_public` contém exatamente as chaves `eauth:user`, `utils:teste`, `utils:metadata`, com `utils:teste == {'utils.list_teste', 'utils.view_teste'}` e as demais vazias.
- **SC-006**: Adicionar um novo modelo a `map_rules.py` e rodar `migrate` é suficiente (sem outra etapa manual) para criar as permissões e atribuí-las ao grupo.
- **SC-007**: Após restaurar dados com `id` explícito, a primeira inserção posterior ao `migrate` não gera erro de chave duplicada.

## Premissas

- Pré-requisitos: `001-fundacao-projeto-django` (configuração, `INSTALLED_APPS`, `backend.utilss.dict2attr`) e `002-autenticacao-usuarios-auditoria` (modelo `User` com `Meta.permissions = PERMS_FOR_USERS`). Os modelos `Teste` e `Metadata` pertencem ao app `utils` (`backend/utils/models.py`) e precisam existir para que `map_rules.py` seja importável; `Metadata` usa `ContentType` com `on_delete=PROTECT`.
- O banco em execução é PostgreSQL (Constituição); o ajuste de sequências é um no-op silencioso em outros bancos.
- O CRUD genérico (feature 004), a API automática (feature 005) e o WebSocket (feature 006) detalham o uso do contrato aqui descrito; esta feature descreve apenas a parte de permissões.
- O idioma ativo durante `migrate` é `pt-br`; o nome do grupo é uma string lazy resolvida no momento do uso e não há catálogo de tradução para ele.
- O teste de convenção `_tests/test_initials.py` exige `default_app_config` mesmo sendo ignorado pelo Django 6.
