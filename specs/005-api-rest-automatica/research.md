# Pesquisa e Decisões Técnicas: API REST Automática (`drfautoapi`)

## Decisões

### D1. Biblioteca própria `drfautoapi` em vez de declarar ViewSets à mão

- **Decisão**: gerar `ModelViewSet`, serializer e `FilterSet` por modelo em tempo de importação (`ApiViewSetConstrutor.build_class`) e registrar tudo num roteador único (`router()`).
- **Justificativa**: princípio IV da constituição — "toda entidade de dados é exposta automaticamente em `/api/<app>/<modelo>/`". Zero código por modelo e comportamento uniforme (paginação, filtros, ordenação).
- **Alternativas**: ViewSets manuais por modelo (repetitivo); `drf-auto-endpoint`/`dynamic-rest` (dependência externa menos controlável).

### D2. Customização por convenção de nomes e por settings (`DRFAUTOAPI`)

- **Decisão**: serializer e filterset específicos são descobertos por nome (`<Modelo>Serializer` em `DEFAULT_SERIALIZER_MODULE`, `<Modelo>FilterSet` em `DEFAULT_FILTER_MODULE`) e as bases globais vêm de `GLOBAL_SERIALIZER_MIXIN`/`GLOBAL_FILTERSET_MIXIN`.
- **Justificativa**: a biblioteca não depende do pacote `backend`; o projeto injeta suas classes via configuração.
- **Alternativas**: registro explícito (`register(Model, Serializer)`); atributos no modelo.

### D3. Filtros gerados para todos os lookups de cada campo

- **Decisão**: `ApiFilterSetMixin.get_fields()` enumera `exact` + todos os lookups/transforms do campo (recursivamente), excetuando `contained_by`, `trigram_similar`, `unaccent`, `search`; `filter_for_field` devolve `None` quando não há filtro suportado.
- **Justificativa**: o frontend e integrações precisam filtrar sem alterar o backend (`?campo__icontains=`, `?data__year__gte=`).
- **Alternativas**: `fields = '__all__'` do django-filter (apenas `exact`); lista manual de lookups.

### D4. `SplitStringCharFilter` — busca "todas as palavras"

- **Decisão**: em `icontains`, dividir por espaços e encadear `filter` (AND); suportar frases entre aspas.
- **Justificativa**: busca natural em campos de texto independente da ordem das palavras.
- **Alternativas**: `SearchFilter` do DRF (desativado nos ViewSets gerados); Solr (feature 008).

### D5. Paginação com envelope `pagination` + `results` e `get_all=true`

- **Decisão**: `StandardPagination` (10/página, máx. 100, `page_size`), `get_all=true` desliga a paginação; o esquema OpenAPI é sobrescrito para refletir o envelope.
- **Justificativa**: tabelas do frontend precisam de metadados (`start_index`, `end_index`, `total_entries`) e, às vezes, da lista completa (selects, exportações).
- **Alternativas**: `LimitOffsetPagination`; envelope padrão (`count`, `next`, `previous`, `results`).

### D6. Autenticação dupla (Token + Sessão) e login por sessão via API

- **Decisão**: `TokenAuthentication` e `SessionAuthentication`; `POST /api/auth/token` (`obtain_auth_token`) para integrações e `POST/DELETE /api/auth/session` para o frontend SPA; `recria_token` para administradores.
- **Justificativa**: o SPA reutiliza a sessão/CSRF do Django (sem armazenar token no navegador); scripts usam token.
- **Alternativas**: JWT (`rest_framework_simplejwt`, deixado comentado em `backend/settings/apps.py`).

### D7. Negociação de conteúdo por sufixo com renderers "de fachada"

