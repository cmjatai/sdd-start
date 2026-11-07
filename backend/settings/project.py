from dj_database_url import parse as db_url

from .apps import *  # Configurações relacionadas aos aplicativos instalados no Django, incluindo aplicativos personalizados e de terceiros  # noqa: F403
from .auth import *  # Configurações relacionadas à autenticação, incluindo backends, permissões e gerenciamento de usuários # noqa: F403
from .drf import *  # Configurações relacionadas ao Django REST Framework, incluindo autenticação, permissões e serialização de dados # noqa: F403
from .email import *  # Configurações relacionadas ao envio de e-mails, incluindo backends, templates e credenciais de serviço # noqa: F403
from .frontend import *  # Configurações relacionadas ao frontend, incluindo templates, arquivos estáticos e integração com frameworks de frontend # noqa: F403
from .languages import *  # Configurações relacionadas a idiomas # noqa: F403
from .logs import *  # Configurações relacionadas a logs, incluindo formatação, níveis e destinos de log # noqa: F403
from .medias import *  # Configurações relacionadas a arquivos de mídia, incluindo diretórios de armazenamento e processamento de imagens, como imagens e vídeos  # noqa: F403
from .middleware import *  # Configurações de middleware do Django, incluindo middlewares personalizados e de terceiros, como autenticação, segurança e logging # noqa: F403
from .solr import *  # Configurações relacionadas ao Solr, incluindo conexão, autenticação e indexação de dados # noqa: F403
from .zasyncs import *  # Configurações Cache, Redis, Celery e Channels, incluindo Channels Layers, Celery Beat Scheduler e configuração de filas assíncronas # noqa: F403
from .zenv import BASE_DIR, DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config

BASE_DIR = BASE_DIR

SECRET_KEY = config("SECRET_KEY")

DEBUG_TOOLBAR_ACTIVE = config("DEBUG_TOOLBAR_ACTIVE", default=False, cast=bool)
DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)

PROJECT_VERSION = "0.0.1"

ALLOWED_HOSTS = ["*"]
SITE_URL = config("SITE_URL", default="http://192.168.15.9:9001")
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
    DATABASES["default"]["PORT"] = 5433
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
