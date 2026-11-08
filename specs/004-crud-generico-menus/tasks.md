---

description: "Lista de tarefas para reconstruir o CRUD genérico, os layouts YAML, os menus e os templates-base"
---

# Tarefas: CRUD Genérico, Layouts YAML, Menus e Templates Base

**Entrada**: Documentos de design em `/specs/004-crud-generico-menus/`

**Pré-requisitos**: plan.md, spec.md, research.md, data-model.md, contracts/ (`crud-http.md`, `layouts-yaml.md`, `menus-yaml.md`, `templates.md`); funcionalidades `001`, `002` e `003` já reconstruídas (settings de templates/crispy, modelo `Teste`, `SearchModelMixin`, `normalize`, rotas `backend.eauth:*`, constantes `RP_*`).

**Testes**: incluídos (princípio VIII da constituição: `pytest`, `ruff`).

**Organização**: tarefas agrupadas por história de usuário; **todas desmarcadas** (roteiro de reconstrução).

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US6 (histórias de `spec.md`)
- As seções citadas (§) referem-se ao "Detalhamento de Implementação" de `plan.md`.

## Convenções de Caminhos

Aplicação web Django: código em `backend/`, templates em `_templates/`, testes ao lado do código (`backend/crud/tests.py`) ou em `_tests/`.

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: garantir dependências e estrutura de pastas.

- [ ] T001 Confirmar em `pyproject.toml` as dependências `django >=6,<7`, `django-crispy-forms`, `crispy-bootstrap5`, `django-braces ^1.17`, `pyyaml ^6.0`, `markdown ^3.11`, `django-vite ^3.2` e que `CRISPY_ALLOWED_TEMPLATE_PACKS`/`CRISPY_TEMPLATE_PACK = "bootstrap5"` e `TEMPLATES[0]["DIRS"] = [PROJECT_DIR / "_templates"]` existem em `backend/settings/frontend.py` (adicionar se faltar; `poetry lock`/`poetry install` se alterar).
- [ ] T002 [P] Criar a estrutura de diretórios `backend/crud/`, `_templates/crud/`, `_templates/menus/` e `_templates/utils/`; criar `backend/crud/__init__.py` com `default_app_config = 'backend.utils.apps.CrudConfig'` (fidelidade, ver research R1) e `backend/crud/apps.py` com `CrudConfig` (`default_auto_field = 'django.db.models.BigAutoField'`, `name = 'backend.crud'`, `label = 'crud'`). NÃO registrar `backend.crud` em `INSTALLED_APPS`.
- [ ] T003 [P] Confirmar que `backend/globalrules/__init__.py` exporta `RP_LIST, RP_VIEW, RP_ADD, RP_CHANGE, RP_DELETE` (`'.list_'`, `'.view_'`, `'.add_'`, `'.change_'`, `'.delete_'`) e que `backend/utilss.py` exporta `normalize`; confirmar `Teste` em `backend/utils/models.py` e `SearchModelMixin` em `backend/model_mixins.py`.

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: utilidades e mixins sobre os quais todas as histórias dependem.

**⚠️ CRÍTICO**: nenhuma história pode começar antes desta fase.

