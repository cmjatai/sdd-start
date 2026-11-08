---

description: "Lista de tarefas de reconstrução da fundação do projeto Django"
---

# Tarefas: Fundação do Projeto Django

**Entrada**: Documentos de design em `/specs/001-fundacao-projeto-django/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de usuário), research.md, data-model.md, contracts/ (`settings-e-ambiente.md`, `utilitarios.md`)

**Testes**: Incluídos (pytest e ruff), pois o estado de referência define `pytest` e `ruff` como parte da qualidade (FR-034, FR-035, FR-038).

**Organização**: As tarefas são agrupadas por história de usuário. **Todas as tarefas estão desmarcadas**: este arquivo é um roteiro de reconstrução a partir do zero.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: A qual história de usuário a tarefa pertence (US1…US6)
- Os caminhos são relativos à raiz do repositório; os detalhes de cada item estão no `plan.md` ("Detalhamento de Implementação", §1–§15), em `data-model.md` e em `contracts/`

## Convenções de Caminhos

- **Aplicação web (monorepo Django)**: pacote `backend/` na raiz; configurações em `backend/settings/`; testes em `_tests/` e `**/tests.py`; notebooks em `__notebooks/`

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: Esqueleto do repositório, dependências e ferramentas

- [ ] T001 Criar a estrutura de diretórios: `backend/`, `backend/settings/`, `backend/utils/{migrations,fixtures,templatetags}/`, `_tests/`, `__notebooks/`, `.github/` e a pasta `logs/` (local, não versionada) conforme `plan.md` (Estrutura do Projeto)
- [ ] T002 Criar `pyproject.toml` com `[project]` (`name="sdd-start"`, `version="0.1.0"`, MIT, `requires-python=">=3.12,<4.0"`), `[build-system]` poetry-core `>=2.0.0,<3.0.0`, `[tool.poetry] package-mode=false`, dependências e grupos `dev`/`test`/`docs` de `contracts/settings-e-ambiente.md` §8
- [ ] T003 Executar `poetry install --with dev,test` e gerar `poetry.lock` (Django 6.0.x)
- [ ] T004 [P] Criar `.gitignore` com os padrões de FR-036 (`.env`, `*.log`, `*.pid`, `db.sqlite3`, `node_modules/`, `.venv`, `.pytest_cache/`, `.coverage`, `.ruff_cache/`, `.vscode/`, `security.json`, `.eslintcache`, `__notebooks__private/`, `__private__/`, `.npm/`, `__pycache__/`)
- [ ] T005 [P] Criar `.editorconfig` (seção `[*.{js,jsx,mjs,cjs,ts,tsx,mts,cts,vue}]`: `charset=utf-8`, `indent_size=2`, `indent_style=space`, `insert_final_newline=true`, `trim_trailing_whitespace=true`) e `.prettierrc.json` (`semi:false`, `singleQuote:true`, `arrowParens:"avoid"`)
- [ ] T006 [P] Criar `.github/dependabot.yml` (`version: 2`; npm `/`, docker e docker-compose em `/_docker/dev` e `/_docker/prod`, pip `/`; todos `weekly`); a recomendação é uma única lista `updates:` (ver `research.md`)
- [ ] T007 [P] Adicionar ao `pyproject.toml` as seções `[tool.pytest.ini_options]`, `[tool.coverage.run]` e `[tool.ruff.lint]` (`select=["E","F","I"]`) de `contracts/settings-e-ambiente.md` §8

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: Núcleo do Django que DEVE existir antes de qualquer história

**⚠️ CRÍTICO**: Nenhuma história pode começar até esta fase estar concluída

- [ ] T008 Criar `manage.py` (`#!/usr/bin/env python`, `setdefault("DJANGO_SETTINGS_MODULE","backend.settings")`, `execute_from_command_line`) e torná-lo executável
- [ ] T009 Criar `backend/settings/zenv.py` (`production`, `AutoConfig` com `search_path` condicional, `DEBUG`, `BASE_DIR`, `PROJECT_DIR`, `FOLDER_DEBUG_CONTAINER`) conforme `plan.md` §1
- [ ] T010 [P] Criar `backend/settings/languages.py` (`LANGUAGE_CODE="pt-br"`, `TIME_ZONE` via `TZ`, `USE_I18N`, `USE_TZ`) e `backend/settings/email.py` vazio (0 bytes)
- [ ] T011 [P] Criar `backend/settings/apps.py` (`DJANGO_CORE_APPS`, `DJANGO_THIRD_PARTY_APPS`, `BACKEND_APPS`, `INSTALLED_APPS` na ordem de FR-014; `daphne` antes de `staticfiles`)
- [ ] T012 [P] Criar `backend/settings/middleware.py` com os 8 middlewares na ordem de FR-015
- [ ] T013 Criar `backend/settings/project.py` (imports `# noqa: F403` dos módulos temáticos, `SECRET_KEY`, `DEBUG_TOOLBAR_ACTIVE`, `DEBUG_RUNNING_CONTAINER`, `PROJECT_VERSION`, `ALLOWED_HOSTS`, `SITE_URL`, `CSRF_TRUSTED_ORIGINS`, `SESSIONS_COOKIE_SECURE`, `ROOT_URLCONF`, `ASGI_APPLICATION`, `WSGI_APPLICATION`, `DEFAULT_AUTO_FIELD`, `DATABASES`, bloco de debug, toolbar condicional) conforme `plan.md` §2 (depende de T009–T012 e T014)
- [ ] T014 Criar `backend/settings/__init__.py` (`from .project import *`) e garantir os módulos importados por `project.py` que pertencem a outras features: `auth.py` (002), `drf.py` (005), `frontend.py` (007), `medias.py` (009), `solr.py` (008), `zasyncs.py` (006) — usar os contratos das respectivas features ou stubs mínimos enquanto não existirem
- [ ] T015 Criar `backend/__init__.py` (`from .celery import app as celery_app`; `__all__ = ('celery_app',)`) e `backend/celery.py` (`Celery("backend")`, `config_from_object("django.conf:settings", namespace="CELERY")`, `autodiscover_tasks(lambda: settings.INSTALLED_APPS)`)
- [ ] T016 Criar `.env` de desenvolvimento em `backend/.env` (não versionado) com `DEBUG=True`, `SECRET_KEY`, `DATABASE_URL_DEV` de exemplo (`contracts/settings-e-ambiente.md` §1) e garantir o diretório `logs/`

