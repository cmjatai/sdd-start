# Plano de Implementação: Autenticação, Usuários e Auditoria (app `eauth`)

**Branch**: `002-autenticacao-usuarios-auditoria` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `specs/002-autenticacao-usuarios-auditoria/spec.md`

## Resumo

Implementa o app Django `backend.eauth` (label `eauth`): modelo de usuário customizado identificado por e-mail (`eauth.User`), gerenciador com `create_user`/`create_superuser`, telas de login/logout, recuperação de senha com reCAPTCHA, edição do próprio perfil, CRUD administrativo de usuários (sobre o `Crud` da feature 004), modelo e sinal de auditoria (`AuditLog`) e a tela de pesquisa de auditoria. Abordagem: reaproveitar as views/formulários de `django.contrib.auth` com subclasses e templates próprios em `_templates/eauth/`, configuração em `backend/settings/auth.py`, crispy-forms (Bootstrap 5) para layout e `django-filter` para a pesquisa de auditoria. Detalhes de reconstrução em "Detalhamento de Implementação"; decisões e dívidas em [research.md](./research.md).

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (venv local 3.12; imagem-base 3.14), Django 6.0.x (`>=6,<7`; migração gerada com 6.0.10)

**Dependências Principais**: `django.contrib.auth`, `django-crispy-forms` 2.7 + `crispy-bootstrap5`, `django-filter` ^26.2, `django-braces` ^1.17 (`FormMessagesMixin`), `django-image-cropping` ^1.7 + `easy-thumbnails` (avatar, feature 009), `djangorestframework` (`rest_framework.authtoken`), `urllib3` (chamada ao reCAPTCHA; dependência transitiva), `python-decouple`

**Armazenamento**: PostgreSQL (tabelas `eauth_user`, `eauth_user_groups`, `eauth_user_user_permissions`, `eauth_auditlog`); migração `backend/eauth/migrations/0001_initial.py`

**Testes**: pytest + pytest-django + model-bakery + django-webtest (fixture `app` em `conftest.py`); não há testes específicos de `eauth` no repositório — as tarefas de `tasks.md` os acrescentam

**Plataforma Alvo**: servidor Linux (Docker, features 010/011)

**Tipo de Projeto**: serviço web (app Django dentro do monólito `backend`)

**Metas de Desempenho**: não definidas; lista de usuários com 100 itens/página, auditoria com 20 itens/página

**Restrições**: senhas mín. 6 caracteres; avatar ≤ 10 MiB; reCAPTCHA obrigatório na recuperação de senha; `distinct('model_name')` exige PostgreSQL

**Escala/Escopo**: esqueleto; dezenas a centenas de usuários; ~1.600 linhas de Python no escopo

## Verificação da Constituição

*PORTÃO (gate): passou na Fase 0 e foi reverificada após o design da Fase 1.*

| Princípio | Situação | Observação |
|-----------|----------|------------|
| I. Backend modular por apps | Atende | `backend/eauth/` com `apps.py`, `models.py`, `urls.py`, `views.py`, `views_auth.py`, `forms*.py`, `admin.py`, `services/`; app em `BACKEND_APPS` (`backend/settings/apps.py`); configuração em `backend/settings/auth.py` (módulo temático) |
| II. Configuração por ambiente | Atende | chaves de reCAPTCHA via `config(...)` com padrão vazio; nenhum segredo versionado |
| III. Paridade dev/prod Docker | Atende (N/A direto) | sem componentes específicos; funciona igual nos dois ambientes |
| IV. API REST gerada, permissões por modelo | Atende | `backend/api/views_eauth.py` gera `/api/eauth/...`; permissões `eauth.*_user` por `Crud`/globalrules; `AuditLog` sem regra de grupo (só superusuário) |
| V. Frontend Vite integrado | Atende (N/A) | telas server-rendered com templates Django; nenhum componente Vue neste app |
| VI. Tempo real e Celery | Justificado | `services/tasks.py` é apenas um stub de logger; a auditoria é síncrona (sinal Django), `eauth` não é sincronizado por WebSocket (`regex_applabels_permitidos` só `^utils`) |
| VII. Português do Brasil | Atende parcialmente | maioria dos textos com `gettext_lazy`; algumas mensagens fixas em português sem tradução (ex.: `NO_ENTRIES_MSG`, rótulos de `OPERATION_CHOICES`, mensagem de e-mail inexistente) — aceitável pois o idioma é único |
| VIII. Qualidade verificável | Justificado | não existem testes de `eauth` no estado atual; `tasks.md` inclui os testes pytest recomendados; `ruff` (E,F,I) aplicado ao código |

