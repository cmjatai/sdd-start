import pytest
from django_webtest import DjangoTestApp, WebTestMixin

collect_ignore_glob = []


class OurTestApp(DjangoTestApp):
    def __init__(self, *args, **kwargs):
        self.default_user = kwargs.pop("default_user", None)
        super(OurTestApp, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs.setdefault("user", self.default_user)
        kwargs.setdefault("auto_follow", True)
        return super(OurTestApp, self).get(*args, **kwargs)


@pytest.fixture(scope="function")
def app(request, admin_user):
    wtm = WebTestMixin()
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    return OurTestApp(default_user=admin_user.username)