**Ponto de Controle**: Fundação pronta; `python manage.py check` pode ser tentado quando os apps referenciados existirem

---

## Fase 3: História de Usuário 1 - Subir o projeto configurado por ambiente (Prioridade: P1) 🎯 MVP

**Objetivo**: O comportamento (debug, banco, Redis, fuso, chave) é decidido só por ambiente/`.env`

**Teste Independente**: com `SECRET_KEY`, `DATABASE_URL_DEV`, `DEBUG=True` e PostgreSQL acessível, `python manage.py check` passa e `migrate` aplica as migrações

### Testes da História de Usuário 1

- [ ] T017 [P] [US1] Criar `_tests/__init__.py` (vazio) e `_tests/test_settings_ambiente.py` com testes (via `subprocess`/`importlib.reload` com `monkeypatch.setenv`) de: `DATABASE_URL_DEV` com `DEBUG=True`; `DATABASE_URL_PRD` com `DEBUG=False`; ausência de `SECRET_KEY` → `decouple.UndefinedValueError`; `LANGUAGE_CODE`/`TIME_ZONE`/`USE_TZ` padrão (cenários 1–6 de US1)

### Implementação da História de Usuário 1

- [ ] T018 [US1] Validar em `backend/settings/project.py` o bloco `DATABASES` (`dj_database_url.parse`, `DATABASE_URL_DEV if DEBUG else DATABASE_URL_PRD`) e a sobrescrita `HOST="localhost"`/`PORT=5433` com os três `print` de FR-006 quando `DEBUG and FOLDER_DEBUG_CONTAINER != PROJECT_DIR`
- [ ] T019 [US1] Validar a precedência do `.env` em `backend_data/.env` (flag `production`) versus `backend/.env` (FR-002) em `backend/settings/zenv.py`
- [ ] T020 [US1] Executar `python manage.py check` e anotar qualquer módulo/app ausente (resolver pelas features correspondentes)

