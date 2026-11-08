# Contrato: Settings, Ambiente e Pontos de Entrada

**Feature**: `001-fundacao-projeto-django` | Referências: [plan.md](../plan.md), [spec.md](../spec.md)

## 1. Variáveis de ambiente / `.env`

Lidas por `decouple.AutoConfig` (`backend/settings/zenv.py`). **Precedência**: variável de ambiente do processo > arquivo `.env` > padrão do código. Local do arquivo: `backend_data/.env` (diretório irmão da raiz do repositório) se existir; senão busca padrão (`backend/.env`, não versionado). Nunca versionar segredos.

| Variável | Tipo | Padrão | Obrigatória | Módulo | Efeito |
|----------|------|--------|-------------|--------|--------|
| `SECRET_KEY` | str | — | **Sim** | `project.py` | chave secreta do Django; ausência → `UndefinedValueError` |
| `DEBUG` | bool | `False` | Não | `zenv.py` | seleciona DEV/PRD, handler `console`, nível de log, toolbar, estáticos pelo Django |
| `DATABASE_URL_DEV` | URL (`dj_database_url`) | — | Sim se `DEBUG=True` | `project.py` | ex.: `postgresql://usuario:senha@host:5432/banco` |
| `DATABASE_URL_PRD` | URL | — | Sim se `DEBUG=False` | `project.py` | idem |
| `FOLDER_DEBUG_CONTAINER` | str (caminho) | caminho do próprio `zenv.py` | Não | `zenv.py` | se igual a `PROJECT_DIR` → "rodando no contêiner" (gravada pelos `start*.sh` com `${HOME}`) |
| `SITE_URL` | str | `http://192.168.15.9:9001` | Não | `project.py` | origem confiável de CSRF |
| `DEBUG_TOOLBAR_ACTIVE` | bool | `False` | Não | `project.py` | só com `DEBUG=True` |
| `TZ` | str | `America/Sao_Paulo` | Não | `languages.py` | `TIME_ZONE` |
| `LOGGING_ROOT_LEVEL` | str | `DEBUG` se `DEBUG` senão `INFO` | Não | `logs.py` | nível dos handlers/loggers |
| `REDIS_HOST` | str | `startdev1-redis` | Não | `zasyncs.py` | forçado a `localhost` com `DEBUG` fora do contêiner |
| `REDIS_PORT` | int | `6379` | Não | `zasyncs.py` | broker Celery, channel layer, cache |

Variáveis de outras features (apenas listadas): `GOOGLE_RECAPTCHA_SITE_KEY`, `GOOGLE_RECAPTCHA_SECRET_KEY` (`auth.py`, padrão `""`; feature 002), `DJANGO_VITE_DEV_MODE` (`frontend.py`, padrão `True`; 007), `USE_SOLR`, `SOLR_URL`, `SOLR_COLLECTIONS` (`solr.py`; 008).

### Exemplo mínimo de `backend/.env` (desenvolvimento no host)

```ini
DEBUG=True
SECRET_KEY=<valor-gerado-localmente>
DATABASE_URL_DEV=postgresql://startdev1:startdev1@localhost:5433/startdev1
```

(os valores `startdev1` são exemplos do repositório; com `DEBUG=True` fora do contêiner `HOST`/`PORT` são sobrescritos para `localhost:5433`.)

## 2. Chaves de settings produzidas por esta feature

| Chave | Valor | Arquivo |
|-------|-------|---------|
| `BASE_DIR` | `Path(__file__).parents[1]` de `zenv.py` (`backend/`) | `zenv.py` |
| `PROJECT_DIR` | `parents[2]` (raiz do repositório) | `zenv.py` |
| `SECRET_KEY` | `config("SECRET_KEY")` | `project.py` |
| `DEBUG` | `config("DEBUG", False, bool)` | `zenv.py` |
| `DEBUG_TOOLBAR_ACTIVE` | bool | `project.py` |
| `DEBUG_RUNNING_CONTAINER` | `DEBUG and "/var/project" in str(PROJECT_DIR)` | `project.py` |
| `PROJECT_VERSION` | `"0.0.1"` | `project.py` |
| `ALLOWED_HOSTS` | `["*"]` | `project.py` |
| `SITE_URL`, `CSRF_TRUSTED_ORIGINS` | `[SITE_URL]` | `project.py` |
| `SESSIONS_COOKIE_SECURE` | `not DEBUG` (nome incorreto; sem efeito) | `project.py` |
| `ROOT_URLCONF` | `"backend.urls"` | `project.py` |
| `ASGI_APPLICATION` / `WSGI_APPLICATION` | `"backend.asgi.application"` / `"backend.wsgi.application"` | `project.py` |
| `DEFAULT_AUTO_FIELD` | `"django.db.models.BigAutoField"` | `project.py` |
| `DATABASES["default"]` | `parse(config(DATABASE_URL_DEV|PRD))` (+ `HOST`/`PORT` locais) | `project.py` |
| `INTERNAL_IPS` | `("127.0.0.1",)` (só `DEBUG`) | `project.py` |
| `NOTEBOOK_ARGUMENTS` | `["--notebook-dir", "__notebooks"]` (só `DEBUG`) | `project.py` |
| `INSTALLED_APPS` | ver §3 | `apps.py` (+ `debug_toolbar` condicional) |
| `MIDDLEWARE` | ver §4 | `middleware.py` (+ toolbar condicional) |
| `LANGUAGE_CODE`, `TIME_ZONE`, `USE_I18N`, `USE_TZ` | `"pt-br"`, `TZ`, `True`, `True` | `languages.py` |
| `LOGGING_ROOT_LEVEL`, `LOGGING` | ver §5 | `logs.py` |
| `THUMBNAIL_SOURCE_GENERATORS` | `("backend.utilss.pil_image",)` | `medias.py` (feature 009) |

