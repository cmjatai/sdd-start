---

description: "Lista de tarefas para reconstruir a API REST automática (drfautoapi), a autenticação por token/sessão e a documentação OpenAPI"
---

# Tarefas: API REST Automática (`drfautoapi`), Autenticação por Token/Sessão e Documentação OpenAPI

**Entrada**: Documentos de design em `/specs/005-api-rest-automatica/`

**Pré-requisitos**: plan.md, spec.md, research.md, data-model.md, contracts/ (`endpoints-api.md`, `drfautoapi-extensao.md`); funcionalidades `001`, `002` e `003` já reconstruídas (settings modulares, `eauth.User` com `avatar`/`avatar_cropping`, `BackendModelPermissions`, `backend/globalrules/map_rules.py`, `Teste` e `Metadata` em `backend/utils/models.py`, `backend/utilss.py`, `backend/fields.py`).

**Testes**: incluídos (princípio VIII da constituição: `pytest`, `ruff`).

**Organização**: tarefas agrupadas por história de usuário; **todas desmarcadas** (roteiro de reconstrução).

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US7 (histórias de `spec.md`)
- As seções citadas (§) referem-se ao "Detalhamento de Implementação" de `plan.md`.

## Convenções de Caminhos

Biblioteca interna em `drfautoapi/`; app de projeto em `backend/api/`; settings em `backend/settings/drf.py`; testes em `backend/api/tests.py`.

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: dependências, app e pastas.

- [ ] T001 Garantir em `pyproject.toml` as dependências `djangorestframework ^3.18.3`, `django-filter ^26.2`, `drf-spectacular ^0.30.0`, `django-image-cropping ^1.7`, `easy-thumbnails ^2.10.1`, `pymupdf ^2.1` e instalar (`poetry install`)
- [ ] T002 [P] Criar a pasta `drfautoapi/` com `__init__.py` e `drfautoapi.py` vazios
- [ ] T003 [P] Criar o app `backend/api/` com `__init__.py` (`default_app_config = 'backend.api.apps.ApiConfig'`), `apps.py` (`ApiConfig`, `name='backend.api'`, `label='api'`), `admin.py` e `models.py` vazios, `tests.py`
- [ ] T004 Registrar em `backend/settings/apps.py` os apps `drf_spectacular`, `rest_framework`, `django_filters`, `rest_framework.authtoken` e `backend.api`
- [ ] T005 [P] Garantir que o `Dockerfile` de produção copia a biblioteca (`ADD drfautoapi ${HOME}/drfautoapi` em `_docker/prod/Dockerfile`) e que `drfautoapi` está no caminho de import do dev

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: configuração DRF, filtros, paginação, serializer base e construtor, sobre os quais todas as histórias dependem.

**⚠️ CRÍTICO**: nenhuma história pode começar antes desta fase.

- [ ] T006 Criar `backend/settings/drf.py` com `REST_FRAMEWORK`, `DRFAUTOAPI` e `SPECTACULAR_SETTINGS` exatamente como em plan.md §1 e importá-lo em `backend/settings/project.py` (`from .drf import *`)
- [ ] T007 [P] Implementar `DrfautoapiNegotiation`, `FilesRenderer`, `JpegRenderer`, `JpgRenderer`, `PngRenderer`, `PDFRenderer` e `ZIPRenderer` em `drfautoapi/__init__.py` (plan.md §2)
- [ ] T008 [P] Implementar `StandardPagination` em `backend/api/pagination.py` (plan.md §5: `page_size=10`, `max_page_size=100`, `get_all`, envelope e esquema)
- [ ] T009 [P] Implementar `BackendSerializerMixin` em `backend/api/serializers.py` (`__str__`, `metadata`, `link_detail_backend`; plan.md §5)
- [ ] T010 [P] Criar `backend/api/schema.py` (`Schema(AutoSchema)` vazio) e `backend/api/forms.py` (`CustomFilterSetMixin(ApiFilterSetMixin)` vazio)
- [ ] T011 Implementar em `drfautoapi/drfautoapi.py` `SplitStringCharFilter` (plan.md §3) com os imports necessários
- [ ] T012 Implementar em `drfautoapi/drfautoapi.py` `ApiFilterSetMixin` (`o`, `Meta.filter_overrides`, `filter_o`, `get_fields`, `filter_for_field`) (plan.md §3)
- [ ] T013 Implementar em `drfautoapi/drfautoapi.py` `DrfautoapiRouter` e `ApiViewSetConstrutor` (`_built_sets`, `ApiViewSet`, `get_viewset_for_model`, `update`, `import_modules`, `router`, `build_class`) (plan.md §4)

