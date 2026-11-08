# Especificação da Funcionalidade: CRUD Genérico, Layouts YAML, Menus e Templates Base

**Branch da Funcionalidade**: `004-crud-generico-menus`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: biblioteca de CRUD genérico (`backend/crud/`), layouts de formulário/detalhe em YAML, menus declarativos em YAML (`backend/utils/templatetags/menus.py`), templates-base (`_templates/`: `base.html`, `index.html`, `404.html`, `crud/*`, `menus/*`, `paginacao.html`, `utils/*`, `eauth/layouts.yaml`) e a demonstração `TesteCrud` em `/teste/`."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Declarar um CRUD completo a partir de um modelo (Prioridade: P1)

Uma pessoa desenvolvedora declara uma classe `Crud` apontando para um modelo Django (`model = Teste`) e inclui `Classe.get_urls()` em um `urls.py`. Sem escrever views, templates ou formulários, o sistema passa a oferecer cinco telas: listagem, criação, detalhe, edição e exclusão, com nomes de rota previsíveis (`<modelo>_list`, `<modelo>_create`, `<modelo>_view`, `<modelo>_update`, `<modelo>_delete`).

**Por que esta prioridade**: é o núcleo da funcionalidade; todas as telas administrativas do esqueleto (usuários em `002`, modelo `Teste`) são construídas sobre ela e sem ela nenhuma outra história tem valor.

**Teste Independente**: registrar `TesteCrud` em `backend/utils/urls.py` sob `^teste/` e acessar `/teste/`, `/teste/create`, `/teste/<pk>`, `/teste/<pk>/edit` e `/teste/<pk>/delete`; as cinco rotas respondem (200 ou redirecionamento de login conforme a permissão).

**Cenários de Aceitação**:

1. **Dado** um `Crud` com `model = Teste`, **Quando** `get_urls()` é chamado, **Então** devolve exatamente cinco `re_path` com as expressões `^$`, `^create$`, `^(?P<pk>\d+)$`, `^(?P<pk>\d+)/edit$`, `^(?P<pk>\d+)/delete$` e nomes `teste_list`, `teste_create`, `teste_view`, `teste_update`, `teste_delete`.
2. **Dado** um superusuário autenticado, **Quando** envia o formulário válido de criação, **Então** o registro é criado, a mensagem "Registro criado com sucesso!" é exibida e o usuário é levado ao detalhe do novo registro.
3. **Dado** um registro existente e um usuário com permissão de alteração, **Quando** salva a edição, **Então** a mensagem "Registro alterado com sucesso!" é exibida e o usuário volta ao detalhe.
4. **Dado** um registro existente e um usuário com permissão de exclusão, **Quando** confirma a exclusão, **Então** o registro é removido, a mensagem "Registro excluído com sucesso!" é exibida e o usuário volta à listagem.
5. **Dado** um formulário inválido, **Quando** é enviado, **Então** a mensagem é prefixada por "Formulário inválido." seguida de "O registro não foi criado." (criação), "Suas alterações não foram salvas." (edição) ou "O registro não foi excluído." (exclusão).
6. **Dado** um `Crud` sem `CreateView` (atributo `None`), **Quando** `get_urls()` é chamado, **Então** a rota de criação não é registrada e o botão "Adicionar" não aparece.

---

### História de Usuário 2 - Controle de acesso por permissão e rotas públicas (Prioridade: P1)

Cada tela do CRUD exige uma permissão de modelo (`list_`, `view_`, `add_`, `change_`, `delete_` + nome do modelo, no app do modelo). O `Crud` pode declarar `public = [...]` para tornar telas específicas acessíveis sem login (caso de `TesteCrud`, que libera listagem e detalhe). Botões e links de ação só aparecem se o usuário puder usá-los.

**Por que esta prioridade**: define a segurança de todas as telas geradas; está acoplada ao modelo de permissões da `003-regras-permissoes-globais`.

**Teste Independente**: com um usuário anônimo, `GET /teste/` retorna 200 e `GET /teste/create` redireciona ao login; com superusuário, ambas retornam 200.

