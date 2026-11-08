# Contrato: Permissões, Regras e Consumidores

Contratos externos/internos que outras features e clientes devem respeitar. Esta feature não define rotas HTTP próprias (`backend/globalrules/urls.py` tem `urlpatterns = []`).

## 1. Vocabulário Python (`backend.globalrules`)

| Símbolo | Descrição |
|---|---|
| `RP_LIST/RP_VIEW/RP_ADD/RP_CHANGE/RP_DELETE` | `'.list_'`, `'.view_'`, `'.add_'`, `'.change_'`, `'.delete_'` |
| `GROUP_ADM_ADMIN`, `GROUP_VISITANTE`, `BACKEND_GROUPS` | grupos |
| `PERMS_FOR_USERS` | usado em `User.Meta.permissions` |
| `MAP_GROUPS_AND_PERMS` | acesso por atributo a grupos e permissões (`.menu_administracao == 'menu_1'`) |
| `backend.globalrules.map_rules.rules_patterns` | lista de `{"group", "rules"}` |
| `backend.globalrules.map_rules.rules_patterns_public` | `{ "app:modelo": {"app.list_modelo", ...} }` |
| `backend.globalrules.apps.get_rules()` | retorna `Rules` (`associar`, `update_groups`, `groups_add_user`, `groups_remove_user`) |
| `backend.globalrules.apps.reset_id_model(model)` | realinha a sequência do `id` (PostgreSQL) |

Convenção de montagem de nomes: `app_label + RP_X + model_name` (ex.: `eauth` + `.list_` + `user` → `eauth.list_user`); `codename` = `RP_X[1:] + model_name`.

## 2. Permissões geradas

| Permissão | Origem |
|---|---|
| `<app>.add_/change_/delete_/view_<modelo>` | padrão do Django |
| `<app>.list_<modelo>` | `create_proxy_permissions` (todo modelo de todo app), nome "Visualizaçao da lista de `<verbose_name_plural>`" |
| `eauth.menu_1` ("Mostrar Menu 1") e `eauth.orcamento_1` ("Ação 1") | `User.Meta.permissions = PERMS_FOR_USERS` |
| `<app>.detail_<modelo>` | **não existe** (consultada pelo consumer WebSocket) |

## 3. Grupos gerenciados

| Grupo | Permissões após `migrate` |
|---|---|
| `Administrador do Sistema` | `list/view/add/change/delete` de `eauth.user`, `utils.teste`, `utils.metadata` + `eauth.menu_1` (16 no total) |

Regra: o conjunto é reescrito a cada `migrate` (clear + add).

## 4. API REST (`/api/<app>/<modelo>/`)

Classe: `backend.api.permissions.BackendModelPermissions` (padrão em `REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']`).

| Método HTTP | Permissões exigidas (todas) |
|---|---|
| `GET`, `HEAD`, `OPTIONS` | `<app>.list_<modelo>` e `<app>.view_<modelo>` |
| `POST` | `<app>.add_<modelo>` |
| `PUT`, `PATCH` | `<app>.change_<modelo>` |
| `DELETE` | `<app>.delete_<modelo>` |

Algoritmo de decisão:

1. `view._ignore_model_permissions` verdadeiro → permitido.
2. `perms` = permissões do método para o modelo do queryset.
3. Se `"app:modelo"` ∈ `rules_patterns_public` e `perms − públicas` é vazio → permitido, **sem autenticação**.
4. Senão: usuário autenticado e `user.has_perms(perms)` (superusuário passa).

Resultados esperados com as regras atuais:

| Requisição | Resultado |
|---|---|
| `GET /api/utils/teste/` anônimo | 200 |
| `POST /api/utils/teste/` anônimo | 401/403 (`TokenAuthentication` primeiro → 401 com `WWW-Authenticate`) |
| `GET /api/eauth/user/` anônimo | 401/403 |
| `GET /api/utils/metadata/` usuário com `list_metadata`+`view_metadata` | 200 |
| `GET /api/utils/metadata/` usuário autenticado sem permissões | 403 |
| Qualquer recurso, superusuário | permitido |