**Restrições adicionais**: validadores de senha padrão (mín. 6) ✔; reCAPTCHA configurável por ambiente ✔; PostgreSQL ✔.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/002-autenticacao-usuarios-auditoria/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http-endpoints.md
│   └── templates-e-configuracao.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── mixins.py                       # GoogleRecapthaMixin
├── settings/
│   ├── auth.py                     # AUTH_USER_MODEL, LOGIN_*, validadores, reCAPTCHA
│   └── email.py                    # vazio (backend padrão do Django)
├── urls.py                         # path("", include("backend.eauth.urls"))
├── api/views_eauth.py              # ApiViewSetConstrutor.build_class([apps.get_app_config('eauth')])
└── eauth/
    ├── __init__.py                 # default_app_config = 'backend.eauth.apps.EAuthConfig'
    ├── apps.py                     # EAuthConfig (name='backend.eauth', label='eauth'); ready() importa services.signals
    ├── admin.py                    # register_all_models_in_admin(__name__)
    ├── models.py                   # User, UserManager, AuditLog, AuditLogManager, groups_*_user, avatar_validation, sizeof_fmt
    ├── forms.py                    # AuditLogFilterSet, get_username, get_models
    ├── forms_auth.py               # UserCreationForm, UserChangeForm, LoginForm, BackendUserChangeForm, BackendUserAdminForm, RecuperarSenhaForm, NovaSenhaForm
    ├── views.py                    # PesquisarAuditLogView
    ├── views_auth.py               # BackendLoginView, BackendPasswordReset*View, BackendUserChangeView, UserCrud
    ├── urls.py                     # app_name = 'backend.eauth'
    ├── migrations/0001_initial.py
    ├── services/
    │   ├── __init__.py
    │   ├── signals.py              # auditlog_signal_function, auditlog_post_signal
    │   └── tasks.py                # stub (logger Celery)
    └── templatetags/               # somente __pycache__ (sem código); a tag avatar_user vive em backend/utils/templatetags/common_tags.py

_templates/eauth/
├── layouts.yaml                    # UserDetail, UserCreate
├── user_form.html                  # estende crud/form.html; JS do botão Renovar token
└── user/
    ├── login.html
    ├── login_portlet.html
    ├── avatar.html
    ├── nova_senha_form.html
    ├── recuperar_senha_email.html          # corpo do e-mail
    ├── recuperar_senha_email_form.html     # formulário (carrega api.js do reCAPTCHA)
    ├── recupera_senha_email_enviado.html
    └── recuperar_senha_completo.html

