# Quickstart: Validar a Fundação do Projeto Django

**Feature**: `001-fundacao-projeto-django` | Referências: [spec.md](./spec.md), [plan.md](./plan.md), [contracts/settings-e-ambiente.md](./contracts/settings-e-ambiente.md)

## Pré-requisitos

- Python >= 3.12, Poetry (`poetry-core >=2,<3`), PostgreSQL acessível (em desenvolvimento no host: `localhost:5433`, porta publicada pelo Docker Compose da feature `010`).
- Diretório `logs/` na raiz (o handler de arquivo usa o caminho relativo `logs/backend_logger.log`).

## 1. Preparar o ambiente

```bash
mkdir -p logs
poetry install --with dev,test        # package-mode = false: instala apenas dependências
```

Criar `backend/.env` (não versionado; valores de exemplo do repositório):

```ini
DEBUG=True
SECRET_KEY=<valor-local>
DATABASE_URL_DEV=postgresql://startdev1:startdev1@localhost:5433/startdev1
```

## 2. Verificações básicas

```bash
python manage.py check                              # "System check identified no issues"
python manage.py makemigrations --check --dry-run   # "No changes detected"
python manage.py migrate                            # aplica utils.0001_initial (utils_teste, utils_metadata)
python -c "import backend; print(backend.celery_app)"
```

Comportamentos esperados:

| Cenário | Como verificar | Esperado |
|---------|----------------|----------|
| Origem do banco por `DEBUG` | `DEBUG=False python manage.py check` sem `DATABASE_URL_PRD` | erro `UndefinedValueError` do decouple |
| `SECRET_KEY` ausente | remover do `.env` e rodar `manage.py check` | erro `UndefinedValueError` |
| Debug fora do contêiner | `DEBUG=True` e `FOLDER_DEBUG_CONTAINER` não definido | três mensagens no console; banco em `localhost:5433` |
| Fuso/idioma | `python manage.py shell -c "from django.conf import settings as s; print(s.LANGUAGE_CODE, s.TIME_ZONE)"` | `pt-br America/Sao_Paulo` |
| Settings `fake` | `DJANGO_SETTINGS_MODULE=backend.settings.fake python manage.py check` | usa SQLite `db.sqlite3` e `DEBUG=False` |

## 3. Servidor, rotas e admin

```bash
python manage.py runserver 0.0.0.0:8000
```

- `GET /system/` → login da administração do Django.
- `GET /` → página `index.html` (rota `index`; a renderização completa depende do frontend, feature `007`).
- Com `DEBUG_TOOLBAR_ACTIVE=True` (só no host, com `DEBUG=True`): `/__debug__/` registrado.
- Em `/system/` (superusuário criado com `python manage.py createsuperuser`): modelos `Teste` e `Metadado(s)` listados.

## 4. Logs

```bash
python manage.py shell -c "import logging; logging.getLogger('backend').error('x')"
tail -n 2 logs/backend_logger.log     # linha 'ERROR ... backend:...:... x'
```

Com `DEBUG=True` a mesma linha aparece também no console; com `DEBUG=False`, apenas no arquivo.

## 5. Utilitários, mixins e `Metadata` (shell)

```bash
python manage.py shell
```

```python
from decimal import Decimal
from backend.utilss import decimal2str, normalize, get_mime_type_from_file_extension, DisableSignals
decimal2str(Decimal("1234.565"))                 # '1.234,56'
decimal2str("abc")                               # 'abc' (erro registrado)
normalize("Ação ç")                              # 'Acao c'
get_mime_type_from_file_extension("a.odt")       # 'application/vnd.oasis.opendocument.text'

from backend.utils.models import Teste, Metadata
t = Teste.objects.create(teste="x")
Metadata.objects.get_metadata(t)                          # None
Metadata.objects.set_or_update_metadata(t, {"a": 1})      # cria
Metadata.objects.set_or_update_metadata(t, {"b": 2}).metadata   # {'a': 1, 'b': 2}
str(t)                                                    # 'x'
```

Template tags (shell ou template de teste):

```python
from django.template import Template, Context
Template("{% load common_tags %}{{ v|decimal2str }}|{{ s|startswith:'ab' }}").render(Context({"v": Decimal('10'), "s": "abc"}))
# '10,00|True'
```

## 6. Testes e qualidade

```bash
pytest                       # coleta **/tests.py e **/test_*.py, --reuse-db, cobertura
pytest _tests/test_initials.py backend/tests.py -q
ruff check .                 # achados legados esperados (ver research.md)
ruff check backend/utilss.py backend/model_mixins.py backend/utils backend/settings
```

Esperado: 3 testes coletados no estado de referência (dois `test_app_init_files_have_default_app_config`, que passam sempre, e `backend/crud/tests.py::test_read_layout_from_yaml` da feature `004`); relatório de cobertura ao final; fixture `app` autenticada como `admin_user`.

Testes que esta feature deveria cobrir (tarefas em `tasks.md`): `decimal2str`/`quantize`, `normalize`, `get_mime_type_from_file_extension`, `clean_text`, `intervalos_tem_intersecao`, `hash_sha512`, `DisableSignals`, `SearchModelMixin`, `CleanModelMixin`, `Metadata.objects.*`, filtros `common_tags` e leitura de settings por ambiente.

## 7. Notebooks e repositório

- `git status` não deve listar `.env`, `*.log`, `db.sqlite3`, `node_modules/` (cobertos pelo `.gitignore`).
- `python manage.py shell_plus --notebook` (usa `NOTEBOOK_ARGUMENTS` com `DEBUG=True`) ou abrir `__notebooks/0init_file.ipynb`: a primeira célula (`import django_setup`) executa `django.setup()`.
- `.editorconfig` e `.prettierrc.json` presentes; `.github/dependabot.yml` válido para ao menos o bloco `pip` semanal.
