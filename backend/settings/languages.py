from .zenv import config

LANGUAGE_CODE = "pt-br"
TIME_ZONE = config("TZ", default="America/Sao_Paulo")
USE_I18N = True
USE_TZ = True
