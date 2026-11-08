# Plano de Implementação: Mídia, Arquivos e Avatar do Usuário

**Branch**: `009-midia-arquivos-avatar` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/009-midia-arquivos-avatar/spec.md`

**Nota**: Documento de engenharia reversa — descreve o que **já existe** no repositório.

## Resumo

Entrega a infraestrutura de mídia do esqueleto: settings de armazenamento/limites/miniaturas (`backend/settings/medias.py`), a rota pública `media/<path>` (`MediaPublicView`) com entrega via `django.views.static.serve` em debug e `X-Accel-Redirect` para o Nginx em produção, o campo de arquivo `CustomFileField`/`CustomFieldFile`, helpers de arquivo em `backend/utilss.py`, `SaveModelWithFileMixin`, o avatar do usuário com enquadramento 128x128 (`django-image-cropping` + `easy-thumbnails`), o `ResponseFileMixin` (dormente) e os renderers de arquivo da `drfautoapi`. Não há tabelas novas além das colunas `avatar` e `avatar_cropping` já criadas na migração inicial de `eauth` (feature 002).

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (imagem-base 3.14), Django >= 6, < 7 (lock 6.0.10)

**Dependências Principais**: `easy-thumbnails` 2.10.1 (^2.10.1), `django-image-cropping` 1.7 (^1.7), `Pillow` 13.0.0 (transitiva), `pymupdf` 2.1 (^2.1, usado por `ResponseFileMixin`), `djangorestframework` (renderers/negociação)

**Armazenamento**: sistema de arquivos — `MEDIA_ROOT` = `<pai do projeto>/backend_media/media`; cache `MEDIA_CACHE_ROOT` = `.../media_cache`; colunas `eauth_user.avatar` (varchar) e `avatar_cropping` (varchar) no PostgreSQL

**Testes**: pytest + pytest-django (`DJANGO_SETTINGS_MODULE = backend.settings`); nenhum teste existente cobre a feature — ver `quickstart.md`

**Plataforma Alvo**: Linux; produção atrás do Nginx (`_docker/prod/nginx/backend_docker.conf`)

**Tipo de Projeto**: aplicação web (backend Django)

**Metas de Desempenho**: não definidas; uploads até 1512 MB (`MAX_DOC_UPLOAD_SIZE`), até 1000 arquivos por requisição, avatar até 10 MB; em produção o conteúdo é entregue pelo Nginx (zero cópia no Python)

**Restrições**: caminho contendo `private` jamais servido por `/media/`; `MEDIA_ROOT` fora da árvore do código; `fitz`/`pymupdf` só carregados se `backend.api.mixins` for importado

**Escala/Escopo**: um campo real de arquivo (`User.avatar`); 1 view, 1 rota, 2 classes de campo, 3 helpers, 2 mixins, 6 classes de renderer/negociação

## Verificação da Constituição

| Princípio | Gate | Situação |
|---|---|---|
| I. Backend modular por apps | Código em `backend/` (campos, utilitários, mixins), view/rota no app `utils`, avatar no app `eauth`, renderers na lib `drfautoapi` | Atendido |
| II. Configuração por ambiente, sem segredos | `medias.py` usa `DEBUG` e `PROJECT_DIR` de `zenv.py`; nenhum segredo | Atendido |
| III. Paridade dev/prod via Docker | Mesma view; dev serve via `static.serve`, prod via Nginx; volume `backend_media` nos dois Dockerfiles | Atendido (comportamento difere por `DEBUG`, justificado) |
| IV. API REST gerada, permissões por modelo | `CustomFieldFile.url` aponta para actions geradas `backend.api:<app>_<modelo>-<campo>`; filtro de `FileField` na `drfautoapi` | Atendido (dormente no esqueleto) |
| V. Frontend Vite integrado | `/static/imgs/perfil.png` vem do build do frontend; avatar exibido pelo template Django e por `/api/version` | Atendido |
| VI. Tempo real e assíncrono | Não se aplica (sem tarefas nem canais nesta feature) | N/A |
| VII. PT-BR | `verbose_name`/`help_text` do avatar em português com `gettext_lazy`; `avatar_validation` usa mensagem em inglês traduzível (`The maximum file size is {0}`) | Atendido (ver research.md sobre a mensagem) |
| VIII. Qualidade verificável | Sem testes existentes; testes propostos em `quickstart.md`; ruff | Atendido com ressalva (cobertura a criar) |
| Restrição de mídia | `backend_media/media` fora do código; `X-Accel-Redirect`; `private` bloqueado | Atendido |

## Estrutura do Projeto

### Documentação (esta funcionalidade)

```text
specs/009-midia-arquivos-avatar/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── contracts/
    ├── media-http.md
    └── campos-e-settings.md
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── fields.py                         # CustomFieldFile, CustomFileField
├── utilss.py                         # get_mime_type_from_file_extension, pil_image, hash_sha512, FileFieldCheckMixin
├── model_mixins.py                   # SaveModelWithFileMixin
├── settings/
│   ├── medias.py                     # MEDIA_*, limites, THUMBNAIL_*, IMAGE_CROPPING_*
│   ├── apps.py                       # easy_thumbnails, image_cropping em INSTALLED_APPS
│   └── drf.py                        # renderers de arquivo e negociação
├── utils/
│   ├── views.py                      # MediaPublicView
│   ├── urls.py                       # media/<path> (mediapublic_view)
│   └── templatetags/common_tags.py   # avatar_user
├── eauth/
│   ├── models.py                     # avatar_validation, sizeof_fmt, User.avatar/avatar_cropping
│   ├── forms_auth.py                 # BackendUserChangeForm (widgets de avatar)
│   └── migrations/0001_initial.py    # colunas avatar e avatar_cropping
└── api/
    ├── views.py                      # AppVersionView (miniatura do avatar)
    └── mixins.py                     # ResponseFileMixin (sem consumidores)