- [ ] T004 Criar `backend/crud/crispy_layout_mixin.py` com `re_start_tag`, `markdown_regex`, `to_column`, `to_row`, `to_fieldsets`, `form_actions`, `CustomFormHelper` (`render_hidden_fields = True`), `CustomFormLayout`, `get_field_display`, `heads_and_tails`, `read_yaml_from_file`, `read_layout_from_yaml` (v1 e v2) conforme plan §7 e `contracts/layouts-yaml.md`.
- [ ] T005 Em `backend/crud/crispy_layout_mixin.py`, implementar `CrispyLayoutFormMixin` (`layout_key`, `layout_key_set`, `get_layout`, `get_layout_set`, `fields`, `get_form`, `list_field_names`, `list_field_names_set`, `get_column`, `fk_urlize_for_detail`, `m2m_urlize_for_detail`, `markdown`, `layout_display`) conforme plan §7 (depende de T004).
- [ ] T006 [P] Criar `backend/crud/forms.py` com `ListWithSearchForm` (campos `q`, `o`, `page_size`; helper GET com `FieldWithButtons`/`StrictButton "Filtrar"`) conforme plan §8.
- [ ] T007 Criar `backend/crud/base.py` com imports, `logger`, constantes `ACTION_*`, `_form_invalid_message`, `FORM_MESSAGES` (com prefixo "Formulário inválido." só nas mensagens de erro), `from_to`, `make_pagination` e o docstring de variáveis do crud, conforme plan §1.
- [ ] T008 Em `backend/crud/base.py`, implementar `PermissionRequiredForAppCrudMixin` e `PermissionRequiredContainerCrudMixin` (`has_permission` por "qualquer uma", `dispatch` com `container_field`, propriedades `container_field`, `container_field_set`, `is_contained`) conforme plan §2 (depende de T007).
- [ ] T009 Em `backend/crud/base.py`, implementar `CrudBaseMixin(CrispyLayoutFormMixin)` (`__init__`, `permission`, `permission_set`, `url_name`, `url_name_set`, `resolve_url`, `resolve_url_set`, `ordered_list`, `list_url`, `create_url`, `detail_url`, `update_url`, `delete_url`, `openapi_url`, `get_template_names`, `verbose_name*`) conforme plan §3 (depende de T005, T008).
- [ ] T010 [P] Criar `_templates/paginacao.html` conforme `contracts/templates.md` (nav de paginação com `page_range`, `filter_url`, `None` → `...`).

**Ponto de Controle**: utilidades de layout, formulário de busca, mixins e paginação prontos.

---

## Fase 3: História de Usuário 1 - Declarar um CRUD completo a partir de um modelo (Prioridade: P1) 🎯 MVP

**Objetivo**: `Crud.get_urls()` gera as 5 rotas e as 5 views funcionam com mensagens.

**Teste Independente**: `TesteCrud.get_urls()` devolve 5 `re_path` com os nomes/regex corretos; fluxo criar/editar/excluir com superusuário exibe as mensagens.

### Testes da História de Usuário 1

- [ ] T011 [P] [US1] Criar `backend/utils/tests.py` (ou `backend/crud/tests.py`) com teste das rotas geradas por `TesteCrud.get_urls()` (cinco padrões `^$`, `^create$`, `^(?P<pk>\d+)$`, `^(?P<pk>\d+)/edit$`, `^(?P<pk>\d+)/delete$` e nomes `teste_*`) e de uma subclasse com `CreateView = None` (4 rotas).
- [ ] T012 [P] [US1] Teste de fluxo com a fixture `app` (`conftest.py`, usuário admin): criar `Teste` em `/teste/create`, editar em `/teste/<pk>/edit`, excluir em `/teste/<pk>/delete`, verificando as mensagens "Registro criado com sucesso!", "Registro alterado com sucesso!", "Registro excluído com sucesso!" e redirecionamentos (detalhe, detalhe, listagem).

### Implementação da História de Usuário 1

