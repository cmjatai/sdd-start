# Especificação da Funcionalidade: API REST Automática (`drfautoapi`), Autenticação por Token/Sessão e Documentação OpenAPI

**Branch da Funcionalidade**: `005-api-rest-automatica`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: biblioteca interna `drfautoapi/` (filtros, roteador e construtor de ViewSets), app `backend/api/` (urls, views de token/sessão/versão, serializers, filtros, paginação, schema, mixin de arquivos), configuração `backend/settings/drf.py` (REST_FRAMEWORK, DRFAUTOAPI, SPECTACULAR_SETTINGS) e documentação Swagger/Redoc."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Todo modelo vira um recurso REST sem escrever código (Prioridade: P1)

Uma pessoa desenvolvedora cria um modelo Django em um app do projeto (hoje `eauth` e `utils`) e declara, uma única vez, que o app deve ser exposto (`ApiViewSetConstrutor.build_class([apps.get_app_config('<app>')])`). Sem escrever serializer, filtro, ViewSet ou rota, o modelo passa a existir em `/api/<app_label>/<modelo>/` com listagem, detalhe, criação, alteração e exclusão, usando o mesmo mecanismo para todos os modelos.

**Por que esta prioridade**: é o núcleo da funcionalidade e a razão de existir de `drfautoapi`; o frontend (feature 007), a sincronização em tempo real (feature 006) e as telas de lista (feature 004) consomem esses endpoints.

**Teste Independente**: com um superusuário autenticado, `GET /api/utils/teste/` devolve `200` com a lista paginada; `POST /api/utils/teste/` com `{"teste": "x"}` cria o registro e devolve `201`; `GET /api/utils/teste/<pk>/`, `PUT/PATCH` e `DELETE` funcionam; `GET /api/` mostra a raiz da API com todos os recursos.

**Cenários de Aceitação**:

1. **Dado** um app registrado em `ApiViewSetConstrutor.build_class`, **Quando** o roteador é construído, **Então** cada modelo do app é registrado em `<app_label>/<modelo>` com `basename` `<app_label>_<modelo>` (ex.: `utils_teste`, rotas `utils_teste-list` e `utils_teste-detail` no namespace `backend.api`).
2. **Dado** um modelo sem serializer/filterset próprios, **Quando** o recurso é consultado, **Então** o serializer expõe todos os campos (`fields = '__all__'`) mais `__str__`, `metadata` e `link_detail_backend`.
3. **Dado** um modelo cujo app define `<Modelo>Serializer` em `backend.api.serializers` (ou `<Modelo>FilterSet` em `backend.api.forms`), **Quando** o construtor roda, **Então** essa classe é usada no lugar do padrão global.
4. **Dado** um modelo com `ManyToMany`, **Quando** o filtro é gerado, **Então** apenas o lookup `exact` é oferecido para esse campo.
5. **Dado** que o recurso aceita sufixo de formato, **Quando** se acessa `/api/utils/teste/1.json`, **Então** a resposta é JSON; **Quando** se acessa um formato sem renderer correspondente (ex.: `.xyz`), **Então** a resposta é `404`.

---

### História de Usuário 2 - Listar com paginação, busca textual e ordenação padronizadas (Prioridade: P1)

Quem consome a API (frontend ou integração) lista qualquer recurso com um formato de paginação único e pode filtrar por qualquer campo com vários lookups, buscar por palavras em campos de texto e ordenar por qualquer campo.

**Por que esta prioridade**: sem paginação, filtros e ordenação consistentes os consumidores (tabelas do frontend) teriam de ser escritos recurso a recurso.

**Teste Independente**: criar 25 registros de `Teste`; `GET /api/utils/teste/` devolve `results` com 10 itens e bloco `pagination` com `total_entries=25`, `total_pages=3`, `page=1`; `?page_size=5` devolve 5; `?page_size=1000` limita a 100; `?get_all=true` devolve a lista completa **sem** `pagination`.

**Cenários de Aceitação**:

