# Pesquisa e Decisões: Regras e Permissões Globais

## Decisões Técnicas

### D1. Tabela declarativa de regras em Python (`map_rules.py`)

- **Decisão**: regras de acesso são dados Python (`rules_patterns`: lista de `{"group", "rules": [(modelo, perms, perms_publicas)]}`) reaplicados a cada `migrate`.
- **Justificativa**: versionada em Git, revisável em PR, reprodutível entre dev/prod (Constituição IV: "nunca por dados manuais em produção"). O terceiro item da tupla permite derivar a lista de permissões públicas da API sem outra tabela.
- **Alternativas**: permissões editadas no admin (não reprodutíveis); fixtures/data migrations (acopladas a ids e ordem de migração); JSON/YAML externo (perde o uso direto de classes de modelo).

### D2. Prefixos `RP_*` com ponto inicial e sublinhado final (`'.list_'`)

- **Decisão**: `RP_LIST='.list_'` etc. são "radicais" que, combinados com o `model_name` (`t[1:] + model_name`) ou com `app_label` + radical + `model_name` (`app_label + '.list_' + model_name`), geram `list_user` ou `eauth.list_user`.
- **Justificativa**: o mesmo radical serve para o `codename` (Group) e para o nome completo (`has_perm`), e distingue radicais de `codename`s literais (`menu_1`) por `t[0] == '.' and t[-1] == '_'`.
- **Alternativas**: funções construtoras de nomes; strings completas por modelo (verboso).

### D3. Sincronização de grupos em `post_migrate` com `clear()` + reatribuição

- **Decisão**: `_config_group` limpa e reatribui as permissões do grupo a cada `migrate`.
- **Justificativa**: a tabela é a fonte da verdade; garante idempotência e remove permissões revogadas.
- **Alternativas**: apenas adicionar (acumularia permissões obsoletas); comando de gerenciamento separado (exigiria etapa manual — contraria a Constituição, "sem etapas manuais").

### D4. Substituir o receptor `create_permissions` do Django pelo mesmo `dispatch_uid`

- **Decisão**: `create_proxy_permissions` reutiliza `dispatch_uid='django.contrib.auth.management.create_permissions'`.
- **Justificativa**: precisa criar `list_<modelo>` (e permissões de modelos proxy) junto com as padrão no mesmo passo; como `backend.globalrules.apps` é importado na fase 1 do `populate`, antes do `ready()` do `auth`, o receptor nativo é descartado (verificado: `post_migrate.receivers` contém uma única entrada com esse `dispatch_uid`).
- **Alternativas**: receptor adicional com `dispatch_uid` próprio (simples e mais seguro; manteria o nativo funcionando); declarar `list_` em `Meta.permissions` de cada modelo (invasivo, não cobre modelos de terceiros).

### D5. Permissões públicas por modelo compartilhadas entre API e WebSocket

- **Decisão**: um único mapa `rules_patterns_public` (`"app:modelo"` → conjunto de nomes completos) é lido por `BackendModelPermissions` e por `SyncRefreshConsumer`.
- **Justificativa**: consistência entre o que a API e o tempo real revelam a anônimos.
- **Alternativas**: atributo por view/serializer (espalhado); `AllowAny` em views específicas (não granular por método).

### D6. Ajuste de sequências por SQL específico do PostgreSQL, tolerante a falhas

- **Decisão**: `reset_id_model` usa `pg_get_serial_sequence` + `setval` e recria a sequência se não houver vínculo; falhas são ignoradas.
- **Justificativa**: cargas e restaurações com ids explícitos deixam a sequência atrás do `max(id)`; o ajuste automático evita erro de chave duplicada sem etapa manual. O `except:` nu mantém o `migrate` robusto em tabelas sem `id` e em bancos não PostgreSQL (SQLite do `collectstatic` em `backend.settings.fake`).
- **Alternativas**: `manage.py sqlsequencereset` (manual); tratar o dialeto explicitamente (`connection.vendor == 'postgresql'`).

### D7. `models.py` vazio no app

- **Decisão**: manter `models.py` vazio.
- **Justificativa**: `emit_post_migrate_signal` só envia o sinal para apps com `models_module`; sem `models.py` o `update_groups` nunca executaria. Por ser o último app em `INSTALLED_APPS`, seu `post_migrate` roda depois dos demais.

### D8. Importações tardias de modelos

- **Decisão**: `get_rules()` importa `Group`, `Permission`, `ContentType` e `map_rules` internamente; o consumer importa `map_rules` em `__init__`.
- **Justificativa**: `map_rules.py` importa modelos (`User`, `Teste`, `Metadata`) e `__init__.py` deve ser importável por `eauth/models.py` sem ciclo.

## Particularidades, dívidas técnicas e riscos observados

Recomendação geral: **o estado atual é replicar para fidelidade**; a coluna "Recomendação" indica o que uma evolução futura deveria fazer.

