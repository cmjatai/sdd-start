# Modelo de Dados: Fundação do Projeto Django

**Branch**: `001-fundacao-projeto-django` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md) | **Plano**: [plan.md](./plan.md)

Esta feature cria **duas tabelas** (`utils_teste` e `utils_metadata`, app `backend.utils`, migração `0001_initial`), cinco **mixins de modelo** reutilizáveis (`backend/model_mixins.py`) e algumas estruturas de dados de configuração (ambiente, `LOGGING`). As demais tabelas do projeto pertencem a outras features.

## 1. Entidade `Teste` (`backend/utils/models.py`)

Modelo simples de ensaio (usado como exemplo pelo CRUD genérico — feature `004` — e em tarefas Celery).

| Campo | Tipo | Opções | Observações |
|-------|------|--------|-------------|
| `id` | `BigAutoField` | PK automática | `DEFAULT_AUTO_FIELD` / `UtilsConfig.default_auto_field` |
| `teste` | `CharField` | `max_length=100`, `verbose_name=_("Teste")` | obrigatório (sem `null`/`blank`/`default`) |

- `Meta`: `verbose_name=_("Teste")`, `verbose_name_plural=_("Testes's")` (grafia com apóstrofo preservada), `ordering=("teste",)`.
- `__str__` → `self.teste`.
- Sem relacionamentos, sem `unique`, sem sinais próprios. Não herda mixins.

## 2. Entidade `Metadata` (`backend/utils/models.py`)

Metadados JSON anexáveis a **qualquer** objeto por chave genérica (`ContentType` + `object_id`).

| Campo | Tipo | Opções | Observações |
|-------|------|--------|-------------|
| `id` | `BigAutoField` | PK automática | |
| `created_at` | `DateTimeField` | `auto_now_add=True`, `editable=False`, `verbose_name=_("Criado em")` | vem de `DateModelMixin` |
| `modified_at` | `DateTimeField` | `auto_now=True`, `editable=False`, `verbose_name=_("Modificado em")` | vem de `DateModelMixin` |
| `content_type` | `ForeignKey(ContentType)` | `blank=True`, `null=True`, `default=None`, `on_delete=PROTECT` | sem `verbose_name` |
| `object_id` | `PositiveIntegerField` | `blank=True`, `null=True`, `default=None` | **inteiro de 32 bits sem sinal**: não comporta PKs `BigAutoField` grandes nem UUID |
| `content_object` | `GenericForeignKey("content_type", "object_id")` | — | não gera coluna |
| `metadata` | `JSONField` | `verbose_name=_("Metadados")`, `blank=True`, `null=True`, `default=None`, `encoder=DjangoJSONEncoder` | importado de `django.db.models.fields.json` |

- Herança: `class Metadata(DateModelMixin, models.Model)`; atributo `objects = MetadataManager()` declarado **antes** dos campos.
- `Meta`: `verbose_name=_("Metadado")`, `verbose_name_plural=_("Metadados")`, `unique_together=(("content_type", "object_id"),)`, `ordering=["id"]`.
- `__str__` → `f"Metadata de {self.content_object}"`.
- Restrição de unicidade: no máximo um `Metadata` por (`content_type`, `object_id`). Com algum valor `NULL` o banco **não** rejeita duplicidade (semântica SQL); `Metadata` não usa `CleanModelMixin`.

### 2.1 Gerenciador `MetadataManager(models.Manager)`

| Método | Comportamento |
|--------|---------------|
| `get_queryset()` | `super().get_queryset().select_related("content_type")` |
| `get_metadata(content_object)` | `self.get(content_type=ContentType.objects.get_for_model(content_object), object_id=content_object.pk)`; se `DoesNotExist` devolve `None` |
| `set_or_update_metadata(content_object, metadata)` | tenta `get` pelo mesmo par; se existir: `metadata_instance.metadata` `None` → `{}`; `.metadata.update(metadata)` (**mescla** chaves de primeiro nível, sem apagar as existentes); `save()`. Se não existir (`DoesNotExist`): `create(content_type=..., object_id=content_object.pk, metadata=metadata)`. Devolve a instância |

Fluxo de estados de um registro `Metadata`: *inexistente* → (`set_or_update_metadata`) → *existente com JSON* → (`set_or_update_metadata` repetido) → *JSON mesclado, `modified_at` atualizado*. Não há remoção pelo gerenciador. A função `backend.utilss.save_in_metadata` oferece variante que **substitui** o JSON (ver `contracts/utilitarios.md`).

## 3. Migração inicial `backend/utils/migrations/0001_initial.py`

- `initial = True`; `dependencies = [("contenttypes", "0002_remove_content_type_name")]`.
- Operação 1 `CreateModel("Teste")`: `id` (`BigAutoField(auto_created, primary_key, serialize=False, verbose_name="ID")`), `teste` (`CharField(max_length=100, verbose_name="Teste")`); `options` = `verbose_name`, `verbose_name_plural`, `ordering=("teste",)`.
- Operação 2 `CreateModel("Metadata")`: `id`, `created_at` (`auto_now_add=True`, `verbose_name="Criado em"`), `modified_at` (`auto_now=True`, `verbose_name="Modificado em"`), `object_id`, `metadata` (`JSONField(blank, default=None, encoder=DjangoJSONEncoder, null, verbose_name="Metadados")`), `content_type` (`ForeignKey(blank, default=None, null, on_delete=PROTECT, to="contenttypes.contenttype")`); `options` = `verbose_name`, `verbose_name_plural`, `ordering=["id"]`, `unique_together={("content_type","object_id")}`.
- Deve ser reproduzível com `python manage.py makemigrations utils`; após criada, `makemigrations --check --dry-run` deve informar "No changes detected" (SC-001). O cabeçalho original foi gerado pelo Django 6.0.10.
- Outras migrações que dependem de `utils` pertencem a features posteriores.

