from django.urls import include, re_path
from django.utils.translation import gettext_lazy as _

from . import views
from .apps import UtilsConfig

app_name = UtilsConfig.name


urlpatterns = [
    re_path(r"^teste/", include(views.TesteCrud.get_urls())),
    re_path(r"^testws/", views.testws, name="testws"),
    re_path(r"^wstest/(?P<slug>[^.]*)$", views.wstest_index, name="wstest_index"),
]
