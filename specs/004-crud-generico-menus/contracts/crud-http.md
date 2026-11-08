# Contrato: Rotas HTTP do CRUD genérico

Aplica-se a qualquer `Crud` (ex.: `TesteCrud` em `^teste/`, `UserCrud` em `002`). O prefixo é definido por quem inclui `get_urls()`; os caminhos abaixo são relativos a esse prefixo. O namespace de reverso é `model._meta.app_config.name` (para `Teste`: `backend.utils`), p.ex. `reverse("backend.utils:teste_list")`.

## Rotas

| Ação | Método(s) | Regex | `name=` | Permissão padrão (`Crud.public` pode remover) | Resposta |
|------|-----------|-------|---------|-----------------------------------------------|----------|
| Listar | GET | `^$` | `<modelo>_list` | `<app>.list_<modelo>` | 200 HTML (`<app>/<modelo>_list.html` → `crud/list.html`) |
| Criar | GET, POST | `^create$` | `<modelo>_create` | `<app>.add_<modelo>` | GET 200 formulário; POST válido 302 → detalhe; inválido 200 com erros |
| Detalhar | GET | `^(?P<pk>\d+)$` | `<modelo>_view` | `<app>.view_<modelo>` | 200 HTML (`<app>/<modelo>_detail.html` → `crud/detail.html`); inexistente → 404 |
| Editar | GET, POST | `^(?P<pk>\d+)/edit$` | `<modelo>_update` | `<app>.change_<modelo>` | GET 200; POST válido 302 → detalhe |
| Excluir | GET, POST | `^(?P<pk>\d+)/delete$` | `<modelo>_delete` | `<app>.delete_<modelo>` | GET 200 confirmação (`crud/confirm_delete.html`); POST 302 → listagem |

Rotas ausentes quando o atributo da view no `Crud` é `None`.

### Rotas de `MasterDetailCrud` (biblioteca, sem uso no esqueleto)

| Ação | Regex | `name=` |
|------|-------|---------|
| Listar filhos do pai `pk` | `^(?P<pk>\d+)/<modelo>$` | `<modelo>_list` |
| Criar filho no pai `pk` | `^(?P<pk>\d+)/<modelo>/create$` | `<modelo>_create` |
| Detalhar filho | `^<modelo>/(?P<pk>\d+)$` | `<modelo>_view` |
| Editar filho | `^<modelo>/(?P<pk>\d+)/edit$` | `<modelo>_update` |
| Excluir filho | `^<modelo>/(?P<pk>\d+)/delete$` | `<modelo>_delete` |

Parâmetro opcional `?pkk=<pk>` desambigua o pai em relações M2M (404 se faltar e houver mais de um pai).

## Rotas da demonstração (`backend/utils/urls.py`, namespace `backend.utils`)

| URL | Nome | Acesso |
|-----|------|--------|
| `/teste/` | `backend.utils:teste_list` | público (`public` contém `RP_LIST`) |
| `/teste/create` | `backend.utils:teste_create` | `utils.add_teste` |
| `/teste/<pk>` | `backend.utils:teste_view` | público (`RP_VIEW`) |
| `/teste/<pk>/edit` | `backend.utils:teste_update` | `utils.change_teste` |
| `/teste/<pk>/delete` | `backend.utils:teste_delete` | `utils.delete_teste` |

(`/testws/`, `/wstest/<slug>` e `/media/<path>` pertencem a `006` e `009`.)

## Regras de autorização

1. `permission_required` da view = permissões do verbo menos `Crud.public`; ao instanciar, cada item é expandido para `app_label + rad + model_name` (`".add_"` → `"utils.add_teste"`).
2. Conjunto vazio → qualquer visitante.
3. Conjunto não vazio → permitido se o usuário tiver **qualquer** das permissões.
4. Negado → anônimo: redireciona para `settings.LOGIN_URL` (`?next=`); autenticado: 403.
5. `container_field` definido → 404 no detalhe/edição/exclusão de objetos que não pertençam ao usuário; filtro na listagem.

## Parâmetros GET da listagem

| Parâmetro | Aplicável quando | Efeito |
|-----------|------------------|--------|
| `page` | sempre (paginado) | número da página (Django `Paginator`) |
| `o` | `ordered_list` verdadeiro (padrão) | índice 1-based da coluna de `list_field_names`; prefixo `-` = decrescente; módulo `n` colunas |
| `q` | `form_search_class` definido e modelo com `search` | busca por palavras (AND, `search__icontains`, sem acentos) |
| `page_size` | `form_search_class` definido | `10`, `25`, `50` ou `100`; padrão: cookie `backend_page_size` ou `10` |

Formulário inválido → 302 para a própria listagem + `messages.error("Formulário inválido. <erros>")`.

## Contexto entregue ao template de listagem

`object_list`, `page_obj`, `paginator`, `is_paginated`, `view`, `title`, `count`, `page_range`, `headers` (`[(rótulo, ordenável)]`), `rows` (`[[(html, url|None, css_class)]]`), `NO_ENTRIES_MSG`, `filter_url`, `ordering_url` (somente se `ordered_list`), `form` (se houver busca) e `<modelo>_list`.

## Mensagens

| Ação | Sucesso | Erro |
|------|---------|------|
| Criar | Registro criado com sucesso! | Formulário inválido. O registro não foi criado. |
| Editar | Registro alterado com sucesso! | Formulário inválido. Suas alterações não foram salvas. |
| Excluir | Registro excluído com sucesso! | Formulário inválido. O registro não foi excluído. |

## Cookies

| Nome | Quem escreve | Quem lê | Observação |
|------|--------------|---------|------------|
| `backend_page_size` | ninguém no código atual | `CrudListView.get` | valor padrão `"10"` |
| `sddstart_page_size` | JS de `crud/list.html` ao mudar `#id_page_size` | ninguém | nome divergente (ver `research.md`) |

## Atributos de configuração do `Crud`

| Atributo | Padrão | Efeito |
|----------|--------|--------|
| `model` | — | modelo alvo |
| `public` | `[]` | permissões (`RP_*`) liberadas a visitantes |
| `help_topic` | `""` | repassado às views |
| `container_css_class` | `""` | classe do container (`container_css_class` tag) |
| `container_field` / `container_field_set` | `""` | caminho `__` até o usuário para restringir objetos / itens relacionados |
| `list_field_names` | derivado do layout | colunas da listagem (str, tupla ou `campo|função`) |
| `list_field_names_set`, `model_set`, `layout_key_set` | — | itens relacionados no detalhe |
| `layout_key` | nome da classe do modelo | chave no `layouts.yaml` |
| `form_search_class` (na `ListView`) | ausente | habilita busca e `page_size` |
| `ordered_list` (no `BaseMixin`) | `True` | liga/desliga ordenação por `o` |
| `is_m2m`, `parent_field`, `link_return_to_parent_field` | `False` | mestre-detalhe |
| `namespace` | — | namespace para `CrudBaseForListAndDetailExternalAppView` |

Ganchos nas views: `hook_<campo>(obj, texto, url)` (listagem; retorna `texto`, `(texto, url)` ou `(texto, url, css)`), `hook_header_<campo>()` (retorna rótulo ou `(rótulo, ordenável)`), `hook_<campo>(obj, verbose_name=, field_display=)` (detalhe; retorna `(rótulo, valor)`), `extras_url`/`extras_list_url` (listas `(href, css_class, texto)` lidas pelos templates de detalhe), `search_url`.
