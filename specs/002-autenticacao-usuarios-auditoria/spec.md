# Especificação da Funcionalidade: Autenticação, Usuários e Auditoria (app `eauth`)

**Branch da Funcionalidade**: `002-autenticacao-usuarios-auditoria`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: app `backend/eauth/` completo (modelos `User`/`UserManager`/`AuditLog`, formulários, views de login, recuperação de senha, edição de perfil e CRUD de usuários, URLs, sinais de auditoria, migração inicial), `backend/mixins.py` (`GoogleRecapthaMixin`), `backend/settings/auth.py`, templates `_templates/eauth/**` e `_templates/eauth/layouts.yaml`, uso de `AUTH_USER_MODEL`, `LOGIN_URL` e criação de superusuário por e-mail."

**Pré-requisito**: `001-fundacao-projeto-django` (estrutura `backend/`, settings modulares, `python-decouple`, PostgreSQL). Features vizinhas: `003-regras-permissoes-globais` (grupos/permissões, `PERMS_FOR_USERS`, `list_<modelo>`), `004-crud-generico-menus` (classe `Crud`, layouts YAML, menus), `005-api-rest-automatica` (endpoints `/api/eauth/...` e `recriar-token`), `009-midia-arquivos-avatar` (campo `avatar` com `ImageCropField`, miniaturas e tag `avatar_user`).

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Entrar e sair do sistema com e-mail e senha (Prioridade: P1)

Um visitante acessa `/login/`, informa o e-mail e a senha e passa a ter uma sessão autenticada. Pode encerrar a sessão pelo menu do usuário (botão "Sair"). Páginas protegidas redirecionam o visitante anônimo para `/login/?next=<página>`.

**Por que esta prioridade**: sem autenticação nenhuma outra funcionalidade protegida (CRUD, API por sessão, auditoria) é utilizável.

**Teste Independente**: criar um usuário ativo, abrir `/login/`, enviar e-mail e senha corretos e verificar o redirecionamento para `/` (ou para `next`) com o menu do usuário exibido; enviar senha errada e verificar a mensagem genérica de erro.

**Cenários de Aceitação**:

1. **Dado** um usuário ativo com e-mail e senha válidos, **Quando** ele envia o formulário de `/login/`, **Então** é autenticado e redirecionado para `LOGIN_REDIRECT_URL` (`/`) ou para o valor do campo oculto `next`.
2. **Dado** credenciais inválidas (e-mail inexistente, senha errada ou usuário inativo), **Quando** o formulário é enviado, **Então** a página é reexibida com o alerta "Usuário e/ou Senha inválidos." sem indicar qual dado falhou.
3. **Dado** um visitante anônimo que acessa uma rota que exige login, **Quando** a rota usa `LOGIN_URL`, **Então** ele é redirecionado para `/login/?next=<rota>`.
4. **Dado** um usuário autenticado, **Quando** ele aciona "Sair" (formulário `POST` para `/logout`), **Então** a sessão é encerrada e ele é levado para `/`.
5. **Dado** a barra de navegação, **Quando** o usuário está anônimo, **Então** é exibido o ícone de acesso (link para `/login/`); quando autenticado, é exibido o menu com avatar, "Meu Perfil" e "Sair".

---

### História de Usuário 2 - Modelo de usuário próprio identificado por e-mail e criação de superusuário (Prioridade: P1)

O projeto usa um modelo de usuário customizado (`eauth.User`) cujo identificador de login é o **e-mail** (não há campo `username` persistido). O administrador técnico cria o primeiro superusuário com `python manage.py createsuperuser`, informando e-mail e senha.

**Por que esta prioridade**: todos os demais apps referenciam `AUTH_USER_MODEL`; a migração inicial e o superusuário são o ponto de partida do sistema.

**Teste Independente**: rodar `migrate`, executar `createsuperuser` (e-mail + senha) e fazer login com esse e-mail em `/login/` e em `/system/` (Django Admin).

**Cenários de Aceitação**:

1. **Dado** um banco migrado, **Quando** `createsuperuser` é executado com e-mail e senha, **Então** é criado um `User` com `is_staff=True`, `is_superuser=True`, `is_active=True` e e-mail normalizado.
2. **Dado** o gerenciador `User.objects`, **Quando** `create_user(email, password)` é chamado, **Então** o usuário criado tem `is_staff=False` e `is_superuser=False`; **Quando** o e-mail é vazio, **Então** `ValueError('The given email must be set')`.
3. **Dado** um usuário com nome e sobrenome, **Quando** `str(user)` é avaliado, **Então** retorna "Nome Sobrenome"; sem nome, retorna o e-mail.
4. **Dado** `user.username`, **Quando** lido, **Então** devolve o e-mail (propriedade de compatibilidade usada por ferramentas de teste como a fixture `app` de `conftest.py`).

---

### História de Usuário 3 - Administrador gerencia usuários (Prioridade: P2)

Um usuário com as permissões do modelo (`eauth.list_user`, `view_user`, `add_user`, `change_user`, `delete_user`) usa o CRUD em `/admin/user/` para listar, criar, visualizar, editar e excluir usuários, definir senha, ativar/desativar, associar grupos e permissões individuais e renovar o token de API.

**Por que esta prioridade**: sem gestão de usuários o sistema só teria o superusuário; é a operação administrativa central.

**Teste Independente**: autenticado como superusuário, abrir `/admin/user/`, criar um usuário com senha, editá-lo marcando um grupo, e visualizar o detalhe.

**Cenários de Aceitação**:

1. **Dado** um administrador, **Quando** abre `/admin/user/`, **Então** vê a lista paginada (100 por página) com coluna "Usuario" (nome completo e e-mail) e "is_active", ordenada por superusuário, ativos e primeiro nome, com busca textual.
2. **Dado** o formulário de criação, **Quando** informa e-mail, nome, sobrenome, ativo e as duas senhas iguais e válidas, **Então** o usuário é criado com a senha definida (com hash).
3. **Dado** o formulário de edição, **Quando** deixa as senhas em branco, **Então** a senha não é alterada; **Quando** preenche senhas diferentes, **Então** erro "As senhas informadas são diferentes".
4. **Dado** a edição de um usuário, **Quando** o administrador clica em "Renovar" ao lado do campo Token, **Então** o token de API do usuário é recriado e exibido no campo (somente leitura).
5. **Dado** a edição, **Quando** a lista de grupos/permissões é exibida, **Então** os já atribuídos aparecem primeiro, seguidos dos demais; as permissões ofertadas se limitam aos apps de `BACKEND_APPS`.
6. **Dado** um usuário sem a permissão correspondente, **Quando** acessa qualquer rota do CRUD, **Então** o acesso é negado (regras do `Crud`, feature 004).

---

### História de Usuário 4 - Usuário edita o próprio perfil e senha (Prioridade: P2)

O usuário autenticado acessa "Meu Perfil" (`/user/edit`) para alterar nome, sobrenome, avatar (com enquadramento 128x128) e senha.

**Por que esta prioridade**: autonomia do usuário sobre os próprios dados, sem depender de um administrador.

**Teste Independente**: autenticado, abrir `/user/edit`, alterar o primeiro nome e salvar; verificar a mensagem de sucesso e o nome atualizado no título.

**Cenários de Aceitação**:

1. **Dado** um usuário autenticado, **Quando** abre `/user/edit`, **Então** o formulário já carrega os dados do próprio usuário (nunca de outro).
2. **Dado** o envio de nome/sobrenome válidos, **Quando** salva, **Então** exibe a mensagem de atualização e permanece em `/user/edit`.
3. **Dado** senha atual correta e nova senha válida repetida, **Quando** salva, **Então** a senha é alterada e, como o hash de sessão muda, o usuário deve se autenticar novamente (conforme aviso na própria tela).
4. **Dado** senha atual incorreta, **Quando** salva, **Então** erro "Senha atual informada não confere com a senha armazenada".
5. **Dado** nova senha igual à atual, **Quando** salva, **Então** erro "Nova senha não pode ser igual à senha anterior".
6. **Dado** um avatar maior que 10 MiB, **Quando** salva, **Então** erro de tamanho máximo (validação `avatar_validation`).
7. **Dado** um visitante anônimo, **Quando** acessa `/user/edit`, **Então** é redirecionado ao login.

