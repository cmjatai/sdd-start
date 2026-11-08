# Pesquisa: Autenticação, Usuários e Auditoria (app `eauth`)

Decisões inferidas do código existente (engenharia reversa). Formato: **Decisão / Justificativa / Alternativas consideradas**.

## Decisões técnicas

### D1. Modelo de usuário customizado com login por e-mail
- **Decisão**: `eauth.User(AbstractBaseUser, SearchModelMixin, PermissionsMixin)` com `USERNAME_FIELD='email'`, sem campo `username`; propriedade `username` devolve o e-mail. `AUTH_USER_MODEL = "eauth.User"` desde a migração inicial.
- **Justificativa**: o e-mail é o identificador natural em sistemas corporativos e evita redundância de `username`; definir o modelo antes da primeira migração evita a migração dolorosa posterior de `AUTH_USER_MODEL`. A propriedade `username` mantém compatibilidade com ferramentas (pytest-django `admin_user`, `conftest.py`, `AppVersionView` em `backend/api/views.py`).
- **Alternativas**: `AbstractUser` com `username` (descartado: exigiria preencher/duplicar o campo); `User` padrão + perfil 1:1 (descartado: junção extra e e-mail não único).

### D2. `SearchModelMixin` no usuário
- **Decisão**: o usuário herda o campo `search` (texto normalizado de `first_name`, `last_name`, `email`) para alimentar a busca da lista do CRUD (`ListWithSearchForm`).
- **Justificativa**: busca simples por `icontains` sobre um único campo normalizado (sem acentos); consistente com os demais modelos do projeto.
- **Alternativas**: filtros `Q` em vários campos (mais custoso e sem normalização).

### D3. Reaproveitar views/forms do `django.contrib.auth` com templates próprios
- **Decisão**: `BackendLoginView`, `BackendPasswordReset*View` herdam das views padrão; só mudam `template_name`, `form_class` e `success_url`; formulários herdam de `AuthenticationForm`, `PasswordResetForm`, `SetPasswordForm`.
- **Justificativa**: menor superfície de segurança própria (tokens, hash de sessão, throttling de Django) e reutilização de testes do Django.
- **Alternativas**: telas por API/SPA (a Constituição V mantém o Django como dono da autenticação por sessão).

### D4. reCAPTCHA apenas na recuperação de senha, validado no servidor
- **Decisão**: `GoogleRecapthaMixin` valida `g-recaptcha-response` chamando `siteverify` com `urllib3`; chaves lidas por `decouple` com padrão vazio (`settings/auth.py`).
- **Justificativa**: impede o uso do formulário como relé de e-mails e a automação de pedidos; não depender de pacote adicional.
- **Alternativas**: `django-recaptcha` (dependência extra); sem captcha (risco de abuso).

### D5. CRUD de usuários sobre a classe genérica `Crud`
- **Decisão**: `UserCrud(Crud)` expõe `/admin/user/` com formulário próprio (`BackendUserAdminForm`), layouts YAML (`layouts.yaml`) e hooks de exibição.
- **Justificativa**: consistência visual e de permissões com o restante do sistema (feature 004); permissões do Django (`*_user`) controlam o acesso.
- **Alternativas**: usar apenas o Django Admin (`/system/`, que também registra os modelos).

### D6. Permissões e grupos por caixas de seleção, limitadas a `BACKEND_APPS`
- **Decisão**: na edição, grupos e permissões do usuário são `CheckboxSelectMultiple`, com os atribuídos primeiro; permissões ofertadas restritas aos `app_label` derivados de `settings.BACKEND_APPS` (`backend.eauth`→`eauth`).
- **Justificativa**: evita listar centenas de permissões de apps de terceiros (admin, celery, haystack…).
- **Alternativas**: `FilteredSelectMultiple` do admin; seleção livre.

