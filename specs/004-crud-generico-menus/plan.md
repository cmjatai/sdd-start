# Plano de Implementação: CRUD Genérico, Layouts YAML, Menus e Templates Base

**Branch**: `004-crud-generico-menus` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/004-crud-generico-menus/spec.md`

**Nota**: Documento de engenharia reversa; descreve o código que já existe e serve de roteiro de reconstrução.

## Resumo

Biblioteca interna `backend/crud/` que gera, a partir de uma classe declarativa `Crud` com `model`, as cinco views de CRUD (lista, criar, detalhe, editar, excluir) com permissões por modelo, rotas públicas opcionais, restrição por "contêiner" (dono), busca/ordenação/paginação, formulários e detalhes dirigidos por layouts YAML, mais um sistema de menus YAML (`backend/utils/templatetags/menus.py`) e o conjunto de templates Django em `_templates/` (página-base com montagem do Vue, `crud/*`, `menus/*`, paginação, 404 e índice). `TesteCrud` em `backend/utils/` demonstra o uso em `/teste/`. Abordagem técnica: *class-based views* do Django 6 compostas dinamicamente (`type` via `class CrudViewWithBase(BaseMixin, View)`), `django-crispy-forms` (pack `bootstrap5`), `django-braces` (`FormMessagesMixin`), `PyYAML` e `Markdown`.

## Contexto Técnico

**Linguagem/Versão**: Python >= 3.12 (`requires-python = ">=3.12,<4.0"`; ambiente local 3.12), Django 6.0.x (`django >=6,<7`)

**Dependências Principais**: `django-crispy-forms` + `crispy-bootstrap5` (`CRISPY_TEMPLATE_PACK = "bootstrap5"`), `django-braces ^1.17` (`FormMessagesMixin`), `pyyaml ^6.0`, `markdown ^3.11`, `django-vite ^3.2` (tags em `base.html`), Bootstrap 5 + Vue 3 (via Vite, feature `007`)

**Armazenamento**: PostgreSQL (herdado de `001`); nenhuma tabela nova (usa o modelo `Teste` de `001`)

**Testes**: `pytest` + `pytest-django` (`DJANGO_SETTINGS_MODULE = "backend.settings"`, `--reuse-db`); teste existente `backend/crud/tests.py::test_read_layout_from_yaml`; `django-webtest` com fixture `app` em `conftest.py`

**Plataforma Alvo**: servidor Linux (Docker, ver `010`/`011`)

**Tipo de Projeto**: aplicação web Django (biblioteca interna + templates)

**Metas de Desempenho**: não há metas formais; paginação padrão de 10 itens (opções 10/25/50/100)

**Restrições**: o pacote `backend.crud` não está em `INSTALLED_APPS` (templates vêm de `TEMPLATES["DIRS"] = [PROJECT_DIR / "_templates"]`, definido em `backend/settings/frontend.py`); os menus YAML são renderizados a cada requisição (sem cache)

**Escala/Escopo**: ~2.300 linhas Python em `backend/crud/`, 1 templatetag (`menus.py`), ~20 templates/YAML

## Verificação da Constituição

*PORTÃO (gate): passou antes da pesquisa; reverificado após o design.*

| Princípio | Avaliação | Observação |
|-----------|-----------|------------|
| I. Backend modular por apps | Atendido com ressalva | `backend/crud/` tem `apps.py` (`CrudConfig`, `label = "crud"`), mas **não** está em `BACKEND_APPS`/`INSTALLED_APPS`; funciona como biblioteca. Registrado em `research.md` (recomendação: manter ou registrar). Constituição cita `crud` como app; sem violação funcional. |
| II. Configuração por ambiente | Atendido | Nenhuma configuração nova; usa `TEMPLATES`/`CRISPY_*` já existentes. Nenhum segredo. |
| III. Paridade dev/prod via Docker | Atendido | Templates são copiados/montados como o restante do código; nada específico de ambiente além de `DEBUG` em `base.html` (manifest só se `not DEBUG`). |
| IV. API REST gerada, permissões por modelo | Atendido | Usa as permissões `<app>.<verbo>_<modelo>` (incl. `list_`) de `003`; o detalhe aponta para `/api/<app>/<modelo>/<id>`. |
| V. Frontend Vite integrado ao Django | Atendido | `base.html` usa `django-vite` (`vite_hmr_client`, `vite_asset 'main.js'`) e o componente raiz `<emf-app>` (prefixo `emf-`). |
| VI. Tempo real e tarefas assíncronas | Não aplicável | Sem tempo real/Celery nesta feature (ver `006`). |
| VII. Português do Brasil | Atendido | Textos com `gettext_lazy`/`{% trans %}`; docs em pt-BR. Alguns comentários internos em inglês no código-fonte (docstring de `make_pagination`) — aceitável. |
| VIII. Qualidade verificável | Atendido parcialmente | Existe 1 teste unitário (layout). Cobertura de views/menus é lacuna; `tasks.md` inclui testes a criar. `ruff` aplicável (`E`, `F`, `I`). |

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/004-crud-generico-menus/
├── plan.md              # Este arquivo
├── research.md          # Decisões e dívidas técnicas
├── data-model.md        # Estruturas de dados (sem tabelas novas)
├── quickstart.md        # Validação
├── contracts/
│   ├── crud-http.md     # Rotas, permissões, parâmetros e respostas do CRUD
│   ├── layouts-yaml.md  # Formato dos layouts (v1/v2)
│   ├── menus-yaml.md    # Formato dos menus e tags
│   └── templates.md     # Blocos e variáveis dos templates
└── tasks.md             # Roteiro de tarefas
```

### Código-Fonte (raiz do repositório)

```text
backend/
├── crud/
│   ├── __init__.py                # default_app_config residual (incorreto)
│   ├── apps.py                    # CrudConfig (name=backend.crud, label=crud)
│   ├── base.py                    # Crud, views, mixins, make_pagination, FORM_MESSAGES
│   ├── crispy_layout_mixin.py     # layout YAML, helpers crispy, get_field_display
│   ├── forms.py                   # ListWithSearchForm
│   └── tests.py                   # test_read_layout_from_yaml
├── utils/
│   ├── templatetags/
│   │   ├── menus.py               # menu, subnav, navbar, nav_run, resolve_urls_inplace
│   │   └── common_tags.py         # container_css_class, view_class_name, avatar_user, url, str2intabs ... (usadas pelos templates)
│   ├── views.py                   # TesteCrud
│   └── urls.py                    # re_path(r"^teste/", include(TesteCrud.get_urls()))
_templates/
├── base.html
├── index.html
├── 404.html
├── paginacao.html
├── crud/
│   ├── list.html  list_tabaux.html  form.html  ajax_form.html  confirm_delete.html
│   ├── detail.html  detail_detail.html  detail_content_widget.html
│   ├── detail_column_widget.html  format_options.html
├── menus/
│   ├── menu.html  nav.html  subnav.html
│   ├── menu_main.yaml  menu_administracao.yaml
├── utils/
│   ├── layouts.yaml  teste_list.html
└── eauth/layouts.yaml            # exemplo (UserDetail, UserCreate); detalhado em 002
```

**Decisão de Estrutura**: biblioteca Python em `backend/crud/` + templates globais em `_templates/` (e não dentro de apps), porque o `Crud` resolve `crud/<sufixo>.html` e `<app_label>/layouts.yaml` a partir do `TEMPLATES["DIRS"]` único do projeto. A templatetag fica no app `utils` (`backend/utils/templatetags/`), que está em `INSTALLED_APPS` e portanto torna a biblioteca `menus` carregável.

## Rastreamento de Complexidade

Sem violações da constituição. As dívidas técnicas (código morto, bugs, inconsistências) estão em `research.md`.

---

## Detalhamento de Implementação

### 1. Constantes e utilidades de `backend/crud/base.py`

- Imports principais: `FormMessagesMixin` (braces), `PermissionRequiredMixin`, views genéricas do Django (`CreateView, DeleteView, DetailView, ListView, UpdateView`), `ContextMixin`, `MultipleObjectMixin`, `classonlymethod`, `format_lazy`, `re_path`, `reverse`, `Http404`, `redirect`, `messages`; `from backend.globalrules import RP_ADD, RP_CHANGE, RP_DELETE, RP_LIST, RP_VIEW` (valores `'.add_'`, `'.change_'`, `'.delete_'`, `'.list_'`, `'.view_'`); `from backend.utilss import normalize`; `from .crispy_layout_mixin import CrispyLayoutFormMixin, get_field_display`.
- `logger = logging.getLogger(settings.BASE_DIR.name)`.
- `ACTION_LIST, ACTION_CREATE, ACTION_VIEW, ACTION_UPDATE, ACTION_DELETE = "list","create","view","update","delete"`.
- `_form_invalid_message(msg)` → `"%s %s" % (_("Formulário inválido."), msg)`.
- `FORM_MESSAGES` (dict por ação → `(msg_sucesso, msg_erro)`), reescrito após a criação para prefixar apenas a mensagem de erro:
  - `create`: ("Registro criado com sucesso!", "O registro não foi criado.")
  - `update`: ("Registro alterado com sucesso!", "Suas alterações não foram salvas.")
  - `delete`: ("Registro excluído com sucesso!", "O registro não foi excluído.")
- `from_to(start, end)` → `list(range(start, end+1))`.
- `make_pagination(index, num_pages)` (`PAGINATION_LENGTH = 10`):
  1. `num_pages <= 10` → `from_to(1, num_pages)`.
  2. senão, se `index - 1 <= 5`: `tail=[n-1, n]`, `head=from_to(1, 7)`.
  3. senão, se `index + 1 >= n - 3`: `tail=from_to(index-1, n)`; senão `tail=[index-1, index, index+1, None, n-1, n]`; `head=from_to(1, 10 - len(tail) - 1)`.
  4. devolve `head + [None] + tail`. Exemplos: `(1,30)→[1..7,None,29,30]`, `(15,30)→[1,2,3,None,14,15,16,None,29,30]`, `(27,30)→[1,2,3,4,None,26,27,28,29,30]`.
- Comentário-docstring com a lista de "variáveis do crud": `help_topic, container_field, container_field_set, is_m2m, model, model_set, form_search_class, list_field_names, list_field_names_set, permission_required (vazio = público), layout_key_set, layout_key, ordered_list, parent_field, namespace, return_parent_field_url`.

### 2. Mixins de permissão (`base.py`)

- `PermissionRequiredForAppCrudMixin(PermissionRequiredMixin)`: `has_permission()` itera `self.app_label` (str → tupla) exigindo `user.has_module_perms(app)` para cada app. Não usado.
- `PermissionRequiredContainerCrudMixin(PermissionRequiredMixin)`:
  - `has_permission()`: `perms = self.get_permission_required()`; vazio → `True`; devolve `True` se `user.has_perm(p)` para **algum** `p`; senão `False`.
  - `dispatch(request, *args, **kwargs)`: se `not has_permission()` → `handle_no_permission()`. Se há `pk` em `kwargs` e `self.container_field`: `params = {"pk": pk, container_field: request.user.pk}`; `not model.objects.filter(**params).exists()` → `Http404`. Se não há `pk` e `container_field`: divide por `__`; se `len > 1`, `container_model = getattr(model, container[0]).field.related_model`, `params = {"__".join(container[1:]): user.pk}`; se não existir → `messages.error(request, "O Usuário (%s) não está registrado como (%s).")` e `redirect("/")`. Termina com `super(PermissionRequiredMixin, self).dispatch(...)` (pula o dispatch do `PermissionRequiredMixin`, evitando verificar duas vezes e usando "algum de").
  - Propriedades `container_field` e `container_field_set`: leem de `self.crud` (criando o atributo `""` se não existir); `is_contained` = `container_field_set or container_field`.

### 3. `CrudBaseMixin(CrispyLayoutFormMixin)` (`base.py`)

- `__init__(**kwargs)`: chama `super().__init__`; `obj = self.crud if hasattr(self,"crud") else self`; define `self.app_label = obj.model._meta.app_label`, `self.model_name = obj.model._meta.model_name`; se `obj.model_set`: `app_label_set`/`model_name_set` = do modelo do *related field* `getattr(obj.model, obj.model_set).field.model`; `obj.public = []` se ausente; se `self.permission_required` não vazio → `self.permission_required = tuple(self.permission(pr) for pr in set(permission_required) - set(obj.public))`.
- `permission(rad)`: `app_label + rad + model_name` se `rad` termina com `_`; senão devolve `rad` (ex.: `".list_"` → `"utils.list_teste"`). `permission_set` análoga com `app_label_set/model_name_set`.
- `url_name(suffix)` (classmethod): `"<model_name>_<suffix>"`; `url_name_set` idem para `model_set`.
- `resolve_url(suffix, args=None)`: `reverse(f"{model._meta.app_config.name}:{url_name(suffix)}", args=args)` (namespace = `backend.utils`, nome do app Django com ponto). `resolve_url_set` análoga.
- `ordered_list` → propriedade que devolve `True` (precede o atributo da view na MRO).
- `list_url/create_url/detail_url/update_url/delete_url`: `""` se a view do CRUD é `None`; se a view não tem `permission_required` → URL sempre; senão URL se `user.has_perm(self.permission(RP_X))`. `detail_url/update_url/delete_url` usam `self.object.id`.
- `openapi_url`: `f"/api/{o._meta.app_label}/{o._meta.model_name}/{o.id}"` (sem barra final).
- `get_template_names()`: `super()` (nomes padrão do Django, ex.: `utils/teste_list.html`) + `"crud/%s.html" % template_name_suffix.lstrip("_")` (`list`, `form`, `detail`, `confirm_delete`).
- `verbose_name`, `verbose_name_plural` do modelo; `verbose_name_set` do modelo relacionado.

### 4. Views genéricas (`base.py`)

Todas herdam `PermissionRequiredContainerCrudMixin` e possuem `logger = logging.getLogger(__name__)` e classmethod `get_url_regex()`.

**`CrudListView(…, ListView)`**: `permission_required = (RP_LIST,)`, `paginate_by = 10`, `no_entries_msg = _("Nenhum registro encontrado.")`, regex `^$`.
- `get_headers()`: para cada item de `list_field_names` (str ou tupla) percorre `a__b__c` via `_meta.get_field`; rótulo = `hook_header_<a__b>()` (pode devolver `(texto, ordenavel)`) ou `verbose_name`; `ordering=False` se algum campo não resolver; junta rótulos com `" / "`.
- `_as_row(obj)`: para cada coluna `i`, URL do detalhe só em `i == 0` (acrescenta `?pkk=<pk>` se `crud.is_m2m`); para cada nome da tupla (vazio → `<br>`), navega `getattr` pelos segmentos, `get_field_display(m, ultimo)[1]`, separador `" / "` (ou `<br>` se o valor contém `<ul>`), `hook_<a__b>(obj, texto, url)` pode devolver `texto`, `(texto, url)` ou `(texto, url, css_class)`; linha = `(html, url, css_class)`.
- `get_context_data`: `form` se existir; `count = object_list.count()`; `title` padrão `verbose_name_plural`; `page_range = make_pagination(...)` se paginado; `headers`, `rows`, `NO_ENTRIES_MSG`; `filter_url = "&" + GET sem 'page'` (ou `""`); se `ordered_list`: `ordering_url` = GET sem `page` e sem `o`.
- `get(request)`: `page_size = COOKIES.get("backend_page_size", "10")`; se há `form_search_class`: `data = GET.copy()`; `data["page_size"] = GET.page_size or cookie`; `self.form = form_search_class(data)`; inválido → `messages.error(request, _("Formulário inválido. %s") % form.errors)` + `redirect(self.list_url)`; válido → `paginate_by = int(cleaned_data["page_size"])`.
- `get_queryset`: (a) se `self.form`: `normalize(str(q)).split(" ")`, `Q(search__icontains=item)` combinados com `&` (ignora vazios); (b) se `ordered_list`: `o = GET.o or "1"`, `desc = "-" if o.startswith("-")`, coluna `list_field_names[(abs(int(o)) - 1) % len]` (str → lista); para cada campo `fo` não vazio: sem `__` → `get_field(fo)`; se relacional usa `related_model._meta.ordering[0]` (sem `-`) → `fo__ordem`; `ordering += (desc+fo,)`; com `__` → `desc+fo`; ao final anexa os itens de `Meta.ordering` ainda ausentes; `queryset.order_by(*ordering)`; qualquer exceção é logada e ignorada; (c) anônimo → devolve; (d) `container_field` → `filter(**{container_field: user.pk})`.

**`CrudCreateView(…, FormMessagesMixin, CreateView)`**: `permission_required = (RP_ADD,)`, regex `^create$`, `form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_CREATE]`; `cancel_url` → `list_url` (ou `super().cancel_url` se existir); `get_success_url` → `detail_url`; contexto `title = "Adicionar <verbose_name>"`; `form_valid`: `self.object = form.instance`, tenta `created_by`/`modified_by = user`; se `container_field` com `__`: carrega o contêiner (`container_model.objects.filter(**params).first()`; ausente → `Exception("Não é permitido adicionar um registro sem estar em um Container …")`), define `setattr(object, container[0], container_data)` (para `is_m2m` grava o campo `container[1]` e, após salvar, `add` no M2M).

**`CrudDetailView(…, DetailView, MultipleObjectMixin)`**: `permission_required = (RP_VIEW,)`, `paginate_by = 10`, `no_entries_msg = "Nenhum registro Associado."`, regex `^(?P<pk>\d+)$`.
- `get`: `self.object = model.objects.get(pk=pk)` (qualquer exceção → `Http404`); se há `model_set`, `object_list = get_queryset()` (relacionados: `getattr(object, model_set).all()` filtrados por `container_field_set`); `render_to_response(get_context_data(object=…))`.
- `get_context_data`: com `model_set` usa `MultipleObjectMixin` (count, page_range, headers, rows, NO_ENTRIES_MSG); sem, `ContextMixin` + `object` + nome de contexto.
- `get_headers/_as_row` do conjunto: usam `list_field_names_set`, `get_column(...)["text"]` com fallback para `get_field_display`, link da 1ª coluna para a rota `view` do modelo relacionado (`resolve_model_set_url`).
- `model_set_verbose_name(_plural)`.

**`CrudUpdateView`**: `permission_required = (RP_CHANGE,)`, regex `^(?P<pk>\d+)/edit$`, mensagens `FORM_MESSAGES[ACTION_UPDATE]`, `cancel_url = get_success_url = detail_url`; `form_valid` tenta `self.object.modifier = user`.

**`CrudDeleteView`**: `permission_required = (RP_DELETE,)`, regex `^(?P<pk>\d+)/delete$`, mensagens `FORM_MESSAGES[ACTION_DELETE]`, `cancel_url = detail_url`, `get_success_url = list_url`; método `delete()` com tratamento de `ProtectedError` (mensagem HTML com `<ul>` dos objetos protegidos) — inalcançável no POST do Django 6.

### 5. `Crud` e `get_urls()`

```python
class Crud:
    __type__ = True
    BaseMixin = CrudBaseMixin
    ListView = CrudListView; CreateView = CrudCreateView; DetailView = CrudDetailView
    UpdateView = CrudUpdateView; DeleteView = CrudDeleteView
    container_css_class = ""; help_topic = ""; frontend = ""
    class PublicMixin: permission_required = []
```

`get_urls()` (classmethod via `classonlymethod`):
1. `_add_base(view)`: `None` → `None`; se `cls.__type__` falso devolve a própria view; `pr = set(view.permission_required)`; se há `cls.public` e `pr` → `pr -= set(cls.public)`; cria `class CrudViewWithBase(cls.BaseMixin, view)` com `permission_required = tuple(pr)`, `model = cls.model`, `help_topic`, `crud = cls`; `__name__ = f"{cls.__name__} {view.__name__}"`.
2. Se `cls.__type__`: cria `class CRUD(cls)` com `__type__ = False` e as cinco views já compostas, e define `view.crud = CRUD` em cada uma (evita recomposição quando `view.crud.get_urls()` é chamado de novo pelo menu).
3. Monta a lista `[regex, view, ação]` (regex pode ser tupla de pares `(regex, sufixo)`) e devolve `re_path(regex, view.as_view(), name=view.url_name(sufixo))`.
- `build(_model, _help_topic, _model_set=None, list_field_names=[])`: cria `ModelCrud(cls)` com `model`, `model_set`, `help_topic`, `list_field_names`, e `__name__ = "<Modelo>Crud"`.

### 6. `MasterDetailCrud` e `CrudBaseForListAndDetailExternalAppView` (biblioteca não usada)

- `MasterDetailCrud(Crud)`: `is_m2m = False`, `link_return_to_parent_field = False`, `build(model, parent_field, help_topic, _model_set=None, list_field_names=[])` define `parent_field`.
- Rotas: List `^(?P<pk>\d+)/<modelo>$` (pk = do pai), Create `^(?P<pk>\d+)/<modelo>/create$`, Update `^<modelo>/(?P<pk>\d+)/edit$`, Delete `^<modelo>/(?P<pk>\d+)/delete$`, Detail `^<modelo>/(?P<pk>\d+)$` (template `crud/detail_detail.html`).
- `BaseMixin`: `list_url/create_url` com `args=(self.kwargs["pk"],)`, sempre condicionados a `has_perm`; `detail_url/update_url` acrescentam `?pkk=`; `get_context_data` calcula `root_pk` (pelo `parent_field`, com `__`, ou `pkk`/`kwargs["pk"]`) e título `"<objeto><br><small>(<pai>)</small>"`; levanta 404 se M2M ambíguo sem `pkk`.
- `ListView.get_queryset` filtra `{parent_field: kwargs["pk"]}`; `dispatch` chama `PermissionRequiredMixin.dispatch` direto (sem checagem de contêiner).
- `CreateView.get_initial/get_form` pré-preenchem o campo-pai; `cancel_url` volta à listagem ou ao detalhe do pai.
- `DeleteView.get_success_url` volta à lista do pai (ou ao detalhe do pai se `is_m2m`).
- `DetailView` expõe `detail_list_url`, `detail_create_url`, `detail_set_create_url`, `detail_root_detail_url`, `detail_root_detail_verbose_name`.
- `CrudBaseForListAndDetailExternalAppView(MasterDetailCrud)`: `CreateView = UpdateView = DeleteView = None`; `BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin)` com `resolve_url` usando `crud.namespace`.

### 7. `backend/crud/crispy_layout_mixin.py`

- Imports: `re`, `ceil`, `markdown as md`, `yaml`, `FormActions`, `FormHelper`, `HTML, Div, Fieldset, Layout, Submit`, `template`, `models`, `reverse`, `formats`, `force_str`, `gettext_lazy`.
- Constantes: `re_start_tag = re.compile("<[^>]*>")`; `markdown_regex = re.compile(r"(.*)\[\[\[\[(.*)\]\]\]\](.*)", re.DOTALL)`.
- `to_column((nome|lista, span))` → `Div(*nomes, css_class="col-lg-<span>")` (se `span` não for int, é usado como classe CSS); `to_row(pares, css_class="row")`; `to_fieldsets(fields)` (listas `[legenda, linha, …]` → `Fieldset(legenda, *rows)`; outros itens passam).
- `form_actions(more=[Div(css_class="clearfix")], label=_("Salvar"), name="salvar", css_class="float-right", disabled=True)` → `FormActions(*more, Submit(name, label, css_class, onclick=…), css_class="justify-content-between form-actions")`; `onclick = "this.form.submit();this.disabled=true;"` quando `disabled` e o rótulo não contém "pesquisa"; senão `"return true;"` (ou `""` se `disabled is None`).
- `CustomFormHelper(FormHelper)` com `render_hidden_fields = True`.
- `CustomFormLayout(Layout)(*fields, cancel_label=_("Cancelar"), save_label=_("Salvar"), actions=None, disabled=False)`: botões = `actions` ou `form_actions(label=save_label, more=[HTML('<a href="{{ view.cancel_url }}" class="btn btn btn-secondary">Cancelar</a>')], disabled=disabled)`; `to_fieldsets(fields)` + `to_row([(buttons, 12)])`.
- `get_field_display(obj, fieldname)` → `(verbose_name, display)` (regras em FR-028; tratamento por **nome de tipo em string**: `.date`, `bool`, `ImageFieldFile`, `FieldFile`, `ManyRelatedManager|RelatedManager|GenericRelatedObjectManager`, `GenericForeignKey`, `TextField`, `DecimalField`). Se `get_field` falha, trata o nome como propriedade/método/manager via `getattr`.
- `CrispyLayoutFormMixin`:
  - `layout_key` (propriedade com setter): `_layout_key` ou `model.__name__` (respeita um `layout_key` da superclasse se `_layout_key` vazio); `layout_key_set`: nome da classe do modelo relacionado.
  - `get_layout()`: `read_layout_from_yaml(f"{model._meta.app_config.label}/layouts.yaml", layout_key)`; `get_layout_set()` análoga para o `model_set`.
  - `fields`: `None` se há `form_class`; senão todos os nomes de campo do layout.
  - `get_form(form_class=None)`: `super().get_form`; `AttributeError` → devolve `None`; se `layout_key` truthy: `form.helper = CustomFormHelper()`, `form.helper.layout = CustomFormLayout(*get_layout())`.
  - `list_field_names`: `crud.list_field_names` se existir; senão da superclasse; senão nomes de campos da 1ª legenda do layout (`get_layout()[0][1:]`). `list_field_names_set` idem com `get_layout_set()`.
  - `get_column(fieldname, span, obj=None)`: suporta `campo|funcao` (chama `getattr(self, funcao)(obj, campo)`) e `hook_<campo>(obj, verbose_name=…, field_display=…)` (fallback chamando só `(obj)`); devolve `{"id","span","verbose_name","text"}`.
  - `fk_urlize_for_detail` (link para `<app>:<modelo>_view`), `m2m_urlize_for_detail` (lista `<ul>` de links para `<app>:<modelo>_detail` — nome de rota inexistente por padrão), `markdown(obj, campo)`.
  - `layout_display`: v1 → `[{"legend", "rows": [[coluna,…],…]}]`; v2 → `[{"version": 2, "colgroups": [{"class_col", "colfieldsets": [{"legend","class_col","rows"}]}]}]`.
- `heads_and_tails(listas)` (gera `(cabeça, resto)`); `read_yaml_from_file(caminho)`: `template.loader.get_template(caminho).render()` → `yaml.full_load(str(...))`.
- `read_layout_from_yaml(arquivo, chave)`: `base = yaml[chave]`; `version = base.pop("version", 1)`; v1 → `[[legenda] + [line_to_namespans(l) for l in linhas] …]`; v2 → `([coluna, [legenda, [classe_col, linha…]…]…], 2)`; `except Exception: return []`. `line_to_namespans(linha)`: `cell.split(":")` por palavra; largura 0 se ausente; `remaining = 12 - soma`; para cada campo sem largura (em ordem) `span = ceil(remaining / restantes)`; `remaining -= span`; devolve lista de tuplas `(nome, largura)`.

### 8. `backend/crud/forms.py` — `ListWithSearchForm`

Campos: `q = CharField(required=False, label="", widget=TextInput(attrs={"type": "search"}))`; `o = CharField(required=False, label="", initial="1", widget=HiddenInput())`; `page_size = ChoiceField(choices=[("10","10"),("25","25"),("50","50"),("100","100")], initial="10", label=_("Resultados por página"), widget=Select(attrs={"class": "form-control"}), required=False)`. `__init__(*args, custom_filters=[])` insere `Field("page_size")` no início de `custom_filters`; `helper = FormHelper()` com `form_method = "GET"` e `Layout(Field("o"), FieldWithButtons(Field("q", placeholder=_("Busque por palavras, números ou códigos"), css_class="input-lg"), StrictButton(_("Filtrar"), css_class="btn-outline-primary btn-lg", type="submit"), css_class="form-filter"), Div(*custom_filters, css_class="d-inline-flex mt-3 gap-3 align-items-center"))`. Observação: `page_size` não é obrigatório, mas `int(cleaned_data["page_size"])` exige valor — por isso a view sempre injeta `data["page_size"]`.

### 9. `backend/utils/templatetags/menus.py`

- `register = template.Library()`; três `inclusion_tag(..., takes_context=True)`: `menu` → `menus/menu.html`, `subnav` → `menus/subnav.html`, `navbar` → `menus/nav.html`; todas com assinatura `(context, path=None, pk=None)` e retorno `nav_run(context, path, pk)`.
- `nav_run`: `root_pk = pk` ou `context["root_pk"]` ou `context["object"].pk`; só prossegue se `root_pk` **ou** `subnav_template_name` no contexto **ou** `path`. Calcula `rm = request.resolver_match`; `app_template = rm.app_name.rsplit(".", 1)[-1]`; `yaml_path = path` ou `context["subnav_template_name"]` ou `"<app_template>/subnav.yaml"`; `template.loader.get_template(yaml_path)` (falha → `None`, sem erro); `rendered = yaml_template.template.render(context)`; `menu = yaml.full_load(rendered)`; `resolve_urls_inplace(menu, root_pk, rm, context)`; exceção → `logger.error(_("Erro na conversão do yaml %s. App: %s. Erro: %s"))`. Retorna `{"menu": menu}` (ou `None` se não processou).
- `resolve_urls_inplace(menu, pk, rm, context)`: lista → aplica em cada item, `item["active"] = ativo`, devolve o último ativo; dict: se `"url"`: com `check_permission` e usuário sem `has_perm` → `url = ""`, `active = ""`; senão, se `":" in url` → `reverse(url, kwargs={"pk": pk})` e fallback `reverse(url)`; sem `:` → mesmo com prefixo `f"{rm.app_name}:{url}"`; falha mantém o valor; `active = "active"` se `request.path == url`; se não, percorre `context["view"].crud.get_urls()` e marca ativo se `u.name == url_name` ou `u.name in menu["urls_extras"]`. Se não há `url` mas há `check_permission` negado → `active = ""` e `del menu["children"]`. Se há `children` → `active` do item = resultado da recursão. Devolve `menu["active"]`.

### 10. Templates (resumo; detalhes em `contracts/templates.md`)

- `base.html`: `<!DOCTYPE html>`, `{% load i18n static django_vite common_tags menus %}`, `<html class="{% block html_class %}" lang="pt-br" data-bs-theme="auto">`, meta `theme-color #5B9F91`, favicon `static 'frontend/favicon.ico'`, `<link rel="manifest" href="/manifest.json">` se `not DEBUG`, `<title>Backend</title>`, `{% vite_hmr_client %}`, `{% vite_asset 'main.js' %}`, bloco `json_content`; corpo com sprite SVG oculto, `<div id="emf"><emf-app>` e blocos `root_body > header_content / main_content > (second_header, container_content > header_main, base_functions, mensagens, appvue_content, base_content, extra_content) / footer_content`; `{% block extra_js %}` após `</div>`. Tags usadas: `avatar_user`, `container_css_class`, `view_class_name`, `menu`, `subnav`.
- `crud/list.html` (estende `base.html`): `{% crispy form %}` se houver `form`; botão "Adicionar" se `view.create_url`; tabela com cabeçalhos ordenáveis; `{% include "paginacao.html" %}`; script que dá foco/seleção em `#id_q` e grava cookie `sddstart_page_size` no `change` de `#id_page_size`.
- `crud/list_tabaux.html`: variante com barra lateral do menu de administração (`perms.eauth.menu_administracao`).
- Demais templates conforme `contracts/templates.md`.

### 11. Registro no projeto

- `backend/utils/views.py`: `class TesteCrud(Crud): model = Teste; public = [RP_LIST, RP_VIEW]`.
- `backend/utils/urls.py`: `app_name = UtilsConfig.name` (`"backend.utils"`) e `re_path(r"^teste/", include(views.TesteCrud.get_urls()))`; `backend/urls.py` inclui `backend.utils.urls` na raiz.
- `_templates/utils/layouts.yaml`: chave `Teste`, legenda `{% trans 'Modelo Teste'%}`, linhas `id teste teste teste` / `teste:5 teste teste` / `teste:3 teste teste`.
- `Teste` (modelo): ver `001`/`data-model.md`.
- `backend/crud/apps.py`: `CrudConfig(AppConfig)` com `default_auto_field = 'django.db.models.BigAutoField'`, `name = 'backend.crud'`, `label = 'crud'`. `backend/crud/__init__.py`: `default_app_config = 'backend.utils.apps.CrudConfig'` (referência incorreta; replicar para fidelidade).
- Nenhuma variável de ambiente, migração ou setting nova é criada por esta feature; depende de `TEMPLATES`, `CRISPY_ALLOWED_TEMPLATE_PACKS`, `CRISPY_TEMPLATE_PACK` (módulo `backend/settings/frontend.py`) e de `django.contrib.messages` (context processor `messages`) e `django.contrib.auth.context_processors.auth` (variável `perms`).