**Ponto de Controle**: US1 funcional e testável de forma independente

---

## Fase 4: História de Usuário 2 - Configurações modulares, apps, middleware e roteamento raiz (Prioridade: P1)

**Objetivo**: Ponto de entrada único de settings, roteamento raiz e entradas ASGI/WSGI/Celery

**Teste Independente**: `check`, `makemigrations --check --dry-run`, `import backend.celery` e `GET /`

### Testes da História de Usuário 2

- [ ] T021 [P] [US2] Criar `_tests/test_urls_entrypoints.py`: `reverse("index") == "/"`, `GET /system/` redireciona ao login do admin, `backend.celery_app` é a instância Celery de nome `backend`, `settings.ROOT_URLCONF == "backend.urls"`, `ASGI_APPLICATION`/`WSGI_APPLICATION`

### Implementação da História de Usuário 2

- [ ] T022 [P] [US2] Criar `backend/urls.py` conforme `contracts/settings-e-ambiente.md` §6 (`system/`, includes de `api`/`eauth`/`utils`, `index`, `__debug__/` e `static()` condicionais)
- [ ] T023 [P] [US2] Criar `backend/wsgi.py` (`get_wsgi_application`) e `backend/asgi.py` (`ProtocolTypeRouter` com `http` e `websocket` via `AuthMiddlewareStack(URLRouter(backend.utils.routing.websocket_urlpatterns))`) conforme `plan.md` §10, preservando a ordem de imports do original
- [ ] T024 [P] [US2] Criar `backend/context_processors.py` (`debug(request)` → `{"DEBUG": settings.DEBUG}`) e registrá-lo em `TEMPLATES` de `backend/settings/frontend.py` (feature 007)
- [ ] T025 [P] [US2] Criar `backend/settings/fake.py` (SQLite em `PROJECT_DIR/db.sqlite3`, `DEBUG=False`, `DJANGO_VITE_DEV_MODE=False`, `DJANGO_VITE` com `manifest_path`) conforme `plan.md` §7
- [ ] T026 [US2] Em `backend/settings/project.py`, adicionar `INTERNAL_IPS`, `NOTEBOOK_ARGUMENTS` (só `DEBUG`) e o acréscimo condicional de `debug_toolbar` em `INSTALLED_APPS`/`MIDDLEWARE` (FR-009, FR-010)
- [ ] T027 [US2] Rodar `python manage.py check` e `python manage.py makemigrations --check --dry-run`; corrigir divergências

**Ponto de Controle**: US1 e US2 funcionais

---

## Fase 5: História de Usuário 3 - Registro de logs e diagnóstico de falhas (Prioridade: P2)

**Objetivo**: Log rotativo, console em debug, caminho da requisição e `excepthook`

**Teste Independente**: `logging.getLogger("backend").error("x")` grava em `logs/backend_logger.log`

### Testes da História de Usuário 3

- [ ] T028 [P] [US3] Criar `_tests/test_logs.py`: `MyFormatter.format` anexa ` - <path>` quando há variável local `request` na pilha e não anexa caso contrário; `LOGGING["handlers"]["backend_logger_file"]` tem `maxBytes=15728640` e `backupCount=10`; `console` usa filtro `require_debug_true`; `uncaught_exceptions` registra um erro (`caplog`)

