# Início Rápido: validar Autenticação, Usuários e Auditoria (`eauth`)

Pré-requisitos: feature `001-fundacao-projeto-django` em funcionamento (PostgreSQL acessível, `backend/.env` criado), dependências instaladas (`poetry install`) e, para as telas, o frontend/`_templates` disponíveis. Os comandos assumem a raiz do repositório com o ambiente Python ativo (`.venv`).

## 1. Banco e superusuário

```bash
python manage.py migrate
python manage.py createsuperuser          # pede E-mail e senha (login por e-mail)
```

Esperado: tabelas `eauth_user`, `eauth_user_groups`, `eauth_user_user_permissions`, `eauth_auditlog`; superusuário com `is_staff` e `is_superuser` verdadeiros.

Verificação rápida no shell:

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model as g; u=g().objects.first(); print(u.email, u.username, u.is_superuser, str(u))"
python manage.py showmigrations eauth      # [X] 0001_initial
python manage.py makemigrations --check --dry-run   # sem mudanças pendentes
```

## 2. Login / logout (US1)

1. `python manage.py runserver` (ou `./rdev.sh`/`./uupdev.sh` — feature 010) e abra `http://localhost:8000/login/`.
2. Entre com o e-mail e a senha → redirecionado para `/`; o menu mostra o avatar, "Meu Perfil" e "Sair".
3. Senha errada → alerta "Usuário e/ou Senha inválidos.".
4. Acesse uma rota protegida anônimo (ex.: `/user/edit`) → `/login/?next=/user/edit`.
5. "Sair" → sessão encerrada, retorno a `/`.
6. Observação: senhas com mais de 30 caracteres são recusadas pelo `LoginForm`.

## 3. CRUD de usuários (US3)

- `http://localhost:8000/admin/user/` (superusuário). Criar em `/admin/user/create` (e-mail, nome, sobrenome, ativo, senhas iguais); editar em `/admin/user/<pk>/edit` (grupos/permissões em caixas de seleção; botão **Renovar** atualiza o token — chama `POST /api/recriar-token/<pk>`).
- Deixar as senhas em branco na edição não altera a senha.

## 4. Perfil (US4)

- `http://localhost:8000/user/edit`: alterar nome → mensagem de sucesso. Alterar senha exige que a nova passe nos validadores; após salvar, a sessão é invalidada e é preciso entrar de novo.

## 5. Recuperação de senha (US5)

- Configure em `backend/.env` as chaves `GOOGLE_RECAPTCHA_SITE_KEY` e `GOOGLE_RECAPTCHA_SECRET_KEY` (valores reais ou de teste do Google; não versionar) e as variáveis de e-mail do seu provedor (o repositório não as define).
- Abra `/user/recuperar-senha/email`. **Atenção ao estado atual**: o script do reCAPTCHA está no bloco `head_content` inexistente em `base.html` e `base_email.html` não existe; sem corrigi-los o fluxo não conclui (ver `research.md` #13 e #14). Para validar apenas a lógica use os testes da seção 7.

## 6. Auditoria (US6)

- `http://localhost:8000/admin/auditlog` (superusuário). Estado atual: falha por ausência de `eauth/auditlog_filter.html`.
- Para confirmar que a gravação está inoperante: no shell, alterar um `User` e conferir `AuditLog.objects.count()` — permanece 0:

```bash
python manage.py shell -c "from backend.eauth.models import AuditLog as A; print(A.objects.count())"
```

## 7. Testes automatizados

```bash
pytest backend/tests.py                    # existente: default_app_config
pytest backend/eauth                       # testes de eauth (a criar — ver tasks.md)
ruff check backend/eauth backend/mixins.py backend/settings/auth.py
```

Testes recomendados (cobertos por `tasks.md`), em `backend/eauth/tests/` ou `backend/eauth/test_*.py` (o `pyproject.toml` procura `**/tests.py` e `**/test_*.py`):

| Teste | Verifica |
|-------|----------|
| `test_create_user_and_superuser` | flags, e-mail normalizado, `ValueError` sem e-mail, `str(user)`, `username` |
| `test_user_manager_swallows_duplicate` | comportamento atual de duplicidade (retorna o existente) |
| `test_groups_add_remove_user` | criação de grupo, idempotência, lista/nome único |
| `test_avatar_validation_limit` | >10 MiB lança `ValidationError`; `sizeof_fmt` |
| `test_login_ok_and_fail` | login com `app` (webtest) e mensagem genérica; senha >30 |
| `test_logout_post` | logout só por POST e redireciona a `/` |
| `test_user_edit_requires_login_and_password_rules` | `/user/edit`: anônimo redireciona; senha atual errada/igual/divergente/ok |
| `test_user_crud_permissions` | superusuário acessa `/admin/user/`; usuário comum não |
| `test_user_admin_form_groups_and_password` | senha opcional na edição; escolhas de grupos/permissões |
| `test_recuperar_senha_form` | reCAPTCHA ausente; e-mail inexistente (mensagem atual); `get_users` ativo/`iexact` (mock de `urllib3`) |
| `test_urls_names_and_order` | `reverse('backend.eauth:...')` para todos os nomes; `recuperar-senha/completo` não cai em `confirma` |
| `test_auditlog_signal_is_noop` | alterar `User` não cria `AuditLog` (estado atual) |
| `test_auditlog_signal_with_patched_filter` | com filtro corrigido (patch), grava `C`/`U`/`D` com usuário do `request` |
| `test_auditlog_model_and_manager` | `last_action_user`, `first_action_user`, `actions_users`, `__str__` |
| `test_auditlog_filterset_busca` | `filter_busca` (id, valores, `icontains`) |
| `test_auditlog_view_permission` | sem `eauth.list_auditlog` → 403/redirect; documentar `TemplateDoesNotExist` atual |

A fixture `app` (`conftest.py`) usa `admin_user.username` (e-mail) — por isso a propriedade `User.username` é necessária.
