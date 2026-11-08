# Plano de Implementação: Frontend Vite + Vue 3 integrado ao Django

**Branch**: `007-frontend-vite-vue` | **Data**: 2026-11-08 | **Especificação**: [spec.md](./spec.md)

**Entrada**: Especificação da funcionalidade em `/specs/007-frontend-vite-vue/spec.md`

## Resumo

Esta feature entrega a camada de frontend do esqueleto: um projeto Vite 8 (raiz em `_frontend/src`) com Vue 3.5, Pinia, Vue Router, Bootstrap 5 / Bootstrap-Vue-Next e FontAwesome, integrado ao Django por `django-vite`. O Django continua dono das páginas (templates em `_templates/`); o Vue é montado em `#emf` e processa o HTML do servidor em tempo de execução (delimitadores `[[ ]]`). Em desenvolvimento o Vite serve os módulos com HMR (`http://localhost:5173/static/…`); em produção o build vai para `_frontend/dist/frontend`, o manifesto do Vite é ajustado por um plugin pós-build (prefixo `frontend/`) e o Django/Nginx servem tudo em `/static/frontend/`. Inclui PWA (manifest + service worker `injectManifest`), modo de cores claro/escuro/auto, cabeçalho rolável, página 404, cliente axios para `/api`, store de autenticação e a configuração de qualidade (ESLint 9 flat config + Prettier + EditorConfig).

## Contexto Técnico

**Linguagem/Versão**: JavaScript ES modules (`"type": "module"`), SFC Vue 3.5 (`<script setup>` e Options API), SCSS (Dart Sass); Python 3.12+ apenas para `backend/settings/frontend.py`. Node.js 26 (`node:26.13.0-bookworm` no dev).

**Dependências Principais** (`package.json`, nome `customfront` v0.1.0):

| Tipo | Pacotes (faixa) |
|------|-----------------|
| runtime | `vue ^3.5.45`, `vue-router ^5.4.0`, `pinia ^4.1.0`, `axios ^1.21.0`, `bootstrap ^5.3.8`, `bootstrap-vue-next ^1.2.3`, `bootstrap-icons ^1.13.2`, `@popperjs/core ^2.11.8`, `@fortawesome/fontawesome-free ^7.3.1`, `@fortawesome/free-{solid,regular,brands}-svg-icons ^7.3.1`, `@fortawesome/vue-fontawesome ^3.3.3`, `jquery ^4.0.0`, `lodash ^4.18.1`, `vue-json-pretty ^2.6.0`, `markdown-it ^15.0.3` + plugins (`abbr ^2.0.0`, `anchor ^10.1.0`, `footnote ^4.0.0`, `highlightjs ^4.3.0`, `sub ^2.0.0`, `sup ^2.0.0`, `task-lists ^2.1.1`, `toc-done-right ^4.2.0`) |
| dev | `vite ^8.3.6`, `@vitejs/plugin-vue ^6.0.10`, `vite-plugin-pwa ^2.0.0`, `workbox-precaching ^7.4.1`, `@rollup/plugin-inject ^5.0.5`, `@nabla/vite-plugin-eslint ^3.0.1`, `unplugin-vue-components ^32.1.0`, `esbuild ^0.28.2`, `sass ^1.108.1`, `eslint ^9.39.5`, `@eslint/js ^9.39.5`, `eslint-plugin-vue ^10.12.0`, `@vue/eslint-config-prettier ^10.2.0`, `prettier ^3.9.10`, `globals ^17.14.0`, `dotenv ^18.0.9` |
| Python | `django-vite ^3.2.0` (`pyproject.toml`) |

**Armazenamento**: N/A no servidor (sem tabelas); no navegador, `localStorage.theme`, cache do service worker (Workbox precache) e cookie `csrftoken`.

**Testes**: Não há testes JS. A validação é por `npm run lint`, `npm run build` e verificação manual/`pytest` com o cliente de teste Django (renderização de `base.html`, ver `quickstart.md`).

**Plataforma Alvo**: Navegadores modernos (`target: 'esnext'`); servidor Vite em contêiner Linux (dev) e arquivos estáticos servidos pelo Nginx (prod).

**Tipo de Projeto**: Aplicação web (backend Django + frontend Vite no mesmo repositório).

**Metas de Desempenho**: Chunks por pacote (cache de longo prazo), carga preguiçosa de views/componentes, *precache* PWA do build.

**Restrições**: Sem segredos; o frontend só fala com `/api/` e `/ws/sync/`; `ESLint failOnError` quebra o build; `base` fixo `/static/` (dev) e `/static/frontend/` (prod) deve coincidir com `STATIC_URL`, o Nginx (`/static/` → `collectedstatic`) e o `manifestTransforms` do PWA.

