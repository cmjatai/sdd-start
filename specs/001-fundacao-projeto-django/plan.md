# Plano de Implementação: Fundação do Projeto Django

**Branch**: `001-fundacao-projeto-django` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/001-fundacao-projeto-django/spec.md`

**Nota**: Plano de engenharia reversa; descreve o código existente com precisão suficiente para recriá-lo.

## Resumo

Criar o núcleo do projeto Django `backend`: pacote de configurações modular lido por `python-decouple`, pontos de entrada (`manage.py`, ASGI, WSGI, Celery), roteamento raiz, logging customizado, utilitários e mixins compartilhados, template tags comuns, o app `backend.utils` (modelos `Teste` e `Metadata` + migração inicial + admin automático), e a infraestrutura de qualidade (pytest, coverage, ruff, `.gitignore`, EditorConfig, Prettier, Dependabot, notebooks). A abordagem é "configuração por ambiente": um único `backend/settings/project.py` reúne módulos temáticos e decide DEV/PRD via `DEBUG`.

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (ambiente local 3.12.16; imagem-base 3.14); Django 6.0.10 (`>=6,<7`)

**Dependências Principais** (versões do `poetry.lock`): Django 6.0.10, daphne 4.2.3, channels 4.3.2, channels-redis ^4.3, celery 5.7.0, django-celery-beat/results, python-decouple 3.8, dj-database-url 3.1.2, psycopg 3 (+pool), django-extensions 4.1, django-vite 3.2.0, djangorestframework 3.18.3, easy-thumbnails 2.10.1, num2words 0.5.14, python-dateutil (transitiva, usada em `common_tags`), pyyaml (logs/menus), django-haystack/celery-haystack (apenas referenciados nos logs e settings); ferramentas: ruff 0.17.4, pytest 9.2.0, pytest-django 4.14.0, pytest-cov 7.1.0, model-bakery 1.24.2, django-webtest 1.9.15; Poetry (`poetry-core>=2.0.0,<3.0.0`)

**Armazenamento**: PostgreSQL (único suportado em execução; `psycopg` 3), SQLite somente em `backend.settings.fake`; Redis para cache/Celery/Channels (módulo `zasyncs`)

**Testes**: pytest + pytest-django (`--reuse-db`, `-p no:warnings`, `--cov=.`), django-webtest (fixture `app`), model-bakery

**Plataforma Alvo**: servidor Linux (contêineres Docker; desenvolvimento também no host)

**Tipo de Projeto**: aplicação web (backend Django monorepo; frontend em `_frontend/` tratado na feature 007)

**Metas de Desempenho**: N/A (infraestrutura); `manage.py check` em poucos segundos

**Restrições**: nenhum segredo versionado; `SECRET_KEY` e URLs de banco sem padrão; `logs/` precisa existir no diretório de trabalho; testes exigem PostgreSQL acessível

**Escala/Escopo**: esqueleto reutilizável (starter); 2 modelos próprios; ~20 helpers; 39 filtros/tags registrados

## Verificação da Constituição

*PORTÃO (gate): Deve passar antes da pesquisa da Fase 0. Reverifique após o design da Fase 1.*

| # | Princípio | Situação | Evidência / Justificativa |
|---|-----------|----------|---------------------------|
| I | Backend Django modular e orientado a apps | ✅ Atendido | Settings divididos em módulos temáticos reunidos por `backend/settings/project.py`; apps em `backend/settings/apps.py`. Observação: `BACKEND_APPS` lista só `eauth` e `utils`; `api` e `globalrules` são acrescentados diretamente em `INSTALLED_APPS`, e `crud` não é app instalado (é biblioteca de views). Divergência cosmética, sem violação. |
| II | Configuração por ambiente, sem segredos | ✅ Atendido | `backend/settings/zenv.py` (`AutoConfig`), `.env` no `.gitignore`; `SECRET_KEY` sem padrão. Valor padrão `SITE_URL=http://192.168.15.9:9001` é apenas exemplo (não segredo). |
| III | Paridade DEV/PRD via Docker | ✅ Atendido (fora do escopo detalhado) | O núcleo decide DEV/PRD por `DEBUG`/`FOLDER_DEBUG_CONTAINER`; Docker está nas features 010/011. |
| IV | API REST gerada, permissões por modelo | ✅ Atendido (referência) | `utils.admin` registra modelos; permissões de `Teste`/`Metadata` em `globalrules/map_rules.py` (feature 003). |
| V | Frontend Vite integrado | ✅ Atendido (referência) | Config em `backend/settings/frontend.py` (feature 007); `.prettierrc.json`/`.editorconfig` garantem estilo (sem ponto e vírgula, aspas simples, 2 espaços). |
| VI | Tempo real e assíncrono | ✅ Atendido | `backend/asgi.py` (Channels) e `backend/celery.py` (Celery com autodiscover) presentes; `UtilsConfig.ready()` carrega os sinais. |
| VII | Português do Brasil | ✅ Atendido | `LANGUAGE_CODE="pt-br"`, `TIME_ZONE=America/Sao_Paulo`, `gettext_lazy` em `verbose_name`; comentários em PT-BR. |
| VIII | Qualidade verificável | ⚠️ Atendido com ressalvas | pytest/ruff/Poetry/Dependabot configurados. Ressalvas (justificadas em `research.md`): teste `test_app_init_files_have_default_app_config` vazio e duplicado; `ruff check .` reporta 119 achados legados; `dependabot.yml` com chave `updates` repetida. |

