# Contrato: Componentes globais `emf-*`, rotas Vue e cliente `Resources`

**Feature**: `007-frontend-vite-vue` | Referências: `_frontend/src/registerComponents.js`, `_frontend/src/js/routers.js`, `_frontend/src/js/utils/resources/index.js`, `_frontend/src/components/utils/`, `_frontend/src/views/`

## 1. Componentes `emf-*`

### 1.1 Componentes raiz (`rootComponents` — usáveis no HTML do Django dentro de `#emf`)

| Tag | Fonte | Carga | Descrição |
|-----|-------|-------|-----------|
| `<emf-app>` | `App.vue` | direta | Raiz: `<slot />` + `<DisplayMessage />` + `<div id="modalApp" ref="modalApp" />`; no `setup` inicia `SyncStore` e `authStore.loginStatus()` |
| `<emf-error-404>` | `views/Error404.vue` | assíncrona | Página 404 (usada por `_templates/404.html`) |

### 1.2 Componentes globais (`globalComponents` — registrados com `app.component` após o `mount`)

| Tag | Fonte | Props | Slots / eventos |
|-----|-------|-------|-----------------|
| `FontAwesomeIcon` | `@fortawesome/vue-fontawesome` | as da biblioteca | — |
| `<emf-alert>` | `components/utils/message/Alert.vue` | — | slot padrão = texto; alerta `alert-info` dispensável (`btn-close`) |
| `<emf-refresh-page>` | `components/utils/RefreshPage.vue` | `timeout` (Number, obrigatório, `> 0`, ms), `show` (Boolean, obrigatório), `enabled` (Boolean, padrão `true`) | slot padrão = mensagem antes de "esta página atualizará em …"; recarrega com `window.location.reload()` após `timeout` |

Exemplo de uso em template Django:

```html
<emf-alert>Registro salvo.</emf-alert>
<emf-refresh-page :timeout="30000" :show="true">Atualização automática:</emf-refresh-page>
```

### 1.3 Componentes não registrados

| Componente | Situação |
|------------|----------|
| `components/utils/Markdown.vue` | Prop `source` (String, padrão `""`); renderiza com `markdown-it` + plugins; só usado por `JsonViewer.vue` |
| `components/utils/JsonViewer.vue` | Legado/morto (research P1); não importar sem corrigir |
| `components/utils/message/{AlertMessage,DisplayMessage}.vue`, `views/WsTest.vue` | Feature 006 |

### 1.4 Regras

- Nova tag global: prefixo `emf-`, chave em `globalComponents` (ou `rootComponents` se precisa existir já na primeira renderização) com `defineAsyncComponent(() => import('~@/…'))`.
- Delimitadores do app raiz: `[[ ]]`; `{{ }}` é do Django.
- Componentes `B*` do Bootstrap-Vue-Next são auto-importados (`unplugin-vue-components`).

## 2. Rotas Vue (`js/routers.js`)

`createRouter({ history: createWebHistory(), routes })`; exporta `routes` (nomeado) e `router` (padrão).

| Caminho | `name` | Componente | Observação |
|---------|--------|------------|------------|
| `/wstest/` | `index_link` | `() => import('~@/views/WsTest.vue')` | `children: []`; feature 006; template `wstest_index.html` usa `<router-view>` |
| `/:pathMatch(.*)` | `error_404` | `() => import('~@/views/Error404.vue')` | `meta: { title: '404 - Not Found', description: 'Page not found' }` |

O roteador só atua sobre elementos `<router-view>`/`<router-link>` presentes no HTML; as demais páginas são do Django (navegação por requisição completa).

## 3. Cliente `Resources` (`js/utils/resources/index.js`)

`import Resources from '~@/js/utils/resources'` → `Resources.Utils`. Base `/api`. Padrões do axios reaplicados: GET sem cache, `xsrfCookieName='csrftoken'`, `xsrfHeaderName='X-CSRFToken'`.

| Método | HTTP | URL | Corpo / config | Retorno |
|--------|------|-----|----------------|---------|
| `login(username, password)` | POST | `/api/auth/session` | `{username, password}`, `withCredentials: true` | Promise axios |
| `logout()` | DELETE | `/api/auth/session` | — | Promise axios |
| `hasPermission(permission)` | OPTIONS | `/api/auth/session/?perm=<permission>` | `withCredentials: true` | `Promise<boolean>` (`data.status === 'ok'`; erro → `false`) |
| `getVersion()` | GET | `/api/version` | — | Promise axios |
| `fetch(m, method='GET')` | `method` | `/api/<app>/<model>/[<id>/][<action>/][?<qs>]` | — | Promise axios |
| `patchModel(m)` | PATCH | `/api/<app>/<model>/[<id>/][<action>/]` | `m.form \|\| {}`, config `m.progress \|\| {}` | Promise axios |
| `putModel(m)` | PUT | idem `patchModel` | idem | Promise axios |
| `postModel(m)` | POST | `/api/<app>/<model>/[<action>/]` | `m.form \|\| {}`, `m.progress \|\| {}` | Promise axios |
| `deleteModel(m)` | DELETE | `/api/<app>/<model>/<id>/` | — | Promise axios |

Descritor `m`: ver `data-model.md` §7.1. Rotas e permissões do lado servidor: feature `005-api-rest-automatica` (e `002` para `/api/auth/session`). `hasPermission` depende de um recurso não implementado no backend (research P3).

## 4. `authStore` (Pinia `authStore`, `js/stores/pinea/AuthStore.js`)

| Membro | Contrato |
|--------|----------|
| `loginStatus()` | `GET /api/version` → guarda `data_connect`; retorna `response.data` |
| `loginPortal(u, p)` | `POST /api/auth/session` → `GET /api/version` |
| `logoutPortal()` | `DELETE /api/auth/session` → `GET /api/version` |
| `isAuthenticated`, `permissions`, `hasPermission(perm)` | Derivados de `data_connect.is_authenticated`/`permissions` (hoje `false`/`[]`/`false`) |

## 5. Utilitários de DOM (efeitos colaterais de `js/utils/index.js`)

| Utilitário | Gatilho | Contrato |
|------------|---------|----------|
| `colormodes` | Importação (aplica tema) + `DOMContentLoaded` | `localStorage.theme`; `html[data-bs-theme]`; `#bd-theme`; `[data-bs-theme-value]`; ícone `svg use` do botão ativo; `aria-label` `"<texto> (<tema>)"` |
| `scrollheader` | `DOMContentLoaded` + 2 s | `#header-main.header-scrolled` conforme `scrollY > 0`; ausente → no-op |

## 6. Estilos expostos

Utilitários Bootstrap `min-vh-{50..100}` (`vh`), `avatar-{1..9}` (`1rem…9rem`, altura e largura); variáveis `$color_logo_backend_sddstart: #EE6600`, `$color_logo_backend_mais: #853d05`, `$color_logo_backend_plataforma: #7D7E7F`; classes `.header-scrolled`, `.color-modes`, `.bi.theme-icon`.
