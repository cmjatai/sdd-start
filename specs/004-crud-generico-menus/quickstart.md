# Início Rápido: validar o CRUD Genérico, os Layouts e os Menus

Pré-requisitos: ambiente de `001` pronto (`backend/.env`, dependências com `poetry install`, PostgreSQL acessível — por Docker em dev, ver `010`) e migrações aplicadas (`poetry run python manage.py migrate`).

## 1. Subir e navegar

```bash
poetry run python manage.py runserver          # ou ./uupdev.sh no ambiente Docker (010)
```

| URL | Esperado |
|-----|----------|
| `/` | 200; logotipo central, barra com "INÍCIO", "1.0", "2.0", "3.0" e ícone de login (anônimo) |
| `/teste/` | 200 sem login (listagem pública); botão "Adicionar Teste" só para quem tem `utils.add_teste`; tabela com colunas repetidas (ver Casos de Borda) |
| `/teste/create` | anônimo → 302 `/login…?next=/teste/create`; superusuário → 200 com fieldset "Modelo Teste" |
| `/teste/<pk>` | 200 sem login; mostra o detalhe e o botão "OpenAPI" (`/api/utils/teste/<pk>`) |
| `/teste/<pk>/edit` e `/teste/<pk>/delete` | exigem `utils.change_teste` / `utils.delete_teste` |
| `/teste/?o=-2` | ordenação decrescente pela 2ª coluna; links de cabeçalho mantêm outros parâmetros |
| `/teste/?page=2` | segunda página (10 por página) |

Como superusuário (criar com `poetry run python manage.py createsuperuser`): a engrenagem do cabeçalho exibe "Configurações Gerais", "Manutenção de Usuários" (Usuários, Auditoria de Acessos) e "Testes" (`/teste/`, `/wstest/`).

## 2. Verificações rápidas no shell Django

```bash
poetry run python manage.py shell -c "
from backend.utils.views import TesteCrud
print([(u.pattern.regex.pattern, u.name) for u in TesteCrud.get_urls()])
from backend.crud.base import make_pagination
print(make_pagination(15, 30))   # [1, 2, 3, None, 14, 15, 16, None, 29, 30]
from backend.crud.crispy_layout_mixin import read_layout_from_yaml
print(read_layout_from_yaml('utils/layouts.yaml', 'Teste'))
"
```

Esperado: 5 rotas (`teste_list`, `teste_create`, `teste_view`, `teste_update`, `teste_delete`), a lista de paginação acima e o layout com larguras `[('id',3),('teste',3),('teste',3),('teste',3)] …`.

## 3. Testes automatizados

```bash
poetry run pytest backend/crud/tests.py -q            # existente: test_read_layout_from_yaml
poetry run pytest backend/crud backend/utils -q       # após criar os testes das tarefas desta feature
poetry run ruff check backend/crud backend/utils
```

Testes que **deveriam existir** (ver `tasks.md`):

| Teste | Verifica |
|-------|----------|
| `test_make_pagination_*` | listas esperadas para `(1,5)`, `(1,30)`, `(15,30)`, `(27,30)`, tamanho ≤ 10 |
| `test_line_to_namespans` / layout v1 e v2 | distribuição de larguras; `[]` em erro |
| `test_teste_crud_urls` | 5 rotas, nomes e regex |
| `test_teste_list_public` (fixture `app` sem usuário) | `/teste/` 200 anônimo; `/teste/create` 302 |
| `test_teste_create_update_delete_superuser` | fluxo completo com mensagens de sucesso |
| `test_list_ordering_param` | `?o=2`, `?o=-2`, `?o=99` sem erro 500 e ordem correta |
| `test_list_search_form` | `ListWithSearchForm` com modelo `SearchModelMixin` (ex.: `User`), `q` em várias palavras, `page_size` inválido → redireciona |
| `test_menu_resolve_urls_inplace` | `check_permission`, `active`, `url` reversa e literal |
| `test_menu_missing_yaml` | `nav_run` devolve `None` sem exceção |
| `test_base_template_renders` | `/` contém `id="emf"`, `<emf-app>`, "INÍCIO" |

## 4. Critérios de aceite resumidos

- [ ] As 5 rotas de `TesteCrud` existem com os nomes e regex do contrato `contracts/crud-http.md`.
- [ ] Listagem e detalhe são públicos; criação/edição/exclusão exigem permissão.
- [ ] Ordenação por `o`, paginação com reticências e preservação de parâmetros funcionam.
- [ ] Layout YAML gera formulário e detalhe; teste de layout passa.
- [ ] Menus principal e de administração renderizam; itens protegidos somem para quem não tem permissão.
- [ ] `pytest` e `ruff check .` sem falhas.

## 5. Observações para a validação

- Com `DEBUG=False`, a URL inexistente resulta em 500 (e não em `404.html`) por causa do menu (ver `research.md` R19); para validar `404.html` use `DEBUG=True` apenas para a página técnica ou renderize o template em teste com `resolver_match` definido.
- O seletor "Resultados por página" só aparece em listagens com `form_search_class` (ex.: usuários em `002`), não em `/teste/`.
