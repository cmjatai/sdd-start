# Pesquisa: Fundação do Projeto Django

Decisões técnicas inferidas do código, dos comentários e da constituição. Para cada item: **Decisão**, **Justificativa** e **Alternativas consideradas** (as alternativas são inferidas; não há registro formal no repositório).

## Decisões

### D1. Configuração por `python-decouple` com `AutoConfig`

- **Decisão**: ler toda configuração por `AutoConfig` (`backend/settings/zenv.py`); variáveis de ambiente têm precedência sobre `.env`; `backend/.env` em desenvolvimento e `backend_data/.env` (fora do diretório do projeto) em produção.
- **Justificativa**: 12-factor; o mesmo código roda no host, em contêiner DEV e em contêiner PRD; o `.env` nunca é versionado (`.gitignore`); o arquivo de produção fica em volume persistente fora da árvore do código, o que permite imagem imutável (o comentário do próprio `zenv.py` explica isso).
- **Alternativas**: `django-environ`; `settings.py` por ambiente (`dev.py`/`prod.py`); variáveis só do SO.

### D2. Um único ponto de entrada de settings (`backend.settings`) que reúne módulos temáticos

- **Decisão**: `backend/settings/__init__.py` → `project.py` → `from .<modulo> import *`; cada preocupação em seu módulo; valores transversais e dependentes de mais de um módulo (banco, hosts, toolbar) em `project.py`.
- **Justificativa**: princípio I da constituição; facilita que cada feature acrescente seu módulo; o `import *` mantém `DJANGO_SETTINGS_MODULE=backend.settings` simples.
- **Alternativas**: `settings.py` monolítico; pacote de settings com `base/dev/prod`.

### D3. DEV vs PRD decidido por `DEBUG` (e `FOLDER_DEBUG_CONTAINER`)

- **Decisão**: `DEBUG` seleciona `DATABASE_URL_DEV`/`DATABASE_URL_PRD`; `FOLDER_DEBUG_CONTAINER != PROJECT_DIR` detecta "rodando no host" e redireciona banco (`localhost:5433`), Redis e Solr para `localhost`.
- **Justificativa**: o desenvolvedor pode rodar `runserver`/`pytest`/notebooks no host contra serviços (Postgres, Redis, Solr) que rodam no Docker com portas publicadas, usando o mesmo `.env` do contêiner. O `.env` do contêiner contém hosts internos (`<projeto>-postgres`) que não resolvem no host.
- **Alternativas**: dois `.env` separados; `DJANGO_SETTINGS_MODULE` distinto por ambiente; `docker compose exec` sempre.

### D4. Logging em arquivo rotativo + console condicionado por `DEBUG` + `excepthook`

- **Decisão**: `RotatingFileHandler` 15 MB × 10 em `logs/backend_logger.log`; console só com `DEBUG`; `MyFormatter` anexa `request.path`; `sys.excepthook` registra exceções não tratadas.
- **Justificativa**: em produção (Gunicorn/Daphne/Celery) é preciso persistir logs sem inflar o disco; o caminho da requisição ajuda a correlacionar erros sem middleware extra; o hook captura falhas fora do ciclo de requisição (comandos, tarefas).
- **Alternativas**: logging para `stdout` apenas (padrão Docker); Sentry; `request_id` por middleware/`contextvars`.

### D5. Postgres como único banco; SQLite só em `settings.fake`

- **Decisão**: `fake.py` troca para SQLite para que `collectstatic` rode no `docker build` sem banco.
- **Justificativa**: `collectstatic` não precisa de banco real, mas o `project.py` carrega `DATABASES` de variáveis; o override evita conexão.
- **Alternativas**: variável dummy de banco; `collectstatic` apenas no start.

### D6. Pacote de utilitários com nome `utilss.py` e mixins em `model_mixins.py`

- **Decisão**: módulo `backend/utilss.py` (grafia com dois "s", provavelmente para evitar conflito com o app `backend.utils`) concentra helpers; `backend/model_mixins.py` concentra mixins de modelo.
- **Justificativa**: ambos são importados por settings (`medias.py` referencia `backend.utilss.pil_image`) e por modelos; um módulo sem dependências de apps evita importações circulares (`utilss` só importa modelos tardiamente em `save_in_metadata`).
- **Alternativas**: colocar em `backend/utils/` (arriscaria import circular no carregamento de settings/modelos).

