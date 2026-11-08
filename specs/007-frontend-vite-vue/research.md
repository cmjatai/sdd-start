# Pesquisa e Decisões Técnicas: Frontend Vite + Vue 3

Decisões inferidas do código e dos comentários de `vite.config.js`, `backend/settings/frontend.py`, `_templates/base.html` e `_frontend/src/`.

## Decisões

### D1 — Vite com `root` em `_frontend/src` e `package.json` na raiz do repositório

- **Decisão**: `root = _frontend/src`, `publicDir = _frontend/src/assets`, `outDir = _frontend/dist/frontend`; `package.json`, `vite.config.js` e `eslint.config.js` na raiz.
- **Justificativa**: O projeto é Django-cêntrico; manter `npm` na raiz simplifica `Dockerfile`s (`COPY package.json vite.config.js`, `ADD _frontend`) e o *volume* de dev (`.:/var/project/backend`). A subpasta final `frontend/` em `dist` faz o `collectstatic` produzir `collectedstatic/frontend/…`, um *namespace* para não colidir com estáticos do Django/admin.
- **Alternativas**: Vite em `_frontend/` com `package.json` próprio (mais isolado, porém duplica scripts e complica o volume); emitir direto em `STATIC_ROOT` (acopla o build ao `collectstatic`).

### D2 — `base` distinto para dev e produção

- **Decisão**: `base` = `/static/` (dev) e `/static/frontend/` (produção).
- **Justificativa**: Em dev o `django-vite` gera `http://localhost:5173/<STATIC_URL>…` (ex.: `/static/main.js`, `/static/@vite/client`), então o servidor Vite precisa responder sob `/static/`. Em produção os arquivos ficam em `collectedstatic/frontend/` e URLs internas (CSS `url()`, imports dinâmicos) devem ser `/static/frontend/…`.
- **Alternativas**: `static_url_prefix` do `django-vite` para ajustar o dev (não usado); base única.

### D3 — Manifesto do Vite reescrito por plugin `closeBundle`

- **Decisão**: plugin `postbuild-commands` prefixa `frontend/` em `file`, `css` e `assets` no `.vite/manifest.json`.
- **Justificativa**: `django-vite` resolve `static(<file>)`; como `STATICFILES_DIRS` aponta para `_frontend/dist` (e não para `dist/frontend`), o caminho estático real é `frontend/<arquivo>`. As chaves do manifesto (`main.js`, `views/Error404.vue`) continuam relativas ao `root`, por isso `vite_asset 'main.js'` funciona.
- **Alternativas**: configurar `STATICFILES_DIRS=[("frontend", dist/frontend)]` (resolveria no Django sem reescrever o manifesto); `build.manifest` com caminho customizado.

### D4 — Django como dono das páginas; Vue compila o DOM em tempo de execução

- **Decisão**: `base.html` envolve o corpo em `<div id="emf"><emf-app>…</emf-app></div>`; o app raiz usa `delimiters ['[[',']]']`; o alias `vue → vue/dist/vue.esm-bundler.js` inclui o compilador.
- **Justificativa**: Permite usar componentes Vue (`<emf-alert>`, `<router-view>`) dentro de templates Django sem reescrever as páginas; `[[ ]]` evita conflito com `{{ }}` do Django (Constituição, princípio V).
- **Alternativas**: SPA completo (perde o controle do Django sobre sessão e SEO); componentes isolados montados por ilhas (mais complexo).

### D5 — Componentes globais assíncronos com prefixo `emf-`

- **Decisão**: `registerComponents.js` separa `rootComponents` (declarados no app raiz, usados no template do Django) e `globalComponents` (registrados por `app.component`, disponíveis em todo componente); ambos com `defineAsyncComponent`.
- **Justificativa**: Divide o bundle e evita importações repetidas; "emf = Backend Frontend" evita colisão com tags HTML/Bootstrap.
- **Alternativas**: importação local em cada componente.

### D6 — `unplugin-vue-components` + `BootstrapVueNextResolver`

- **Decisão**: auto-importação de componentes `B*` do `bootstrap-vue-next`.
- **Justificativa**: Elimina `import` manual e permite *tree-shaking*; `createBootstrap()` registra diretivas/plugins.
- **Alternativas**: registro global completo (bundle maior).

### D7 — PWA por `injectManifest` com registro manual do service worker