**Cenários de Aceitação**:

1. **Dado** `public = [RP_LIST, RP_VIEW]`, **Quando** um visitante anônimo acessa a listagem ou o detalhe, **Então** a página é exibida sem exigir login.
2. **Dado** o mesmo `Crud`, **Quando** o visitante anônimo acessa `/teste/create`, `/teste/<pk>/edit` ou `/teste/<pk>/delete`, **Então** é redirecionado ao login (ou recebe 403 se já autenticado sem a permissão).
3. **Dado** um usuário autenticado que possui **qualquer uma** das permissões exigidas pela view, **Quando** acessa a view, **Então** o acesso é concedido (a verificação é "alguma de", não "todas").
4. **Dado** um usuário sem a permissão `utils.add_teste`, **Quando** vê a listagem, **Então** o botão "Adicionar Teste" não é exibido; **Dado** um usuário com a permissão, **Então** o botão aparece.
5. **Dado** um usuário sem a permissão `utils.change_teste`/`utils.delete_teste`, **Quando** vê o detalhe, **Então** os botões "Editar"/"Excluir" não aparecem.

---

### História de Usuário 3 - Listagem com busca, ordenação, paginação e tamanho de página (Prioridade: P1)

A listagem apresenta tabela com cabeçalhos clicáveis para ordenar (parâmetro `o`, índice 1-based da coluna; negativo = decrescente), paginação com reticências, contador "Total de …", e — quando a view declara `form_search_class` (ex.: `ListWithSearchForm`) e o modelo herda de `SearchModelMixin` — uma caixa de busca textual (`q`), seletor "Resultados por página" (10/25/50/100) e botão "Filtrar".

**Por que esta prioridade**: a listagem é a tela de entrada de qualquer CRUD e a mais usada.

**Teste Independente**: com registros cadastrados, acessar `/teste/?o=-2` ordena decrescentemente pela 2ª coluna; no CRUD de usuários (`002`), digitar `q=maria` filtra por todas as palavras informadas.

**Cenários de Aceitação**:

1. **Dado** uma listagem com mais de 10 páginas, **Quando** a página 15 de 30 é exibida, **Então** a barra mostra `1 2 3 … 14 15 16 … 29 30`.
2. **Dado** uma listagem sem parâmetro `o`, **Quando** é aberta, **Então** ordena pela 1ª coluna (e, na sequência, pela ordenação padrão do modelo) e o cabeçalho da 1ª coluna aponta para `-1` (inverter).
3. **Dado** `?o=-3`, **Quando** a listagem é aberta, **Então** ordena decrescente pela 3ª coluna de `list_field_names`; índices fora do intervalo são tratados por módulo (`(|o|-1) % n`).
4. **Dado** `form_search_class` configurado, **Quando** o usuário envia `q=ana silva`, **Então** só retornam registros cujo campo `search` contém **todas** as palavras (sem acentos, `icontains`, AND).
5. **Dado** `form_search_class` configurado e nenhuma query `page_size`, **Quando** existe o cookie `backend_page_size`, **Então** o valor do cookie define o tamanho da página; caso contrário, 10.
6. **Dado** um valor de formulário inválido (ex.: `page_size=7`), **Quando** a listagem é carregada, **Então** o usuário é redirecionado para a própria listagem com mensagem de erro "Formulário inválido. …".
7. **Dado** nenhuma linha, **Quando** a listagem é aberta, **Então** exibe "Nenhum registro encontrado." no lugar da tabela.
8. **Dado** qualquer filtro/ordenação ativo, **Quando** o usuário muda de página ou de ordenação, **Então** os demais parâmetros GET são preservados nos links (`filter_url` / `ordering_url`).

---

### História de Usuário 4 - Formulários e telas de detalhe dirigidos por layout YAML (Prioridade: P2)

