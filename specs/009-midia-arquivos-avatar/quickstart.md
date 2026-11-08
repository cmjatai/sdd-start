# Quickstart: Validar Mídia, Arquivos e Avatar do Usuário

**Feature**: `009-midia-arquivos-avatar`

## Pré-requisitos

- Ambiente de desenvolvimento do projeto de pé (feature 010) ou Poetry instalado com `backend/.env` (feature 001); `DEBUG=True` para os passos manuais 1–4.
- Volume de mídia acessível: contêiner `/var/project/backend_media/media` ou, no host em debug, `/mnt/volumes/backend_media/media`.

## Validação manual

1. **Settings** — `python manage.py shell -c "from django.conf import settings as s; print(s.MEDIA_URL, s.MEDIA_ROOT, s.MAX_DOC_UPLOAD_SIZE, s.MAX_IMAGE_UPLOAD_SIZE, s.DATA_UPLOAD_MAX_NUMBER_FILES, s.THUMBNAIL_SOURCE_GENERATORS)"` → `/media/ <caminho conforme DEBUG> 1585446912 10485760 1000 ('backend.utilss.pil_image',)`.
2. **Entrega em debug** — criar `MEDIA_ROOT/avatars/teste.png` (qualquer PNG) e `MEDIA_ROOT/private/a.txt`:
   - `curl -i http://localhost:8000/media/avatars/teste.png` → `200` e `Content-Type: image/png`.
   - `curl -i http://localhost:8000/media/private/a.txt` → `404`.
   - `curl -i http://localhost:8000/media/inexistente.png` → `404`.
3. **Avatar** — autenticar, abrir o perfil do usuário (feature 002), enviar uma imagem ≤ 10 MB, ajustar o enquadramento e salvar; o cabeçalho (`avatar_user`) passa a mostrar a imagem recortada; um arquivo > 10 MB deve mostrar `The maximum file size is 10.0MiB`.
4. **`/api/version`** — `curl -i -b <cookie de sessão> http://localhost:8000/api/version` → `user.avatar` com URL da miniatura sob `/media/...`; sem avatar → `/static/imgs/perfil.png`; anônimo → sem a chave `user`.
5. **Produção (`DEBUG=False`, Nginx)** — `curl -i http://<host>/media/avatars/teste.png` → o corpo é o arquivo (entregue pelo Nginx) e a resposta traz `Cache-Control: no-cache`; `curl -i http://<host>/mediaredirect/avatars/teste.png` → `404` (interno); `curl -i http://<host>/media/private/a.txt` → `404`. Para ver o cabeçalho `X-Accel-Redirect`, consultar diretamente o upstream Django (porta interna do Gunicorn): `curl -i http://localhost:<porta-gunicorn>/media/avatars/teste.png` → corpo vazio e `X-Accel-Redirect: /mediaredirect/avatars/teste.png`.

## Testes automatizados propostos (nenhum existe hoje)

Arquivo: `backend/test_media.py`. Executar: `pytest backend/test_media.py -q` (requer PostgreSQL só nos testes com `@pytest.mark.django_db`). Cobertura mínima:

```python
import hashlib

import pytest
from django.test import RequestFactory, override_settings
from django.http import Http404

from backend.utilss import get_mime_type_from_file_extension, hash_sha512
from backend.utils.views import MediaPublicView
from backend.fields import CustomFieldFile


def test_mime_por_extensao():
    assert get_mime_type_from_file_extension("a.odt") == "application/vnd.oasis.opendocument.text"
    assert get_mime_type_from_file_extension("a.pdf") == "application/pdf"
    assert get_mime_type_from_file_extension("a.png") == "application/png"


def test_hash_sha512_caminho_e_arquivo(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    esperado = hashlib.sha512(b"abc").hexdigest()
    assert hash_sha512(str(f)) == esperado
    with open(f, "rb") as fh:
        assert hash_sha512(fh) == esperado


@override_settings(DEBUG=False)
def test_media_producao_x_accel():
    req = RequestFactory().get("/media/avatars/a.png")
    r = MediaPublicView.as_view()(req, path="avatars/a.png")
    assert r["X-Accel-Redirect"] == "/mediaredirect/avatars/a.png"
    assert r["Cache-Control"] == "no-cache" and r["Pragma"] == "no-cache"
    assert r["Content-Disposition"] == 'inline; filename="a.png"'


@pytest.mark.parametrize("debug", [True, False])
def test_media_private_404(debug):
    with override_settings(DEBUG=debug):
        req = RequestFactory().get("/media/private/a.pdf")
        with pytest.raises(Http404):
            MediaPublicView.as_view()(req, path="private/a.pdf")


@override_settings(DEBUG=True)
def test_media_debug_serve(tmp_path):
    (tmp_path / "a.txt").write_text("oi")
    with override_settings(MEDIA_ROOT=tmp_path):
        r = MediaPublicView.as_view()(RequestFactory().get("/media/a.txt"), path="a.txt")
        assert r.status_code == 200


def test_settings_midia(settings):
    assert settings.MEDIA_URL == "/media/"
    assert settings.MAX_DOC_UPLOAD_SIZE == 1512 * 1024 * 1024
    assert settings.MAX_IMAGE_UPLOAD_SIZE == 10 * 1024 * 1024
    assert settings.DATA_UPLOAD_MAX_NUMBER_FILES == 1000
    assert settings.THUMBNAIL_PROCESSORS[0] == "image_cropping.thumbnail_processors.crop_corners"
    assert settings.THUMBNAIL_SOURCE_GENERATORS == ("backend.utilss.pil_image",)
```

Testes adicionais recomendados:

- `avatar_validation`: objeto com `size = 10*1024*1024 + 1` levanta `ValidationError`; `size = 10*1024*1024` passa; `sizeof_fmt(10*1024*1024) == "10.0MiB"`.
- `CustomFieldFile.url` e `shorten_file_name` com modelo de teste (ou `SimpleNamespace`): sem rota → `""`; nome de 130 caracteres → `f_` + 20 caracteres.
- `AppVersionView` com `app` (webtest): anônimo → sem `user`; usuário sem avatar → `user.avatar == "/static/imgs/perfil.png"`.
- `DrfautoapiNegotiation.filter_renderers` com `PngRenderer`/`PDFRenderer`: formato `120.png` seleciona `PngRenderer`; `xyz` levanta `Http404`.
- `SaveModelWithFileMixin`: modelo de teste com `FileField` verificando que o primeiro `save()` ocorre sem arquivo (`@pytest.mark.django_db`).

## Qualidade

- `ruff check backend/fields.py backend/utilss.py backend/model_mixins.py backend/utils backend/settings/medias.py` → sem erros.
- `pytest backend/test_media.py -q` → verde.
