# Modelo de Dados: Regras e Permissões Globais

**Não há tabelas novas.** `backend/globalrules/models.py` está vazio e `backend/globalrules/migrations/` contém apenas `__init__.py` (nenhuma migração). O app só existe para: (a) abrigar a configuração de regras, (b) emitir `post_migrate` (depende de `models_module`) e (c) expor constantes. As estruturas abaixo são configuração em memória e linhas nas tabelas padrão do Django.

## 1. Tabelas do Django utilizadas

| Tabela / modelo | Uso nesta feature |
|---|---|
| `auth_permission` (`django.contrib.auth.models.Permission`) | Recebe `list_<modelo>` para todo modelo, mais permissões de `Meta.permissions` (`menu_1`, `orcamento_1` em `eauth.user`). Campos relevantes: `content_type`, `codename`, `name` (limite `max_length` do campo, validado). |
| `auth_group` (`Group`) | Grupo "Administrador do Sistema" (`GROUP_ADM_ADMIN`), criado por `get_or_create(name=...)`. |
| `auth_group_permissions` | Limpa e reatribui a cada `migrate`. |
| `django_content_type` (`ContentType`) | Resolve a qual modelo pertence cada permissão; para modelos proxy cria o `ContentType` se faltar. |
| `eauth_user` | Tem `Meta.permissions = PERMS_FOR_USERS` (feature 002). |

Estado esperado após `migrate` em banco limpo (verificado no banco de desenvolvimento): 1 grupo; grupo com 16 permissões; `list_user`, `menu_1`, `orcamento_1` presentes em `eauth`; `list_<modelo>` para cada modelo.

## 2. Estruturas de configuração (em memória)

### 2.1 Constantes (`backend/globalrules/__init__.py`)

| Nome | Tipo | Valor |
|---|---|---|
| `RP_LIST` | `str` | `'.list_'` |
| `RP_VIEW` | `str` | `'.view_'` |
| `RP_ADD` | `str` | `'.add_'` |
| `RP_CHANGE` | `str` | `'.change_'` |
| `RP_DELETE` | `str` | `'.delete_'` |
| `GROUP_ADM_ADMIN` | lazy `str` | `_('Administrador do Sistema')` |
| `GROUP_VISITANTE` | `str` | `''` (ignorado) |
| `BACKEND_GROUPS` | `list` | `[GROUP_ADM_ADMIN]` |
| `menu_administracao` | `str` | `'menu_1'` |
| `action_1` | `str` | `'orcamento_1'` |
| `PERMS_FOR_USERS` | `tuple[tuple[str, lazy str]]` | `(('menu_1', 'Mostrar Menu 1'), ('orcamento_1', 'Ação 1'))` |
| `VARS` | `dict` | variáveis do módulo com prefixo `GROUP_`, `action_`, `menu_` |
| `PERMS_FOR_USERS_DICT` | `dict` | `dict(PERMS_FOR_USERS)` + `VARS` |
| `MAP_GROUPS_AND_PERMS` | `dict2attr` | `PERMS_FOR_USERS_DICT` com acesso por atributo |

Conteúdo de `PERMS_FOR_USERS_DICT`/`MAP_GROUPS_AND_PERMS`: `{'menu_1': 'Mostrar Menu 1', 'orcamento_1': 'Ação 1', 'GROUP_ADM_ADMIN': 'Administrador do Sistema', 'GROUP_VISITANTE': '', 'menu_administracao': 'menu_1', 'action_1': 'orcamento_1'}`.

### 2.2 Regras (`backend/globalrules/map_rules.py`)

```text
rules_patterns: list[RuleGroup]
RuleGroup = {"group": str|lazy, "rules": list[RuleModel]}
RuleModel = (model_class, perms: list[str], perms_publicas: set[str])
perms/perms_publicas: radicais RP_* ('.list_') ou codenames literais ('menu_1')
```

Instâncias: `rules_group_adm_admin` (3 regras) e `rules_group_visitante` (0 regras, grupo `''`).

| Modelo | Perms do grupo | Perms públicas |
|---|---|---|
| `get_user_model()` (`eauth.User`) | `list_user, view_user, add_user, change_user, delete_user, menu_1` | vazio |
| `utils.Teste` | `list/view/add/change/delete` | `{RP_LIST, RP_VIEW}` |
| `utils.Metadata` | `list/view/add/change/delete` | vazio |

### 2.3 Permissões públicas derivadas

`rules_patterns_public: dict[str, set[str]]` — chave `"<app_label>:<model_name>"`, valor conjunto de `"<app_label><radical><model_name>"`.

```text
{'eauth:user': set(), 'utils:teste': {'utils.list_teste', 'utils.view_teste'}, 'utils:metadata': set()}
```

Regras de construção: a chave existe para todo modelo presente em alguma regra; valores são a união (`|`) entre grupos.

### 2.4 `perms_map` da API (`BackendModelPermissions`)

| Método | Permissões exigidas (todas) |
|---|---|
| `GET`, `OPTIONS`, `HEAD` | `<app>.list_<modelo>`, `<app>.view_<modelo>` |
| `POST` | `<app>.add_<modelo>` |
| `PUT`, `PATCH` | `<app>.change_<modelo>` |
| `DELETE` | `<app>.delete_<modelo>` |

### 2.5 Metadados criados nos modelos (efeito de `post_migrate`)

Para cada modelo `klass` com `opts = klass._meta`: `opts.permissions = tuple(set([('list_' + opts.model_name, 'Visualizaçao da lista de ' + verbose_name_plural)] + list(opts.permissions)))`.

## 3. Comportamentos/transições

| Gatilho | Resultado |
|---|---|
| `post_migrate` (cada app com `models_module`) | `create_proxy_permissions` cria permissões ausentes; `check_ids_sequences` ajusta sequências dos modelos `managed` do app |
| `post_migrate` do app `globalrules` | `update_groups`: para cada grupo com nome → `get_or_create`, `permissions.clear()`, `permissions.add(...)`, `group.save()` |
| Permissão/ContentType ausente em `associar` | ContentType ausente → modelo ignorado; permissão ausente → `DoesNotExist` capturado em `_config_group` (log) |

## 4. Migrações iniciais

Nenhuma. Ordem de execução do `migrate`: apps na ordem de `INSTALLED_APPS`; `globalrules` por último, de modo que quando seu `post_migrate` roda, as permissões dos demais apps já foram criadas.

## 5. Unicidade e validação

- Unicidade herdada do Django: `Permission (content_type, codename)`, `Group.name`.
- Validação: `len(perm.name) <= Permission.name.max_length` (255) antes de `bulk_create`; senão `ValidationError` (a mensagem inclui o nome e o modelo).
