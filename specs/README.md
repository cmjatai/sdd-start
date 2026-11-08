# Especificações do sdd-start

Este diretório contém as especificações no molde do [Spec Kit](https://github.com/github/spec-kit) obtidas por **engenharia reversa** do código-fonte do esqueleto. A intenção é que, se o código não existisse, um LLM (ou uma pessoa) seguindo estas especificações **na ordem abaixo** chegaria ao estado atual do projeto, com o mesmo comportamento.

Os princípios que regem o projeto estão em [`.specify/memory/constitution.md`](../.specify/memory/constitution.md). Tudo é escrito em português do Brasil.

## Funcionalidades (ordem de construção)

| # | Pasta | Assunto | Depende de |
|---|---|---|---|
| 001 | [`001-fundacao-projeto-django`](001-fundacao-projeto-django/spec.md) | Projeto Django, settings modulares, ambiente, utilitários, mixins, testes e ferramentas de qualidade | — |
| 002 | [`002-autenticacao-usuarios-auditoria`](002-autenticacao-usuarios-auditoria/spec.md) | Usuário por e-mail, login, recuperação de senha, perfil, CRUD de usuários e auditoria | 001 |
| 003 | [`003-regras-permissoes-globais`](003-regras-permissoes-globais/spec.md) | Grupos, permissões por modelo, permissões públicas e sincronização pós-migração | 001, 002 |
| 004 | [`004-crud-generico-menus`](004-crud-generico-menus/spec.md) | CRUD genérico no servidor, layouts YAML, menus YAML e templates base | 001–003 |
| 005 | [`005-api-rest-automatica`](005-api-rest-automatica/spec.md) | API REST gerada dos modelos (`drfautoapi`), filtros, paginação, token/sessão e OpenAPI | 001–003 |
| 006 | [`006-sincronizacao-tempo-real`](006-sincronizacao-tempo-real/spec.md) | WebSocket (Channels), sincronização de modelos, Celery e demonstração | 001, 003, 005 |
| 007 | [`007-frontend-vite-vue`](007-frontend-vite-vue/spec.md) | Frontend Vue 3 + Vite integrado ao Django, PWA, estilos e componentes | 001, 004–006 |
| 008 | [`008-busca-solr-haystack`](008-busca-solr-haystack/spec.md) | Infraestrutura de busca Haystack + Solr (duas coleções) | 001 |
| 009 | [`009-midia-arquivos-avatar`](009-midia-arquivos-avatar/spec.md) | Mídia, campos de arquivo, avatar, miniaturas e entrega de arquivos | 001, 002 |
| 010 | [`010-docker-desenvolvimento`](010-docker-desenvolvimento/spec.md) | Imagem-base e ambiente Docker de desenvolvimento (várias instâncias) | 001–009 |
| 011 | [`011-docker-producao`](011-docker-producao/spec.md) | Imagem e ambiente Docker de produção (Nginx, Gunicorn, Daphne, Celery) | 001–010 |

## Estrutura de cada funcionalidade

```text
specs/NNN-nome/
├── spec.md          # O quê e por quê: histórias, requisitos, critérios de sucesso
├── plan.md          # Contexto técnico, verificação da constituição e detalhamento de implementação
├── research.md      # Decisões, alternativas e particularidades/dívidas técnicas observadas
├── data-model.md    # Modelos e estruturas de dados
├── contracts/       # Contratos externos (HTTP, WebSocket, YAML, variáveis de ambiente, Docker...)
├── quickstart.md    # Como validar a funcionalidade
└── tasks.md         # Roteiro de reconstrução em tarefas ordenadas
```

## Como usar

- **Reconstruir o projeto do zero** (repositório vazio com `.specify/`): execute `/speckit-implement` para cada funcionalidade, de `001` a `011`. Todas as tarefas de `tasks.md` estão **desmarcadas** (`[ ]`) de propósito: elas são o roteiro de reconstrução.
- **Neste repositório (código já existente)**: use `/speckit-analyze` para checar a consistência entre os artefatos e `/speckit-converge` para reconciliar o código com as especificações; não reexecute `/speckit-implement` sobre código já implementado sem revisar o impacto.
- **Evoluir o esqueleto**: crie uma nova funcionalidade com `/speckit-specify` (próximo número sequencial, `012-...`) e, se alterar comportamento descrito aqui, atualize a especificação correspondente na mesma entrega.
- Cada `research.md` traz a seção **Particularidades, dívidas técnicas e riscos observados**. O estado documentado é o do código atual (fidelidade); correções recomendadas aparecem ali como sugestões e devem virar novas funcionalidades.