Restrições adicionais: stack coerente (Django >= 6 < 7, Python >= 3.12); "CORS aberto" da constituição não existe no código (sem `corsheaders`) — registrado em `research.md`. **Resultado do portão: PASSA** (sem violações que exijam Rastreamento de Complexidade).

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/001-fundacao-projeto-django/
├── plan.md              # Este arquivo
├── research.md          # Decisões e particularidades/dívidas técnicas
├── data-model.md        # Modelos Teste/Metadata, mixins, estruturas de configuração
├── quickstart.md        # Como validar a feature
├── contracts/
│   ├── settings-e-ambiente.md  # Variáveis de ambiente (decouple), chaves de settings, URLs raiz, ASGI/WSGI/Celery
│   └── utilitarios.md          # API pública de utilss.py, model_mixins.py e template tags (common_tags)
└── tasks.md             # Tarefas de reconstrução
```

### Código-Fonte (raiz do repositório)

```text
manage.py
pyproject.toml / poetry.lock
conftest.py
.gitignore  .editorconfig  .prettierrc.json
.github/dependabot.yml
__notebooks/
├── django_setup.py
├── 0init_file.ipynb
└── shell_plusss.ipynb
_tests/
├── __init__.py
└── test_initials.py
logs/                       # criada em runtime (não versionada); backend_logger.log, celery/
backend/
├── __init__.py             # expõe celery_app
├── asgi.py  wsgi.py  celery.py  urls.py  context_processors.py
├── tests.py                # duplicata de _tests/test_initials.py
├── utilss.py               # helpers
├── model_mixins.py         # mixins de modelo
├── settings/
│   ├── __init__.py         # from .project import *
│   ├── project.py          # ponto de reunião
│   ├── zenv.py  apps.py  middleware.py  languages.py  logs.py  email.py(vazio)
│   ├── auth.py  drf.py  frontend.py  medias.py  solr.py  zasyncs.py   # referenciados (outras features)
│   └── fake.py             # collectstatic com SQLite
└── utils/
    ├── __init__.py         # default_app_config = "backend.utils.apps.UtilsConfig"
    ├── apps.py  models.py  admin.py
    ├── migrations/{__init__.py, 0001_initial.py}
    ├── fixtures/           # diretório vazio
    └── templatetags/common_tags.py   # (+ menus.py: feature 004)