### D7. Admin automático por app (`register_all_models_in_admin`)

- **Decisão**: cada `admin.py` de app chama `register_all_models_in_admin(__name__)`.
- **Justificativa**: um esqueleto de CRUD/API genérico não quer manter `ModelAdmin` por modelo; todo modelo fica disponível em `/system/` sem código adicional.
- **Alternativas**: `@admin.register` por modelo; `admin.autodiscover` com `ModelAdmin` genérico.

### D8. Metadata genérica por `ContentType`

- **Decisão**: `Metadata` associa JSON a qualquer objeto por (`content_type`, `object_id`) únicos; o gerenciador faz `select_related("content_type")` e oferece `get_metadata`/`set_or_update_metadata` (mescla).
- **Justificativa**: guardar dados auxiliares (ex.: dados de sincronização/mídia) sem alterar o esquema de cada modelo; consumido pela API (feature 005) e por `save_in_metadata`.
- **Alternativas**: `JSONField` em cada modelo; EAV.

### D9. Poetry com `package-mode = false` e grupos `dev`/`test`/`docs`

- **Decisão**: `pyproject.toml` no formato misto PEP 621 (`[project]`) + `[tool.poetry.dependencies]`; `poetry.lock` versionado; dependências com caret (`^`) e Django `>=6,<7`.
- **Justificativa**: reprodutibilidade (princípio VIII); Dependabot (`pip`) mantém atualizado; grupos permitem instalar imagem de produção sem ferramentas de teste/documentação.
- **Alternativas**: `requirements.txt`; `uv`; `pip-tools`.

### D10. pytest configurado no `pyproject.toml`, `--reuse-db`, cobertura em toda a raiz

- **Decisão**: `addopts = '--reuse-db -p no:warnings --cov=.'`, `testpaths` com globs `**/tests.py` e `**/test_*.py`; `coverage` omite `_tests/*`, `backend/settings/*`, `backend/wsgi.py`, `backend/asgi.py`.
- **Justificativa**: criação de banco de teste em Postgres é lenta; reuso acelera o ciclo; warnings suprimidos para reduzir ruído.
- **Alternativas**: `pytest.ini`/`tox.ini`; `--create-db` sempre.

### D11. Fixture `app` com django-webtest

- **Decisão**: `conftest.py` oferece cliente WebTest autenticado como `admin_user`, com `auto_follow` em `GET`.
- **Justificativa**: testes de CRUD/páginas com formulários (feature 004) ficam concisos; baseado em um gist citado no docstring (`magopian/6673250`).
- **Alternativas**: `django.test.Client`/`pytest-django` `client`/`admin_client`.

### D12. Cadernos Jupyter com `django_setup`

- **Decisão**: pasta `__notebooks/` com `django_setup.py` e `NOTEBOOK_ARGUMENTS` em `project.py` (`shell_plus --notebook` abre nessa pasta).
- **Justificativa**: exploração interativa do ORM com o Django carregado; prefixo `__` mantém a pasta fora de pacotes e do teste.
- **Alternativas**: apenas `manage.py shell_plus`.

## Particularidades, dívidas técnicas e riscos observados

Recomendação geral: **o estado atual é replicar para fidelidade** (a reconstrução deve reproduzir cada comportamento abaixo); a coluna "Recomendação" indica o que seria o ideal numa evolução. Itens confirmados no código em 2026-11-08.

