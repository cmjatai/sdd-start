# Plano de Implementação: API REST Automática (`drfautoapi`), Autenticação por Token/Sessão e Documentação OpenAPI

**Branch**: `005-api-rest-automatica` | **Data**: 2026-11-08 | **Especificação**: [spec.md](spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/005-api-rest-automatica/spec.md`

## Resumo

Biblioteca interna `drfautoapi/` que, a partir de modelos Django, constrói `ModelViewSet`s, serializers, `FilterSet`s e um roteador DRF (`/api/<app_label>/<modelo>/`), mais o app `backend/api/` que a configura (serializer base, filtros, paginação com envelope `pagination`/`results`, esquema OpenAPI, views de token/sessão/versão) e `backend/settings/drf.py` (REST_FRAMEWORK, DRFAUTOAPI, SPECTACULAR_SETTINGS). A autorização padrão é `BackendModelPermissions` (feature 003).

## Contexto Técnico

**Linguagem/Versão**: Python `>=3.12,<4.0` (CI/uso em 3.12 e 3.14), Django 6

**Dependências Principais**: `djangorestframework ^3.18.3`, `django-filter ^26.2`, `drf-spectacular ^0.30.0`, `django-image-cropping ^1.7` e `easy-thumbnails ^2.10.1` (avatar/miniaturas), `pymupdf ^2.1` (somente `ResponseFileMixin`; importado como `fitz` e `pymupdf`)

**Armazenamento**: sem tabelas novas; usa `rest_framework.authtoken.Token` (migração do próprio DRF) e modelos existentes

**Testes**: `pytest` + `pytest-django` (`DJANGO_SETTINGS_MODULE = "backend.settings"`, `testpaths = ["**/tests.py", "**/test_*.py"]`); `backend/api/tests.py` hoje é só o esqueleto vazio de `TestCase`

**Plataforma Alvo**: servidor Linux (Docker), Gunicorn/Daphne em produção

**Tipo de Projeto**: serviço web (biblioteca interna + app Django)

**Metas de Desempenho**: página padrão de 10 itens, máximo 100 por página

**Restrições**: sem throttling (apenas `TODO`); `ApiViewSet` só com `DjangoFilterBackend`

**Escala/Escopo**: 2 apps expostos (`eauth`, `utils`), ~4 modelos (`User`, `AuditLog`, `Teste`, `Metadata`)

## Verificação da Constituição

| Princípio | Gate | Situação |
|---|---|---|
| I. Backend Django modular | `drfautoapi/` (biblioteca) e `backend/api/` (app com `apps.py`, `urls.py`, `views.py`), registrado em `backend/settings/apps.py`; settings em `backend/settings/drf.py` | Atendido |
| II. Configuração por ambiente, sem segredos | Nenhum segredo; `PROJECT_VERSION` vem de `backend/settings/project.py` | Atendido |
| III. Paridade dev/prod via Docker | `_docker/prod/Dockerfile` copia `drfautoapi/` (`ADD drfautoapi ${HOME}/drfautoapi`); mesma configuração nos dois | Atendido |
| IV. API REST gerada, permissões por modelo | Núcleo desta feature: `/api/<app>/<modelo>/`, paginação/filtros/ordenação, OpenAPI; permissão `BackendModelPermissions` | Atendido |
| V. Frontend Vite integrado | `/api/version`, `/api/auth/session` consumidos pelo frontend (007) | Atendido (com ressalva: `/api/version` não devolve `is_authenticated`/`permissions`) |
| VI. Tempo real e tarefas assíncronas | `ApiViewSetConstrutor.get_viewset_for_model` é usado pelos sinais de sincronização (006) | Atendido |
| VII. Português do Brasil | Mensagens de resposta e esquema em português (`gettext_lazy`) | Atendido |
| VIII. Qualidade verificável | Testes `pytest` e `ruff` definidos em `tasks.md`; hoje a cobertura própria é inexistente | Atendido com dívida (ver `research.md`) |

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/005-api-rest-automatica/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── contracts/
    ├── endpoints-api.md
    └── drfautoapi-extensao.md
```

### Código-Fonte (raiz do repositório)

```text
drfautoapi/
├── __init__.py          # DrfautoapiNegotiation + renderers de arquivo
└── drfautoapi.py        # filtros, roteador, ApiViewSetConstrutor, decoradores
backend/
├── api/
│   ├── __init__.py      # default_app_config = 'backend.api.apps.ApiConfig'
│   ├── apps.py          # ApiConfig(name='backend.api', label='api')
│   ├── urls.py          # rotas /api/...
│   ├── views.py         # recria_token, AppSessionAuthView, AppVersionView, BackendApiViewSetConstrutor
│   ├── views_eauth.py   # build_class([eauth])
│   ├── views_utils.py   # build_class([utils])
│   ├── serializers.py   # BackendSerializerMixin
│   ├── forms.py         # CustomFilterSetMixin
│   ├── pagination.py    # StandardPagination
│   ├── schema.py        # Schema(AutoSchema)
│   ├── mixins.py        # ResponseFileMixin (não usado)
│   ├── permissions.py   # BackendModelPermissions (feature 003 — apenas referenciada)
│   ├── admin.py, models.py (vazios), tests.py
└── settings/drf.py      # REST_FRAMEWORK, DRFAUTOAPI, SPECTACULAR_SETTINGS
```

**Decisão de Estrutura**: a biblioteca genérica (`drfautoapi/`, sem dependência de `backend`) fica separada do app de projeto (`backend/api/`), que injeta, via `DRFAUTOAPI` em settings, o módulo de serializers, o módulo de filtros e os mixins globais. A raiz `backend/urls.py` faz `path("", include("backend.api.urls"))`.

## Detalhamento de Implementação

### 1. Settings (`backend/settings/drf.py`)

- `REST_FRAMEWORK`:
  - `DEFAULT_PARSER_CLASSES`: `rest_framework.parsers.JSONParser`, `MultiPartParser`, `FileUploadParser`.
  - `DEFAULT_RENDERER_CLASSES`: `rest_framework.renderers.JSONRenderer`, `drfautoapi.PDFRenderer`, `drfautoapi.PngRenderer`, `drfautoapi.JpgRenderer`, `drfautoapi.JpegRenderer`, `drfautoapi.ZIPRenderer`.
  - `DEFAULT_CONTENT_NEGOTIATION_CLASS`: `drfautoapi.DrfautoapiNegotiation`.
  - `DEFAULT_PERMISSION_CLASSES`: `("backend.api.permissions.BackendModelPermissions",)`.
  - `DEFAULT_AUTHENTICATION_CLASSES`: `TokenAuthentication`, `SessionAuthentication` (nessa ordem).
  - `DEFAULT_SCHEMA_CLASS`: `backend.api.schema.Schema`.
  - `DEFAULT_PAGINATION_CLASS`: `backend.api.pagination.StandardPagination`.
  - `DEFAULT_FILTER_BACKENDS`: `rest_framework.filters.SearchFilter`, `django_filters.rest_framework.DjangoFilterBackend` (sobrescrito pelos ViewSets gerados).
  - Comentário `# TODO: rate limiting` (https://www.django-rest-framework.org/api-guide/throttling/).
- `DRFAUTOAPI`: `DEFAULT_SERIALIZER_MODULE = "backend.api.serializers"`, `DEFAULT_FILTER_MODULE = "backend.api.forms"`, `GLOBAL_SERIALIZER_MIXIN = "backend.api.serializers.BackendSerializerMixin"`, `GLOBAL_FILTERSET_MIXIN = "backend.api.forms.CustomFilterSetMixin"`.
- `SPECTACULAR_SETTINGS`: `TITLE = "Backend API - docs"`, `DESCRIPTION = "API de dados do Backend. Documentação dos modelos, seus atributos, filtros de busca e endpoint's de comunicação RestFULL."`, `VERSION = "0.0.1"`.
- `INSTALLED_APPS` (`backend/settings/apps.py`): `drf_spectacular`, `rest_framework`, `django_filters`, `rest_framework.authtoken` e `backend.api`. O módulo `drf.py` deve ser importado por `backend/settings/project.py` (feature 001).

### 2. Negociação e renderers (`drfautoapi/__init__.py`)

- `DrfautoapiNegotiation(DefaultContentNegotiation).filter_renderers(renderers, format)`: mantém os renderers para os quais `re.match(renderer.format, format)` casa; se a lista ficar vazia, `raise Http404`.
- `FilesRenderer(BaseRenderer)`: `render()` sempre `raise Http404`.
- Subclasses (`media_type` / `format`): `JpegRenderer` `image/jpeg` / `r'[a-zA-Z0-9]*\.?(jpeg|jpg)'`; `JpgRenderer` `image/jpg` / `r'[a-zA-Z0-9]*\.?(jpg|jpeg)'`; `PngRenderer` `image/png` / `r'[a-zA-Z0-9]*\.?png'`; `PDFRenderer` `application/pdf` / `'pdf'`; `ZIPRenderer` `application/zip` / `'zip'`.
- O prefixo `[a-zA-Z0-9]*\.?` permite sufixos como `c200.jpg` (miniaturas) para uso futuro de `ResponseFileMixin.thumbnail`. O `JSONRenderer` tem `format='json'`.

### 3. Filtros (`drfautoapi/drfautoapi.py`)

- `SplitStringCharFilter(django_filters.CharFilter)`; `_re = re.compile(r'("[^"]+"| +|[^"]+)')`. `filter(qs, value)`:
  1. `value in EMPTY_VALUES` → devolve `qs`; se `self.distinct` → `qs.distinct()`.
  2. `lookup = f"{field_name}__{lookup_expr}"`; `values = [value]`.
  3. Se `lookup_expr == "icontains"`: sem `"` no valor → `value.split(" ")`; com aspas → termos fora de aspas (`x and x != " " and x[0] != '"'`) + frases entre aspas sem as aspas (`x[1:-1]`), obtidos de `_re.findall(value)`.
  4. Para cada `v`: `qs = self.get_method(qs)(**{lookup: v})` (encadeia `filter`/`exclude` → AND).
- `ApiFilterSetMixin(FilterSet)`:
  - `o = CharFilter(method="filter_o")`; `filter_o` faz `queryset.order_by(*map(str.strip, value.split(",")))` com `except: return queryset`.
  - `Meta.fields = "__all__"` e `filter_overrides`: `FileField` → `CharFilter` (`extra: lookup_expr='exact'`); `CharField`/`TextField` → `SplitStringCharFilter`; `JSONField` → `CharFilter` (`lookup_expr='exact'`).
  - `get_fields()` (classmethod): `fields_model = get_all_model_fields(model)`; `fields_filter = cls._meta.fields`; `exclude = cls._meta.exclude`; se `exclude is not None and fields_filter is None` → `ALL_FIELDS`; `fields = fields_filter if dict else {}`. Para cada campo do modelo ausente em `fields`: M2M → `["exact"]`; demais → `["exact"]` ∪ `get_keys_lookups(f.get_lookups(), "")`. `get_keys_lookups(lookups, prefixo)` percorre os lookups/transforms do campo, ignora `contained_by`, `trigram_similar`, `unaccent`, `search`, gera nomes encadeados (`prefixo__lookup`) e recorre em `lv.get_lookups()` quando existir (transforms, ex.: `year__gte`). Há um ramo morto (`hasattr(lv, "output_field.get_lookups")` nunca é verdadeiro). Por fim remove `exclude` e devolve `OrderedDict`.
  - `filter_for_field(cls, f, name, lookup_expr="exact")` (classmethod): `f, lookup_type = resolve_field(f, lookup_expr)`; `default = {field_name, label=capfirst(f.verbose_name), lookup_expr}`; `filter_class, params = cls.filter_for_lookup(f, lookup_type)`; devolve instância ou `None` se não houver classe (ignora lookups sem filtro).
- `BusinessRulesNotImplementedMixin`: `http_method_names = ["get","head","options","trace"]`; `create`, `update`, `delete` levantam `Exception(_("POST Create não implementado"))`, `_("PUT and PATCH não implementado")`, `_("DELETE Delete não implementado")`.

### 4. Roteador e construtor

- `DrfautoapiRouter(DefaultRouter).get_urls()`: `urls = super(DefaultRouter, self).get_urls()` (pula a lógica de DefaultRouter e usa `SimpleRouter`); se `include_root_view` adiciona `path("", view, name=self.root_view_name)` com `view = self.get_api_root_view(api_urls=urls)`; se `include_format_suffixes` → `format_suffix_patterns(urls, allowed=["[a-zA-Z.0-9]+"])`.
- `ApiViewSetConstrutor`:
  - `_built_sets = {}` (atributo de classe compartilhado; `BackendApiViewSetConstrutor = ApiViewSetConstrutor` é o **mesmo** objeto).
  - `ApiViewSet(ModelViewSet)` com `filter_backends = (DjangoFilterBackend,)`.
  - `get_viewset_for_model(model)` → `_built_sets[model._meta.app_config][model]`; `update(other)` → `_built_sets.update(other._built_sets)`; `import_modules(modules)` → `importlib.import_module` de cada um.
  - `router(router_class=DrfautoapiRouter)`: `router.register(f"{app.label}/{model._meta.model_name}", viewset, basename=f"{app.label}_{model._meta.model_name}")` para todo app/modelo em `_built_sets`.
  - `build_class(apps_or_models)`:
    1. Lê `settings.DRFAUTOAPI`; dentro de `try/except Exception → logger.error(e)`: importa `DEFAULT_SERIALIZER_MODULE` e coleta com `inspect.getmembers` os membros cujo nome termina em `Serializer`; idem `DEFAULT_FILTER_MODULE` para `FilterSet`; resolve `GLOBAL_SERIALIZER_MIXIN` e `GLOBAL_FILTERSET_MIXIN` por `"modulo.Classe".split(".")` (padrões: `rest_framework.serializers.ModelSerializer` e `ApiFilterSetMixin`).
    2. Para cada modelo, `build(_model)`: `object_name = _model._meta.object_name`; escolhe `<object_name>Serializer` e `<object_name>FilterSet` (senão globais).
    3. Cria `ApiSerializer(_serializer_class)` com `Meta(_meta_serializer)` (ou `object` se a classe não tem `Meta`) definindo `ref_name = f"{object_name}Serializer"` (se não existir), `model = _model` (se não existir) e `exclude` herdado quando existe; senão `fields = "__all__"` (se ausente), `list(fields)` quando lista, ou `"__all__"`.
    4. Cria `ApiFilterSet(_filterset_class)` com `Meta(_meta_filterset)` definindo `model = _model` se ausente.
    5. Cria `ModelApiViewSet(ApiViewSetConstrutor.ApiViewSet)` com `queryset = _model.objects.all()`, `filterset_class = ApiFilterSet`, `serializer_class = ApiSerializer`; `__name__ = f"{_model.__name__}ModelViewSet"`.
    6. Para cada item de `apps_or_models`: se `ModelBase` → `app = am._meta.app_config`; garante `_built_sets[app] = {}`; se for modelo → só ele; se for app → `app.get_models()`. Devolve `cls` (encadeável).
- Decoradores:
  - `customize(model)`: `__call__(cls)` cria `_ApiViewSet(cls, <viewset gerado>)`; se tiver `build` → `_ApiViewSet = _ApiViewSet.build()`; grava de volta em `_built_sets[app][model]` e devolve.
  - `wrapper_queryset_response_for_drf_action(model)`: `__call__(cls)` devolve `wrapper(instance_view, *args, **kwargs)` que copia `queryset`/`serializer_class`/`filterset_class` do ViewSet gerado para a instância, faz `iv.queryset = iv.filter_queryset(iv.get_queryset())`, chama `cls(instance_view, ...)` → `qs`, pagina (`iv.paginate_queryset`), serializa (`many=True`) e devolve `get_paginated_response(data)` ou `Response(data)`.

### 5. App `backend/api`

- `apps.py`: `ApiConfig(AppConfig)` com `name = 'backend.api'`, `label = 'api'`; `__init__.py`: `default_app_config = 'backend.api.apps.ApiConfig'`.
- `serializers.py` — `BackendSerializerMixin(serializers.ModelSerializer)`: campos `__str__ = SerializerMethodField()`, `metadata = SerializerMethodField()`, `link_detail_backend = SerializerMethodField()`; `Meta.fields = '__all__'`. `get_link_detail_backend(obj) -> str`: `reverse(f'{Meta.model._meta.app_config.name}:{model_name}_detail', kwargs={'pk': obj.pk})` com `except` → `''`; `get___str__(obj) -> str`: `str(obj)`; `get_metadata(obj) -> dict`: `Metadata.objects.get(content_type=ContentType.objects.get_for_model(obj._meta.model), object_id=obj.id).metadata`, `{}` em qualquer exceção (há um teste `obj._meta.model == 'Metadata'` que nunca é verdadeiro). Anotações de retorno servem ao `drf_spectacular` (`extend_schema_field` importado e não usado).
- `forms.py`: `CustomFilterSetMixin(ApiFilterSetMixin)` vazio. `schema.py`: `Schema(AutoSchema)` vazio.
- `pagination.py` — `StandardPagination(PageNumberPagination)`: `page_size = 10`, `page_size_query_param = 'page_size'`, `max_page_size = 100`; `paginate_queryset` devolve `None` se `request.query_params.get('get_all','').lower() == 'true'`; `get_paginated_response(data)` monta o envelope (captura `EmptyPage` de `previous_page_number()`/`next_page_number()` → `None`; `start_index()`, `end_index()`, `paginator.count`, `paginator.num_pages`, `page.number`; links por `get_next_link()`/`get_previous_link()`); `get_paginated_response_schema(schema)` devolve objeto OpenAPI com `pagination` (`links.next/previous` string uri nullable; inteiros `previous_page`, `next_page`, `start_index`, `end_index`, `total_entries`, `total_pages`, `page`, todos com `example: 123`) e `results: schema`.
- `views.py`:
  - `recria_token(request, pk)`: `@api_view(['POST'])`, `@permission_classes([IsAdminUser])`; `Token.objects.filter(user_id=pk).delete()`; `Token.objects.create(user_id=pk)`; `Response({'message': 'Token recriado com sucesso!', 'token': token.key})`.
  - `AppSessionAuthView(ObtainAuthToken)`: `post` → `serializer = self.get_serializer(data=request.data)`; `is_valid(raise_exception=True)`; `login(request, serializer.validated_data['user'])`; `Response({'detail': _('Autenticação efetuada com sucesso!')})`. `delete` → `logout(request)`; `Response({'detail': _('Desconexão efetuada com sucesso!')})`.
  - `AppVersionView(APIView)`: `permission_classes = (AllowAny,)`; `get` devolve `{'name': 'Backend', 'description': 'Plataforma ...', 'version': settings.PROJECT_VERSION}`; se `request.user.is_authenticated`, acrescenta `user = {username, fullname: get_full_name(), avatar}` onde `avatar = '/static/imgs/perfil.png'` se vazio ou `image_cropping.utils.get_backend().get_thumbnail_url(user.avatar, {'size': (128,128), 'box': user.avatar_cropping, 'crop': True, 'detail': True})`.
  - Fim do arquivo: `BackendApiViewSetConstrutor = ApiViewSetConstrutor` e `BackendApiViewSetConstrutor.import_modules(['backend.api.views_eauth', 'backend.api.views_utils'])`.
- `views_eauth.py`: `ApiViewSetConstrutor.build_class([apps.get_app_config('eauth')])`; `views_utils.py`: idem com `'utils'`. Cada arquivo tem `logger = logging.getLogger(__name__)`.
- `urls.py`: `app_name = ApiConfig.name` (`'backend.api'`); `router_backend = BackendApiViewSetConstrutor.router()` (executado na importação, depois de `views.py` registrar os apps); `urlpatterns_api_doc` = `^schema/swagger-ui/` (`SpectacularSwaggerView.as_view(url_name='backend.api:schema_api')`, nome `swagger_ui_schema_api`), `^schema/redoc/` (`SpectacularRedocView`, nome `redoc_schema_api`), `^schema/` (`SpectacularAPIView`, nome `schema_api`) — nessa ordem; `urlpatterns`: `^api/` + docs, `^api/` + `router_backend.urls`, `^api/version$` (sem nome), `^api/auth/token$` (`obtain_auth_token`, sem nome), `^api/auth/session` (`AppSessionAuthView`, sem `$` e sem nome), `^api/recriar-token/(?P<pk>\d*)$` (nome `recria_token`).
- `mixins.py` — `ResponseFileMixin` (não usado): ver `contracts/drfautoapi-extensao.md` §4 para o algoritmo.
- Pontos de integração fora do escopo: `backend/fields.py` (`CustomFieldFile`, feature 009) tenta `reverse('backend.api:<app>_<modelo>-<campo-com-hifen>', kwargs={'pk': ...})`; `backend/utils/services/signals_syncrefresh.py` (feature 006) importa `ApiViewSetConstrutor` para serializar; `_templates/eauth/user_form.html` chama `{% url 'backend.api:recria_token' object.id %}`; `_templates/utils/teste_list.html` usa `url_openapi='backend.api:utils_teste-list'`.

### 6. Variáveis de ambiente

Nenhuma específica. Usa `settings.PROJECT_VERSION`, `DEBUG` (apenas em `ResponseFileMixin`) e a `SECRET_KEY`/sessões/CSRF das features anteriores.

## Rastreamento de Complexidade

Sem violações. Observações: `format_suffix_patterns` com regex ampla e `DrfautoapiRouter.get_urls` chamando `super(DefaultRouter, self)` são escolhas deliberadas (ver `research.md`).