conftest.py                         # fixture app (usa admin_user.username)
backend/tests.py                    # teste genérico de default_app_config
```

**Decisão de Estrutura**: app Django único (`backend/eauth`) seguindo o padrão do projeto (Princípio I). Formulários e views de autenticação ficam em arquivos `*_auth.py` separados dos de auditoria (`forms.py`/`views.py`). Templates ficam em `_templates/eauth/` (diretório global de templates, `settings/frontend.py`), não em `backend/eauth/templates/`.

## Rastreamento de Complexidade

Sem violações dos princípios. As dívidas técnicas observadas (auditoria inoperante, templates ausentes, enumeração de usuários, etc.) estão em [research.md](./research.md); a reconstrução fiel as **replica**, com recomendação de correção registrada.

## Detalhamento de Implementação

### 1. Configuração (`backend/settings/auth.py`)

```python
AUTH_USER_MODEL = "eauth.User"
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/?next="
LOGOUT_REDIRECT_URL = "/"
str_pv = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [MinimumLengthValidator(min_length=6), UserAttributeSimilarityValidator, CommonPasswordValidator, NumericPasswordValidator]
GOOGLE_RECAPTCHA_SITE_KEY = config("GOOGLE_RECAPTCHA_SITE_KEY", cast=str, default="")
GOOGLE_RECAPTCHA_SECRET_KEY = config("GOOGLE_RECAPTCHA_SECRET_KEY", cast=str, default="")
```

- `backend/settings/project.py` faz `from .auth import *`. `backend/settings/apps.py`: `BACKEND_APPS = ["backend.eauth", "backend.utils"]`; `INSTALLED_APPS = DJANGO_CORE_APPS + DJANGO_THIRD_PARTY_APPS + BACKEND_APPS + ["backend.api", "backend.globalrules"]`. Dependências de terceiros necessárias em `INSTALLED_APPS`: `image_cropping`, `easy_thumbnails`, `crispy_forms`, `crispy_bootstrap5`, `django_filters`, `rest_framework.authtoken`.
- Middlewares relevantes (`backend/settings/middleware.py`): `SessionMiddleware`, `CsrfViewMiddleware`, `AuthenticationMiddleware`, `MessageMiddleware`, `LocaleMiddleware`. Context processor `django.contrib.auth.context_processors.auth` fornece `user`/`perms` aos templates.
- `settings/email.py` vazio ⇒ `EMAIL_BACKEND` padrão (SMTP `localhost:25`). Variáveis `.env`: `GOOGLE_RECAPTCHA_SITE_KEY`, `GOOGLE_RECAPTCHA_SECRET_KEY` (nunca versionar valores reais).
- `.env` de teste/dev pode deixar as chaves vazias; nesse caso a recuperação de senha falha sempre.

### 2. App (`backend/eauth/apps.py`, `__init__.py`)

- `EAuthConfig(AppConfig)`: `default_auto_field='django.db.models.BigAutoField'`, `name='backend.eauth'`, `label='eauth'`; `ready()` chama `AppConfig.ready(self)` e `from .services import signals` (registra o receptor).
- `__init__.py`: `default_app_config = 'backend.eauth.apps.EAuthConfig'` (verificado por `backend/tests.py`).
- `admin.py`: `register_all_models_in_admin(__name__)` (de `backend/utilss.py`; deriva o app do nome do módulo).

### 3. Modelos (`backend/eauth/models.py`) — ver `data-model.md`

- `groups_remove_user(user, groups_name)` / `groups_add_user(user, groups_name)`: normalizam para lista; para cada nome não vazio, `remove` só se o usuário pertence ao grupo; `add` só se não pertence; usam `Group.objects.get_or_create(name=...)[0]`.
- `UserManager(BaseUserManager)`, `use_in_migrations = True`: `_create_user(email, password, is_staff, is_superuser, **extra)` → `ValueError('The given email must be set')` se vazio; `normalize_email`; instancia `self.model(email, is_staff, is_active=True, is_superuser, date_joined=timezone.now(), **extra)`; `set_password(password)`; `try: user.save(using=self._db) except: user = self.model.objects.get_by_natural_key(email)` (exceção engolida); retorna `user`. `create_user(email, password=None, **extra)` e `create_superuser(email, password, **extra)`.
- `sizeof_fmt(num, suffix='B')` (formato legível: `'%3.1f%s%s'`, unidades `'', Ki, Mi, Gi, Ti, Pi, Ei, Zi`, depois `Yi`) e `avatar_validation(image)`: se `image.size > 10*1024*1024` → `forms.ValidationError(_('The maximum file size is {0}').format(sizeof_fmt(max)))`.
- `User(AbstractBaseUser, SearchModelMixin, PermissionsMixin, models.Model)` (nessa ordem): `FIELDFILE_NAME = ('avatar',)`, `fields_search = ['first_name','last_name','email']`, `objects = UserManager()`, `USERNAME_FIELD = 'email'`; propriedade `username`; métodos `get_full_name` (`' '.join([first,last]).strip()`), `get_short_name` (first_name), `get_display_name` (full ou e-mail), `__str__` = `get_display_name()`, `get_absolute_url` → `('users_profile', [self.pk], {})`.
- `AuditLogManager(models.Manager)`: `use_for_related_fields = True` (atributo obsoleto); `last_action_user()` = `filter(user__isnull=False).first()`; `first_action_user()` = `.last()`; `actions_users()` = `filter(user__isnull=False)`.
- `AuditLog`: ver data-model.md; FK de usuário usa `get_settings_auth_user_model()` (`backend/utilss.py`, retorna `settings.AUTH_USER_MODEL`).

### 4. Formulários de autenticação (`backend/eauth/forms_auth.py`)

| Classe | Base | Pontos-chave |
|--------|------|--------------|
| `UserCreationForm` | `django.contrib.auth.forms.UserCreationForm` | `Meta.model = get_user_model()`, `fields=('email',)` (não usado nas views) |
| `UserChangeForm` | `BaseUserChangeForm` | `Meta.model = get_user_model()` (não usado) |
| `LoginForm` | `AuthenticationForm` | `username` CharField(label 'Username', max 254, TextInput `form-control`, `autocomplete=username`, placeholder "Digite seu Endereço de email"); `password` CharField(label 'Password', **max_length=30**, PasswordInput `form-control`, `autocomplete=current-password`, placeholder "Digite sua Senha") |
| `BackendUserChangeForm` | `ModelForm` | ver abaixo |
| `BackendUserAdminForm` | `ModelForm` | ver abaixo |
| `RecuperarSenhaForm` | `GoogleRecapthaMixin, PasswordResetForm` | ver seção 5 |
| `NovaSenhaForm` | `SetPasswordForm` | `__init__(self, user, *args, **kwargs)`; layout `Layout(to_row([('new_password1',6),('new_password2',6)]), form_actions(label='Enviar'))` com `CustomFormHelper` |

**`BackendUserChangeForm`**: campos declarados `current_password`, `new_password1`, `new_password2` (`CharField`, `max_length=50`, `strip=False`, `required=False`, `PasswordInput`); `Meta.fields = ['first_name','last_name','avatar','avatar_cropping','current_password','new_password1','new_password2']`, `widgets = {'avatar': ImageCropWidget(), 'avatar_cropping': CropWidget()}`. `__init__`: monta `to_row` com `Fieldset('Cadastro Básico')` (first_name 5, last_name 4, avatar 7, avatar_cropping 5) em 8 colunas e `Fieldset('Definição de senha')` (current_password 12; new_password1 6 + new_password2 6; `Alert` info "Após a definição e/ou alteração de senha, sua tela será redirecionada para a tela de Login para que você faça uma nova autenticação.", `dismiss=False`) em 4 colunas; `FormHelper` com `CustomFormLayout(rows)` e `include_media=False`; atualiza `attrs` do widget `avatar` com `get_attrs(self.instance.avatar, 'avatar')` e remove `class`. `save()`: se `new_password1`, `user.set_password(...)` e `super().save(commit)`. `clean()`: se há erros, retorna; se `current_password` informada: erro se `check_password` falhar ("Senha atual informada não confere com a senha armazenada") e erro se `check_password(new_password1)` ("Nova senha não pode ser igual à senha anterior"); se `new_password1 != new_password2` → `ValidationError(code='password_mismatch')` ("As senhas informadas são diferentes"); caso contrário, se ambas preenchidas, `password_validation.validate_password(new_password2, instance)`.

**`BackendUserAdminForm`**: `is_active = TypedChoiceField(label='Usuário Ativo', choices=YES_NO_CHOICES, coerce=lambda x: x == 'True')`; `new_password1/2` (max 50, `strip=False`, não obrigatórios, help "Deixe os campos em branco para não fazer alteração de senha"); `token = CharField(required=False, max_length=40, widget=TextInput(readonly), help_text='Token de acesso para o Backend')`. `Meta.fields = ['email','first_name','last_name','is_active','token','new_password1','new_password2','groups','user_permissions']`. `__init__`: `self.user_session = kwargs.pop('user_session', None)`; layout `CustomFormLayout(to_row([...]))` com colunas email 4, first_name 3, last_name 3, is_active 2, new_password1 4, new_password2 4, `FieldWithButtons('token', StrictButton('Renovar', id='renovar-token', css_class='btn-outline-primary'))` 4, groups 12, user_permissions 12; helper `CustomFormHelper`. Com `instance.pk`: `token.initial = instance.auth_token.key` se `hasattr(instance,'auth_token')`; `groups` → `CheckboxSelectMultiple` com `choices` = grupos do usuário (ordem por nome) + `Group.objects.exclude(user=instance)` por nome; `user_permissions` → `CheckboxSelectMultiple` com permissões do usuário (ordenadas por `content_type__app_label`, `content_type__model`, `codename`) + `Permission.objects.exclude(user=instance).filter(content_type__app_label__in=map(lambda x: x.lower().split('.')[-1], settings.BACKEND_APPS))` com a mesma ordenação. `save()`: define a senha se `new_password1`; retorna `super().save(commit)` (o restante é código comentado). `clean()`: mesma lógica de senhas (sem `current_password`) — não retorna `data` (aceito pelo Django).

### 5. Recuperação de senha

- `backend/mixins.py` → `GoogleRecapthaMixin`: `__init__` extrai `title_label` e `action_label` de `kwargs` (obrigatórios); monta `to_row([(Div(css_class='g-recaptcha float-right', data_sitekey=settings.GOOGLE_RECAPTCHA_SITE_KEY), 5), ('email', 7)])`; `self.helper = CustomFormHelper()` com `CustomFormLayout(Fieldset(title_label, row1), actions=form_actions(label=action_label))`; depois `super().__init__`. `clean()`: chama `super().clean()`; lê `self.data.get('g-recaptcha-response','')`; vazio → `ValidationError('Verificação do reCAPTCHA não efetuada.')`; senão `urllib3.PoolManager().request('POST', 'https://www.google.com/recaptcha/api/siteverify?secret=<SECRET>&response=<resp>')`, decodifica JSON; qualquer exceção ou `success` falso → `ValidationError('Ocorreu um erro na validação do reCAPTCHA.')`; sucesso retorna `cleaned_data`.
- `RecuperarSenhaForm.__init__`: `kwargs['title_label'] = 'Insira o e-mail cadastrado com a sua conta'`, `kwargs['action_label'] = 'Enviar'`. `clean()`: chama `super().clean()`; `existe = User.objects.filter(email=self.data['email']).exists()`; se não → `ValidationError('Não existe nenhum usuário cadastrado com este e-mail.')`; retorna `cleaned_data`. `get_users(email)`: `filter(email__iexact=email, is_active=True)` (usa `get_email_field_name()`), gerador. Possui atributo morto `teste = ''`.
- Views (`backend/eauth/views_auth.py`): `BackendPasswordResetView(PasswordResetView)` com `email_template_name = html_email_template_name = 'eauth/user/recuperar_senha_email.html'`, `template_name = 'eauth/user/recuperar_senha_email_form.html'`, `form_class = RecuperarSenhaForm`, `success_url = reverse_lazy('backend.eauth:recuperar_senha_finalizado')`, `dispatch` decorado com `csrf_protect`. `BackendPasswordResetEncaminhadoView(PasswordResetView)` com `template_name = 'eauth/user/recupera_senha_email_enviado.html'` (herda `PasswordResetView`, não `PasswordResetDoneView`). `BackendPasswordResetConfirmView(PasswordResetConfirmView)`: `form_class = NovaSenhaForm`, `template_name = 'eauth/user/nova_senha_form.html'`, `success_url = reverse_lazy('backend.eauth:password_reset_complete')`. `BackendPasswordResetCompleteView(PasswordResetCompleteView)`: `template_name = 'eauth/user/recuperar_senha_completo.html'`.
- Templates: `recuperar_senha_email_form.html` estende `crud/form.html` e acrescenta ao `{% block head_content %}{{ block.super }}` o `<script src='https://www.google.com/recaptcha/api.js' async defer>` (o bloco `head_content` não existe em `base.html`, logo o script não é emitido). `recuperar_senha_email.html` estende `base_email.html` (ausente) com texto "Você está recebendo este e-mail pois solicitou recuperação de senha..." e botão-link `https://{{ domain }}{% url 'backend.eauth:recuperar_senha_confirma' uidb64=uid token=token %}`. `recupera_senha_email_enviado.html` estende `crud/detail.html`, sobrescreve `base_content`. `recuperar_senha_completo.html` estende `crud/detail.html`, bloco `table_content` com link para `backend.eauth:login`. `nova_senha_form.html` apenas `{% extends "crud/form.html" %}`.