- [ ] T013 [US1] Em `backend/crud/base.py`, implementar `CrudCreateView`, `CrudDetailView`, `CrudUpdateView`, `CrudDeleteView` (regex, `permission_required`, mensagens `FORM_MESSAGES`, `cancel_url`, `get_success_url`, `form_valid` com `created_by`/`modified_by`/`modifier`, contêiner) conforme plan §4 (depende de T009).
- [ ] T014 [US1] Em `backend/crud/base.py`, implementar `Crud` (`__type__`, `BaseMixin`, views, `container_css_class`, `help_topic`, `frontend`, `PublicMixin`), `Crud.get_urls()` (`_add_base`, classe `CRUD`, `re_path`s com `name=view.url_name(sufixo)`) e `Crud.build()` conforme plan §5.
- [ ] T015 [P] [US1] Criar `_templates/crud/form.html`, `_templates/crud/ajax_form.html` e `_templates/crud/confirm_delete.html` conforme `contracts/templates.md`.
- [ ] T016 [US1] Em `backend/utils/views.py`, definir `class TesteCrud(Crud): model = Teste; public = [RP_LIST, RP_VIEW]` e em `backend/utils/urls.py` adicionar `re_path(r"^teste/", include(views.TesteCrud.get_urls()))` com `app_name = UtilsConfig.name` (depende de T014).
- [ ] T017 [P] [US1] Criar `_templates/utils/layouts.yaml` com a chave `Teste` (legenda `{% trans 'Modelo Teste'%}`; linhas `id teste teste teste`, `teste:5 teste teste`, `teste:3 teste teste`) conforme `contracts/layouts-yaml.md`.

**Ponto de Controle**: CRUD completo operando em `/teste/` (listagem ainda sem template específico até US3).

---

## Fase 4: História de Usuário 2 - Controle de acesso por permissão e rotas públicas (Prioridade: P1)

**Objetivo**: permissões por verbo, `public`, `container_field` e botões condicionados.

**Teste Independente**: anônimo vê `/teste/` (200) e é redirecionado em `/teste/create` (302); superusuário acessa tudo.

### Testes da História de Usuário 2

- [ ] T018 [P] [US2] Teste com `app` sem usuário (`user=None`/cliente anônimo): `GET /teste/` e `GET /teste/<pk>` → 200; `GET /teste/create`, `/edit`, `/delete` → 302 para login.
- [ ] T019 [P] [US2] Teste de permissão "qualquer uma" e de botões: usuário com apenas `utils.add_teste` vê o botão "Adicionar Teste" em `/teste/`; usuário sem `utils.change_teste` não vê "Editar" no detalhe; usuário autenticado sem permissão recebe 403 em `/teste/create`.
- [ ] T020 [P] [US2] Teste unitário de `CrudBaseMixin.permission(".add_")` → `"utils.add_teste"` e de `Crud.public` removendo permissões exigidas.

### Implementação da História de Usuário 2

- [ ] T021 [US2] Revisar/implementar em `backend/crud/base.py` a remoção de `Crud.public` em `Crud.get_urls()` e em `CrudBaseMixin.__init__`, e a lógica de `list_url`/`create_url`/etc. que devolve `""` sem permissão (plan §3 e §5).
- [ ] T022 [US2] Implementar em `backend/crud/base.py` o tratamento de `container_field` na listagem (`get_queryset`), no detalhe (`dispatch` → 404), na criação (`form_valid` com contêiner) e `PermissionRequiredContainerCrudMixin.dispatch` (plan §2 e §4).

**Ponto de Controle**: acesso controlado por permissão e por contêiner.

---

## Fase 5: História de Usuário 3 - Listagem com busca, ordenação, paginação e tamanho de página (Prioridade: P1)

**Objetivo**: tela de listagem completa.

**Teste Independente**: `/teste/?o=-2` ordena decrescente; `ListWithSearchForm` filtra o CRUD de usuários.

### Testes da História de Usuário 3

- [ ] T023 [P] [US3] Em `backend/crud/tests.py`, testes de `make_pagination` para `(1,5)`, `(1,30)`, `(6,30)`, `(7,30)`, `(15,30)`, `(27,30)`, `(30,30)` com os resultados do plan §1 e verificação de `len <= 10` para `1 <= index <= num_pages < 80`.
- [ ] T024 [P] [US3] Teste de ordenação em `/teste/` com ≥3 registros: `?o=2` (asc), `?o=-2` (desc), `?o=999` (módulo, sem 500) e verificação de `ordering_url`/`filter_url` no contexto.
- [ ] T025 [P] [US3] Teste da listagem com `ListWithSearchForm` (CRUD de usuários de `002` ou modelo de teste com `SearchModelMixin`): `q` com várias palavras (AND), `page_size=25`, cookie `backend_page_size=50`, `page_size=7` inválido → 302 para a listagem com mensagem de erro.