---

### História de Usuário 5 - Recuperar senha por e-mail com reCAPTCHA (Prioridade: P2)

Quem esqueceu a senha clica em "Esqueci minha Senha" no login, resolve o reCAPTCHA, informa o e-mail cadastrado, recebe um link de redefinição e define nova senha.

**Por que esta prioridade**: evita dependência do administrador para reset de senha; depende de infraestrutura externa (reCAPTCHA e SMTP), por isso P2.

**Teste Independente**: com chaves de reCAPTCHA válidas e backend de e-mail configurado, solicitar a recuperação para um e-mail cadastrado e seguir o link recebido até a tela de "senha alterada com sucesso".

**Cenários de Aceitação**:

1. **Dado** `/user/recuperar-senha/email`, **Quando** o reCAPTCHA não foi resolvido, **Então** erro "Verificação do reCAPTCHA não efetuada.".
2. **Dado** reCAPTCHA resolvido e e-mail cadastrado e ativo, **Quando** envia, **Então** um e-mail com link `https://<domínio>/user/recuperar-senha/<uidb64>/<token>` é enviado e o usuário é levado a `/user/recuperar-senha/finalizado`.
3. **Dado** e-mail não cadastrado, **Quando** envia, **Então** a mensagem "Não existe nenhum usuário cadastrado com este e-mail." é exibida (comportamento real, que permite enumerar contas).
4. **Dado** o link recebido, **Quando** o usuário o abre e informa duas senhas iguais e válidas, **Então** a senha é alterada e é levado a `/user/recuperar-senha/completo`, com link para o login.
5. **Dado** falha de rede/resposta inválida do Google, **Quando** envia, **Então** erro "Ocorreu um erro na validação do reCAPTCHA.".

---

### História de Usuário 6 - Trilha de auditoria de alterações e sua consulta (Prioridade: P3)

O sistema mantém o modelo `AuditLog` e um sinal global (`post_save`/`post_delete`) projetado para registrar criação, atualização e exclusão de registros dos apps do projeto, com o usuário responsável. Auditores com a permissão `eauth.list_auditlog` consultam os registros em `/admin/auditlog`, com filtros por usuário, operação, tipo de registro, busca por campo e período (padrão: última semana).

**Por que esta prioridade**: valor de governança, mas não bloqueia o uso do sistema; no estado atual a gravação está inoperante e a página depende de um template ausente (ver Casos de Borda).

**Teste Independente**: como superusuário, abrir `/admin/auditlog`; criar/alterar registros e verificar linhas de `AuditLog` (comportamento projetado). Hoje: verificar, por teste, que o sinal retorna cedo e que a página falha por falta de `eauth/auditlog_filter.html`.

**Cenários de Aceitação**:

1. **Dado** um modelo de app cujo nome de configuração casa com o filtro do sinal, **Quando** um registro é criado, alterado ou excluído durante uma requisição autenticada, **Então** é gravado um `AuditLog` com operação `C`, `U` ou `D`, usuário, e-mail, JSON serializado do objeto (mais a chave `stack`), `app_name`, `model_name` e `obj_id`.
2. **Dado** o modelo `AuditLog` ou a execução de `migrate`, **Quando** ocorre `post_save`/`post_delete`, **Então** nada é registrado.
3. **Dado** um auditor, **Quando** acessa `/admin/auditlog` sem parâmetros, **Então** o filtro de período assume `timestamp=week` e os resultados vêm ordenados por `-id`, 20 por página.
4. **Dado** o filtro "Filtrar Campo" com `campo=valor, outro=valor2`, **Quando** aplicado, **Então** filtra pelo JSON `obj[0].fields.<campo>`; a chave especial `id` filtra por `object_id`.
5. **Dado** um usuário sem `eauth.list_auditlog`, **Quando** acessa `/admin/auditlog`, **Então** acesso negado.

---

### Casos de Borda

