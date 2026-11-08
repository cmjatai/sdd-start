# Início Rápido: Regras e Permissões Globais

Pré-requisitos: ambiente de desenvolvimento da feature 010 no ar (ou `.venv` com PostgreSQL acessível conforme `backend/.env`), migrações das features 001/002 aplicadas.

## 1. Aplicar regras

```bash
python manage.py migrate
```

Saída esperada (trecho): `Atualizando grupos do Sistema:` seguido de `  Administrador do Sistema`; em `verbosity >= 2`, linhas `Adding permission '...'` na primeira execução. Reexecutar não deve gerar erros nem duplicar dados.

## 2. Verificar permissões e grupos

```bash
python manage.py shell -c "
from django.contrib.auth.models import Group, Permission
g = Group.objects.get(name='Administrador do Sistema')
print(g.permissions.count())   # 16
print(sorted(g.permissions.values_list('content_type__app_label', 'codename')))
print(Permission.objects.filter(codename='list_user').values_list('name', flat=True))  # Visualizaçao da lista de Usuários
print(Permission.objects.filter(codename__in=['menu_1', 'orcamento_1']).count())       # 2
"
```

## 3. Verificar permissões públicas

```bash
python manage.py shell -c "
from backend.globalrules.map_rules import rules_patterns_public as p
print(p)
from backend.globalrules import MAP_GROUPS_AND_PERMS as M
print(M.menu_administracao, M.GROUP_ADM_ADMIN)
"
```

Esperado: `{'eauth:user': set(), 'utils:teste': {'utils.list_teste', 'utils.view_teste'}, 'utils:metadata': set()}` e `menu_1 Administrador do Sistema`.

## 4. API

```bash
curl -i http://localhost:8000/api/utils/teste/         # 200 (leitura pública)
curl -i -X POST http://localhost:8000/api/utils/teste/ # 401/403
curl -i http://localhost:8000/api/eauth/user/          # 401/403
```

(Ajuste host/porta conforme `_docker/dev`.) Com sessão/token de superusuário, todas as rotas respondem normalmente.

## 5. Interface

1. Entrar como superusuário: o ícone de engrenagem (menu de administração) aparece no topo.
2. Entrar como usuário comum, mesmo no grupo "Administrador do Sistema": o menu **não** aparece (particularidade documentada em `research.md`, item 10).

## 6. Sequências de ids (PostgreSQL)

```bash
python manage.py shell -c "
from django.db import connection
from backend.utils.models import Teste
Teste.objects.create(id=500, teste='x')
"
python manage.py migrate
python manage.py shell -c "
from backend.utils.models import Teste
print(Teste.objects.create(teste='y').id)   # 501
"
```

## 7. Testes (pytest) que cobrem / deveriam cobrir

Executar: `pytest backend/globalrules -q` e `pytest _tests/test_initials.py -q`; lint: `ruff check backend/globalrules backend/api`.

| Teste | Verifica |
|---|---|
| `_tests/test_initials.py` (existente) | `globalrules/__init__.py` tem `default_app_config` apontando para `backend.globalrules.apps.AppConfig` |
| `test_rp_constants` | valores de `RP_*` |
| `test_map_groups_and_perms` | `MAP_GROUPS_AND_PERMS.menu_administracao == 'menu_1'`, presença de `GROUP_ADM_ADMIN`, `action_1` |
| `test_rules_patterns_public` | conteúdo exato de `rules_patterns_public` |
| `test_list_permission_created` | `Permission` `list_user`, `list_teste` existem |
| `test_update_groups_idempotent_and_clears` | grupo com 16 permissões; após `add` de permissão extra e `get_rules().update_groups()`, volta a 16 |
| `test_group_visitante_ignored` | nenhum grupo com nome vazio |
| `test_api_public_read` / `test_api_private` | `APIClient`: anônimo `GET /api/utils/teste/` 200, `POST` 401/403, `GET /api/eauth/user/` 401/403; usuário do grupo administrador `GET /api/eauth/user/` 200 |
| `test_backend_model_permissions_unit` | `has_permission` com view fake (queryset de `Teste`) |
| `test_reset_id_model` | com PostgreSQL de teste: após insert com id explícito, `reset_id_model(Teste)` faz o próximo id = max+1 |
| `test_menu_check_permission` | `resolve_urls_inplace` anula `url` sem permissão |