**Ponto de Controle**: `python manage.py check` passa; `ApiViewSetConstrutor.build_class([...])` roda no shell sem erro.

## Fase 3: História de Usuário 1 - Todo modelo vira um recurso REST (Prioridade: P1) 🎯 MVP

**Objetivo**: `/api/<app>/<modelo>/` para todos os modelos de `eauth` e `utils`, com a raiz `/api/`.

**Teste Independente**: `GET /api/utils/teste/` como superusuário → `200`; `POST` → `201`.

### Testes da História de Usuário 1

- [ ] T014 [P] [US1] Teste do roteador: `registry` contém `utils/teste` com basename `utils_teste`; `reverse('backend.api:utils_teste-list') == '/api/utils/teste/'` em `backend/api/tests.py`
- [ ] T015 [P] [US1] Teste CRUD completo (`POST/GET/PATCH/DELETE`) de `Teste` com `APIClient` autenticado como superusuário, e dos campos extras `__str__`, `metadata`, `link_detail_backend` em `backend/api/tests.py`
- [ ] T016 [P] [US1] Teste `get_viewset_for_model(Teste)` e `build_class` com serializer/filterset específicos (monkeypatch de `DRFAUTOAPI`) em `backend/api/tests.py`

### Implementação da História de Usuário 1

- [ ] T017 [US1] Criar `backend/api/views.py` com `BackendApiViewSetConstrutor = ApiViewSetConstrutor` e `import_modules(['backend.api.views_eauth', 'backend.api.views_utils'])` ao final (plan.md §5)
- [ ] T018 [P] [US1] Criar `backend/api/views_eauth.py` (`build_class([apps.get_app_config('eauth')])`) e `backend/api/views_utils.py` (`'utils'`)
- [ ] T019 [US1] Criar `backend/api/urls.py` com `app_name`, `router_backend`, `urlpatterns_api_doc`, `urlpatterns` e a ordem de plan.md §5 (rotas de recursos); incluir `path("", include("backend.api.urls"))` em `backend/urls.py` antes das demais
- [ ] T020 [US1] Testar manualmente `GET /api/` e o sufixo `.json`; `.xyz` → `404` (teste `test_formato_desconhecido_404`)

**Ponto de Controle**: todos os modelos de `eauth` e `utils` expostos.

## Fase 4: História de Usuário 2 - Paginação, filtros e ordenação (Prioridade: P1)

**Objetivo**: envelope de paginação, `get_all`, filtros por lookup, `icontains` multitermo e `o`.

**Teste Independente**: 25 registros → 10 itens e `total_pages=3`; `?teste__icontains=ana silva`; `?o=-teste`.

### Testes da História de Usuário 2

- [ ] T021 [P] [US2] Testes de paginação (`page_size`, máximo 100, `get_all=true`, `next_page`/`previous_page` nulos nas pontas) em `backend/api/tests.py`
- [ ] T022 [P] [US2] Testes unitários de `SplitStringCharFilter` (espaços, aspas, valor vazio) e de `ApiFilterSetMixin.get_fields()` (inclui `exact` e `icontains`; exclui `unaccent`, `search`; M2M só `exact`) em `backend/api/tests.py`
- [ ] T023 [P] [US2] Testes de `?o=-teste,id`, `?id__gte=`, `?teste=` exato e `o` inválido em `backend/api/tests.py`

### Implementação da História de Usuário 2