### 6. Login/logout e perfil

- `BackendLoginView(LoginView)`: `template_name='eauth/user/login.html'`, `authentication_form=LoginForm`. `login.html` estende `base.html`, `block main_container_class` = `container`, inclui `eauth/user/login_portlet.html`; o portlet tem `<form id="login-form" method="post" action="/login" enctype="multipart/form-data">`, `{% csrf_token %}`, alerta "Usuário e/ou Senha inválidos." quando `form.errors`, campos `form.username`/`form.password` com ícones Font Awesome (`fa-user`, `fa-key`), link `backend.eauth:recuperar_senha_email`, botão "ENTRAR" e `<input type="hidden" name="next" value="{{ next }}">`; título "Acesso ao Sdd-Start".
- Logout: `re_path(r'^logout', LogoutView.as_view(), {'next_page': '/'}, name='logout')`; o menu (`_templates/base.html`) usa `<form action="{% url 'backend.eauth:logout' %}" method="POST">` com `{% csrf_token %}`.
- `BackendUserChangeView(FormMessagesMixin, UpdateView)`: `form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_UPDATE]` (de `backend/crud/base.py`), `model = get_user_model()`, `form_class = BackendUserChangeForm`, `template_name = 'crud/form.html'`; `get_context_data` define `title = '%s <small>(%s)</small>' % (get_full_name(), email)`; `get_success_url` = `reverse_lazy('backend.eauth:backend_user_change')`; `cancel_url()` devolve `'/'`; `get_object` devolve `self.request.user`. Rota protegida por `login_required(...)` na `urls.py`.