### Implementação da História de Usuário 3

- [ ] T029 [US3] Criar `backend/settings/logs.py` conforme `plan.md` §8 (`LOGGING_ROOT_LEVEL`, `logging.captureWarnings(True)`, `MyFormatter`, `LOGGING`, `uncaught_exceptions`, `sys.excepthook`)
- [ ] T030 [US3] Garantir a criação de `logs/` no diretório de trabalho (documentar no `quickstart.md`; Docker nas features 010/011)
- [ ] T031 [US3] Validar manualmente o cenário do `quickstart.md` §4 (arquivo criado e linha gravada)

**Ponto de Controle**: logs operacionais

---

## Fase 6: História de Usuário 4 - Utilitários e mixins reutilizáveis (Prioridade: P2)

**Objetivo**: `utilss.py`, `model_mixins.py` e biblioteca `common_tags`

**Teste Independente**: importar os módulos no shell e renderizar templates com `{% load common_tags %}`

### Testes da História de Usuário 4

- [ ] T032 [P] [US4] Criar `_tests/test_utilss.py` cobrindo: `decimal2str(Decimal("1234.565")) == "1.234,56"`, entrada inválida devolve `str(value)`, `quantize`, `normalize("Ação ç") == "Acao c"`, `get_mime_type_from_file_extension` (`odt`, `pdf`, `PDF`), `dict2attr`, `show_results_filter_set` (vazio, só `iframe`, com filtros), `intervalos_tem_intersecao` (extremos inclusivos), `hash_sha512` (caminho e arquivo aberto), `clean_text`, `DisableSignals` (sinal não dispara dentro e volta depois), `TimeExecution`
- [ ] T033 [P] [US4] Criar `_tests/test_model_mixins.py` com `model_bakery`/modelos de teste: `SearchModelMixin` (campo `search` normalizado, tupla e `__`), `CleanModelMixin` (duplicidade com `unique_together` e `NULL` → `ValidationError`), `DateModelMixin` (`created_at`/`modified_at`)
- [ ] T034 [P] [US4] Criar `_tests/test_common_tags.py` cobrindo filtros/tags de `contracts/utilitarios.md` §4 (`decimal2str`, `startswith`, `jsonify`, `lookup`, `age`, `str2intabs`, `url`, `youtube_url`, `youtube_id`, `file_extension`, `params_search_to_api`, `obfuscate_value`, `settings_key_tag`, `yaml_render`, `model_verbose_name`)

### Implementação da História de Usuário 4

- [ ] T035 [US4] Criar `backend/utilss.py` com todos os itens de `contracts/utilitarios.md` §1 (ordem de `plan.md` §11)
- [ ] T036 [US4] Criar `backend/model_mixins.py` com `DateModelMixin`, `AuditoriaModelMixin`, `SearchModelMixin`, `CleanModelMixin`, `SaveModelWithFileMixin` conforme `data-model.md` §5 e `plan.md` §12 (replicar o `save` posicional do `SaveModelWithFileMixin` para fidelidade; ver `research.md`)
- [ ] T037 [US4] Criar `backend/utils/templatetags/common_tags.py` (sem `__init__.py` no pacote) com os 39 filtros/tags de `contracts/utilitarios.md` §4 e `get_class`
- [ ] T038 [US4] Rodar `pytest _tests/test_utilss.py _tests/test_model_mixins.py _tests/test_common_tags.py` e corrigir falhas

**Ponto de Controle**: utilitários disponíveis às demais features

---

## Fase 7: História de Usuário 5 - Modelos base do app `utils` e migração inicial (Prioridade: P2)

**Objetivo**: `Teste`, `Metadata`, migração `0001_initial` e admin automático

**Teste Independente**: `python manage.py migrate utils` cria `utils_teste` e `utils_metadata`; ambos aparecem em `/system/`

### Testes da História de Usuário 5