- **Decisão**: `VitePWA` com `strategies:'injectManifest'`, SW próprio mínimo (`service-worker.js`) e `navigator.serviceWorker.register('/service-worker.js', {scope:'/', type:'module'})` somente em `import.meta.env.PROD`. `manifestTransforms` prefixa as URLs de *precache* com `/static/frontend/`.
- **Justificativa**: O SW precisa ser servido da raiz (`/service-worker.js`) para ter `scope '/'` — o Nginx faz *alias* para `collectedstatic/frontend/service-worker.js` (e `/manifest.json` idem). Controle manual da URL (comentário: "controle total da URL") evita o `registerSW.js` gerado. `Service-Worker-Allowed: /` no dev server permite escopo `/` a partir de `/static/…`.
- **Alternativas**: `generateSW` (menos controle), `injectRegister: 'auto'`.

### D8 — Chunks por pacote (`manualChunks`)

- **Decisão**: cada pacote de `node_modules` é um chunk (FontAwesome por subpacote).
- **Justificativa**: Melhor cache do navegador e do SW. O comentário "expansivo" no código indica que a alternativa `vendor` único foi considerada e rejeitada (`'vendor'` junta tudo; o comentário marca a abordagem como "expansiva" e a deixou comentada). Um `manualChunks` por objeto (`group1`, `group2`) também ficou comentado.
- **Alternativas**: chunk `vendor` único; agrupamentos fixos por arquivo.

### D9 — ESLint como parte do pipeline do Vite

- **Decisão**: `@nabla/vite-plugin-eslint` com `failOnError: true`; `npm run lint` com `--fix`.
- **Justificativa**: Garante estilo/erros antes do deploy (Constituição VIII); `skipFormatting` delega formatação ao Prettier.
- **Alternativas**: apenas lint em CI.

### D10 — Modo de cores do Bootstrap 5.3 adaptado

- **Decisão**: script derivado do *color-mode toggler* oficial (docs do Bootstrap, CC BY 3.0), importado em `js/utils/index.js` pelo `main.js`; seletor de tema no rodapé de `base.html`; `data-bs-theme="auto"` inicial no `<html>`.
- **Justificativa**: O Bootstrap 5.3 já oferece `data-bs-theme`; o SCSS usa `@include color-mode(dark)`.
- **Alternativas**: tema só por CSS `prefers-color-scheme` (sem escolha do usuário).

### D11 — `DJANGO_VITE_DEV_MODE` condicionado a `DEBUG`

- **Decisão**: `DJANGO_VITE_DEV_MODE = config(..., default=True) and DEBUG`.
- **Justificativa**: Evita que produção aponte acidentalmente para `localhost:5173` (Constituição II: modo decidido por `DEBUG`).
- **Alternativas**: variável independente.

### D12 — Ativos de `publicDir` também em `STATICFILES_DIRS` apenas em `DEBUG`

- **Decisão**: `_frontend/src/assets` é adicionado a `STATICFILES_DIRS` quando `DEBUG=True`.
- **Justificativa**: Em dev o Django (`runserver`) serve `/static/imgs/…`, `/static/bootstrap-icons/…` e `favicon` sem precisar do build; em produção os mesmos arquivos vêm do `copyPublicDir` do build, sob `frontend/`.
- **Alternativas**: sempre incluir (duplicaria arquivos no `collectstatic`).

### D13 — Bootstrap Icons vendorizado

- **Decisão**: cópia do pacote em `_frontend/src/assets/bootstrap-icons` e `$bootstrap-icons-font-dir: "/static/bootstrap-icons/font/fonts"` em `custom/bootstrap.scss`.
- **Justificativa**: Fontes/SVGs acessíveis por URL estática (SVGs individuais podem ser usados em templates).
- **Alternativas**: usar apenas o pacote npm (as fontes iriam para chunks com *hash*).

### D14 — Sem testes JS

- **Decisão**: validação por `lint` + `build`.
- **Justificativa**: Esqueleto mínimo. **Recomendação**: adicionar Vitest + `@vue/test-utils` em evolução futura; fora do escopo da reconstrução fiel.

## Particularidades, dívidas técnicas e riscos observados

Legenda da recomendação: **Replicar** (manter fiel ao código atual, necessário para fidelidade) ou **Corrigir** (melhoria recomendada para derivados). **O estado atual é replicar para fidelidade**; as correções ficam como evolução.

