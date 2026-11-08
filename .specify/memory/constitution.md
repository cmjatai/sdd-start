# Constituição do sdd-start

## Princípios Fundamentais

### I. Backend Django modular e orientado a apps (INEGOCIÁVEL)

Todo o código de servidor vive no pacote `backend` (apps `eauth`, `utils`, `api`, `globalrules`, `crud`) e na biblioteca interna `drfautoapi`. Cada responsabilidade tem um app próprio, com `apps.py` e, quando aplicável, `models.py`, `urls.py`, `views.py`, `admin.py` e `services/` (sinais e tarefas Celery). Os apps do projeto são registrados em `backend/settings/apps.py` (`BACKEND_APPS`/`INSTALLED_APPS`). As configurações são divididas em módulos temáticos em `backend/settings/` (apps, auth, drf, email, frontend, languages, logs, medias, middleware, solr, zasyncs, zenv) e reunidas por `backend/settings/project.py`. Novas configurações devem entrar no módulo temático correspondente, nunca diretamente em `project.py`, salvo valores transversais.

### II. Configuração por ambiente, sem segredos no repositório

Toda configuração variável (modo, banco, Redis, Solr, chaves, fuso horário) é lida por `python-decouple` (`backend/settings/zenv.py`) a partir de variáveis de ambiente ou do arquivo `.env`, que nunca é versionado. `SECRET_KEY`, senhas e chaves de terceiros não podem ser escritos em código nem em arquivos versionados; em produção a `SECRET_KEY` é gerada no primeiro start e persistida no volume de dados. O comportamento de desenvolvimento e de produção é decidido por `DEBUG` (e `DJANGO_VITE_DEV_MODE`), nunca por ramificações de código espalhadas.

### III. Paridade entre desenvolvimento e produção via Docker

O ambiente padrão é o Docker Compose: `_docker/dev` (código montado como volume, `runserver`, Vite com HMR) e `_docker/prod` (imagem imutável com build do frontend, `collectstatic`, Nginx, Gunicorn, Daphne e Celery). Ambos usam os mesmos serviços de apoio (PostgreSQL 18 com pgvector, Redis, Solr 9.7) e a mesma imagem-base. Várias instâncias independentes devem poder coexistir apenas variando o nome do projeto Compose (`COMPOSE_PROJECT_NAME`), que prefixa contêineres, hosts, bancos e coleções Solr. Os scripts de raiz (`rdev.sh`, `uupdev.sh`, `ddev.sh`, `upprod.sh`, `dprod.sh`) são a interface oficial para subir e derrubar os ambientes.

### IV. API REST gerada, permissões por modelo

Toda entidade de dados dos apps do projeto é exposta automaticamente em `/api/<app>/<modelo>/` por `drfautoapi`, com paginação, filtros e ordenação padronizados e documentação OpenAPI. A autorização usa o modelo de permissões do Django estendido com `list_<modelo>` e a tabela de regras de `backend/globalrules` (grupos, permissões e permissões públicas de leitura). Alterações de regras de acesso são feitas em `globalrules/map_rules.py` e aplicadas automaticamente após `migrate`; nunca por dados manuais em produção.

### V. Frontend Vite integrado ao Django

O frontend (`_frontend/src`, Vue 3 + Pinia + Vue Router + Bootstrap 5) é construído pelo Vite e consumido pelo Django com `django-vite`; o Django continua dono das páginas, da autenticação por sessão e dos templates. O código do frontend segue ESLint + Prettier (sem ponto e vírgula, aspas simples, indentação de 2 espaços) e o alias `~@` aponta para `_frontend/src`. Componentes globais usam o prefixo `emf-`. O frontend se comunica com o backend apenas pela API `/api/` e pelo WebSocket `/ws/sync/`.

### VI. Tempo real e tarefas assíncronas por padrão

Mudanças em modelos sincronizáveis são propagadas aos navegadores por Django Channels (grupo `group_sync_refresh_channel`), respeitando as permissões de visualização de cada usuário. Trabalho pesado ou diferido usa Celery (broker Redis, resultados em banco, agendador `django_celery_beat`). Indexação em Solr é sempre assíncrona (processador de sinais `celery-haystack`).

