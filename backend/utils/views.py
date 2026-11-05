import logging

from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from backend.crud.base import Crud
from backend.globalrules import RP_LIST, RP_VIEW
from backend.utils.models import (
    Teste,
)
from backend.utils.services.tasks import debug_task

logger = logging.getLogger(__name__)


def wstest_index(request: HttpRequest, slug: str) -> HttpResponse:
    return render(request, "wstest_index.html", {})


def testws(request: HttpRequest) -> JsonResponse:
    teste = Teste.objects.order_by("id").last() or Teste()

    debug_task.apply_async((), countdown=2)

    return JsonResponse(
        dict(
            message="ultimo cadastrado. task chamada para criar novo",
            teste=model_to_dict(teste),
        )
    )


class TesteCrud(Crud):
    model = Teste
    public = [RP_LIST, RP_VIEW]
