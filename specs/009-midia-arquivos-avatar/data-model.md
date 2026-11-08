# Modelo de Dados: Mídia, Arquivos e Avatar do Usuário

**Feature**: `009-midia-arquivos-avatar` | **Data**: 2026-11-08

> **Não há tabelas novas.** A única persistência da feature são as colunas `avatar` e `avatar_cropping` do modelo `User` (app `eauth`, tabela `eauth_user`), já criadas na migração inicial `backend/eauth/migrations/0001_initial.py` (feature 002). O restante são estruturas em disco, configuração e classes auxiliares.

## 1. Campos do modelo `User` (`backend/eauth/models.py`)

| Campo | Tipo | Opções | Observações |
|---|---|---|---|
| `avatar` | `image_cropping.ImageCropField` (subclasse de `ImageField`) | `upload_to='avatars/'`, `verbose_name=_('Avatar')`, `validators=[avatar_validation]`, `null=True`, `blank=True` | Guarda o caminho relativo `avatars/<nome>`; arquivo físico em `MEDIA_ROOT/avatars/` |
| `avatar_cropping` | `image_cropping.ImageRatioField` (campo de texto `CharField` interno, `max_length=255`) | referência `'avatar'`, razão `'128x128'`, `verbose_name=_('Seleção (Enquadramento)')`, `help_text=_('A configuração do Avatar é possível após a atualização da fotografia.')` | Guarda `"x1,y1,x2,y2"` (retângulo do enquadramento; vazio quando não definido) |

Atributo de classe: `User.FIELDFILE_NAME = ('avatar',)` (inerte: `User` não herda `SaveModelWithFileMixin`).

**Validação** — `avatar_validation(image)`: se `image` e `image.size > 10 * 1024 * 1024` → `forms.ValidationError(_('The maximum file size is {0}').format(sizeof_fmt(10485760)))` (texto padrão: `The maximum file size is 10.0MiB`).

**Comportamentos**: sem `save()` customizado nem sinais para o avatar; o arquivo é gravado pelo `FileField` no `save()` padrão; arquivos antigos não são apagados na troca; a miniatura é gerada sob demanda por `easy-thumbnails` e registrada nas tabelas `easy_thumbnails_source`, `easy_thumbnails_thumbnail`, `easy_thumbnails_thumbnaildimensions` (migrações da própria biblioteca, aplicadas por estar em `INSTALLED_APPS`).

**Migração inicial**: `0001_initial.py` cria `avatar` (`image_cropping.fields.ImageCropField`, `upload_to="avatars/"`, `validators=[backend.eauth.models.avatar_validation]`) e `avatar_cropping` (`image_cropping.fields.ImageRatioField`, `"avatar"`, `"128x128"`) — por isso `avatar_validation` precisa continuar importável no caminho `backend.eauth.models`.

## 2. Estruturas de arquivos em disco

| Item | Caminho | Observações |
|---|---|---|
| Raiz de mídia | `MEDIA_ROOT` (`<pai do projeto>/backend_media/media`; `/mnt/volumes/backend_media/media` em debug fora do contêiner) | Volume Docker `backend_media` |
| Cache de mídia | `MEDIA_CACHE_ROOT` (`.../backend_media/media_cache`) | Definido, sem consumidor no esqueleto |
| Avatares | `MEDIA_ROOT/avatars/<arquivo>` | `upload_to='avatars/'` |
| Miniaturas | ao lado do original, com sufixo do `easy-thumbnails` (ex.: `<arquivo>.128x128_q85_box-<x1>,<y1>,<x2>,<y2>_crop_detail.jpg`) | Geradas por `get_thumbnail`/`cropped_thumbnail` |
| Área privada | qualquer caminho com `private` | Nunca servido por `/media/` |
| Cache de página PDF (`ResponseFileMixin`) | `<caminho do arquivo>-p<NNN>-d<NNN>.png` | Somente quando a action de arquivo é usada |
| Original preservado (`?original`) | `original__<nome>` | Convenção usada no `X-Accel-Redirect` do `ResponseFileMixin` |

## 3. Classes auxiliares (sem persistência própria)

| Classe | Arquivo | Papel |
|---|---|---|
| `CustomFileField(models.FileField)` | `backend/fields.py` | `attr_class = CustomFieldFile` |
| `CustomFieldFile(FieldFile)` | `backend/fields.py` | `url`, `_url`, `shorten_file_name()`, `delete(save=True)` |
| `SaveModelWithFileMixin` | `backend/model_mixins.py` | `FIELDFILE_NAME = ("arquivo",)`; `save()` em duas etapas |
| `FileFieldCheckMixin(BaseForm)` | `backend/utilss.py` | `clean()`/`_check()` para campos de arquivo |
| `ResponseFileMixin` | `backend/api/mixins.py` | Métodos de resposta de arquivo/PDF |
| `DrfautoapiNegotiation`, `FilesRenderer`, `JpegRenderer`, `JpgRenderer`, `PngRenderer`, `PDFRenderer`, `ZIPRenderer` | `drfautoapi/__init__.py` | Negociação por sufixo |

## 4. Estruturas de configuração (settings)

Valores e nomes em `contracts/campos-e-settings.md`. Variáveis de ambiente usadas: apenas `DEBUG` (via `zenv.py`); `MEDIA_ROOT` depende de `DEBUG` e do caminho físico do projeto.

## 5. Estrutura da resposta de `/api/version` (parte do avatar)

```json
{"name": "Backend", "description": "Plataforma ...", "version": "0.0.1",
 "user": {"username": "<email>", "fullname": "<nome>", "avatar": "/static/imgs/perfil.png | <URL da miniatura 128x128 em /media/...>"}}
```

`user` só existe para usuário autenticado; `version` vem de `settings.PROJECT_VERSION`.
