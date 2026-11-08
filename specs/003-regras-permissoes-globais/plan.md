# Plano de Implementação: Regras e Permissões Globais

**Branch**: `003-regras-permissoes-globais` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/003-regras-permissoes-globais/spec.md`

## Resumo

Centralizar a autorização do projeto em um app (`backend/globalrules`) que (1) define o vocabulário de permissões (`RP_*`, `PERMS_FOR_USERS`, grupos), (2) declara em uma tabela (`map_rules.py`) quais grupos têm quais permissões por modelo e quais permissões são públicas, (3) usa sinais `post_migrate` para criar a permissão `list_<modelo>`, sincronizar grupos e realinhar sequências de ids, e (4) alimenta a classe de permissão do DRF (`backend/api/permissions.py`), o consumer WebSocket, os menus YAML/templates e o CRUD genérico.

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (ambiente local `.venv` com 3.12), Django 6.0.x (`pyproject.toml`: `django = ">=6,<7"`)

**Dependências Principais**: `django.contrib.auth` / `contenttypes`, Django REST Framework (`^3.18.3`), Channels (consumer), `psycopg` 3 (PostgreSQL)

**Armazenamento**: PostgreSQL (tabelas `auth_permission`, `auth_group`, `auth_group_permissions`, `django_content_type`); nenhuma tabela nova

**Testes**: pytest + pytest-django + model-bakery + django-webtest (`pyproject.toml`, `[tool.pytest.ini_options]`: `DJANGO_SETTINGS_MODULE = "backend.settings"`, `--reuse-db`)

**Plataforma Alvo**: servidor Linux (Docker)

**Tipo de Projeto**: serviço web (app Django dentro do pacote `backend`)

**Metas de Desempenho**: custo apenas em `migrate` (uma consulta `setval` por modelo gerenciado; `permissions.clear()` + `add` por regra); `rules_patterns_public` é um dicionário em memória consultado em O(1) por requisição

**Restrições**: o ajuste de sequências só funciona em PostgreSQL; `map_rules.py` importa modelos (`get_user_model()`, `Teste`, `Metadata`) em tempo de importação, portanto só pode ser importado após o registro de apps (por isso `apps.py` importa `map_rules` dentro de `get_rules()` e o consumer o importa em `__init__`)

**Escala/Escopo**: 1 grupo gerenciado, 3 modelos com regras, 2 permissões de menu/ação

## Verificação da Constituição

| Princípio | Gate | Situação |
|---|---|---|
| I. Backend Django modular | App próprio `backend/globalrules` com `apps.py`, `models.py`, `urls.py`, `views.py`; registrado em `backend/settings/apps.py` | Atendido |
| II. Configuração por ambiente | Nenhuma configuração/segredo novo; usa apenas `settings.REST_FRAMEWORK` | Atendido |
| III. Paridade dev/prod | Comportamento idêntico nos dois ambientes (sinais de `migrate`) | Atendido |
| IV. API REST gerada, permissões por modelo | `BackendModelPermissions` padrão do DRF + `list_<modelo>` + `rules_patterns_public`; regras só em `map_rules.py`, aplicadas após `migrate` | Atendido (é a implementação do princípio) |
| V. Frontend Vite | Sem impacto direto | Atendido (N/A) |
| VI. Tempo real respeita permissões | Consumer usa `rules_patterns_public` e `view_`/`detail_` | Atendido (com ressalvas em `research.md`) |
| VII. PT-BR | Nomes lazy em PT-BR (`gettext_lazy`) | Atendido |
| VIII. Qualidade verificável | Tarefas de testes pytest e `ruff` em `tasks.md`; o app original não possui testes próprios (lacuna registrada) | Atendido com testes planejados |

Reverificação pós-design: sem mudanças.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/003-regras-permissoes-globais/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── permissoes.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── globalrules/
│   ├── __init__.py        # RP_*, GROUP_*, PERMS_FOR_USERS, VARS, MAP_GROUPS_AND_PERMS, default_app_config
│   ├── apps.py            # AppConfig + receivers post_migrate + get_rules()/Rules + reset_id_model
│   ├── map_rules.py       # rules_patterns, rules_patterns_public
│   ├── models.py          # vazio (necessário para emitir post_migrate)
│   ├── views.py           # vazio
│   ├── urls.py            # urlpatterns = []
│   └── migrations/
│       └── __init__.py    # sem migrações
├── api/
│   └── permissions.py     # BackendModelPermissions, ContainerPermission
├── settings/
│   ├── apps.py            # "backend.globalrules" por último em INSTALLED_APPS
│   └── drf.py             # DEFAULT_PERMISSION_CLASSES
├── eauth/models.py        # User.Meta.permissions = PERMS_FOR_USERS (feature 002)
├── utils/
│   ├── consumers.py       # SyncRefreshConsumer usa rules_patterns_public (feature 006)
│   └── templatetags/menus.py   # check_permission (feature 004)
└── crud/base.py           # RP_*, PermissionRequiredContainerCrudMixin (feature 004)
_templates/
├── base.html              # {% if perms.menu_administracao %}
└── menus/menu_administracao.yaml   # check_permission: menu_administracao
_tests/test_initials.py    # exige default_app_config
```