### 7. CRUD de usuários (`UserCrud` em `views_auth.py`)

`UserCrud(Crud)`, `model = get_user_model()`. `BaseMixin(Crud.BaseMixin)`: `list_field_names = ['usuario','is_active']`, `get_context_object_name` → `None`. `CreateView(Crud.CreateView)`: `layout_key='UserCreate'`, `form_class=BackendUserAdminForm`. `UpdateView(Crud.UpdateView)`: `form_class=BackendUserAdminForm`, `layout_key=''`, `get_form_kwargs` acrescenta `user_session=request.user`. `DetailView(Crud.DetailView)`: `layout_key='UserDetail'` e hooks `hook_first_name`, `hook_last_name`, `hook_email`, `hook_is_active`, `hook_groups`, `hook_user_permissions` que devolvem `(rótulo, field_display)` com rótulos "Nome", "Sobrenome", "Email", "Ativo", "Grupos/Perfis", "Permissões"; `dispatch` apenas delega. `ListView(Crud.ListView)`: `form_search_class = ListWithSearchForm` (`backend/crud/forms.py`), `ordered_list = None`, `paginate_by = 100`, `hook_header_usuario` → `'Usuario'`, `hook_usuario` → `('{nome}<br><small>{email}</small>', args[2])`, `get_queryset` → `order_by('-is_superuser','-is_active','first_name')`.
- `_templates/eauth/layouts.yaml` (começa com `{% load i18n %}`): `UserDetail` → fieldset `{% trans 'Usuário' %}` com linhas `email:8 is_active`, `first_name last_name`, `groups`, `user_permissions`; `UserCreate` → `email first_name last_name is_active` e `new_password1 new_password2`. O layout é lido por `read_layout_from_yaml("eauth/layouts.yaml", layout_key)` (feature 004).
- `_templates/eauth/user_form.html` (nome derivado do modelo: `<app>/<model>_form.html`): estende `crud/form.html` e, em `{% block extra_js %}`, no `DOMContentLoaded`, lê o `csrfmiddlewaretoken`, e no clique de `#renovar-token` faz `fetch("{% url 'backend.api:recria_token' object.id %}", {method:'POST', headers:{'X-CSRFToken':..., 'Content-Type':'application/json'}})`, e define `#id_token` com `data.token`.