| # | Observação (confirmada no código) | Impacto | Recomendação |
|---|-----------------------------------|---------|--------------|
| P1 | `JsonViewer.vue` importa `~@/js/resources` (inexistente; o correto seria `~@/js/utils/resources`) e chama `Utils.Utils.patchModel('etl','layout', props.objectid, formData)` com 4 argumentos posicionais, enquanto `patchModel(m)` recebe um único objeto `{app, model, id, form, progress}`. Referencia o modelo `etl.layout` (inexistente neste esqueleto). Não está registrado em `registerComponents.js` nem usado em templates. `Markdown.vue` só é usado por ele. | Componente morto/legado; se importado, o build falha por módulo não resolvido. | **Replicar** (mantê-lo como está); **Corrigir** removendo-o ou ajustando import e chamada (`Resources.Utils.patchModel({app, model, id, form})`). |
| P2 | `AuthStore` lê `data_connect.is_authenticated` e `data_connect.permissions` de `GET /api/version`, mas `AppVersionView` (feature 005) devolve `{name, description, version[, user]}`. | `isAuthenticated` é sempre `false`, `permissions` sempre `[]`, `hasPermission()` sempre `false`. | **Replicar**; **Corrigir** derivando de `data_connect.user` ou estendendo a view. |
| P3 | `Resources.Utils.hasPermission` usa `OPTIONS /api/auth/session/?perm=<perm>` esperando `{status:'ok'}`; `AppSessionAuthView` não implementa essa verificação. | Sempre resolve `false` (via `catch`/resposta sem `status`). | **Replicar**; **Corrigir** implementando o endpoint ou removendo o método. |
| P4 | `src/sw.js` e `src/service-worker.js` são quase idênticos (`sw.js` tem comentário e um `fetch` vazio; sem ponto e vírgula só no segundo). Apenas `service-worker.js` é usado (`VitePWA.filename`). | Duplicidade; ESLint/Prettier tratam ambos. | **Replicar**; **Corrigir** removendo `sw.js`. |
| P5 | `main.js` registra `globalComponents` **depois** de `.mount('#emf')`. | Componentes globais usados na primeira renderização síncrona podem não resolver; funciona hoje porque são assíncronos. | **Replicar**; **Corrigir** registrando antes do `mount`. |
| P6 | `main.js` importa e registra todos os ícones FontAwesome (`fas`, `far`, `fab`) e chama `dom.watch()`. | Chunks pesados (`free-solid/regular/brands-svg-icons`). | **Replicar**; **Corrigir** registrando só os ícones usados. |
| P7 | `axios.defaults` (cache, CSRF) são configurados em `main.js` **e** em `js/utils/resources/index.js`. | Duplicidade inofensiva. | **Replicar**. |
| P8 | `esbuild.pure` remove `console.log`/`console.debug` em produção, mas o código usa `console.error` (mantido) e o `vite.config.js` tem `console.debug` ruidoso (inclusive `manualChunks` para cada módulo e o manifesto completo). | Logs extensos no build; nenhum impacto funcional. | **Replicar**. |
| P9 | `start_url`/`scope` do manifesto PWA em modo não produtivo apontam para `http://localhost:9099/`; `theme_color` do manifesto (`#114d81`) difere do `<meta name="theme-color" content="#5B9F91">` de `base.html` e das cores da marca (`#EE6600`). | Inconsistência visual; manifesto de dev não é usado (`<link rel="manifest">` só com `DEBUG` falso). | **Replicar**; **Corrigir** alinhando cores/URLs. |
| P10 | `includeAssets` lista `robots.txt`, que não existe em `_frontend/src/assets`; o `Nginx` mapeia `/robots.txt` para `collectedstatic/robots.txt`. `registerSW.js` é gerado mas não usado. | Sem erro; arquivos supérfluos. | **Replicar**. |
| P11 | O plugin `inject` (`$`, `jQuery`, `_`) usa `include: ['src/**/*.js','src/**/*.vue']`, caminhos relativos ao `cwd` (raiz do repositório), mas os fontes estão em `_frontend/src/**`; além disso o comentário afirma "should be first" e o plugin está depois do PWA. Nenhum arquivo atual usa `$`/`_`. (Inferido: padrões não casam; `dist` não contém chunks de `jquery`/`lodash`.) | Injeção provavelmente inativa; jQuery/lodash não entram no bundle. | **Replicar** (manter dependências e config); **Corrigir** ajustando `include` para `_frontend/src/**` se quiser usar. |
| P12 | `Error404.vue` usa `src="/imgs/logo_backend.svg"` (caminho absoluto sem `/static/`). Em dev o Vite serve `publicDir` na raiz do `base`… e em produção `/imgs/…` não é servido pelo Nginx (só `/static/frontend/imgs/…`). `base.html` e `index.html` usam `{% static '/imgs/logo_backend…svg' %}` → `/static/imgs/…`, que só existe com `DEBUG=True` (assets no `STATICFILES_DIRS`). | Imagem pode quebrar em produção (404). | **Replicar**; **Corrigir** usando `import` do asset ou `/static/frontend/imgs/…`. |
| P13 | `custom/bootstrap.scss` define `$bootstrap-icons-font-dir: "/static/bootstrap-icons/font/fonts"`; em produção a fonte está em `/static/frontend/bootstrap-icons/font/fonts/…`. | Ícones `bi-*` por fonte podem não carregar em produção. | **Replicar**; **Corrigir** ajustando o caminho por modo. |
| P14 | `base.html` usa `<svg><use href="#svg-emais">` (cabeçalho em telas pequenas e rodapé em telas grandes) mas só existe `<symbol id="svg-perfil">`; o `<svg>` oculto inclui símbolos não usados (`bootstrap`). Também há classes `fa fa-sign-out` do FontAwesome 4 (renderiza o ícone só com compat). | Elementos vazios/ícones ausentes. | **Replicar**. |
| P15 | `styles.scss` importa fontes do Google (`fonts.googleapis.com`) em tempo de execução; o Sass emite avisos de `@import` descontinuado e funções globais (Dart Sass). | Dependência de rede externa, privacidade (LGPD) e avisos de depreciação. | **Replicar**; **Corrigir** hospedando as fontes localmente / migrando para `@use`. |
| P16 | `_icon-list.scss` não é importado por nenhum arquivo. Em `styles.scss` há referências a `$primary` (variável do Bootstrap) e a classes da cabeçalho de "casa legislativa" (`.header-casa-legislativa`, `.img-brasao`) herdadas de outro projeto. | Código morto. | **Replicar**. |
| P17 | `main.js` usa `delimiters` apenas no app raiz; componentes SFC (compilados em build) não são afetados — porém templates dentro de `emf-app` herdam o compilador em tempo de execução. | Cuidado ao usar `{{ }}` em componentes SFC (usar `{{ }}` normalmente) e `[[ ]]` no HTML do Django. | **Replicar**. |
| P18 | O `eslintPlugin` roda no `vite build` com `failOnError: true`; o `eslint.config.js` marca `EventBus` e `bootstrap` como globais. `npm run lint` usa `--fix` (altera arquivos). | Um erro de lint quebra o build/Docker. | **Replicar**. |
| P19 | `vite.config.js` tem `cache: false` no ESLint e polling no `server.watch` (necessário para volumes Docker). | Mais CPU em dev. | **Replicar**. |
| P20 | O Dockerfile de produção não copia `package-lock.json` (linha comentada) nem `eslint.config.js`/`.prettierrc.json`; o `ADD _frontend` e `COPY vite.config.js` bastam para o build, mas o ESLint plugin roda sem `eslint.config.js` na imagem (o plugin tenta carregar a config do `cwd`). Confirmar na feature 011. | Build de produção pode divergir do local (lint sem config ou instalação sem lockfile). | **Replicar** (descrever); **Corrigir** copiando `package-lock.json` e a config de ESLint. |
| P21 | `AuthStore.loginStatus()` não trata erros (sem `.catch`), e `App.vue` o chama no `setup` sem tratamento. | Rejeição não tratada se `/api/version` falhar. | **Replicar**. |
| P22 | `Markdown.vue` usa `v-html` com `markdown-it` padrão (`html:false`), que escapa HTML bruto; `JsonViewer.vue` renderiza links `http…` de strings do JSON (`target="_blank"` sem `rel="noopener"`). | Baixo risco; atenção a novos usos do `v-html`. | **Replicar**. |
| P23 | O service worker faz *precache* de `**/*.{js,css,html,png,jpg,jpeg,svg,gif,woff2}`, incluindo todos os ícones vendorizados (~2000 SVGs de `bootstrap-icons`) se estiverem em `dist/frontend`. | Instalação do SW baixa muitos arquivos (tamanho do *precache*). | **Replicar**; **Corrigir** excluindo `bootstrap-icons/icons/**` via `globIgnores`. |
| P24 | `ESLint` ignora `dist` mas `files` inclui apenas `_frontend/src/**`; `vite.config.js` e `eslint.config.js` não são lintados (e usam `// eslint-disable-next-line` apenas por ruído). | Nenhum. | **Replicar**. |

> Nota sobre P12/P13/P20: parte dessas afirmações envolve comportamento em produção que depende das features 010/011 (Dockerfile e Nginx). São observações derivadas da leitura estática do código; devem ser verificadas em um ambiente de produção real.
