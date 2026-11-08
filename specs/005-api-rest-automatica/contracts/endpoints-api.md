# Contrato: Endpoints HTTP da API

Todos os caminhos são relativos à raiz do site (`backend/urls.py`: `path("", include("backend.api.urls"))`; `app_name = 'backend.api'`). Autenticação padrão: `Authorization: Token <chave>` **ou** cookie de sessão (com `X-CSRFToken` para escritas). Permissão padrão: `BackendModelPermissions` (feature 003). Parsers: JSON, multipart, `FileUploadParser`. Renderer: JSON (e renderers de arquivo que dão `404`).

## 1. Recursos gerados (`/api/<app_label>/<modelo>/`)

Para cada modelo dos apps `eauth` e `utils` (ex.: `/api/utils/teste/`). Nome de URL: `backend.api:<app_label>_<modelo>-list|detail`. Sufixos de formato aceitos pela regex `[a-zA-Z.0-9]+` (ex.: `/api/utils/teste/1.json`).

| Método | Rota | Permissão exigida | Resposta |
|---|---|---|---|
| GET | `/api/<app>/<modelo>/` | `<app>.list_<modelo>` **ou** `<app>.view_<modelo>` (regra de 003: todas as de `perms_map` para o método; pública se `<app>:<modelo>` está em `rules_patterns_public`) | `200` lista paginada (ver §1.1) |
| GET | `/api/<app>/<modelo>/<pk>/` | idem | `200` objeto |
| POST | `/api/<app>/<modelo>/` | `<app>.add_<modelo>` | `201` objeto criado; `400` com erros de validação |
| PUT | `/api/<app>/<modelo>/<pk>/` | `<app>.change_<modelo>` | `200` objeto |
| PATCH | `/api/<app>/<modelo>/<pk>/` | `<app>.change_<modelo>` | `200` objeto |
| DELETE | `/api/<app>/<modelo>/<pk>/` | `<app>.delete_<modelo>` | `204` |
| OPTIONS / HEAD | ambas | idem leitura | metadados / cabeçalhos |
| GET | `/api/` | — (view raiz, nome `api-root`) | índice dos recursos |

Erros: sem credencial → `401` (Token é o primeiro autenticador, envia `WWW-Authenticate: Token`); sem permissão → `403`; inexistente → `404`; sufixo de formato sem renderer → `404`.

### 1.1 Parâmetros de listagem

| Parâmetro | Efeito |
|---|---|
| `page` | número da página (DRF). Página inválida → `404` |
| `page_size` | itens por página (padrão 10, máx. 100) |
| `get_all=true` | sem paginação (lista simples) |
| `<campo>=valor` | filtro `exact` |
| `<campo>__<lookup>=valor` | demais lookups: `icontains`, `istartswith`, `gte`, `lte`, `in` (valores separados por vírgula), `isnull`, `year`, `year__gte`, `range`… (conforme o tipo do campo) |
| `<campo>__icontains=a b "c d"` | AND entre os termos `a`, `b` e a frase `c d` (apenas `CharField`/`TextField`) |
| `o=campo1,-campo2` | ordenação (`order_by`); inválido → ignorado |

Não há `search=` (o `SearchFilter` está desativado nos ViewSets gerados).

### 1.2 Campos de cada item

Todos os campos do modelo + `__str__`, `metadata`, `link_detail_backend` (ver `data-model.md` §4). **Atenção**: `eauth/user` inclui o hash `password` (`research.md` #1).

## 2. Autenticação

| Método | Rota | Nome | Permissão | Corpo → Resposta |
|---|---|---|---|---|
| POST | `/api/auth/token` | — | qualquer | `{"username": "<e-mail>", "password": "…"}` → `200 {"token": "<chave>"}`; `400` se inválido. (Campo de login conforme `USERNAME_FIELD` do usuário — e-mail na feature 002.) |
| POST | `/api/auth/session` | — | qualquer | mesmas credenciais → `200 {"detail": "Autenticação efetuada com sucesso!"}` + cookie `sessionid`; `400` se inválidas |
| DELETE | `/api/auth/session` | — | qualquer | → `200 {"detail": "Desconexão efetuada com sucesso!"}` |
| POST | `/api/recriar-token/<pk>` | `recria_token` | `IsAdminUser` (`is_staff`) | → `200 {"message": "Token recriado com sucesso!", "token": "<nova chave>"}` |

Notas: regex de sessão `^api/auth/session` (sem `$`); `recria_token` aceita `\d*` (`pk` vazio ou inexistente gera erro/`500`); a view de sessão herda de `ObtainAuthToken` (serializer `AuthTokenSerializer`, que usa `authenticate(request, username=..., password=...)`). Escritas autenticadas por cookie exigem CSRF.

## 3. Versão

| Método | Rota | Permissão | Resposta |
|---|---|---|---|
| GET | `/api/version` | `AllowAny` | `{"name": "Backend", "description": "Plataforma ...", "version": "<PROJECT_VERSION>"}`; se autenticado, `+ "user": {"username", "fullname", "avatar"}` |

`avatar`: `/static/imgs/perfil.png` (sem avatar) ou URL da miniatura 128x128 com recorte (`avatar_cropping`). **Não** há `is_authenticated` nem `permissions`.

## 4. Documentação OpenAPI

| Método | Rota | Nome (namespace `backend.api`) | Conteúdo |
|---|---|---|---|
| GET | `/api/schema/` | `schema_api` | esquema OpenAPI 3 (`SpectacularAPIView`; `?format=json`/`yaml`) |
| GET | `/api/schema/swagger-ui/` | `swagger_ui_schema_api` | Swagger UI (`url_name='backend.api:schema_api'`) |
| GET | `/api/schema/redoc/` | `redoc_schema_api` | Redoc |

Metadados: `title "Backend API - docs"`, `version "0.0.1"`. A resposta de listagem é documentada com o envelope `{pagination, results}`. A ordem das rotas importa: `schema/swagger-ui/` e `schema/redoc/` vêm antes de `^schema/` (sem `$`).

## 5. Ordem das rotas em `backend/api/urls.py`

1. `^api/` + `urlpatterns_api_doc`
2. `^api/` + `router_backend.urls`
3. `^api/version$`
4. `^api/auth/token$`
5. `^api/auth/session`
6. `^api/recriar-token/(?P<pk>\d*)$` (`recria_token`)
