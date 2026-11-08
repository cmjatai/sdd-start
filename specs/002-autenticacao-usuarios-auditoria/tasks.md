---

description: "Lista de tarefas para reconstruir a funcionalidade 002 — Autenticação, Usuários e Auditoria (app eauth)"
---

# Tarefas: Autenticação, Usuários e Auditoria (app `eauth`)

**Entrada**: Documentos de design em `/specs/002-autenticacao-usuarios-auditoria/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de usuário), research.md, data-model.md, contracts/ — e a funcionalidade `001-fundacao-projeto-django` já construída. Itens que dependem de `003` (regras/permissões), `004` (CRUD genérico), `005` (API) e `009` (avatar) só precisam existir para a execução completa das telas; as tarefas abaixo indicam onde.

**Testes**: Incluídos (Constituição VIII). Os testes de `eauth` não existem no repositório e são parte do roteiro.

**Organização**: Tarefas agrupadas por história de usuário. **Todas as tarefas estão desmarcadas** (roteiro de reconstrução). Onde o estado atual contém um defeito conhecido (ver `research.md`), a tarefa manda **replicar** o comportamento; as correções recomendadas são opcionais (Fase de Acabamento).

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US6 conforme `spec.md`
- Caminhos relativos à raiz do repositório

## Convenções de Caminhos

Aplicação web Django: código em `backend/eauth/`, templates em `_templates/eauth/`, configuração em `backend/settings/`, testes em `backend/eauth/test_*.py` (padrão `**/test_*.py` do `pyproject.toml`).

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: esqueleto do app e dependências.

- [ ] T001 Confirmar/adicionar em `pyproject.toml` as dependências `django>=6,<7`, `django-crispy-forms`/`crispy-bootstrap5`, `django-filter`, `django-braces`, `django-image-cropping`, `easy-thumbnails`, `djangorestframework`, `python-decouple` e rodar `poetry install` (plan.md "Contexto Técnico")
- [ ] T002 Criar o pacote `backend/eauth/` com `__init__.py` contendo `default_app_config = 'backend.eauth.apps.EAuthConfig'` e a pasta `backend/eauth/services/` com `__init__.py` vazio
- [ ] T003 [P] Criar `backend/eauth/apps.py` com `EAuthConfig` (`name='backend.eauth'`, `label='eauth'`, `default_auto_field=BigAutoField`, `ready()` que chama `AppConfig.ready(self)` e importa `.services.signals`) (plan.md §2)
- [ ] T004 [P] Criar `backend/eauth/admin.py` chamando `register_all_models_in_admin(__name__)` de `backend/utilss.py`
- [ ] T005 [P] Criar a pasta `_templates/eauth/user/` (templates globais) e confirmar `TEMPLATES[0]['DIRS']` apontando para `_templates` em `backend/settings/frontend.py`
- [ ] T006 Registrar `"backend.eauth"` em `BACKEND_APPS` e garantir em `INSTALLED_APPS` os apps `image_cropping`, `easy_thumbnails`, `crispy_forms`, `crispy_bootstrap5`, `django_filters`, `rest_framework.authtoken` em `backend/settings/apps.py`

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: configuração de autenticação, modelos e migração — bloqueiam todas as histórias.

**⚠️ CRÍTICO**: nenhuma história pode começar antes desta fase.

- [ ] T007 Criar `backend/settings/auth.py` com `AUTH_USER_MODEL="eauth.User"`, `LOGIN_REDIRECT_URL="/"`, `LOGIN_URL="/login/?next="`, `LOGOUT_REDIRECT_URL="/"`, `AUTH_PASSWORD_VALIDATORS` (mínimo 6 + 3 validadores padrão) e `GOOGLE_RECAPTCHA_SITE_KEY`/`GOOGLE_RECAPTCHA_SECRET_KEY` por `config(..., cast=str, default="")`; importar em `backend/settings/project.py` com `from .auth import *` (plan.md §1)
- [ ] T008 Criar `backend/settings/email.py` vazio e importá-lo em `backend/settings/project.py` (`from .email import *`)
- [ ] T009 Em `backend/eauth/models.py` implementar `groups_remove_user`, `groups_add_user`, `sizeof_fmt`, `avatar_validation` e `UserManager` (incluindo o `try/except` que devolve o usuário existente) exatamente como em plan.md §3
- [ ] T010 Em `backend/eauth/models.py` implementar `User(AbstractBaseUser, SearchModelMixin, PermissionsMixin, models.Model)` com todos os campos, `Meta` (`permissions = PERMS_FOR_USERS` importado de `backend.globalrules`), propriedade `username`, `get_full_name`, `get_short_name`, `get_display_name`, `__str__` e `get_absolute_url` (tupla) (data-model.md)
- [ ] T011 Em `backend/eauth/models.py` implementar `AuditLogManager` e `AuditLog` com todos os campos, `OPERATION_CHOICES`, `Meta` e `__str__` (data-model.md)
- [ ] T012 Gerar a migração `backend/eauth/migrations/0001_initial.py` (`python manage.py makemigrations eauth`) e conferir dependências `auth.0012` e `contenttypes.0002` e `managers=[('objects', UserManager())]`
- [ ] T013 Criar `backend/eauth/services/tasks.py` (stub com `get_task_logger`) e `backend/eauth/services/signals.py` vazio de lógica por ora, apenas com `logger` (será completado na US6)
- [ ] T014 Incluir `path("", include("backend.eauth.urls"))` em `backend/urls.py` (após `backend.api.urls`, antes de `backend.utils.urls` e do `index`) e criar `backend/eauth/urls.py` com `app_name = EAuthConfig.name` e `urlpatterns = []` provisório
- [ ] T015 Rodar `python manage.py migrate` e `python manage.py check`; confirmar que `createsuperuser` pede e-mail e senha

**Checkpoint**: app carrega, tabelas criadas, `User` utilizável.

---

## Fase 3: História de Usuário 2 - Usuário por e-mail e superusuário (Prioridade: P1) 🎯 MVP

**Objetivo**: manager/modelo corretos e `createsuperuser` funcional (a base de todo login).

**Teste Independente**: `create_user`/`create_superuser` e `createsuperuser` produzem usuários válidos com e-mail como identificador.

### Testes da História de Usuário 2

- [ ] T016 [P] [US2] Criar `backend/eauth/test_models_user.py` com `test_create_user_and_superuser` (flags, e-mail normalizado `A@EXAMPLE.COM`→`A@example.com`, `ValueError` sem e-mail, senha com hash, `str(user)`, `username == email`)
- [ ] T017 [P] [US2] Em `backend/eauth/test_models_user.py` adicionar `test_user_manager_swallows_duplicate` (segundo `create_user` com o mesmo e-mail devolve o usuário existente), `test_groups_add_remove_user` e `test_avatar_validation_limit`/`sizeof_fmt`
- [ ] T018 [P] [US2] Em `backend/eauth/test_models_user.py` adicionar teste de ordenação (`-is_superuser`, `first_name`, `last_name`) e de `search` preenchido por `SearchModelMixin`

### Implementação da História de Usuário 2

- [ ] T019 [US2] Validar manualmente `python manage.py createsuperuser` (e-mail + senha) e o login em `/system/` (Django Admin) — registrar resultado em `quickstart.md` se divergir
- [ ] T020 [US2] Garantir a fixture `app` em `conftest.py` usando `admin_user.username` (e-mail) e que `pytest backend/eauth/test_models_user.py` passa

**Checkpoint**: US2 concluída e testada.

---

## Fase 4: História de Usuário 1 - Login e logout (Prioridade: P1)

**Objetivo**: telas de login/logout por e-mail e senha.

**Teste Independente**: login válido redireciona para `/`; inválido mostra mensagem genérica; logout por POST.

### Testes da História de Usuário 1

- [ ] T021 [P] [US1] Criar `backend/eauth/test_login.py` com `test_login_ok_redirects`, `test_login_invalid_generic_message` ("Usuário e/ou Senha inválidos."), `test_login_password_over_30_chars_rejected` e `test_login_next_param`
- [ ] T022 [P] [US1] Em `backend/eauth/test_login.py` adicionar `test_logout_requires_post` (GET → 405; POST → redireciona a `/` e encerra a sessão) e `test_login_url_redirect` (anônimo em rota protegida → `/login/?next=...`)

### Implementação da História de Usuário 1

- [ ] T023 [US1] Em `backend/eauth/forms_auth.py` criar `LoginForm(AuthenticationForm)` com `username` (max 254) e `password` (**max_length=30**), widgets `form-control`, placeholders e `autocomplete` (plan.md §4)
- [ ] T024 [US1] Em `backend/eauth/views_auth.py` criar `BackendLoginView(LoginView)` (`template_name='eauth/user/login.html'`, `authentication_form=LoginForm`)
- [ ] T025 [P] [US1] Criar `_templates/eauth/user/login.html` (estende `base.html`, `main_container_class`=`container`, inclui `login_portlet.html`) e `_templates/eauth/user/login_portlet.html` (formulário `POST /login`, `csrf_token`, alerta de erro genérico, ícones, link `backend.eauth:recuperar_senha_email`, botão "ENTRAR", campo `next`)
- [ ] T026 [US1] Em `backend/eauth/urls.py` declarar as rotas `^login` (`login`) e `^logout` (`LogoutView.as_view()` com kwargs `{'next_page': '/'}`, nome `logout`) na ordem do plan.md §8
- [ ] T027 [P] [US1] Garantir em `_templates/base.html` o link de login (anônimo) e o menu do usuário com formulário `POST` para `backend.eauth:logout` e link `backend.eauth:backend_user_change` (feature 001/007)

**Checkpoint**: US1 e US2 funcionam; login em `/login/`.

---

## Fase 5: História de Usuário 3 - Administração de usuários (Prioridade: P2)

**Objetivo**: CRUD `/admin/user/` com formulário administrativo.

**Teste Independente**: superusuário cria, lista, edita (grupos) e visualiza usuário.

### Testes da História de Usuário 3

- [ ] T028 [P] [US3] Criar `backend/eauth/test_user_crud.py` com `test_user_list_superuser_ok` e `test_user_crud_denied_without_permission` (usuário comum sem `eauth.list_user`)
- [ ] T029 [P] [US3] Em `backend/eauth/test_user_crud.py` adicionar `test_create_user_with_password` (senha com hash; senhas diferentes → "As senhas informadas são diferentes") e `test_update_without_password_keeps_hash`
- [ ] T030 [P] [US3] Em `backend/eauth/test_user_crud.py` adicionar `test_admin_form_group_and_permission_choices` (atribuídos primeiro; permissões restritas a `BACKEND_APPS`) e `test_token_initial_from_auth_token`

### Implementação da História de Usuário 3

- [ ] T031 [US3] Em `backend/eauth/forms_auth.py` criar `BackendUserAdminForm` (campos declarados, `Meta.fields`, layout com `FieldWithButtons('token', StrictButton('Renovar', id='renovar-token'))`, escolhas de grupos/permissões, `save` e `clean`) conforme plan.md §4 — manter o comportamento (sem reimplementar o código comentado)
- [ ] T032 [P] [US3] Em `backend/eauth/forms_auth.py` criar `UserCreationForm` e `UserChangeForm` (subclasses do Django, não usadas pelas views)
- [ ] T033 [US3] Em `backend/eauth/views_auth.py` criar `UserCrud(Crud)` com `BaseMixin`, `CreateView`, `UpdateView` (com `user_session`), `DetailView` (hooks de rótulos), `ListView` (`ListWithSearchForm`, `paginate_by=100`, `hook_usuario`, `get_queryset` ordenado) conforme plan.md §7
- [ ] T034 [P] [US3] Criar `_templates/eauth/layouts.yaml` com `UserDetail` e `UserCreate` (contracts/templates-e-configuracao.md)
- [ ] T035 [P] [US3] Criar `_templates/eauth/user_form.html` (estende `crud/form.html`, `extra_js` com `fetch` para `backend.api:recria_token` e preenchimento de `#id_token`)
- [ ] T036 [US3] Em `backend/eauth/urls.py` acrescentar `re_path(r'^admin/user/', include(views_auth.UserCrud.get_urls()))` (por último, após `admin/auditlog`) e conferir os nomes `user_list|create|view|update|delete`
- [ ] T037 [P] [US3] Criar `backend/api/views_eauth.py` (`ApiViewSetConstrutor.build_class([apps.get_app_config('eauth')])`) e registrá-lo em `import_modules` de `backend/api/views.py` (feature 005) — necessário para `recria_token`/API de usuários
- [ ] T038 [US3] Adicionar em `_templates/menus/menu_administracao.yaml` os itens `backend.eauth:user_list` e `backend.eauth:pesquisar_auditlog` sob `check_permission: menu_administracao` (feature 004)
- [ ] T039 [US3] Garantir em `backend/globalrules/map_rules.py` a regra do grupo `GROUP_ADM_ADMIN` para `get_user_model()` com `RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE` + `menu_administracao` (feature 003)

