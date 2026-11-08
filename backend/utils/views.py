import logging

from django.conf import settings
from django.forms.models import model_to_dict
from django.http import Http404, HttpRequest, HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.views.static import serve as view_static_server

from backend.crud.base import Crud
from backend.globalrules import RP_LIST, RP_VIEW
from backend.utils.models import (
    Teste,
)
from backend.utils.services.tasks import debug_task
from backend.utilss import get_mime_type_from_file_extension

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


class MediaPublicView(View):
    def get(self, request, *args, **kwargs):

        path = kwargs["path"]

        if "private" in path:
            raise Http404

        if settings.DEBUG:
            return view_static_server(request, path, document_root=settings.MEDIA_ROOT)

        file_path = f"{settings.MEDIA_ROOT}/{path}"
        file_name = path.split("/")[-1]
        ext = file_name.split(".")[-1]

        mime = get_mime_type_from_file_extension(file_name)

        if not mime and ext in ["png", "jpg", "jpeg", "gif"]:
            mime = f"image/{ext}"
        else:
            mime = get_mime_type_from_file_extension(file_name)

        response = HttpResponse(content_type=mime)
        response["Content-Disposition"] = 'inline; filename="%s"' % file_name

        response["Cache-Control"] = "no-cache"
        response["Pragma"] = "no-cache"
        response["Expires"] = 0

        response["X-Accel-Redirect"] = "/mediaredirect/{0}".format(path)

        return response