### VII. Português do Brasil em tudo que o usuário e a equipe leem

Interface, mensagens, `verbose_name`, documentação, especificações, planos, tarefas, commits descritivos e comentários explicativos são escritos em português do Brasil (`LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = America/Sao_Paulo`). Textos de interface usam as funções de tradução do Django (`gettext_lazy`, `{% trans %}`). Identificadores de código seguem as convenções do ecossistema (inglês técnico), exceto nomes de domínio já em português (ex.: `eauth`, `globalrules`, `recuperar-senha`).

### VIII. Qualidade verificável

Todo comportamento novo deve ter teste automatizado com `pytest` (`pytest-django`, `model-bakery`, `django-webtest`; fixture `app` em `conftest.py`). O código Python segue `ruff` (regras `E`, `F`, `I`) e o código do frontend segue ESLint/Prettier. Dependências são gerenciadas por Poetry (`pyproject.toml`/`poetry.lock`) e npm (`package.json`/`package-lock.json`), e atualizadas semanalmente pelo Dependabot.

## Restrições Adicionais

- **Stack de referência**: Python >= 3.12 (imagem-base com 3.14), Django >= 6 e < 7, Django REST Framework, Channels/Daphne, Celery 5, PostgreSQL 18 (pgvector), Redis, Solr 9.7 (SolrCloud com ZooKeeper embutido), Node.js 26, Vite 8, Vue 3.5.
- **Banco de dados**: PostgreSQL é o único banco suportado em execução; SQLite é usado somente pela configuração `backend.settings.fake` durante o `collectstatic` na construção da imagem de produção.
- **Segurança**: `ALLOWED_HOSTS` e CORS são abertos no esqueleto e DEVEM ser restringidos por quem derivar o projeto para produção; senhas obedecem aos validadores padrão do Django (mínimo de 6 caracteres); a recuperação de senha usa reCAPTCHA configurável por ambiente; o Solr em produção usa autenticação básica gerada por `solr_cli.py`.
- **Mídia**: arquivos enviados ficam em `backend_media/media`, fora da árvore do código; em produção a entrega é feita pelo Nginx via `X-Accel-Redirect` e caminhos contendo `private` nunca são servidos publicamente.
- **Compatibilidade do esqueleto**: o projeto deve continuar subindo "do zero" com um único comando por ambiente e sem etapas manuais além de criar o `backend/.env` de desenvolvimento.

## Fluxo de Desenvolvimento

1. Toda funcionalidade nova nasce como especificação em `specs/NNN-nome-curto/` (numeração sequencial) criada com `/speckit-specify`, e segue `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`. Use `/speckit-converge` para reconciliar código e especificação.
2. Especificações descrevem o **quê** e o **porquê** (spec.md); decisões técnicas, modelos de dados, contratos e roteiros de validação ficam em `plan.md`, `research.md`, `data-model.md`, `contracts/` e `quickstart.md`.
3. As especificações de `specs/001` a `specs/011` descrevem o estado atual do código (engenharia reversa) e servem de linha de base: uma mudança que altere comportamento existente deve atualizar a especificação correspondente na mesma entrega.
4. Alterações passam por pull request; antes do merge devem passar `pytest`, `ruff check .`, `npm run lint` e a construção do frontend (`npm run build`).

## Governança

Esta constituição prevalece sobre quaisquer outras práticas do projeto. Emendas exigem: descrição da mudança e da motivação, atualização desta constituição com incremento de versão (semântico: MAJOR para remoção/redefinição incompatível de princípios, MINOR para novo princípio ou seção, PATCH para esclarecimentos), e revisão dos templates em `.specify/templates/` e das especificações afetadas. Todo plano (`plan.md`) deve conter uma Verificação da Constituição e justificar qualquer violação na tabela de Rastreamento de Complexidade. Orientações de uso diário estão em [README.md](../../README.md).

**Versão**: 1.0.0 | **Ratificada em**: 2026-11-08 | **Última Alteração**: 2026-11-08
