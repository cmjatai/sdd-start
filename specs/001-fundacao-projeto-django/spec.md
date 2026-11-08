# Especificação da Funcionalidade: Fundação do Projeto Django

**Branch da Funcionalidade**: `001-fundacao-projeto-django`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: núcleo do projeto Django — pacote de configurações `backend/settings/*`, `backend/{urls,asgi,wsgi,celery,context_processors}.py`, `manage.py`, `pyproject.toml` (dependências, grupos, pytest, coverage, ruff), `conftest.py`, `_tests/`, `backend/tests.py`, utilitários (`backend/utilss.py`, `backend/model_mixins.py`), app `backend.utils` (modelos `Teste` e `Metadata`, admin automático, template tags comuns), arquivos de qualidade do repositório (`.gitignore`, `.editorconfig`, `.prettierrc.json`, `.github/dependabot.yml`) e `__notebooks/`."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Subir o projeto configurado por ambiente (Prioridade: P1)

Uma pessoa desenvolvedora (ou o processo de implantação) obtém o código, informa as variáveis de ambiente (ou o arquivo `backend/.env`) e executa `python manage.py ...`, `runserver`, Gunicorn/Daphne ou Celery. O comportamento (modo de depuração, banco de dados, Redis, fuso horário, chave secreta) é decidido exclusivamente pela configuração externa, nunca por valores escritos no código.

**Por que esta prioridade**: sem um projeto Django que inicialize e leia a configuração de ambiente, nenhuma outra funcionalidade (autenticação, CRUD, API, tempo real, frontend, Docker) existe. É o MVP de toda a plataforma.

**Teste Independente**: com `SECRET_KEY`, `DATABASE_URL_DEV` e `DEBUG=True` definidos e um PostgreSQL acessível, `python manage.py check` conclui com "System check identified no issues" e `python manage.py migrate` aplica as migrações iniciais.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e `DATABASE_URL_DEV` definida, **Quando** o Django carrega as configurações, **Então** `DATABASES["default"]` é construído a partir de `DATABASE_URL_DEV`.
2. **Dado** `DEBUG` ausente ou `False`, **Quando** o Django carrega as configurações, **Então** `DATABASES["default"]` é construído a partir de `DATABASE_URL_PRD`.
3. **Dado** `DEBUG=True` e a execução fora do contêiner da aplicação (isto é, `FOLDER_DEBUG_CONTAINER` diferente do diretório do projeto), **Quando** as configurações são carregadas, **Então** o host do banco é forçado para `localhost`, a porta para `5433`, e três mensagens informativas são impressas no console.
4. **Dado** que `SECRET_KEY` (ou a URL de banco do modo corrente) não está definida, **Quando** o Django carrega as configurações, **Então** a inicialização falha com erro explícito do `python-decouple` (não existe valor padrão).
5. **Dado** o arquivo `backend_data/.env` existente ao lado do diretório do projeto (cenário de produção em contêiner), **Quando** as configurações são carregadas, **Então** as variáveis são lidas desse arquivo, e não de `backend/.env`.
6. **Dado** nenhuma definição de `TZ`, **Quando** as configurações são carregadas, **Então** `LANGUAGE_CODE` é `pt-br`, `TIME_ZONE` é `America/Sao_Paulo`, `USE_I18N` e `USE_TZ` são verdadeiros.

---

### História de Usuário 2 - Configurações modulares, apps, middleware e roteamento raiz (Prioridade: P1)

A pessoa desenvolvedora encontra as configurações divididas em módulos temáticos reunidos por um único ponto de entrada (`backend.settings`), os apps e o middleware em listas ordenadas, o roteamento raiz do projeto (admin, API, autenticação, utilitários, página inicial), e os pontos de entrada ASGI, WSGI e Celery.

**Por que esta prioridade**: define o esqueleto sobre o qual todas as outras funcionalidades se encaixam (cada feature acrescenta seu módulo de settings, seu app e suas rotas).

**Teste Independente**: `python manage.py check` e `python manage.py makemigrations --check --dry-run` passam; `python -c "import backend.celery"` expõe `backend.celery_app`; uma requisição `GET /` retorna a página inicial.

**Cenários de Aceitação**:

1. **Dado** o pacote `backend.settings`, **Quando** `import backend.settings` é executado, **Então** todas as configurações dos módulos temáticos (`apps`, `auth`, `drf`, `email`, `frontend`, `languages`, `logs`, `medias`, `middleware`, `solr`, `zasyncs`) estão disponíveis como atributos do módulo.
2. **Dado** `DJANGO_SETTINGS_MODULE` não definido, **Quando** `manage.py`, `asgi.py`, `wsgi.py` ou `celery.py` iniciam, **Então** assumem `backend.settings` por padrão.
3. **Dado** o servidor em execução, **Quando** o navegador acessa `/system/`, **Então** a administração do Django é exibida.
4. **Dado** o servidor em execução, **Quando** o navegador acessa `/`, **Então** é renderizado o template `index.html` (rota de nome `index`), depois de as rotas de `backend.api`, `backend.eauth` e `backend.utils` terem tido chance de responder.
5. **Dado** `DEBUG=True` e `DEBUG_TOOLBAR_ACTIVE=True`, **Quando** as configurações são carregadas, **Então** `debug_toolbar` é adicionado aos apps e ao final do middleware, e a rota `/__debug__/` é registrada.
6. **Dado** `DEBUG=True`, **Quando** as URLs são carregadas, **Então** os arquivos estáticos de `STATIC_ROOT` são servidos em `STATIC_URL` pelo próprio Django.
7. **Dado** um processo Celery iniciado com `-A backend`, **Quando** o app Celery carrega, **Então** lê as chaves `CELERY_*` das configurações do Django e descobre automaticamente as tarefas de todos os apps instalados.
8. **Dado** uma conexão WebSocket, **Quando** ela chega ao ASGI, **Então** é encaminhada para as rotas de `backend.utils.routing.websocket_urlpatterns` com a autenticação de sessão do Channels (detalhes na feature `006-sincronizacao-tempo-real`).

---

### História de Usuário 3 - Registro de logs e diagnóstico de falhas (Prioridade: P2)

Quem opera o sistema precisa de logs consistentes: arquivo rotativo, saída de console em depuração, URL da requisição em cada linha de log quando disponível e captura de exceções não tratadas.

**Por que esta prioridade**: não impede o sistema de funcionar, mas é essencial para diagnosticar falhas em desenvolvimento e produção.

**Teste Independente**: iniciar qualquer comando Django com `logs/` existente e verificar que `logs/backend_logger.log` é criado e que `logging.getLogger("backend").error("x")` grava uma linha no arquivo.

**Cenários de Aceitação**:

1. **Dado** `LOGGING_ROOT_LEVEL` não definida, **Quando** as configurações são carregadas, **Então** o nível raiz é `DEBUG` se `DEBUG=True` e `INFO` caso contrário.
2. **Dado** um log emitido durante o tratamento de uma requisição HTTP, **Quando** a linha é formatada, **Então** o caminho (`request.path`) da requisição é anexado ao final da linha após ` - `.
3. **Dado** `DEBUG=False`, **Quando** um log é emitido, **Então** ele é gravado apenas no arquivo (o handler de console só emite com `DEBUG=True`).
4. **Dado** o arquivo `logs/backend_logger.log` com 15 MB, **Quando** novas linhas são gravadas, **Então** ele é rotacionado, mantendo até 10 arquivos de backup.
5. **Dado** uma exceção que escapa a qualquer tratamento no processo, **Quando** o interpretador a captura, **Então** ela é registrada com nível ERROR (tipo, valor e pilha) e impressa no console.

---

### História de Usuário 4 - Utilitários e mixins reutilizáveis (Prioridade: P2)

Pessoas desenvolvedoras de qualquer app reutilizam funções auxiliares (formatação decimal, normalização de texto, hash, tipos MIME, SQL cru, supressão de sinais, medição de tempo, etc.), mixins de modelo (datas, auditoria, busca, validação de unicidade com nulos, salvamento de arquivos) e template tags/filtros comuns.

**Por que esta prioridade**: reduz duplicação e é pré-requisito de várias features (autenticação usa `SearchModelMixin`, `YES_NO_CHOICES`, `show_results_filter_set`; CRUD e API usam `normalize`, `clean_text`, `get_mime_type_from_file_extension`; regras globais usam `dict2attr`).

**Teste Independente**: importar `backend.utilss` e `backend.model_mixins` em `manage.py shell` e exercitar cada helper; renderizar um template que carregue `{% load common_tags %}` e use os filtros listados nos contratos.

**Cenários de Aceitação**:

1. **Dado** `Decimal("1234.565")`, **Quando** `decimal2str(valor)` é chamado em `pt-br`, **Então** retorna `"1.234,56"` (arredondamento `ROUND_HALF_DOWN`, agrupamento de milhar ativo).
2. **Dado** um valor que não é número, **Quando** `decimal2str` é chamado, **Então** um erro é registrado no logger e o valor original é devolvido como `str`.
3. **Dado** o texto `"Ação ç"`, **Quando** `normalize` é chamado, **Então** retorna `"Acao c"` (ASCII sem acentos).
4. **Dado** um nome de arquivo `relatorio.odt`, **Quando** `get_mime_type_from_file_extension` é chamado, **Então** retorna `application/vnd.oasis.opendocument.text`; para `x.pdf` retorna `application/pdf` (qualquer outra extensão vira `application/<extensão>`, sem normalizar caixa).
5. **Dado** um modelo que herda `SearchModelMixin` com `fields_search`, **Quando** ele é salvo, **Então** o campo `search` é recomposto concatenando os campos e normalizado sem acentos.
6. **Dado** um modelo com `CleanModelMixin` e `unique_together` contendo campo nulo, **Quando** é salvo duplicando a combinação, **Então** uma `ValidationError` é levantada (o banco não detecta duplicidade com `NULL`).
7. **Dado** o bloco `with DisableSignals():`, **Quando** modelos são salvos dentro dele, **Então** os sinais `pre_init`, `post_init`, `pre_save`, `post_save`, `pre_delete`, `post_delete`, `pre_migrate`, `post_migrate` e `m2m_changed` não disparam, e são restaurados ao sair.
8. **Dado** um template com `{% load common_tags %}`, **Quando** os filtros/tags são usados, **Então** produzem os resultados descritos em `contracts/utilitarios.md`.
9. **Dado** um módulo `admin.py` de app que chama `register_all_models_in_admin(__name__)`, **Quando** o admin carrega, **Então** todos os modelos do app ainda não registrados são registrados no admin.

---

### História de Usuário 5 - Modelos base do app `utils` e migração inicial (Prioridade: P2)

O app `backend.utils` fornece o modelo `Teste` (exemplo/ensaio do CRUD genérico e das tarefas Celery) e o modelo `Metadata` (metadados JSON anexáveis a qualquer objeto por chave genérica), com a migração inicial `0001_initial`.

**Por que esta prioridade**: valida ponta a ponta o ciclo modelo → migração → admin → permissões e fornece um recurso de metadados usado pela API (feature 005).

**Teste Independente**: `python manage.py migrate utils` cria as tabelas `utils_teste` e `utils_metadata`; no admin (`/system/`) ambos aparecem registrados; `Metadata.objects.set_or_update_metadata(obj, {"a": 1})` cria e depois atualiza o registro.

**Cenários de Aceitação**:

1. **Dado** um objeto qualquer persistido, **Quando** `Metadata.objects.set_or_update_metadata(obj, {"a": 1})` é chamado pela primeira vez, **Então** um `Metadata` é criado com `content_type` e `object_id` do objeto.
2. **Dado** um `Metadata` existente, **Quando** `set_or_update_metadata(obj, {"b": 2})` é chamado, **Então** o JSON passa a conter `{"a": 1, "b": 2}` (mescla, não substitui).
3. **Dado** um objeto sem metadado, **Quando** `Metadata.objects.get_metadata(obj)` é chamado, **Então** retorna `None`.
4. **Dado** dois `Metadata` com o mesmo par (`content_type`, `object_id`) com valores não nulos, **Quando** o segundo é salvo, **Então** o banco rejeita por unicidade.
5. **Dado** registros de `Teste`, **Quando** listados, **Então** vêm ordenados por `teste`, e `str(obj)` é o texto do campo `teste`.

---

### História de Usuário 6 - Qualidade verificável e ferramentas do repositório (Prioridade: P3)

A equipe executa testes (`pytest`), lint (`ruff check .`), cobertura e formata código conforme as convenções do repositório; dependências são declaradas em `pyproject.toml` e atualizadas semanalmente pelo Dependabot; cadernos Jupyter permitem explorar o projeto com o Django carregado.

**Por que esta prioridade**: sustenta a evolução segura, mas não altera o comportamento em tempo de execução.

**Teste Independente**: `pytest` coleta e passa os testes existentes; `ruff check .` executa (com achados legados); abrir `__notebooks/0init_file.ipynb` e executar a primeira célula inicializa o Django.

**Cenários de Aceitação**:

1. **Dado** o ambiente com PostgreSQL acessível, **Quando** `pytest` é executado na raiz, **Então** arquivos `**/tests.py` e `**/test_*.py` são coletados, o banco de teste é reaproveitado (`--reuse-db`) e a cobertura é calculada.
2. **Dado** a fixture `app` de `conftest.py`, **Quando** um teste a usa, **Então** recebe um cliente WebTest já autenticado como `admin_user`, que segue redirecionamentos automaticamente em `GET`.
3. **Dado** arquivos `.env`, `*.log`, `node_modules/`, `security.json`, `db.sqlite3`, **Quando** `git status` é executado, **Então** eles não aparecem como não rastreados (estão no `.gitignore`).
4. **Dado** um arquivo `.js/.ts/.vue`, **Quando** aberto em editor com EditorConfig, **Então** usa UTF-8, indentação de 2 espaços, LF final e remoção de espaços à direita.
5. **Dado** um notebook de `__notebooks/`, **Quando** a primeira célula (`import django_setup`) é executada, **Então** `django.setup()` é chamado com `DJANGO_SETTINGS_MODULE=backend.settings`.

---

### Casos de Borda

- **`SESSIONS_COOKIE_SECURE` sem efeito**: `project.py` define `SESSIONS_COOKIE_SECURE = not DEBUG`, nome inexistente no Django (o correto é `SESSION_COOKIE_SECURE`). O cookie de sessão **não** é marcado como `Secure` mesmo em produção.
- **`backend/settings/email.py` está vazio**: não há `EMAIL_BACKEND`/`EMAIL_HOST*`; vale o padrão do Django (SMTP em `localhost:25`). Envios de e-mail (ex.: recuperação de senha, feature 002) tentam esse SMTP.
- **`ALLOWED_HOSTS = ["*"]`** e `CSRF_TRUSTED_ORIGINS = [SITE_URL]` (`SITE_URL` padrão `http://192.168.15.9:9001`): o esqueleto aceita qualquer `Host`.
- **Debug fora do contêiner**: com `DEBUG=True`, o banco é forçado para `localhost:5433` mesmo que `DATABASE_URL_DEV` aponte para outro host/porta (somente host e porta são sobrescritos; usuário, senha e nome vêm da URL). O mesmo `FOLDER_DEBUG_CONTAINER` também força `REDIS_HOST="localhost"` (`zasyncs.py`) e decide o host do Solr (`solr.py`).
- **Variáveis sem padrão**: `SECRET_KEY` e `DATABASE_URL_DEV`/`DATABASE_URL_PRD` (conforme `DEBUG`) são obrigatórias.
- **`DEBUG` padrão `False`**: sem `.env`, o projeto sobe em modo "produção" e exige `DATABASE_URL_PRD`.
- **`DEBUG_TOOLBAR_ACTIVE`** só tem efeito com `DEBUG=True` e, segundo o comentário do código, não funciona no contêiner de desenvolvimento (precisa de `runserver` no host).
- **Diretório `logs/`**: o handler de arquivo usa o caminho relativo `logs/backend_logger.log`; se a pasta `logs/` não existir no diretório de trabalho, o carregamento das configurações falha com `FileNotFoundError`. A pasta não é versionada (`*.log` e `*.pid` estão no `.gitignore`); o Docker a cria (`mkdir -p ${HOME}/logs/celery`).
- **`MyFormatter`** percorre toda a pilha de chamadas (`inspect.stack()`) procurando qualquer variável local chamada `request`; é custoso e pode anexar o caminho de uma requisição que não é a da linha de log.
- **`backend/tests.py` e `_tests/test_initials.py` duplicam** o mesmo teste (`test_app_init_files_have_default_app_config`), que na prática **não verifica nada**: itera diretórios da raiz do repositório (`.`) e só valida os que, com o prefixo `backend.`, estão em `INSTALLED_APPS` — nenhum diretório da raiz satisfaz isso. Ambos passam sempre.
- **`backend/crud/__init__.py`** define `default_app_config = 'backend.utils.apps.CrudConfig'` (classe inexistente) e `backend.crud` não está em `INSTALLED_APPS`; `default_app_config` é ignorado no Django ≥ 4.1, portanto sem efeito.
- **`backend.settings.fake`** reutiliza todo `project.py` (portanto ainda exige `SECRET_KEY` e `DATABASE_URL_*` definidos), mas troca o banco por SQLite (`db.sqlite3` na raiz) e força `DEBUG=False` e `DJANGO_VITE_DEV_MODE=False`; destina-se ao `collectstatic` na construção da imagem (feature 011).
- **`SaveModelWithFileMixin`** chama `super().save(force_insert, force_update, using, update_fields)` com argumentos posicionais; no Django 6 `Model.save` aceita apenas argumentos nomeados, portanto o primeiro `save()` de um objeto novo levantaria `TypeError`. O mixin não é usado por nenhum modelo do projeto.
- **`decimal2str`** nunca propaga exceção: loga o erro e devolve `str(value)`.
- **`get_mime_type_from_file_extension`** não normaliza caixa (`a.PDF` → `application/PDF`) e tem um `TODO` para usar detecção real de MIME.
- **Filtros `common_tags`** frágeis: `to_dict`, `settings_key_*`, `lookup` etc. não tratam entradas inválidas; `get_class` aceita `"app_label.Model"` e cai para importação por módulo se a busca no `ContentType` falhar.
- **`backend/utils/templatetags/`** não possui `__init__.py` (pacote de namespace); o Django ainda descobre a biblioteca `common_tags`.
- **`.github/dependabot.yml`** repete a chave `updates:` seis vezes no mesmo documento YAML; na prática só o último bloco (`pip`) é considerado de forma confiável.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**Configuração e ambiente**