**Decisão de Estrutura**: um app Django único e sem modelos próprios; a lógica fica em `apps.py` (sinais) e `map_rules.py` (dados), com o vocabulário em `__init__.py` para ser importável sem carregar modelos (`backend.eauth.models` importa `PERMS_FOR_USERS` de `backend.globalrules`).

## Rastreamento de Complexidade

Sem violações.

## Detalhamento de Implementação

### 1. `backend/globalrules/__init__.py` (vocabulário)

- `from django.utils.translation import gettext_lazy as _` e `from backend.utilss import dict2attr`.
- `default_app_config = 'backend.globalrules.apps.AppConfig'` (ignorado pelo Django 6, mas exigido por `_tests/test_initials.py`).
- `RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE = ('.list_', '.view_', '.add_', '.change_', '.delete_')`.
- `GROUP_ADM_ADMIN = _('Administrador do Sistema')`; `GROUP_VISITANTE = ''`; `BACKEND_GROUPS = [GROUP_ADM_ADMIN]`.
- `menu_administracao = 'menu_1'`; `action_1 = 'orcamento_1'`.
- `PERMS_FOR_USERS = ((menu_administracao, _('Mostrar Menu 1')), (action_1, _('Ação 1')))`.
- `VARS = {k: v for k, v in locals().items() if k.startswith('GROUP_') or k.startswith('action_') or k.startswith('menu_')}` (compreensão sobre `locals()` no nível de módulo: captura `GROUP_ADM_ADMIN`, `GROUP_VISITANTE`, `action_1`, `menu_administracao`).
- `PERMS_FOR_USERS_DICT = dict(PERMS_FOR_USERS); PERMS_FOR_USERS_DICT.update(VARS)` → `{'menu_1': 'Mostrar Menu 1', 'orcamento_1': 'Ação 1', 'GROUP_ADM_ADMIN': ..., 'GROUP_VISITANTE': '', 'menu_administracao': 'menu_1', 'action_1': 'orcamento_1'}`.
- `MAP_GROUPS_AND_PERMS = dict2attr(PERMS_FOR_USERS_DICT)`; `dict2attr` (`backend/utilss.py`) cria uma subclasse de `dict` cujas chaves também são atributos (`setattr`) e retorna a instância com `update(value)`.
- Este módulo NÃO pode importar modelos (é importado por `eauth/models.py`).

### 2. `backend/globalrules/map_rules.py` (tabela de regras)