```

**Decisão de Estrutura**: monorepo Django "aplicação web" com pacote único `backend` na raiz do repositório, apps como subpacotes, configurações fatiadas por tema em `backend/settings/`, diretórios de apoio com prefixo `_`/`__` (`_tests`, `_templates`, `_frontend`, `_docker`, `__notebooks`) para ordená-los/segregá-los do código Python. Arquivos `backend/utils/consumers.py`, `routing.py`, `urls.py`, `views.py`, `forms.py`, `services/` e `templatetags/menus.py` pertencem a outras features.

## Detalhamento de Implementação

### 1. `backend/settings/zenv.py` — leitura de ambiente

1. `production = (Path(__file__).parents[3] / "backend_data" / ".env").exists()` — `parents[3]` é o diretório **pai** da raiz do repositório (ex.: `$HOME` no contêiner).
2. `config = AutoConfig(search_path=(Path(__file__).parents[3] / "backend_data") if production else None)` (`decouple.AutoConfig`; com `None` busca `.env`/`settings.ini` subindo a partir do diretório do módulo chamador — encontra `backend/.env`; variáveis de ambiente têm precedência sobre o arquivo).
3. `DEBUG = config("DEBUG", default=False, cast=bool)`.
4. `BASE_DIR = Path(__file__).parents[1]` (`backend/`); `PROJECT_DIR = Path(__file__).parents[2]` (raiz).
5. `FOLDER_DEBUG_CONTAINER = Path(config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str))`. Dentro do contêiner o `start*.sh` grava `${HOME}` (que coincide com `PROJECT_DIR`), de modo que `FOLDER_DEBUG_CONTAINER == PROJECT_DIR` identifica "rodando no contêiner".

### 2. `backend/settings/project.py` — reunião e valores transversais

- Imports na ordem (com `# noqa: F403`): `apps, auth, drf, email, frontend, languages, logs, medias, middleware, solr, zasyncs`; depois `from .zenv import BASE_DIR, DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config` e `from dj_database_url import parse as db_url`.
- Valores: `BASE_DIR = BASE_DIR` (redundante); `SECRET_KEY = config("SECRET_KEY")`; `DEBUG_TOOLBAR_ACTIVE = config("DEBUG_TOOLBAR_ACTIVE", default=False, cast=bool)`; `DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)`; `PROJECT_VERSION = "0.0.1"`; `ALLOWED_HOSTS = ["*"]`; `SITE_URL = config("SITE_URL", default="http://192.168.15.9:9001")`; `CSRF_TRUSTED_ORIGINS = [SITE_URL]`; `SESSIONS_COOKIE_SECURE = not DEBUG` (nome errado, preservar); `ROOT_URLCONF`, `ASGI_APPLICATION`, `WSGI_APPLICATION`, `DEFAULT_AUTO_FIELD`.
- `DATABASES = {"default": config("DATABASE_URL_DEV" if DEBUG else "DATABASE_URL_PRD", cast=db_url)}`; se `DEBUG and FOLDER_DEBUG_CONTAINER != PROJECT_DIR`: `DATABASES["default"]["HOST"]="localhost"`, `["PORT"]=5433` e três `print`.
- `if DEBUG and DEBUG_TOOLBAR_ACTIVE:` `INSTALLED_APPS += ["debug_toolbar"]` e `MIDDLEWARE = MIDDLEWARE + ["debug_toolbar.middleware.DebugToolbarMiddleware"]`.
- `if DEBUG:` `INTERNAL_IPS = ("127.0.0.1",)`; `NOTEBOOK_ARGUMENTS = ["--notebook-dir", "__notebooks"]`.
- `backend/settings/__init__.py`: uma linha `from .project import *`.

### 3. `backend/settings/apps.py`

Listas `DJANGO_CORE_APPS`, `DJANGO_THIRD_PARTY_APPS`, `BACKEND_APPS = ["backend.eauth", "backend.utils"]` e `INSTALLED_APPS = DJANGO_CORE_APPS + DJANGO_THIRD_PARTY_APPS + BACKEND_APPS + ["backend.api", "backend.globalrules"]` (ordem exata em FR-014). `daphne` precisa vir antes de `staticfiles` para que `runserver` use ASGI. Há um comentário preservado sobre `rest_framework_simplejwt` (não instalado).

### 4. `backend/settings/middleware.py`

`MIDDLEWARE` com 8 entradas na ordem de FR-015 (aspas simples no arquivo; `LocaleMiddleware` por último).

### 5. `backend/settings/languages.py`

`LANGUAGE_CODE="pt-br"`; `TIME_ZONE=config("TZ", default="America/Sao_Paulo")`; `USE_I18N=True`; `USE_TZ=True`. Sem `LANGUAGES`/`LOCALE_PATHS`.

### 6. `backend/settings/email.py`

Arquivo vazio (0 bytes). Importado por `project.py` sem efeito. Reconstrução fiel: criar vazio.

