# Pesquisa e Decisões Técnicas: CRUD Genérico, Layouts YAML, Menus e Templates Base

Decisões inferidas do código e dos comentários. Cada item: **Decisão / Justificativa / Alternativas consideradas**.

## Decisões

### D1. CRUD por composição dinâmica de classes (`Crud.get_urls()`)

- **Decisão**: uma classe declarativa `Crud` com atributos de classe e views internas; `get_urls()` cria `class CrudViewWithBase(cls.BaseMixin, view)` para cada view e devolve `re_path`s.
- **Justificativa**: permite sobrescrever só a view/ação necessária (`UserCrud.CreateView`), compartilhar comportamento no `BaseMixin` e manter nomes de rota previsíveis (`<modelo>_<ação>`) sem escrever `urls.py` por modelo.
- **Alternativas**: `ModelViewSet`/`django-filter` (descartado: o projeto já gera API via `drfautoapi`, ver `005`); views avulsas por modelo (repetição); `django.contrib.admin` (já usado em `/system/`, mas sem a UX própria do projeto). O código tem um `TODO: refatorar para django-filter` na busca/ordenação.

### D2. Permissões por verbo com sufixos relativos (`".list_"`)

- **Decisão**: as views declaram `permission_required = (RP_LIST,)` etc., onde `RP_*` são **prefixos** (`".list_"`); `CrudBaseMixin.permission()` os expande para `app_label + rad + model_name`. `Crud.public` remove verbos da exigência; vazio = público.
- **Justificativa**: o mesmo código serve a qualquer modelo; combina com a permissão `list_<modelo>` criada em `003`.
- **Alternativas**: `permission_required` completo por view (verboso); `has_perms` (todas) — o código escolheu "qualquer uma" explicitamente (comentário "Torna a view pública…" e linha comentada `has_perms`).

### D3. Layout declarativo em YAML renderizado como template

- **Decisão**: `layouts.yaml` por app, renderizado pelo motor de templates (permite `{% trans %}`), com linhas `campo:largura` e divisão de colunas Bootstrap 12.
- **Justificativa**: formulário e detalhe vêm da mesma definição; textos traduzíveis; evita `ModelForm` por tela.
- **Alternativas**: `form_class` explícito (continua suportado: `fields` devolve `None` quando há `form_class`); `Layout` crispy em Python (mais verboso). Há `TODO cache this at application level` (YAML relido a cada requisição).

### D4. Menus em YAML renderizado como template

- **Decisão**: `menus.py` carrega YAML via loader de templates, renderiza com o contexto, resolve URLs/permissões in-place e entrega ao template de apresentação.
- **Justificativa**: permite lógica condicional (`{% if user.is_superuser %}`), `{% trans %}` e permissões por item sem código Python.
- **Alternativas**: menu em `settings`/Python; `django-menu`; o frontend Vue montando o menu pela API (não adotado).

### D5. Templates globais em `_templates/` e `backend.crud` fora de `INSTALLED_APPS`

- **Decisão**: templates (`crud/*`, `menus/*`, `base.html`) no diretório global; `backend/crud` é só biblioteca Python.
- **Justificativa**: o projeto é um esqueleto; os templates devem ser facilmente sobrescritos. O teste `_tests/test_initials.py` ignora diretórios que não estão em `INSTALLED_APPS`.
- **Alternativas**: registrar `backend.crud` e mover templates para `backend/crud/templates/` (mais "padrão Django").

### D6. Página-base como casca do Vue

- **Decisão**: `base.html` renderiza o HTML completo do servidor dentro de `<div id="emf"><emf-app>`, carrega `main.js` via `django-vite` e embute o sprite SVG; páginas Django e componentes Vue convivem.
- **Justificativa**: constituição, princípio V (Django dono das páginas e da sessão).
- **Alternativas**: SPA pura (não adotada).

### D7. Busca simples por `icontains` em campo `search` normalizado

