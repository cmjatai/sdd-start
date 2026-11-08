---

description: "Lista de tarefas para reconstruir a funcionalidade Frontend Vite + Vue 3 integrado ao Django"
---

# Tarefas: Frontend Vite + Vue 3 integrado ao Django

**Entrada**: Documentos de design em `/specs/007-frontend-vite-vue/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de usuário), research.md, data-model.md, contracts/ (`vite-django-integracao.md`, `componentes-e-rotas.md`). Features 001–006 devem estar reconstruídas (settings modulares, `django_vite` em `INSTALLED_APPS`, API `/api`, tempo real).

**Testes**: Não há testes JS no projeto. A validação é por `npm run lint`, `npm run build` e testes `pytest` de renderização (ver `quickstart.md`).

**Organização**: As tarefas são agrupadas por história de usuário (US1…US8, conforme `spec.md`). Todas as tarefas estão desmarcadas: este arquivo é um roteiro de reconstrução.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: A qual história de usuário esta tarefa pertence (US1…US8)
- Caminhos relativos à raiz do repositório; detalhes de cada item na seção correspondente do `plan.md` ("Detalhamento de Implementação")

## Convenções de Caminhos

- Aplicação web: Django em `backend/` e `_templates/`; frontend em `_frontend/src/` (root do Vite); `package.json`, `vite.config.js`, `eslint.config.js` na raiz.

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: Inicialização do projeto npm e ferramentas de qualidade

- [ ] T001 Criar `package.json` (`name: "customfront"`, `version: "0.1.0"`, `type: "module"`, scripts `dev`, `build`, `preview`, `lint`, `format`) com dependências e devDependencies das versões do `plan.md` (Contexto Técnico) e executar `npm install` para gerar `package-lock.json`
- [ ] T002 [P] Criar `.prettierrc.json` (`semi: false`, `singleQuote: true`, `arrowParens: "avoid"`, `$schema`) — plan.md §4
- [ ] T003 [P] Criar `.editorconfig` (seção `[*.{js,jsx,mjs,cjs,ts,tsx,mts,cts,vue}]`, UTF-8, 2 espaços, newline final, trim) sem `root = true` — plan.md §4
- [ ] T004 [P] Criar `eslint.config.js` (flat config: globais `EventBus`/`bootstrap`, ignores `dist`, `js.configs.recommended`, `skipFormatting`, `flat/strongly-recommended`, `vue/multi-word-component-names: off`) — plan.md §3
- [ ] T005 [P] Garantir `.gitignore` com `node_modules/` e `dist/` (e `package-lock.json` versionado)
- [ ] T006 [P] Criar `startfront-dev.sh` (`#!/usr/bin/env bash`, `npm install`, `npm run dev`) e torná-lo executável (`chmod +x`) — plan.md §16
- [ ] T007 Criar a árvore `_frontend/src/{js/{stores/pinea,utils/{colormodes,scrollheader,resources}},views,components/utils/message,scss/custom,assets/imgs/icons}` e copiar para `_frontend/src/assets/` os ativos (favicon, logos, ícones PWA, pacote `bootstrap-icons`) — plan.md §15

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: Configuração do Vite e integração mínima com o Django, necessárias a todas as histórias

**⚠️ CRÍTICO**: Nenhuma história pode começar antes desta fase