| # | Observação (confirmada) | Impacto | Reconstrução | Recomendação |
|---|-------------------------|---------|--------------|--------------|
| P1 | `backend/settings/project.py`: `SESSIONS_COOKIE_SECURE = not DEBUG` — nome errado; o Django lê `SESSION_COOKIE_SECURE`. Nenhuma outra ocorrência no código. | Cookie de sessão **nunca** é `Secure`; também falta `CSRF_COOKIE_SECURE`. Risco de segurança em produção HTTPS. | Replicar (nome incorreto) | **Corrigir** para `SESSION_COOKIE_SECURE` (e avaliar `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`) |
| P2 | `backend/settings/email.py` vazio (0 bytes). | Sem `EMAIL_BACKEND`/`EMAIL_HOST`: Django usa SMTP em `localhost:25`; e-mails de recuperação de senha falham/ficam sem entrega em ambientes sem SMTP local; não há `DEFAULT_FROM_EMAIL`. | Replicar (arquivo vazio) | **Corrigir**: configurar por `decouple` (`EMAIL_HOST`, `EMAIL_PORT`, credenciais, `DEFAULT_FROM_EMAIL`) e usar `console` em DEV |
| P3 | `DATABASES` = `DATABASE_URL_DEV` se `DEBUG` senão `DATABASE_URL_PRD`; em `DEBUG` fora do contêiner força `HOST="localhost"`, `PORT=5433` (int) e imprime 3 linhas. | Prints a cada import de settings (poluem saída de comandos/testes); porta fixa 5433 ignora a da URL; mesmas verificações em `zasyncs.py` (Redis) e `solr.py`. | Replicar | Parametrizar host/porta por variáveis (`DB_HOST_LOCAL`/`DB_PORT_LOCAL`) e usar `logging` em vez de `print` |
| P4 | `ALLOWED_HOSTS = ["*"]`; `CSRF_TRUSTED_ORIGINS = [SITE_URL]` com `SITE_URL` padrão `http://192.168.15.9:9001` (IP de rede local específico). | Aceita qualquer `Host` (risco de host header injection/cache poisoning); padrão de `SITE_URL` não serve para outras máquinas. | Replicar | **Corrigir** em derivações: `ALLOWED_HOSTS` por variável; `SITE_URL` sem padrão em produção |
| P5 | O Dockerfile/Compose não faz parte desta feature, mas `SECRET_KEY` não tem padrão e `fake.py` herda `project.py` | `collectstatic` com `settings.fake` ainda exige `SECRET_KEY` e `DATABASE_URL_PRD` (ou `DEBUG`+DEV) definidos no ambiente de build | Replicar | Dar valores dummy no build ou separar `fake.py` de `project.py` |
| P6 | `DEBUG_TOOLBAR_ACTIVE`: só ativa com `DEBUG`; o comentário diz que não funciona no contêiner dev (precisa de `runserver` no host); `INTERNAL_IPS = ("127.0.0.1",)`. Em `urls.py` a rota `__debug__/` só existe se `DEBUG and DEBUG_TOOLBAR_ACTIVE`. | Dev em contêiner não tem toolbar | Replicar | Ajustar `INTERNAL_IPS` dinamicamente para contêiner |
| P7 | `backend/tests.py` e `_tests/test_initials.py`: **mesmo** teste duplicado (`test_app_init_files_have_default_app_config`). Itera subdiretórios da **raiz** (`Path(".")`, sem `_`/`.`) e só valida os que satisfazem `f"backend.{app_name}" in INSTALLED_APPS` — nenhum diretório da raiz (`backend`, `drfautoapi`, `logs`, `solr`...) satisfaz (`backend.backend` etc. não existem). A intenção parecia ser iterar `backend/`. | O teste passa sempre sem verificar nada (falsa sensação de cobertura); ainda quebraria se algum app fosse validado: `backend.utils` tem `default_app_config` correto, `backend.globalrules` aponta `backend.globalrules.apps.AppConfig`, `backend.eauth` e `backend.api` têm o seu; `backend.crud` está errado (P8). | Replicar (inclusive a duplicata) | Mover para `backend/` iterando `Path("backend")`, remover duplicata e remover a regra obsoleta `default_app_config` (ignorada desde Django 4.1/removida no 5.1) |
| P8 | `backend/crud/__init__.py`: `default_app_config = 'backend.utils.apps.CrudConfig'` — classe inexistente (`backend/utils/apps.py` só tem `UtilsConfig`); `backend.crud` **não** está em `INSTALLED_APPS` (é biblioteca de views/CRUD, feature 004). | Sem efeito em runtime (o Django ≥ 4.1 ignora `default_app_config`, e `crud` não é app instalado); causaria falha se o teste P7 fosse corrigido e `crud` fosse instalado | Replicar | Corrigir/remover (e decidir se `crud` deve ser app) |
| P9 | `backend/settings/logs.py`: caminho relativo `logs/backend_logger.log`; `logs/` não é versionada (`*.log` ignorado) e nada a cria fora do Docker (`mkdir -p ${HOME}/logs/celery`). | Em clone novo, qualquer `manage.py`/`pytest` falha com `FileNotFoundError` até criar `logs/`; o caminho depende do diretório de trabalho (Celery/Gunicorn rodam a partir da raiz). | Replicar, mas **criar a pasta `logs/`** na reconstrução (tarefa) | Usar `PROJECT_DIR / "logs"` e `mkdir(exist_ok=True)` em `logs.py` |
| P10 | `MyFormatter.format` varre `inspect.stack()` buscando qualquer local chamado `request` (e `except:` genérico ao ler `r.path`). | Custo O(profundidade da pilha) por linha de log; pode anexar o caminho errado ou objetos que não são requisições (um `request` de `requests`/DRF Request tem `.path`; senão cai em `""`) | Replicar | Usar `contextvars` + middleware ou filtro de log |
| P11 | `logs.py`: `yaml.warnings({"YAMLLoadWarning": False})` — resquício do PyYAML < 5.1 (a chamada existe mas é inócua); `logging.captureWarnings(True)` global. | Nenhum efeito prático; importar `yaml` só para isso | Replicar | Remover |
| P12 | `sys.excepthook` global sobrescrito em `logs.py` (import time) e `print` da pilha. | Duplica saída (log+console); sobrescreve hooks de outras bibliotecas | Replicar | Tratar em `LOGGING`/servidor |
| P13 | `backend/model_mixins.py::SaveModelWithFileMixin.save` usa `super().save(force_insert, force_update, using, update_fields)` posicional; Django 6 torna `Model.save` keyword-only. Parâmetro `clean` não é usado. Nenhum modelo do projeto usa o mixin. | `TypeError` ao salvar objeto novo com o mixin | Replicar (código morto) | Corrigir para argumentos nomeados; remover `clean` |
| P14 | `SearchModelMixin.save`: assinatura própria com `auto_update_search`; campos aninhados (`a__b`) não têm `try/except` (levantam `AttributeError`/`ObjectDoesNotExist`), tuplas e simples engolem erros silenciosamente; `fields_search` mutável de classe. | Comportamentos divergentes entre formas de declaração | Replicar | Uniformizar tratamento de erros |
| P15 | `CleanModelMixin.clean` só valida `unique_together` com nulos (ignora `UniqueConstraint`); `unique_error_message` recebe só os campos não nulos. Mixin sem uso no projeto. | Cobertura parcial | Replicar | Cobrir `UniqueConstraint(nulls_distinct=...)` (Django nativo) |
| P16 | `AuditoriaModelMixin` usa `PROTECT` e `related_name="+"`; não preenche `created_by/modified_by` automaticamente (o preenchimento é da feature 002). | — | Replicar | — |
| P17 | `utilss.py`: `get_mime_type_from_file_extension` sem normalização de caixa e com `TODO` (python-magic já está nas dependências); `decimal2str` repassa `DECIMAL_PLACES[decimal_places]` (um `Decimal`) para `quantize`, engolindo `KeyError` para casas ≥ 10 (retorna `str(value)`); `run_sql` devolve o cursor/`None` se `fetchall` falhar; `clean_text` usa `except:` e `while re.search` (risco teórico de laço infinito se a substituição reproduzir o padrão); `hash_sha512` não fecha arquivos recebidos como objeto (comportamento intencional). | Armadilhas conhecidas | Replicar | Cobrir com testes; usar `python-magic`/`mimetypes` |
| P18 | `common_tags.py`: 29 `E722` (bare `except`) e funções que quebram com entradas inesperadas (`to_dict`, `url`, `component_frontend`, `settings_key_*`, `is_video_url`...); `url`/`audio_url` exigem `str`; `lookup` devolve `[]` se a chave não existir; `valor_abs_str` exige `Decimal` (`copy_abs`); `search_value` usa `getattr(request, request.method)` (só funciona para GET/POST); filtro `age` tem tratamento de plural por concatenação ("mes"+"es"). | Erros de template em dados inválidos | Replicar | Endurecer entradas e adicionar testes |
| P19 | `ruff check .` retorna 119 achados (por regra: E722 29, E501 29, F401 29, F841 11, E741 4, F541 4, F405 4, F811 3, I001 3, E713 2, F403 1). A constituição exige ruff limpo no PR, mas o legado não está limpo. | Gate de PR do princípio VIII não é satisfeito por todo o repositório | Replicar (estado atual) | Corrigir gradualmente (`ruff check --fix`) |
| P20 | `pyproject.toml` mantém `black` e `isort` no grupo `dev`, mas a formatação/organização usa `ruff` (`.vscode/settings.json` usa `charliermarsh.ruff`). | Dependências redundantes | Replicar | Remover `black`/`isort` |
| P21 | `.github/dependabot.yml`: a chave `updates:` aparece seis vezes no mesmo mapeamento YAML (chave duplicada). Dependendo do parser, só o último bloco (`pip`) vale, ou o arquivo é rejeitado. | Atualizações semanais de npm/docker/docker-compose possivelmente inativas | Replicar | **Corrigir**: lista única sob `updates:` |
| P22 | `__notebooks/django_setup.py` assume que a pasta do repositório se chama `sdd-start` e fica em `parents[2]/sdd-start` (adiciona ao `sys.path`). | Quebra se o diretório for renomeado/clonado com outro nome | Replicar | Usar `parents[1]` (raiz real) |
| P23 | O `.gitignore` não ignora `collectedstatic/` (`STATIC_ROOT`) nem `logs/` como pasta; ignora `.vscode/` e `security.json` (segredo do Solr). Há `backend/db.sqlite3` local ignorado por `db.sqlite3`. | `collectedstatic/` poderia ser versionado por engano | Replicar | Acrescentar `collectedstatic/` e `logs/` |
| P24 | A constituição afirma "CORS aberto", porém o código não tem `corsheaders` nem configuração de CORS (frontend é servido pelo próprio Django/Vite via `django-vite`). | Imprecisão documental | Replicar (sem CORS) | Ajustar a constituição |
| P25 | A constituição lista `crud` como app em `BACKEND_APPS`; no código `BACKEND_APPS = ["backend.eauth", "backend.utils"]` e `crud` não é app instalado. | Imprecisão documental | Replicar | Ajustar a constituição |
| P26 | `backend/settings/project.py`: `BASE_DIR = BASE_DIR` (atribuição redundante); `PROJECT_VERSION="0.0.1"` diverge de `pyproject.toml` (`0.1.0`). | Cosmético | Replicar | Unificar versão |
| P27 | `backend/utils/templatetags/` sem `__init__.py`; `backend/utils/fixtures/` vazio. | Pacote de namespace; Django ainda descobre `common_tags` (verificado: `python manage.py check` passa) | Replicar | Adicionar `__init__.py` |
| P28 | `asgi.py` importa `backend.utils.routing` antes de `django.setup()`; funciona porque `routing`/`consumers` só importam modelos/regras dentro de funções (e `import backend` já executa `os.environ.setdefault` em `celery.py`). | Frágil a mudanças | Replicar | Importar após `django.setup()` |
| P29 | `Metadata.__str__` usa `content_object` (pode disparar consulta por registro); `object_id` é `PositiveIntegerField` (não suporta PKs não inteiros/UUID/`BigAutoField` acima de 2³¹−1). | Limite funcional | Replicar | Usar `PositiveBigIntegerField` ou `CharField` |
| P30 | `SESSIONS_COOKIE_SECURE`, `ALLOWED_HOSTS`, `SITE_URL` e ausência de e-mail (P1, P2, P4) somam-se a `LOGIN_URL = "/login/?next="` (feature 002) | — | — | — |

**Estado de verificação (2026-11-08)**: `python manage.py check` → "no issues"; `makemigrations --check --dry-run` → "No changes detected"; `pytest --no-cov` → 3 passed.