- Importa `get_user_model`, `MAP_GROUPS_AND_PERMS`, `RP_*` e `Metadata`, `Teste` de `backend.utils.models`.
- `__base__ = [RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE]`; `__base_view__ = [RP_LIST, RP_VIEW]`; `__base_change__ = [RP_LIST, RP_VIEW, RP_CHANGE]` (não usado); `__perms_publicas__ = {}` (não usado).
- `rules_group_adm_admin = {"group": MAP_GROUPS_AND_PERMS.GROUP_ADM_ADMIN, "rules": [(get_user_model(), __base__ + [MAP_GROUPS_AND_PERMS.menu_administracao], set()), (Teste, __base__, set(__base_view__)), (Metadata, __base__, set())]}`.
- `rules_group_visitante = {"group": MAP_GROUPS_AND_PERMS.GROUP_VISITANTE, "rules": []}`; `rules_patterns = [rules_group_adm_admin, rules_group_visitante]`.
- Construção de `rules_patterns_public` (dict): para cada grupo e cada regra `(modelo, perms, publicas)`: `key = "%s:%s" % (app_label, model_name)` (função `_get_registration_key`); `rules_patterns_public.setdefault(key, set())`; `rules_patterns_public[key] |= {"{}{}{}".format(app_label, prefixo, model_name) for prefixo in publicas}` (ex.: `'utils.list_teste'`). Resultado: `{'eauth:user': set(), 'utils:teste': {'utils.list_teste','utils.view_teste'}, 'utils:metadata': set()}`.
- Para adicionar permissões públicas de um modelo, basta incluir os prefixos `RP_*` no 3º item da tupla.

### 3. `backend/globalrules/apps.py` (sinais)

**Classe**: `AppConfig(django.apps.AppConfig)` com `default_auto_field='django.db.models.BigAutoField'`, `name='backend.globalrules'`, `label='globalrules'`, `verbose_name=_('Regras e Permissões para a Aplicação')`. Atenção: o módulo faz `from django import apps` (o nome `apps` é o módulo; usa `apps.apps.get_model`).

**Receiver 1 — `create_proxy_permissions`** (`@receiver(post_migrate, dispatch_uid='django.contrib.auth.management.create_permissions')`, assinatura `(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, **kwargs)`). Algoritmo:
1. Retorna se `not app_config.models_module`.
2. `Permission = apps.apps.get_model('auth', 'Permission')` (LookupError → log e retorna); retorna se `not router.allow_migrate_model(using, Permission)`.
3. Para cada `klass` em `app_config.get_models()`: monta `permissions = (('list_' + opts.model_name, format_lazy('{} {}', _('Visualizaçao da lista de'), opts.verbose_name_plural)),)`; atribui `opts.permissions = tuple(set(list(permissions) + list(opts.permissions)))` (mutação de `Meta`).
4. `ContentType`: se `opts.proxy`, tenta `ContentType.objects.db_manager(using).get_by_natural_key(app_label, model)` e, em exceção, `create(app_label=..., model=...)`; senão `get_for_model(klass)`. Acumula `ctypes`.
5. `_get_all_permissions(klass._meta)` (import privado de `django.contrib.auth.management`) retorna as padrão + `Meta.permissions`; acumula `(ctype, (codename, name))`.
6. Busca `(content_type, codename)` existentes em `Permission` filtrando `content_type__in=ctypes`; cria com `bulk_create` as ausentes.
7. Antes de criar, valida `len(perm.name) > Permission._meta.get_field('name').max_length` → `logger.error` + `raise exceptions.ValidationError`.
8. Se `verbosity >= 2`, imprime `Adding permission '<perm>'`.
- Efeito de bastidor: pelo mesmo `dispatch_uid`, este receptor é registrado (na importação do módulo de apps, fase 1 de `apps.populate`) antes do `ready()` de `django.contrib.auth`, que então tem seu `connect` ignorado por `Signal.connect` (dedup por `(dispatch_uid, id(sender))`). Para reproduzir fielmente mantenha o `dispatch_uid`.