### Implementação da História de Usuário 3

- [ ] T026 [US3] Em `backend/crud/base.py`, implementar `CrudListView` completo (`get_rows`, `get_headers`, `_as_row`, `get_context_data`, `get`, `get_queryset` com busca, ordenação por `o`, contêiner) conforme plan §4 (depende de T009).
- [ ] T027 [P] [US3] Criar `_templates/crud/list.html` (ações, formulário de busca `{% crispy form %}`, tabela com cabeçalhos ordenáveis, `paginacao.html`, script de foco em `#id_q` e cookie `sddstart_page_size`) e `_templates/crud/list_tabaux.html` conforme `contracts/templates.md`.
- [ ] T028 [P] [US3] Criar `_templates/utils/teste_list.html` (estende `crud/list.html`; sobrescreve `header_exports` incluindo `crud/format_options.html` com `url_reverse='backend.utils:teste_list'` e `url_openapi='backend.api:utils_teste-list'`) e `_templates/crud/format_options.html`.
- [ ] T029 [US3] Verificar a integração com `UserCrud.ListView` em `backend/eauth/views_auth.py` (feature `002`): ela usa `form_search_class = ListWithSearchForm` e `paginate_by = 100`; confirmar que a busca `q` funciona nessa listagem (sem alterar `002`).

**Ponto de Controle**: listagem com ordenação, busca e paginação.

---

## Fase 6: História de Usuário 4 - Formulários e detalhes dirigidos por layout YAML (Prioridade: P2)

**Objetivo**: layouts v1/v2, `get_field_display`, detalhe com widgets.

**Teste Independente**: `read_layout_from_yaml` (teste existente) e render do detalhe de `Teste`.

### Testes da História de Usuário 4

- [ ] T030 [P] [US4] Manter/criar em `backend/crud/tests.py` `test_read_layout_from_yaml` (mock de `read_yaml_from_file`; expectativa do plan: `Cool Legend` com `[('name',9),('place',2),('tiny',1)]`, `[('field',10),('nature',2)]`, `[('kind',1),('date',3),('unit',5),('status',3)]`; `More data` com 4/4/4 e `[('highlander',12)]`).
- [ ] T031 [P] [US4] Testes adicionais: layout versão 2 (retorna `(lista, 2)`), chave inexistente e YAML inválido → `[]`.
- [ ] T032 [P] [US4] Testes de `get_field_display` (booleano "Sim"/"Não", choices, data curta, TextField com `\n`→`<br/>`, DecimalField com milhar, manager em `<ul>`).
- [ ] T033 [P] [US4] Teste do detalhe de `Teste` (`/teste/<pk>`): contém `h2.legend` "Modelo Teste", o link `OpenAPI` com `/api/utils/teste/<pk>` e as colunas `col-lg-<span>`.

### Implementação da História de Usuário 4

- [ ] T034 [US4] Em `backend/crud/base.py`, completar `CrudDetailView` com `model_set` (`get_headers`, `_as_row`, `get_queryset`, `get_context_data`, `model_set_verbose_name*`) conforme plan §4.
- [ ] T035 [P] [US4] Criar `_templates/crud/detail.html`, `_templates/crud/detail_detail.html`, `_templates/crud/detail_content_widget.html` e `_templates/crud/detail_column_widget.html` conforme `contracts/templates.md` (v1 e v2 do `layout_display`, widgets áudio/vídeo/YouTube/Facebook/link/componente frontend).
- [ ] T036 [P] [US4] Criar `_templates/eauth/layouts.yaml` com `UserDetail` e `UserCreate` (exemplo; conteúdo em `contracts/layouts-yaml.md`; coordenar com `002`).
- [ ] T037 [US4] Em `backend/crud/base.py`, implementar `MasterDetailCrud` (BaseMixin, List/Create/Update/Delete/Detail Views, `build`) e `CrudBaseForListAndDetailExternalAppView` conforme plan §6 (biblioteca; cobrir por teste de importação/rotas com um modelo de teste).