- [ ] T008 Criar `backend/settings/frontend.py` com `TEMPLATES`, `CRISPY_*`, `STATIC_URL`, `STATIC_ROOT`, `DJANGO_VITE_ASSETS_PATH`, `STATICFILES_DIRS`, `DJANGO_VITE_DEV_MODE` (E lógico com `DEBUG`) e `DJANGO_VITE` — plan.md §5, contracts/vite-django-integracao.md §5
- [ ] T009 Importar `from .frontend import *` em `backend/settings/project.py`, garantir `django_vite` e `django.contrib.staticfiles` em `backend/settings/apps.py` e `DJANGO_VITE_DEV_MODE=False` + `manifest_path` de `dist` em `backend/settings/fake.py`; adicionar `django-vite ^3.2.0` ao `pyproject.toml`
- [ ] T010 Criar `vite.config.js` base: constantes, `loadEnv`, `root`, `base` por modo, `publicDir`, `resolve` (extensões, alias `~@` e `vue → vue/dist/vue.esm-bundler.js`), `esbuild.pure`, `server`, `build` (`outDir`, `assetsDir: ''`, `manifest`, `emptyOutDir`, `copyPublicDir`, `target`, `minify`, `sourcemap`, `rollupOptions.input`) — plan.md §2
- [ ] T011 Adicionar ao `vite.config.js` os plugins na ordem: `vue()`, `inject` (`$`, `jQuery`, `_`), `eslintPlugin` (`failOnError: true`), `Components` com `BootstrapVueNextResolver` (PWA e pós-build entram nas fases US5/US2)
- [ ] T012 Criar `_frontend/src/scss/custom/bootstrap.scss`, `_frontend/src/scss/header.scss` e `_frontend/src/scss/styles.scss` mínimos (imports do Bootstrap, `bootstrap-vue-next`, `bootstrap-icons` com `$bootstrap-icons-font-dir`) — plan.md §14
- [ ] T013 Criar `_frontend/src/main.js` com a ordem de inicialização do plan.md §7 (polyfill, estilos, bootstrap, FontAwesome, axios, `createApp` com `delimiters ['[[',']]']`, `provide`/`$EventBus`, `use(router/pinia/bootstrap)`, `mount('#emf')`, `globalComponents`, registro do SW condicional)
- [ ] T014 [P] Criar `_frontend/src/registerComponents.js` (`rootComponents`, `globalComponents`) — plan.md §11, contracts/componentes-e-rotas.md §1
- [ ] T015 [P] Criar `_frontend/src/js/routers.js` (`createWebHistory`, rotas `index_link` e `error_404`) — contracts/componentes-e-rotas.md §2
- [ ] T016 [P] Criar `_frontend/src/js/utils/index.js` (importa `./colormodes` e `./scrollheader`) e stubs vazios dos utilitários, a preencher em US4/US6
- [ ] T017 Criar `_frontend/src/App.vue` (`<slot />`, `<DisplayMessage />`, `<div id="modalApp">`; `useSyncStore().initialize()`, `registerModels('utils', ['teste'])`, `useAuthStore().loginStatus()`) — plan.md §11 (depende das stores da feature 006 e de T014/T015)
- [ ] T018 Atualizar `_templates/base.html`: `{% load … django_vite %}`, `{% vite_hmr_client %}`, `{% vite_asset 'main.js' %}`, `<div id="emf"><emf-app>…</emf-app></div>`, `<html data-bs-theme="auto" lang="pt-br">`, `<svg>` de símbolos e `{% if not DEBUG %}<link rel="manifest" href="/manifest.json">{% endif %}` — plan.md §6

**Ponto de Controle**: Fundação pronta; `npm run build` ainda pode falhar até a US2 (plugin pós-build) e as views/componentes serem criados

---

## Fase 3: História de Usuário 1 - Desenvolver o frontend com recarga a quente (Prioridade: P1) 🎯 MVP

**Objetivo**: Vite em desenvolvimento servido por `django-vite` com HMR.

**Teste Independente**: Com `DEBUG=True` e `DJANGO_VITE_DEV_MODE=True`, `./startfront-dev.sh` e `curl http://localhost:9099/` contêm `5173/static/@vite/client` e `5173/static/main.js`.

### Testes da História de Usuário 1

- [ ] T019 [P] [US1] Teste pytest em `backend/tests.py` (ou `tests/test_frontend.py`) validando `settings.DJANGO_VITE["default"]["dev_mode"]` e as tags `@vite/client`/`main.js` na resposta de `/` com `DEBUG=True` e `DJANGO_VITE_DEV_MODE=True` (quickstart §6)

### Implementação da História de Usuário 1

- [ ] T020 [US1] Conferir em `vite.config.js` o `server` (`host '0.0.0.0'`, `port 5173`, `open false`, `Service-Worker-Allowed: /`, `watch.usePolling: true`) e `base: '/static/'` em dev
- [ ] T021 [US1] Conferir em `backend/settings/frontend.py` a inclusão de `_frontend/src/assets` em `STATICFILES_DIRS` quando `DEBUG=True`
- [ ] T022 [US1] Executar `./startfront-dev.sh` e validar o HMR e o cenário de erro de lint (erro de ESLint falha o módulo; warning apenas emite) — quickstart §3

**Ponto de Controle**: US1 funcional e testável de forma independente

---

## Fase 4: História de Usuário 2 - Servir o frontend compilado em produção (Prioridade: P1)

**Objetivo**: `npm run build` produz `dist/frontend` com manifesto ajustado.

