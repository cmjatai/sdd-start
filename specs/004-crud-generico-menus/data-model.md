# Modelo de Dados: CRUD Genérico, Layouts YAML, Menus e Templates Base

**Não há tabelas, modelos nem migrações novas nesta funcionalidade.** O CRUD opera sobre modelos de outras features; a única entidade usada na demonstração é `Teste` (definida em `backend/utils/models.py`, migração `backend/utils/migrations/0001_initial.py`, coberta em `001`). Abaixo, as estruturas de dados relevantes (modelo de demonstração, configuração, YAML, contexto).

## 1. Modelo de demonstração `Teste` (`backend/utils/models.py`)

| Campo | Tipo | Opções |
|-------|------|--------|
| `id` | `BigAutoField` (`default_auto_field`) | PK |
| `teste` | `CharField` | `max_length=100`, `verbose_name=_("Teste")` |

`Meta`: `verbose_name = _("Teste")`, `verbose_name_plural = _("Testes's")`, `ordering = ("teste",)`. `__str__` devolve `teste`. Permissões: as padrão do Django + `list_teste` (criada por `globalrules`, `003`). O modelo **não** herda `SearchModelMixin`, por isso `TesteCrud` não habilita busca.

## 2. Requisitos do modelo para recursos opcionais do CRUD

| Recurso | Requisito no modelo |
|---------|---------------------|
| Busca `q` (`ListWithSearchForm`) | herdar `SearchModelMixin` (`backend/model_mixins.py`): campo `search = TextField(blank=True, default="")`, `fields_search = []` (nomes ou tuplas, `a__b`), `save()` recompõe `search` concatenando os campos e aplicando `normalize` (NFKD → ASCII) |
| Auditoria automática | campos `created_by` / `modified_by` (`AuditoriaModelMixin`); a criação tenta preenchê-los (a edição tenta o atributo `modifier`, que não é campo) |
| Contêiner | caminho `container_field` (`campo__subcampo`) terminando no usuário |
| Mestre-detalhe | `parent_field` (FK ou M2M) e opcionalmente `model_set` (nome do related manager) |
| Ordenação | `Meta.ordering` é anexado ao final de qualquer ordenação por `o` |

## 3. Estruturas de configuração do `Crud`

```text
Crud
├─ model, model_set, help_topic, frontend, container_css_class
├─ public: list[str]                   # subconjunto de {".list_", ".view_", ".add_", ".change_", ".delete_"}
├─ container_field, container_field_set, is_m2m, parent_field, namespace
├─ BaseMixin  (CrudBaseMixin)          # atributos comuns às views: list_field_names, ordered_list, ganchos
├─ ListView   (CrudListView)           # form_search_class, paginate_by, no_entries_msg, ganchos hook_*
├─ CreateView (CrudCreateView)         # form_class, layout_key
├─ DetailView (CrudDetailView)         # layout_key, ganchos hook_*, extras_url
├─ UpdateView (CrudUpdateView)
└─ DeleteView (CrudDeleteView)
```

Constantes: `ACTION_LIST="list"`, `ACTION_CREATE="create"`, `ACTION_VIEW="view"`, `ACTION_UPDATE="update"`, `ACTION_DELETE="delete"`; `RP_LIST=".list_"`, `RP_VIEW=".view_"`, `RP_ADD=".add_"`, `RP_CHANGE=".change_"`, `RP_DELETE=".delete_"`.

## 4. Estrutura do layout após leitura (`read_layout_from_yaml`)

| Versão | Python |
|--------|--------|
| 1 | `[[legenda, [(campo, largura), ...], ...], ...]` |
| 2 | `([[classe_coluna, [legenda, [classe_col_interna, [(campo, largura), ...], ...], ...], ...], ...], 2)` |
| erro | `[]` |

`layout_display` converte em dicionários: v1 `[{"legend", "rows": [[{"id","span","verbose_name","text"}]]}]`; v2 `[{"version": 2, "colgroups": [{"class_col", "colfieldsets": [{"legend","class_col","rows"}]}]}]`.

## 5. Estrutura dos itens de menu

```text
item = {
  title: str, url: str, children: [item], check_permission: str,
  css_class_li|a|span|ul|icon: str, urls_extras: [str],
  active: "active" | ""        # preenchido por resolve_urls_inplace
}
```

## 6. Dados de interface sem persistência

| Dado | Onde | Observação |
|------|------|-----------|
| Cookie `backend_page_size` | navegador → `CrudListView.get` | valor padrão `"10"` |
| Cookie `sddstart_page_size` | JS de `crud/list.html` | gravado, mas não lido |
| Mensagens `django.contrib.messages` | sessão/cookie | exibidas em `base.html` |
| Tema (`data-bs-theme`) | atributo HTML + script do frontend | `light`/`dark`/`auto` |

## 7. Migrações iniciais

Nenhuma (esta feature não cria modelos). A migração de `Teste` pertence a `utils` (`0001_initial`).