- **Decisão**: renderers `.pdf/.png/.jpg/.jpeg/.zip` que levantam `Http404` e `DrfautoapiNegotiation` que converte "formato sem renderer" em `404`.
- **Justificativa**: permitir URLs como `/api/<app>/<modelo>/<pk>/arquivo.pdf` em que a view serve o arquivo diretamente (via `ResponseFileMixin`) sem que o DRF responda `404/406` antes por sufixo desconhecido.
- **Alternativas**: rotas separadas sem `format_suffix_patterns`.

### D8. Documentação com `drf-spectacular`

- **Decisão**: Swagger UI, Redoc e esquema JSON/YAML em `/api/schema/…`, com `Schema(AutoSchema)` próprio para futura customização.
- **Justificativa**: documentação viva gerada dos serializers/filtros.
- **Alternativas**: `drf-yasg`, `coreapi` (obsoletos).

### D9. Registro global em `ApiViewSetConstrutor._built_sets`

- **Decisão**: dicionário de classe `{AppConfig: {Model: ViewSet}}` populado por `build_class` e lido por `router()`, `customize`, `wrapper_queryset_response_for_drf_action` e `get_viewset_for_model` (sinais de tempo real).
- **Justificativa**: um único lugar para descobrir o ViewSet de qualquer modelo.
- **Alternativas**: registry por instância de roteador.

## Particularidades, dívidas técnicas e riscos observados

Para cada item: **Recomendação** de uma reconstrução ideal; **estado atual = replicar** para fidelidade.