**Função `get_rules()`** (imports tardios de `Group`, `Permission`, `ContentType` e `from .map_rules import rules_patterns`) devolve `Rules(rules_patterns)`; classe `Rules`:
- `associar(self, g, model, tipo)`: `ContentType.objects.get_by_natural_key(app_label=..., model=...)` num `try/except:` nu que dá `return` em falha; para cada `t` em `tipo`: `codename = (t[1:] + model._meta.model_name) if t[0] == '.' and t[-1] == '_' else t`; `p = Permission.objects.get(content_type=content_type, codename=codename)`; `g.permissions.add(p)`; ao final `g.save()`.
- `_config_group(self, group_name, rules_list)`: `if not group_name: return`; `group, created = Group.objects.get_or_create(name=group_name)`; `group.permissions.clear()`; dentro de `try`: `print(' ', group_name)` e, para cada `(model, perms, perms_publicas)`, `self.associar(group, model, perms)`; `except Exception as e`: `logger.error(str(e))` + `print(group_name, e)`.
- `groups_add_user` / `groups_remove_user`: normalizam `groups_name` para lista; ignoram nomes vazios; `Group.objects.get_or_create(name=...)[0]`; `user.groups.add/remove`; evitam operação redundante via `user.groups.filter(name=...).exists()`.
- `update_groups(self)`: imprime cabeçalho amarelo/negrito (`'\033[93m\033[1m'` + `_('Atualizando grupos do Sistema:')` + `'\033[0m'`) e chama `_config_group(rules_group['group'], rules_group['rules'])` para cada item de `rules_patterns`.

**Receiver 2 — `update_groups`** (`dispatch_uid='update_groups'`): retorna se `app_config != AppConfig and not isinstance(app_config, AppConfig)` (só age no `post_migrate` do próprio app); senão `get_rules().update_groups()`.

**Receiver 3 — `check_ids_sequences`** (`dispatch_uid='check_ids_sequences'`): para cada `model` em `app_config.models.values()` com `model._meta.managed`, chama `reset_id_model(model)`.

**`reset_id_model(model)`**: monta `query = SELECT setval(pg_get_serial_sequence('<tabela>','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "<tabela>";` (interpolação com `%` do nome da tabela `model._meta.db_table`); dentro de `try`: executa com `connection.cursor()`, `fetchall()`; se `rows[0][0] is None` (sem sequência vinculada), executa `DROP SEQUENCE IF EXISTS <tabela>_id_seq cascade; CREATE SEQUENCE <tabela>_id_seq start 1 OWNED BY <tabela>.id; ALTER TABLE <tabela> ALTER COLUMN id SET DEFAULT nextval('<tabela>_id_seq'::regclass);` seguido de `query`; `except:` nu → `pass`. Usa a conexão `default` (`django.db.connection`), não `using`.

### 4. `backend/api/permissions.py`

- `BackendModelPermissions(rest_framework.permissions.DjangoModelPermissions)` com `perms_map` próprio (tabela em `contracts/permissoes.md`), em formato `"%(app_label)s.<prefixo>%(model_name)s"`.
- `has_permission(self, request, view)`: (1) `getattr(view, "_ignore_model_permissions", False)` → `True`; (2) queryset via `view.get_queryset()` se existir, senão `view.queryset`; `assert queryset is not None`; (3) `perms = self.get_required_permissions(request.method, queryset.model)`; (4) `key = "{app_label}:{model_name}"`; se `key in backend_rpp`: `private_perms = set(perms) - backend_rpp[key]`; se vazio → `True`; (5) retorno final `request.user and (request.user.is_authenticated or not self.authenticated_users_only) and request.user.has_perms(perms)`.
- `ContainerPermission(BackendModelPermissions).has_permission`: `view.permission_required = self.get_required_permissions(request.method, view.queryset.model)`; `return True`.
- `backend/settings/drf.py`: `"DEFAULT_PERMISSION_CLASSES": ("backend.api.permissions.BackendModelPermissions",)`. Importa `rules_patterns_public as backend_rpp` de `backend.globalrules.map_rules` no topo do módulo.
- Autenticação padrão (`TokenAuthentication`, `SessionAuthentication`) é descrita na feature 005.

### 5. Consumo em outros pontos (apenas contrato)

