from dj_database_url import parse as db_url

from .apps import *
from .auth import *
from .drf import *
from .frontend import *

# from .email import *
from .languages import *
from .logs import *
from .medias import *  # Configurações relacionadas a arquivos de mídia, incluindo diretórios de armazenamento e processamento de imagens
from .middleware import *  # Configurações de middleware do Django, incluindo middlewares personalizados e de terceiros
from .solr import *  # Configurações relacionadas ao Solr, incluindo conexão e indexação de dados
from .zasyncs import *  # Configurações Cache, Redis, Celery e Channels, incluindo Channels Layers e Celery Beat Scheduler
from .zenv import BASE_DIR, DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config

BASE_DIR = BASE_DIR

SECRET_KEY = config("SECRET_KEY")

DEBUG_TOOLBAR_ACTIVE = config("DEBUG_TOOLBAR_ACTIVE", default=False, cast=bool)
DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)

PROJECT_VERSION = "0.0.1"

ALLOWED_HOSTS = ["*"]
SITE_URL = config("SITE_URL", default="http://localhost:9098")
CSRF_TRUSTED_ORIGINS = [
    SITE_URL,
]
SESSIONS_COOKIE_SECURE = not DEBUG

ROOT_URLCONF = "backend.urls"

ASGI_APPLICATION = "backend.asgi.application"
WSGI_APPLICATION = "backend.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": config(
        "DATABASE_URL_DEV" if DEBUG else "DATABASE_URL_PRD",
        cast=db_url,
    )
}
if DEBUG and FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
    DATABASES["default"]["HOST"] = "localhost"
    DATABASES["default"]["PORT"] = 5432
    print("Running in debug mode with local database settings.")
    print("Database host:", DATABASES["default"]["HOST"])
    print("Database port:", DATABASES["default"]["PORT"])

if (
    DEBUG and DEBUG_TOOLBAR_ACTIVE
):  # não funciona no container dev, sendo necessário rodar no runserver no host
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    MIDDLEWARE = MIDDLEWARE + [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    INTERNAL_IPS = ("127.0.0.1",)

if DEBUG:
    NOTEBOOK_ARGUMENTS = [
        "--notebook-dir",
        "__notebooks",
    ]