**Checkpoint**: gestão de usuários operacional.

---

## Fase 6: História de Usuário 4 - Edição do próprio perfil (Prioridade: P2)

**Objetivo**: `/user/edit` com troca de nome/avatar/senha.

**Teste Independente**: autenticado altera o nome e a senha com as regras de validação.

### Testes da História de Usuário 4

- [ ] T040 [P] [US4] Criar `backend/eauth/test_profile.py` com `test_profile_requires_login`, `test_profile_updates_names` e `test_profile_edits_only_request_user`
- [ ] T041 [P] [US4] Em `backend/eauth/test_profile.py` adicionar `test_change_password_ok`, `test_current_password_wrong`, `test_new_equals_current`, `test_password_mismatch`, `test_password_validators_applied` e `test_new_password_without_current_is_accepted` (documenta research.md #17)

### Implementação da História de Usuário 4

- [ ] T042 [US4] Em `backend/eauth/forms_auth.py` criar `BackendUserChangeForm` (campos virtuais de senha, widgets `ImageCropWidget`/`CropWidget`, layout 8/4 colunas com `Alert`, `save` e `clean`) conforme plan.md §4
- [ ] T043 [US4] Em `backend/eauth/views_auth.py` criar `BackendUserChangeView(FormMessagesMixin, UpdateView)` (`get_object` = `request.user`, título, `get_success_url`, `cancel_url`)
- [ ] T044 [US4] Em `backend/eauth/urls.py` acrescentar `re_path(r'^user/edit', login_required(BackendUserChangeView.as_view()), name='backend_user_change')`
- [ ] T045 [P] [US4] Criar `_templates/eauth/user/avatar.html` e garantir a tag `avatar_user` em `backend/utils/templatetags/common_tags.py` (referência: feature 009)

**Checkpoint**: perfil funcional.

---

## Fase 7: História de Usuário 5 - Recuperação de senha com reCAPTCHA (Prioridade: P2)

**Objetivo**: fluxo de recuperação por e-mail.

**Teste Independente**: com `urllib3` simulado, o formulário valida reCAPTCHA e e-mail; as views respondem.

### Testes da História de Usuário 5

- [ ] T046 [P] [US5] Criar `backend/eauth/test_password_reset.py` com `test_recaptcha_missing`, `test_recaptcha_failure`, `test_email_not_found_message` (mensagem atual) e `test_get_users_only_active_iexact` (usando `unittest.mock` em `urllib3.PoolManager`)
- [ ] T047 [P] [US5] Em `backend/eauth/test_password_reset.py` adicionar `test_reset_email_sent_with_locmem_backend` (template de e-mail de teste via `override_settings`/`TEMPLATES`), `test_confirm_view_sets_password` e `test_url_names_and_order` (`completo` não casa `confirma`)

### Implementação da História de Usuário 5

- [ ] T048 [US5] Criar `backend/mixins.py` com `GoogleRecapthaMixin` (`__init__` com `title_label`/`action_label`, layout crispy com `div.g-recaptcha`, `clean` com validação em `https://www.google.com/recaptcha/api/siteverify`) conforme plan.md §5
- [ ] T049 [US5] Em `backend/eauth/forms_auth.py` criar `RecuperarSenhaForm(GoogleRecapthaMixin, PasswordResetForm)` (textos de título/ação, `clean` com a checagem de e-mail inexistente, `get_users`) e `NovaSenhaForm(SetPasswordForm)`
- [ ] T050 [US5] Em `backend/eauth/views_auth.py` criar `BackendPasswordResetView` (com `csrf_protect`), `BackendPasswordResetEncaminhadoView(PasswordResetView)`, `BackendPasswordResetConfirmView` e `BackendPasswordResetCompleteView` com os templates e `success_url` do plan.md §5
- [ ] T051 [P] [US5] Criar os templates `_templates/eauth/user/recuperar_senha_email_form.html`, `recupera_senha_email_enviado.html`, `nova_senha_form.html`, `recuperar_senha_completo.html` e `recuperar_senha_email.html` (estendendo `base_email.html`, que permanece ausente — replicar)
- [ ] T052 [US5] Em `backend/eauth/urls.py` declarar, **nesta ordem**, as rotas `recuperar_senha_email`, `recuperar_senha_finalizado`, `recuperar_senha_confirma`, `password_reset_complete` antes de `user/edit`, `login` e `logout`
- [ ] T053 [US5] Documentar em `backend/.env` (apenas nomes, sem valores reais) `GOOGLE_RECAPTCHA_SITE_KEY` e `GOOGLE_RECAPTCHA_SECRET_KEY`

**Checkpoint**: formulários/views de recuperação prontos (envio real depende do ambiente — ver research.md #13/#14).

---

## Fase 8: História de Usuário 6 - Auditoria (Prioridade: P3)

**Objetivo**: modelo, sinal e tela de consulta de auditoria.

**Teste Independente**: o sinal retorna cedo (estado atual); o `AuditLog` é gravável; o filtro de busca funciona.

### Testes da História de Usuário 6

- [ ] T054 [P] [US6] Criar `backend/eauth/test_auditlog.py` com `test_auditlog_signal_is_noop` (alterar `User` não cria `AuditLog`), `test_auditlog_model_and_manager` (`last_action_user`, `first_action_user`, `actions_users`, `__str__`) e `test_auditlog_signal_with_patched_filter` (com o filtro `name[:10]` contornado por patch, grava `C`/`U`/`D` e ignora `AuditLog`)
- [ ] T055 [P] [US6] Em `backend/eauth/test_auditlog.py` adicionar `test_filter_busca_id_and_fields`, `test_filter_busca_icontains_fallback` e `test_auditlog_view_requires_permission` (sem `eauth.list_auditlog` → negado; documentar `TemplateDoesNotExist` para superusuário)

### Implementação da História de Usuário 6

- [ ] T056 [US6] Em `backend/eauth/services/signals.py` implementar `auditlog_signal_function` e `auditlog_post_signal` exatamente como em plan.md §9 (filtro `name[:10] not in ('backend',)`, ignorar `AuditLog`, varrer `inspect.stack()`, parar em `migrate`, serializar, gravar, logar erros)
- [ ] T057 [US6] Em `backend/eauth/forms.py` implementar `get_username`, `get_models` e `AuditLogFilterSet` (filtros, `filter_busca`, helper crispy GET com `Fieldset('Filtros')` e `form_actions(label='Aplicar Filtro')`) conforme plan.md §9
- [ ] T058 [US6] Em `backend/eauth/views.py` implementar `PesquisarAuditLogView` (permissão `eauth.list_auditlog`, `paginate_by=20`, `get`/`get_context_data` com `timestamp='week'` padrão)
- [ ] T059 [US6] Em `backend/eauth/urls.py` acrescentar `re_path(r'^admin/auditlog', views.PesquisarAuditLogView.as_view(), name='pesquisar_auditlog')` antes de `^admin/user/`
- [ ] T060 [US6] Em `backend/utils/services/signals_syncrefresh.py` manter `"auditlog"` na lista de modelos ignorados (feature 006) e conferir que `EAuthConfig.ready()` registra o receptor

**Checkpoint**: auditoria presente no código, com o estado atual (inoperante) preservado e testado.

---

## Fase 9: Acabamento e Preocupações Transversais

- [ ] T061 [P] Rodar `ruff check backend/eauth backend/mixins.py backend/settings/auth.py` e `ruff format --check` conforme a configuração do projeto; corrigir somente avisos `E`, `F`, `I` introduzidos
- [ ] T062 [P] Rodar `pytest backend/eauth backend/tests.py` e confirmar que todos passam com `--reuse-db`
- [ ] T063 Revisar que os 32 itens de `research.md` estão refletidos como comportamento replicado (nenhuma correção silenciosa) e que `quickstart.md` continua verdadeiro
- [ ] T064 [P] (Opcional, evolução) Aplicar as correções recomendadas de maior risco em PR separado atualizando `spec.md`: filtro do sinal (#1), template `eauth/auditlog_filter.html` (#6), `PasswordResetDoneView` (#12), `base_email.html` e bloco do reCAPTCHA (#13/#14), remoção do `try/except` do `_create_user` (#15)
- [ ] T065 [P] Atualizar `README.md` (seção de endereços: `/login/`, `/admin/user/`, `/admin/auditlog`) se houver divergência

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)** → **Fundacional (Fase 2)** → histórias.
- Fase 2 bloqueia todas as histórias (modelos, `AUTH_USER_MODEL`, migração).
- **Acabamento (Fase 9)** depende das histórias desejadas.

### Dependências entre Histórias de Usuário

- **US2** (modelo/manager) antes de tudo que autentica (US1, US3, US4).
- **US1** independente após US2; fornece `LoginForm` e rotas `login`/`logout`.
- **US3** depende de `Crud` (004), `globalrules` (003) e `api` (005) para execução completa; US4 depende de US1 (login) e do avatar (009).
- **US5** depende de US1 (link de volta ao login) e das rotas da Fase 7 antes de `user/edit`/`login` (ordem de `urls.py`).
- **US6** independente das demais; depende apenas do modelo `AuditLog` (Fase 2).

### Dentro de Cada História

- Testes (T016–T018, T021–T022, …) escritos primeiro e falhando; depois formulários → views → templates → URLs.
- `backend/eauth/urls.py` é editado por várias histórias: manter a **ordem final** do plan.md §8 (T052 → T044/T026 → T059 → T036).

### Oportunidades de Paralelismo

- Tarefas marcadas `[P]` (arquivos distintos) rodam em paralelo; as quatro suítes de teste (US1, US3, US4, US5/US6) podem ser escritas em paralelo após a Fase 2.

## Exemplo de Paralelismo: História de Usuário 5

```text
T046 test_password_reset.py (reCAPTCHA/e-mail)   T051 templates de recuperação
T047 test_password_reset.py (e-mail/URLs)        T053 variáveis .env
```

## Estratégia de Implementação

### MVP Primeiro (US2 + US1)

1. Fases 1–2 (app, modelos, migração, settings).
2. US2 (manager/superusuário) e US1 (login/logout) — validar `/login/` e `/system/`.
3. **Parar e validar** antes de prosseguir.

### Entrega Incremental

1. MVP → US3 (CRUD) → US4 (perfil) → US5 (recuperação) → US6 (auditoria) → Acabamento.
2. Cada história é testável isoladamente.

### Estratégia de Equipe em Paralelo

- Dev A: US1/US4 (login/perfil); Dev B: US3 (CRUD); Dev C: US5/US6 (recuperação/auditoria), após a Fase 2.

## Notas

- Tarefas `[P]` = arquivos diferentes, sem dependências.
- Preservar os comportamentos listados em `research.md` (fidelidade); correções só na T064.
- Commits em português descritivo, após cada tarefa ou grupo lógico.