Os campos mostrados no formulário (criação/edição) e na tela de detalhe vêm de um arquivo YAML por app (`<app_label>/layouts.yaml`), na chave igual ao nome da classe do modelo (ou a `layout_key` da view). Cada linha lista campos com larguras opcionais em colunas Bootstrap (`campo:8`), e as larguras não informadas dividem o restante de 12 colunas. Há uma versão 2 do layout para organizar o detalhe em grupos de colunas.

**Por que esta prioridade**: reduz o código por tela, mas um CRUD ainda funciona com `form_class` explícito (por isso P2).

**Teste Independente**: com `utils/layouts.yaml` (chave `Teste`), abrir `/teste/create` mostra o fieldset "Modelo Teste"; `read_layout_from_yaml` é coberto por teste unitário.

**Cenários de Aceitação**:

1. **Dado** a linha `teste:3 teste teste`, **Quando** o layout é lido, **Então** as larguras resultantes são `(teste,3) (teste,5) (teste,4)` (o restante 9 é dividido por teto entre os dois campos sem largura).
2. **Dado** o texto `name:9  place  tiny`, **Quando** lido, **Então** resulta `[('name',9),('place',2),('tiny',1)]`.
3. **Dado** um layout versão 1 (padrão), **Quando** o detalhe é exibido, **Então** cada chave do YAML vira um bloco com legenda `<h2 class="legend">` e linhas de colunas `col-lg-N`.
4. **Dado** um layout com `version: 2`, **Quando** o detalhe é exibido, **Então** o YAML é lido como grupos de colunas → fieldsets → colunas internas → linhas, e os blocos usam as classes CSS informadas nas chaves.
5. **Dado** uma chave de layout inexistente ou um arquivo YAML inválido, **Quando** o layout é lido, **Então** o resultado é lista vazia (sem exceção propagada).
6. **Dado** um campo com ganchos (`hook_<campo>`, `hook_header_<campo>`) definidos na view, **Quando** o detalhe/listagem é montado, **Então** o gancho pode alterar rótulo, valor, URL e classe CSS da célula.

---

### História de Usuário 5 - Menus declarativos em YAML com permissões (Prioridade: P2)

Os menus da barra superior (principal, administração) e a sub-navegação (abas) são definidos em arquivos YAML renderizados como templates Django, com título, URL (nome de rota ou caminho), ícones/classes CSS e `check_permission`. O sistema resolve as URLs, marca o item ativo e oculta/zera itens para os quais o usuário não tem permissão.

**Por que esta prioridade**: dá navegação ao esqueleto; independente do CRUD, mas dele consome o contexto (`view.crud`) para marcar o item ativo.

**Teste Independente**: abrir `/` mostra a barra com "INÍCIO"; como superusuário o ícone de engrenagem exibe o menu de administração com "Usuários", "Auditoria de Acessos" e "Testes".

**Cenários de Aceitação**:

1. **Dado** `{% menu 'menus/menu_main.yaml' %}`, **Quando** a página é renderizada, **Então** cada item vira `<li><a href=…><span>título</span></a></li>`.
2. **Dado** um item com `url: backend.eauth:user_list`, **Quando** resolvido, **Então** vira o caminho reverso da rota (tentando primeiro com `pk` e depois sem).
3. **Dado** um item com `check_permission` que o usuário não satisfaz, **Quando** resolvido, **Então** a URL do item é esvaziada e o item não fica ativo; se for grupo (sem `url`), seus `children` são removidos.
4. **Dado** `request.path` igual à URL resolvida do item, **Quando** renderizado, **Então** o item recebe a classe `active`; um grupo fica ativo se algum filho estiver ativo.
5. **Dado** um item sem `url` e sem `title`, **Quando** renderizado em `menus/menu.html`, **Então** vira um separador `<li role="separator" class="divider">`.
6. **Dado** um usuário comum (não superusuário), **Quando** vê a barra, **Então** o menu de administração não é exibido; o item "Testes" só existe para superusuário.

---

### História de Usuário 6 - Página-base, índice, 404 e demonstração `TesteCrud` (Prioridade: P3)