**Ponto de Controle**: formulários e detalhes dirigidos por YAML.

---

## Fase 7: História de Usuário 5 - Menus declarativos em YAML com permissões (Prioridade: P2)

**Objetivo**: tags `menu`, `subnav`, `navbar` e arquivos YAML.

**Teste Independente**: `/` mostra o menu principal; superusuário vê o menu de administração.

### Testes da História de Usuário 5

- [ ] T038 [P] [US5] Teste de `resolve_urls_inplace` (em `backend/utils/tests.py`): item com `check_permission` negado zera `url`/`active` e remove `children` se grupo; `url` literal (`/`, `#`) preservada; `url` `app:nome` revertida; `active` por igualdade de caminho; `urls_extras` marca ativo via `view.crud.get_urls()`.
- [ ] T039 [P] [US5] Teste de `nav_run`: YAML inexistente → `None` sem exceção; YAML inválido → log de erro e `menu=None`; ordem de precedência `path` > `subnav_template_name` > `<app>/subnav.yaml`.
- [ ] T040 [P] [US5] Teste de renderização de `/`: HTML contém `id="emf"`, `<emf-app>`, `INÍCIO`; como superusuário contém "Auditoria de Acessos" e "Testes"; como usuário comum não contém "Manutenção de Usuários".

### Implementação da História de Usuário 5

- [ ] T041 [US5] Criar `backend/utils/templatetags/menus.py` (`register`, `menu`, `subnav`, `navbar`, `nav_run`, `resolve_urls_inplace`) conforme plan §9 e `contracts/menus-yaml.md` (garantir `backend/utils/templatetags/__init__.py` se necessário).
- [ ] T042 [P] [US5] Criar `_templates/menus/menu.html`, `_templates/menus/nav.html`, `_templates/menus/subnav.html` conforme `contracts/menus-yaml.md` ("Saídas HTML").
- [ ] T043 [P] [US5] Criar `_templates/menus/menu_main.yaml` (INÍCIO, 1., 2., 3.) e `_templates/menus/menu_administracao.yaml` (Configurações Gerais, Manutenção de Usuários → `backend.eauth:user_list` e `backend.eauth:pesquisar_auditlog`, Testes para superusuário → `/teste/` e `/wstest/`) conforme `contracts/menus-yaml.md`.

**Ponto de Controle**: menus funcionais e sensíveis a permissões.

---

## Fase 8: História de Usuário 6 - Página-base, índice, 404 e demonstração (Prioridade: P3)

**Objetivo**: casca visual e páginas simples.

**Teste Independente**: `GET /` → 200 com `#emf`; anônimo vê o ícone de login; autenticado vê "Meu Perfil".

### Testes da História de Usuário 6

- [ ] T044 [P] [US6] Teste: anônimo em `/` tem link para `backend.eauth:login`; autenticado tem "Meu Perfil" e formulário POST de logout com `csrfmiddlewaretoken`.
- [ ] T045 [P] [US6] Teste: mensagens do Django (`messages.error`) aparecem como `alert-danger` em `base.html`; `404.html` renderizado com `resolver_match` definido contém `<emf-error-404>`.

### Implementação da História de Usuário 6

- [ ] T046 [US6] Criar `_templates/base.html` conforme `contracts/templates.md` (blocos, sprite SVG, `<div id="emf"><emf-app>`, `vite_hmr_client`, `vite_asset 'main.js'`, menus, mensagens, rodapé com seletor de tema, `extra_js`); manter fielmente (inclusive `#svg-emais` e `perms.menu_administracao`) ou registrar a correção em `research.md`.
- [ ] T047 [P] [US6] Criar `_templates/index.html` (logotipo `imgs/logo_backend.svg`) e `_templates/404.html` (`<emf-error-404>`); confirmar `path("", TemplateView.as_view(template_name="index.html"), name="index")` em `backend/urls.py`.
- [ ] T048 [P] [US6] Confirmar as tags de `backend/utils/templatetags/common_tags.py` usadas pelos templates (`container_css_class`, `view_class_name`, `avatar_user`, `url`, `str2intabs`, `audio_url`, `is_video_url`, `youtube_url`, `youtube_id`, `facebook_url`, `component_frontend`, `file_extension`, `params_search_to_api`).

