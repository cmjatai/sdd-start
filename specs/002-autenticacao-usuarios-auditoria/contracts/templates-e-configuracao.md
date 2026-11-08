# Contrato: templates, layouts YAML, configuração e ambiente

## Variáveis de ambiente / settings

| Variável (`.env`) | Setting | Padrão | Uso |
|-------------------|---------|--------|-----|
| `GOOGLE_RECAPTCHA_SITE_KEY` | `settings.GOOGLE_RECAPTCHA_SITE_KEY` | `""` | atributo `data-sitekey` do `div.g-recaptcha` em `GoogleRecapthaMixin` |
| `GOOGLE_RECAPTCHA_SECRET_KEY` | `settings.GOOGLE_RECAPTCHA_SECRET_KEY` | `""` | segredo enviado ao `siteverify` do Google (nunca versionar) |
| — (código) | `AUTH_USER_MODEL` | `"eauth.User"` | modelo de usuário |
| — | `LOGIN_URL` | `"/login/?next="` | destino de `login_required`/`PermissionRequiredMixin` anônimo |
| — | `LOGIN_REDIRECT_URL` | `"/"` | pós-login sem `next` |
| — | `LOGOUT_REDIRECT_URL` | `"/"` | pós-logout |
| — | `AUTH_PASSWORD_VALIDATORS` | 4 validadores (mín. 6) | todas as definições de senha |
| (a definir pelo derivado) | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `DEFAULT_FROM_EMAIL`… | `settings/email.py` vazio ⇒ SMTP `localhost:25` | envio do e-mail de recuperação |

## Templates (`_templates/eauth/`, diretório global em `TEMPLATES[0]['DIRS']`)

| Template | Estende | Blocos / contexto | Observação |
|----------|---------|-------------------|------------|
| `user/login.html` | `base.html` | `main_container_class`=`container`, `title` vazio, `base_content` inclui `login_portlet.html` | página de login |
| `user/login_portlet.html` | — | `form` (LoginForm), `next`; `{% url 'backend.eauth:recuperar_senha_email' %}` | formulário `POST /login` |
| `user/recuperar_senha_email_form.html` | `crud/form.html` | `head_content` (inexistente em `base.html`) com `api.js` do reCAPTCHA | formulário crispy do `RecuperarSenhaForm` |
| `user/recupera_senha_email_enviado.html` | `crud/detail.html` | `base_content` | texto "Foi enviado um e-mail para o endereço inserido…" |
| `user/nova_senha_form.html` | `crud/form.html` | — | `NovaSenhaForm` |
| `user/recuperar_senha_completo.html` | `crud/detail.html` | `table_content` | "A sua senha foi alterada com sucesso! Clique aqui e faça seu login." |
| `user/recuperar_senha_email.html` | `base_email.html` (**ausente**) | `email_content`; variáveis `domain`, `uid`, `token` | corpo do e-mail (texto e HTML) |
| `user/avatar.html` | — | `user_render`, `css_class` | usado por `{% avatar_user user 'avatar-2' %}` (feature 009) |
| `user_form.html` | `crud/form.html` | `extra_js` com o script do botão `#renovar-token` | template do `UserCrud` (create/update) |
| `auditlog_filter.html` | — | — | **não existe** (necessário por `PesquisarAuditLogView`) |

Texto-chave do login: título "Acesso ao Sdd-Start", subtítulo "Entre com seu usuário e senha", botão "ENTRAR", link "Esqueci minha Senha", alerta "Usuário e/ou Senha inválidos.".

## `_templates/eauth/layouts.yaml`

Arquivo Django-template + YAML lido por `read_layout_from_yaml("eauth/layouts.yaml", layout_key)` (feature 004). Conteúdo:

```yaml
{% load i18n %}

UserDetail:
  {% trans 'Usuário' %}:
  - email:8 is_active
  - first_name last_name
  - groups
  - user_permissions

UserCreate:
  {% trans 'Usuário' %}:
  - email first_name last_name is_active
  - new_password1 new_password2
```

Sintaxe: cada chave de topo é um `layout_key`; cada subchave é a legenda do fieldset; cada item é uma linha com nomes de campos separados por espaço; `campo:N` define a largura em colunas Bootstrap.

## Contrato de formulários (campos expostos)

| Formulário | Campos |
|------------|--------|
| `LoginForm` | `username`, `password` |
| `BackendUserChangeForm` | `first_name`, `last_name`, `avatar`, `avatar_cropping`, `current_password`, `new_password1`, `new_password2` |
| `BackendUserAdminForm` | `email`, `first_name`, `last_name`, `is_active` (Sim/Não → bool), `token` (somente leitura), `new_password1`, `new_password2`, `groups`, `user_permissions` |
| `RecuperarSenhaForm` | `email` (+ `g-recaptcha-response` fora do formulário) |
| `NovaSenhaForm` | `new_password1`, `new_password2` |
| `AuditLogFilterSet` | `user`, `busca`, `operation`, `model_name`, `timestamp` |

## Contrato de sinal de auditoria

- Receptor: `backend.eauth.services.signals.auditlog_post_signal`, `dispatch_uid='auditlog_post_signal'`, conectado a `post_save` e `post_delete` de **todos** os modelos; carregado por `EAuthConfig.ready()`.
- Saída (quando gravar): `AuditLog` com `operation ∈ {C,U,D}`, `obj = [{"model": "<app>.<modelo>", "pk": <id>, "fields": {...}, "stack": "<str do frame>"}]`.
- Condições de descarte: app sem `name[:10] == 'backend'` (todos, hoje), modelo `AuditLog`, execução dentro de função `migrate`, usuário anônimo identificado.

## Comandos (CLI)

| Comando | Efeito |
|---------|--------|
| `python manage.py migrate` | cria `eauth_user`, `eauth_auditlog` e permissões (`list_*` por `globalrules`) |
| `python manage.py createsuperuser` | solicita e-mail e senha (campo `email` é `USERNAME_FIELD`) e cria superusuário |
| `python manage.py makemigrations eauth` | regenera a migração do app |