- [ ] T039 [P] [US5] Criar `_tests/test_utils_models.py` (`pytest.mark.django_db`): `set_or_update_metadata` cria e depois **mescla**; `get_metadata` devolve `None` sem registro; unicidade (`content_type`, `object_id`) levanta `IntegrityError`; `Teste` ordenado por `teste` e `str()` = texto; ambos registrados em `admin.site`

### Implementação da História de Usuário 5

- [ ] T040 [P] [US5] Criar `backend/utils/__init__.py` (`default_app_config = "backend.utils.apps.UtilsConfig"`) e `backend/utils/apps.py` (`UtilsConfig`, `ready()` importando `services.signals` e `services.signals_syncrefresh` — feature 006)
- [ ] T041 [US5] Criar `backend/utils/models.py` com `Teste`, `MetadataManager` e `Metadata` conforme `data-model.md` §1–§2
- [ ] T042 [US5] Gerar `backend/utils/migrations/0001_initial.py` (`python manage.py makemigrations utils`), criando também `migrations/__init__.py`; conferir contra `data-model.md` §3
- [ ] T043 [P] [US5] Criar `backend/utils/admin.py` (`register_all_models_in_admin(__name__)`) e a pasta `backend/utils/fixtures/` (vazia)
- [ ] T044 [US5] Rodar `python manage.py migrate` e `python manage.py makemigrations --check --dry-run`

**Ponto de Controle**: ciclo modelo → migração → admin validado

---

## Fase 8: História de Usuário 6 - Qualidade verificável e ferramentas do repositório (Prioridade: P3)

**Objetivo**: pytest, cobertura, ruff e notebooks funcionando

**Teste Independente**: `pytest` passa; `ruff check .` executa; a primeira célula do notebook inicializa o Django

### Testes da História de Usuário 6

- [ ] T045 [P] [US6] Criar `_tests/test_initials.py` (com `pytestmark = pytest.mark.django_db`) e `backend/tests.py` com o teste `test_app_init_files_have_default_app_config` conforme `research.md` (replicar a duplicação)
- [ ] T046 [P] [US6] Criar `_tests/test_fixture_app.py`: a fixture `app` devolve `OurTestApp` com `default_user == admin_user.username` e `GET /system/` autenticado retorna 200

### Implementação da História de Usuário 6

- [ ] T047 [US6] Criar `conftest.py` (`OurTestApp` com `default_user`, `get` com `setdefault('user')`/`setdefault('auto_follow', True)`; fixture `app(request, admin_user)` com `WebTestMixin()._patch_settings()` e finalizador) conforme `plan.md` §15
- [ ] T048 [P] [US6] Criar `__notebooks/django_setup.py` (`PROJECT_ROOT_DIR`, `DJANGO_ROOT_DIR`, `sys.path.append`, `DJANGO_ALLOW_ASYNC_UNSAFE="false"`, `django.setup()`) e os notebooks `__notebooks/0init_file.ipynb` e `__notebooks/shell_plusss.ipynb` (duas células de código; a primeira com `import django_setup` e a expressão `django_setup.PROJECT_ROOT_DIR, django_setup.DJANGO_ROOT_DIR`)
- [ ] T049 [US6] Executar `pytest` na raiz (com PostgreSQL acessível) e conferir coleta de `**/tests.py` e `**/test_*.py`, `--reuse-db` e relatório de cobertura
- [ ] T050 [P] [US6] Executar `ruff check backend/utilss.py backend/model_mixins.py backend/utils backend/settings _tests conftest.py` e corrigir apenas problemas dos arquivos desta feature (`ruff check .` global pode listar achados legados; ver `research.md`)
- [ ] T051 [P] [US6] Executar `ruff format --check` nos arquivos novos desta feature (opcional; `black`/`isort` permanecem como ferramentas do grupo `dev`)

**Ponto de Controle**: todas as histórias independentemente funcionais