Todas as páginas herdam de `base.html`: cabeçalho com marca, menu principal, menu de administração (se permitido), avatar/menu do usuário ou ícone de login, mensagens do Django, rodapé com seletor de tema (claro/escuro/automático) e montagem do frontend Vue dentro de `<div id="emf"><emf-app>`. `index.html` mostra o logotipo; `404.html` mostra `<emf-error-404>`. `TesteCrud` demonstra o conjunto.

**Por que esta prioridade**: casca visual e demonstração; é consumida por todas as demais features, mas é substituível.

**Teste Independente**: `GET /` retorna 200 com o logotipo e a barra; `GET /teste/` lista os `Teste` cadastrados; uma URL inexistente com `DEBUG=True` mostra a página técnica de 404 do Django (com `DEBUG=False`, ver Casos de Borda).

**Cenários de Aceitação**:

1. **Dado** um usuário anônimo, **Quando** abre qualquer página, **Então** vê o ícone de login apontando para `backend.eauth:login`.
2. **Dado** um usuário autenticado, **Quando** abre o menu do avatar, **Então** vê "Meu Perfil" (`backend.eauth:backend_user_change`) e o botão "Sair" (POST para `backend.eauth:logout` com CSRF).
3. **Dado** mensagens do Django, **Quando** a página é renderizada, **Então** são mostradas como alertas Bootstrap dispensáveis (tag `error` vira `danger`).
4. **Dado** a listagem de `Teste`, **Quando** aberta, **Então** usa o template `utils/teste_list.html` (que estende `crud/list.html`) por precedência sobre `crud/list.html`.

---

### Casos de Borda

- **Modelo sem `SearchModelMixin`** com `form_search_class`: a listagem quebra ao filtrar por `search__icontains` (campo inexistente). `TesteCrud` não declara `form_search_class`, portanto `/teste/` **não** tem busca nem seletor de página e ignora `q`/`page_size` (tamanho fixo 10).
- **Colunas duplicadas na demonstração**: sem `list_field_names`, a listagem usa todos os campos da **primeira legenda** do layout; em `utils/layouts.yaml` isso gera 10 colunas (`id` e nove repetições/variações de `teste`), e o formulário renderiza o campo `teste` várias vezes (aviso "A field should only be rendered once: teste").
- **Cookie de tamanho de página**: o JavaScript de `crud/list.html` grava o cookie `sddstart_page_size`, mas o backend lê `backend_page_size`; a escolha do usuário no seletor não persiste entre páginas (só vale pelo parâmetro `page_size` da própria requisição).
- **Exclusão protegida**: o tratamento de `ProtectedError` está implementado em `delete()`, que o `DeleteView` do Django 6 não chama no POST; um objeto referenciado por `PROTECT` causa erro 500 em vez da mensagem amigável.
- **`ordered_list = None` em uma `ListView`** não desativa a ordenação (a propriedade do `BaseMixin` tem precedência); para desativar, deve-se sobrescrever `ordered_list` no `BaseMixin` do `Crud`.
- **404 com `DEBUG=False`**: `404.html` estende `base.html`, cujas tags `{% menu %}` leem `request.resolver_match.app_name`; como `resolver_match` é `None` em rotas inexistentes, a renderização levanta `AttributeError` e a resposta vira **500** em vez de 404 (verificado com `Client().get('/nao-existe-xyz')`).
- **Menu "1.", "2.", "3."** em `menu_main.yaml` são interpretados pelo YAML como números (`1.0`, `2.0`, `3.0`) e aparecem assim na barra.
- **`#svg-emais`** é referenciado em `base.html` (logo mobile/rodapé) mas não existe no sprite SVG embutido; o ícone não aparece.
- **`perms.menu_administracao`** (barra) testa permissão de **módulo** com esse nome de app (inexistente); na prática só superusuários ativos passam.
- **Detalhe sem filhos clicáveis**: em `crud/detail.html` as células da tabela de itens relacionados só mostram o valor quando há link (`href`).
- **Container**: com `container_field` definido, objetos de outros usuários respondem 404 no detalhe/edição/exclusão e são filtrados da listagem; na criação, o usuário precisa estar registrado no modelo-contêiner, senão é redirecionado a `/` com mensagem de erro.
- **Layout ausente**: se o YAML/chave não existir, `read_layout_from_yaml` devolve `[]` e a listagem/detalhe falham ao tentar `[0][1:]` (sem `list_field_names` explícito).
- **Menu YAML inexistente/ inválido**: `nav_run` devolve `None`/registra erro e nada é renderizado (a página continua funcionando).

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**CRUD genérico**