- **FR-001**: O sistema DEVE ler toda configuração variável por `python-decouple` (`AutoConfig`) a partir de variáveis de ambiente ou de um arquivo `.env`, e NÃO DEVE conter segredos no código.
- **FR-002**: O sistema DEVE procurar o `.env` em `backend_data/.env` (diretório irmão do diretório do projeto) quando esse arquivo existir (flag `production` em `backend/settings/zenv.py`); caso contrário DEVE usar a busca padrão do `AutoConfig` (que encontra `backend/.env`).
- **FR-003**: O sistema DEVE expor `DEBUG` (padrão `False`), `BASE_DIR` (`backend/`), `PROJECT_DIR` (raiz do repositório) e `FOLDER_DEBUG_CONTAINER` (padrão: caminho do próprio `zenv.py`) a partir de `backend/settings/zenv.py`.
- **FR-004**: O sistema DEVE exigir `SECRET_KEY` sem valor padrão.
- **FR-005**: O sistema DEVE montar `DATABASES["default"]` com `dj_database_url.parse` a partir de `DATABASE_URL_DEV` quando `DEBUG` for verdadeiro e de `DATABASE_URL_PRD` caso contrário.
- **FR-006**: Quando `DEBUG` for verdadeiro e `FOLDER_DEBUG_CONTAINER != PROJECT_DIR`, o sistema DEVE sobrescrever `HOST` por `"localhost"` e `PORT` por `5433` e imprimir "Running in debug mode with local database settings.", "Database host:" e "Database port:".
- **FR-007**: O sistema DEVE definir `ALLOWED_HOSTS = ["*"]`, `SITE_URL` (variável `SITE_URL`, padrão `http://192.168.15.9:9001`) e `CSRF_TRUSTED_ORIGINS = [SITE_URL]`.
- **FR-008**: O sistema DEVE definir `PROJECT_VERSION = "0.0.1"`, `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`, `ROOT_URLCONF = "backend.urls"`, `ASGI_APPLICATION = "backend.asgi.application"` e `WSGI_APPLICATION = "backend.wsgi.application"`.
- **FR-009**: O sistema DEVE expor `DEBUG_TOOLBAR_ACTIVE` (variável, padrão `False`) e `DEBUG_RUNNING_CONTAINER` (`DEBUG` e `"/var/project"` contido em `PROJECT_DIR`); com `DEBUG` e `DEBUG_TOOLBAR_ACTIVE` verdadeiros DEVE acrescentar `debug_toolbar` a `INSTALLED_APPS` e `debug_toolbar.middleware.DebugToolbarMiddleware` ao final de `MIDDLEWARE`.
- **FR-010**: Com `DEBUG` verdadeiro o sistema DEVE definir `INTERNAL_IPS = ("127.0.0.1",)` e `NOTEBOOK_ARGUMENTS = ["--notebook-dir", "__notebooks"]` (usado por `shell_plus --notebook` do `django-extensions`).
- **FR-011**: O sistema DEVE manter o nome incorreto `SESSIONS_COOKIE_SECURE = not DEBUG` em `project.py` (comportamento atual: sem efeito sobre `SESSION_COOKIE_SECURE`); a reconstrução fiel replica o nome, a recomendação é corrigi-lo (ver `research.md`).

**Módulos de configuração**

