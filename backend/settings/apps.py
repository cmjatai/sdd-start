DJANGO_CORE_APPS = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django.forms",
    "django_vite",
]

DJANGO_THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "easy_thumbnails",
    "image_cropping",
    "django_celery_beat",
    "django_celery_results",
    "haystack",
    "celery_haystack",
    "drf_spectacular",
    "rest_framework",
    "django_filters",
    "rest_framework.authtoken",
    #'rest_framework_simplejwt' if PYTHON_VERSION >= PYTHON_VERSION_MIN_FOR_JWT else 'rest_framework.authtoken',
]

BACKEND_APPS = ["backend.eauth", "backend.utils"]

INSTALLED_APPS = (
    DJANGO_CORE_APPS
    + DJANGO_THIRD_PARTY_APPS
    + BACKEND_APPS
    + [
        "backend.api",
        "backend.globalrules",
    ]
)
