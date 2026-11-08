def debug(request):
    from django.conf import settings

    return {"DEBUG": settings.DEBUG}