**Escala/Escopo**: ~20 arquivos-fonte próprios (JS/Vue/SCSS) + ~2000 arquivos vendorizados em `_frontend/src/assets/bootstrap-icons` (não descritos individualmente).

## Verificação da Constituição

*PORTÃO (gate): deve passar antes da pesquisa. Reavaliado após o desenho.*

| Princípio | Gate | Resultado |
|-----------|------|-----------|
| I. Backend Django modular | Configuração do frontend isolada em `backend/settings/frontend.py` (módulo temático), importado por `project.py`; nada em `project.py` além do `import *`. | ✅ Atendido |
| II. Configuração por ambiente, sem segredos | `DJANGO_VITE_DEV_MODE` lido por `python-decouple` e combinado com `DEBUG`; nenhum segredo em `vite.config.js`/`package.json`; `.env` não versionado. O `console.debug` de `vite.config.js` imprime só variáveis `VITE_*`. | ✅ Atendido |
| III. Paridade dev/prod via Docker | `startfront-dev.sh` é o `CMD` do contêiner `front` (dev); o build de produção roda `npm run build` na imagem (`_docker/prod/Dockerfile`) e o `collectstatic` incorpora `_frontend/dist`. | ✅ Atendido (docker em 010/011) |
| IV. API REST gerada | O frontend consome `/api/…` apenas pelo cliente `Resources.Utils`; não cria endpoints. | ✅ Atendido |
| V. Frontend Vite integrado ao Django | Vue 3 + Pinia + Vue Router + Bootstrap 5, `django-vite`, ESLint + Prettier (sem `;`, aspas simples, 2 espaços), alias `~@`, prefixo `emf-`. | ✅ Atendido |
| VI. Tempo real e assíncrono | WebSocket/Channels pertencem à 006; aqui apenas `App.vue` os inicializa. | ✅ N/A (citado) |
| VII. Português do Brasil | Textos de UI em pt-BR (404, "esta página atualizará em…", manifesto `lang: 'pt-BR'`); comentários em pt-BR. Observação: o frontend não usa i18n (`gettext`) — textos fixos. | ⚠️ Atendido com ressalva (sem tradução no frontend) |
| VIII. Qualidade verificável | ESLint/Prettier/EditorConfig presentes; `npm run lint` e `npm run build` são portões do PR. Não há testes automatizados JS. | ⚠️ Atendido com ressalva (ver Rastreamento de Complexidade) |