- **Auditoria inoperante**: a função do sinal só prossegue se `sender._meta.app_config.name[:10] == 'backend'` (tupla `('backend',)`). Como os apps são `backend.eauth`, `backend.utils`, `backend.api`, `backend.globalrules`, o prefixo de 10 caracteres nunca é igual a `'backend'`; **nenhum** `AuditLog` é gravado hoje.
- Mesmo se o filtro fosse corrigido: a ausência de `request` na pilha (shell, Celery, comandos) **não** impede o registro (grava com `user=None`, `email=''`); usuário anônimo também resulta em `user=None` (o teste `is_anonymous` nunca é alcançado porque `AnonymousUser` não tem `_meta`); a pilha de chamadas (`str` do frame) é gravada em `obj[0]['stack']`; a operação `P` (Pesquisa) existe nas choices mas nunca é gerada.
- **Página de auditoria quebrada**: `PesquisarAuditLogView` resolve o template `eauth/auditlog_filter.html`, que **não existe** em `_templates/eauth/` — a página levanta `TemplateDoesNotExist`.
- `AuditLogFilterSet.user` avalia `get_username()` na importação do módulo (consulta ao banco no carregamento das URLs; retorna `[]` se a consulta falhar, ex.: antes de `migrate`) e a lista não se atualiza até reiniciar; `model_name` usa `distinct('model_name')` (somente PostgreSQL).
- `filter_busca` espera pares `k=v` separados por vírgula; um termo sem `=` provoca erro de desempacotamento (HTTP 500).
- **Recuperação de senha revela existência da conta** (enumeração de usuários) e verifica e-mail com comparação exata, enquanto o envio usa `iexact` e só usuários ativos; usuário inativo vê sucesso mas não recebe e-mail.
- Se `email` não vier no POST (com reCAPTCHA presente), `RecuperarSenhaForm.clean` acessa `self.data['email']` e falha com `MultiValueDictKeyError`.
- O template do e-mail estende `base_email.html`, que **não existe** no repositório; e `settings/email.py` está vazio (backend SMTP padrão do Django em `localhost:25`): o envio real exige que o derivado do projeto forneça ambos.
- O template `recuperar_senha_email_form.html` acrescenta o `<script>` de `https://www.google.com/recaptcha/api.js` no bloco `head_content`, **que não existe** em `_templates/base.html`; portanto o script não é emitido e o widget do reCAPTCHA não é renderizado na tela, a menos que o projeto derivado defina esse bloco (ou carregue o script de outra forma).
- Sem chaves de reCAPTCHA (`GOOGLE_RECAPTCHA_*` vazias) a recuperação nunca valida (sempre erro).
- `LoginForm.password` limita a 30 caracteres: senhas mais longas nunca autenticam pelo login, embora outros formulários aceitem até 50.
- Na edição do próprio perfil, a senha atual só é verificada **se informada**: preencher apenas nova senha + confirmação altera a senha sem exigir a atual.
- `UserManager._create_user` engole qualquer exceção de `save()` e devolve o usuário já existente com o mesmo e-mail (`get_by_natural_key`), em vez de erro de duplicidade; se não existir, a exceção `DoesNotExist` surge.
- `BackendPasswordResetEncaminhadoView` (`/user/recuperar-senha/finalizado`) herda de `PasswordResetView`: um POST direto nessa URL aciona o fluxo padrão do Django sem reCAPTCHA.
- As rotas usam `re_path` sem âncora final (`^login`, `^logout`, `^user/edit`): qualquer caminho que **comece** com esses prefixos casa. A ordem importa: `email`, `finalizado` e `completo` precisam ser avaliados de modo que não sejam capturados por `recuperar_senha_confirma` (que exige `<uidb64>/<token>`).
- `User.get_absolute_url()` devolve uma tupla `('users_profile', [pk], {})` (padrão antigo de `permalink`), não uma URL; `users_profile` não existe como rota.
- `User.Meta.permissions = PERMS_FOR_USERS` (de `backend/globalrules`) cria `menu_1` ("Mostrar Menu 1") e `orcamento_1` ("Ação 1") no modelo `User`; o menu administrativo é protegido pela permissão `eauth.menu_1`.
- `BackendUserAdminForm` contém muito código comentado (`areatrabalho`, `autor`) herdado de outro projeto; o campo `token` é somente leitura e só tem valor se o usuário já possui `auth_token`.
- `LOGIN_URL = "/login/?next="`: o Django substitui o parâmetro `next` já existente, resultando em `/login/?next=<rota>`.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**Modelo de usuário e configuração**