### 8. URLs (`backend/eauth/urls.py`) — `app_name = EAuthConfig.name` (`'backend.eauth'`)

Ordem exata (importa): (1) `^user/recuperar-senha/email` `recuperar_senha_email`; (2) `^user/recuperar-senha/finalizado` `recuperar_senha_finalizado`; (3) `^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)` `recuperar_senha_confirma`; (4) `^user/recuperar-senha/completo` `password_reset_complete`; (5) `^user/edit` `login_required(BackendUserChangeView.as_view())` `backend_user_change`; (6) `^login` `login`; (7) `^logout` `LogoutView` com kwargs `{'next_page': '/'}`; (8) `^admin/auditlog` `pesquisar_auditlog`; (9) `^admin/user/` → `include(UserCrud.get_urls())` (nomes `user_list`, `user_create`, `user_view`, `user_update`, `user_delete`; regex `^$`, `^create$`, `^(?P<pk>\d+)$`, `^(?P<pk>\d+)/edit$`, `^(?P<pk>\d+)/delete$`). Todas via `re_path`. Em `backend/urls.py` a inclusão é `path("", include("backend.eauth.urls"))`, depois de `backend.api.urls` e antes de `backend.utils.urls` e do `index`.

### 9. Auditoria

- `backend/eauth/services/signals.py`:
  1. `@receiver([post_save, post_delete], dispatch_uid='auditlog_post_signal') auditlog_post_signal(sender, **kwargs)` registra `logger.debug` de início/fim e chama `auditlog_signal_function`.
  2. `auditlog_signal_function(sender, **kwargs)`: `try: app_name = sender._meta.app_config.name[:10]; if app_name not in ('backend',): return; except: return` (⇒ sempre retorna, ver research.md). Em seguida: se `instance._meta.model in (AuditLog,)` retorna; percorre `inspect.stack()` — a cada frame `stack = str(frame_info)`; se `frame.function == 'migrate'` retorna; lê `request` de `f_locals`; `try: if r.user._meta.label == settings.AUTH_USER_MODEL: u = r.user; if u.is_anonymous: return; break` `except: pass`.
  3. `operation = kwargs.get('created', 'D')`; se diferente de `'D'`, `'C' if created else 'U'`.
  4. Monta `AuditLog(user=u, email=u.email if u else '', operation, obj=json.loads(serializers.serialize('json',(instance,))), content_object=instance se operation != 'D' senão None, obj_id=instance.id, model_name=instance._meta.model_name, app_name=instance._meta.app_label)`, define `al.obj[0]['stack'] = stack` e `save()`; qualquer exceção → `logger.error('Error saving auditing log object')` + `logger.error(e)`.