1. **Dado** mais de 10 registros, **Quando** `GET /api/<app>/<modelo>/`, **Então** a resposta é `{"pagination": {"links": {"next", "previous"}, "previous_page", "next_page", "start_index", "end_index", "total_entries", "total_pages", "page"}, "results": [...]}` com 10 itens.
2. **Dado** `?get_all=true` (qualquer capitalização), **Quando** a lista é pedida, **Então** a resposta é uma lista simples (sem o envelope de paginação) com todos os registros filtrados.
3. **Dado** `?page_size=N`, **Quando** N > 100, **Então** o tamanho da página é 100.
4. **Dado** um campo de texto, **Quando** `?teste__icontains=ana silva` é enviado, **Então** são retornados registros que contêm **todas** as palavras (`ana` E `silva`), em qualquer ordem; **Quando** o valor contém aspas (`"ana silva" maria`), **Então** o trecho entre aspas é tratado como uma frase única.
5. **Dado** `?o=-teste,id`, **Quando** a lista é pedida, **Então** o resultado é ordenado por `teste` decrescente e depois `id`; **Quando** o valor de `o` é inválido, **Então** a ordenação é ignorada sem erro.
6. **Dado** `?teste=abc` (lookup `exact`) ou `?id__gte=10` (lookup sufixado), **Quando** a lista é pedida, **Então** apenas os registros que satisfazem o filtro são retornados.
7. **Dado** um campo de arquivo ou JSON, **Quando** é filtrado, **Então** só o lookup `exact` por texto é oferecido.

---

### História de Usuário 3 - Autenticar por token ou por sessão e gerenciar o token (Prioridade: P1)

Integrações obtêm um token (`POST /api/auth/token`) e o enviam em `Authorization: Token <chave>`. O frontend usa sessão (cookie) via `POST /api/auth/session` (login) e `DELETE /api/auth/session` (logout). Administradores podem recriar o token de qualquer usuário.

**Por que esta prioridade**: a API é protegida por padrão; sem uma forma de autenticar, nenhum recurso é utilizável.

**Teste Independente**: `POST /api/auth/token` com credenciais válidas devolve `{"token": "..."}`; `GET /api/utils/teste/` com `Authorization: Token ...` devolve `200` para usuário com permissão; `POST /api/auth/session` seguido de `GET` com o cookie de sessão funciona; `DELETE /api/auth/session` encerra a sessão.

**Cenários de Aceitação**:

1. **Dado** credenciais válidas, **Quando** `POST /api/auth/token`, **Então** devolve o token do usuário (criado se não existir).
2. **Dado** credenciais válidas, **Quando** `POST /api/auth/session`, **Então** a sessão Django é criada e a resposta é `{"detail": "Autenticação efetuada com sucesso!"}`.
3. **Dado** credenciais inválidas em `/api/auth/session`, **Quando** enviadas, **Então** a resposta é `400` com os erros do serializer do DRF.
4. **Dado** uma sessão ativa, **Quando** `DELETE /api/auth/session`, **Então** a sessão é encerrada e a resposta é `{"detail": "Desconexão efetuada com sucesso!"}`.
5. **Dado** um administrador (`is_staff`), **Quando** `POST /api/recriar-token/<pk>`, **Então** o token do usuário `<pk>` é removido, um novo é criado e a resposta traz `{"message": "Token recriado com sucesso!", "token": "<nova chave>"}`.
6. **Dado** um usuário não administrador ou anônimo, **Quando** chama `/api/recriar-token/<pk>`, **Então** a resposta é `403` (ou `401`/`403` conforme autenticação).

---

### História de Usuário 4 - Autorização por permissões de modelo, com leitura pública configurável (Prioridade: P2)

Cada método HTTP exige a permissão Django correspondente do modelo (`list_`/`view_` para leitura, `add_`, `change_`, `delete_`). Modelos/ações marcados como públicos na tabela de regras globais podem ser lidos sem autenticação.

**Por que esta prioridade**: protege os dados, mas a classe de permissão pertence à feature 003 (`BackendModelPermissions`); aqui ela só é configurada como padrão da API.