- [ ] T024 [US2] Revisar `ApiFilterSetMixin`/`StandardPagination` contra os testes e ajustar (nenhum código novo esperado se a fase 2 foi fiel)

**Ponto de Controle**: listagem uniforme em todos os recursos.

## Fase 5: História de Usuário 3 - Token e sessão (Prioridade: P1)

**Objetivo**: `/api/auth/token`, `/api/auth/session` (POST/DELETE) e `/api/recriar-token/<pk>`.

**Teste Independente**: token obtido autentica `GET /api/utils/teste/`; POST/DELETE de sessão.

### Testes da História de Usuário 3

- [ ] T025 [P] [US3] Testes de `/api/auth/token` (válido, inválido `400`) em `backend/api/tests.py`
- [ ] T026 [P] [US3] Testes de `/api/auth/session` (`POST` mensagem de sucesso e cookie; `DELETE` encerra; inválido `400`) em `backend/api/tests.py`
- [ ] T027 [P] [US3] Testes de `recria_token` (admin recebe token novo ≠ anterior; não-admin `403`; anônimo `401`) em `backend/api/tests.py`

### Implementação da História de Usuário 3

- [ ] T028 [US3] Implementar `recria_token` e `AppSessionAuthView` em `backend/api/views.py` (plan.md §5)
- [ ] T029 [US3] Acrescentar em `backend/api/urls.py` as rotas `^api/auth/token$` (`obtain_auth_token`), `^api/auth/session` e `^api/recriar-token/(?P<pk>\d*)$` (`name='recria_token'`)
- [ ] T030 [US3] Confirmar o uso de `{% url 'backend.api:recria_token' object.id %}` em `_templates/eauth/user_form.html` (feature 002)

**Ponto de Controle**: autenticação por token e por sessão funcionando.

## Fase 6: História de Usuário 4 - Permissões por modelo (Prioridade: P2)

**Objetivo**: autorização por método via `BackendModelPermissions` (feature 003).

**Teste Independente**: anônimo `401`; sem permissão `403`; superusuário `200`.

### Testes da História de Usuário 4

- [ ] T031 [P] [US4] Testes de permissão por método (`list_/view_`, `add_`, `change_`, `delete_`) e de modelo público em `backend/api/tests.py` (usar fixtures de grupos/permissões da feature 003)

### Implementação da História de Usuário 4

- [ ] T032 [US4] Verificar que `DEFAULT_PERMISSION_CLASSES` e `DEFAULT_AUTHENTICATION_CLASSES` em `backend/settings/drf.py` seguem plan.md §1 (sem código adicional além da referência a `backend.api.permissions.BackendModelPermissions`, definida em 003)

**Ponto de Controle**: API protegida por permissões.

## Fase 7: História de Usuário 5 - Documentação OpenAPI (Prioridade: P2)

**Objetivo**: `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/`.

**Teste Independente**: três URLs respondem `200`; envelope paginado documentado.

### Testes da História de Usuário 5

- [ ] T033 [P] [US5] Testes das três rotas (`reverse('backend.api:schema_api')` etc.) e da presença de `pagination` no esquema de `/api/utils/teste/` em `backend/api/tests.py`

### Implementação da História de Usuário 5

- [ ] T034 [US5] Completar `urlpatterns_api_doc` em `backend/api/urls.py` (Swagger `url_name='backend.api:schema_api'`, Redoc, esquema) na ordem de plan.md §5
- [ ] T035 [US5] Executar `python manage.py spectacular --file /dev/null` e corrigir erros do esquema, se houver

**Ponto de Controle**: documentação navegável.

## Fase 8: História de Usuário 6 - Versão e usuário corrente (Prioridade: P3)

**Objetivo**: `GET /api/version`.

**Teste Independente**: anônimo vs. autenticado (com e sem avatar).

### Testes da História de Usuário 6

- [ ] T036 [P] [US6] Testes de `/api/version` (anônimo; autenticado sem avatar → `/static/imgs/perfil.png`) em `backend/api/tests.py`