Restrições adicionais: Node 26 / Vite 8 / Vue 3.5 conforme "Stack de referência" ✅; `backend.settings.fake` mantém `DJANGO_VITE_DEV_MODE=False` para o `collectstatic` da imagem ✅.

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/007-frontend-vite-vue/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── vite-django-integracao.md
│   └── componentes-e-rotas.md
└── tasks.md
```

### Código-Fonte (raiz do repositório)

```text
vite.config.js                      # configuração Vite (plugins, PWA, build, server)
package.json / package-lock.json    # scripts e dependências npm
eslint.config.js                    # ESLint 9 flat config
.prettierrc.json                    # Prettier
.editorconfig                       # EditorConfig (apenas arquivos de frontend)
startfront-dev.sh                   # npm install && npm run dev
backend/settings/frontend.py        # TEMPLATES, STATIC_*, DJANGO_VITE
backend/context_processors.py       # `debug` (expõe DEBUG aos templates) — feature 001
_templates/
├── base.html                       # vite_hmr_client, vite_asset 'main.js', #emf/<emf-app>, seletor de tema, manifest
└── 404.html                        # <emf-error-404>
_frontend/
├── src/                            # root do Vite
│   ├── main.js                     # entrada
│   ├── App.vue                     # componente raiz <emf-app>
│   ├── registerComponents.js       # rootComponents / globalComponents (prefixo emf-)
│   ├── service-worker.js           # SW usado pelo VitePWA (injectManifest)
│   ├── sw.js                       # SW legado, NÃO usado
│   ├── js/
│   │   ├── routers.js
│   │   ├── EventBus.js             # (006)
│   │   ├── stores/
│   │   │   ├── TeleportStore.js
│   │   │   ├── MessageStore.js     # (006)
│   │   │   └── pinea/{AuthStore.js, SyncStore.js(006)}
│   │   └── utils/
│   │       ├── index.js            # importa colormodes e scrollheader
│   │       ├── colormodes/index.js
│   │       ├── scrollheader/index.js
│   │       ├── resources/index.js  # cliente axios /api
│   │       ├── timer/TimerWorkerService.js   # (006)
│   │       └── ws/WebSocketManager.js        # (006)
│   ├── views/{Error404.vue, WsTest.vue(006)}
│   ├── components/utils/{JsonViewer.vue, Markdown.vue, RefreshPage.vue, message/Alert.vue, message/{AlertMessage,DisplayMessage}.vue(006)}
│   ├── scss/{styles.scss, header.scss, _icon-list.scss, custom/bootstrap.scss}
│   └── assets/                     # publicDir
│       ├── favicon.ico
│       ├── imgs/{logo_backend.svg, logo_backend_42px.svg, perfil.png, perfil.svg, icons/*.png}
│       └── bootstrap-icons/        # cópia vendorizada (font/, icons/, bootstrap-icons.svg…)
└── dist/frontend/                  # saída do build (ignorada pelo git; `dist/` no .gitignore)
```

**Decisão de Estrutura**: Projeto web com frontend e backend no mesmo repositório. O Vite usa `root=_frontend/src` e escreve em `_frontend/dist/frontend`; `package.json`, `vite.config.js` e `eslint.config.js` ficam na raiz do repositório (executados do diretório raiz, `process.cwd()`). O subdiretório `frontend/` dentro de `dist` existe para que, ao ser coletado por `collectstatic` (`STATICFILES_DIRS=[_frontend/dist]`), os arquivos fiquem em `collectedstatic/frontend/…` → URL `/static/frontend/…`.

## Rastreamento de Complexidade

| Desvio | Por que é necessário | Alternativa mais simples rejeitada porque |
|--------|----------------------|-------------------------------------------|
| Sem testes automatizados de frontend (princípio VIII exige teste para comportamento novo) | O esqueleto herdado não adotou Vitest/Playwright; a validação é por lint + build + verificação manual. | Adicionar Vitest está fora do escopo da engenharia reversa (replica o estado atual); recomendado como evolução. |
| Plugin pós-build que reescreve o manifesto | `django-vite` + `STATICFILES_DIRS` exigem chaves `file`/`css`/`assets` já com o prefixo `frontend/`. | Alterar `build.assetsDir` ou `base` não adiciona prefixo ao manifesto. |
| Alias `vue → vue.esm-bundler.js` | O HTML do Django é compilado no cliente (runtime compiler). | Renderizar tudo com SFCs eliminaria o papel do Django como dono das páginas. |

## Detalhamento de Implementação

### 1. `package.json`

- `name: "customfront"`, `version: "0.1.0"`, `type: "module"`.
- `scripts`: `dev: "vite"`, `build: "vite build"`, `preview: "vite preview"`, `lint: "eslint _frontend/src/ --fix"`, `format: "prettier --write _frontend/src/"`.
- Dependências conforme a tabela do Contexto Técnico. O `package-lock.json` deve ser versionado (o `Dockerfile` de produção comenta a cópia dele, mas o Dependabot o atualiza semanalmente).
- Pacotes transitivos relevantes: `highlight.js ^11` (via `markdown-it-highlightjs`), `@fortawesome/fontawesome-svg-core` (via `vue-fontawesome`).

### 2. `vite.config.js` — `defineConfig(({command, mode}) => …)`

Constantes: `BASE_DIR='./_frontend'`, `OUTPUT_DIR='./_frontend/dist/frontend'`, `INPUT_DIR='./_frontend/src'`. No início: `console.debug` do comando/modo, `cwd = process.cwd()` e `env = loadEnv(mode, cwd, 'VITE_')` (apenas log).

Configuração retornada:

| Chave | Valor |
|-------|-------|
| `esbuild.pure` | `mode === 'production' ? ['console.log','console.debug'] : []` |
| `root` | `path.resolve(INPUT_DIR)` |
| `base` | `mode === 'production' ? '/static/frontend/' : '/static/'` |
| `publicDir` | `path.resolve(INPUT_DIR,'assets')` |
| `resolve.extensions` | `['.js','.json','.vue']` |
| `resolve.alias` | `'~@' → path.resolve(INPUT_DIR)`; `'vue' → 'vue/dist/vue.esm-bundler.js'` |
| `server` | `host '0.0.0.0'`, `port 5173`, `open false`, `headers {'Service-Worker-Allowed':'/'}`, `watch {usePolling:true, disableGlobbing:false}` |
| `build` | `outDir path.resolve(OUTPUT_DIR)`, `assetsDir ''`, `manifest true`, `emptyOutDir true`, `copyPublicDir true`, `target 'esnext'`, `minify 'esbuild'`, `sourcemap mode==='production' ? false : true` |
| `build.rollupOptions.input` | `{ main: path.resolve(INPUT_DIR,'main.js') }` |
| `build.rollupOptions.output` | `chunkFileNames: undefined`; `manualChunks(id)` |

**`manualChunks(id)`** (algoritmo): `console.debug('manualChunks processing id:', id)`; se `id.includes('node_modules')`, retornar `id.split('node_modules/')[1].split('/')[idx]` onde `idx = id.includes('fortawesome') ? 1 : 0` (para `@fortawesome/free-solid-svg-icons/...` → `free-solid-svg-icons`; para `@vue/runtime-core` → `@vue`; para `vue/dist/…` → `vue`); caso contrário `undefined`.

**Plugins, na ordem**:

1. `vue()`.
2. `VitePWA({...})` — `registerType:'autoUpdate'`, `scope:'/'`, `strategies:'injectManifest'`, `srcDir:''`, `filename:'service-worker.js'`, `manifestFilename:'manifest.json'`, `devOptions:{enabled:false}`, `includeAssets:['favicon.ico','robots.txt']`, `injectManifest.globPatterns:['**/*.{js,css,html,png,jpg,jpeg,svg,gif,woff2}']`, `injectManifest.manifestTransforms:[async entries => ({manifest: entries.map(e => ({...e, url: '/static/frontend/' + e.url.replace(/^\//,'')})), warnings: []})]`. (O código original muta `entry.url`.) `manifest`: ver seção 8.
3. `inject({ $:'jquery', jQuery:'jquery', '_':'lodash', include:['src/**/*.js','src/**/*.vue'], exclude:'src/routers/**' })` — comentário no código: "that should be first under plugins array" (na prática está após o PWA).
4. `eslintPlugin({ exclude:['node_modules/**','dist/**','dist-ssr/**','coverage/**'], cache:false, failOnWarning:false, failOnError:true, emitWarning:true, emitError:true })`.
5. `Components({ resolvers:[ BootstrapVueNextResolver({ aliases:{} }) ] })` (importar `BootstrapVueNextResolver` de `bootstrap-vue-next`).
6. Plugin inline `{ name:'postbuild-commands', closeBundle }`: se `command !== 'build'` retorna; senão lê `./_frontend/dist/frontend/.vite/manifest.json`, para cada chave: `file` → `'frontend/' + file`; `css` → cada item prefixado; `assets` → cada item prefixado (`imports`/`dynamicImports` não são alterados); `console.debug` do manifesto ajustado; grava com `JSON.stringify(manifest, null, 2)`.

Importações no topo: `fs`, `path`, `defineConfig, loadEnv` de `vite`, `VitePWA` de `vite-plugin-pwa`, `vue` de `@vitejs/plugin-vue`, `inject` de `@rollup/plugin-inject`, `Components` de `unplugin-vue-components/vite`, `eslintPlugin` de `@nabla/vite-plugin-eslint`.

Observação: o arquivo termina com comentários (referência a `https://demo.viewflow.io/dashboard/oilngas/` e um bloco `viteStaticCopy` comentado) — não funcionais.

### 3. `eslint.config.js`

`defineConfig([...])` de `eslint/config`:

1. Bloco `app/files-to-lint`: `files:['_frontend/src/**/*.{js,mjs,jsx,vue}']`, `languageOptions.globals = {...globals.browser, ...globals.node, EventBus:'readonly', bootstrap:'readonly'}`.
2. Bloco `app/files-to-ignore`: `ignores:['**/dist/**','**/dist-ssr/**','**/coverage/**']`.
3. `js.configs.recommended`, `skipFormatting` (de `@vue/eslint-config-prettier/skip-formatting`), `...pluginVue.configs['flat/strongly-recommended']`.
4. Bloco `{ rules: { 'vue/multi-word-component-names': 'off' } }`.

### 4. `.prettierrc.json` e `.editorconfig`

- Prettier: `{"$schema":"https://json.schemastore.org/prettierrc","semi":false,"singleQuote":true,"arrowParens":"avoid"}`.
- EditorConfig (sem `root = true`): seção `[*.{js,jsx,mjs,cjs,ts,tsx,mts,cts,vue}]` com `charset=utf-8`, `indent_size=2`, `indent_style=space`, `insert_final_newline=true`, `trim_trailing_whitespace=true`.

### 5. `backend/settings/frontend.py`

- `from .zenv import DEBUG, PROJECT_DIR, config`.
- `TEMPLATES` (um `DjangoTemplates`): `DIRS=[PROJECT_DIR/"_templates"]`, `APP_DIRS=True`, `context_processors`: `django.template.context_processors.{debug,request,media,static}`, `django.contrib.auth.context_processors.auth`, `django.contrib.messages.context_processors.messages`, `backend.context_processors.debug`; `options.debug = DEBUG`.
- `CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"`, `CRISPY_TEMPLATE_PACK = "bootstrap5"`.
- `STATIC_URL = "static/"`, `STATIC_ROOT = PROJECT_DIR/"collectedstatic"`.
- `DJANGO_VITE_ASSETS_PATH = PROJECT_DIR/"_frontend"/"dist"`; `STATICFILES_DIRS=[DJANGO_VITE_ASSETS_PATH]`; `if DEBUG: STATICFILES_DIRS += [PROJECT_DIR/"_frontend"/"src"/"assets"]`.
- `DJANGO_VITE_DEV_MODE = config("DJANGO_VITE_DEV_MODE", default=True, cast=bool)`; depois `DJANGO_VITE_DEV_MODE = DJANGO_VITE_DEV_MODE and DEBUG`.
- `DJANGO_VITE = {"default": {"dev_mode": DJANGO_VITE_DEV_MODE, "manifest_path": (DJANGO_VITE_ASSETS_PATH if DJANGO_VITE_DEV_MODE else STATIC_ROOT) / "frontend" / ".vite" / "manifest.json"}}`.
- `backend/settings/project.py` importa com `from .frontend import *`; `backend/settings/apps.py` inclui `"django_vite"` em `DJANGO_CORE_APPS` e `django.contrib.staticfiles`; `backend/settings/fake.py` força `DJANGO_VITE_DEV_MODE=False` e `manifest_path = DJANGO_VITE_ASSETS_PATH/frontend/.vite/manifest.json` (usado no `collectstatic` do Dockerfile de produção).
- Em dev, `django-vite` (padrões: protocolo `http`, host `localhost`, porta `5173`, `static_url_prefix=""`) monta URLs `http://localhost:5173/static/@vite/client` e `http://localhost:5173/static/main.js` (por isso o `base` de dev é `/static/`).

### 6. `_templates/base.html` (partes pertencentes a esta feature)

- Linha 2: `{% load i18n static django_vite common_tags menus %}`.
- `<html class="{% block html_class %}{% endblock %}" lang="pt-br" data-bs-theme="auto">`.
- `<head>`: `meta charset`, `meta theme-color #5B9F91`, `viewport`, `<link rel="icon" type="image/x-icon" href="{% static 'frontend/favicon.ico' %}">`, `{% if not DEBUG %}<link rel="manifest" href="/manifest.json">{% endif %}`, `<title>Backend</title>`, `{% vite_hmr_client %}`, `{% vite_asset 'main.js' %}`, `{% block json_content %}{% endblock %}`.
- `<body class="{% block body_class %}{% endblock %}">` abre com `<svg style="display:none">` contendo os `<symbol>` `bootstrap`, `check2`, `circle-half`, `moon-stars-fill`, `sun-fill`, `svg-perfil` (caminhos SVG copiados da documentação do Bootstrap).
- `<div id="emf"><emf-app> {% block root_body %}…{% endblock root_body %} </emf-app></div>`, seguido de `{% block extra_js %}{% endblock %}`.
- Cabeçalho (`header#header-main.sticky-top`, `nav.navbar.navbar-expand-lg.navbar-topo`), `main#main-content.min-vh-100`, rodapé e menus pertencem a `004-crud-generico-menus`/`002`; esta feature depende somente de: `#header-main` (scrollheader), `#bd-theme` e `[data-bs-theme-value]` (colormodes) e do `<emf-app>`.
- Seletor de tema no rodapé: `div.d-flex.align-items-center.dropup.color-modes` com `button#bd-theme.btn.btn-link.dropdown-toggle` (`data-bs-toggle="dropdown"`, `data-bs-display="static"`) contendo `span#bd-theme-text > svg.bi.theme-icon.theme-icon-active > use[href="#circle-half"]`; `ul.dropdown-menu` com três `button.dropdown-item[data-bs-theme-value]` (`light` ícone `#sun-fill`, `dark` ícone `#moon-stars-fill`, `auto` ícone `#circle-half` e classe `active` inicial), cada um com um `svg.theme-icon` `#check2` (classe `d-none ms-auto`).
- `_templates/404.html`: `{% extends 'base.html' %}` + `{% block base_content %}<emf-error-404></emf-error-404>{% endblock %}`.
- `_templates/wstest_index.html` usa `<router-view>` (feature 006) e `index.html` usa `<img src="{% static '/imgs/logo_backend.svg' %}">`.

### 7. `_frontend/src/main.js` — ordem exata

1. `import 'vite/modulepreload-polyfill'`.
2. `import '~@/scss/styles.scss'`.
3. `import * as bootstrap from 'bootstrap'`.
4. `import { library, dom } from '@fortawesome/fontawesome-svg-core'`; `fas`, `far`, `fab`; `library.add(fas, far, fab)`; `dom.watch()`.
5. `import axios from 'axios'`; `import './js/utils'` (carrega `colormodes` e `scrollheader`).
6. `createApp` (vue), `createBootstrap` (`bootstrap-vue-next`), `createPinia` (`pinia`), `router` (`./js/routers`), `EventBus` (`./js/EventBus`), `registerComponents`.
7. Para cada `[data-bs-toggle="popover"]`: `new bootstrap.Popover(el)`.
8. `axios.defaults.headers.get` com `Cache-Control`, `Pragma`, `Expires`; `axios.defaults.xsrfCookieName='csrftoken'`; `axios.defaults.xsrfHeaderName='X-CSRFToken'`.
9. `const app = createApp({ components: registerComponents.rootComponents, setup(){}, delimiters:['[[',']]'] })`.
10. `app.provide('EventBus', EventBus)`; `app.config.globalProperties.$EventBus = EventBus`.
11. `app.use(router).use(createPinia()).use(createBootstrap()).mount('#emf')`.
12. `Object.keys(registerComponents.globalComponents).forEach(name => app.component(name, …))` (após o mount).
13. `console.debug('Environment Mode:', import.meta.env.MODE)`; se `'serviceWorker' in navigator && import.meta.env.PROD`: `navigator.serviceWorker.register('/service-worker.js', {scope:'/', type:'module'})` com `.then` (debug do escopo) e `.catch` (`console.error('Falha ao registrar o Service Worker:', error)`).

### 8. PWA

Manifesto (`VitePWA.manifest`): `id 'br.leg.go.jatai.sddstart'`, `name`/`short_name`/`description` `'Sdd Start 2026'`, `background_color '#ffffff'`, `theme_color '#114d81'`, `start_url` e `scope` = `'/'` em produção, `'http://localhost:9099/'` caso contrário, `display 'fullscreen'`, `orientation 'any'`, `lang 'pt-BR'`, `icons`: 192x192 e 512x512 `image/png`, `src` = `/static/frontend/imgs/icons/android-chrome-<size>.png` em produção e `imgs/icons/android-chrome-<size>.png` caso contrário. Saída em `_frontend/dist/frontend/manifest.json` (+ `service-worker.js`, e `registerSW.js` não usado). Nginx expõe `/service-worker.js` → `collectedstatic/frontend/service-worker.js` e `/manifest.json` → `collectedstatic/frontend/manifest.json` (`_docker/prod/nginx/backend_docker.conf`, feature 011).

`_frontend/src/service-worker.js`:

```js
import { precacheAndRoute } from 'workbox-precaching'
precacheAndRoute(self.__WB_MANIFEST)
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()))
```

`_frontend/src/sw.js` é uma cópia antiga com `fetch` vazio (ver research).

### 9. Modo de cores — `js/utils/colormodes/index.js`

IIFE derivada do script de cores da documentação do Bootstrap 5.3 (licença CC BY 3.0 no cabeçalho): `getStoredTheme` = `localStorage.getItem('theme')`; `setStoredTheme`; `getPreferredTheme()` = tema salvo ou `matchMedia('(prefers-color-scheme: dark)')`→`'dark'|'light'`; `setTheme(theme)` grava `data-bs-theme` em `document.documentElement` (resolvendo `auto`); executa `setTheme(getPreferredTheme())` imediatamente; `showActiveTheme(theme, focus=false)` atualiza `.active`/`aria-pressed`, o `href` do `use` do ícone ativo (copiado do `svg use` do botão ativo), o `aria-label` do `#bd-theme` (`"<texto> (<tema>)"`) e foca se `focus`; listener `change` de `matchMedia` reaplica `setTheme(getPreferredTheme())` se o tema salvo não for `light`/`dark`; em `DOMContentLoaded` chama `showActiveTheme(getPreferredTheme())` e registra clique em cada `[data-bs-theme-value]` (grava, aplica, `showActiveTheme(theme, true)`).

### 10. `js/utils/scrollheader/index.js`

IIFE: em `DOMContentLoaded`, `setTimeout(…, 2000)`; se existir `#header-main`, define `checkScroll()` (`scrollY > 0` → `classList.add('header-scrolled')`, senão `remove`), chama-a uma vez e registra `window.addEventListener('scroll', checkScroll)`. `js/utils/index.js` apenas importa `./colormodes` e `./scrollheader` e contém uma IIFE vazia com `'use strict'`.

### 11. `registerComponents.js`, `App.vue`, roteador, stores

- `registerComponents.js`: `defineAsyncComponent` de `vue`; `App` de `./App.vue`; `FontAwesomeIcon` de `@fortawesome/vue-fontawesome`. Exporta `default { rootComponents, globalComponents }` conforme FR-021 (comentário: "emf = Backend Frontend").
- `App.vue` (`<script setup>`): importa `DisplayMessage` (`~@/components/utils/message/DisplayMessage`), `useSyncStore` (`~@/js/stores/pinea/SyncStore`), `useAuthStore`, `ref`; `syncStore.initialize()`; `authStore.loginStatus()` (sem `catch`); `modalApp = ref(null)`; `syncStore.registerModels('utils', ['teste'])`. Template: `<slot /> <DisplayMessage /> <div id="modalApp" ref="modalApp" />`.
- `js/routers.js`: exporta `routes` e `default router = createRouter({history: createWebHistory(), routes})`; `WsTest = () => import('~@/views/WsTest.vue')`, `Error404 = () => import('~@/views/Error404.vue')`.
- `AuthStore.js`: `defineStore('authStore', {state:()=>({data_connect:{}}), getters:{isAuthenticated, permissions, hasPermission}, actions:{loginStatus, loginPortal, logoutPortal}})` usando `Resources.Utils` (`getVersion`, `login`, `logout`). Após login/logout encadeia `getVersion()` e atualiza `data_connect`.
- `TeleportStore.js`: `export const activeTeleportId = ref(null)`.

### 12. `js/utils/resources/index.js`

Constante `basePath='/api'`; reaplica os padrões do axios (GET sem cache, `xsrfCookieName`, `xsrfHeaderName`). `export default { Utils: {…} }`:

| Método | Requisição |
|--------|------------|
| `login(username, password)` | `POST /api/auth/session` corpo `{username,password}`, `withCredentials:true` |
| `logout()` | `DELETE /api/auth/session` |
| `hasPermission(permission)` | `OPTIONS /api/auth/session/?perm=<permission>`, `withCredentials`; resolve `response.data.status === 'ok'`; em erro, `false` |
| `getVersion()` | `GET /api/version` |
| `fetch(m, method='GET')` | se `m.params && !m.query_string`, `m.query_string = new URLSearchParams(m.params).toString()`; URL `/api/${m.app}/${m.model}/${m.id ? m.id+'/' : ''}${m.action ? m.action+'/' : ''}${query_string ? '?'+qs : ''}` |
| `patchModel(m)` | `PATCH /api/<app>/<model>/[<id>/][<action>/]`, corpo `m.form || {}`, config `m.progress || {}` |
| `putModel(m)` | idem com `PUT` |
| `postModel(m)` | `POST /api/<app>/<model>/[<action>/]` |
| `deleteModel(m)` | `DELETE /api/<app>/<model>/<id>/` |

### 13. Componentes

- `Alert.vue`: `<div class="alert alert-info fade show alert-dismissible" role="alert"><slot/><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"/></div>`; `export default { name: 'Alert' }` + `<script setup>` vazio.
- `RefreshPage.vue` (Options API, `name:'RefreshPage'`): props `timeout` (Number, obrigatório, validador `>0`), `show` (Boolean, obrigatório), `enabled` (Boolean, padrão `true`); `data: timer, remainingTime`; `displayTime` computada: `Math.ceil(remainingTime/1000)` → `"<n> segundos"` ou `"Agora"`; `mounted` inicia se `enabled`; `beforeUnmount` limpa; `watch enabled/timeout` reiniciam/limpam; `startTimer()` define `remainingTime = timeout`, `setTimeout(() => window.location.reload(), timeout)` e, se `show`, `setInterval` de 1 s decrementando 1000 ms; `clearTimers()`. Template: `v-if="show"` `div.refresh-countdown` com `<slot/>... esta página atualizará em {{ displayTime }}.`; estilo *scoped* fixo canto inferior direito.
- `Markdown.vue` (`<script setup lang="js">`): instância `MarkdownIt` com os plugins; prop `source` (String, `""`); template `<div v-html="markdown.render(source)" />` (atenção: `markdown-it` por padrão não habilita HTML bruto — `html:false` — mitigando XSS).
- `JsonViewer.vue`: ver `research.md` (legado).
- `Error404.vue`: `.http-404` flex centrado (`min-height:70vh`), `<img src="/imgs/logo_backend.svg" alt="Logo Sdd-Start" class="img-fluid">`, `h1.error-code` "404" (cor `#dc3545`, 8rem), `h2.error-title` "Página não encontrada", `p.error-message` "A página que você está procurando não existe ou foi movida.", `a.home-button[href="/"]` "Voltar para página inicial" (`#007bff`, hover `#0069d9`); `@media (min-width:768px)` `.img-fluid{max-width:50%}`; estilo `scoped`.

### 14. SCSS

- `scss/styles.scss`: `@use 'sass:math'`; `@import url(https://fonts.googleapis.com/css2?family=Roboto+Condensed:ital,wght@0,100..900;1,100..900&family=Rubik:ital,wght@0,300..900;1,300..900&display=swap)`; variáveis `$color_logo_backend_sddstart:#EE6600`, `$color_logo_backend_mais:#853d05`, `$color_logo_backend_plataforma:#7D7E7F`, `$color_primary`, `$color_secondary`, `$heightBrand:3rem`, `$heightBrasao:6rem`; `$utilities` com `min-viewport-height` (`class: min-vh`, 50–100 em `vh`) e `avatar` (`property: height width`, `class: avatar`, 1–9 → `1rem…9rem`), `$grid-gutter-width: 2rem !default`, `$yellow:#c99909 !default`; `@import 'custom/bootstrap'` e `@import 'header'`; seções: `a`, `main` (gradiente, `.main-box`, `.nav`), `footer`, `.bi.theme-icon`, `.text-right`, `.color-modes`, `.nav-pagination`, `[id*=helptext]`, `.context-actions`, `.container-table`, `.container-login`, `@include color-mode(dark)`, `@media` ≥768/992/1200 e `print`.
- `scss/custom/bootstrap.scss`: `@import 'bootstrap/scss/bootstrap'`; `@import 'bootstrap-vue-next/src/styles/styles.scss'`; `$bootstrap-icons-font-dir: "/static/bootstrap-icons/font/fonts" !default`; `@import 'bootstrap-icons/font/bootstrap-icons.scss'`.
- `scss/header.scss`: `.navbar`, `header` (borda superior primária, `.navbar-topo`, `.nav-brand`, `.nav-user`, `&.header-scrolled` reduz `min-height`, `.navbar-nav`), `.navbar-brand`, `.header-casa-legislativa/.footer-casa-legislativa`, modo escuro, `@media` mobile (`max-width:991.98px`) e desktop (`min-width:992px`), `.dropdown-divider/.divider`.
- `scss/_icon-list.scss`: parcial `.icon-list` com marcadores SVG; **não importado** (morto).

### 15. Assets (`publicDir`)

`favicon.ico`; `imgs/logo_backend.svg`, `imgs/logo_backend_42px.svg`, `imgs/perfil.png`, `imgs/perfil.svg`; `imgs/icons/`: `android-chrome-192x192.png`, `android-chrome-512x512.png`, `apple-touch-icon.png` e variantes `-60x60`, `-76x76`, `-120x120`, `-152x152`, `-180x180`, `favicon-16x16.png`, `favicon-32x32.png`, `msapplication-icon-144x144.png`, `mstile-150x150.png`; `bootstrap-icons/` (pacote vendorizado: `bootstrap-icons.svg`, `font/` com CSS/SCSS/JSON/fontes, `icons/*.svg`, `LICENSE`, `package.json`, `README.md`) — copiar do pacote `bootstrap-icons` instalado.

### 16. `startfront-dev.sh`

```bash
#!/usr/bin/env bash

npm install
npm run dev
```

Executável (`chmod +x`); é o `CMD` do contêiner `front` (`_docker/dev/Dockerfile.Dev.Front`, feature 010).

### 17. Variáveis de ambiente

| Variável | Onde é lida | Efeito |
|----------|-------------|--------|
| `DJANGO_VITE_DEV_MODE` (padrão `True`) | `backend/settings/frontend.py` (`python-decouple`) | Ativa modo dev do `django-vite`, somente se `DEBUG=True` |
| `DEBUG` | `backend/settings/zenv.py` | Decide `STATICFILES_DIRS`, `<link rel="manifest">`, modo dev |
| `VITE_*` | `vite.config.js` (`loadEnv`) | Apenas impresso em log; sem uso funcional |
| `mode` do Vite (`production` por padrão em `vite build`) | CLI | `base`, `sourcemap`, `esbuild.pure`, manifest PWA |