## 4. Admin (`backend/utils/admin.py`)

`register_all_models_in_admin(__name__)` registra `Teste` e `Metadata` em `admin.site` com `ModelAdmin` padrão (sem `list_display` customizado). Permissões: gerenciadas pelo Django (`add/change/delete/view_<modelo>`); regras globais na feature `003`.

## 5. Mixins de modelo (`backend/model_mixins.py`)

Nenhum cria tabela por si só; os abstratos contribuem com campos aos modelos que os herdam (usados por outras features, p.ex. `SearchModelMixin`, `DateModelMixin` e `AuditoriaModelMixin` em `eauth`).

| Mixin | Abstrato? | Campos / atributos | Comportamento |
|-------|-----------|--------------------|---------------|
| `DateModelMixin` | sim | `created_at` (`DateTimeField`, `editable=False`, `auto_now_add=True`, `_("Criado em")`), `modified_at` (`DateTimeField`, `editable=False`, `auto_now=True`, `_("Modificado em")`) | — |
| `AuditoriaModelMixin` | sim | `created_by`, `modified_by`: `ForeignKey(get_settings_auth_user_model(), related_name="+", on_delete=PROTECT, verbose_name=_("Criado Por")/_("Modificado Por"))` | os campos **não** são `null`: o chamador deve preenchê-los; `related_name="+"` desabilita relação reversa |
| `SearchModelMixin` | sim | `fields_search = []` (atributo de classe, não campo); `search = TextField(blank=True, default="")` | `save(force_insert=False, force_update=False, using=None, update_fields=None, auto_update_search=True)`; recompõe `search` conforme `fields_search` (item `str` simples → `str(getattr)+" "`; `tuple` → concatenação sem separador + `" "`; `str` com `__` → navegação encadeada + `" "`), `strip()`, `normalize()` (sem acentos) e chama `super().save(...)` nomeado. Valor `search` é normalizado **mesmo** com `auto_update_search=False` |
| `CleanModelMixin` | não (mixin puro, sem campos) | — | `clean()`: `super().clean()` + verificação de `unique_together` com `NULL` (filtra `campo__isnull=True`, exclui o próprio `pk`) e levanta `ValidationError(self.unique_error_message(...))`; `save(..., clean=True)` executa `self.clean()` antes de salvar |
| `SaveModelWithFileMixin` | não (mixin puro) | `FIELDFILE_NAME = ("arquivo",)` | `save(..., clean=True)`: para objeto novo, salva primeiro sem arquivos para obter `pk`, depois restaura os arquivos e salva. **Defeito conhecido**: primeiro `super().save` com argumentos posicionais (falha no Django 6; ver `research.md`) |

Dependência de importação: `model_mixins.py` importa `get_settings_auth_user_model` e `normalize` de `backend/utilss.py`; `utils/models.py` importa `DateModelMixin`.

## 6. Estruturas de dados de configuração (sem tabelas)

### 6.1 Ambiente (`.env` / variáveis)

Lidas por `decouple.AutoConfig` (`backend/settings/zenv.py`); catálogo completo em `contracts/settings-e-ambiente.md`.

| Estrutura | Origem | Forma |
|-----------|--------|-------|
| `production` | `zenv.py` | `bool`: existe `<pai-do-repo>/backend_data/.env` |
| `DATABASES["default"]` | `project.py` | `dict` produzido por `dj_database_url.parse` (`ENGINE`, `NAME`, `USER`, `PASSWORD`, `HOST`, `PORT`, ...); `HOST="localhost"`/`PORT=5433` se `DEBUG` fora do contêiner |
| `LOGGING` | `logs.py` | `dictConfig` versão 1 (filtros, formatadores, handlers, loggers) |
| `INSTALLED_APPS`, `MIDDLEWARE` | `apps.py`, `middleware.py` | listas ordenadas (ver `plan.md` e FR-014/FR-015) |

### 6.2 Estruturas auxiliares de `utilss.py`

- `DECIMAL_PLACES`: `dict[int, Decimal]` de `0` a `9` (`Decimal(10) ** -i`).
- `YES_NO_CHOICES` / `NONE_YES_NO_CHOICES`: listas de tuplas de `choices` (`True`/`False` e `None` com rótulo `---------`).
- `dict2attr`: objeto híbrido `dict` + atributos.

## 7. Resumo de relacionamentos

```text
ContentType (django.contrib.contenttypes) 1 ──< Metadata (content_type, PROTECT, nullable)
Qualquer modelo (object_id) ····(GenericForeignKey, sem FK de banco)···> Metadata
Teste                       (isolado)
```

Não há outras tabelas, sinais de modelo ou fixtures nesta feature (`backend/utils/fixtures/` existe vazio).