### 7. `backend/settings/fake.py`

`from .project import *`; `DEBUG=False`; `DJANGO_VITE_DEV_MODE=False`; `DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":os.path.join(PROJECT_DIR,"db.sqlite3")}}`; `DJANGO_VITE={"default":{"dev_mode":False,"manifest_path":DJANGO_VITE_ASSETS_PATH/"frontend"/".vite"/"manifest.json"}}` (`DJANGO_VITE_ASSETS_PATH` vem de `frontend.py`).

### 8. `backend/settings/logs.py`

1. `LOGGING_ROOT_LEVEL = config("LOGGING_ROOT_LEVEL", default="DEBUG" if DEBUG else "INFO", cast=str)`.
2. `logging.captureWarnings(True)`; `yaml.warnings({"YAMLLoadWarning": False})` (chamada herdada de versões antigas do PyYAML; funciona porque `yaml.warnings` existe como função).
3. `class MyFormatter(logging.Formatter)`: `__init__(fmt=None, datefmt=None, style="%")`; `format(record)`: `s = super-format`; para cada `i in inspect.stack()`: `r = i.frame.f_locals.get("request", None)`; se `r`: `url = r.path` (em `try/except` → `""`) e `return f"{s} - {url}"`; senão retorna `s`.
4. `LOGGING` (versão 1, `disable_existing_loggers=False`): filtros `require_debug_false`/`require_debug_true` (`django.utils.log.*`); formatadores `verbose` (`class: backend.settings.logs.MyFormatter`, formato `"%(levelname)s %(asctime)s %(name)s:%(funcName)s:%(lineno)d %(message)s"`) e `simple` (`"%(levelname)s %(asctime)s - %(message)s"`); handlers `console` (`StreamHandler`, `verbose`, filtro `require_debug_true`, nível `LOGGING_ROOT_LEVEL`) e `backend_logger_file` (`logging.handlers.RotatingFileHandler`, `filename="logs/backend_logger.log"`, `maxBytes=1024*1024*15`, `backupCount=10`, `verbose`); `root` e loggers `django`, `haystack`, `backend` com handlers `["backend_logger_file","console"]`, nível `LOGGING_ROOT_LEVEL`; os três loggers nomeados com `propagate=False`.
5. `uncaught_exceptions(type, value, error_traceback)`: `logger = logging.getLogger(__name__)`; `error_msg = "".join(traceback.format_tb(error_traceback))`; `logger.error(f"{type}\n{value}\n{error_msg}")`; `print(...)`. `sys.excepthook = uncaught_exceptions`.

### 9. `backend/urls.py`

`urlpatterns = [path("system/", admin.site.urls), path("", include("backend.api.urls")), path("", include("backend.eauth.urls")), path("", include("backend.utils.urls")), path("", TemplateView.as_view(template_name="index.html"), name="index")]`; `if settings.DEBUG and settings.DEBUG_TOOLBAR_ACTIVE: += [path("__debug__/", include("debug_toolbar.urls"))]`; `if settings.DEBUG: += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)`.

### 10. `backend/asgi.py` / `wsgi.py` / `celery.py` / `__init__.py` / `manage.py`

- `asgi.py`: importa `backend.utils.routing as backend_routing`; `os.environ.setdefault("DJANGO_SETTINGS_MODULE","backend.settings")`; `django.setup()`; `application = ProtocolTypeRouter({"http": ASGIHandler(), "websocket": AuthMiddlewareStack(URLRouter(backend_routing.websocket_urlpatterns))})`. Nota: o `import` de `backend.utils.routing` ocorre **antes** do `setdefault`/`django.setup()` (ordem do arquivo original; funciona porque `routing` não importa modelos no nível do módulo).
- `wsgi.py`: `setdefault` + `application = get_wsgi_application()`.
- `celery.py`: `app = Celery("backend")`; `app.config_from_object("django.conf:settings", namespace="CELERY")`; `app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)`.
- `backend/__init__.py`: `from .celery import app as celery_app` e `__all__ = ('celery_app',)`.
- `manage.py`: script padrão do Django com `setdefault("DJANGO_SETTINGS_MODULE","backend.settings")`; executável (`#!/usr/bin/env python`).
- `context_processors.py`: `def debug(request): return {"DEBUG": settings.DEBUG}` (import de `settings` dentro da função); registrado em `TEMPLATES` (`frontend.py`) como `backend.context_processors.debug`.

