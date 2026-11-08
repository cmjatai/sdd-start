# Tarefas: Regras e Permissões Globais

**Entrada**: Documentos de design em `/specs/003-regras-permissoes-globais/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de usuário), research.md, data-model.md, contracts/permissoes.md; features 001 e 002 concluídas (inclui `backend/utils/models.py` com `Teste` e `Metadata`, e `backend/eauth/models.py` com `User`).

**Testes**: incluídos (Constituição, princípio VIII: pytest e ruff).

**Organização**: as tarefas são agrupadas por história de usuário. Todas as tarefas permanecem desmarcadas: este arquivo é um roteiro de reconstrução.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: história de usuário a que pertence (US1…US5)
- Caminhos exatos de arquivos nas descrições; detalhes de código em `plan.md` → "Detalhamento de Implementação"

## Convenções de Caminhos

- Aplicação web Django: código em `backend/`, testes em `backend/globalrules/tests.py` (ou `backend/globalrules/test_*.py`) e `_tests/`

---

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: estrutura do app

- [ ] T001 Criar o pacote `backend/globalrules/` com `__init__.py`, `models.py` (vazio), `views.py` (vazio), `urls.py` (`urlpatterns = []`) e `migrations/__init__.py` (vazio)
- [ ] T002 Registrar `"backend.globalrules"` por último na lista `INSTALLED_APPS` em `backend/settings/apps.py` (depois de `"backend.api"`)

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: vocabulário de permissões e classe `AppConfig`, necessários a todas as histórias

**⚠️ CRÍTICO**: nenhuma história pode começar antes desta fase

- [ ] T003 Implementar em `backend/globalrules/__init__.py` as constantes `default_app_config`, `RP_LIST/RP_VIEW/RP_ADD/RP_CHANGE/RP_DELETE`, `GROUP_ADM_ADMIN` (lazy `'Administrador do Sistema'`), `GROUP_VISITANTE = ''`, `BACKEND_GROUPS`, `menu_administracao = 'menu_1'`, `action_1 = 'orcamento_1'`, `PERMS_FOR_USERS`, `VARS`, `PERMS_FOR_USERS_DICT` e `MAP_GROUPS_AND_PERMS = dict2attr(...)` (plan.md §1)
- [ ] T004 [P] Garantir `dict2attr` em `backend/utilss.py` (dict com acesso por atributo) — já criado na feature 001
- [ ] T005 Declarar `class AppConfig(apps.AppConfig)` em `backend/globalrules/apps.py` com `default_auto_field`, `name='backend.globalrules'`, `label='globalrules'`, `verbose_name` (plan.md §3)
- [ ] T006 Ligar `User.Meta.permissions = PERMS_FOR_USERS` em `backend/eauth/models.py` (importando de `backend.globalrules`) e gerar/aplicar a migração correspondente no app `eauth` se ainda não existir (feature 002)

**Ponto de Controle**: `python manage.py check` passa e `from backend.globalrules import MAP_GROUPS_AND_PERMS` funciona

---

## Fase 3: História de Usuário 1 - `list_<modelo>` e grupos sincronizados a cada `migrate` (Prioridade: P1) 🎯 MVP

**Objetivo**: criar permissões `list_<modelo>`, grupos e atribuições após `migrate`

**Teste Independente**: `python manage.py migrate` em banco limpo cria `eauth.list_user` e o grupo com 16 permissões

### Testes da História de Usuário 1

- [ ] T007 [P] [US1] Teste das constantes e do mapa em `backend/globalrules/tests.py` (`RP_*`, `MAP_GROUPS_AND_PERMS.menu_administracao == 'menu_1'`, `GROUP_VISITANTE == ''`)
- [ ] T008 [P] [US1] Teste `list_user`/`list_teste` existem em `Permission` e `eauth.menu_1`/`eauth.orcamento_1` existem, em `backend/globalrules/tests.py` (`@pytest.mark.django_db`)
- [ ] T009 [P] [US1] Teste de idempotência/limpeza: grupo com 16 permissões; adicionar permissão extra, chamar `get_rules().update_groups()` e verificar retorno a 16; nenhum `Group` com nome vazio — em `backend/globalrules/tests.py`

### Implementação da História de Usuário 1

- [ ] T010 [US1] Criar `backend/globalrules/map_rules.py` com `__base__`, `__base_view__`, `__base_change__`, `rules_group_adm_admin` (User + `menu_administracao`; Teste com públicas `set(__base_view__)`; Metadata), `rules_group_visitante`, `rules_patterns` (plan.md §2)
- [ ] T011 [US1] Implementar em `backend/globalrules/apps.py` o receiver `create_proxy_permissions` com `dispatch_uid='django.contrib.auth.management.create_permissions'`, incluindo mutação de `opts.permissions`, tratamento de modelos proxy, validação de `max_length` e `bulk_create` (plan.md §3)
- [ ] T012 [US1] Implementar em `backend/globalrules/apps.py` `get_rules()` com a classe `Rules` (`associar`, `_config_group`, `groups_add_user`, `groups_remove_user`, `update_groups`)
- [ ] T013 [US1] Implementar em `backend/globalrules/apps.py` o receiver `update_groups` (`dispatch_uid='update_groups'`, filtrando pelo `AppConfig` do próprio app)
- [ ] T014 [US1] Rodar `python manage.py migrate` duas vezes e validar `quickstart.md` §1–§2

**Ponto de Controle**: US1 funcional e testável de forma independente

---

## Fase 4: História de Usuário 2 - API REST respeita permissões e permissões públicas (Prioridade: P1)

**Objetivo**: autorização por modelo na API com leitura pública configurável

**Teste Independente**: `GET /api/utils/teste/` anônimo 200; `POST` anônimo 401/403; `GET /api/eauth/user/` anônimo 401/403

### Testes da História de Usuário 2

- [ ] T015 [P] [US2] Teste `rules_patterns_public == {'eauth:user': set(), 'utils:teste': {'utils.list_teste', 'utils.view_teste'}, 'utils:metadata': set()}` em `backend/globalrules/tests.py`
- [ ] T016 [P] [US2] Testes com `APIClient` (acesso anônimo público, anônimo negado, usuário do grupo administrador permitido, usuário sem permissão 403, superusuário permitido) em `backend/api/tests.py` (substituir o stub)
- [ ] T017 [P] [US2] Teste unitário de `BackendModelPermissions.has_permission` com view simulada (`_ignore_model_permissions`, queryset ausente → `AssertionError`, método `POST` em modelo público) em `backend/api/tests.py`

### Implementação da História de Usuário 2

- [ ] T018 [US2] Em `backend/globalrules/map_rules.py`, construir `rules_patterns_public` com `_get_registration_key` e a união dos conjuntos formatados `"{app_label}{radical}{model_name}"` (plan.md §2)
- [ ] T019 [US2] Criar `backend/api/permissions.py` com `BackendModelPermissions` (`perms_map` próprio e `has_permission`) e `ContainerPermission` (plan.md §4)
- [ ] T020 [US2] Configurar `"DEFAULT_PERMISSION_CLASSES": ("backend.api.permissions.BackendModelPermissions",)` em `backend/settings/drf.py`

**Ponto de Controle**: US1 e US2 funcionam de forma independente

---

## Fase 5: História de Usuário 3 - Visibilidade de menus e áreas administrativas (Prioridade: P2)

**Objetivo**: menu de administração e itens YAML condicionados por permissão

**Teste Independente**: página inicial como superusuário mostra o menu de administração; como usuário comum, não

### Testes da História de Usuário 3

- [ ] T021 [P] [US3] Teste com `app` (webtest) em `_tests/` ou `backend/utils/tests.py`: superusuário vê `nav-admin`, usuário comum do grupo administrador não vê (documentar a particularidade)
- [ ] T022 [P] [US3] Teste de `resolve_urls_inplace` (`backend/utils/templatetags/menus.py`) com `check_permission` negado: `url == ""`, `active == ""`; sem `url`: `children` removido

### Implementação da História de Usuário 3

- [ ] T023 [US3] Garantir em `_templates/base.html` o bloco `{% if perms.menu_administracao %}<ul class="navbar-nav nav-admin">{% menu 'menus/menu_administracao.yaml' %}</ul>{% endif %}`
- [ ] T024 [US3] Declarar `check_permission: menu_administracao` nos itens "Manutenção de Usuários" e "Testes" de `_templates/menus/menu_administracao.yaml` e suportar `check_permission` em `backend/utils/templatetags/menus.py` (feature 004 detalha o tag `menu`)

**Ponto de Controle**: US1–US3 funcionais

---

## Fase 6: História de Usuário 4 - Contrato de permissões para CRUD e WebSocket (Prioridade: P2)

**Objetivo**: garantir que CRUD e consumer consumam `RP_*` e `rules_patterns_public` conforme o contrato

**Teste Independente**: importar `RP_*` e verificar nomes montados e decisões do consumer

### Testes da História de Usuário 4

- [ ] T025 [P] [US4] Teste de `PermissionRequiredContainerCrudMixin.has_permission` (lista vazia → público; qualquer permissão basta) em `backend/crud/tests.py`
- [ ] T026 [P] [US4] Teste do `SyncRefreshConsumer.sync_refresh_message` (anônimo + `utils:teste` mantém `instance`; anônimo + `eauth:user` remove; superusuário mantém) em `backend/utils/tests.py` usando `channels.testing`

### Implementação da História de Usuário 4

- [ ] T027 [US4] Usar `from backend.globalrules import RP_ADD, RP_CHANGE, RP_DELETE, RP_LIST, RP_VIEW` em `backend/crud/base.py` (`permission_required = (RP_LIST,)` etc.; função `permission(rad)`; `PermissionRequiredContainerCrudMixin`) — detalhado na feature 004
- [ ] T028 [US4] Em `backend/utils/consumers.py`, importar `rules_patterns_public` no `__init__` de `SyncRefreshConsumer` e aplicar a lógica `detail_`/`view_` em `sync_refresh_message` — detalhado na feature 006

**Ponto de Controle**: US1–US4 funcionais

---

## Fase 7: História de Usuário 5 - Sequências de ids consistentes (Prioridade: P3)

**Objetivo**: realinhar sequências após `migrate`

**Teste Independente**: inserir `Teste` com `id=500`, rodar `migrate`, próximo id = 501

### Testes da História de Usuário 5

- [ ] T029 [P] [US5] Teste de `reset_id_model(Teste)` em PostgreSQL (`@pytest.mark.django_db`): insert com id explícito, chamada da função, próximo id = max+1; teste de que exceções são engolidas (tabela inexistente/modelo sem `id`)

### Implementação da História de Usuário 5

- [ ] T030 [US5] Implementar `reset_id_model(model)` em `backend/globalrules/apps.py` com `setval(pg_get_serial_sequence(...))`, recriação de `<tabela>_id_seq` e `try/except` amplo (plan.md §3)
- [ ] T031 [US5] Implementar o receiver `check_ids_sequences` (`dispatch_uid='check_ids_sequences'`) iterando `app_config.models` com `_meta.managed`

**Ponto de Controle**: todas as histórias funcionais

---

## Fase 8: Acabamento e Preocupações Transversais

- [ ] T032 [P] Rodar `ruff check backend/globalrules backend/api` e `ruff format --check` e corrigir apontamentos
- [ ] T033 [P] Rodar `pytest _tests/test_initials.py backend/globalrules backend/api -q` (inclui o teste de `default_app_config`)
- [ ] T034 Validar `specs/003-regras-permissoes-globais/quickstart.md` de ponta a ponta (migrate duplo, shell, curl, interface)
- [ ] T035 [P] Documentar em `README.md` (seção de arquitetura) o procedimento "como adicionar permissões/grupos" (plan.md §7), se ainda não existir
- [ ] T036 Conferir que não há novas tabelas: `python manage.py makemigrations --check --dry-run` não gera migração para `globalrules`

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências
- **Fundacional (Fase 2)**: depende da Preparação; bloqueia todas as histórias
- **Histórias (Fases 3–7)**: dependem da Fundacional
- **Acabamento (Fase 8)**: depende das histórias desejadas

### Dependências entre Histórias de Usuário

- **US1 (P1)**: após a Fundacional; independente
- **US2 (P1)**: após a Fundacional; depende de `map_rules.py` (T010) para `rules_patterns_public`; T018 estende o arquivo de T010 (mesmo arquivo, não paralelizar)
- **US3 (P2)**: após a Fundacional; usa o grupo/permissões da US1 para o teste com usuário do grupo
- **US4 (P2)**: depende de `rules_patterns_public` (US2) e dos prefixos `RP_*` (Fundacional); a implementação do CRUD/consumer pertence às features 004/006
- **US5 (P3)**: após a Fundacional; independente

### Dentro de Cada História de Usuário

- Testes escritos antes e devem falhar antes da implementação
- `apps.py`: T011 → T012 → T013 (mesmo arquivo, sequenciais) → T030 → T031

### Oportunidades de Paralelismo

- T004 em paralelo com T003/T005
- Testes marcados com [P] da mesma história em paralelo
- US2, US3 e US5 podem ser trabalhadas em paralelo após a Fundacional (arquivos distintos), exceto a edição de `apps.py` (US1 e US5) e `map_rules.py` (US1 e US2)

## Exemplo de Paralelismo: História de Usuário 1

```bash
Task: "T007 constantes em backend/globalrules/tests.py"
Task: "T008 permissões list_ em backend/globalrules/tests.py"
Task: "T009 idempotência de grupos em backend/globalrules/tests.py"
```

---

## Estratégia de Implementação

### MVP Primeiro (Somente a História de Usuário 1)

1. Concluir Preparação (Fase 1) e Fundacional (Fase 2)
2. Concluir a US1 (permissões `list_` e grupos)
3. **PARAR e VALIDAR**: `migrate` duplo e conferência no shell (`quickstart.md` §1–§2)

### Entrega Incremental

1. Fundação → US1 (MVP) → US2 (API protegida) → US3 (menus) → US4 (contrato CRUD/WebSocket) → US5 (sequências) → Acabamento
2. Cada história agrega valor sem quebrar as anteriores

### Estratégia de Equipe em Paralelo

1. A equipe conclui Preparação + Fundacional
2. Depois: um desenvolvedor na US1/US5 (`apps.py`), outro na US2 (`api/permissions.py`), outro na US3 (templates)

---

## Notas

- Tarefas [P] = arquivos diferentes, sem dependências
- Replicar o comportamento atual (inclusive particularidades em `research.md`) para fidelidade; correções são evolução posterior
- Fazer commit após cada tarefa ou grupo lógico
