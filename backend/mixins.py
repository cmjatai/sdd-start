from crispy_forms.layout import Div, Fieldset
from django.conf import settings
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from backend.crud.crispy_layout_mixin import (
    CustomFormHelper,
    CustomFormLayout,
    form_actions,
    to_row,
)


class GoogleRecapthaMixin:
    def __init__(self, *args, **kwargs):
        title_label = kwargs.pop("title_label")
        action_label = kwargs.pop("action_label")

        row1 = to_row(
            [
                (
                    Div(
                        css_class="g-recaptcha float-right",  # if not settings.DEBUG else '',
                        data_sitekey=settings.GOOGLE_RECAPTCHA_SITE_KEY,
                    ),
                    5,
                ),
                ("email", 7),
            ]
        )

        self.helper = CustomFormHelper()
        self.helper.layout = CustomFormLayout(
            Fieldset(title_label, row1), actions=form_actions(label=action_label)
        )

        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        cd = self.cleaned_data

        recaptcha = self.data.get("g-recaptcha-response", "")
        if not recaptcha:
            raise ValidationError(_("Verificação do reCAPTCHA não efetuada."))

        import json

        import urllib3

        # encoded_data = json.dumps(fields).encode('utf-8')

        url = (
            "https://www.google.com/recaptcha/api/siteverify?"
            "secret=%s"
            "&response=%s" % (settings.GOOGLE_RECAPTCHA_SECRET_KEY, recaptcha)
        )

        http = urllib3.PoolManager()
        try:
            r = http.request("POST", url)
            data = r.data.decode("utf-8")
            jdata = json.loads(data)
        except Exception as e:
            raise ValidationError(_("Ocorreu um erro na validação do reCAPTCHA."))

        if jdata["success"]:
            return cd
        else:
            raise ValidationError(_("Ocorreu um erro na validação do reCAPTCHA."))

        return cd