- **FR-001**: O projeto DEVE definir `AUTH_USER_MODEL = "eauth.User"`, `LOGIN_REDIRECT_URL = "/"`, `LOGIN_URL = "/login/?next="` e `LOGOUT_REDIRECT_URL = "/"` em `backend/settings/auth.py`.
- **FR-002**: O modelo `User` DEVE usar o e-mail (único) como `USERNAME_FIELD`, estender `AbstractBaseUser`, `SearchModelMixin` e `PermissionsMixin`, e conter `first_name`, `last_name` (30 caracteres, opcionais), `is_staff`, `is_active` (padrão `True`), `date_joined`, `avatar` (`ImageCropField`, até 10 MiB) e `avatar_cropping` (`ImageRatioField` 128x128).
- **FR-003**: `User` DEVE manter o campo de busca `search` indexado a partir de `first_name`, `last_name` e `email` (via `SearchModelMixin`, feature 001/004).
- **FR-004**: `UserManager` DEVE fornecer `create_user` (sem privilégios) e `create_superuser` (`is_staff` e `is_superuser`), exigir e-mail, normalizá-lo e definir a senha com hash; DEVE funcionar com `createsuperuser`.
- **FR-005**: `User.Meta` DEVE ordenar por `-is_superuser`, `first_name`, `last_name`, ter `verbose_name` "Usuário"/"Usuários" e `permissions = PERMS_FOR_USERS`.
- **FR-006**: DEVEM existir os auxiliares `groups_add_user(user, nomes)` e `groups_remove_user(user, nomes)` que aceitam nome único ou lista, criam o grupo se não existir (`get_or_create`) e ignoram nomes vazios.
- **FR-007**: Os validadores de senha DEVEM ser `MinimumLengthValidator` (mínimo 6), `UserAttributeSimilarityValidator`, `CommonPasswordValidator` e `NumericPasswordValidator`.
- **FR-008**: Todos os modelos de `eauth` DEVEM estar registrados no Django Admin (`/system/`) por `register_all_models_in_admin`.

**Login e logout**

- **FR-009**: `GET/POST /login` (nome `backend.eauth:login`) DEVE usar `BackendLoginView` com o template `eauth/user/login.html` e `LoginForm` (campos com classes `form-control`, placeholders traduzíveis, `max_length` 254 e 30).
- **FR-010**: O formulário de login DEVE mostrar uma única mensagem genérica "Usuário e/ou Senha inválidos." quando `form.errors` existir, e um link "Esqueci minha Senha" para `backend.eauth:recuperar_senha_email`.
- **FR-011**: `/logout` (nome `backend.eauth:logout`) DEVE usar `LogoutView` e encerrar a sessão por requisição `POST` (formulário com CSRF no menu do usuário em `_templates/base.html`).

**Recuperação de senha**

