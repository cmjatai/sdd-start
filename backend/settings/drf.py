REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "drfautoapi.PDFRenderer",
        "drfautoapi.PngRenderer",
        "drfautoapi.JpgRenderer",
        "drfautoapi.JpegRenderer",
        "drfautoapi.ZIPRenderer",
    ),
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "drfautoapi.DrfautoapiNegotiation",
    "DEFAULT_PERMISSION_CLASSES": ("backend.api.permissions.BackendModelPermissions",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "backend.api.schema.Schema",
    "DEFAULT_PAGINATION_CLASS": "backend.api.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
}

# TODO:
# rate limiting for API requests
# https://www.django-rest-framework.org/api-guide/throttling/


DRFAUTOAPI = {
    "DEFAULT_SERIALIZER_MODULE": "backend.api.serializers",
    "DEFAULT_FILTER_MODULE": "backend.api.forms",
    "GLOBAL_SERIALIZER_MIXIN": "backend.api.serializers.BackendSerializerMixin",
    "GLOBAL_FILTERSET_MIXIN": "backend.api.forms.CustomFilterSetMixin",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Backend API - docs",
    "DESCRIPTION": "API de dados do Backend. Documentação dos modelos, seus atributos, filtros de busca e endpoint's de comunicação RestFULL.",
    "VERSION": "0.0.1",
}
