import logging
from warnings import filters

from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.utils.translation import gettext_lazy as _


class ListWithSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='',
        # label=_('Filtrar'),
        widget=forms.TextInput(attrs={'type': 'search'}),
    )

    o = forms.CharField(
        required=False, label='', initial='1', widget=forms.HiddenInput()
    )

    page_size = forms.ChoiceField(
        choices=[('10', '10'), ('25', '25'), ('50', '50'), ('100', '100')],
        initial='10',
        label=_('Resultados por página'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        fields = ['q', 'o', 'page_size']

    def __init__(self, *args, **kwargs):
        custom_filters = kwargs.pop('custom_filters', [])
        custom_filters.insert(
            0,
            Field(
                'page_size',
            ),
        )

        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('o'),
            FieldWithButtons(
                Field(
                    'q',
                    placeholder=_('Busque por palavras, números ou códigos'),
                    css_class='input-lg',
                ),
                StrictButton(
                    _('Filtrar'), css_class='btn-outline-primary btn-lg', type='submit'
                ),
                css_class='form-filter',
            ),
            Div(
                *custom_filters, css_class='d-inline-flex mt-3 gap-3 align-items-center'
            ),
        )