- **FR-001**: O sistema DEVE oferecer a classe `Crud` (`backend/crud/base.py`) cujo atributo `model` define o modelo e cuja classmethod `get_urls()` devolve uma lista de `re_path` para List, Create, Detail, Update e Delete, omitindo as views cujo atributo (`ListView`, `CreateView`, `DetailView`, `UpdateView`, `DeleteView`) seja `None`.
- **FR-002**: Os nomes das rotas DEVEM ser `<model_name>_<ação>` com ação em `list`, `create`, `view`, `update`, `delete`; as expressões DEVEM ser `^$`, `^create$`, `^(?P<pk>\d+)$`, `^(?P<pk>\d+)/edit$`, `^(?P<pk>\d+)/delete$`.
- **FR-003**: Cada view gerada DEVE misturar o `BaseMixin` do CRUD com a view genérica, receber `model`, `help_topic` e `crud`, e ter nome de classe `"<Crud> <View>"`.
- **FR-004**: O sistema DEVE oferecer `Crud.build(model, help_topic, model_set=None, list_field_names=[])` que cria dinamicamente uma subclasse `<Model>Crud`.
- **FR-005**: O `Crud` DEVE permitir sobrescrever `BaseMixin` e as views internas (ex.: `UserCrud.BaseMixin`, `UserCrud.CreateView`) e declarar atributos de configuração: `help_topic`, `container_css_class`, `public`, `container_field`, `container_field_set`, `is_m2m`, `model_set`, `form_search_class`, `list_field_names`, `list_field_names_set`, `layout_key`, `layout_key_set`, `ordered_list`, `parent_field`, `namespace`.

**Permissões**

- **FR-006**: Cada view DEVE exigir, por padrão, a permissão do seu verbo: List → `<app>.list_<modelo>`, Create → `<app>.add_<modelo>`, Detail → `<app>.view_<modelo>`, Update → `<app>.change_<modelo>`, Delete → `<app>.delete_<modelo>` (constantes `RP_LIST`, `RP_ADD`, `RP_VIEW`, `RP_CHANGE`, `RP_DELETE` de `backend/globalrules`).
- **FR-007**: As permissões listadas em `Crud.public` DEVEM ser removidas das permissões exigidas; uma view sem permissões exigidas DEVE ser acessível a qualquer visitante, inclusive anônimo.
- **FR-008**: Havendo várias permissões exigidas, o acesso DEVE ser concedido se o usuário tiver **ao menos uma** delas.
- **FR-009**: Sem permissão, a view DEVE seguir `handle_no_permission` do Django (login para anônimo; 403 para autenticado).
- **FR-010**: As propriedades `list_url`, `create_url`, `detail_url`, `update_url`, `delete_url` DEVEM devolver `""` quando a view não existe ou o usuário não tem a permissão correspondente (exceto se a view for pública), e a URL reversa caso contrário, usando o namespace `model._meta.app_config.name`.
- **FR-011**: Com `container_field` definido, o sistema DEVE restringir o acesso a objetos cujo campo (caminho `__` até o usuário) seja o usuário logado: 404 em detalhe/edição/exclusão de objeto alheio, filtro na listagem e, na criação, vincular o objeto ao contêiner do usuário ou falhar.
- **FR-012**: O mixin `PermissionRequiredForAppCrudMixin` DEVE conceder acesso quando o usuário tem permissões no módulo (app) da view; não é usado por padrão.

**Listagem**