`backend/settings/__init__.py` contém apenas `from .project import *`; `backend/settings/email.py` é vazio; `backend/settings/fake.py` ver §7.

## 3. `INSTALLED_APPS` (ordem exata)

1. Núcleo: `daphne`, `channels`, `django.contrib.admin`, `django.contrib.auth`, `django.contrib.contenttypes`, `django.contrib.sessions`, `django.contrib.messages`, `django.contrib.staticfiles`, `django_extensions`, `django.forms`, `django_vite`.
2. Terceiros: `crispy_forms`, `crispy_bootstrap5`, `easy_thumbnails`, `image_cropping`, `django_celery_beat`, `django_celery_results`, `haystack`, `celery_haystack`, `drf_spectacular`, `rest_framework`, `django_filters`, `rest_framework.authtoken`.
3. Projeto: `backend.eauth`, `backend.utils`, `backend.api`, `backend.globalrules`.
4. Condicional: `debug_toolbar` (se `DEBUG and DEBUG_TOOLBAR_ACTIVE`), acrescentado ao final.

## 4. `MIDDLEWARE` (ordem exata)

`django.middleware.security.SecurityMiddleware`, `django.contrib.sessions.middleware.SessionMiddleware`, `django.middleware.common.CommonMiddleware`, `django.middleware.csrf.CsrfViewMiddleware`, `django.contrib.auth.middleware.AuthenticationMiddleware`, `django.contrib.messages.middleware.MessageMiddleware`, `django.middleware.clickjacking.XFrameOptionsMiddleware`, `django.middleware.locale.LocaleMiddleware`; condicional: `debug_toolbar.middleware.DebugToolbarMiddleware` ao final.

## 5. Logging

| Item | Valor |
|------|-------|
| Arquivo | `logs/backend_logger.log` (caminho **relativo** ao diretório de trabalho; `logs/` deve existir) |
| Rotação | `RotatingFileHandler`, `maxBytes=15*1024*1024`, `backupCount=10` |
| Console | `StreamHandler`, filtro `require_debug_true` |
| Formatador `verbose` | `backend.settings.logs.MyFormatter`, `"%(levelname)s %(asctime)s %(name)s:%(funcName)s:%(lineno)d %(message)s"` + ` - <request.path>` |
| Formatador `simple` | `"%(levelname)s %(asctime)s - %(message)s"` (não usado por handlers) |
| Loggers | `root`, `django`, `haystack`, `backend` → handlers `backend_logger_file` e `console`, nível `LOGGING_ROOT_LEVEL`; os três nomeados com `propagate=False` |
| Exceções não tratadas | `sys.excepthook = uncaught_exceptions` (ERROR no logger do módulo + `print`) |
| Avisos Python | `logging.captureWarnings(True)` |

## 6. Rotas raiz (`backend/urls.py`)

| Ordem | Padrão | Destino | `name` |
|-------|--------|---------|--------|
| 1 | `system/` | `admin.site.urls` | (namespace `admin`) |
| 2 | `""` | `include("backend.api.urls")` | feature 005 |
| 3 | `""` | `include("backend.eauth.urls")` | feature 002 |
| 4 | `""` | `include("backend.utils.urls")` | features 004/006 |
| 5 | `""` | `TemplateView.as_view(template_name="index.html")` | `index` |
| cond. | `__debug__/` | `include("debug_toolbar.urls")` | só `DEBUG and DEBUG_TOOLBAR_ACTIVE` |
| cond. | `STATIC_URL` | `static(STATIC_URL, document_root=STATIC_ROOT)` | só `DEBUG` |

Permissão: o admin exige usuário staff; `GET /` é público (template `index.html`, ver feature 007).

## 7. Pontos de entrada e CLI

