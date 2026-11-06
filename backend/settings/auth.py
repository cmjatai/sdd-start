from .zenv import config

AUTH_USER_MODEL = "eauth.User"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/?next="
LOGOUT_REDIRECT_URL = "/"

str_pv = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": str_pv + ".MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": str_pv + ".UserAttributeSimilarityValidator",
    },
    {
        "NAME": str_pv + ".CommonPasswordValidator",
    },
    {
        "NAME": str_pv + ".NumericPasswordValidator",
    },
]

GOOGLE_RECAPTCHA_SITE_KEY = config("GOOGLE_RECAPTCHA_SITE_KEY", cast=str, default="")
GOOGLE_RECAPTCHA_SECRET_KEY = config(
    "GOOGLE_RECAPTCHA_SECRET_KEY", cast=str, default=""
)