- **FR-013**: A listagem DEVE montar `headers` (rótulo, pode_ordenar) e `rows` (valor, url, css_class) a partir de `list_field_names`, aceitando campos simples, tuplas (junção com ` / ` ou `<br>` para listas), caminhos `a__b`, sufixo `|função` e ganchos `hook_<campo>` / `hook_header_<campo>`; somente a 1ª coluna recebe link para o detalhe.
- **FR-014**: A listagem DEVE expor no contexto `count`, `page_range` (via `make_pagination`), `NO_ENTRIES_MSG`, `filter_url`, `ordering_url`, `title` (padrão: `verbose_name_plural`) e `form` (se houver).
- **FR-015**: A ordenação DEVE ser feita pelo parâmetro `o` conforme os cenários da História 3, acrescentando a ordenação `Meta.ordering` do modelo ao final; para campos relacionais DEVE usar a ordenação do modelo relacionado.
- **FR-016**: Com `form_search_class`, a view DEVE instanciar o formulário com os parâmetros GET, preencher `page_size` com o parâmetro, ou o cookie `backend_page_size`, ou o padrão; formulário inválido DEVE redirecionar para `list_url` com mensagem de erro; válido DEVE definir `paginate_by = int(page_size)` e filtrar por `search__icontains` por palavra (normalizada, AND).
- **FR-017**: A paginação padrão DEVE ser 10 itens por página na listagem e no detalhe.
- **FR-018**: `make_pagination(index, num_pages)` DEVE devolver todas as páginas se `num_pages <= 10`; caso contrário uma lista com `None` representando reticências, sempre começando com as primeiras páginas e terminando com as duas últimas e incluindo `index-1, index, index+1`.
- **FR-019**: `ListWithSearchForm` DEVE conter os campos `q` (texto, tipo `search`, opcional), `o` (oculto, inicial `1`) e `page_size` (choices 10, 25, 50, 100; inicial 10; opcional), com método GET, botão "Filtrar" e placeholder "Busque por palavras, números ou códigos".

**Criação, edição, exclusão e detalhe**

- **FR-020**: Create, Update e Delete DEVEM exibir mensagens de sucesso/erro conforme `FORM_MESSAGES` (textos em pt-BR do cenário 5 da História 1) via `django-braces`.
- **FR-021**: Após criar ou editar, o sistema DEVE redirecionar ao detalhe; após excluir, à listagem; o botão "Cancelar" do formulário DEVE apontar para `view.cancel_url` (listagem na criação; detalhe na edição/exclusão).
- **FR-022**: Na criação, o sistema DEVE tentar gravar `created_by` e `modified_by` com o usuário logado (e na edição, `modifier`), ignorando falhas.
- **FR-023**: O título da criação DEVE ser "Adicionar <verbose_name>".
- **FR-024**: O detalhe DEVE renderizar o objeto conforme o layout (`layout_display`), com link "OpenAPI" para `/api/<app_label>/<model_name>/<id>`, e botões Listar, Adicionar, Editar e Excluir condicionados às permissões; se `model_set` estiver definido, DEVE listar também os itens relacionados (paginados, 10 por página).
- **FR-025**: O sistema DEVE oferecer `MasterDetailCrud` (mestre-detalhe) com rotas `^(?P<pk>\d+)/<modelo>$`, `^(?P<pk>\d+)/<modelo>/create$`, `^<modelo>/(?P<pk>\d+)$`, `^<modelo>/(?P<pk>\d+)/edit$`, `^<modelo>/(?P<pk>\d+)/delete$`, `parent_field`, `is_m2m` e parâmetro `?pkk=`; e `CrudBaseForListAndDetailExternalAppView` (somente leitura, público, usando `namespace` do app local). Ambos são biblioteca sem uso no esqueleto atual.

**Layouts**