- **FR-012**: As rotas `user/recuperar-senha/email`, `.../finalizado`, `.../<uidb64>/<token>` e `.../completo` DEVEM existir com os nomes `recuperar_senha_email`, `recuperar_senha_finalizado`, `recuperar_senha_confirma` e `password_reset_complete`.
- **FR-013**: `RecuperarSenhaForm` DEVE combinar `GoogleRecapthaMixin` com `PasswordResetForm`, exigir `g-recaptcha-response` e validá-lo no endpoint `https://www.google.com/recaptcha/api/siteverify` com `GOOGLE_RECAPTCHA_SECRET_KEY`; mensagens: "Verificação do reCAPTCHA não efetuada." e "Ocorreu um erro na validação do reCAPTCHA.".
- **FR-014**: `RecuperarSenhaForm.clean` DEVE rejeitar e-mails inexistentes com "Não existe nenhum usuário cadastrado com este e-mail." (estado atual; ver research.md para a recomendação de correção).
- **FR-015**: `get_users(email)` DEVE retornar somente usuários ativos com e-mail igual (`iexact`).
- **FR-016**: O e-mail de recuperação DEVE usar o template `eauth/user/recuperar_senha_email.html` (texto e HTML) com link `https://{{ domain }}` + URL `recuperar_senha_confirma`.
- **FR-017**: A confirmação DEVE usar `NovaSenhaForm` (`SetPasswordForm` com layout crispy 6/6 e botão "Enviar"), template `eauth/user/nova_senha_form.html` e sucesso em `password_reset_complete`.
- **FR-018**: O template de formulário de e-mail DEVE declarar o carregamento de `https://www.google.com/recaptcha/api.js` (no bloco `head_content`; ver Casos de Borda) e o widget DEVE usar `GOOGLE_RECAPTCHA_SITE_KEY` (`div.g-recaptcha`).
- **FR-019**: As chaves `GOOGLE_RECAPTCHA_SITE_KEY` e `GOOGLE_RECAPTCHA_SECRET_KEY` DEVEM ser lidas do ambiente com padrão vazio.

**Edição de perfil**

- **FR-020**: `/user/edit` (nome `backend_user_change`) DEVE exigir login (`login_required`), editar sempre `request.user` e usar `crud/form.html`, `BackendUserChangeForm` e mensagens de atualização do CRUD.
- **FR-021**: `BackendUserChangeForm` DEVE editar `first_name`, `last_name`, `avatar`, `avatar_cropping` e os campos virtuais `current_password`, `new_password1`, `new_password2` (máx. 50), validar igualdade das novas senhas, validar a nova senha com os validadores do Django e rejeitar nova senha igual à atual; o título da página DEVE ser "<nome completo> (<e-mail>)".

**CRUD de usuários**

- **FR-022**: `UserCrud` (subclasse de `Crud`, feature 004) DEVE ser montado em `^admin/user/` com rotas `user_list`, `user_create`, `user_view`, `user_update`, `user_delete`.
- **FR-023**: Criação e edição DEVEM usar `BackendUserAdminForm` (e-mail, nomes, `is_active` Sim/Não, `token`, `new_password1/2`, `groups`, `user_permissions`); a edição DEVE receber `user_session`.
- **FR-024**: Na edição, `groups` e `user_permissions` DEVEM ser caixas de seleção múltipla listando primeiro os já atribuídos e depois os demais; as permissões ofertadas DEVEM ser restritas aos `app_label` dos apps em `settings.BACKEND_APPS`.
- **FR-025**: O botão "Renovar" (`#renovar-token`) em `eauth/user_form.html` DEVE chamar `POST {% url 'backend.api:recria_token' object.id %}` com `X-CSRFToken` e preencher `#id_token` com o token retornado.
- **FR-026**: A lista DEVE usar `ListWithSearchForm`, 100 itens por página, colunas `usuario` e `is_active` e ordenação `-is_superuser`, `-is_active`, `first_name`; o detalhe DEVE usar os layouts `UserDetail`/`UserCreate` de `_templates/eauth/layouts.yaml`.

**Auditoria**

- **FR-027**: DEVE existir o modelo `AuditLog` (usuário nulo/`SET_NULL`, e-mail, operação `U/C/D/P`, `timestamp` automático, `obj` JSON, `content_type`/`object_id`/`content_object`, `obj_id`, `model_name`, `app_name`), ordenado por `-id`.
- **FR-028**: Um receptor global de `post_save` e `post_delete` (`dispatch_uid='auditlog_post_signal'`), carregado em `EAuthConfig.ready()`, DEVE implementar a lógica descrita em plan.md (filtro por `name[:10]`, exclusão de `AuditLog`, busca do `request` na pilha, interrupção durante `migrate`, serialização JSON, falhas apenas logadas).
- **FR-029**: `AuditLogManager` DEVE oferecer `last_action_user()`, `first_action_user()` e `actions_users()`.
- **FR-030**: `/admin/auditlog` (nome `pesquisar_auditlog`) DEVE exigir `eauth.list_auditlog`, paginar 20 itens, assumir `timestamp=week` quando ausente e usar `AuditLogFilterSet` (filtros `user`, `busca`, `operation`, `model_name`, `timestamp`).
- **FR-031**: O sistema NÃO DEVE registrar auditoria do próprio `AuditLog` (evitar recursão).

