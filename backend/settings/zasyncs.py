from .zenv import DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config

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
    # "default": {
    #    "BACKEND": (
    #        "django.core.cache.backends.locmem.LocMemCache"
    #        if not DEBUG
    #        else "django.core.cache.backends.dummy.DummyCache"
    #    ),
    #    "LOCATION": "unique-snowflake",
    # }
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    }
}