**Teste Independente**: `npm run build` gera `.vite/manifest.json` com todas as chaves `file`/`css`/`assets` iniciadas por `frontend/`.

### Testes da História de Usuário 2

- [ ] T023 [P] [US2] Teste pytest verificando que, com `DEBUG=False`, `DJANGO_VITE_DEV_MODE` é `False` e `manifest_path` termina em `frontend/.vite/manifest.json` (settings) — quickstart §4
- [ ] T024 [P] [US2] Verificação por comando (quickstart §2): ausência de `.map`, de `console.log`/`console.debug` nos chunks e prefixo `frontend/` em 100% das entradas

### Implementação da História de Usuário 2

- [ ] T025 [US2] Implementar `manualChunks(id)` em `vite.config.js` (nome do pacote; segundo segmento para `fortawesome`) e `chunkFileNames: undefined` — plan.md §2
- [ ] T026 [US2] Implementar o plugin inline `postbuild-commands` (`closeBundle`, somente `command === 'build'`) que prefixa `frontend/` em `file`, `css` e `assets` e regrava o manifesto — contracts/vite-django-integracao.md §4
- [ ] T027 [US2] Criar as views/componentes referenciados (T030, T031, T046, T049, T050) e executar `npm run build`; conferir a saída (`main-<hash>.js/css`, `manifest.json`, `service-worker.js`)
- [ ] T028 [US2] Executar `collectstatic` com `DEBUG=False` e conferir `collectedstatic/frontend/.vite/manifest.json` e a página `/` com `/static/frontend/main-<hash>.js`, sem `5173`

**Ponto de Controle**: US1 e US2 funcionais; MVP de build entregue

---

## Fase 5: História de Usuário 3 - Páginas Django hospedam a aplicação Vue (Prioridade: P1)

**Objetivo**: Vue montado em `#emf` sobre o HTML do Django.

**Teste Independente**: Em `/`, `#emf > emf-app` renderizado com slot, `#modalApp` presente, `{{ }}` preservado para o Django e `[[ ]]` interpretado pelo Vue.

- [ ] T029 [P] [US3] Criar `_frontend/src/js/stores/TeleportStore.js` (`export const activeTeleportId = ref(null)`)
- [ ] T030 [P] [US3] Criar `_frontend/src/components/utils/message/Alert.vue` (`alert alert-info fade show alert-dismissible` + `btn-close`; `name: 'Alert'`) — plan.md §13
- [ ] T031 [P] [US3] Criar `_frontend/src/components/utils/RefreshPage.vue` (props `timeout`/`show`/`enabled`, `displayTime`, `startTimer`, `clearTimers`, estilo *scoped*) — plan.md §13
- [ ] T032 [US3] Validar em `main.js`: cabeçalhos do axios (`xsrfCookieName`, `xsrfHeaderName`, `Cache-Control`, `Pragma`, `Expires`), instâncias de `bootstrap.Popover` para `[data-bs-toggle="popover"]` e registro de `fas`/`far`/`fab` + `dom.watch()`
- [ ] T033 [US3] Verificar manualmente (quickstart §5) a montagem, os delimitadores, `<emf-alert>` e `<emf-refresh-page>` em um template Django de teste e remover o template de teste

**Ponto de Controle**: US1–US3 funcionais (todas P1)

---

## Fase 6: História de Usuário 4 - Alternar tema claro, escuro ou automático (Prioridade: P2)

**Objetivo**: Tema claro/escuro/auto persistido.

**Teste Independente**: Alternar `#bd-theme` altera `html[data-bs-theme]` e `localStorage.theme` e persiste ao recarregar.

- [ ] T034 [US4] Implementar `_frontend/src/js/utils/colormodes/index.js` (IIFE: `getStoredTheme`, `setStoredTheme`, `getPreferredTheme`, `setTheme`, `showActiveTheme`, listener `matchMedia`, `DOMContentLoaded` + cliques em `[data-bs-theme-value]`; cabeçalho de licença CC BY 3.0) — plan.md §9
- [ ] T035 [US4] Adicionar ao rodapé de `_templates/base.html` o seletor `div.color-modes.dropup` com `#bd-theme`, `#bd-theme-text` e os três `button[data-bs-theme-value]` (`light`, `dark`, `auto` ativo) e os símbolos `check2`, `circle-half`, `moon-stars-fill`, `sun-fill` — plan.md §6
- [ ] T036 [P] [US4] Adicionar em `styles.scss` as regras `.bi.theme-icon`, `.color-modes` e `@include color-mode(dark)` correspondentes
- [ ] T037 [US4] Validar cenários: sem tema salvo + sistema escuro; clique em Light/Dark/Auto; mudança de `prefers-color-scheme` com tema `auto` e com tema fixo — quickstart §5