### D7. Token de API visível/renovável pela tela de usuário
- **Decisão**: campo somente leitura `token` (valor `user.auth_token.key`) e botão "Renovar" que chama `POST /api/recriar-token/<pk>` por `fetch` com CSRF e atualiza o campo.
- **Justificativa**: o token é a credencial de API por usuário (`rest_framework.authtoken`); renová-lo sem recarregar a página é conveniente para administradores.
- **Alternativas**: página própria de gestão de tokens.

### D8. Auditoria genérica por sinais, serializando o objeto como JSON do Django
- **Decisão**: um único receptor de `post_save`/`post_delete` (sem `sender`) grava `AuditLog` com `serializers.serialize('json', (instance,))`, o usuário encontrado varrendo a pilha por uma variável local `request`, e a pilha em `obj[0]['stack']`.
- **Justificativa**: auditar sem alterar views/modelos (zero acoplamento); a varredura da pilha evita middleware/`threadlocal`.
- **Alternativas**: `django-simple-history`/`django-auditlog` (dependências externas); middleware com contexto de usuário (mais robusto e barato).

### D9. Pesquisa de auditoria com `django-filter` e busca em campos do JSON
- **Decisão**: `AuditLogFilterSet` filtra por usuário, operação, tipo de registro, período (`DateRangeFilter`, padrão semana) e busca textual `campo=valor` em `obj__0__fields__<campo>` (JSONField do PostgreSQL).
- **Justificativa**: permite localizar alterações de um registro específico sem tabelas adicionais.
- **Alternativas**: colunas dedicadas por campo; indexação no Solr.

### D10. URLs na raiz com `re_path` e namespace `backend.eauth`
- **Decisão**: rotas como `/login`, `/logout`, `/user/edit`, `/user/recuperar-senha/...`, `/admin/user/`, `/admin/auditlog`, incluídas em `backend/urls.py` com `path("", include(...))`.
- **Justificativa**: URLs curtas e estáveis para o usuário final; `/system/` fica reservado ao Django Admin; `LOGIN_URL="/login/?next="` casa com `^login` (a barra final é aceita porque a regex não tem âncora final).
- **Alternativas**: prefixo `/eauth/` (URLs mais longas).

### D11. Templates globais em `_templates/eauth/`
- **Decisão**: templates ficam no diretório global `_templates` (e não em `backend/eauth/templates`), junto de `layouts.yaml` lido pelo `Crud` como `<label>/layouts.yaml`.
- **Justificativa**: um só diretório de templates compartilhado com o frontend Django e com os menus (feature 004/007).

## Particularidades, dívidas técnicas e riscos observados

> Recomendação geral: o **estado atual é replicar** para fidelidade da reconstrução; a coluna "Recomendação" indica a correção desejável em evolução futura (que deve atualizar esta especificação — Constituição, Fluxo 3).

