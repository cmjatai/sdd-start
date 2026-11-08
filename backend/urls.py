from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("system/", admin.site.urls),
    path("", include("backend.api.urls")),
    path("", include("backend.eauth.urls")),
    path("", include("backend.utils.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ACTIVE:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