- **FR-026**: `read_layout_from_yaml(arquivo, chave)` DEVE renderizar o arquivo como template Django, carregá-lo com `yaml.full_load`, interpretar cada linha `campo[:largura] …` distribuindo `12 - soma` entre campos sem largura por teto e devolver `[[legenda, linha, …], …]` (v1) ou `([...], 2)` (v2); qualquer exceção DEVE resultar em `[]`.
- **FR-027**: O mixin de layout DEVE derivar `fields` (campos do formulário) de todas as linhas do layout quando a view não tem `form_class`, decorar o formulário com `CustomFormHelper` + `CustomFormLayout` (fieldsets/linhas/colunas Bootstrap, botão "Salvar" que desabilita duplo clique, link "Cancelar") e derivar `list_field_names` da primeira legenda quando não informado.
- **FR-028**: `get_field_display(obj, nome)` DEVE formatar valores: `None`→vazio, datas no `SHORT_DATE_FORMAT`, booleanos "Sim"/"Não", choices pelo `get_<campo>_display`, imagens como `<img>`, arquivos como link, gerenciadores como `<ul><li>…</li></ul>`, `TextField` em `<div class="dont-break-out">` com `\n`→`<br/>` se não houver HTML, decimais com separador de milhar, e devolver `(verbose_name, display)`.
- **FR-029**: O sistema DEVE oferecer utilidades para detalhes: `fk_urlize_for_detail`, `m2m_urlize_for_detail` e `markdown` (extensões `fenced_code` e `codehilite`, com suporte a trecho entre `[[[[ ]]]]`), acionáveis via sufixo `|função` no nome do campo.

**Menus**

- **FR-030**: As tags `{% menu %}`, `{% subnav %}` e `{% navbar %}` (biblioteca `menus`) DEVEM renderizar, respectivamente, `menus/menu.html`, `menus/subnav.html` e `menus/nav.html` a partir de um YAML definido por: argumento `path`, ou variável de contexto `subnav_template_name`, ou o padrão `<app_name>/subnav.yaml`.
- **FR-031**: O YAML DEVE aceitar, por item, as chaves `title`, `url`, `children`, `check_permission`, `css_class_li`, `css_class_a`, `css_class_span`, `css_class_ul`, `css_class_icon`, `urls_extras`; o arquivo é renderizado como template com o contexto da página.
- **FR-032**: A resolução de URLs DEVE reverter nomes (`app:nome` com ou sem `pk`; nome simples prefixado por `request.resolver_match.app_name`) e preservar o valor original quando não reversível (ex.: `/`, `#`).
- **FR-033**: O item ativo DEVE ser definido por igualdade de caminho ou por pertencer às rotas do `view.crud` (ou `urls_extras`); itens pai herdam `active` dos filhos.
- **FR-034**: Falhas ao carregar/converter o YAML NÃO DEVEM quebrar a página (erro registrado em log, menu vazio).

**Templates-base**

- **FR-035**: `base.html` DEVE carregar `i18n static django_vite common_tags menus`, injetar `{% vite_hmr_client %}` e `{% vite_asset 'main.js' %}`, definir `data-bs-theme="auto"`, embutir o sprite SVG (símbolos `bootstrap`, `check2`, `circle-half`, `moon-stars-fill`, `sun-fill`, `svg-perfil`), envolver o corpo em `<div id="emf"><emf-app>` e expor os blocos listados em `contracts/templates.md`.
- **FR-036**: `base.html` DEVE exibir mensagens do Django como alertas Bootstrap, título da página (`title_custom`, `title`, `view.title` ou `object`), o menu principal `menus/menu_main.yaml`, o menu de administração `menus/menu_administracao.yaml` dentro de `{% if perms.menu_administracao %}` e o menu de usuário (avatar via `avatar_user`, "Meu Perfil", "Sair" ou ícone de login).
- **FR-037**: Os templates `crud/list.html`, `crud/list_tabaux.html`, `crud/form.html`, `crud/ajax_form.html`, `crud/confirm_delete.html`, `crud/detail.html`, `crud/detail_detail.html`, `crud/detail_content_widget.html`, `crud/detail_column_widget.html`, `crud/format_options.html` e `paginacao.html` DEVEM existir com o comportamento descrito em `contracts/templates.md`; a resolução de template por view DEVE preferir `<app>/<model>_<sufixo>.html` e recorrer a `crud/<sufixo>.html`.
- **FR-038**: `index.html` DEVE mostrar o logotipo `imgs/logo_backend.svg` centralizado; `404.html` DEVE renderizar `<emf-error-404>`.