- **Decisão**: `ListWithSearchForm.q` → palavras normalizadas (sem acentos) combinadas com AND sobre `search__icontains`; o modelo mantém `search` por `SearchModelMixin`.
- **Justificativa**: busca barata, sem Solr, aplicável a qualquer modelo com o mixin. A busca Solr é outra feature (`008`).
- **Alternativas**: `django-filter` (indicado em `TODO`), Haystack/Solr.

### D8. Ordenação por índice de coluna (`o`)

- **Decisão**: parâmetro `o` = índice 1-based da coluna de `list_field_names`, sinal `-` = decrescente, módulo `n` colunas, `Meta.ordering` como desempate.
- **Justificativa**: URL curta, sem expor nomes de campos; vale para campos relacionais (usa a ordenação do modelo relacionado) e tuplas (ordena por todos os campos da tupla).
- **Alternativas**: `ordering=campo` (expõe nomes), `OrderingFilter` do DRF.

### D9. Hooks por convenção de nome

- **Decisão**: `hook_<campo>`, `hook_header_<campo>` e `campo|funcao` personalizam rótulo/valor/URL/CSS sem subclasses de campo.
- **Justificativa**: extensibilidade mínima dentro de views e `layouts.yaml`.

## Particularidades, dívidas técnicas e riscos observados

Para cada item, a **recomendação** indica o que fazer em uma reconstrução melhorada; **o estado atual é replicar para fidelidade** (reproduzir o comportamento descrito), salvo instrução contrária.

