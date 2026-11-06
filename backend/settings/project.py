from pathlib import Path

from decouple import AutoConfig
from dj_database_url import parse as db_url

from .apps import *
from .auth import *
from .drf import *

# from .email import *
# from .frontend import *
# from .languages import *
from .logs import *
from .medias import *
from .middleware import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR.parent

config = AutoConfig(search_path=BASE_DIR)

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)
DEBUG_TOOLBAR_ACTIVE = config("DEBUG_TOOLBAR_ACTIVE", default=False, cast=bool)
DEBUG_RUNNING_CONTAINER = DEBUG and "/var/project" in str(PROJECT_DIR)

PROJECT_VERSION = "0.0.1"
MUNICIPIO_UNICO = config("MUNICIPIO_UNICO", default="", cast=str)

FOLDER_DEBUG_CONTAINER = Path(
    config("FOLDER_DEBUG_CONTAINER", default=__file__, cast=str)
)

ALLOWED_HOSTS = ["*"]
SITE_URL = config("SITE_URL", default="http://localhost:9098")
CSRF_TRUSTED_ORIGINS = [
    SITE_URL,
]
SESSIONS_COOKIE_SECURE = not DEBUG

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_DIR / "_templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]

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


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
# Name of static files folder (after called python manage.py collectstatic)
STATIC_URL = "static/"

STATIC_ROOT = PROJECT_DIR / "collectedstatic"

DJANGO_VITE_ASSETS_PATH = PROJECT_DIR / "_frontend" / "dist"

# Include DJANGO_VITE_ASSETS_PATH into STATICFILES_DIRS to be copied inside
# when run command python manage.py collectstatic
STATICFILES_DIRS = [
    DJANGO_VITE_ASSETS_PATH,
]
if DEBUG:
    STATICFILES_DIRS += [
        PROJECT_DIR / "_frontend" / "src" / "assets",
    ]

DJANGO_VITE_DEV_MODE = config("DJANGO_VITE_DEV_MODE", default=True, cast=bool)
DJANGO_VITE_DEV_MODE = DJANGO_VITE_DEV_MODE and DEBUG
DJANGO_VITE = {
    "default": {
        "dev_mode": DJANGO_VITE_DEV_MODE,
        "manifest_path": (
            DJANGO_VITE_ASSETS_PATH if DJANGO_VITE_DEV_MODE else STATIC_ROOT
        )
        / ".vite"
        / "manifest.json",
    }
}


REDIS_HOST = config("REDIS_HOST", cast=str, default="backendredis")
REDIS_PORT = config("REDIS_PORT", cast=int, default=6379)
if DEBUG:
    if FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
        REDIS_HOST = "localhost"

CELERY_BROKER_URL = "redis://{}:{}".format(REDIS_HOST, REDIS_PORT)

CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": CELERY_BROKER_URL,
                    "socket_timeout": None,
                    "socket_connect_timeout": 5,
                }
            ],
        },
    },
}

CACHES = {
    #'default': {
    #    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    #    'LOCATION': '/var/tmp/django_cache',
    # }
    "default": {
        "BACKEND": (
            "django.core.cache.backends.locmem.LocMemCache"
            if not DEBUG
            else "django.core.cache.backends.dummy.DummyCache"
        ),
        "LOCATION": "unique-snowflake",
    }
    # "default": {
    #    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    #    "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    # }
}

USE_SOLR = config("USE_SOLR", default=True, cast=bool)
SOLR_URL = config("SOLR_URL", default="http://solr:solr@backendsolr:8983")
HAYSTACK_SIGNAL_PROCESSOR = "backend.haystack.CelerySignalProcessor"

if DEBUG:
    if FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
        # HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
        SOLR_URL = "http://solr:solr@localhost:8983"
        REDIS_HOST = "localhost"

SOLR_COLLECTION = "backend_arq1"

SEARCH_BACKEND = "haystack.backends.solr_backend.SolrEngine"
SEARCH_URL = ("URL", "{}/solr/{}".format(SOLR_URL, SOLR_COLLECTION))
HAYSTACK_ROUTERS = ["backend.haystack.DefaultRouter"]
HAYSTACK_ITERATOR_LOAD_PER_QUERY = 100
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": SEARCH_BACKEND,
        SEARCH_URL[0]: SEARCH_URL[1],
        "BATCH_SIZE": 1000,
        "TIMEOUT": 600,
        "EXCLUDED_INDEXES": [
            # 'backend.arq.search_indexes.ArqDocIndex',
        ],
    },
    "backendarq": {
        "ENGINE": SEARCH_BACKEND,
        "URL": "{}/solr/{}".format(SOLR_URL, "backend_arq2"),
        "BATCH_SIZE": 1000,
        "TIMEOUT": 600,
        "EXCLUDED_INDEXES": [
            # 'backend.search.search_indexes....Index',
        ],
    },
}


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"


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