**Demonstração**

- **FR-039**: O app `utils` DEVE expor `TesteCrud(Crud)` com `model = Teste` e `public = [RP_LIST, RP_VIEW]` em `^teste/` (namespace `backend.utils`), com layout `Teste` em `_templates/utils/layouts.yaml` e template `_templates/utils/teste_list.html` (que inclui `crud/format_options.html` apenas quando `view.formats_impl` existe, o que não ocorre).

### Entidades-Chave

- **Crud**: configuração declarativa de um CRUD (modelo, views, permissões públicas, campos da listagem, contêiner, mestre-detalhe).
- **Layout YAML**: descrição de campos/colunas/legendas por modelo, base de formulários e detalhes.
- **Item de menu**: título, URL/rota, permissão exigida, classes CSS e filhos.
- **Teste** (modelo de demonstração, definido em `backend/utils/models.py`): um campo `teste` de texto; usado para demonstrar o CRUD.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: Declarar um CRUD completo para um novo modelo exige no máximo 3 elementos de código (classe `Crud` com `model`, entrada de layout YAML e inclusão de `get_urls()` em um `urls.py`) e resulta em 5 rotas funcionais.
- **SC-002**: 100% das telas de ação (criar/editar/excluir) respondem 302 ao login para visitantes anônimos quando `public` não as inclui; as telas listadas em `public` respondem 200.
- **SC-003**: `make_pagination` devolve, para 30 páginas, no máximo 10 posições (incluindo `None`) em todas as páginas atuais de 1 a 30.
- **SC-004**: O teste `backend/crud/tests.py::test_read_layout_from_yaml` passa e demonstra a regra de distribuição de larguras (soma de larguras de cada linha = 12 quando há campos sem largura).
- **SC-005**: Menus são renderizados sem erro 500 mesmo com YAML inexistente ou inválido (0 falhas de página causadas por menu).
- **SC-006**: Ordenar a listagem por qualquer índice de coluna (positivo ou negativo) nunca gera erro HTTP 500 e mantém a ordenação padrão do modelo como desempate.
- **SC-007**: Em `/`, o HTML contém o elemento `#emf`, `<emf-app>`, os menus principal e (para superusuário) administração, e o link de login para anônimos.

## Premissas

- **Dependências de outras features**: `001-fundacao-projeto-django` (configuração de `TEMPLATES` com `_templates`, crispy-forms/`bootstrap5`, `SearchModelMixin`, `normalize`, `Teste`), `002-autenticacao-usuarios-auditoria` (rotas `backend.eauth:*`, `avatar_user`, `UserCrud` como principal consumidor), `003-regras-permissoes-globais` (constantes `RP_*` e criação da permissão `list_<modelo>` para todo modelo).
- O pacote `backend.crud` **não** é app Django registrado em `INSTALLED_APPS`; suas classes e os templates (que vivem em `_templates/`) são usados como biblioteca. O `default_app_config` de `backend/crud/__init__.py` é residual e não tem efeito.
- O código do frontend Vue/Vite (`<emf-app>`, componentes `emf-*`) é coberto por `007-frontend-vite-vue`; WebSocket e mídia por outras features (`006`, `009`).
- A busca Solr/Haystack não é usada pela listagem do CRUD (a busca `q` é por `icontains` no campo `search`); Solr é tratado em `008-busca-solr-haystack`.
- O `MasterDetailCrud`, `CrudBaseForListAndDetailExternalAppView`, `Crud.build` e `container_field` fazem parte da biblioteca, porém **nenhum** modelo do esqueleto os usa; sua especificação decorre apenas da leitura do código (comportamentos de borda não foram exercitados em runtime).
- Os textos de interface são em pt-BR e traduzidos por `gettext_lazy`/`{% trans %}`.