| Arquivo | Contrato |
|---------|----------|
| `manage.py` | `#!/usr/bin/env python`; `setdefault("DJANGO_SETTINGS_MODULE","backend.settings")`; `execute_from_command_line(sys.argv)` |
| `backend/wsgi.py` | `application = get_wsgi_application()` (Gunicorn: `backend.wsgi:application`) |
| `backend/asgi.py` | `application = ProtocolTypeRouter({"http": ASGIHandler(), "websocket": AuthMiddlewareStack(URLRouter(backend.utils.routing.websocket_urlpatterns))})` (Daphne: `backend.asgi:application`) |
| `backend/celery.py` | `app = Celery("backend")`; `config_from_object("django.conf:settings", namespace="CELERY")`; `autodiscover_tasks(lambda: settings.INSTALLED_APPS)`; CLI: `celery -A backend worker\|beat` |
| `backend/__init__.py` | `from .celery import app as celery_app`; `__all__ = ('celery_app',)` |
| `backend/context_processors.py` | `debug(request)` → `{"DEBUG": settings.DEBUG}`; registrar em `TEMPLATES` (`frontend.py`) |
| `backend/settings/fake.py` | `DJANGO_SETTINGS_MODULE=backend.settings.fake`: SQLite `PROJECT_DIR/db.sqlite3`, `DEBUG=False`, `DJANGO_VITE_DEV_MODE=False`, `DJANGO_VITE={"default":{"dev_mode":False,"manifest_path":DJANGO_VITE_ASSETS_PATH/"frontend"/".vite"/"manifest.json"}}`; uso: `collectstatic` na imagem Docker (feature 011) |
| `__notebooks/django_setup.py` | `import django_setup` define `PROJECT_ROOT_DIR`, `DJANGO_ROOT_DIR`, `DJANGO_ALLOW_ASYNC_UNSAFE="false"`, `DJANGO_SETTINGS_MODULE` e chama `django.setup()` |

Chaves `CELERY_*` e `CHANNEL_LAYERS` vêm de `zasyncs.py` (feature 006): `CELERY_BROKER_URL="redis://{REDIS_HOST}:{REDIS_PORT}"`, `CELERY_RESULT_BACKEND="django-db"`, `CELERY_CACHE_BACKEND="django-cache"`, `CELERY_BEAT_SCHEDULER="django_celery_beat.schedulers.DatabaseScheduler"`.

## 8. Configuração de ferramentas (`pyproject.toml`)

| Seção | Chaves |
|-------|--------|
| `[tool.pytest.ini_options]` | `DJANGO_SETTINGS_MODULE="backend.settings"`; `addopts='--reuse-db -p no:warnings --cov=.'`; `testpaths=["**/tests.py","**/test_*.py"]` |
| `[tool.coverage.run]` | `omit=["_tests/*","backend/settings/*","backend/wsgi.py","backend/asgi.py"]` |
| `[tool.ruff.lint]` | `select=["E","F","I"]` |
| `[tool.poetry]` | `package-mode=false`; grupos `dev` (ruff, jupyter, django-debug-toolbar, django-silk, black, isort), `test` (pytest, pytest-cov, pytest-django, model-bakery, django-webtest), `docs` (sphinx 9.1.1, sphinxcontrib-django) |
| `[project]` | `name="sdd-start"`, `version="0.1.0"`, licença MIT, `requires-python=">=3.12,<4.0"` |

### Dependências de produção (`[tool.poetry.dependencies]`)

`django >=6,<7`; `daphne ^4.2.3`; `channels ^4.3.2`; `channels-redis ^4.3.0`; `django-vite ^3.2.0`; `django-extensions ^4.1`; `python-decouple ^3.8`; `gunicorn ^26.2.0`; `kazoo ^2.11.0`; `twisted[http2,tls] ^26.10.0`; `redis ^8.1.0`; `celery ^5.7.0`; `django-celery-beat ^2.9.0`; `django-celery-results ^2.6.0`; `psycopg[pool] ^3.3.8`; `dj-database-url ^3.1.2`; `ipython ^9.18.1`; `pyyaml ^6.0.3`; `django-haystack ^3.4.0`; `celery-haystack` (Git: `https://github.com/LeandroJatai/celery-haystack.git`); `pysolr ^3.11.0`; `pymupdf ^2.1`; `django-image-cropping ^1.7`; `easy-thumbnails ^2.10.1`; `pytz ^2026.6`; `djangorestframework ^3.18.3`; `django-filter ^26.2`; `drf-spectacular ^0.30.0`; `crispy-bootstrap5 ^2026.9`; `markdown ^3.11.3`; `django-braces ^1.17.0`; `num2words ^0.5.14`; `xlsxwriter ^3.3.1`; `python-docx ^1.2.0`; `weasyprint ^70.0`; `pandas ^3.1.1`; `python-magic ^0.4.27`. (`python-dateutil` é transitiva; `django-crispy-forms` vem via `crispy-bootstrap5`.)
