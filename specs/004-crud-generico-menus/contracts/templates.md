# Contrato: Templates, blocos e variáveis

Todos os templates ficam em `_templates/` (diretório registrado em `TEMPLATES[0]["DIRS"]`, `backend/settings/frontend.py`). Bibliotecas de tags usadas: `i18n`, `static`, `django_vite`, `crispy_forms_tags`, `common_tags` (`backend/utils/templatetags/common_tags.py`), `menus`.

## `base.html`

Raiz de todas as páginas.

| Elemento | Detalhe |
|----------|---------|
| `<html>` | `class="{% block html_class %}"`, `lang="pt-br"`, `data-bs-theme="auto"` |
| `<head>` | meta charset/viewport, `theme-color #5B9F91`, ícone `static 'frontend/favicon.ico'`, `<link rel="manifest" href="/manifest.json">` somente se `not DEBUG`, `<title>Backend</title>`, `{% vite_hmr_client %}`, `{% vite_asset 'main.js' %}`, `{% block json_content %}` |
| `<body class="{% block body_class %}">` | sprite SVG oculto com símbolos: `bootstrap`, `check2`, `circle-half`, `moon-stars-fill`, `sun-fill`, `svg-perfil` (**não** define `svg-emais`, embora usado) |
| Raiz do Vue | `<div id="emf"><emf-app> … </emf-app></div>` |
| Cabeçalho | `<header id="header-main" class="sticky-top">` com marca (`static '/imgs/logo_backend_42px.svg'`), botão de colapso (`#navbarNavAltMarkup`), menu de administração (`perms.menu_administracao`), menu do usuário (avatar `avatar_user user 'avatar-2'`, "Meu Perfil" → `backend.eauth:backend_user_change`, formulário POST "Sair" → `backend.eauth:logout`; anônimo → ícone para `backend.eauth:login`), menu principal `menus/menu_main.yaml` |
| `<main id="main-content" class="min-vh-100 {% view_class_name %}">` | `view_class_name` = nome da classe da view ou `main-content` |
| Rodapé | logotipo, texto "Sdd Start", seletor de tema (`data-bs-theme-value` = `light`/`dark`/`auto`), "CopyLeft © 2026 - Sdd Start" |
| Final | `{% block extra_js %}` |

### Blocos (hierarquia)

```text
html_class, json_content, body_class
root_body
├─ header_content
├─ main_content
│  ├─ second_header > sections_nav ({% subnav %})
│  └─ container_content  (<div class="{% container_css_class %}">)
│     ├─ main_container_class
│     ├─ header_main > header_left > title | header_center | header_right | header_exports
│     ├─ base_functions
│     ├─ (mensagens do Django)
│     ├─ appvue_content
│     ├─ base_content
│     └─ extra_content
└─ footer_content
extra_js
```

### Variáveis de contexto usadas

`title_icon`, `title_custom`, `title`, `view.title`, `object` (título, com `|safe|linebreaksbr`), `view.subtitle`, `bg_title`, `messages` (tag `error` → classe `alert-danger`), `perms`, `user`, `DEBUG` (via `backend.context_processors.debug`), `container_css_class`.

Tags de `common_tags` usadas: `container_css_class` (contexto → `view.crud.container_css_class` → `"container"`), `view_class_name`, `avatar_user` (inclui `eauth/user/avatar.html`), filtros `url`, `str2intabs`, `audio_url`, `is_video_url`, `youtube_url`, `youtube_id`, `facebook_url`, `component_frontend`, `file_extension`, `params_search_to_api`.

## `index.html`

Estende `base.html`; `base_content` com `<img src="{% static '/imgs/logo_backend.svg' %}" class="img-fluid">` centralizado (`col-6 offset-3 opacity-50 min-vh-80`). Servido por `TemplateView` na raiz (`name="index"`, em `backend/urls.py`).

## `404.html`

Estende `base.html`; `base_content` = `<emf-error-404></emf-error-404>` (componente Vue, feature `007`).

## `paginacao.html`

Renderiza `<nav class="nav-pagination">` somente se `is_paginated`: botões "Anterior"/"Próxima" (desabilitados nas extremidades), números de `page_range` (`None` → `...` desabilitado), links `?page=N{{filter_url}}`.

## `crud/list.html` (estende `base.html`)

