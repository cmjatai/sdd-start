# sdd-start

Projeto-esqueleto (*starter*) de uma aplicação **Django (backend) + Vite/Vue (frontend)**, totalmente integrada e funcional, pensada para ser o ponto de partida de novos sistemas desenvolvidos com **Spec-Driven Development (SDD)** usando o [Spec Kit](https://github.com/github/spec-kit).

O esqueleto sobe com um único comando e já traz, integrados e funcionando:

- Django 6 (ASGI + WSGI) com configurações modulares, usuário customizado autenticado por e-mail, auditoria, permissões por modelo e CRUD genérico renderizado no servidor;
- API REST gerada automaticamente a partir dos modelos (Django REST Framework), com documentação OpenAPI (Swagger/Redoc);
- Sincronização em tempo real via WebSocket (Django Channels + Redis);
- Tarefas assíncronas (Celery + Redis) e busca textual (Haystack + Solr);
- Frontend Vue 3 construído com Vite e servido pelo Django (`django-vite`), com PWA, Pinia e Bootstrap 5;
- Estratégia Docker para **desenvolvimento** (hot reload, várias instâncias em paralelo) e **produção** (Nginx + Gunicorn + Daphne + Celery em um único contêiner de aplicação).

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `backend/` | Projeto Django (pacote `backend`): `settings/` modular, `urls.py`, `asgi.py`, `wsgi.py`, `celery.py` e os apps `eauth`, `utils`, `api`, `globalrules`, `crud` |
| `drfautoapi/` | Biblioteca interna que constrói `ViewSet`s, `FilterSet`s e rotas DRF automaticamente a partir dos modelos |
| `_frontend/src/` | Código-fonte do frontend (Vue 3, Pinia, Vue Router, SCSS, Service Worker) |
| `_templates/` | Templates Django (base, CRUD, autenticação, menus em YAML) |
| `_docker/` | `dev/` e `prod/` (Dockerfiles, `docker-compose.yaml`, scripts de inicialização, Nginx) e `foundation/` (imagem-base) |
| `solr/` | *Configsets* do Solr das duas coleções (`arq1` e `arq2`) |
| `_tests/`, `conftest.py` | Testes com pytest e fixture `app` (django-webtest) |
| `__notebooks/` | Notebooks Jupyter com `django_setup.py` para explorar o projeto no shell |
| `specs/` | **Especificações Spec Kit (engenharia reversa do código atual)** — veja [specs/README.md](specs/README.md) |
| `.specify/` | Configuração, templates, scripts e constituição do Spec Kit |
| `.github/skills/` | Skills do Spec Kit para o GitHub Copilot (`/speckit-*`) |

## Pré-requisitos

- Docker e Docker Compose (os scripts usam `sudo docker compose`);
- Imagem-base `leandrojatai/building_foundation:0003` (definida em `_docker/foundation/Dockerfile`; pode ser construída localmente, veja o final desse arquivo);
- Para rodar fora do contêiner: Python >= 3.12 com [Poetry](https://python-poetry.org/) e Node.js 26.

## Executando em desenvolvimento

1. Crie o arquivo `backend/.env` (ignorado pelo Git) com, no mínimo, a chave secreta do Django:

   ```ini
   SECRET_KEY = troque-por-um-valor-aleatorio-longo
   ```

   O script `_docker/dev/start-dev.sh` completa/atualiza no `backend/.env` as demais variáveis (`DATABASE_URL_DEV`, `SOLR_URL`, `SOLR_COLLECTIONS`, `REDIS_HOST`, `DEBUG`, `DJANGO_VITE_DEV_MODE`, `FOLDER_DEBUG_CONTAINER`, `COMPOSE_PROJECT_NAME`, `TZ`).

2. Suba o ambiente (o nome do projeto Compose é opcional; o padrão é `startdev1`):

   ```bash
   ./rdev.sh [nome]     # derruba, ajusta permissões (chown) e sobe com --build -d
   ./uupdev.sh [nome]   # apenas sobe (up --build -d) com saída detalhada
   ./ddev.sh [nome]     # derruba e ajusta permissões
   ```

3. Acesse:

   | Serviço | Endereço |
   |---|---|
   | Aplicação (Django `runserver`) | <http://localhost:9099> (`APP_PORT` em `_docker/dev/.env_dev_compose`) |
   | Vite (HMR) | <http://localhost:5173> |
   | PostgreSQL | `localhost:5433` |
   | Redis | `localhost:6379` |
   | Solr / ZooKeeper embutido | `localhost:8983` / `localhost:9983` |

Para criar várias instâncias de desenvolvimento em paralelo, passe nomes diferentes aos scripts (`./rdev.sh startdev2`) e ajuste `APP_PORT` e as portas publicadas no `docker-compose.yaml`.

O frontend também pode ser executado fora do Docker com `./startfront-dev.sh` (`npm install` + `npm run dev`).

## Executando em produção

1. Ajuste `_docker/prod/.env_prod_compose` (senhas, `APP_PORT`, `SITE_URL` com o domínio público real).
2. Suba/derrube com:

   ```bash
   ./upprod.sh [nome]   # padrão: startprod1
   ./dprod.sh  [nome]
   ```

O contêiner `app` constrói o frontend (`npm run build`), roda `collectstatic`, gera a `SECRET_KEY` na primeira execução (persistida em `backend_data/secret.key`), aplica as migrações, prepara o Solr, inicia o Celery, o Gunicorn (WSGI), o Daphne (ASGI/WebSocket) e o Nginx na porta 80 do contêiner (publicada em `APP_PORT`, padrão `9001`).

## Comandos úteis

```bash
poetry install                       # dependências Python (inclui grupos dev/test)
npm install && npm run dev           # frontend com Vite
npm run build                        # build do frontend (_frontend/dist/frontend)
npm run lint && npm run format       # ESLint e Prettier
pytest                               # testes (pytest-django, --reuse-db, cobertura)
ruff check .                         # lint Python (regras E, F, I)
python manage.py migrate             # migrações (também cria permissões e grupos)
python manage.py createsuperuser     # usuário administrador (login por e-mail)
```

Endereços principais: `/` (início), `/login/`, `/system/` (Django Admin), `/admin/user/` (usuários), `/admin/auditlog` (auditoria), `/teste/` (CRUD de demonstração), `/wstest/` (demonstração de WebSocket), `/api/schema/swagger-ui/` e `/api/schema/redoc/` (documentação da API).

## Desenvolvimento orientado a especificações (Spec Kit)

Todas as especificações do projeto ficam em `specs/` e foram obtidas por **engenharia reversa** do código: seguindo-as em ordem, um LLM deve ser capaz de reconstruir o estado atual do projeto. O fluxo padrão para novas funcionalidades usa as skills em `.github/skills/`:

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` (e `/speckit-converge` para reconciliar código e especificação).

Os princípios do projeto estão em [`.specify/memory/constitution.md`](.specify/memory/constitution.md). **Toda documentação do projeto (README, especificações, planos, tarefas e constituição) é escrita em português do Brasil.**

## Imagem-base (opcional)

```bash
docker build -t building_foundation:0003 -f _docker/foundation/Dockerfile _docker/foundation
```

## Licença

[MIT](LICENSE)