drfautoapi/
├── __init__.py                       # DrfautoapiNegotiation, FilesRenderer e renderers
└── drfautoapi.py                     # ApiFilterSetMixin (FileField → CharFilter)
_templates/
├── base.html                         # símbolo svg-perfil e {% avatar_user user 'avatar-2' %}
└── eauth/user/avatar.html            # template da tag avatar_user
_docker/prod/nginx/backend_docker.conf  # location /mediaredirect/
```

**Decisão de Estrutura**: a infraestrutura de mídia é transversal e fica nos módulos de base do pacote `backend` (`fields.py`, `utilss.py`, `model_mixins.py`, `settings/medias.py`); a entrega HTTP fica no app `utils` (rota pública sem modelo) e o avatar no app `eauth`, dono do `User`. Os renderers ficam na biblioteca interna `drfautoapi` por serem parte da negociação por sufixo das actions geradas.

## Detalhamento de Implementação

### 1. Settings de mídia — `backend/settings/medias.py`

Imports: `from pathlib import Path`; `from easy_thumbnails.conf import Settings as thumbnail_settings`; `from .zenv import DEBUG, PROJECT_DIR`. O módulo é incluído pelo pacote de settings (feature 001).

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = PROJECT_DIR.parent / "backend_media" / "media"
MEDIA_CACHE_ROOT = PROJECT_DIR.parent / "backend_media" / "media_cache"
if DEBUG and "/var/project" not in str(PROJECT_DIR):
    MEDIA_ROOT = Path("/mnt/volumes") / "backend_media" / "media"
    MEDIA_CACHE_ROOT = Path("/mnt/volumes") / "backend_media" / "media_cache"
FILTERS_HELP_TEXT_FILTER = False
IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_JQUERY_URL = None
THUMBNAIL_PROCESSORS = ("image_cropping.thumbnail_processors.crop_corners",) + thumbnail_settings.THUMBNAIL_PROCESSORS
THUMBNAIL_SOURCE_GENERATORS = ("backend.utilss.pil_image",)
MAX_DOC_UPLOAD_SIZE = 1512 * 1024 * 1024
MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
DATA_UPLOAD_MAX_NUMBER_FILES = 1000
```

Lógica: `PROJECT_DIR = Path(__file__).parents[2]` (raiz do repositório; `zenv.py`). Em contêiner o projeto está em `/var/project/backend`, logo `MEDIA_ROOT=/var/project/backend_media/media`. Fora do contêiner com `DEBUG`, usa o volume do host `/mnt/volumes/backend_media`. Fora do contêiner **sem** `DEBUG`, usa o irmão do projeto (`<repo>/../backend_media/media`).

`INSTALLED_APPS` (`backend/settings/apps.py`): incluir `"easy_thumbnails"` e `"image_cropping"` (ambas listas de apps de terceiros).

### 2. Campo de arquivo — `backend/fields.py`

Imports: `os`, `settings`, `models`, `FieldFile`, `reverse`.

`CustomFieldFile(FieldFile)`:

- `_url` (property): dentro de `try`/`except:` nu → `""`. Chama `self._require_file()`; `field_name_action = self.field.name.replace("_", "-")`; `reverse("backend.api:%s_%s-%s" % (app_label, model_name, field_name_action), kwargs={"pk": self.instance.pk})`. Há um bloco comentado para `settings.DEBUG` → `storage.url` (não ativo).
- `url` (property): `url = self._url`; `ext = self.name.split(".")[-1]`; se `url` e `url[-1]=="/"`: `url = f"{url[:-1]}.{ext}"`; qualquer exceção → `""`.
- `shorten_file_name()`: `name = self.name`; se vazio retorna; `nl = name.split("/")`; se `len(nl[-1]) < 128` retorna; `nl[-1] = "f_" + nl[-1][-20:]`; `new_path = f'{settings.MEDIA_ROOT}/{"/".join(nl)}'`; `os.rename(self.path, new_path)`; `self.name = "/".join(nl)`; `self.instance.save()`.
- `delete(self, save=True)`: `if not self: return`; se `hasattr(self, "_file")`: `self.close(); del self.file`; `self.storage.delete(self.name)`; `self.name = None`; `setattr(self.instance, self.field.name, self.name)`; `self._committed = False`; `if save: self.instance.save()`.

`CustomFileField(models.FileField)`: `attr_class = CustomFieldFile`.

Observação: a rota `backend.api:<app>_<modelo>-<campo>` é nome de action gerada pela `drfautoapi` com `url_path`/nome por campo e `pk`; com `include_format_suffixes` (feature 005) o sufixo vira `.ext`. No esqueleto não existem tais actions.

### 3. View e rota de mídia — `backend/utils/views.py`, `backend/utils/urls.py`

Imports da view: `settings`, `Http404`, `HttpResponse`, `django.views.generic.View`, `django.views.static.serve as view_static_server`, `get_mime_type_from_file_extension`.

`MediaPublicView(View).get(request, *args, **kwargs)`:

1. `path = kwargs["path"]`; se `"private" in path`: `raise Http404`.
2. Se `settings.DEBUG`: `return view_static_server(request, path, document_root=settings.MEDIA_ROOT)`.
3. `file_name = path.split("/")[-1]`; `ext = file_name.split(".")[-1]`; `mime = get_mime_type_from_file_extension(file_name)`; `if not mime and ext in ["png","jpg","jpeg","gif"]: mime = f"image/{ext}"` senão recalcula o mesmo valor. (`file_path` é calculado e não usado.)
4. `response = HttpResponse(content_type=mime)`; cabeçalhos: `Content-Disposition: inline; filename="<file_name>"`, `Cache-Control: no-cache`, `Pragma: no-cache`, `Expires: 0`, `X-Accel-Redirect: /mediaredirect/<path>`.

`backend/utils/urls.py` (`app_name = UtilsConfig.name`): `re_path(r"^media/(?P<path>.*)$", views.MediaPublicView.as_view(), name="mediapublic_view")`; incluído por `path("", include("backend.utils.urls"))` em `backend/urls.py`.

### 4. Nginx de produção — `_docker/prod/nginx/backend_docker.conf`

```nginx
location /mediaredirect/ {
    internal;
    alias /var/project/backend_media/media/;
    add_header Pragma "no-cache";
    add_header Cache-Control "no-cache";
    add_header Expires 0;
    expires 0;
}
```

Também `client_max_body_size 4G;` no `server`. Não existe `location /media/`; a requisição cai em `location /` (proxy ao Django). Detalhes do Nginx: feature 011.

### 5. Helpers — `backend/utilss.py`

- `get_mime_type_from_file_extension(filename)`: `ext = filename.split(".")[-1]`; `"odt"` → `application/vnd.oasis.opendocument.text`; senão `"application/%s" % ext` (há um `TODO` sobre usar `python-magic`/`mimetypes`).
- `pil_image(source, exif_orientation=False, **options)`: `return source_generators.pil_image(source, exif_orientation, **options)` com `from easy_thumbnails import source_generators`.
- `hash_sha512(arquivo)`: abre `rb` se `str`; `hashlib.sha512()`; `for byte_block in iter(lambda: f.read(4096), b"")`; fecha se abriu; `hexdigest()`.
- `FileFieldCheckMixin(BaseForm)`: `_check()` chama `super().clean()` (guarda em `cleaned_data`), percorre `self.fields`; para cada `forms.fields.FileField`: se há `self.errors.get(name)`, reescreve cada mensagem trocando `"Certifique-se de que o arquivo"` por `"Certifique-se de que o nome do arquivo no campo '{rótulo}'"`; se `cleaned_data.get(name)` existe e não é `UploadedFile` e `not os.path.exists(arquivo.path)` acrescenta `"Arquivo referenciado no campo  '<rótulo>' inexistente! Marque a opção Limpar e Salve."` (note os dois espaços antes do rótulo, por concatenação de strings); se houver erros, `raise ValidationError(errors)`; devolve `cleaned_data`. `clean()` é alias que retorna `self._check()`.

