# Contrato: Menus YAML e templatetags `menus`

## Tags (`{% load menus %}`, `backend/utils/templatetags/menus.py`)

| Tag | Template de renderização | Uso típico |
|-----|--------------------------|-----------|
| `{% menu 'caminho.yaml' [pk] %}` | `menus/menu.html` | barras de navegação (`<li>` com classes CSS e ícones) |
| `{% subnav ['caminho.yaml'] [pk] %}` | `menus/subnav.html` | abas (`nav nav-tabs justify-content-end`) |
| `{% navbar ['caminho.yaml'] [pk] %}` | `menus/nav.html` | menu com dropdown e cabeçalhos |

Origem do YAML (precedência): (1) argumento `path`; (2) variável de contexto `subnav_template_name`; (3) `<último segmento de request.resolver_match.app_name>/subnav.yaml`. A tag só renderiza algo se houver `pk` (argumento, `root_pk` do contexto ou `object.pk`), `path` ou `subnav_template_name`.

Uso em `base.html`:

```django
{% if perms.menu_administracao %}<ul class="navbar-nav nav-admin">{% menu 'menus/menu_administracao.yaml' %}</ul>{% endif %}
<ul class="navbar-nav nav-main">{% menu 'menus/menu_main.yaml' %}</ul>
{% block sections_nav %}{% subnav %}{% endblock %}   {# subnav.yaml do app, se existir #}
```

## Esquema do arquivo YAML

O arquivo é renderizado como template Django (com o contexto da página: `user`, `request`, `view`, …) e deve resultar em uma **lista** de itens:

| Chave | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `title` | texto | não | texto do item (HTML permitido, `|safe`); vazio + sem `url` → separador |
| `url` | texto | não | nome de rota (`app.ns:nome` ou apenas `nome`, prefixado pelo `app_name` atual) ou caminho literal (`/`, `#`, `/teste/`); resolvido por `reverse` com `kwargs={"pk": pk}` e, se falhar, sem `kwargs`; se não reversível, mantém o literal |
| `children` | lista | não | subitens (mesmo esquema, recursivo) |
| `check_permission` | texto | não | permissão exigida (`user.has_perm(valor)`); negada → `url=""`, `active=""` e, se o item é grupo sem `url`, `children` removido |
| `css_class_li`, `css_class_a`, `css_class_span`, `css_class_ul`, `css_class_icon` | texto | não | classes aplicadas ao `<li>`, `<a>`, `<span>`, `<ul>` de filhos e `<i>` do ícone |
| `urls_extras` | lista de nomes de rota | não | rotas do `Crud` que também ativam o item |

Chaves adicionadas pela resolução: `active` (`"active"` ou `""`). Observação: valores YAML como `1.` viram número (`1.0`); use aspas para texto.

### Resolução do item ativo

1. `request.path == url resolvida` → `active`.
2. Senão, se `context["view"]` tem `crud`: percorre `view.crud.get_urls()`; `active` se `u.name == url` (nome original) ou `u.name in urls_extras`.
3. Grupos: `active` = o último filho ativo.

## Arquivos entregues

`_templates/menus/menu_main.yaml` (menu principal):

```yaml
- title: {% trans 'INÍCIO' %}
  url: '/'
- title: {% trans '1.' %}      # renderiza "1.0" (quirk)
  url: '/'
- title: {% trans '2.' %}
  url: '/'
- title: {% trans '3.' %}
  url: '/'
```

`_templates/menus/menu_administracao.yaml` (menu da engrenagem; estrutura):

```text
(item raiz) title ' ', url '#', css_class_ul: right, css_class_icon: fa-solid fa-gears, css_class_a: dropdown-toggle
├─ 'Configurações Gerais' (css_class_li head_title, icon fa-gear, url '')
│   ├─ '1. ...' url '/' (icon fa-building-columns)
│   ├─ separador (title '', url '')
│   └─ '2. ' url '/' (icon fa-gavel)
├─ 'Manutenção de Usuários' (check_permission: menu_administracao, icon fa-users-gear)
│   ├─ 'Usuários' url backend.eauth:user_list
│   └─ 'Auditoria de Acessos' url backend.eauth:pesquisar_auditlog
└─ {% if user.is_superuser %} 'Testes' (check_permission: menu_administracao)
    ├─ 'Testes' url /teste/
    └─ 'Test WS' url /wstest/
```

`check_permission: menu_administracao` usa `has_perm("menu_administracao")`, que só é verdadeiro para superusuário ativo (não existe permissão com esse nome).

## Saídas HTML

- `menu.html`: `<li class="{active} {css_class_li}">` com `<a class="{css_class_a}" href title>` + `<i class="{css_class_icon}">` + `<span class="{css_class_span}">`; com filhos, `<ul class="{css_class_ul}">` recursivo; sem `url`, usa `<span>` no lugar de `<a>`; sem `url` e `title` → `<li role="separator" class="divider">`.
- `subnav.html`: `<ul class="nav nav-tabs justify-content-end">` com `<a class="nav-link {active}">`; filhos só se tiverem `url`; títulos passados por `{% trans %}`.
- `nav.html`: `<li class="dropdown">` para grupos; item com `url` → `<li><a href …>`; sem `url`/`title` → separador; sem `url` e sem `check_permission` → `<li class="dropdown-header">`.
