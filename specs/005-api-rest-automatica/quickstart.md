# Guia Rápido: Validar a API REST Automática

Pré-requisitos: features `001`–`004` reconstruídas; ambiente de desenvolvimento no ar (Docker, `_docker/dev`, aplicação em `http://localhost:9099`) ou `python manage.py runserver` local; `python manage.py migrate` executado (cria `authtoken_token`, permissões e grupos); um superusuário (`python manage.py createsuperuser`, login por e-mail).

## 1. Verificações estáticas

```bash
ruff check drfautoapi backend/api backend/settings/drf.py
python manage.py check
python manage.py spectacular --file /dev/null   # gera o esquema sem erros/avisos fatais
```

## 2. Smoke manual (curl)

```bash
BASE=http://localhost:9099
# 2.1 versão (anônimo)
curl -s $BASE/api/version
# → {"name":"Backend","description":"Plataforma ...","version":"0.0.1"}

# 2.2 token
curl -s -X POST $BASE/api/auth/token -d 'username=admin@exemplo.com' -d 'password=<senha>'
# → {"token":"<chave>"}
TOKEN=<chave>

# 2.3 listagem paginada
curl -s -H "Authorization: Token $TOKEN" "$BASE/api/utils/teste/"
# → {"pagination":{...},"results":[...]}

# 2.4 criar / alterar / excluir
curl -s -X POST -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' -d '{"teste":"ana silva"}' $BASE/api/utils/teste/
curl -s -X PATCH -H "Authorization: Token $TOKEN" -H 'Content-Type: application/json' -d '{"teste":"ana maria silva"}' $BASE/api/utils/teste/1/
curl -s -X DELETE -H "Authorization: Token $TOKEN" $BASE/api/utils/teste/1/   # 204

# 2.5 filtros, ordenação, paginação
curl -s -H "Authorization: Token $TOKEN" "$BASE/api/utils/teste/?teste__icontains=silva%20ana&o=-id&page_size=5"
curl -s -H "Authorization: Token $TOKEN" "$BASE/api/utils/teste/?get_all=true"   # lista simples

# 2.6 sessão (cookie)
curl -s -c cj -X POST $BASE/api/auth/session -d 'username=admin@exemplo.com' -d 'password=<senha>'   # 200 {"detail":"Autenticação efetuada com sucesso!"}
curl -s -b cj $BASE/api/version        # inclui "user": {...}
curl -s -b cj -X DELETE $BASE/api/auth/session   # exige CSRF com cookie de sessão

# 2.7 recriar token (administrador)
curl -s -X POST -H "Authorization: Token $TOKEN" $BASE/api/recriar-token/1
```

Comportamentos esperados adicionais:

- Sem credenciais, `GET /api/eauth/user/` → `401`; usuário sem permissão → `403`.
- `GET /api/utils/teste/1.xyz` → `404`; `GET /api/utils/teste/1.json` → JSON.
- `?page_size=1000` devolve no máximo 100 itens; `?page=999` → `404`.
- `GET /api/eauth/user/` (superusuário) **contém** `password` (particularidade registrada em `research.md` #1).
- Abrir `/api/schema/swagger-ui/`, `/api/schema/redoc/` e `/api/schema/` no navegador; conferir a resposta paginada com `pagination` e `results`, e o título "Backend API - docs".

## 3. Testes automatizados (a criar em `backend/api/tests.py`; hoje vazio)

Executar: `pytest backend/api/tests.py` (usa `--reuse-db`, `-p no:warnings`, `--cov=.`).

| Teste | Verifica |
|---|---|
| `test_router_registra_modelos` | `ApiViewSetConstrutor.router().registry` contém `utils/teste` com basename `utils_teste`; `reverse('backend.api:utils_teste-list')` → `/api/utils/teste/` |
| `test_get_viewset_for_model` | devolve o ViewSet de `Teste` com `queryset.model is Teste` |
| `test_serializer_campos_extras` | resposta inclui `__str__`, `metadata` (`{}`), `link_detail_backend` |
| `test_paginacao_padrao` | 25 registros → 10 itens, `total_entries=25`, `total_pages=3`; `page_size=1000` → 25 (<100); com 150 registros, 100 |
| `test_get_all` | `?get_all=true` → lista sem `pagination` |
| `test_filtro_icontains_multiplo` | `?teste__icontains=ana silva` e com aspas |
| `test_filtro_ordenacao_o` | `?o=-teste`; `?o=` inválido não levanta exceção na camada de filtro |
| `test_filtro_lookups_gerados` | `ApiFilterSetMixin.get_fields()` de `Teste` contém `teste: [exact, icontains, ...]` e não contém `unaccent` |
| `test_permissoes_por_metodo` | anônimo `401`; sem permissão `403`; superusuário `200/201/204` |
| `test_token_e_sessao` | `/api/auth/token` devolve token e autentica; `/api/auth/session` POST/DELETE |
| `test_recria_token` | admin recebe novo token diferente do anterior; não-admin `403` |
| `test_version_anonimo_e_autenticado` | campos de `version` e `user.avatar == '/static/imgs/perfil.png'` sem avatar |
| `test_formato_desconhecido_404` | `/api/utils/teste/1.xyz` → `404` |
| `test_schema_e_docs` | `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/` → `200` |
| `test_split_string_char_filter` | unidade: divisão por espaços e aspas, valor vazio não filtra |
| `test_customize_e_wrapper` | `@customize` substitui o ViewSet; `@wrapper_queryset_response_for_drf_action` pagina/serializa |

Use `APIClient` (`rest_framework.test`) com `force_authenticate` e crie permissões/grupos conforme a feature 003.