- **Modelo `User`** (`backend/eauth/models.py`): `from backend.globalrules import PERMS_FOR_USERS` e `class Meta(AbstractBaseUser.Meta): permissions = PERMS_FOR_USERS`.
- **WebSocket** (`backend/utils/consumers.py`, `SyncRefreshConsumer.__init__` importa `rules_patterns_public`; `sync_refresh_message`): `key = f"{app}:{model}"`, `perms_publicas = rules_patterns_public.get(key, set())`; `perm_detail = f"{app}.detail_{model}"`, `perm_view = f"{app}.view_{model}"`; anônimo sem públicas → sem permissão; anônimo com públicas → `perm_detail in perms_publicas or perm_view in perms_publicas`; autenticado não superusuário → `has_perm(perm_detail)` e, se falso, `has_perm(perm_view)` (via `database_sync_to_async`); superusuário → permitido. Sem permissão: `del message["instance"]` (KeyError ignorado); a mensagem é enviada de qualquer forma. Detalhes na feature 006.
- **Template base** (`_templates/base.html`): `{% if perms.menu_administracao %}<ul class="navbar-nav nav-admin">{% menu 'menus/menu_administracao.yaml' %}</ul>{% endif %}`.
- **Menus** (`backend/utils/templatetags/menus.py`, função `resolve_urls_inplace`): item com `url` e `check_permission` cujo `user.has_perm(check_permission)` é falso → `menu["url"] = ""` e `menu["active"] = ""`; item sem `url` com `check_permission` falso → `menu["active"] = ""` e `del menu["children"]`. Em `_templates/menus/menu_administracao.yaml`, `check_permission: menu_administracao` aparece nos grupos "Manutenção de Usuários" e "Testes" (este dentro de `{% if user.is_superuser %}`).
- **CRUD genérico** (`backend/crud/base.py`, só contrato; feature 004): importa `RP_ADD, RP_CHANGE, RP_DELETE, RP_LIST, RP_VIEW`; `permission(rad)` retorna `"%s%s%s" % (app_label if rad.endswith("_") else "", rad, model_name if rad.endswith("_") else "")` — com `rad='.list_'` produz `eauth.list_user`; em `CrudBaseMixin.__init__`, `permission_required` = permissões não listadas em `obj.public`, convertidas por `permission()`; `PermissionRequiredContainerCrudMixin.has_permission` libera se `permission_required` vazio ou se o usuário possuir **qualquer** permissão da lista (OU lógico, ao contrário do `AND` do `PermissionRequiredMixin` padrão). `PermissionRequiredForAppCrudMixin` exige `has_module_perms(app)` para todos os apps de `app_label`.
- **`PesquisarAuditLogView`** (`backend/eauth/views.py`): `permission_required = ('eauth.list_auditlog',)` — usa a permissão `list_` criada por esta feature (feature 002).

### 6. Registro e configuração

- `backend/settings/apps.py`: `INSTALLED_APPS = DJANGO_CORE_APPS + DJANGO_THIRD_PARTY_APPS + BACKEND_APPS + ["backend.api", "backend.globalrules"]` (`BACKEND_APPS = ["backend.eauth", "backend.utils"]`). `globalrules` por último.
- `backend/globalrules/models.py` DEVE existir (vazio) para que `app_config.models_module` não seja `None` e o `post_migrate` seja emitido para o app (`emit_post_migrate_signal` ignora apps sem `models_module`).
- `backend/globalrules/urls.py`: `urlpatterns = []`. `views.py`: vazio. `migrations/__init__.py`: vazio.
- Variáveis de ambiente: nenhuma.

### 7. Como estender (receita)

1. Novo modelo com API/CRUD: adicionar a tupla `(Modelo, __base__, set())` (e, se leitura pública, `set(__base_view__)`) à lista `rules` do grupo em `map_rules.py`.
2. Nova permissão customizada: declarar em `Meta.permissions` do modelo (ou em `PERMS_FOR_USERS` para `User`) e listar o `codename` literal em `perms` da regra; variável `action_*`/`menu_*` em `__init__.py` entra automaticamente em `MAP_GROUPS_AND_PERMS`.
3. Novo grupo: constante `GROUP_*` em `__init__.py` + dicionário `{"group": ..., "rules": [...]}` incluído em `rules_patterns`.
4. Rodar `python manage.py migrate` para aplicar.