| # | Observação (confirmada no código) | Impacto | Recomendação |
|---|-----------------------------------|---------|--------------|
| R1 | `backend/crud/__init__.py` contém `default_app_config = 'backend.utils.apps.CrudConfig'`, que aponta para uma classe inexistente em `backend.utils.apps` (a classe é `backend.crud.apps.CrudConfig`). `default_app_config` foi removido do Django (>=4.1) e é ignorado. | nenhum em runtime (módulo nunca é carregado como app) | **Corrigir** (remover ou apontar certo) se `crud` virar app. Replicar hoje. |
| R2 | `backend.crud` **não** está em `INSTALLED_APPS` (apenas `eauth`, `utils`, `api`, `globalrules`), embora a constituição cite `crud` como app. Templates e módulos funcionam como biblioteca. | `crud` não tem models/migrations/templates próprios; teste `_tests/test_initials.py` o ignora | Manter (decisão D5) ou **corrigir** registrando o app; replicar hoje. |
| R3 | A view de lista só aplica busca e `page_size` se a `ListView` tiver `form_search_class`; o modelo precisa herdar `SearchModelMixin` (campo `search`), senão `FieldError` ao filtrar. `TesteCrud` não usa busca. | demonstração sem busca/seletor | Replicar. Documentar o requisito. |
| R4 | Ordenação via `o`: índice 1-based em `list_field_names`, negativo = desc, `% len` para índices fora da faixa; só quando `ordered_list`. Erros são engolidos (log) e a ordenação é ignorada. | `o=999` não falha | Replicar. |
| R5 | `ordered_list = None` declarado na `ListView` (ex.: `UserCrud.ListView`) **não** desativa a ordenação, pois `CrudBaseMixin.ordered_list` é propriedade (`True`) e precede a view na MRO. | desativação ineficaz; links de ordenação continuam | **Corrigir** removendo a propriedade fixa ou lendo o atributo da view. Replicar hoje. |
| R6 | `Crud.public` remove permissões exigidas (view pública) em dois pontos: no `get_urls` (remove de `permission_required`) e no `__init__` do `CrudBaseMixin`. | ok; mas `list_url` usa `obj.ListView.permission_required` vazio para decidir "público" | Replicar. |
| R7 | `has_permission` aceita **qualquer** permissão exigida (OR); o Django padrão exige todas. Há uma linha comentada com `has_perms`. | views com várias permissões ficam mais permissivas | Replicar (só há uma por view). |
| R8 | `container_field` restringe objetos ao usuário (404/filtro). Com um único segmento (`container_field = "usuario"`), a criação **não** vincula nada (`TODO: implementar caso o user for o próprio container`) e `dispatch` ignora. | restrição incompleta no caso simples | **Corrigir** (implementar o caso). Replicar hoje. |
| R9 | Na criação a exceção "Não é permitido adicionar um registro sem estar em um Container" é um `Exception` genérico (500). | UX ruim | Corrigir (403/mensagem). |
| R10 | `CrudDeleteView.delete()` trata `ProtectedError` e chama `super().delete(request, args, kwargs)` (argumentos errados), mas no Django 6 o POST de `DeleteView` chama `form_valid`, não `delete()`. Resultado: exclusão de objeto protegido → erro 500; o código de tratamento é morto. | falha na exclusão protegida | **Corrigir** (tratar em `form_valid`). Replicar hoje. |
| R11 | `CrudUpdateView.form_valid` grava `self.object.modifier` (atributo que não existe como campo; o campo é `modified_by`); `CrudCreateView` grava `created_by`/`modified_by` em qualquer objeto (atributos Python inertes se o modelo não os tem). | auditoria de edição não funciona | **Corrigir** para `modified_by`. Replicar hoje. |
| R12 | Cookie de tamanho de página: backend lê `backend_page_size`, mas o JS de `crud/list.html` grava `sddstart_page_size`; nada grava `backend_page_size`. | a preferência não persiste | **Corrigir** unificando o nome. Replicar hoje. |
| R13 | `base.html` referencia o símbolo SVG `#svg-emais` (logo mobile e rodapé) que não existe no sprite embutido (existem `bootstrap`, `check2`, `circle-half`, `moon-stars-fill`, `sun-fill`, `svg-perfil`). | ícone vazio | **Corrigir** (definir símbolo ou usar `<img>`). Replicar hoje. |
| R14 | `base.html` usa `{% if perms.menu_administracao %}`: em `PermWrapper` isso testa `has_module_perms("menu_administracao")` (nome de app inexistente) → só superusuário ativo. `crud/list_tabaux.html` usa `perms.eauth.menu_administracao` (permissão inexistente). Em `menu_administracao.yaml`, `check_permission: menu_administracao` usa `has_perm` com nome sem `app.` → só superusuário. Há constante `menu_administracao = 'menu_1'` em `globalrules`. | menu de administração invisível para não superusuários, mesmo com grupo "Administrador do Sistema" | **Corrigir** (usar permissão real). Replicar hoje. |
| R15 | `menu_main.yaml` usa `{% trans '1.' %}` sem aspas no YAML → vira float (`1.0`, `2.0`, `3.0`). `menu_administracao.yaml`: item com `title: ' '`, `url: ''`. Itens "1. ..."/"2. " apontam para `/`. | rótulos errados (placeholders) | Corrigir ao personalizar o menu. Replicar hoje. |
| R16 | `crud/list.html` e `crud/detail.html`: o filtro `url` (`common_tags.url`) exige `str` (`value.startswith`); valor não-str em `rows` pode gerar erro silencioso no template. Em `detail.html`, células sem `href` ficam **vazias** (só `detail_detail.html` mostra o valor). Em `list.html`, `</div>` extra após o link de URL literal. | HTML inválido/ células vazias | Corrigir. |
| R17 | Sem `list_field_names`, a listagem usa **todos os campos da primeira legenda** do layout; em `utils/layouts.yaml` isso produz 10 colunas (campos repetidos `teste` e `id`) e o formulário renderiza `teste` várias vezes (aviso crispy "A field should only be rendered once"). | demo confusa | **Corrigir** o layout (`Teste: - teste`) e declarar `list_field_names`. Replicar hoje. |
| R18 | `read_layout_from_yaml` engole **qualquer** exceção e devolve `[]`; chamadas posteriores (`get_layout()[0][1:]`) causam `IndexError` sem mensagem clara. `read_yaml_from_file` não faz cache (`TODO`). | diagnóstico difícil; custo por requisição | Corrigir (logar e cachear). |
| R19 | `nav_run`: `except:` nus e `try/except pass` em reversões; `view.crud.get_urls()` é recalculada para cada item de menu (recria classes a cada chamada). `return` sem valor quando `yaml_path` vazio. **Verificado**: `rm.app_name` com `resolver_match = None` levanta `AttributeError` em páginas 404 (`DEBUG=False`), transformando o 404 em **500** (a falha ocorre fora do `try`). | desempenho e robustez; 404 quebrado em produção | Corrigir (cachear `get_urls`, tratar `resolver_match=None`). |
| R20 | `m2m_urlize_for_detail` e `GenericForeignKey` em `get_field_display` usam o nome de rota `<modelo>_detail`, enquanto o CRUD gera `<modelo>_view` (`fk_urlize_for_detail` usa `_view`). | `NoReverseMatch` | Corrigir para `_view`. |
| R21 | `crud/format_options.html` depende de `view.formats_impl` (não existe) e `utils/teste_list.html` o inclui com `url_openapi='backend.api:utils_teste-list'`. Código morto. Idem `view.search_url`, `extras_url`, `extras_list_url`, `object.checkcheck` em `detail.html` (herança de outro projeto). | sem efeito | Manter/limpar. |
| R22 | `MasterDetailCrud`, `CrudBaseForListAndDetailExternalAppView`, `Crud.build`, `PermissionRequiredForAppCrudMixin`, `Crud.frontend` e `return_parent_field_url` não são usados por nenhum modelo do esqueleto; `MasterDetailCrud.DetailView.detail_list_url` compara `obj.ListView.permission_required not in obj.public` (tupla dentro de lista: sempre `True`). `resolve_url` de `MasterDetailCrud.CreateView.cancel_url` contém `break` dentro do `for` (só usa o primeiro segmento). | código não exercitado; bugs latentes | Manter como biblioteca; cobrir com testes antes de usar. |
| R23 | Segurança: `value|safe` é aplicado a valores de células/detalhe/título (`{{ title|safe }}`, `{{ message|safe }}`, `{{ column.text|safe }}`) e `get_field_display` monta HTML por concatenação (`<a href>`, `<li>`) sem escape de `str(obj)`; `confirm_delete.html` usa `{{ object|safe }}`. | risco de XSS armazenado se campos contêm HTML | **Corrigir** (escapar por padrão e marcar seguro seletivamente). Replicar hoje. |
| R24 | CSRF e login: `base.html` faz logout por `POST` com `csrf_token` (correto). `ALLOWED_HOSTS` e CORS abertos (restrição constitucional, ver `001`). | — | Replicar. |
| R25 | `forms.py` importa `from warnings import filters` (importação inútil), e `custom_filters=[]` default mutável é mutado (`insert(0, Field("page_size"))`) quando passado explicitamente. | efeito colateral se reutilizada a lista | Corrigir. |
| R26 | `get_headers` usa `except:` nu e `if f:` fora do loop que pode usar `f` não definido (campo vazio). `CrudDetailView.get` captura `Exception` e converte tudo em 404 (inclusive erros reais). | erros mascarados | Corrigir. |
| R27 | Comentário em `FORM_MESSAGES`: a primeira definição é sobrescrita pela segunda (apenas erro recebe prefixo "Formulário inválido."). | — | Replicar. |
| R28 | `base.html` tem `<title>Backend</title>` fixo e textos "Sdd Start"/"Backend" misturados; `{% if False %}` com despejo de `request.META` (código de depuração desativado). | cosmético | Parametrizar o título. |
