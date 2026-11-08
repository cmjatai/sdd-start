from .zenv import DEBUG, PROJECT_DIR, config

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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"


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
        / "frontend"
        / ".vite"
        / "manifest.json",
    }
}