**Teste Independente**: anônimo em `GET /api/eauth/user/` recebe `401`/`403`; usuário sem permissão recebe `403`; superusuário recebe `200`.

**Cenários de Aceitação**:

1. **Dado** `DEFAULT_PERMISSION_CLASSES = ('backend.api.permissions.BackendModelPermissions',)`, **Quando** qualquer recurso gerado é acessado, **Então** a permissão exigida é derivada do método e do modelo.
2. **Dado** que as autenticações padrão são `TokenAuthentication` e `SessionAuthentication`, **Quando** uma requisição traz token ou cookie de sessão, **Então** o usuário é identificado por um deles.

---

### História de Usuário 5 - Consultar a documentação interativa da API (Prioridade: P2)

Pessoas desenvolvedoras abrem `/api/schema/swagger-ui/` ou `/api/schema/redoc/` e navegam pelos modelos, atributos, filtros e endpoints; o esquema OpenAPI bruto está em `/api/schema/`.

**Por que esta prioridade**: facilita a integração, mas a API funciona sem ela.

**Teste Independente**: `GET /api/schema/` devolve o esquema OpenAPI (título "Backend API - docs", versão "0.0.1") com os caminhos `/api/utils/teste/`; as páginas Swagger e Redoc carregam apontando para esse esquema; a resposta paginada documentada contém `pagination` e `results`.

**Cenários de Aceitação**:

1. **Dado** o servidor no ar, **Quando** `GET /api/schema/swagger-ui/`, **Então** a página Swagger UI é servida usando `backend.api:schema_api`.
2. **Dado** o servidor no ar, **Quando** `GET /api/schema/redoc/`, **Então** a página Redoc é servida.
3. **Dado** um recurso paginado, **Quando** o esquema é gerado, **Então** a resposta de listagem documenta o envelope `{pagination: {...}, results: <schema>}`.

---

### História de Usuário 6 - Obter versão do sistema e usuário corrente (Prioridade: P3)

O frontend consulta `GET /api/version` (sem exigir autenticação) para obter nome, descrição e versão do backend e, se houver usuário autenticado, seus dados básicos para exibição.

**Por que esta prioridade**: conveniência de inicialização do frontend.

**Teste Independente**: `GET /api/version` anônimo devolve `{"name": "Backend", "description": "Plataforma ...", "version": "0.0.1"}`; autenticado, acrescenta `user` com `username`, `fullname` e `avatar`.

**Cenários de Aceitação**:

1. **Dado** um anônimo, **Quando** `GET /api/version`, **Então** a resposta contém apenas `name`, `description` e `version` (valor de `settings.PROJECT_VERSION`).
2. **Dado** um usuário autenticado sem avatar, **Quando** `GET /api/version`, **Então** `user.avatar` é `/static/imgs/perfil.png`.
3. **Dado** um usuário autenticado com avatar, **Quando** `GET /api/version`, **Então** `user.avatar` é a URL da miniatura 128x128 recortada conforme `avatar_cropping`.

---

### História de Usuário 7 - Estender a API gerada para casos especiais (Prioridade: P3)

A pessoa desenvolvedora redefine o ViewSet gerado de um modelo (decorador `customize`), cria endpoints `@action` que devolvem querysets de outro modelo com serializer/filtros/paginação desse modelo (`wrapper_queryset_response_for_drf_action`), torna um ViewSet somente-leitura (`BusinessRulesNotImplementedMixin`) ou serve arquivos por endpoint (`ResponseFileMixin`).

**Por que esta prioridade**: pontos de extensão da biblioteca, não usados pelo esqueleto atual além da própria definição.

**Teste Independente**: aplicar `@customize(Teste)` a uma classe com um `@action` e verificar que o roteador usa a classe customizada; aplicar `wrapper_queryset_response_for_drf_action(Modelo)` em um `@action` e verificar resposta paginada com o serializer de `Modelo`.

**Cenários de Aceitação**:

1. **Dado** `@customize(Modelo)` aplicado a uma classe, **Quando** o roteador é construído depois, **Então** o ViewSet registrado para `Modelo` é a classe customizada (que herda também do ViewSet gerado).
2. **Dado** `@wrapper_queryset_response_for_drf_action(Modelo)` em um método de ação que devolve um queryset, **Quando** a ação é chamada, **Então** o resultado é filtrado, paginado e serializado com a configuração do ViewSet de `Modelo`.
3. **Dado** `BusinessRulesNotImplementedMixin`, **Quando** o ViewSet é consultado com `POST/PUT/PATCH/DELETE`, **Então** o método HTTP não é permitido (`405`), pois só `get`, `head`, `options` e `trace` ficam habilitados.

---

### Casos de Borda

- **Hash de senha exposto**: como não existe `UserSerializer` em `backend.api.serializers`, o recurso `/api/eauth/user/` usa o serializer global com `fields='__all__'` e **expõe o campo `password` (hash)** e `last_login` a quem tiver permissão de leitura do modelo.
- **`ResponseFileMixin` não é usado** por nenhum ViewSet atual; os endpoints de arquivo (`<campo-com-hifen>`) que `CustomFieldFile` tenta resolver via `reverse('backend.api:<app>_<modelo>-<campo>')` **não existem** no esqueleto; o `reverse` falha e `CustomFieldFile.url` devolve string vazia.
- **Renderers de arquivo**: `PDFRenderer`, `PngRenderer`, `JpgRenderer`, `JpegRenderer` e `ZIPRenderer` sempre levantam `Http404` ao renderizar; existem apenas para que a negociação por sufixo (`.pdf`, `.png`…) não falhe antes de a view decidir.
- **Formato desconhecido**: sufixo sem renderer correspondente devolve `404` (não `406`).
- **Filtro `o` inválido** (campo inexistente) não gera erro: a ordenação é silenciosamente ignorada (exceção engolida por `except`); porém erros de campo inexistente só aparecem na avaliação do queryset e, nesse caso, podem resultar em `500`/`FieldError` posterior.
- **`get_all=true`** desliga a paginação: listas grandes podem ser devolvidas inteiras sem limite.
- **`ApiViewSet.filter_backends = (DjangoFilterBackend,)`** sobrescreve o padrão global; portanto `SearchFilter` **não** está ativo nos ViewSets gerados (`?search=` é ignorado).
- **Método não implementado** em `BusinessRulesNotImplementedMixin`: `create`, `update` e `delete` levantam `Exception` genérica (mensagens "POST Create não implementado", etc.) caso sejam alcançados; na prática o `405` ocorre antes.
- **`AppVersionView` não devolve** `is_authenticated` nem `permissions`; o `AuthStore` do frontend (feature 007) espera esses campos e, por isso, precisa derivá-los de outro modo.
- **`recria_token` com `pk` vazio**: a rota aceita `\d*`, então `/api/recriar-token/` sem número casa e tenta recriar para `user_id=''` (erro de banco/valor); com `pk` inexistente, falha por integridade (`500`).
- **`/api/auth/session` aceita qualquer método** na regex (`^api/auth/session`, sem `$`), inclusive `/api/auth/sessionxyz`; só `POST` e `DELETE` são tratados (demais → `405`).
- **Autenticação de sessão e CSRF**: `SessionAuthentication` exige CSRF para métodos de escrita autenticados por cookie.
- **Falha ao importar módulos de configuração** do `DRFAUTOAPI` é apenas logada (`logger.error`) e o construtor segue com os padrões do DRF (`ModelSerializer`) e de `ApiFilterSetMixin`.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **FR-001**: O sistema DEVE oferecer a classe `ApiViewSetConstrutor` com os métodos de classe `build_class(apps_or_models)`, `router(router_class=DrfautoapiRouter)`, `import_modules(modules)`, `get_viewset_for_model(model)` e `update(other)`, mantendo o registro `_built_sets` (`{AppConfig: {Model: ViewSet}}`).
- **FR-002**: `build_class` DEVE aceitar `AppConfig` (todos os modelos do app) ou classes de modelo individuais, gerando para cada modelo um `ModelViewSet` (nome `<Modelo>ModelViewSet`) com `queryset = Modelo.objects.all()`, `filterset_class` e `serializer_class` próprios.
- **FR-003**: O serializer de cada modelo DEVE ser `<ObjectName>Serializer` encontrado no módulo `DRFAUTOAPI['DEFAULT_SERIALIZER_MODULE']` (classes cujo nome termina em `Serializer`) ou, na ausência, `DRFAUTOAPI['GLOBAL_SERIALIZER_MIXIN']`; seu `Meta` DEVE ganhar `ref_name = '<ObjectName>Serializer'`, `model` e `fields = '__all__'` quando não definidos.
- **FR-004**: O filterset de cada modelo DEVE ser `<ObjectName>FilterSet` encontrado no módulo `DRFAUTOAPI['DEFAULT_FILTER_MODULE']` (classes terminadas em `FilterSet`) ou, na ausência, `DRFAUTOAPI['GLOBAL_FILTERSET_MIXIN']` (padrão `ApiFilterSetMixin`).
- **FR-005**: O roteador DEVE registrar cada ViewSet em `<app_label>/<model_name>` com `basename = <app_label>_<model_name>`, incluir a view raiz da API e aplicar `format_suffix_patterns` com `allowed=['[a-zA-Z.0-9]+']`.
- **FR-006**: O sistema DEVE gerar, para cada campo do modelo (`get_all_model_fields`), um filtro para o lookup `exact` e para todos os lookups/transforms registrados no campo, exceto `contained_by`, `trigram_similar`, `unaccent` e `search`; campos `ManyToMany` DEVEM ter apenas `exact`; lookups sem filtro suportado DEVEM ser ignorados (sem erro).
- **FR-007**: Campos `CharField` e `TextField` DEVEM usar `SplitStringCharFilter`; campos `FileField` e `JSONField` DEVEM usar `CharFilter` com `lookup_expr='exact'`.
- **FR-008**: `SplitStringCharFilter` com `lookup_expr='icontains'` DEVE dividir o valor por espaços (ou por frases entre aspas duplas) e aplicar **cada termo** em sequência (AND); para outros lookups DEVE aplicar o valor inteiro; valores vazios DEVEM retornar o queryset sem filtro; se `distinct` estiver ativo, DEVE aplicar `distinct()`.
- **FR-009**: O parâmetro `o` DEVE ordenar o queryset por uma lista de campos separados por vírgula (`order_by`), ignorando espaços; em caso de exceção DEVE devolver o queryset inalterado.
- **FR-010**: Todo ViewSet gerado DEVE usar apenas `DjangoFilterBackend` como backend de filtro (`filter_backends = (DjangoFilterBackend,)`).
- **FR-011**: A paginação padrão DEVE ser `backend.api.pagination.StandardPagination` com `page_size = 10`, parâmetro `page_size` e `max_page_size = 100`; a resposta DEVE ser `{pagination: {links: {next, previous}, previous_page, next_page, start_index, end_index, total_entries, total_pages, page}, results}`; `previous_page`/`next_page` DEVEM ser `null` quando inexistentes.
- **FR-012**: `?get_all=true` (comparação sem diferenciar maiúsculas/minúsculas) DEVE desabilitar a paginação, devolvendo a lista completa.
- **FR-013**: O esquema OpenAPI da resposta paginada DEVE descrever o mesmo envelope `{pagination, results}` (`get_paginated_response_schema`).
- **FR-014**: `BackendSerializerMixin` DEVE adicionar aos serializers os campos somente-leitura `__str__` (representação textual), `metadata` (JSON do `Metadata` do objeto ou `{}`) e `link_detail_backend` (URL `<app_config.name>:<model_name>_detail` com `pk`, ou `''` se não existir).
- **FR-015**: A API DEVE usar `JSONParser`, `MultiPartParser` e `FileUploadParser` como parsers e `JSONRenderer` mais os renderers de arquivo (`PDFRenderer`, `PngRenderer`, `JpgRenderer`, `JpegRenderer`, `ZIPRenderer`) como renderers.
- **FR-016**: `DrfautoapiNegotiation` DEVE filtrar renderers comparando o sufixo de formato com `renderer.format` por expressão regular (`re.match`) e levantar `Http404` se nenhum renderer corresponder.
- **FR-017**: Os renderers de arquivo DEVEM declarar `media_type` e `format` (`image/jpeg`, `image/jpg`, `image/png`, `application/pdf`, `application/zip`) e DEVEM levantar `Http404` em `render`.
- **FR-018**: A API DEVE autenticar por `TokenAuthentication` e `SessionAuthentication` (nessa ordem) e usar por padrão `BackendModelPermissions` (definida na feature 003).
- **FR-019**: `POST /api/auth/token` DEVE ser a view `obtain_auth_token` do DRF (rota sem nome, regex `^api/auth/token$`).
- **FR-020**: `POST /api/auth/session` DEVE validar credenciais com o serializer de `ObtainAuthToken`, abrir sessão Django (`login`) e responder `{"detail": "Autenticação efetuada com sucesso!"}`; `DELETE` DEVE chamar `logout` e responder `{"detail": "Desconexão efetuada com sucesso!"}`.
- **FR-021**: `POST /api/recriar-token/<pk>` (nome `recria_token`, regex `^api/recriar-token/(?P<pk>\d*)$`) DEVE exigir `IsAdminUser`, apagar os tokens do usuário `pk`, criar um novo e responder `{"message": "Token recriado com sucesso!", "token": <chave>}`.
- **FR-022**: `GET /api/version` DEVE permitir qualquer visitante (`AllowAny`) e devolver `name` (`Backend`), `description` (`Plataforma ...`) e `version` (`settings.PROJECT_VERSION`); para autenticados DEVE acrescentar `user = {username, fullname, avatar}` com avatar padrão `/static/imgs/perfil.png` ou miniatura 128x128 recortada (`image_cropping`).
- **FR-023**: O esquema OpenAPI DEVE ser servido por `drf-spectacular` em `/api/schema/` (nome `schema_api`), Swagger UI em `/api/schema/swagger-ui/` (nome `swagger_ui_schema_api`) e Redoc em `/api/schema/redoc/` (nome `redoc_schema_api`), no namespace `backend.api`, com `TITLE = "Backend API - docs"`, `VERSION = "0.0.1"` e descrição em português.
- **FR-024**: Os apps `eauth` e `utils` DEVEM ser expostos na API por `backend/api/views_eauth.py` e `backend/api/views_utils.py`, importados via `BackendApiViewSetConstrutor.import_modules([...])` ao fim de `backend/api/views.py` (antes de o roteador ser construído em `backend/api/urls.py`).
- **FR-025**: O decorador `customize(model)` DEVE criar uma classe que herda da classe decorada e do ViewSet gerado do modelo, chamar `build()` se existir e substituir a entrada em `_built_sets`.
- **FR-026**: O decorador `wrapper_queryset_response_for_drf_action(model)` DEVE, ao ser chamado, adotar `queryset`, `serializer_class` e `filterset_class` do ViewSet do modelo informado, filtrar o queryset, executar o método decorado (que devolve um queryset), paginar e serializar (`many=True`), devolvendo resposta paginada ou lista simples.
- **FR-027**: `BusinessRulesNotImplementedMixin` DEVE restringir `http_method_names` a `get`, `head`, `options`, `trace`.
- **FR-028**: `ResponseFileMixin` (`backend/api/mixins.py`) DEVE oferecer `response_file`, `response_pagepdftoimage`, `response_pdftotext`, `anon` e `thumbnail` para servir arquivos de um campo do modelo (com miniaturas, PDF → PNG/texto e anonimização); NÃO é utilizado por nenhum ViewSet no esqueleto.
- **FR-029**: As rotas da API DEVEM ser definidas em `backend/api/urls.py` com `app_name = 'backend.api'` e incluídas na raiz por `path("", include("backend.api.urls"))`.
- **FR-030**: `backend/api/forms.py` DEVE expor `CustomFilterSetMixin(ApiFilterSetMixin)` e `backend/api/schema.py` DEVE expor `Schema(AutoSchema)` como pontos de customização vazios.

