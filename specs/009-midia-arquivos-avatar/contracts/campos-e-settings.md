# Contrato: Campos, Mixins, Helpers e Settings de Mídia

**Feature**: `009-midia-arquivos-avatar`

## Settings (`backend/settings/medias.py`)

| Setting | Valor |
|---|---|
| `MEDIA_URL` | `"/media/"` |
| `MEDIA_ROOT` | `PROJECT_DIR.parent / "backend_media" / "media"`; se `DEBUG` e `"/var/project"` ∉ `str(PROJECT_DIR)` → `/mnt/volumes/backend_media/media` |
| `MEDIA_CACHE_ROOT` | `PROJECT_DIR.parent / "backend_media" / "media_cache"`; mesma regra de debug → `/mnt/volumes/backend_media/media_cache` |
| `FILTERS_HELP_TEXT_FILTER` | `False` |
| `IMAGE_CROPPING_SIZE_WARNING` | `True` |
| `IMAGE_CROPPING_JQUERY_URL` | `None` |
| `THUMBNAIL_PROCESSORS` | `("image_cropping.thumbnail_processors.crop_corners",) + easy_thumbnails.conf.Settings.THUMBNAIL_PROCESSORS` |
| `THUMBNAIL_SOURCE_GENERATORS` | `("backend.utilss.pil_image",)` |
| `MAX_DOC_UPLOAD_SIZE` | `1512 * 1024 * 1024` (1512 MB) |
| `MAX_IMAGE_UPLOAD_SIZE` | `10 * 1024 * 1024` (10 MB) |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | `MAX_DOC_UPLOAD_SIZE` |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | `MAX_DOC_UPLOAD_SIZE` |
| `DATA_UPLOAD_MAX_NUMBER_FILES` | `1000` |

`PROJECT_DIR` e `DEBUG` vêm de `backend/settings/zenv.py` (`DEBUG = config("DEBUG", default=False, cast=bool)`). Apps: `easy_thumbnails`, `image_cropping` em `INSTALLED_APPS`.

**Volumes/portas**: volume Docker `backend_media` → `/var/project/backend_media` (`VOLUME` em `_docker/dev/Dockerfile.Dev` e `_docker/prod/Dockerfile`, com `mkdir -p ${ROOT_HOME}/backend_media`); host em debug: `/mnt/volumes/backend_media`. Nenhuma porta própria.

## `backend/fields.py`

| Símbolo | Assinatura/contrato |
|---|---|
| `CustomFileField` | `models.FileField` com `attr_class = CustomFieldFile` |
| `CustomFieldFile._url` | property → `reverse("backend.api:<app>_<model>-<campo-com-hifens>", kwargs={"pk": pk})`; erro → `""` |
| `CustomFieldFile.url` | property → `_url`; termina em `/` → remove a barra e anexa `.<ext>`; erro → `""` |
| `CustomFieldFile.shorten_file_name()` | nome (último segmento) ≥ 128 → `f_<últimos 20>`; `os.rename` + `instance.save()` |
| `CustomFieldFile.delete(save=True)` | fecha/apaga do storage, `name=None`, `_committed=False`, salva se `save` |

## `backend/utilss.py`

| Símbolo | Contrato |
|---|---|
| `get_mime_type_from_file_extension(filename)` | `odt` → `application/vnd.oasis.opendocument.text`; demais → `application/<ext>` |
| `pil_image(source, exif_orientation=False, **options)` | delegação a `easy_thumbnails.source_generators.pil_image` |
| `hash_sha512(arquivo)` | `str` (caminho) ou arquivo binário; blocos de 4096; hexdigest (128 hex) |
| `FileFieldCheckMixin(BaseForm)` | `clean()` ≡ `_check()`; mensagens: `"Certifique-se de que o nome do arquivo no campo '<rótulo>' ..."` (reescrita) e `"Arquivo referenciado no campo  '<rótulo>' inexistente! Marque a opção Limpar e Salve."` |

## `backend/model_mixins.py`

`SaveModelWithFileMixin`: `FIELDFILE_NAME = ("arquivo",)` (tupla de nomes de campos de arquivo); `save(force_insert=False, force_update=False, using=None, update_fields=None, clean=True)` — objeto novo: zera arquivos → `save` → restaura → `save` final; objeto existente: um `save`.

## `backend/api/mixins.py` — `ResponseFileMixin`

Requisitos do host (ViewSet): `get_queryset()`, `request`, `action` (nome do campo de arquivo), `format_kwarg`, opcional `custom_filename(item)`; e, se houver `thumbnail` por recorte, o campo `<action>_cropping` no modelo. Métodos públicos: `response_file(request, *args, **kwargs)`, `response_pagepdftoimage(arquivo, _page, _dpi, _grade='0')`, `response_pdftotext(arquivo)`, `anon(arquivo, page, grade, anon)`, `thumbnail()`.

## `drfautoapi/__init__.py` e `backend/settings/drf.py`

| Classe | `media_type` | `format` (regex com `re.match`) |
|---|---|---|
| `JpegRenderer` | `image/jpeg` | `[a-zA-Z0-9]*\.?(jpeg\|jpg)` |
| `JpgRenderer` | `image/jpg` | `[a-zA-Z0-9]*\.?(jpg\|jpeg)` |
| `PngRenderer` | `image/png` | `[a-zA-Z0-9]*\.?png` |
| `PDFRenderer` | `application/pdf` | `pdf` |
| `ZIPRenderer` | `application/zip` | `zip` |

`FilesRenderer.render` → `Http404`. `DrfautoapiNegotiation.filter_renderers` → filtra por `re.match(renderer.format, format)`; vazio → `Http404`. Em `REST_FRAMEWORK`: `DEFAULT_RENDERER_CLASSES` = JSON, PDF, Png, Jpg, Jpeg, ZIP; `DEFAULT_CONTENT_NEGOTIATION_CLASS = "drfautoapi.DrfautoapiNegotiation"`; `DEFAULT_PARSER_CLASSES` = JSON, MultiPart, FileUpload.

## Avatar — símbolos

| Símbolo | Arquivo | Contrato |
|---|---|---|
| `sizeof_fmt(num, suffix='B')` | `backend/eauth/models.py` | Ki/Mi/Gi… base 1024, `'%3.1f%s%s'` |
| `avatar_validation(image)` | `backend/eauth/models.py` | limite 10 MiB |
| `User.avatar`, `User.avatar_cropping` | `backend/eauth/models.py` | ver `data-model.md` |
| `avatar_user(user_render=None, css_class="avatar")` | `backend/utils/templatetags/common_tags.py` | inclusion tag → `eauth/user/avatar.html` |
| símbolo SVG `svg-perfil` | `_templates/base.html` | ícone padrão |
| `/static/imgs/perfil.png` | origem `_frontend/src/assets/imgs/perfil.png` | imagem padrão do `AppVersionView` |
