# Modelo de Dados: Frontend Vite + Vue 3 integrado ao Django

**Branch**: `007-frontend-vite-vue` | **Data**: 2026-11-08 | **Plano**: [plan.md](./plan.md)

> **Não há tabelas, modelos Django nem migrações novas nesta feature.** As estruturas abaixo são de configuração, artefatos de build e estado no navegador. Os modelos acessados via `/api/<app>/<modelo>/` pertencem às features 002–005.

## 1. Configuração do Vite (`vite.config.js`)

Função `defineConfig(({ command, mode }) => ({ ... }))`.

| Constante | Valor | Uso |
|-----------|-------|-----|
| `BASE_DIR` | `./_frontend` | Declarada (referência) |
| `OUTPUT_DIR` | `./_frontend/dist/frontend` | `build.outDir` e leitura do manifesto no `closeBundle` |
| `INPUT_DIR` | `./_frontend/src` | `root`, `publicDir`, alias `~@`, entrada `main` |

| Modo / comando | `base` | `sourcemap` | `esbuild.pure` | `manifest` PWA (`start_url`/`scope`, ícones) |
|----------------|--------|-------------|----------------|-----------------------------------------------|
| `vite` (dev, `mode=development`) | `/static/` | `true` | `[]` | `http://localhost:9099/`; `imgs/icons/android-chrome-<size>.png` |
| `vite build` (`mode=production`) | `/static/frontend/` | `false` | `['console.log','console.debug']` | `/`; `/static/frontend/imgs/icons/android-chrome-<size>.png` |

Demais chaves (`resolve`, `server`, `build`, plugins): ver `plan.md`, seção 2.

## 2. Manifesto do Vite (`_frontend/dist/frontend/.vite/manifest.json`)

Gerado por `build.manifest: true`; mapa `chave → entrada`. A chave é o caminho relativo ao `root` (`_frontend/src`).

| Campo da entrada | Tipo | Observação |
|------------------|------|------------|
| `file` | string | Arquivo emitido, ex. `main-<hash>.js`. **Após o plugin `postbuild-commands`: `frontend/main-<hash>.js`** |
| `src` | string | Caminho-fonte (inalterado) |
| `name` | string | Nome do *chunk* |
| `isEntry` | boolean | `true` para `main.js` |
| `isDynamicEntry` | boolean | `true` para views/componentes carregados com `import()` |
| `css` | string[] | Arquivos CSS associados; cada item é prefixado com `frontend/` |
| `assets` | string[] | Ativos associados; cada item é prefixado com `frontend/` |
| `imports` | string[] | Chaves de outros *chunks* (inalterado) |
| `dynamicImports` | string[] | Chaves de *chunks* dinâmicos (inalterado) |

Exemplo (após o pós-processamento; hashes ilustrativos):

```json
{
  "main.js": {
    "file": "frontend/main-AbC123.js",
    "name": "main",
    "src": "main.js",
    "isEntry": true,
    "css": ["frontend/main-XyZ789.css"],
    "imports": ["vue", "bootstrap"]
  },
  "views/Error404.vue": { "file": "frontend/Error404-Qw12.js", "isDynamicEntry": true }
}
```

Invariante (SC-002): para toda entrada, `file`, cada `css[i]` e cada `assets[i]` começam com `frontend/`. O plugin **não** é idempotente — rodar duas vezes duplicaria o prefixo (só roda em `closeBundle` de `vite build`, que sempre esvazia `outDir` antes).

Nomes dos *chunks* de pacotes (`manualChunks`): `vue`, `@vue`, `bootstrap`, `bootstrap-vue-next`, `axios`, `pinia`, `vue-router`, `free-solid-svg-icons`, `free-regular-svg-icons`, `free-brands-svg-icons`, `vue-fontawesome`, etc.

## 3. Estrutura de saída do build (`_frontend/dist/frontend/`)

