import django_filters
from crispy_forms.layout import Fieldset, Layout
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from backend.crud.crispy_layout_mixin import (
    CustomFormHelper,
    form_actions,
    to_row,
)
from backend.eauth.models import AuditLog


def get_username():
    try:
        return [
            (u.pk, f'{u.get_full_name()} ({u.email})')
            for u in get_user_model().objects.all()
        ]
    except:
        return []


def get_models():
    return [
        (m, m)
        for m in AuditLog.objects.distinct('model_name')
        .order_by('model_name')
        .values_list('model_name', flat=True)
    ]


class AuditLogFilterSet(django_filters.FilterSet):
    OPERATION_CHOICES = (
        ('U', 'Atualizado'),
        ('C', 'Criado'),
        ('D', 'Excluído'),
        ('P', 'Pesquisa'),
    )

    user = django_filters.ChoiceFilter(choices=get_username(), label=_('Usuário'))
    busca = django_filters.CharFilter(label=_('Filtrar Campo'), method='filter_busca')
    operation = django_filters.ChoiceFilter(
        choices=OPERATION_CHOICES, label=_('Operação')
    )
    model_name = django_filters.ChoiceFilter(
        choices=get_models, label=_('Tipo de Registro')
    )
    timestamp = django_filters.DateRangeFilter(label=_('Período'))

    class Meta:
        model = AuditLog
        fields = ['user', 'operation', 'model_name', 'timestamp', 'busca']

    def filter_busca(self, qs, field, value):
        value = value.split(',')
        value = list(map(lambda x: x.strip().split('='), value))

        params = {}
        for k, v in value:
            if k == 'id':
                params['object_id'] = v
                continue
            try:
                v = int(v)
                params[f'obj__0__fields__{k}'] = v
            except:
                params[f'obj__0__fields__{k}'] = v

        qsf = qs.filter(**params)
        if not qsf:
            params = {}
            for k, v in value:
                try:
                    v = int(v)
                    params[f'obj__0__fields__{k}'] = v
                except:
                    params[f'obj__0__fields__{k}__icontains'] = v

            qsf = qs.filter(**params)
        return qsf

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row0 = to_row(
            [
                ('user', 2),
                ('operation', 2),
                ('model_name', 4),
                ('busca', 2),
                ('timestamp', 2),
            ]
        )

        self.form.helper = CustomFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Filtros'), row0, form_actions(label='Aplicar Filtro'))
        )