`ContainerPermission(BackendModelPermissions)`: define `view.permission_required` (lista de permissões do método) e retorna `True`; não usada no código atual.

## 5. WebSocket `/ws/sync/` (`SyncRefreshConsumer.sync_refresh_message`)

Entrada: mensagem do grupo `group_sync_refresh_channel` com `app`, `model` e (opcional) `instance`.

| Usuário | Mantém `instance` quando |
|---|---|
| Anônimo, modelo sem públicas | nunca |
| Anônimo, modelo com públicas | `"<app>.detail_<model>"` ou `"<app>.view_<model>"` ∈ `rules_patterns_public["app:model"]` |
| Autenticado não superusuário | `has_perm("<app>.detail_<model>")` ou `has_perm("<app>.view_<model>")` |
| Superusuário | sempre |

Sem permissão: remove `instance` da mensagem (se existir) e **envia a mensagem mesmo assim**. Exceções → `{"type": "error", "error": "<texto>"}`. Detalhes do protocolo: feature 006.

## 6. Templates e menus

- `_templates/base.html`: `{% if perms.menu_administracao %}` → renderiza `{% menu 'menus/menu_administracao.yaml' %}` (verdadeiro apenas para superusuário; ver `research.md`, item 10).
- Menus YAML (`_templates/menus/*.yaml`): chave opcional `check_permission` (string passada a `user.has_perm`). Item com `url` e sem permissão → `url = ""` e `active = ""`; item sem `url` e sem permissão → `active = ""` e remoção de `children`. Valor usado: `check_permission: menu_administracao` (em "Manutenção de Usuários" e "Testes"). `_templates/menus/menu_main.yaml` apenas documenta `check_permission: teste` no comentário de exemplo.
- `_templates/crud/list_tabaux.html`: `perms.eauth.menu_administracao` (não resolve para o código real `menu_1`).

## 7. Contrato com o CRUD genérico (`backend/crud/base.py`, feature 004)

| Elemento | Contrato |
|---|---|
| `permission(rad)` | `"<app_label><rad><model_name>"` quando `rad` termina em `_`; senão `rad` literal |
| `permission_required` das views | lista de radicais `RP_*` (`ListView` → `RP_LIST`, `DetailView` → `RP_VIEW`, `CreateView` → `RP_ADD`, `UpdateView` → `RP_CHANGE`, `DeleteView` → `RP_DELETE`), convertidos em nomes completos, excluindo os radicais presentes em `crud.public` |
| `PermissionRequiredContainerCrudMixin.has_permission` | `permission_required` vazio → view pública; senão, **qualquer** permissão satisfaz |
| URLs de ação (`list_url`, `create_url`…) | só retornadas se a view é pública ou o usuário tem a permissão correspondente |

## 8. Sinais `post_migrate` (ordem de registro)

| `dispatch_uid` | Função | Efeito |
|---|---|---|
| `django.contrib.auth.management.create_permissions` | `create_proxy_permissions` | cria permissões (padrão + `Meta.permissions` + `list_`) |
| `update_groups` | `update_groups` | sincroniza grupos (somente no sinal do app `globalrules`) |
| `check_ids_sequences` | `check_ids_sequences` | `reset_id_model` para cada modelo `managed` do app |

## 9. Saída de console do `migrate`

`update_groups` imprime (cabeçalho em amarelo/negrito): "Atualizando grupos do Sistema:" e, para cada grupo processado, uma linha `  <nome do grupo>`. Permissões criadas imprimem `Adding permission '<perm>'` quando `verbosity >= 2`.

## 10. Variáveis de ambiente / portas / CLI

Nenhuma específica. Comando de aplicação: `python manage.py migrate`.