```text
.vite/manifest.json            # manifesto do Vite (ajustado)
main-<hash>.js / main-<hash>.css
<pacote>-<hash>.js             # um chunk por pacote de node_modules
<View|Componente>-<hash>.js    # chunks dinâmicos (Error404, Alert, RefreshPage, WsTest…)
manifest.json                  # manifesto PWA
service-worker.js              # SW (injectManifest)
registerSW.js                  # gerado, não usado
favicon.ico, imgs/, bootstrap-icons/   # cópia do publicDir (copyPublicDir)
```

## 4. Manifesto PWA (`manifest.json`)

| Campo | Valor |
|-------|-------|
| `id` | `br.leg.go.jatai.sddstart` |
| `name` / `short_name` / `description` | `Sdd Start 2026` |
| `background_color` | `#ffffff` |
| `theme_color` | `#114d81` |
| `start_url` / `scope` | `/` (produção) · `http://localhost:9099/` (demais modos) |
| `display` | `fullscreen` |
| `orientation` | `any` |
| `lang` | `pt-BR` |
| `icons` | `[{src, sizes:'192x192', type:'image/png'}, {src, sizes:'512x512', type:'image/png'}]` |

`src` do ícone: `/static/frontend/imgs/icons/android-chrome-<size>.png` (produção) ou `imgs/icons/android-chrome-<size>.png`.

### *Precache* do Workbox (`self.__WB_MANIFEST`)

Lista `[{ url, revision }]` injetada em `service-worker.js` a partir de `globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,svg,gif,woff2}']`. `manifestTransforms` transforma cada `url` em `'/static/frontend/' + url.replace(/^\//, '')`. Resultado: `{ url: '/static/frontend/main-<hash>.js', revision: <hash|null> }`.

## 5. Configurações Django (`backend/settings/frontend.py`)

| Símbolo | Tipo | Valor / regra |
|---------|------|---------------|
| `TEMPLATES` | lista | 1 backend `DjangoTemplates`; `DIRS=[PROJECT_DIR/"_templates"]`; `APP_DIRS=True`; `options.debug=DEBUG` |
| `CRISPY_ALLOWED_TEMPLATE_PACKS` / `CRISPY_TEMPLATE_PACK` | str | `"bootstrap5"` |
| `STATIC_URL` | str | `"static/"` |
| `STATIC_ROOT` | `Path` | `PROJECT_DIR/"collectedstatic"` |
| `DJANGO_VITE_ASSETS_PATH` | `Path` | `PROJECT_DIR/"_frontend"/"dist"` |
| `STATICFILES_DIRS` | lista | `[DJANGO_VITE_ASSETS_PATH]` (+ `_frontend/src/assets` se `DEBUG`) |
| `DJANGO_VITE_DEV_MODE` | bool | `config("DJANGO_VITE_DEV_MODE", default=True, cast=bool) and DEBUG` |
| `DJANGO_VITE` | dict | `{"default": {"dev_mode": <bool>, "manifest_path": (<ASSETS_PATH se dev, senão STATIC_ROOT>)/"frontend"/".vite"/"manifest.json"}}` |

## 6. Estado do frontend (navegador)

### 6.1 Store Pinia `authStore` (`_frontend/src/js/stores/pinea/AuthStore.js` — o diretório chama-se `pinea`, com erro de grafia, e deve ser mantido)

| Elemento | Tipo | Descrição |
|----------|------|-----------|
| `state.data_connect` | `object` (inicial `{}`) | Última resposta de `GET /api/version`: `{name, description, version[, user]}` |
| getter `isAuthenticated` | `boolean` | `data_connect.is_authenticated \|\| false` (hoje sempre `false`, ver research P2) |
| getter `permissions` | `string[]` | `data_connect?.permissions \|\| []` |
| getter `hasPermission` | `(perm) => boolean` | `false` se não há `permissions`; senão `permissions.includes(perm)` |
| ação `loginStatus()` | `Promise<object>` | `getVersion()` → `data_connect = response.data` |
| ação `loginPortal(username, password)` | `Promise<object>` | `login()` → `getVersion()` → atualiza `data_connect` |
| ação `logoutPortal()` | `Promise<object>` | `logout()` → `getVersion()` → atualiza `data_connect` |

Hook de uso: `useAuthStore()`. Sem persistência.