| # | Observação (confirmada no código) | Risco / efeito | Recomendação |
|---|---|---|---|
| 1 | `update_groups` faz `group.permissions.clear()` e reatribui a cada `migrate`. | Ajustes manuais no admin em grupos gerenciados são perdidos; há uma janela entre `clear()` e `add()` sem permissões. | Replicar (é intencional: tabela = fonte da verdade). Documentar. |
| 2 | `GROUP_VISITANTE = ''` é ignorado por `_config_group` (`if not group_name: return`); `rules_group_visitante` tem `rules: []`. | Placeholder sem efeito; qualquer grupo com nome vazio é silenciosamente ignorado. | Replicar. |
| 3 | `VARS` varre `locals()` do módulo por prefixos `GROUP_`, `action_`, `menu_`. | Variável nova fora desses prefixos não entra em `MAP_GROUPS_AND_PERMS`; `PERMS_FOR_USERS_DICT` mistura rótulos (`menu_1`→'Mostrar Menu 1') e nomes de variáveis (`menu_administracao`→'menu_1') no mesmo dicionário. | Replicar; documentar convenção de prefixos. |
| 4 | `reset_id_model` só funciona em PostgreSQL, usa `django.db.connection` (default) em vez de `using`, interpola o nome da tabela com `%` (SQL por string) e engole tudo com `except:` nu. | Falhas ocultas; não há SQL injection explorável pois o nome vem de `Meta.db_table`, mas é frágil; em transação quebrada o erro é mascarado. | Replicar para fidelidade; corrigir: checar `connection.vendor`, usar `using`, `except Exception` com log. |
| 5 | `create_proxy_permissions` substitui o `create_permissions` nativo pelo `dispatch_uid` duplicado e importa `_get_all_permissions` (API privada do Django). | Dependência de ordem de importação e de API interna; atualização do Django pode quebrar. | Replicar; corrigir: `dispatch_uid` próprio e receptor adicional. |
| 6 | O receptor muta `opts.permissions` com `tuple(set(...))`. | Ordem não determinística de `Meta.permissions`; efeito colateral apenas em memória, durante o processo de `migrate`. | Replicar. |
| 7 | O nome da permissão tem erro de grafia: "Visualizaçao da lista de" (sem til). | Nome persistido em `auth_permission.name` (visível no admin). | Corrigir para "Visualização" se aceitável alterar dados existentes (recomendado); fidelidade atual: replicar. |
| 8 | `associar` captura `ContentType.DoesNotExist` com `except:` nu e `Permission.objects.get` lança `DoesNotExist` se a permissão não existir; a exceção aborta as regras restantes do grupo (capturada em `_config_group`). | Uma permissão inexistente (erro de digitação em `map_rules.py`) apenas gera log/print e deixa o grupo incompleto sem falhar o `migrate`. | Replicar; corrigir: falhar alto ou logar com nível `error` e continuar nas demais regras. |
| 9 | `update_groups` usa `print` com sequências ANSI e `print(' ', group_name)` em vez de `logger`. | Ruído na saída; ANSI em logs. | Replicar. |
| 10 | `{% if perms.menu_administracao %}` (base.html) resolve para `user.has_module_perms('menu_administracao')`; `check_permission: menu_administracao` nos YAML resolve para `user.has_perm('menu_administracao')`; `list_tabaux.html` usa `perms.eauth.menu_administracao`. Nenhum é o código real (`eauth.menu_1`). | Para não superusuários, o menu de administração e os itens com `check_permission` **nunca** aparecem, mesmo para o grupo "Administrador do Sistema" (que tem `eauth.menu_1`); apenas superusuários ativos veem. | Replicar para fidelidade; corrigir: usar `perms.eauth.menu_1` e `check_permission: eauth.menu_1`. |
| 11 | O consumer consulta `<app>.detail_<modelo>`, permissão que nunca é criada. | O `or view_` mascara; `detail_` é código morto na prática (para usuários autenticados sempre falha e cai em `view_`). | Replicar; corrigir: criar `detail_` ou removê-lo. |
| 12 | O consumer envia sempre o evento e só remove `instance`; `u` pode ser `None` (falha → mensagem `error`). | Vaza a existência de mudanças (`app`, `model` e demais campos da mensagem) a qualquer cliente conectado, inclusive anônimo. | Replicar; corrigir: não enviar o evento sem permissão. |
| 13 | `ContainerPermission` não é usada em lugar algum e quebra se a view não tiver `.queryset` (usa `view.queryset.model`). | Código morto; retorna sempre `True`. | Replicar ou remover. |
| 14 | `BackendModelPermissions` exige `list_` E `view_` em `GET`; públicas só liberam se **ambas** forem públicas. | Públicas parciais exigem login. | Replicar. |
| 15 | `has_permission` não trata permissões por objeto; `OPTIONS`/`HEAD` seguem a regra de `GET`. | Sem permissão por instância. | Replicar. |
| 16 | `__init__.py` define `default_app_config`, ignorado pelo Django >= 4.1; mantido por `_tests/test_initials.py`. | Ruído. | Replicar (o teste exige). |
| 17 | `__base_change__` e `__perms_publicas__` em `map_rules.py`, `BACKEND_GROUPS`, `groups_add_user`, `groups_remove_user` e `action_1` não têm uso interno. | Código morto/pontos de extensão. | Replicar. |
| 18 | `_get_registration_key` define a chave `app_label:model_name`; `eauth:user` usa o `app_label` do `User` customizado (`eauth`). | Se o `AUTH_USER_MODEL` mudar, a chave muda. | Replicar. |
| 19 | O app não possui testes próprios (`backend/globalrules` sem `tests.py`; `backend/api/tests.py` é o stub padrão). | Risco de regressão. | Corrigir: testes planejados em `tasks.md`. |
| 20 | O nome do grupo é string lazy (`gettext_lazy`) usada como `name` do `Group`. | Se existir catálogo de tradução, o nome persistido depende do idioma ativo durante `migrate`. Hoje não há catálogo; `LANGUAGE_CODE = "pt-br"`. | Replicar; corrigir: usar `str` fixa para identidade do grupo. |
| 21 | Não há permissões para a ação `orcamento_1` ('Ação 1') em nenhum grupo; `menu_1` só é atribuída via regra de `User`. | `eauth.orcamento_1` existe, mas ninguém a recebe por regra. | Replicar. |
