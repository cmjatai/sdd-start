# Modelo de Dados: API REST Automática (`drfautoapi`)

**Não há tabelas novas nesta feature.** `backend/api/models.py` e `backend/api/admin.py` estão vazios e `backend.api` não possui migrações. A feature usa apenas:

- `rest_framework.authtoken.Token` (app `rest_framework.authtoken`, migração do próprio DRF; um token por usuário, `OneToOne` com `AUTH_USER_MODEL`, chave de 40 caracteres hex);
- modelos de outras features, expostos automaticamente: `eauth.User`, `eauth.AuditLog` (feature 002), `utils.Teste`, `utils.Metadata` (features 001/004).

Abaixo, as estruturas de dados relevantes (configuração, registro em memória e formatos de resposta).

## 1. Registro em memória: `ApiViewSetConstrutor._built_sets`

| Chave | Valor | Preenchido por |
|---|---|---|
| `AppConfig` (ex.: `apps.get_app_config('utils')`) | `dict[ModelBase, ViewSet]` | `build_class` em `backend/api/views_eauth.py` e `views_utils.py` |

Recursos resultantes (rota → basename → nomes de URL):

| Rota (`/api/…`) | basename | Nomes de URL (namespace `backend.api`) |
|---|---|---|
| `eauth/user/` | `eauth_user` | `eauth_user-list`, `eauth_user-detail` |
| `eauth/auditlog/` | `eauth_auditlog` | `eauth_auditlog-list`, `eauth_auditlog-detail` |
| `utils/teste/` | `utils_teste` | `utils_teste-list`, `utils_teste-detail` |
| `utils/metadata/` | `utils_metadata` | `utils_metadata-list`, `utils_metadata-detail` |

(O conjunto exato é `app.get_models()` de cada app; modelos futuros entram automaticamente.) A raiz `GET /api/` tem o nome `api-root`.

## 2. Configuração `DRFAUTOAPI` (`backend/settings/drf.py`)

| Chave | Valor | Uso |
|---|---|---|
| `DEFAULT_SERIALIZER_MODULE` | `backend.api.serializers` | procura classes `*Serializer` por nome `<Modelo>Serializer` |
| `DEFAULT_FILTER_MODULE` | `backend.api.forms` | procura classes `*FilterSet` por nome `<Modelo>FilterSet` |
| `GLOBAL_SERIALIZER_MIXIN` | `backend.api.serializers.BackendSerializerMixin` | base de todos os serializers sem classe específica |
| `GLOBAL_FILTERSET_MIXIN` | `backend.api.forms.CustomFilterSetMixin` | base de todos os filtersets sem classe específica |

Todas as chaves são opcionais; na ausência/erro: `rest_framework.serializers.ModelSerializer` e `drfautoapi.drfautoapi.ApiFilterSetMixin`.

## 3. Estrutura de classes geradas por modelo

| Classe | Base | Atributos definidos |
|---|---|---|
| `ApiSerializer` | serializer escolhido | `Meta.ref_name = '<ObjectName>Serializer'`, `Meta.model`, `Meta.fields = '__all__'` (ou lista / `exclude` herdado) |
| `ApiFilterSet` | filterset escolhido | `Meta.model` (e `Meta.fields = "__all__"` herdado de `ApiFilterSetMixin`) |
| `<Modelo>ModelViewSet` | `ApiViewSetConstrutor.ApiViewSet` (`ModelViewSet`, `filter_backends = (DjangoFilterBackend,)`) | `queryset = Modelo.objects.all()`, `filterset_class`, `serializer_class` |

## 4. Campos adicionais do serializer global (`BackendSerializerMixin`)

| Campo | Tipo | Origem |
|---|---|---|
| `__str__` | string (somente leitura) | `str(obj)` |
| `metadata` | objeto JSON (somente leitura) | `Metadata.metadata` do par (`ContentType` do modelo, `object_id = obj.id`); `{}` se não existir/erro |
| `link_detail_backend` | string (somente leitura) | `reverse('<app_config.name>:<model_name>_detail', kwargs={'pk': obj.pk})` ou `''` |
| demais campos | conforme modelo | `fields = '__all__'` (inclui o hash `password` de `User` — ver `research.md` #1) |

## 5. Filtros gerados por tipo de campo

| Tipo de campo | Classe do filtro | Lookups |
|---|---|---|
| `CharField`, `TextField` | `SplitStringCharFilter` | `exact` + todos os lookups/transforms do campo |
| `FileField` (e derivados) | `CharFilter` | somente `exact` |
| `JSONField` | `CharFilter` | somente `exact` |
| `ManyToManyField` | filtro padrão do django-filter | somente `exact` |
| demais | filtro padrão do django-filter para o tipo | `exact` + todos os lookups/transforms (ex.: `gte`, `lte`, `in`, `isnull`, `year`, `year__gte`) |
| (extra) `o` | `CharFilter(method="filter_o")` | ordenação por lista separada por vírgula |

Exclusões: `contained_by`, `trigram_similar`, `unaccent`, `search`. Nome do parâmetro: `<campo>` para `exact` e `<campo>__<lookup>` para os demais.

## 6. Formatos de resposta

**Lista paginada** (padrão):

```json
{
  "pagination": {
    "links": {"next": "http://…/?page=2", "previous": null},
    "previous_page": null,
    "next_page": 2,
    "start_index": 1,
    "end_index": 10,
    "total_entries": 25,
    "total_pages": 3,
    "page": 1
  },
  "results": [{"id": 1, "teste": "x", "__str__": "x", "metadata": {}, "link_detail_backend": "/teste/1"}]
}
```

**Lista completa** (`?get_all=true`): lista JSON simples `[ {...}, ... ]`.

**Versão** (`GET /api/version`): `{"name", "description", "version"}` + `user: {"username", "fullname", "avatar"}` se autenticado.

**Token**: `{"token": "<40 hex>"}` (`/api/auth/token`) ou `{"message", "token"}` (`/api/recriar-token/<pk>`).

**Sessão**: `{"detail": "<mensagem>"}`.

## 7. Migrações

Nenhuma migração própria. É necessário que `rest_framework.authtoken` esteja em `INSTALLED_APPS` para que `python manage.py migrate` crie a tabela `authtoken_token`.