Imports usados: `hashlib`, `os`, `forms`, `UploadedFile`, `BaseForm`, `ValidationError`.

### 6. `SaveModelWithFileMixin` — `backend/model_mixins.py`

`FIELDFILE_NAME = ("arquivo",)`; `save(self, force_insert=False, force_update=False, using=None, update_fields=None, clean=True)`:

```python
if not self.pk:
    files = {f: getattr(self, f) for f in self.FIELDFILE_NAME}
    for f in self.FIELDFILE_NAME: setattr(self, f, None)
    super().save(force_insert, force_update, using, update_fields)
    for f, file in files.items():
        if file: setattr(self, f, file)
return super().save(force_insert=..., force_update=..., using=..., update_fields=...)
```

Atenção: o 1º `save` repassa `force_insert` posicionalmente; se `force_insert=True` o segundo `save` também o repassa (risco documentado em research.md). O mixin deve vir **antes** do modelo base na lista de herança.

### 7. Avatar — `backend/eauth/models.py`

Imports: `from django import forms`, `from image_cropping import ImageCropField, ImageRatioField`.

- `sizeof_fmt(num, suffix='B')` (unidades `['', 'Ki','Mi','Gi','Ti','Pi','Ei','Zi']`, base 1024, formato `'%3.1f%s%s'`, `'Yi'` ao esgotar).
- `avatar_validation(image)`: `if image:` e `image.size > 10*1024*1024` → `forms.ValidationError(_('The maximum file size is {0}').format(sizeof_fmt(max_file_size)))`.
- `User.FIELDFILE_NAME = ('avatar',)`.
- `avatar = ImageCropField(upload_to='avatars/', verbose_name=_('Avatar'), validators=[avatar_validation], null=True, blank=True)`.
- `avatar_cropping = ImageRatioField('avatar', '128x128', verbose_name=_('Seleção (Enquadramento)'), help_text=_('A configuração do Avatar é possível após a atualização da fotografia.'))`.
- Migração: já em `backend/eauth/migrations/0001_initial.py` (colunas `avatar` e `avatar_cropping`).

`backend/eauth/forms_auth.py` (`BackendUserChangeForm`, `Meta.fields` inclui `'avatar'`, `'avatar_cropping'`; `widgets = {'avatar': ImageCropWidget(), 'avatar_cropping': CropWidget()}`; layout `('avatar', 7), ('avatar_cropping', 5)` na mesma linha; `__init__` termina com `avatar = self.fields['avatar'].widget; avatar.attrs.update(get_attrs(self.instance.avatar, 'avatar')); avatar.attrs.pop('class', None)`; `helper.include_media = False`). Imports: `from image_cropping.widgets import CropWidget, ImageCropWidget, get_attrs`.

`backend/api/views.py` — `AppVersionView(APIView)`, `permission_classes = (AllowAny,)`, rota `re_path(r'^api/version$', AppVersionView.as_view())` em `backend/api/urls.py`. Resposta: `{name:'Backend', description:'Plataforma ...', version: settings.PROJECT_VERSION}` e, se autenticado, `user: {username, fullname, avatar}` com `avatar` conforme FR-021 (`from image_cropping.utils import get_backend`).

Template tag (`backend/utils/templatetags/common_tags.py`): `@register.inclusion_tag("eauth/user/avatar.html") def avatar_user(user_render=None, css_class="avatar"): return {"user_render": user_render, "css_class": css_class}`.

Template `_templates/eauth/user/avatar.html`: `{% load i18n static cropping%}`; `{% if user_render.avatar %}<img class="{{ css_class }}" src="{% cropped_thumbnail user_render 'avatar_cropping' %}">{% else %}<svg class="{{ css_class }}" title="{{user_render}}"><use href="#svg-perfil"></use></svg>{% endif %}`. `_templates/base.html` define `<symbol id="svg-perfil" viewBox="0 0 73.2575 73.2575">` e chama `{% avatar_user user 'avatar-2' %}`.

Imagem padrão: `_frontend/src/assets/imgs/perfil.png` (servida como `/static/imgs/perfil.png` após o build).

### 8. `ResponseFileMixin` — `backend/api/mixins.py`

Imports: `logging`, `os`, `fitz`, `pymupdf`, `settings`, `HttpResponse`, `get_thumbnailer`, `Rect`, `NotFound`, `clean_text`, `get_mime_type_from_file_extension`. Métodos:

- `response_pagepdftoimage(arquivo, _page, _dpi, _grade='0')`: `nocache = request.GET.get('nocache', False)`; `_grade` numérico → int; senão interpreta `x0,y0,x1,y1` como `Rect` e usa grade 25. `fcache_path = f'{arquivo.file}-p{_page:0>3}-d{_dpi:0>3}.png'`; se `_grade < 10`, usa o cache se existir (e não `nocache`), ou o remove. Abre com `fitz.open(arquivo.file)`, na página pedida desenha a grade (se `_grade >= 10`; linhas tracejadas a cada `_grade` pontos com rótulos e o `Rect` semitransparente), `get_pixmap(dpi=_dpi or 300)`, grava o cache quando permitido e devolve `HttpResponse(png, 'image/png')`; página inexistente → `NotFound`.
- `anon(arquivo, page, grade, anon)`: abre o PDF com `pymupdf`, para cada página (todas ou só `page`), procura cada termo (`anon` separado por vírgula) com `search_for`, adiciona anotações de redação preta nas áreas que interceptam o retângulo `grade` (ou a página) e `apply_redactions`; em `DEBUG` salva em `/home/leandro/TEMP/pdf_anon.pdf` sem alterar o original (caminho de máquina do autor — ver research.md); fora de debug grava `<arquivo>.new` e substitui o original. Exceções são impressas e ignoradas.
- `response_pdftotext(arquivo)`: junta `page.get_text()` de todas as páginas, `clean_text`, `HttpResponse(text, 'text/plain; charset=utf-8')`.
- `response_file(request, *args, **kwargs)`: fluxo de FR-032…FR-037; usa `self.action`, `self.format_kwarg`, `self.get_queryset()`, `self.custom_filename(item)` (opcional) e `self.thumbnail()`.
- `thumbnail()`: `format = self.format_kwarg`; se contém `.` → `format, ext = format.split('.')`, senão `format=None` e devolve o próprio arquivo. Se `format[0] != 'c'`: `get_thumbnailer(arquivo).get_thumbnail({'size': (N, N), 'box': None, 'crop': False, 'detail': True})`; senão `N = format[1:]` com `'box': getattr(self.item, f'{self.action}_cropping')` e `'crop': True`.

Não há classe de view que herde `ResponseFileMixin` no esqueleto.

### 9. Renderers e negociação — `drfautoapi/__init__.py`

- `DrfautoapiNegotiation(DefaultContentNegotiation).filter_renderers(renderers, format)`: `[r for r in renderers if re.match(r.format, format)]`; vazio → `raise Http404`.
- `FilesRenderer(BaseRenderer).render(...)`: `raise Http404`.
- Subclasses (atributos `media_type` / `format`): `JpegRenderer` (`image/jpeg`, `[a-zA-Z0-9]*\.?(jpeg|jpg)`), `JpgRenderer` (`image/jpg`, `[a-zA-Z0-9]*\.?(jpg|jpeg)`), `PngRenderer` (`image/png`, `[a-zA-Z0-9]*\.?png`), `PDFRenderer` (`application/pdf`, `pdf`), `ZIPRenderer` (`application/zip`, `zip`).
- `backend/settings/drf.py`: `DEFAULT_RENDERER_CLASSES = (JSONRenderer, drfautoapi.PDFRenderer, PngRenderer, JpgRenderer, JpegRenderer, ZIPRenderer)`; `DEFAULT_CONTENT_NEGOTIATION_CLASS = "drfautoapi.DrfautoapiNegotiation"`; parsers `JSONParser`, `MultiPartParser`, `FileUploadParser`.
- `drfautoapi/drfautoapi.py`: `ApiFilterSetMixin.Meta.filter_overrides[FileField] = {"filter_class": django_filters.CharFilter, "extra": lambda f: {"lookup_expr": "exact"}}`; `DrfautoapiRouter(DefaultRouter).get_urls` aplica `format_suffix_patterns(urls, allowed=["[a-zA-Z.0-9]+"])` quando `include_format_suffixes` (atributo `True` por padrão do `DefaultRouter` do DRF), o que permite sufixos como `.png`, `.pdf`, `.zip` e `<tamanho>.png`.

### 10. Testes propostos (princípio VIII)

Arquivo sugerido `backend/test_media.py` (casa com `testpaths = **/test_*.py`): ver `quickstart.md`.

## Rastreamento de Complexidade

Sem violações da constituição. Dívidas técnicas (código morto, `except:` nu, caminho local fixo no `anon`, mensagem em inglês) estão em `research.md`; a recomendação é replicar para fidelidade e corrigir em evolução controlada.
