# Modelo de Dados: Autenticação, Usuários e Auditoria (app `eauth`)

Migração inicial: `backend/eauth/migrations/0001_initial.py` (gerada pelo Django 6.0.10; `initial = True`; dependências `auth.0012_alter_user_first_name_max_length` e `contenttypes.0002_remove_content_type_name`). `default_auto_field = 'django.db.models.BigAutoField'` ⇒ chaves primárias `bigint`.

## Entidade `User` (`eauth.User`, tabela `eauth_user`)

Herança: `AbstractBaseUser` + `SearchModelMixin` (`backend/model_mixins.py`, feature 001) + `PermissionsMixin` + `models.Model`. `AUTH_USER_MODEL = "eauth.User"`.

| Campo | Tipo / opções | Origem | Observações |
|-------|---------------|--------|-------------|
| `id` | `BigAutoField` PK | modelo | |
| `password` | `CharField(128)` | `AbstractBaseUser` | hash; `set_password()` |
| `last_login` | `DateTimeField(null=True, blank=True)` | `AbstractBaseUser` | |
| `is_superuser` | `BooleanField(default=False)` | `PermissionsMixin` | |
| `groups` | `ManyToManyField(auth.Group, blank=True, related_name='user_set', related_query_name='user')` | `PermissionsMixin` | tabela `eauth_user_groups` |
| `user_permissions` | `ManyToManyField(auth.Permission, blank=True, related_name='user_set', related_query_name='user')` | `PermissionsMixin` | tabela `eauth_user_user_permissions` |
| `search` | `TextField(blank=True, default='')` | `SearchModelMixin` | recalculado em `save()` a partir de `fields_search`, normalizado |
| `email` | `EmailField('email address', unique=True)` (`max_length=254`) | modelo | `USERNAME_FIELD`; único (sem normalização de caixa no banco) |
| `first_name` | `CharField('first name', max_length=30, blank=True)` | modelo | |
| `last_name` | `CharField('last name', max_length=30, blank=True)` | modelo | |
| `is_staff` | `BooleanField('staff status', default=False)` | modelo | acesso ao Django Admin e à API `IsAdminUser` |
| `is_active` | `BooleanField('active', default=True)` | modelo | desativar em vez de excluir |
| `date_joined` | `DateTimeField('date joined', default=timezone.now)` | modelo | |
| `avatar` | `ImageCropField(upload_to='avatars/', verbose_name='Avatar', validators=[avatar_validation], null=True, blank=True)` | modelo (`image_cropping`) | até 10 MiB; armazenamento/entrega: feature 009 |
| `avatar_cropping` | `ImageRatioField('avatar', '128x128', verbose_name='Seleção (Enquadramento)', help_text=...)` | modelo | guarda a caixa de corte `x1,y1,x2,y2` (texto); opções padrão na migração: `adapt_rotation=False, allow_fullsize=False, free_crop=False, hide_image_field=False, size_warning=True` |

Constantes/atributos de classe: `FIELDFILE_NAME = ('avatar',)`; `fields_search = ['first_name', 'last_name', 'email']`; `objects = UserManager()`; `USERNAME_FIELD = 'email'`. `REQUIRED_FIELDS` permanece o padrão (vazio).

`Meta(AbstractBaseUser.Meta)`: `abstract = False`; `permissions = PERMS_FOR_USERS` (hoje `('menu_1', 'Mostrar Menu 1')`, `('orcamento_1', 'Ação 1')`, de `backend/globalrules/__init__.py`, feature 003); `ordering = ('-is_superuser', 'first_name', 'last_name')`; `verbose_name = 'Usuário'`; `verbose_name_plural = 'Usuários'`.

Permissões geradas: `add_user`, `change_user`, `delete_user`, `view_user`, `menu_1`, `orcamento_1` e `list_user` (criada por `backend/globalrules/apps.py`, feature 003).

