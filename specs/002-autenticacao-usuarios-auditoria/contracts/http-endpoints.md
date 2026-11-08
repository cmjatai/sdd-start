# Contrato HTTP: rotas do app `eauth`

Namespace de URLs: `backend.eauth` (`app_name = EAuthConfig.name`). Todas as rotas são definidas por `re_path` em `backend/eauth/urls.py` e incluídas na raiz (`path("", include("backend.eauth.urls"))` em `backend/urls.py`). A ordem das rotas abaixo é a ordem real de avaliação.

## Rotas de autenticação e perfil

| # | Nome (`backend.eauth:<nome>`) | Regex | Métodos | Acesso | View / template |
|---|------------------------------|-------|---------|--------|-----------------|
| 1 | `recuperar_senha_email` | `^user/recuperar-senha/email` | GET, POST | público (CSRF) | `BackendPasswordResetView` · `eauth/user/recuperar_senha_email_form.html` |
| 2 | `recuperar_senha_finalizado` | `^user/recuperar-senha/finalizado` | GET (e POST herdado — ver research.md #12) | público | `BackendPasswordResetEncaminhadoView` · `eauth/user/recupera_senha_email_enviado.html` |
| 3 | `recuperar_senha_confirma` | `^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)` | GET, POST | quem possui o link válido | `BackendPasswordResetConfirmView` · `eauth/user/nova_senha_form.html` |
| 4 | `password_reset_complete` | `^user/recuperar-senha/completo` | GET | público | `BackendPasswordResetCompleteView` · `eauth/user/recuperar_senha_completo.html` |
| 5 | `backend_user_change` | `^user/edit` | GET, POST | autenticado (`login_required`) | `BackendUserChangeView` · `crud/form.html` |
| 6 | `login` | `^login` | GET, POST | público | `BackendLoginView` · `eauth/user/login.html` |
| 7 | `logout` | `^logout` | POST (GET retorna 405 no Django ≥ 5) | qualquer | `LogoutView` (kwargs `{'next_page': '/'}`; redireciona para `LOGOUT_REDIRECT_URL = "/"`) |

### `POST /login`
- Campos: `username` (e-mail, máx. 254), `password` (máx. 30), `csrfmiddlewaretoken`, `next` (oculto).
- Sucesso: 302 para `next` (se seguro) ou `LOGIN_REDIRECT_URL` (`/`); sessão por cookie.
- Falha: 200 com o formulário e alerta "Usuário e/ou Senha inválidos.".
- Redirecionamento de páginas protegidas: `LOGIN_URL = "/login/?next="` ⇒ `/login/?next=<caminho>`.

### `POST /user/recuperar-senha/email`
- Campos: `email`, `g-recaptcha-response` (preenchido pelo widget do Google), `csrfmiddlewaretoken`.
- Validações em ordem: reCAPTCHA ausente → "Verificação do reCAPTCHA não efetuada."; `siteverify` com erro/`success=false` → "Ocorreu um erro na validação do reCAPTCHA."; e-mail inexistente → "Não existe nenhum usuário cadastrado com este e-mail.".
- Sucesso: envia e-mail (template `eauth/user/recuperar_senha_email.html`, destinatários = usuários ativos com `email__iexact`) e 302 para `recuperar_senha_finalizado`.
- Link do e-mail: `https://<host da requisição>/user/recuperar-senha/<uidb64>/<token>`.
- Chamada externa: `POST https://www.google.com/recaptcha/api/siteverify?secret=<GOOGLE_RECAPTCHA_SECRET_KEY>&response=<token>` — resposta JSON com `success`.

### `GET/POST /user/recuperar-senha/<uidb64>/<token>`
- O Django troca o token por `set-password` na sessão (302 na primeira visita) e exibe `NovaSenhaForm` (`new_password1`, `new_password2`, botão "Enviar").
- Sucesso: 302 para `password_reset_complete`; link inválido/expirado: página do Django com `validlink=False` (usa o template do formulário).

### `GET/POST /user/edit`
- Campos: `first_name`, `last_name`, `avatar` (arquivo; `multipart`), `avatar_cropping`, `current_password`, `new_password1`, `new_password2`.
- Sucesso: mensagem de atualização (`FORM_MESSAGES[ACTION_UPDATE]`) e 302 para `/user/edit`. Alterar a senha invalida a sessão atual.
- Anônimo: 302 para o login.

## Rotas de administração

| Nome | Regex (relativa ao prefixo `^admin/user/`) | URL final | Permissão (Django) | Observação |
|------|------------------------------------------|-----------|--------------------|------------|
| `user_list` | `^$` | `/admin/user/` | `eauth.list_user` | 100 por página; busca `q`; `page_size`; ordenação `-is_superuser,-is_active,first_name` |
| `user_create` | `^create$` | `/admin/user/create` | `eauth.add_user` | `BackendUserAdminForm`; `layout_key='UserCreate'` |
| `user_view` | `^(?P<pk>\d+)$` | `/admin/user/<pk>` | `eauth.view_user` | layout `UserDetail` |
| `user_update` | `^(?P<pk>\d+)/edit$` | `/admin/user/<pk>/edit` | `eauth.change_user` | template `eauth/user_form.html` (botão Renovar) |
| `user_delete` | `^(?P<pk>\d+)/delete$` | `/admin/user/<pk>/delete` | `eauth.delete_user` | `crud/confirm_delete.html` |

As rotas e permissões exatas são produzidas por `Crud.get_urls()` (feature 004; `RP_LIST`, `RP_VIEW`, `RP_ADD`, `RP_CHANGE`, `RP_DELETE` concatenados a `<app_label>` e `<model_name>`). O grupo `Administrador do Sistema` recebe essas permissões e `menu_1` sobre `User` por `backend/globalrules/map_rules.py` (feature 003).

### `GET /admin/auditlog` (`pesquisar_auditlog`)
- Regex `^admin/auditlog`; permissão `eauth.list_auditlog` (superusuário por padrão; sem regra de grupo).
- Parâmetros GET: `user` (pk), `operation` (`U|C|D|P`), `model_name`, `timestamp` (`today|yesterday|week|month|year`; padrão `week` quando ausente), `busca` (`campo=valor,campo2=valor2`; `id=` → `object_id`), `page`.
- Contexto: `filter`, `object_list`, `page_obj`, `paginator`, `page_range`, `filter_url`, `show_results`, `numero_res`, `NO_ENTRIES_MSG = 'Nenhum registro de log encontrado!'`, `title = 'Pesquisar Logs de Auditoria'`.
- Paginação: 20 itens; ordenação `-id`.
- **Estado atual**: o template `eauth/auditlog_filter.html` não existe ⇒ a resolução do template falha (`TemplateDoesNotExist`) mesmo para superusuário.

## Integrações com outros contratos

| Origem | Contrato |
|--------|----------|
| API (feature 005) | `/api/eauth/user/` e `/api/eauth/auditlog/` gerados por `ApiViewSetConstrutor.build_class([apps.get_app_config('eauth')])`; `POST /api/recriar-token/<pk>` (`IsAdminUser`, nome `backend.api:recria_token`) recria o `Token` e responde `{"message": "Token recriado com sucesso!", "token": "<chave>"}`; `POST/DELETE` de sessão em `AppSessionAuthView` (`login`/`logout` por API) |
| Menu (feature 004) | `menu_administracao.yaml`: `backend.eauth:user_list` e `backend.eauth:pesquisar_auditlog` sob `check_permission: menu_administracao` |
| Base (`_templates/base.html`) | `backend.eauth:backend_user_change`, `backend.eauth:logout` (formulário `POST`), `backend.eauth:login` |
