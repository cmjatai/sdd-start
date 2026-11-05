from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import include, path, re_path
from django.urls.conf import include, re_path
from django.utils.translation import gettext_lazy as _

from . import views, views_auth
from .apps import EAuthConfig

app_name = EAuthConfig.name


urlpatterns = [
    # password_reset
    re_path(
        r'^user/recuperar-senha/email',
        views_auth.BackendPasswordResetView.as_view(),
        name='recuperar_senha_email',
    ),
    # password_reset_done
    re_path(
        r'^user/recuperar-senha/finalizado',
        views_auth.BackendPasswordResetEncaminhadoView.as_view(),
        name='recuperar_senha_finalizado',
    ),
    # password_reset_confirme
    re_path(
        r'^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)',
        views_auth.BackendPasswordResetConfirmView.as_view(),
        name='recuperar_senha_confirma',
    ),
    # password_reset_complete
    re_path(
        r'^user/recuperar-senha/completo',
        views_auth.BackendPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    re_path(
        r'^user/edit',
        login_required(views_auth.BackendUserChangeView.as_view()),
        name='backend_user_change',
    ),
    re_path(r'^login', views_auth.BackendLoginView.as_view(), name='login'),
    re_path(
        r'^logout',
        LogoutView.as_view(),
        {'next_page': '/'},
        name='logout',
    ),
    re_path(
        r'^admin/auditlog',
        views.PesquisarAuditLogView.as_view(),
        name='pesquisar_auditlog',
    ),
    re_path(r'^admin/user/', include(views_auth.UserCrud.get_urls())),
]