### 11. `backend/utilss.py` — API pública (ordem do arquivo)

| Item | Assinatura / comportamento |
|------|---------------------------|
| `logger` | `logging.getLogger(__name__)` |
| `YES_NO_CHOICES` | `[(True, _("Sim")), (False, _("Não"))]` |
| `NONE_YES_NO_CHOICES` | `[(None, _("---------")), (True, _("Sim")), (False, _("Não"))]` |
| `DECIMAL_PLACES` | `{i: Decimal(10) ** -i for i in range(0, 10)}` |
| `get_mime_type_from_file_extension(filename)` | extensão = parte após o último `.`; `odt` → `application/vnd.oasis.opendocument.text`; demais → `"application/%s" % ext` (sem normalizar caixa); `TODO` para usar detecção real |
| `quantize(value, decimal_places=2, rounding=ROUND_HALF_DOWN) -> Decimal` | `value.quantize(DECIMAL_PLACES[dp] se int, senão dp, rounding=rounding)` |
| `decimal2str(value, decimal_places=2, rounding=ROUND_HALF_DOWN, force_grouping=True, use_l10n=True) -> str` | `quantize(value, decimal_places=DECIMAL_PLACES[decimal_places], rounding=rounding)` e `formats.number_format(value, decimal_pos=decimal_places, use_l10n, force_grouping)`; qualquer exceção → `logger.error(...)` e `return str(value)` |
| `normalize(txt)` | `unicodedata.normalize("NFKD", txt).encode("ASCII","ignore").decode("ASCII")` |
| `dict2attr(value)` | cria subclasse local `d2a(dict)` cujo `__init__` faz `setattr` de cada chave; devolve instância atualizada com o dicionário (acesso por atributo e por chave) |
| `get_settings_auth_user_model()` | `getattr(settings, "AUTH_USER_MODEL", "auth.User")` |
| `register_all_models_in_admin(module_name)` | `parts = module_name.split(".")`; `appname = parts[1] if parts[0]=="backend" else parts[0]`; `app = apps.get_app_config(appname)`; para cada `model in app.get_models()` não registrado em `admin.site`, `admin.site.register(model)` |
| `save_in_metadata(obj, mdict=None)` | import tardio de `ContentType` e `Metadata`; `get_or_create(content_type=ContentType.objects.get_for_model(obj._meta.model), object_id=obj.id)`; **substitui** `md.metadata = mdict`; `save()`; devolve `md` |
| `run_sql(sql)` | executa em `connection.cursor()`, tenta `fetchall()` (ignora exceção) e devolve o resultado |
| `show_results_filter_set(qr)` | `query_params = set(qr.keys())`; `False` se vazio ou se for exatamente `{"iframe"}`; senão `True` |
| `pil_image(source, exif_orientation=False, **options)` | delega a `easy_thumbnails.source_generators.pil_image`; é referenciado por `THUMBNAIL_SOURCE_GENERATORS = ("backend.utilss.pil_image",)` (`medias.py`) |
| `clean_text(text, _normalizes=None)` | lista de pares (regex, substituição): `\n ?\d+ ?/ ?\d+ ?\n`→`\n`; `[ ]{2,}`→espaço; ` \n`→`\n`; `(\w)\n(.)`→`\1 \2`; `(,|\.)\n(.)`→`\1 \2`; `\n\n`→`\n`; `-\n`→`-`; `^\n`→``; `–`→`-`; `•`→`*`; `[“”]`→`"`. Cada regex é reaplicada em laço `while re.search` até não casar; qualquer exceção devolve o texto original |
| `intervalos_tem_intersecao(a_inicio, a_fim, b_inicio, b_fim)` | `max(inícios) <= min(fins)` (extremos inclusivos) |
| `hash_sha512(arquivo)` | aceita caminho (`str`, abre/fecha) ou objeto de arquivo binário; lê blocos de 4096 bytes; devolve `hexdigest()` |
| `DisableSignals(disabled_signals=None)` | gerenciador de contexto; padrão: `pre_init, post_init, pre_save, post_save, pre_delete, post_delete, pre_migrate, post_migrate, m2m_changed`; `__enter__` guarda `signal.receivers` em `stashed_signals` e zera; `__exit__` restaura e limpa `signal.sender_receivers_cache` |
| `TimeExecution(print_date=False)` | gerenciador de contexto; mede com `timezone.localtime()`; imprime início/fim se `print_date`; sempre imprime `"TimeExecution:", fim - início` |
| `FileFieldCheckMixin(BaseForm)` | `_check()`: para cada `FileField` com erro, reescreve a mensagem "Certifique-se de que o arquivo" → "Certifique-se de que o nome do arquivo no campo '<label>'"; se o valor limpo não for `UploadedFile` e `arquivo.path` não existir, acrescenta "Arquivo referenciado no campo '<label>' inexistente! Marque a opção Limpar e Salve."; levanta `ValidationError(errors)` se houver; `clean()` é alias de `_check()` |