| Parte | Comportamento |
|-------|---------------|
| `main_container_class` | `main-box` |
| `base_functions` | `{% crispy form %}` dentro de `div.actions.search` se `form`; blocos `actions`, `more_buttons_left`, `more_buttons`; botão "Adicionar <verbose_name>" se `view.create_url` |
| `base_content` | bloco `container_table_list`: sem `rows` → `<p>{{ NO_ENTRIES_MSG }}</p>`; senão bloco `container-info-table` ("Total de <plural>: <strong>count</strong>"), tabela `table table-striped table-borderless table-hover` |
| Cabeçalhos | `{% for name, ordering in headers %}`; se `view.ordered_list and ordering` → link `?o=[-]N{{ordering_url}}` com título "Clique para alterar a ordem da listagem" e classe `ordering asc|desc`; o sinal `-` é aplicado quando a coluna já é a atual (ou é a 1ª sem `o`) |
| Células | `{% for value, href, css_class in value_list %}`: `href` → `<a>`; senão, se `value|url` → link; senão texto (`|safe`) |
| Rodapé | `{% include "paginacao.html" %}` |
| `extra_js` | foco/seleção em `#id_q`; no `change` de `#id_page_size` grava `document.cookie = "sddstart_page_size=<valor>; path=/"` |

`crud/list_tabaux.html` estende `crud/list.html` e envolve `base_content` em `div.row.container-tabaux`, com barra lateral (`div.sidebar-tabaux`, "Menu Administração" + `{% subnav 'menus/menu_administracao.yaml' %}`) se `perms.eauth.menu_administracao`.

## `crud/form.html` / `crud/ajax_form.html`

`form.html` (estende `base.html`, `main-box`): `base_content` = `{% crispy form %}`. `ajax_form.html`: apenas `{% crispy form %}` (fragmento). Também usado fora do CRUD (`BackendUserChangeView`, `002`).

## `crud/confirm_delete.html`

`<form method="post">` + `csrf_token`; painel com "Confirma exclusão de" + `"{{ object|safe }}"?`; botão "Cancelar" (`view.cancel_url`) e botão "Confirmar" (`btn-danger`).

## `crud/detail.html` (estende `base.html`, `main-container-class "main-box crud-detail"`)

- `base_functions` > `container_actions` > `actions`: botões "Listar <plural>" (`view.list_url`), "Fazer nova pesquisa" (`view.search_url`), "Adicionar" (`view.create_url`), `view.extras_list_url` (tuplas `(href, css_class, texto)`), "Editar"/"Excluir" (`view.update_url`/`view.delete_url`, ocultos se `object.checkcheck`), `view.extras_url`.
- `base_content`: `div.container-detail` com `crud/detail_content_widget.html`; bloco `table_content` com a tabela de itens relacionados (cabeçalho `headers`, linhas `rows`; **valor só é exibido quando há `href`**) e `paginacao.html`.

`crud/detail_detail.html`: variante do mestre-detalhe (`DetailView` de `MasterDetailCrud`), com botões `detail_list_url` / `detail_create_url` e tabela que mostra o valor mesmo sem link.

`crud/detail_content_widget.html`: percorre `view.layout_display`; v1 → `<h2 class="legend">` + `div.row` de colunas; v2 → `div.row` > `colgroup.class_col` > `fieldset.class_col`; ao final, botão "OpenAPI" (`view.openapi_url`).

`crud/detail_column_widget.html`: se `column.verbose_name` ou `column.text`: `div.col-lg-{{span}}` > `div#div_id_{{id}}.form-group` com rótulo `<p class="control-label">` e valor detectado por filtros: `audio_url` → `<audio>`; `is_video_url` → `<video>`; `youtube_url` → `<iframe>` embed; `facebook_url` → `div.fb-video`; `url` → link; `component_frontend` (texto iniciado por `<emf-`) → HTML cru; senão `div.form-control-static {{id}}`.

`crud/format_options.html`: se `view.formats_impl`, botões de exportação CSV/XLSX/JSON (`{% url url_reverse %}?format=…{{ filter_url }}`) e link OpenAPI (`url_openapi`). Variáveis `url_reverse` e `url_openapi` são passadas por `{% with %}`. **Código sem efeito hoje** (`formats_impl` não existe).

## Resolução de template por view

`CrudBaseMixin.get_template_names()` = nomes padrão do Django + `crud/<sufixo>.html`:

| View | Nomes tentados (modelo `Teste`) |
|------|---------------------------------|
| List | `utils/teste_list.html` → `crud/list.html` |
| Create/Update | `utils/teste_form.html` → `crud/form.html` |
| Detail | `utils/teste_detail.html` → `crud/detail.html` |
| Delete | `utils/teste_confirm_delete.html` → `crud/confirm_delete.html` |

`_templates/utils/teste_list.html`: estende `crud/list.html`; sobrescreve `header_exports` com `{% with url_reverse='backend.utils:teste_list' url_openapi='backend.api:utils_teste-list' %}{% include "crud/format_options.html" %}{% endwith %}` (sem efeito visível).