- `backend/utils/services/signals_syncrefresh.py` ignora `auditlog` na sincronização em tempo real (feature 006).
- `backend/eauth/forms.py`: `get_username()` → `[(pk, f'{full_name} ({email})') ...]` com `except: []`; `get_models()` → `[(m, m) for m in AuditLog.objects.distinct('model_name').order_by('model_name').values_list('model_name', flat=True)]`. `AuditLogFilterSet(django_filters.FilterSet)`: `OPERATION_CHOICES` (U/C/D/P); filtros `user` (`ChoiceFilter(choices=get_username())`, avaliado na importação), `busca` (`CharFilter(method='filter_busca', label='Filtrar Campo')`), `operation`, `model_name` (`choices=get_models`, callable), `timestamp` (`DateRangeFilter(label='Período')`); `Meta.model = AuditLog`, `fields = ['user','operation','model_name','timestamp','busca']`. `filter_busca(qs, field, value)`: `value.split(',')` → pares `k=v` (strip); fase 1 exata (`id` → `object_id`; inteiros convertidos com `int()`; filtro `obj__0__fields__<k>`); se vazio, fase 2: strings com `obj__0__fields__<k>__icontains`. `__init__`: `CustomFormHelper` com `form_method='GET'`, layout `Fieldset('Filtros', to_row([('user',2),('operation',2),('model_name',4),('busca',2),('timestamp',2)]), form_actions(label='Aplicar Filtro'))`.
- `backend/eauth/views.py` → `PesquisarAuditLogView(PermissionRequiredMixin, FilterView)`: `model = AuditLog`, `filterset_class = AuditLogFilterSet`, `paginate_by = 20`, `permission_required = ('eauth.list_auditlog',)`; `get_filterset_kwargs` devolve `{'data': request.GET or None, 'queryset': get_queryset().order_by('-id')}`; `get()` força `timestamp='week'` quando ausente (copia `request.GET`), chama `super().get(request)`, monta `filter_url` (`'&' + QUERY_STRING`, vazio se começar com `&page`), chama `get_context_data(filter=..., object_list=..., filter_url=..., numero_res=len(resultados))`, define `show_results = show_results_filter_set(GET)`; `get_context_data` remove `page` da query, calcula `filter_url`, `show_results`, `page_range = make_pagination(page_obj.number, paginator.num_pages)`, `NO_ENTRIES_MSG = 'Nenhum registro de log encontrado!'` e `title = 'Pesquisar Logs de Auditoria'`. Template esperado (inexistente): `eauth/auditlog_filter.html`.