### Entidades-Chave

- **Recurso de API**: par (ViewSet, rota) gerado por modelo; identificado por `<app_label>/<model_name>`.
- **ApiViewSetConstrutor**: registro global dos ViewSets construídos e fábrica do roteador.
- **ApiFilterSetMixin / SplitStringCharFilter**: filtros automáticos por campo/lookup, `o` para ordenação.
- **BackendSerializerMixin**: serializer base com `__str__`, `metadata`, `link_detail_backend`.
- **StandardPagination**: paginação com envelope `pagination` + `results`.
- **Token de API**: `rest_framework.authtoken.models.Token` (um por usuário).
- **Esquema OpenAPI**: documento gerado por `drf-spectacular`.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Adicionar um novo modelo a um app já registrado em `build_class` o expõe em `/api/<app>/<modelo>/` sem editar nenhum outro arquivo (0 linhas de código de API por modelo).
- **SC-002**: 100% dos modelos dos apps `eauth` e `utils` aparecem em `GET /api/` e em `GET /api/schema/`.
- **SC-003**: Uma listagem sem parâmetros devolve no máximo 10 itens; com `page_size` > 100 devolve no máximo 100; com `get_all=true` devolve todos.
- **SC-004**: `GET /api/schema/` responde `200` e `GET /api/schema/swagger-ui/` e `/api/schema/redoc/` carregam sem erro.
- **SC-005**: Requisições sem credencial a recursos privados recebem `401/403`; com token ou sessão e permissão adequada recebem `200`.
- **SC-006**: `POST /api/auth/token` + `GET` com cabeçalho `Authorization: Token <chave>` funciona de ponta a ponta em menos de 2 chamadas.
- **SC-007**: A suíte de testes cobre filtros (`exact`, `icontains` com múltiplos termos e aspas, `o`), paginação, `get_all`, autenticação por token/sessão, `recria_token` e `version`.