Propriedades/métodos: `username` (= e-mail), `get_full_name()`, `get_short_name()`, `get_display_name()` (nome completo ou e-mail), `__str__`, `get_absolute_url()` (tupla — ver research.md #20).

Validações: e-mail único e válido; `avatar_validation` (tamanho máximo 10 MiB, mensagem "The maximum file size is 10.0MiB"); senha pelos validadores de `settings/auth.py`.

### `UserManager(BaseUserManager)` (`use_in_migrations = True`)

- `_create_user(email, password, is_staff, is_superuser, **extra_fields)`: ver plan.md §3 (e-mail obrigatório → `ValueError('The given email must be set')`; `normalize_email`; `is_active=True`; `date_joined=now`; `set_password`; `save` com exceção engolida ⇒ retorna o usuário existente por `get_by_natural_key`).
- `create_user(email, password=None, **extra_fields)` → `_create_user(email, password, False, False, ...)`.
- `create_superuser(email, password, **extra_fields)` → `_create_user(email, password, True, True, ...)`.

### Funções auxiliares do módulo `models.py`

| Função | Assinatura | Comportamento |
|--------|-----------|---------------|
| `groups_add_user` | `(user, groups_name)` | adiciona o usuário aos grupos (cria o grupo se preciso); ignora vazios/já pertencentes |
| `groups_remove_user` | `(user, groups_name)` | remove do(s) grupo(s) existente(s) no usuário; ignora vazios/não pertencentes |
| `sizeof_fmt` | `(num, suffix='B')` | tamanho legível (KiB, MiB, …) |
| `avatar_validation` | `(image)` | `ValidationError` se `image.size > 10 * 1024 * 1024` |

## Entidade `AuditLog` (`eauth.AuditLog`, tabela `eauth_auditlog`)

| Campo | Tipo / opções | Observações |
|-------|---------------|-------------|
| `id` | `BigAutoField` PK | |
| `user` | `ForeignKey(AUTH_USER_MODEL, verbose_name='Usuário', on_delete=SET_NULL, null=True, blank=True, default=None)` | via `get_settings_auth_user_model()`; sem `related_name` (padrão `auditlog_set`) |
| `email` | `CharField(max_length=100, verbose_name='email', blank=True, db_index=True)` | e-mail do autor na data do evento (cópia) |
| `operation` | `CharField(max_length=1, choices=OPERATION_CHOICES, db_index=True, verbose_name='operation')` | `U` Atualizado, `C` Criado, `D` Excluído, `P` Pesquisa (nunca gerada) |
| `timestamp` | `DateTimeField(verbose_name='timestamp', editable=False, auto_now_add=True)` | |
| `obj` | `JSONField(verbose_name='Object', blank=True, null=True, default=None, encoder=DjangoJSONEncoder)` | resultado de `serializers.serialize('json', (instance,))` (lista de um item `{model, pk, fields}`) + chave `stack` no item 0 |
| `content_type` | `ForeignKey(ContentType, null=True, blank=True, default=None, on_delete=PROTECT)` | |
| `object_id` | `PositiveIntegerField(null=True, blank=True, default=None)` | usado pelo filtro `id=` |
| `content_object` | `GenericForeignKey('content_type', 'object_id')` | `None` em exclusões |
| `obj_id` | `PositiveIntegerField(verbose_name='object_id', db_index=True)` | obrigatório (`instance.id`) |
| `model_name` | `CharField(max_length=100, db_index=True, verbose_name='model')` | `instance._meta.model_name` |
| `app_name` | `CharField(max_length=100, db_index=True, verbose_name='app')` | `instance._meta.app_label` |

`Meta`: `verbose_name = 'AuditLog'`, `verbose_name_plural = 'AuditLogs'`, `ordering = ('-id',)`. `__str__`: `'[<timestamp>] <operation> <app_name>.<model_name> <user>'`.
Índices: `db_index=True` em `email`, `operation`, `obj_id`, `model_name`, `app_name` (mais os de FK).
Não há `unique_together`.

### `AuditLogManager(models.Manager)`

`use_for_related_fields = True` (obsoleto no Django moderno); `last_action_user()` → primeiro registro com `user` preenchido (mais recente, por `-id`); `first_action_user()` → o último (mais antigo); `actions_users()` → queryset com `user__isnull=False`.

### Transições / comportamento (sinais)

`post_save` (criação → `C`; alteração → `U`) e `post_delete` (→ `D`) de qualquer modelo disparam `auditlog_post_signal` (`backend/eauth/services/signals.py`). A gravação só ocorre para modelos cujo `app_config.name[:10] == 'backend'` — condição **nunca satisfeita** no estado atual (ver research.md #1); registros de `AuditLog` e execuções sob `migrate` são ignorados. Falhas na gravação são apenas logadas (`logger.error`). O `AuditLog` é ignorado pela sincronização em tempo real (`backend/utils/services/signals_syncrefresh.py`).

## Estruturas não persistidas

| Estrutura | Local | Descrição |
|-----------|-------|-----------|
| Campos virtuais de formulário | `forms_auth.py` | `current_password`, `new_password1`, `new_password2` (perfil); `new_password1/2` e `token` (admin) — não existem no modelo |
| `AuditLogFilterSet` | `forms.py` | filtros `user`, `busca`, `operation`, `model_name`, `timestamp` (`DateRangeFilter`: hoje, ontem, 7 dias ("week"), mês, ano) |
| Layouts YAML | `_templates/eauth/layouts.yaml` | `UserDetail`, `UserCreate` (ver `contracts/templates-e-configuracao.md`) |
| Token de API | `rest_framework.authtoken.Token` (`related_name='auth_token'`) | tabela `authtoken_token`, pertence à feature 005, exibida/renovada na edição de usuário |

## Migração inicial — resumo das operações

1. `CreateModel User` com todos os campos acima, `options` (`verbose_name`, `verbose_name_plural`, `ordering`, `permissions`, `abstract=False`) e `managers=[('objects', backend.eauth.models.UserManager())]`.
2. `CreateModel AuditLog` com `user` → `settings.AUTH_USER_MODEL` (`SET_NULL`), `content_type` → `contenttypes.contenttype` (`PROTECT`) e `options` (`verbose_name`, `verbose_name_plural`, `ordering`).

A migração referencia `backend.eauth.models.avatar_validation` e `backend.eauth.models.UserManager`; ambos DEVEM continuar importáveis.