**Ponto de Controle**: US4 funcional

---

## Fase 7: História de Usuário 5 - Instalar e usar como PWA (Prioridade: P2)

**Objetivo**: Manifesto PWA e service worker em produção.

**Teste Independente**: Em produção, `/manifest.json` e `/service-worker.js` existem; SW ativo com escopo `/`.

- [ ] T038 [US5] Adicionar `VitePWA({...})` ao `vite.config.js` logo após `vue()` (estratégia `injectManifest`, `manifestTransforms` com prefixo `/static/frontend/`, manifesto `br.leg.go.jatai.sddstart`, ícones por modo) — plan.md §2 e §8, data-model.md §4
- [ ] T039 [P] [US5] Criar `_frontend/src/service-worker.js` (`precacheAndRoute(self.__WB_MANIFEST)`, `skipWaiting` no `install`, `clients.claim` no `activate`) — plan.md §8
- [ ] T040 [P] [US5] (Fidelidade) Criar `_frontend/src/sw.js` legado não utilizado, conforme research P4
- [ ] T041 [US5] Conferir em `main.js` o registro de `/service-worker.js` (`scope: '/'`, `type: 'module'`) somente com `'serviceWorker' in navigator && import.meta.env.PROD`
- [ ] T042 [US5] Conferir `<link rel="manifest" href="/manifest.json">` condicionado a `not DEBUG` em `_templates/base.html` e validar no DevTools (manifesto, ícones 192/512, SW ativo) — quickstart §5

**Ponto de Controle**: US5 funcional

---

## Fase 8: História de Usuário 6 - Identidade visual, cabeçalho e página 404 (Prioridade: P2)

**Objetivo**: Estilos da marca, cabeçalho rolável e 404.

**Teste Independente**: `#header-main` recebe `header-scrolled` ao rolar; `/rota-inexistente/` exibe `emf-error-404`.

- [ ] T043 [US6] Implementar `_frontend/src/js/utils/scrollheader/index.js` (IIFE; `DOMContentLoaded` + `setTimeout` 2000 ms; `checkScroll` com `scrollY > 0`; no-op sem `#header-main`) — plan.md §10
- [ ] T044 [P] [US6] Completar `_frontend/src/scss/styles.scss`: fontes do Google, variáveis da marca, `$utilities` (`min-viewport-height`, `avatar`), `$grid-gutter-width`, `$yellow`, seções `a`, `main`, `footer`, `.text-right`, `.nav-pagination`, `[id*=helptext]`, `.context-actions`, `.container-table`, `.container-login`, `@media` ≥768/992/1200 e `print` — plan.md §14
- [ ] T045 [P] [US6] Completar `_frontend/src/scss/header.scss` (`header`, `.navbar-topo`, `.header-scrolled`, modo escuro, mobile/desktop) e criar `_frontend/src/scss/_icon-list.scss` (parcial não importada)
- [ ] T046 [P] [US6] Criar `_frontend/src/views/Error404.vue` (`.http-404`, logo, `h1.error-code`, título, mensagem, `a.home-button`, estilos *scoped*) — plan.md §13
- [ ] T047 [US6] Criar `_templates/404.html` (`{% extends 'base.html' %}` + `<emf-error-404>` em `base_content`) e conferir a rota `error_404`
- [ ] T048 [US6] Teste pytest: resposta 404 contém `<emf-error-404>` (quickstart §6) e validação manual da rolagem do cabeçalho

**Ponto de Controle**: US6 funcional

---

## Fase 9: História de Usuário 7 - Consumir a API REST e o estado de autenticação (Prioridade: P3)

**Objetivo**: Cliente axios único e `authStore`.

**Teste Independente**: `Resources.Utils.getVersion()` envia `GET /api/version`; `authStore.loginStatus()` preenche `data_connect`.

