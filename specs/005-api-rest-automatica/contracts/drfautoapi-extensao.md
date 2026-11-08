# Contrato: Extensão da API Gerada (`drfautoapi`) e Configuração

Este contrato descreve a interface Python da biblioteca `drfautoapi/` para quem a usa ou estende. Referências: `drfautoapi/__init__.py`, `drfautoapi/drfautoapi.py`, `backend/api/mixins.py`, `backend/settings/drf.py`.

## 1. Expor um app/modelo

```python
# backend/api/views_<app>.py
import logging
from django.apps.registry import apps
from drfautoapi.drfautoapi import ApiViewSetConstrutor

logger = logging.getLogger(__name__)
ApiViewSetConstrutor.build_class([apps.get_app_config('<label>')])
```

E acrescentar `'backend.api.views_<app>'` à lista de `BackendApiViewSetConstrutor.import_modules([...])` no fim de `backend/api/views.py`. `build_class` também aceita classes de modelo (`[Teste]`) e mistura de apps e modelos. Só entra na API o que for construído **antes** de `BackendApiViewSetConstrutor.router()` ser chamado em `backend/api/urls.py` (na importação do módulo).

| Método de `ApiViewSetConstrutor` | Assinatura | Retorno |
|---|---|---|
| `build_class` | `(apps_or_models: list[AppConfig | ModelBase])` | `cls` (encadeável) |
| `router` | `(router_class=DrfautoapiRouter)` | instância do roteador com todos os ViewSets registrados |
| `import_modules` | `(modules: list[str])` | `None` |
| `get_viewset_for_model` | `(model)` | classe do ViewSet (`KeyError` se não construído) |
| `update` | `(other)` | mescla `other._built_sets` em `_built_sets` |

## 2. Substituir serializer / filterset de um modelo

| Para | Defina | Em | Convenção |
|---|---|---|---|
| Serializer | `class <ObjectName>Serializer(BackendSerializerMixin)` com `Meta.fields`/`Meta.exclude` | `backend/api/serializers.py` | nome termina em `Serializer`; o construtor completa `ref_name`, `model` e `fields` |
| FilterSet | `class <ObjectName>FilterSet(CustomFilterSetMixin)` com `Meta.fields`/`Meta.exclude` | `backend/api/forms.py` | nome termina em `FilterSet`; `ApiFilterSetMixin.get_fields()` completa lookups dos campos não listados |

`<ObjectName>` é `model._meta.object_name` (ex.: `User`). Exemplo de correção de segurança recomendada (não implementada): `class UserSerializer(BackendSerializerMixin): class Meta: exclude = ('password',)`.

## 3. Decoradores

```python
@customize(Teste)             # recria o ViewSet de Teste herdando (cls, ViewSetGerado)
class TesteViewSet:
    @action(detail=False)
    def extra(self, request): ...

class OutroViewSet(ApiViewSetConstrutor.ApiViewSet):
    @action(detail=True)
    @wrapper_queryset_response_for_drf_action(Teste)
    def testes_relacionados(self, request, pk=None):
        return Teste.objects.filter(...)   # devolve queryset; o decorador filtra/pagina/serializa
```

| Decorador | Entrada | Efeito |
|---|---|---|
| `customize(model)` | classe com métodos/atributos de ViewSet | cria `_ApiViewSet(cls, gerado)`; chama `build()` se existir; substitui em `_built_sets` (precisa ser aplicado antes de `router()`) |
| `wrapper_queryset_response_for_drf_action(model)` | função de ação que devolve queryset | adota `queryset`, `serializer_class`, `filterset_class` do ViewSet de `model`, aplica `filter_queryset`, chama a função, pagina e serializa (`many=True`) |
| `BusinessRulesNotImplementedMixin` (mixin) | — | `http_method_names = ["get","head","options","trace"]` → escrita responde `405` |

## 4. `ResponseFileMixin` (`backend/api/mixins.py`) — algoritmo (não usado hoje)

Uso pretendido: `class XViewSet(ResponseFileMixin, ApiViewSet)` com `@action(detail=True, url_path='<campo-com-hifen>')` cujo nome do método é o **nome do campo de arquivo** (`self.action`), chamando `return self.response_file(request, *args, **kwargs)`.

`response_file(request, *args, **kwargs)`:
1. `self.item = self.get_queryset().filter(pk=kwargs['pk']).first()`; lê `text`, `page` (0), `dpi` (72), `grade` ('0'), `anon` ('') de `request.GET`.
2. `dpi` = `int`, limitado a 72–300 e arredondado para cima em `(72, 100, 150, 200, 300)`; erro → 72.
3. `NotFound` se não há item, se o item não tem atributo `self.action` ou se o arquivo está vazio.
4. `mime = get_mime_type_from_file_extension(arquivo.name)` (`backend/utilss.py`); corrige `application/png|jpg|jpeg` para `image/...`.
5. Superusuário + `anon` + PDF → `self.anon(arquivo, page, grade, anon)` (redação destrutiva dos termos informados via PyMuPDF; com `DEBUG` salva em caminho fixo e não altera o original).
6. `text` + PDF → `response_pdftotext` (`text/plain; charset=utf-8`, `clean_text` de `backend/utilss.py`).
7. `page` + PDF → `response_pagepdftoimage(arquivo, page, dpi, grade)`: `grade` numérica (<10 = sem grade; ≥10 = linhas de grade a cada N pontos) ou `x0,y0,x1,y1` (retângulo destacado, grade 25); cache em `<arquivo>-pNNN-dNNN.png` (ignorado com `nocache`); página inexistente → `NotFound`.
8. Nome de download: último segmento de `arquivo.name` ou `self.custom_filename(item)` se existir.
9. Miniatura (`self.thumbnail()`) quando há `format_kwarg` e o mime é de imagem: formato `<N>.<ext>` → miniatura `N×N` sem recorte; `c<N>.<ext>` → miniatura `N×N` com recorte `crop=True`, `box=<campo>_cropping`, `detail=True` (`easy_thumbnails.get_thumbnailer`).
10. `DEBUG=True`: lê o arquivo (original se `?original`; miniatura se houver) e devolve `HttpResponse` com `Content-Disposition: inline`. Produção: resposta vazia com `X-Accel-Redirect: /mediaredirect/<original__><nome>`, `Cache-Control: no-cache`, `Pragma: no-cache`, `Expires: 0` (o Nginx serve o arquivo — features 009/011).

## 5. Renderers e negociação

| Classe | `media_type` | `format` |
|---|---|---|
| `JpegRenderer` | `image/jpeg` | `[a-zA-Z0-9]*\.?(jpeg|jpg)` |
| `JpgRenderer` | `image/jpg` | `[a-zA-Z0-9]*\.?(jpg|jpeg)` |
| `PngRenderer` | `image/png` | `[a-zA-Z0-9]*\.?png` |
| `PDFRenderer` | `application/pdf` | `pdf` |
| `ZIPRenderer` | `application/zip` | `zip` |
| `DrfautoapiNegotiation` | — | `filter_renderers` com `re.match`; sem correspondência → `Http404` |

Todos importáveis como `drfautoapi.<Nome>` (definidos em `drfautoapi/__init__.py`); `render()` sempre levanta `Http404`.

## 6. Pontos de extensão vazios

- `backend/api/forms.py::CustomFilterSetMixin(ApiFilterSetMixin)`
- `backend/api/schema.py::Schema(AutoSchema)` (`DEFAULT_SCHEMA_CLASS`)
- `ContainerPermission` (`backend/api/permissions.py`, feature 003): variação que apenas registra `view.permission_required`.