| # | Observação (confirmada no código) | Risco | Recomendação |
|---|-----------------------------------|-------|--------------|
| 1 | **Auditoria inoperante.** `auditlog_signal_function` usa `sender._meta.app_config.name[:10]` e compara com `('backend',)`. Como todos os apps são `backend.<nome>` (nomes com ≥ 10 caracteres), `name[:10]` é p.ex. `'backend.ea'`, nunca `'backend'`: a função sempre retorna antes de gravar. Verificado com `django.setup()`: nenhum app tem `name[:10] == 'backend'`. | Alto (funcionalidade prometida não ocorre) | Replicar (fidelidade). Corrigir: `sender._meta.app_config.name.startswith('backend.')` (e filtrar apps de interesse), com teste. |
| 2 | Mesmo corrigido o filtro: o **anônimo** nunca é detectado (o `AnonymousUser` não tem `_meta`, a exceção é engolida pelo `except` e o laço continua), logo grava com `user=None`; **sem request** (shell, Celery, management commands) também grava `user=None, email=''`. | Médio (ruído e logs sem autoria) | Replicar. Corrigir: ignorar/marcar explicitamente quando não há usuário autenticado; usar `contextvars` + middleware. |
| 3 | Se o filtro do item 1 for corrigido, o laço sobre `inspect.stack()` passa a executar a **cada** `post_save`/`post_delete` de modelos do projeto; `inspect.stack()` é caro (lê o código-fonte dos frames). Hoje não executa, pois o filtro retorna antes. | Médio (desempenho em cargas em lote) | Replicar. Corrigir: usar `inspect.currentframe()` ou contexto por middleware; checar tipo do modelo antes. |
| 4 | A **pilha de chamadas** (`str` do frame) é gravada no JSON (`obj[0]['stack']`) — vaza caminhos de arquivo e nomes de variáveis ao auditor e infla a tabela. Só o frame do `request` (ou o mais externo) é guardado, não a pilha toda (comentário `'\n'.join(stack)` desativado). | Baixo/Médio | Replicar. Corrigir: remover ou guardar apenas dados úteis. |
| 5 | Operação `'P'` (Pesquisa) existe em `OPERATION_CHOICES` e no filtro, mas nenhum código a gera. | Baixo | Replicar (manter choices). Remover ou implementar. |
| 6 | **Template ausente**: `PesquisarAuditLogView` (`FilterView`, sufixo `_filter`) exige `eauth/auditlog_filter.html`, inexistente em `_templates/eauth/` (verificado: `get_template` falha). A tela `/admin/auditlog` (item de menu) gera `TemplateDoesNotExist`. | Alto (tela quebrada) | Replicar estado atual para fidelidade; corrigir criando o template (filtro crispy + tabela paginada usando `page_range`, `filter_url`, `NO_ENTRIES_MSG`, `paginacao.html`). |
| 7 | `AuditLogFilterSet.user = ChoiceFilter(choices=get_username())` é avaliado **na importação** (consulta ao banco ao carregar `backend.eauth.forms`, via `urls.py`→`views.py`); `except:` nu devolve `[]` se falhar (ex.: antes do `migrate`). A lista fica estática até reiniciar o processo e carrega todos os usuários na memória. | Médio | Replicar. Corrigir: `choices=get_username` (callable) ou `ModelChoiceFilter`. |
| 8 | `get_models()` usa `distinct('model_name')` (DISTINCT ON do PostgreSQL). | Baixo (alinhado à restrição "somente PostgreSQL") | Replicar. |
| 9 | `filter_busca` desempacota `k, v` por `split('=')`: termo sem `=` ou com mais de um `=` causa `ValueError` (HTTP 500); valores inteiros são comparados como `int` mesmo quando o campo é texto; usa chaves de JSON vindas do usuário (`obj__0__fields__<k>`) sem lista de campos permitidos. | Médio | Replicar. Corrigir: validar entrada e tratar erros como filtro vazio. |
| 10 | `PesquisarAuditLogView.get`: `len(resultados)` carrega toda a consulta na memória (`numero_res`); muta `request.GET`; `filter_url` passado ao contexto é sobrescrito por `get_context_data`; `get_filterset_kwargs` descarta o retorno do `super()`; importações não usadas (`RP_LIST`, `RP_VIEW`) e bloco comentado. | Baixo/Médio | Replicar. Corrigir: usar `paginator.count`. |
| 11 | **`RecuperarSenhaForm.clean` revela se o e-mail existe** (mensagem "Não existe nenhum usuário cadastrado com este e-mail."): permite enumerar contas. A checagem é por igualdade exata, mas o envio usa `iexact` + `is_active` (inconsistência: e-mail com caixa diferente é rejeitado; usuário inativo recebe "sucesso" sem e-mail). Além disso `self.data['email']` gera `MultiValueDictKeyError` se a chave faltar. | Alto (privacidade) | Replicar. Corrigir: resposta idêntica para existentes e inexistentes (padrão do Django), apenas `get_users` decide o envio. |
| 12 | **`/user/recuperar-senha/finalizado` herda `PasswordResetView`** (e não `PasswordResetDoneView`): um `POST` nessa rota executa o fluxo padrão do Django **sem reCAPTCHA** (envia e-mail com `registration/password_reset_email.html`) e depois falha em `reverse_lazy('password_reset_done')` (rota inexistente) ⇒ possibilidade de abuso para disparo de e-mails. | Alto | Replicar. Corrigir: herdar de `PasswordResetDoneView`. |
| 13 | **Template de e-mail ausente**: `recuperar_senha_email.html` estende `base_email.html`, que não existe em nenhum diretório do repositório; usado como `email_template_name` e `html_email_template_name`. O envio real falha com `TemplateDoesNotExist` e `settings/email.py` está vazio (SMTP `localhost:25`). O link do e-mail usa `https://` fixo e o `domain` vem de `RequestSite` (`django.contrib.sites` não está instalado). | Alto (recuperação de senha não funcional "de fábrica") | Replicar. Corrigir: criar `base_email.html`, `html_email_template_name` + versão texto, `EMAIL_*` por ambiente (`decouple`) e `SITE_URL`. |
| 14 | **reCAPTCHA não renderiza**: `recuperar_senha_email_form.html` coloca o `<script>` em `{% block head_content %}`, bloco inexistente em `base.html`; sem o script, `g-recaptcha-response` nunca é enviado e o formulário sempre falha com "Verificação do reCAPTCHA não efetuada.". Além disso, a `secret` é enviada na query string (`POST` com URL), `urllib3` sem timeout explícito, e chaves vazias nunca validam. O comentário `# if not settings.DEBUG else ''` indica que havia desligamento em DEBUG, hoje inexistente. | Alto (fluxo inutilizável) | Replicar. Corrigir: definir o bloco (ou usar `extra_js`), enviar `secret`/`response` no corpo, timeout, e modo de teste por variável de ambiente. |
| 15 | `UserManager._create_user` engole **qualquer** exceção do `save()` (`except:` nu) e retorna `get_by_natural_key(email)`: criar usuário com e-mail duplicado devolve o existente (e a senha informada é descartada silenciosamente) em vez de erro; outras falhas viram `DoesNotExist`. | Alto (mascaramento de erros, risco de confundir contas) | Replicar. Corrigir: remover o `try/except` (deixar `IntegrityError`). |
| 16 | `LoginForm.password.max_length = 30`, mas as demais telas aceitam até 50 caracteres e o Django não limita: usuários com senha > 30 não conseguem entrar (mensagem genérica). | Médio | Replicar. Corrigir: remover/alinhar o limite. |
| 17 | `BackendUserChangeForm.clean`: a senha atual só é checada `if old_password`; enviar só `new_password1/2` altera a senha sem confirmar a identidade (sessão sequestrada ⇒ troca de senha). Após `set_password` não há `update_session_auth_hash`, então a sessão cai (o aviso da tela descreve isso). | Médio | Replicar. Corrigir: exigir `current_password` sempre que houver nova senha. |
| 18 | `BackendUserAdminForm`: grande bloco de código/campos comentados (`areatrabalho`, `autor`, `OperadorAreaTrabalho`…) herdados de outro sistema; `save()` termina em `return inst` com docstrings mortas; `clean()` não retorna `data`; `user_session` é recebido e não usado. | Baixo (dívida) | Replicar o comportamento; limpar o código morto. |
| 19 | `token`: o valor do token de API de **qualquer** usuário é exibido a quem edita o usuário; e `recria_token` exige apenas `IsAdminUser` (`is_staff`) e aceita qualquer `pk` (inclusive vazio por `\d*`): um staff comum pode obter token de outro usuário (inclusive superusuário) e assumir sua identidade na API. Na criação (`object` nulo) o botão "Renovar" chama a rota com `pk` vazio. | Alto (escalonamento de privilégio; feature 005) | Replicar. Corrigir: exigir `change_user`/superusuário, restringir `pk` a `\d+`, não exibir o token em claro. |
| 20 | `User.get_absolute_url()` devolve tupla `('users_profile', [pk], {})` (padrão `@models.permalink` removido) e a rota `users_profile` não existe; qualquer uso (ex.: Admin "ver no site") quebra. | Baixo | Replicar. Corrigir: `reverse('backend.eauth:user_view', args=[pk])`. |
| 21 | `User.Meta.permissions = PERMS_FOR_USERS` (de `backend.globalrules`, feature 003) cria `menu_1` e `orcamento_1` no `User`; nomes de exemplo ("Mostrar Menu 1", "Ação 1") do esqueleto. `models.py` importa `backend.globalrules` (somente as constantes de `backend/globalrules/__init__.py`). | Baixo | Replicar (derivados renomeiam). |
| 22 | `AuditLog` não tem regra em `map_rules.py` ⇒ só superusuários têm `eauth.list_auditlog`; `AuditLogManager.use_for_related_fields` é atributo obsoleto; `content_type` com `PROTECT` impede apagar `ContentType`; `obj_id` é `PositiveIntegerField` obrigatório (não suporta PK não inteira/UUID; um `instance.id` nulo falha no `save`, capturado pelo `except` do sinal). | Baixo | Replicar. |
| 23 | URLs com `re_path` sem `$`: `^login`, `^logout`, `^user/edit`, `^admin/auditlog` casam qualquer sufixo (`/loginxyz`, `/user/editar`). A ordem importa: `confirma` (`<uidb64>/<token>`) precede `completo`; `email` e `finalizado` vêm antes e interceptam qualquer caminho com esse prefixo. `urls.py` importa `include/re_path` duas vezes e `path`/`_` sem uso. | Baixo | Replicar. Corrigir: ancorar com `$`. |
| 24 | `LogoutView` recebe `{'next_page': '/'}` como kwargs de URL (ignorado pela view); o redirecionamento efetivo vem de `LOGOUT_REDIRECT_URL`. A rota só aceita `POST` (Django ≥ 5). | Baixo | Replicar. |
| 25 | `LOGIN_URL = "/login/?next="`: funciona porque o Django substitui o `next` vazio; configuração incomum (o idiomático seria `/login/`). | Baixo | Replicar. |
| 26 | `login_portlet.html` posta em `action="/login"` fixo (sem `{% url %}`), com `enctype="multipart/form-data"` desnecessário e tags `<a ... />`/`<button ... />` auto-fechadas (HTML inválido). | Baixo | Replicar. |
| 27 | `settings/auth.py` define validadores com mínimo 6 caracteres (Constituição) — mais fraco que o padrão Django (8). Não há limitação de tentativas de login (rate limiting) nem 2FA. | Médio | Replicar; avaliar `django-axes`/throttling. |
| 28 | `services/tasks.py` é um stub (importa `app` do Celery e cria `logger` sem tarefas); `apps.py` importa `inspect` e `settings` sem uso; `templatetags/` contém somente `__pycache__` (sem código); `forms_auth.UserCreationForm`/`UserChangeForm` não são usados pelas views; `RecuperarSenhaForm.teste` é atributo morto. | Baixo | Replicar (ou remover). |
| 29 | `email.py` de `settings` vazio; as variáveis `GOOGLE_RECAPTCHA_*` são lidas por `decouple` e o `backend/.env` de desenvolvimento declara as duas chaves (valores não registrados aqui). | Baixo | Documentar as variáveis no guia de configuração dos derivados. |
| 30 | Não existem testes de `eauth`; a cobertura limita-se a `backend/tests.py::test_app_init_files_have_default_app_config`. | Médio (Constituição VIII) | Corrigir: implementar os testes das tarefas de `tasks.md`. |
| 31 | `BackendUserAdminForm` limita permissões listadas a apps de `BACKEND_APPS` (`eauth`, `utils`), excluindo `api` e `globalrules`; a lista de grupos/permissões só é reconfigurada quando `instance.pk` existe (na criação usa os widgets padrão). | Baixo | Replicar. |
| 32 | `User.first_name`/`last_name` limitados a 30 caracteres (herança do Django antigo); `AbstractBaseUser.Meta` herdado com `abstract=False` explícito. | Baixo | Replicar. |