### Implementação da História de Usuário 6

- [ ] T037 [US6] Implementar `AppVersionView` em `backend/api/views.py` e a rota `^api/version$` em `backend/api/urls.py` (plan.md §5)

**Ponto de Controle**: frontend consegue consultar versão.

## Fase 9: História de Usuário 7 - Pontos de extensão (Prioridade: P3)

**Objetivo**: `customize`, `wrapper_queryset_response_for_drf_action`, `BusinessRulesNotImplementedMixin`, `ResponseFileMixin`.

**Teste Independente**: ver T038–T040.

### Testes da História de Usuário 7

- [ ] T038 [P] [US7] Teste de `customize` (substitui entrada em `_built_sets`) e de `BusinessRulesNotImplementedMixin` (`POST` → `405`) em `backend/api/tests.py`
- [ ] T039 [P] [US7] Teste de `wrapper_queryset_response_for_drf_action` (resposta paginada com serializer do modelo anotado) em `backend/api/tests.py`

### Implementação da História de Usuário 7

- [ ] T040 [US7] Implementar `wrapper_queryset_response_for_drf_action`, `customize` e `BusinessRulesNotImplementedMixin` em `drfautoapi/drfautoapi.py` (plan.md §3–§4), se ainda não feitos na fase 2
- [ ] T041 [US7] Implementar `ResponseFileMixin` em `backend/api/mixins.py` conforme `contracts/drfautoapi-extensao.md` §4 (`response_file`, `response_pagepdftoimage`, `response_pdftotext`, `anon`, `thumbnail`), usando `get_mime_type_from_file_extension` e `clean_text` de `backend/utilss.py`; sem uso por ViewSets (fidelidade)

**Ponto de Controle**: extensão disponível, sem alterar o comportamento padrão.

## Fase 10: Acabamento e Preocupações Transversais

- [ ] T042 [P] Rodar `ruff check drfautoapi backend/api` e `ruff format --check` (regras E, F, I) e corrigir
- [ ] T043 [P] Rodar `pytest backend/api/tests.py` e verificar cobertura
- [ ] T044 [P] Registrar em comentários/`README.md` raiz (linha da tabela de pastas) que `drfautoapi/` é a biblioteca interna de API
- [ ] T045 Validar o `quickstart.md` ponta a ponta (curl e navegador)
- [ ] T046 Confirmar (sem corrigir, por fidelidade) as particularidades de `research.md` (hash de senha exposto, `ResponseFileMixin` sem uso, `reverse` inexistente de `CustomFieldFile`, `/api/version` sem `is_authenticated`/`permissions`)

## Dependências e Ordem de Execução

### Dependências de Fase

- Preparação (Fase 1) → Fundacional (Fase 2) → histórias.
- US1 depende da Fase 2; US2, US3, US5, US6 dependem de US1 (rotas) mas não entre si; US4 depende de US1 e da feature 003; US7 depende da Fase 2.
- Acabamento depende de todas as histórias desejadas.

### Dependências Dentro das Histórias

- T011 → T012 → T013; T017/T018 antes de T019 (o `router()` é executado na importação de `urls.py`, portanto os apps precisam já estar construídos); T028 antes de T029; T034 antes de T033 passar.

### Oportunidades de Paralelismo

- T007–T010 em paralelo; testes `[P]` de cada história em paralelo; `views_eauth.py` e `views_utils.py` em paralelo.

## Estratégia de Implementação

### MVP Primeiro (US1 + US2 + US3)

1. Fases 1–2; 2. US1 (recursos gerados); 3. US2 (paginação/filtros); 4. US3 (token/sessão). Validar com o quickstart.

### Entrega Incremental

US4 (permissões — reutiliza 003) → US5 (documentação) → US6 (versão) → US7 (extensões).

### Observação de Fidelidade

O estado atual é o alvo: **replicar** as particularidades listadas em `research.md` (inclusive as inseguras) e só corrigi-las em uma evolução posterior explícita (por exemplo, `UserSerializer` com `exclude = ('password',)` e throttling).