## Premissas

- Depende de `001-fundacao-projeto-django` (settings modulares, `backend.settings.apps` com `rest_framework`, `rest_framework.authtoken`, `django_filters`, `drf_spectacular`, `PROJECT_VERSION = "0.0.1"`).
- Depende de `002-autenticacao-usuarios-auditoria` (modelo `eauth.User` com `avatar`/`avatar_cropping`, `AuditLog`, e `backend.fields.CustomFieldFile`).
- Depende de `003-regras-permissoes-globais`: `backend.api.permissions.BackendModelPermissions` e `ContainerPermission` pertencem àquela feature e aqui só são referenciadas como permissão padrão.
- `004-crud-generico-menus` usa os endpoints (`url_openapi='backend.api:utils_teste-list'`) nas listas; `006-sincronizacao-tempo-real` usa `ApiViewSetConstrutor.get_viewset_for_model` para serializar instâncias; `007-frontend-vite-vue` consome `/api/version` e `/api/auth/session`.
- O modelo `Metadata` (`backend.utils.models`) existe e é usado por `BackendSerializerMixin.get_metadata`.
- Dependências Python: `djangorestframework ^3.18.3`, `django-filter ^26.2`, `drf-spectacular ^0.30.0`, `pymupdf ^2.1`, `easy-thumbnails ^2.10.1`, `django-image-cropping ^1.7` (Python `>=3.12,<4.0`).
- Não existem modelos de dados novos: a feature só usa `Token` do DRF e modelos já existentes.
- Limitação de taxa (throttling) NÃO está implementada (há apenas um `TODO` em `backend/settings/drf.py`).