**Ponto de Controle**: todas as histórias funcionais.

---

## Fase 9: Acabamento e Preocupações Transversais

- [ ] T049 [P] Executar `poetry run ruff check backend/crud backend/utils` e `poetry run ruff format --check` (regras `E`, `F`, `I`); corrigir ordenação de imports e avisos.
- [ ] T050 [P] Executar `poetry run pytest backend/crud backend/utils _tests -q` e garantir verde (o teste `_tests/test_initials.py` deve continuar ignorando `crud`, que não está em `INSTALLED_APPS`).
- [ ] T051 [P] Validar manualmente o roteiro de `quickstart.md` (URLs, permissões, ordenação, menus).
- [ ] T052 Revisar `research.md` ("Particularidades, dívidas técnicas e riscos") e decidir, por item, replicar ou corrigir; registrar eventuais correções em `spec.md`/`plan.md` (constituição, Fluxo de Desenvolvimento §3).
- [ ] T053 [P] Atualizar a documentação (README, seção de estrutura/`_templates`) se nomes de rotas ou arquivos mudarem.

---

## Dependências e Ordem de Execução

### Dependências de Fase

- **Preparação (Fase 1)**: sem dependências.
- **Fundacional (Fase 2)**: depende da Fase 1; **bloqueia** todas as histórias.
- **Histórias (Fases 3–8)**: dependem da Fase 2. US1 e US2 são P1 e dependem de `base.py` (T013/T014); US3 depende de T009/T026; US4 depende de US1 (views); US5 independe do CRUD (exceto o `active` via `view.crud`) e de `002` para os nomes de rota; US6 depende de US5 (menus usados em `base.html`) e de `002` (`avatar_user`, rotas de login/logout).
- **Acabamento (Fase 9)**: depende das histórias desejadas.

### Dependências Dentro das Histórias

- T004 → T005 → T009; T007 → T008 → T009; T009 → T013, T014, T026; T014 → T016.
- Testes (T011, T012, T018–T020, T023–T025, T030–T033, T038–T040, T044–T045) podem ser escritos antes ou junto da implementação correspondente.
- Templates (T015, T027, T028, T035, T042, T043, T046, T047) são independentes entre si ([P]) e dependem apenas da definição dos contratos.

### Oportunidades de Paralelismo

- T006, T010 (Fundacional) em paralelo com T004/T005.
- Todos os templates de cada fase e todos os testes marcados [P].
- US5 (menus) pode ser desenvolvida em paralelo a US3/US4 por outra pessoa.

---

## Estratégia de Implementação

### MVP Primeiro (US1 + US2 + US3)

1. Concluir Fases 1 e 2.
2. Implementar US1 (CRUD básico) e validar `/teste/`.
3. Adicionar US2 (permissões) e US3 (listagem) — fecha o MVP do CRUD.
4. **PARAR e VALIDAR** com `quickstart.md`.

### Entrega Incremental

1. US4 (layouts/detalhe) → validar o teste de layout e o detalhe.
2. US5 (menus) → validar a barra e o menu de administração.
3. US6 (base/índice/404) → validar `/` e mensagens.
4. Fase 9 (ruff/pytest/documentação).

### Observação de Fidelidade

O estado atual contém dívidas técnicas catalogadas em `research.md` (R1–R28). Para reproduzir o projeto **exatamente**, replique-as; para uma reconstrução melhorada, aplique as recomendações de correção (principalmente R10, R11, R12, R13, R19 e R23) e atualize esta especificação na mesma entrega.