### 6.2 `TeleportStore.js` (`_frontend/src/js/stores/TeleportStore.js`)

`export const activeTeleportId = ref(null)` — `ref` reativo simples (não é store Pinia).

### 6.3 Stores da feature 006 (apenas citadas)

`SyncStore` (Pinia, `useSyncStore`), `MessageStore`, `EventBus` — ver `specs/006-sincronizacao-tempo-real/`.

### 6.4 Armazenamento do navegador

| Local | Chave | Valores | Escrita |
|-------|-------|---------|---------|
| `localStorage` | `theme` | `light` \| `dark` \| `auto` | `colormodes/index.js` ao clicar em `[data-bs-theme-value]` |
| Atributo DOM | `html[data-bs-theme]` | `light` \| `dark` (resolvido) | `setTheme()`; inicial no HTML: `auto` |
| Cookie (Django) | `csrftoken` | token | lido pelo axios → cabeçalho `X-CSRFToken` |
| Cache API (Workbox) | `workbox-precache-v2-…` | respostas dos arquivos do *precache* | `precacheAndRoute` |
| Atributo DOM | `#header-main.header-scrolled` | classe presente se `scrollY > 0` | `scrollheader` |

### 6.5 Registro de componentes (`registerComponents.js`)

| Grupo | Chave | Valor |
|-------|-------|-------|
| `rootComponents` | `emf-app` | `App.vue` (importação direta) |
| `rootComponents` | `emf-error-404` | `defineAsyncComponent(() => import('~@/views/Error404.vue'))` |
| `globalComponents` | `FontAwesomeIcon` | `FontAwesomeIcon` de `@fortawesome/vue-fontawesome` |
| `globalComponents` | `emf-alert` | async `components/utils/message/Alert.vue` |
| `globalComponents` | `emf-refresh-page` | async `components/utils/RefreshPage.vue` |

## 7. Formato do cliente `/api` (`_frontend/src/js/utils/resources/index.js`)

### 7.1 Objeto descritor `m` (parâmetro de `fetch`, `patchModel`, `putModel`, `postModel`, `deleteModel`)

| Campo | Tipo | Obrigatório | Uso |
|-------|------|-------------|-----|
| `app` | string | sim | Segmento 1 da URL |
| `model` | string | sim | Segmento 2 da URL |
| `id` | string \| number | não | Segmento `<id>/` |
| `action` | string | não | Segmento `<action>/` |
| `params` | objeto | não | Convertido em `query_string` (se `query_string` ausente) por `new URLSearchParams(params).toString()` |
| `query_string` | string | não | Sufixo `?<qs>` |
| `form` | objeto/`FormData` | não | Corpo de `PATCH`/`PUT`/`POST` (padrão `{}`) |
| `progress` | objeto (config axios) | não | Config adicional, ex. `onUploadProgress` (padrão `{}`) |

### 7.2 Resposta

Todas as funções retornam a `Promise` do axios (resposta completa: `data`, `status`, …), exceto `hasPermission` (`Promise<boolean>`). O formato do corpo é o da API gerada na feature 005.

### 7.3 Resposta de `GET /api/version` consumida por `authStore`

```json
{ "name": "…", "description": "…", "version": "…", "user": { "...": "somente se autenticado" } }
```

## 8. Estruturas de qualidade

| Arquivo | Estrutura |
|---------|-----------|
| `package.json` | `name`, `version`, `type:"module"`, `scripts{dev,build,preview,lint,format}`, `dependencies`, `devDependencies` |
| `eslint.config.js` | Array flat config: `files-to-lint`, `files-to-ignore`, `js.configs.recommended`, `skipFormatting`, `flat/strongly-recommended`, regra `vue/multi-word-component-names: off` |
| `.prettierrc.json` | `{$schema, semi:false, singleQuote:true, arrowParens:"avoid"}` |
| `.editorconfig` | Seção `[*.{js,jsx,mjs,cjs,ts,tsx,mts,cts,vue}]` |

## 9. Migrações

Nenhuma. A feature não cria nem altera tabelas.
