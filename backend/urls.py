from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve as view_static_server

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
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            view_static_server,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
    ]
