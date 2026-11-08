from braces.views import FormMessagesMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.db.models import Q
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import FormView, UpdateView

from backend.crud.base import ACTION_UPDATE, FORM_MESSAGES, Crud
from backend.crud.forms import ListWithSearchForm
from backend.eauth.forms_auth import (
    BackendUserAdminForm,
    BackendUserChangeForm,
    LoginForm,
    NovaSenhaForm,
    RecuperarSenhaForm,
)
from backend.utilss import get_settings_auth_user_model


class BackendUserChangeView(FormMessagesMixin, UpdateView):
    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_UPDATE]
    model = get_user_model()
    form_class = BackendUserChangeForm
    template_name = 'crud/form.html'

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            self.object.get_full_name(),
            self.object.email,
        )
        return context

    def get_success_url(self):
        return reverse_lazy('backend.eauth:backend_user_change')

    def cancel_url(self):
        return '/'

    def get_object(self, queryset=None):
        return self.request.user


class BackendLoginView(LoginView):
    template_name = 'eauth/user/login.html'
    authentication_form = LoginForm


class BackendPasswordResetView(PasswordResetView):
    # password_reset
    email_template_name = 'eauth/user/recuperar_senha_email.html'
    success_url = reverse_lazy('backend.eauth:recuperar_senha_finalizado')

    html_email_template_name = 'eauth/user/recuperar_senha_email.html'
    template_name = 'eauth/user/recuperar_senha_email_form.html'
    # from_email = EMAIL_SEND_USER
    form_class = RecuperarSenhaForm

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return PasswordResetView.dispatch(self, *args, **kwargs)


class BackendPasswordResetEncaminhadoView(PasswordResetView):
    # password_reset_done
    template_name = 'eauth/user/recupera_senha_email_enviado.html'


class BackendPasswordResetConfirmView(PasswordResetConfirmView):
    # password_reset_confirme
    form_class = NovaSenhaForm
    template_name = 'eauth/user/nova_senha_form.html'
    success_url = reverse_lazy('backend.eauth:password_reset_complete')


class BackendPasswordResetCompleteView(PasswordResetCompleteView):
    # password_reset_complete
    template_name = 'eauth/user/recuperar_senha_completo.html'


class UserCrud(Crud):
    model = get_user_model()

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['usuario', 'is_active']

        def get_context_object_name(self, *args, **kwargs):
            return None

    class CreateView(Crud.CreateView):
        layout_key = 'UserCreate'
        form_class = BackendUserAdminForm

    class UpdateView(Crud.UpdateView):
        form_class = BackendUserAdminForm
        layout_key = ''

        def get_form_kwargs(self):
            kwargs = Crud.UpdateView.get_form_kwargs(self)
            kwargs['user_session'] = self.request.user
            return kwargs

    class DetailView(Crud.DetailView):
        layout_key = 'UserDetail'

        def hook_first_name(self, obj, verbose_name='', field_display=''):
            return _('Nome'), field_display

        def hook_last_name(self, obj, verbose_name='', field_display=''):
            return _('Sobrenome'), field_display

        def hook_email(self, obj, verbose_name='', field_display=''):
            return _('Email'), field_display

        def hook_is_active(self, obj, verbose_name='', field_display=''):
            return _('Ativo'), field_display

        def hook_groups(self, obj, verbose_name='', field_display=''):
            return _('Grupos/Perfis'), field_display

        def hook_user_permissions(self, obj, verbose_name='', field_display=''):
            return _('Permissões'), field_display

        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)

    class ListView(Crud.ListView):
        form_search_class = ListWithSearchForm
        ordered_list = None
        paginate_by = 100

        def get_context_data(self, **kwargs):
            context = Crud.ListView.get_context_data(self, **kwargs)
            return context

        def hook_header_usuario(self, *args, **kwargs):
            return 'Usuario'

        def hook_usuario(self, *args, **kwargs):
            return '{}<br><small>{}</small>'.format(
                args[0].get_full_name(),
                args[0].email,
            ), args[2]

        def get_queryset(self):
            qs = super().get_queryset()

            return qs.order_by('-is_superuser', '-is_active', 'first_name')