- [ ] T049 [US7] Implementar `_frontend/src/js/utils/resources/index.js` (`basePath = '/api'`, padrões do axios, `Utils.{login, logout, hasPermission, getVersion, fetch, patchModel, putModel, postModel, deleteModel}`) — plan.md §12, contracts/componentes-e-rotas.md §3
- [ ] T050 [US7] Implementar `_frontend/src/js/stores/pinea/AuthStore.js` (`defineStore('authStore')`, `data_connect`, getters e ações) — data-model.md §6.1
- [ ] T051 [P] [US7] Criar `_frontend/src/components/utils/Markdown.vue` (`markdown-it` + plugins `abbr`, `anchor`, `footnote`, `highlightjs`, `sub`, `sup`, `task-lists`, `toc-done-right`; prop `source`)
- [ ] T052 [P] [US7] (Fidelidade) Criar `_frontend/src/components/utils/JsonViewer.vue` legado, mantendo o import quebrado conforme research P1, sem registrá-lo em `registerComponents.js`
- [ ] T053 [US7] Validar no console do navegador: `getVersion`, `loginStatus` e `hasPermission` (retorna `false`, research P2/P3)

**Ponto de Controle**: US7 funcional

---

## Fase 10: História de Usuário 8 - Qualidade de código do frontend (Prioridade: P3)

**Objetivo**: ESLint + Prettier + EditorConfig verificados.

**Teste Independente**: `npm run lint`, `npm run format` e `npm run build` sem erros em clone limpo.

- [ ] T054 [US8] Executar `npm run lint` e corrigir os erros remanescentes em `_frontend/src/` (ESLint com `failOnError: true` quebra o build)
- [ ] T055 [US8] Executar `npm run format` (Prettier) e reexecutar `npm run lint`
- [ ] T056 [US8] Executar `npm run build` em um clone limpo (`rm -rf node_modules && npm install && npm run build`) e confirmar SC-001
- [ ] T057 [P] [US8] Confirmar que `.editorconfig` e `.prettierrc.json` estão no formato do plan.md §4

---

## Fase 11: Acabamento e Preocupações Transversais

**Propósito**: Verificações finais e documentação

- [ ] T058 [P] Executar `ruff check` e `pytest` para os arquivos Python tocados (`backend/settings/frontend.py`, testes)
- [ ] T059 [P] Conferir que nenhum segredo foi adicionado a `vite.config.js`, `package.json` ou `_frontend/src/`
- [ ] T060 [P] Documentar o fluxo (`npm run dev`, `npm run build`, variáveis `DJANGO_VITE_DEV_MODE`/`DEBUG`) na documentação do projeto, se existir
- [ ] T061 Executar a validação completa do `quickstart.md` (§1–§5) em dev e em produção

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: sem dependências
- **Fundacional (Fase 2)**: depende da Preparação; BLOQUEIA todas as histórias
- **US1, US2, US3 (P1)** → **US4, US5, US6 (P2)** → **US7, US8 (P3)**; todas dependem da Fundacional e podem ser paralelizadas
- **Acabamento (Fase 11)**: depende das histórias desejadas

### Dependências entre Histórias e Tarefas

- T013 depende de T014, T015, T016 e T012 para compilar; T017 depende da feature 006 (`SyncStore`, `DisplayMessage`) e de T050 (`AuthStore`)
- T027 (build completo) depende de T030, T031, T046, T049, T050 e das stubs de T016; execute-o após essas tarefas
- US5 (T038) pode ser feita após T010/T011; ESLint (T004) deve existir antes do primeiro `npm run build`
- T054–T056 devem ser a última verificação antes do Acabamento

### Oportunidades de Paralelismo

- T002–T006 em paralelo; T014–T016 em paralelo; T029–T031 em paralelo; T044–T046 em paralelo

## Exemplo de Paralelismo: Fundacional

```bash
Task: "Criar _frontend/src/registerComponents.js"
Task: "Criar _frontend/src/js/routers.js"
Task: "Criar _frontend/src/js/utils/index.js"
```

---

## Estratégia de Implementação

### MVP Primeiro (US1 + US2 + US3)

1. Concluir Preparação e Fundacional
2. Entregar US1 (dev com HMR), US2 (build e manifesto) e US3 (Vue em `#emf`)
3. **PARAR e VALIDAR** com `quickstart.md` §1–§5

### Entrega Incremental

1. Adicionar US4 (tema), US5 (PWA) e US6 (identidade/404)
2. Adicionar US7 (API/auth) e US8 (qualidade)
3. Executar o Acabamento

---

## Notas

- Tarefas [P] = arquivos diferentes, sem dependências
- Replicar as particularidades de `research.md` (P1–P24) para fidelidade; correções são evolução
- Faça commit após cada tarefa ou grupo lógico