**Integração**

- **FR-032**: A API REST DEVE expor os modelos de `eauth` automaticamente (`backend/api/views_eauth.py`, feature 005).
- **FR-033**: O menu administrativo DEVE apontar para `backend.eauth:user_list` e `backend.eauth:pesquisar_auditlog` (`_templates/menus/menu_administracao.yaml`, feature 004).
- **FR-034**: As URLs de `eauth` DEVEM ser incluídas em `backend/urls.py` na raiz (`path("", include("backend.eauth.urls"))`) com namespace `backend.eauth` (`app_name = EAuthConfig.name`).

### Entidades-Chave

- **User** (`eauth.User`): conta de acesso identificada por e-mail; possui grupos e permissões (`PermissionsMixin`), avatar com enquadramento e campo `search`.
- **AuditLog** (`eauth.AuditLog`): registro imutável de uma operação sobre um objeto (quem, quando, o quê, JSON do objeto).
- **Group / Permission** (Django auth): associados ao usuário; regras em `backend/globalrules` (feature 003).
- **Token de API** (`rest_framework.authtoken.Token`): credencial de API 1:1 por usuário, renovável pela tela de edição (feature 005).

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Após `migrate` + `createsuperuser`, é possível autenticar com o e-mail em `/login/` e `/system/` em até 1 minuto, sem edição manual de código.
- **SC-002**: 100% das tentativas de login inválidas exibem a mesma mensagem genérica, sem diferenciar e-mail inexistente de senha errada.
- **SC-003**: Um administrador cria um usuário com senha e grupo pelo CRUD em até 3 interações de formulário, e o novo usuário consegue entrar imediatamente.
- **SC-004**: 100% das senhas definidas por qualquer formulário (perfil, admin, recuperação) passam pelos validadores configurados (mínimo 6 caracteres, não puramente numérica, não comum).
- **SC-005**: Com chaves de reCAPTCHA e SMTP válidos, o fluxo completo de recuperação de senha (pedido → e-mail → nova senha → login) é concluído sem intervenção de administrador.
- **SC-006**: Rotas protegidas retornam redirecionamento ao login (anônimo) ou 403/negação (sem permissão) em 100% dos casos testados.
- **SC-007**: Para o estado atual, um teste automatizado comprova que `auditlog_signal_function` não grava registros (comportamento a preservar na reconstrução fiel) e outro que o modelo `AuditLog` é gravável manualmente com todos os campos.

## Premissas

- O ambiente tem PostgreSQL (a consulta `distinct('model_name')` não funciona em SQLite) e a feature `001-fundacao-projeto-django` já foi construída (settings modulares, `zenv`, `utilss.py`, `model_mixins.py`).
- A classe `Crud`, `CustomFormHelper`, `CustomFormLayout`, `form_actions`, `to_row`, `make_pagination` (feature 004), `PERMS_FOR_USERS`/`RP_*` e as permissões `list_<modelo>` (feature 003), as rotas `/api/` e `recriar-token` (feature 005) e o campo de avatar/miniaturas (feature 009) são fornecidos por outras features.
- A permissão `eauth.list_auditlog` não é concedida a nenhum grupo em `map_rules.py`; apenas superusuários a possuem.
- O envio real de e-mails depende de configuração (`EMAIL_*`) fornecida por quem derivar o esqueleto; `backend/settings/email.py` existe vazio.
- O template `base_email.html` e `eauth/auditlog_filter.html` não existem; a reconstrução fiel os mantém ausentes (ver `research.md` para a recomendação de criá-los).
- O app `backend.crud` não é um app instalado (não consta em `INSTALLED_APPS`); é uma biblioteca de código em `backend/crud/`.