---

## Fase 9: Acabamento e Preocupações Transversais

**Propósito**: Melhorias que afetam várias histórias

- [ ] T052 [P] Revisar `research.md` ("Particularidades, dívidas técnicas e riscos observados") e confirmar que cada particularidade replicada (ex.: `SESSIONS_COOKIE_SECURE`, `email.py` vazio, `ALLOWED_HOSTS=["*"]`) está presente ou conscientemente corrigida
- [ ] T053 [P] Garantir que nenhum segredo está versionado (`git grep -n "SECRET_KEY"` só em código que lê de `config`) e que `backend/.env` está no `.gitignore`
- [ ] T054 Executar a validação completa do `quickstart.md` (§1–§7)
- [ ] T055 [P] Confirmar `python manage.py check --deploy` sem erros de configuração inesperados para esta feature (avisos de `SESSION_COOKIE_SECURE`, `ALLOWED_HOSTS` são conhecidos)

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências
- **Fundacional (Fase 2)**: depende da Preparação; BLOQUEIA todas as histórias. Internamente: T009 → T010–T012 → T013/T014 → T015 → T016
- **US1 (P1)** e **US2 (P1)**: após a Fundacional; US2 reaproveita `project.py` de US1 (T026 depende de T013)
- **US3 (P2)**: após a Fundacional (`logs.py` é importado por `project.py`; para o `check` inicial pode-se criá-lo logo na Fundacional)
- **US4 (P2)**: independente de US1–US3, exceto `common_tags` que usa `utilss.decimal2str` (T037 depende de T035) e `model_mixins` que usa `utilss` (T036 depende de T035)
- **US5 (P2)**: depende de T036 (`DateModelMixin`) e T035 (`register_all_models_in_admin`)
- **US6 (P3)**: após as demais para executar a suíte completa (T049); T047 (`conftest.py`) pode ser feito antes
- **Acabamento (Fase 9)**: depende das histórias desejadas

### Dentro de Cada História

- Testes escritos antes da implementação (devem falhar inicialmente)
- Utilitários antes de mixins; mixins antes de modelos; modelos antes da migração e do admin

### Oportunidades de Paralelismo

- T004–T007 (Preparação) em paralelo; T010–T012 em paralelo
- T022–T025 em paralelo (arquivos distintos)
- T032–T034 em paralelo; T039 e T045–T046 em paralelo com implementações não relacionadas

## Exemplo de Paralelismo: História de Usuário 4

```text
Task: "Criar _tests/test_utilss.py"          (T032)
Task: "Criar _tests/test_model_mixins.py"    (T033)
Task: "Criar _tests/test_common_tags.py"     (T034)
# Depois: T035 (utilss.py) → T036 (model_mixins.py) e T037 (common_tags.py) em paralelo
```

---

## Estratégia de Implementação

### MVP Primeiro (US1 + US2)

1. Concluir Fase 1 (Preparação) e Fase 2 (Fundacional)
2. Concluir US1 e US2: `manage.py check` verde, `/system/` e `/` respondendo
3. **PARAR e VALIDAR** com `quickstart.md` §2–§3

### Entrega Incremental

1. Fundacional + US1 + US2 → projeto sobe (MVP)
2. + US3 (logs) → diagnóstico
3. + US4 (utilitários) → base para as features 002–009
4. + US5 (modelos `utils`) → ciclo modelo → admin
5. + US6 (qualidade) → `pytest` e `ruff`

## Notas

- Esta feature referencia módulos de settings de outras features (`auth`, `drf`, `frontend`, `medias`, `solr`, `zasyncs`) e apps (`eauth`, `api`, `globalrules`); o `manage.py check` completo só passa quando essas features existirem (ou com stubs)
- Preservar, para fidelidade, as particularidades de `research.md`; as correções recomendadas são opcionais
- Nenhuma tarefa deste arquivo está marcada como concluída