| # | Observação | Risco | Recomendação |
|---|---|---|---|
| 1 | `fields = '__all__'` sem `UserSerializer` expõe o hash `password` (e `last_login`, permissões) em `/api/eauth/user/` | **Segurança (alto)**: vazamento de hash por quem tem `view_user` | **Corrigir**: criar `UserSerializer` em `backend/api/serializers.py` com `exclude = ('password',)` (o construtor já usa `exclude` herdado). Hoje: replicar |
| 2 | `ResponseFileMixin` (`backend/api/mixins.py`) não é usado por nenhum ViewSet; contém caminho fixo `/home/leandro/TEMP/pdf_anon.pdf` em `DEBUG`, `print(e)` e `except` genérico | Código morto; caminho local fixo; anonimização destrutiva (reescreve o PDF original) | Replicar como código disponível; ao ativar, corrigir caminho e logging |
| 3 | `CustomFieldFile._url` (`backend/fields.py`) faz `reverse('backend.api:<app>_<modelo>-<campo>')`, rota inexistente no esqueleto | `url` de arquivos sempre `''` | Replicar; ou criar `@action(detail=True, url_path='<campo>')` com `ResponseFileMixin` ao adotar arquivos (feature 009) |
| 4 | Renderers de arquivo sempre `Http404` | Somente têm efeito na negociação; confuso | Replicar |
| 5 | `DrfautoapiNegotiation` usa `re.match` (prefixo, sem `$`): `json` casa com `jsonx`; formato desconhecido → `404` em vez de `406` | Comportamento ligeiramente permissivo | Replicar (corrigir com `re.fullmatch` se necessário) |
| 6 | Paginação: `get_all=true` ignora `max_page_size` | Resposta enorme/DoS em tabelas grandes | Replicar; recomendável limitar a um teto |
| 7 | `ApiViewSet.filter_backends = (DjangoFilterBackend,)` ignora `DEFAULT_FILTER_BACKENDS` (que inclui `SearchFilter`) | `?search=` não funciona | Replicar |
| 8 | `filter_o` engole exceções; campo inválido não falha em `order_by` e sim ao avaliar o queryset (erro `FieldError`/500) | Erro tardio | Corrigir com validação contra `model._meta` |
| 9 | `get_keys_lookups` tem ramo morto (`hasattr(lv, "output_field.get_lookups")` sempre falso); também `get_fields` muta `cls._meta.fields` quando for `dict` | Código morto; mutação de Meta compartilhada | Replicar |
| 10 | `BackendSerializerMixin.get_metadata` compara `obj._meta.model == 'Metadata'` (sempre falso) e faz uma consulta por objeto (N+1) | Desempenho em listas | Replicar; otimizar com prefetch se necessário |
| 11 | `get_link_detail_backend` usa `except:` nu e `app_config.name` (ex.: `backend.utils`) como namespace | Silencia erros | Replicar |
| 12 | `BackendSerializerMixin` exige `Meta.model`; o construtor injeta `model` na subclasse | — | Replicar |
| 13 | `AppVersionView` não devolve `is_authenticated`/`permissions` esperados pelo `AuthStore` do frontend | Inconsistência entre 005 e 007 | **Corrigir** se o frontend for usá-los; hoje replicar |
| 14 | `AppVersionView`: `description` = `'Plataforma ...'` e `name` = `'Backend'` fixos; comentário sobre token removido | Placeholder em produção | Replicar |
| 15 | `/api/auth/session` regex sem `$` e `AppSessionAuthView` herda de `ObtainAuthToken` (traz renderers/parsers do próprio DRF, `403`/`400`) | Casa `/api/auth/sessionX` | Replicar |
| 16 | `recria_token`: `pk` `\d*` permite vazio; não valida existência do usuário; sem `transaction.atomic` entre `delete` e `create`; usa `IsAdminUser` (`is_staff`), não superusuário | `500` para usuário inexistente; privilégio de staff para trocar token de qualquer usuário | **Corrigir**: `get_object_or_404`, `atomic`, restringir a superusuário/`change_user`. Hoje replicar |
| 17 | `BusinessRulesNotImplementedMixin` levanta `Exception` genérica em `create/update/delete` (alcançáveis só se `http_method_names` for sobrescrito) e define `delete` (não é método de ViewSet; o nome correto seria `destroy`) | Mixin parcialmente ineficaz (a proteção real é `http_method_names`) | Replicar |
| 18 | `wrapper_queryset_response_for_drf_action` muta a instância do ViewSet (`queryset`, `serializer_class`, `filterset_class`) e filtra o queryset antes de chamar o método decorado | Efeitos colaterais na instância (por requisição, aceitável) | Replicar |
| 19 | `customize` exige que `build_class` já tenha registrado o modelo (`KeyError` caso contrário) e só vale se aplicado **antes** de `router()` | Ordem de importação sensível | Replicar (documentar) |
| 20 | `_built_sets` é estado global de classe; `BackendApiViewSetConstrutor` é apenas alias do mesmo objeto | Testes/reloads acumulam estado | Replicar |
| 21 | `ApiViewSet`/`ModelViewSet` permitem `PUT/PATCH/DELETE`, ou seja, todo modelo exposto é gravável via API conforme permissão (inclui `AuditLog`, `Metadata`, `User`) | Segurança dependente das permissões do modelo | Revisar permissões (feature 003); replicar |
| 22 | Throttling não implementado (`TODO`) | Sem limite de taxa em `/api/auth/token` (força bruta) | **Corrigir**: configurar `DEFAULT_THROTTLE_CLASSES/RATES` |
| 23 | `DEFAULT_PARSER_CLASSES` inclui `FileUploadParser` (exige `filename` na URL/cabeçalho `Content-Disposition`) | Pouco usado | Replicar |
| 24 | `SPECTACULAR_SETTINGS.VERSION = "0.0.1"` fixo; independe de `PROJECT_VERSION` | Dessincronização | Replicar |
| 25 | `backend/api/tests.py` vazio; sem cobertura da API | Regressões | Adicionar testes (ver `tasks.md`) |
| 26 | Imports não usados (`inspect` em `apps.py`, `extend_schema_field` em `serializers.py`, `CharField` etc.) e `import fitz` + `import pymupdf` redundantes em `mixins.py` | Ruído | Replicar (ou limpar com `ruff`) |
| 27 | `get_viewset_for_model` assume que o app do modelo foi construído; `KeyError` caso contrário (usado pelos sinais 006 dentro de `try`) | — | Replicar |