### 12. `backend/model_mixins.py`

- `DateModelMixin` (abstrato): `created_at = DateTimeField(verbose_name=_("Criado em"), editable=False, auto_now_add=True)`; `modified_at = DateTimeField(verbose_name=_("Modificado em"), editable=False, auto_now=True)`.
- `AuditoriaModelMixin` (abstrato): `created_by` e `modified_by` = `ForeignKey(get_settings_auth_user_model(), verbose_name=_("Criado Por")/_("Modificado Por"), related_name="+", on_delete=PROTECT)`.
- `SearchModelMixin` (abstrato): `fields_search = []`; `search = TextField(blank=True, default="")`; `save(force_insert=False, force_update=False, using=None, update_fields=None, auto_update_search=True)`: se `auto_update_search`, reconstrói `search`: item `tuple` → concatena (sem separador, ignorando erros) os valores dos campos e acrescenta `" "`; item `str` sem `__` → `str(getattr(self, campo)) + " "` (erros ignorados); item com `__` → navega atributos encadeados (sem proteção de erros) e acrescenta valor + `" "`; `self.search = search.strip()`; sempre `self.search = normalize(self.search)`; chama `super().save(...)` com argumentos nomeados.
- `CleanModelMixin` (não abstrato, mixin puro): `clean()` chama `super().clean()` e, para cada tupla de `_meta.unique_together`, monta filtro com `campo__isnull=True` para valores `None`; se houver algum nulo, consulta `self.__class__.objects.filter(**filtro)` (excluindo `pk` próprio) e, se existir, levanta `ValidationError(self.unique_error_message(self.__class__, tuple(campos_não_nulos)))`; `save(..., clean=True)` chama `self.clean()` antes de salvar.
- `SaveModelWithFileMixin`: `FIELDFILE_NAME = ("arquivo",)`; `save(..., clean=True)`: se `not self.pk`, guarda os arquivos, zera os campos, faz um primeiro `super().save(force_insert, force_update, using, update_fields)` (**posicional**) para obter `pk`, restaura os arquivos; depois salva normalmente (nomeado). Objetivo: gravar o arquivo em caminho que dependa do `pk`.

### 13. `backend/utils/` (app)

- `__init__.py`: `default_app_config = "backend.utils.apps.UtilsConfig"` (ignorado pelo Django moderno, mantido por convenção do projeto/`backend/tests.py`).
- `apps.py`: `UtilsConfig(AppConfig)`: `default_auto_field="django.db.models.BigAutoField"`, `name="backend.utils"`, `label="utils"`; `ready()`: `AppConfig.ready(self)`, importa `from .services import signals, signals_syncrefresh` e atribui `__all__ = [signals, signals_syncrefresh]` (artifício para evitar aviso de import não usado).
- `models.py` e `migrations/0001_initial.py`: ver `data-model.md`.
- `admin.py`: `from backend.utilss import register_all_models_in_admin` e `register_all_models_in_admin(__name__)`.
- `fixtures/`: diretório existente, vazio (sem arquivos versionados; o Git não rastreia pastas vazias — recriar com `mkdir` é opcional).

### 14. `backend/utils/templatetags/common_tags.py`

Biblioteca `register = template.Library()` (sem `__init__.py` no pacote `templatetags`). Lista completa em `contracts/utilitarios.md`. Detalhes algorítmicos relevantes:

- `get_class(class_string)`: se o argumento não tem `__bases__` (não é classe), `str()` e divide no último `.`; tenta `ContentType.objects.get_by_natural_key(mod_name, class_name.lower())` e devolve `ct.model_class()`; em qualquer exceção, importa o módulo com `__import__(mod_name, {}, {}, [""])` e devolve `getattr(módulo, class_name)`. Se já for classe, devolve `None` (retorno implícito).
- `age(data, max_age=0)`: usa `dateutil.relativedelta`; se `data` não tiver `tzinfo`, assume hoje com dia/mês/ano de `data`; se `max_age` (dias) for excedido, devolve `date_format(data, r"d \d\e M \d\e Y")`; se há anos, meses ou mais de 2 dias, devolve texto "N ano(s), N mes(es), N dia(s)"; senão "N dia(s), N hora(s), N minuto(s)".
- `yaml_render(context, template_name, increment_space=0)`: renderiza o template com o contexto e, se `increment_space`, prefixa cada linha com esse número de espaços (usado nos YAMLs de layout/menus).
- `params_search_to_api(items)`: ignora valores vazios e a chave `tipo_listagem`; monta `k=v&...`; substitui `_b=`, `_i=`, `_is=` por `=` e `autoria` por `autores`.
- `obfuscate_value(value, key)`: devolve `"***************"` para as chaves `hash`, `google_recaptcha_secret_key`, `password`, `google_recaptcha_site_key`, `hash_code`, `jdata`.

### 15. Qualidade e repositório

- `pyproject.toml`: seções `[project]` (nome `sdd-start`, versão `0.1.0`, licença MIT, `requires-python >=3.12,<4.0`), `[build-system]` poetry-core, `[tool.poetry] package-mode=false`, grupos `dependencies`, `group.dev` (ruff, jupyter, django-debug-toolbar, django-silk, black, isort), `group.test` (pytest, pytest-cov, pytest-django, model-bakery, django-webtest), `group.docs` (sphinx 9.1.1, sphinxcontrib-django); `celery-haystack` vem do Git (`https://github.com/LeandroJatai/celery-haystack.git`). Lista completa de dependências em `contracts/settings-e-ambiente.md` (seção "Dependências").
- `conftest.py`: `OurTestApp(DjangoTestApp)` com `default_user` e `get` com `setdefault('user', default_user)`/`setdefault('auto_follow', True)`; fixture `app(request, admin_user)` com `WebTestMixin()._patch_settings()` e `request.addfinalizer(wtm._unpatch_settings)`.
- `.editorconfig`: seção `[*.{js,jsx,mjs,cjs,ts,tsx,mts,cts,vue}]`: `charset=utf-8`, `indent_size=2`, `indent_style=space`, `insert_final_newline=true`, `trim_trailing_whitespace=true`.
- `.prettierrc.json`: `"semi": false`, `"singleQuote": true`, `"arrowParens": "avoid"`.
- `.github/dependabot.yml`: `version: 2`, blocos para `npm` (`/`), `docker` (`/_docker/dev`, `/_docker/prod`), `docker-compose` (idem), `pip` (`/`), todos `weekly`. A reconstrução fiel preserva a repetição da chave `updates:`; a recomendação é unificar em uma lista única.
- `__notebooks/django_setup.py`: `PROJECT_ROOT_DIR = Path(os.path.abspath(__file__)).parents[2]`; `DJANGO_ROOT_DIR = PROJECT_ROOT_DIR / "sdd-start"`; `sys.path.append(DJANGO_ROOT_DIR.as_posix())`; `DJANGO_ALLOW_ASYNC_UNSAFE="false"`; `setdefault("DJANGO_SETTINGS_MODULE","backend.settings")`; `django.setup()`. Notebooks: duas células de código, a primeira `import django_setup` + `django_setup.PROJECT_ROOT_DIR, django_setup.DJANGO_ROOT_DIR`.
- Testes: ver `quickstart.md`. `backend/tests.py` e `_tests/test_initials.py` têm o mesmo teste; no segundo há `pytestmark = pytest.mark.django_db`.

## Rastreamento de Complexidade

Sem violações da constituição. As ressalvas do princípio VIII e as particularidades do código estão registradas em `research.md` (seção "Particularidades, dívidas técnicas e riscos observados") e não exigem justificativa de complexidade.