### 10. Integrações externas ao app

- `backend/api/views_eauth.py`: `ApiViewSetConstrutor.build_class([apps.get_app_config('eauth')])`; carregado por `BackendApiViewSetConstrutor.import_modules([...])` em `backend/api/views.py`.
- `recria_token` (`backend/api/views.py`, rota `^api/recriar-token/(?P<pk>\d*)$`, nome `recria_token`, namespace `backend.api`): `IsAdminUser`; apaga e recria o `Token` do `user_id` informado.
- Tag `avatar_user(user_render=None, css_class="avatar")` em `backend/utils/templatetags/common_tags.py` renderiza `eauth/user/avatar.html`: se há avatar, `<img class=... src="{% cropped_thumbnail user_render 'avatar_cropping' %}">`, senão `<svg class=... ><use href="#svg-perfil">` (feature 009).
- `_templates/base.html`: links `backend.eauth:backend_user_change`, `backend.eauth:logout`, `backend.eauth:login`; `_templates/menus/menu_administracao.yaml`: itens `backend.eauth:user_list` e `backend.eauth:pesquisar_auditlog` sob a permissão `menu_administracao`.
- `backend/globalrules/map_rules.py`: o grupo `GROUP_ADM_ADMIN` recebe `RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE` + `menu_administracao` sobre `get_user_model()` (feature 003).

### 11. Migração (`backend/eauth/migrations/0001_initial.py`)

`initial = True`; dependências `("auth", "0012_alter_user_first_name_max_length")` e `("contenttypes", "0002_remove_content_type_name")`; operações `CreateModel('User', ...)` (com `managers=[('objects', backend.eauth.models.UserManager())]`, `options` incluindo `permissions` `menu_1`/`orcamento_1`) e `CreateModel('AuditLog', ...)`. Referencia `backend.eauth.models.avatar_validation` (função DEVE permanecer importável em `models.py`). Gerar com `python manage.py makemigrations eauth`.