- **FR-012**: O sistema DEVE dividir as configurações nos módulos `apps`, `auth`, `drf`, `email`, `frontend`, `languages`, `logs`, `medias`, `middleware`, `solr`, `zasyncs` e `zenv` em `backend/settings/`, reunidos por `project.py` (via `import *`) e reexportados por `backend/settings/__init__.py` (`from .project import *`).
- **FR-013**: O sistema DEVE manter `backend/settings/email.py` como módulo vazio (sem configurações de e-mail).
- **FR-014**: O sistema DEVE registrar em `INSTALLED_APPS`, nesta ordem: apps centrais do Django e utilitários (`daphne`, `channels`, `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `django_extensions`, `django.forms`, `django_vite`), apps de terceiros (`crispy_forms`, `crispy_bootstrap5`, `easy_thumbnails`, `image_cropping`, `django_celery_beat`, `django_celery_results`, `haystack`, `celery_haystack`, `drf_spectacular`, `rest_framework`, `django_filters`, `rest_framework.authtoken`), `backend.eauth`, `backend.utils`, `backend.api`, `backend.globalrules`.
- **FR-015**: O sistema DEVE configurar `MIDDLEWARE` na ordem: `SecurityMiddleware`, `SessionMiddleware`, `CommonMiddleware`, `CsrfViewMiddleware`, `AuthenticationMiddleware`, `MessageMiddleware`, `XFrameOptionsMiddleware`, `LocaleMiddleware`.
- **FR-016**: O sistema DEVE definir `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE` a partir da variável `TZ` (padrão `America/Sao_Paulo`), `USE_I18N = True`, `USE_TZ = True`.
- **FR-017**: O sistema DEVE definir `backend.settings.fake` que importa `project` e substitui `DEBUG=False`, `DJANGO_VITE_DEV_MODE=False`, o banco por SQLite em `PROJECT_DIR/db.sqlite3` e `DJANGO_VITE` com `manifest_path` em `DJANGO_VITE_ASSETS_PATH/frontend/.vite/manifest.json`.

**Logs**

- **FR-018**: O sistema DEVE definir `LOGGING_ROOT_LEVEL` (variável; padrão `DEBUG` se `DEBUG` senão `INFO`) e a configuração `LOGGING` com handlers `console` (somente com `DEBUG` verdadeiro, via filtro `require_debug_true`) e `backend_logger_file` (`RotatingFileHandler`, `logs/backend_logger.log`, 15 MB, 10 backups), formatador `verbose` baseado em `MyFormatter`, aplicados ao logger raiz e aos loggers `django`, `haystack` e `backend` (sem propagação).
- **FR-019**: O formatador `MyFormatter` DEVE anexar ` - <request.path>` à mensagem quando encontrar uma variável local `request` na pilha de chamadas.
- **FR-020**: O sistema DEVE instalar `sys.excepthook = uncaught_exceptions`, que registra (nível ERROR) e imprime tipo, valor e pilha de exceções não tratadas, e DEVE habilitar `logging.captureWarnings(True)`.

**Roteamento e pontos de entrada**

- **FR-021**: `backend/urls.py` DEVE expor, nesta ordem: `system/` (admin do Django), inclusão de `backend.api.urls`, `backend.eauth.urls`, `backend.utils.urls` na raiz `""`, e `""` → `TemplateView` de `index.html` com `name="index"`; com `DEBUG` e `DEBUG_TOOLBAR_ACTIVE` acrescenta `__debug__/`; com `DEBUG` acrescenta `static(STATIC_URL, document_root=STATIC_ROOT)`.
- **FR-022**: `backend/asgi.py` DEVE definir `application` como `ProtocolTypeRouter` com `http` (`ASGIHandler`) e `websocket` (`AuthMiddlewareStack(URLRouter(backend.utils.routing.websocket_urlpatterns))`), chamando `django.setup()` antes.
- **FR-023**: `backend/wsgi.py` DEVE definir `application = get_wsgi_application()`.
- **FR-024**: `backend/celery.py` DEVE criar `app = Celery("backend")`, ler `namespace="CELERY"` de `django.conf:settings` e chamar `autodiscover_tasks` com `settings.INSTALLED_APPS`; `backend/__init__.py` DEVE expor `celery_app`.
- **FR-025**: `manage.py` DEVE definir `DJANGO_SETTINGS_MODULE=backend.settings` por padrão e delegar a `execute_from_command_line`.
- **FR-026**: O sistema DEVE oferecer o context processor `backend.context_processors.debug`, que injeta `DEBUG` nos templates.

**Utilitários e mixins**

- **FR-027**: `backend/utilss.py` DEVE oferecer: `YES_NO_CHOICES`, `NONE_YES_NO_CHOICES`, `DECIMAL_PLACES`, `get_mime_type_from_file_extension`, `quantize`, `decimal2str`, `normalize`, `dict2attr`, `get_settings_auth_user_model`, `register_all_models_in_admin`, `save_in_metadata`, `run_sql`, `show_results_filter_set`, `pil_image`, `clean_text`, `intervalos_tem_intersecao`, `hash_sha512`, `DisableSignals`, `TimeExecution` e `FileFieldCheckMixin`, com o comportamento descrito em `plan.md` (Detalhamento de Implementação).
- **FR-028**: `backend/model_mixins.py` DEVE oferecer os mixins abstratos/auxiliares `DateModelMixin`, `AuditoriaModelMixin`, `SearchModelMixin`, `CleanModelMixin` e `SaveModelWithFileMixin`.
- **FR-029**: `register_all_models_in_admin(module_name)` DEVE resolver o app a partir do nome do módulo (`backend.<app>.admin` → `<app>`) e registrar no admin todos os modelos do app ainda não registrados.
- **FR-030**: `backend/utils/templatetags/common_tags.py` DEVE registrar a biblioteca `common_tags` com os filtros, tags simples e tags de inclusão listados em `contracts/utilitarios.md`.

**Modelos de `utils`**

- **FR-031**: O app `backend.utils` DEVE definir `UtilsConfig` (`name="backend.utils"`, `label="utils"`) que, em `ready()`, importa `backend.utils.services.signals` e `backend.utils.services.signals_syncrefresh` (o conteúdo desses módulos é coberto por `006-sincronizacao-tempo-real`).
- **FR-032**: O sistema DEVE definir o modelo `Teste` (campo `teste`, `CharField(100)`, ordenação por `teste`) e o modelo `Metadata` (`DateModelMixin` + `content_type`/`object_id`/`content_object`/`metadata`, unicidade `(content_type, object_id)`, gerenciador `MetadataManager` com `get_metadata` e `set_or_update_metadata`).
- **FR-033**: O sistema DEVE fornecer a migração `backend/utils/migrations/0001_initial.py` criando `Teste` e `Metadata` (dependência: `contenttypes.0002_remove_content_type_name`) e registrar ambos no admin por `backend/utils/admin.py`.

**Qualidade e repositório**

- **FR-034**: `pyproject.toml` DEVE declarar o projeto Poetry (`package-mode = false`, `requires-python = ">=3.12,<4.0"`), as dependências de produção, os grupos `dev`, `test` e `docs`, a configuração do pytest (`DJANGO_SETTINGS_MODULE = "backend.settings"`, `addopts = '--reuse-db -p no:warnings --cov=.'`, `testpaths = ["**/tests.py", "**/test_*.py"]`), do coverage (omitindo `_tests/*`, `backend/settings/*`, `backend/wsgi.py`, `backend/asgi.py`) e do ruff (`select = ["E", "F", "I"]`).
- **FR-035**: `conftest.py` DEVE fornecer a fixture `app` (escopo de função) que aplica e remove os patches de `WebTestMixin` e devolve `OurTestApp(default_user=admin_user.username)`, cujo `get` assume por padrão `user=default_user` e `auto_follow=True`.
- **FR-036**: O repositório DEVE conter `.gitignore` (ignorando ao menos `.env`, `*.log`, `db.sqlite3`, `node_modules/`, `.venv`, `.pytest_cache/`, `.coverage`, `.ruff_cache/`, `.vscode/`, `security.json`, `.eslintcache`, `__notebooks__private/`, `__private__/`, `.npm/`), `.editorconfig` e `.prettierrc.json` com as convenções descritas, e `.github/dependabot.yml` com atualização semanal de npm, docker, docker-compose e pip.
- **FR-037**: O repositório DEVE conter `__notebooks/django_setup.py` (inicializa o Django para notebooks) e os notebooks `0init_file.ipynb` e `shell_plusss.ipynb`, cuja primeira célula executa `import django_setup`.
- **FR-038**: Os testes `backend/tests.py::test_app_init_files_have_default_app_config` e `_tests/test_initials.py::test_app_init_files_have_default_app_config` DEVEM existir e passar (comportamento replicado; ver Casos de Borda).

### Entidades-Chave

- **Configuração de ambiente (`.env`/variáveis)**: pares chave/valor lidos por `decouple` (ex.: `DEBUG`, `SECRET_KEY`, `DATABASE_URL_DEV`, `DATABASE_URL_PRD`, `REDIS_HOST`, `REDIS_PORT`, `TZ`, `SITE_URL`, `LOGGING_ROOT_LEVEL`, `DEBUG_TOOLBAR_ACTIVE`, `FOLDER_DEBUG_CONTAINER`).
- **Teste**: registro simples com um texto (`teste`), usado como modelo de ensaio do CRUD e de tarefas.
- **Metadata**: metadados JSON associados a um objeto qualquer do sistema por (tipo de conteúdo, id do objeto); no máximo um por objeto; guarda data de criação/modificação.
- **Mixins de modelo**: `DateModelMixin`, `AuditoriaModelMixin`, `SearchModelMixin`, `CleanModelMixin`, `SaveModelWithFileMixin` — comportamento compartilhado por modelos de outros apps.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Com as variáveis mínimas (`SECRET_KEY`, `DATABASE_URL_DEV`, `DEBUG=True`) e PostgreSQL acessível, `python manage.py check` conclui sem problemas em menos de 10 segundos e `python manage.py makemigrations --check --dry-run` informa "No changes detected".
- **SC-002**: 100% das chaves de configuração variáveis do projeto são lidas de ambiente/`.env`; nenhum segredo aparece em arquivos versionados.
- **SC-003**: Alternar apenas `DEBUG` entre `True` e `False` troca a origem do banco (`DATABASE_URL_DEV` ↔ `DATABASE_URL_PRD`) sem alterar código.
- **SC-004**: `pytest` na raiz coleta exatamente os testes existentes (3 no estado atual: dois de `test_app_init_files_have_default_app_config` e `backend/crud/tests.py::test_read_layout_from_yaml`) e todos passam.
- **SC-005**: Todos os 20 itens públicos (constantes, funções e classes) de `backend/utilss.py` e os 5 mixins de `backend/model_mixins.py` descritos no plano são importáveis e se comportam conforme os cenários de aceitação.
- **SC-006**: `python manage.py migrate` aplica `utils.0001_initial` criando as tabelas `utils_teste` e `utils_metadata`, e `/system/` lista os dois modelos.
- **SC-007**: Qualquer linha de log emitida durante uma requisição HTTP inclui o caminho da requisição; exceções não tratadas ficam registradas em `logs/backend_logger.log`.
- **SC-008**: Iniciar um novo app seguindo a convenção (módulo em `backend/<app>/`, registro em `backend/settings/apps.py`, `admin.py` com `register_all_models_in_admin(__name__)`) expõe seus modelos no admin sem código adicional.

## Premissas

- O PostgreSQL de desenvolvimento é acessível em `localhost:5433` quando o código roda no host (porta publicada pelo Docker Compose da feature `010-docker-desenvolvimento`); testes e `manage.py` dependem desse banco.
- O arquivo `backend/.env` existe no ambiente de desenvolvimento (não versionado) com as chaves listadas em `contracts/settings-e-ambiente.md`; em produção o arquivo é `backend_data/.env`, gerado pelo `start.sh` do contêiner (feature `011-docker-producao`).
- A pasta `logs/` existe no diretório de trabalho (criada pelo Docker ou manualmente); a reconstrução DEVE garantir isso (ver tarefas).
- O tratamento de `FOLDER_DEBUG_CONTAINER` pelos scripts `start-dev.sh`/`start.sh` (que gravam `${HOME}` nessa chave do `.env`) pertence às features Docker (`010`, `011`).
- Os módulos `auth`, `drf`, `frontend`, `medias`, `solr`, `zasyncs` de `backend/settings/` são apenas referenciados aqui como parte da reunião em `project.py`; seu conteúdo é detalhado nas features `002-autenticacao-usuarios-auditoria`, `005-api-rest-automatica`, `007-frontend-vite-vue`, `009-midia-arquivos-avatar`, `008-busca-solr-haystack` e `006-sincronizacao-tempo-real`, respectivamente.
- As rotas de `backend.api.urls`, `backend.eauth.urls` e `backend.utils.urls`, o conteúdo de `index.html` e o consumidor WebSocket são tratados nas features `005`, `002`, `004`/`006` e `007`; esta feature só especifica como são montados na raiz.
- As permissões e regras para `Teste` e `Metadata` (`backend/globalrules/map_rules.py`) pertencem à feature `003-regras-permissoes-globais`; o CRUD `TesteCrud` pertence à `004-crud-generico-menus`.
- Python 3.12 é o mínimo suportado (a imagem-base usa 3.14); Django 6.0.x.
- O CORS não está configurado no projeto atual (não há `corsheaders`), embora a constituição o mencione como "aberto"; considera-se que isso é uma imprecisão documental, registrada em `research.md`.
