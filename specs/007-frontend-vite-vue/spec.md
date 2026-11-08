# Especificação da Funcionalidade: Frontend Vite + Vue 3 integrado ao Django

**Branch da Funcionalidade**: `007-frontend-vite-vue`

**Criado em**: 2026-11-08

**Status**: Implementado (engenharia reversa)

**Entrada**: "Engenharia reversa do código existente: `vite.config.js`, `package.json`, `eslint.config.js`, `.prettierrc.json`, `.editorconfig`, `backend/settings/frontend.py`, integração `{% vite_hmr_client %}`/`{% vite_asset 'main.js' %}` em `_templates/base.html`, código-fonte em `_frontend/src/` (main.js, App.vue, registerComponents.js, roteador, stores Pinia, utilitários, cliente axios de `/api`, modo de cores, cabeçalho rolável, 404, componentes utilitários, SCSS, assets), PWA (manifest e service worker), seletor de tema claro/escuro/auto e `startfront-dev.sh`."

> Fora do escopo desta funcionalidade (pertencem à `006-sincronizacao-tempo-real`, apenas citados): `WebSocketManager`, `SyncStore`, `MessageStore`, `EventBus`, `DisplayMessage`/`AlertMessage`, `TimerWorkerService` e `views/WsTest.vue`. O `App.vue` e o `main.js` os consomem, mas seu comportamento é especificado na feature 006. Os contêineres Docker que executam o Vite (dev) e a imagem que o compila (prod) são tratados em `010-docker-desenvolvimento` e `011-docker-producao`.

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Desenvolver o frontend com recarga a quente (Prioridade: P1)

Como pessoa desenvolvedora, quero subir o servidor do Vite junto com o Django em modo de desenvolvimento e ver minhas alterações em Vue/SCSS refletidas no navegador sem build manual, para trabalhar com ciclo de feedback curto.

**Por que esta prioridade**: Sem o servidor de desenvolvimento do Vite e a integração `django-vite` em modo dev, não há como evoluir o frontend; é a base de toda a feature.

**Teste Independente**: Com `DEBUG=True` e `DJANGO_VITE_DEV_MODE=True`, executar `./startfront-dev.sh` (ou `npm run dev`) e abrir qualquer página Django; o HTML deve referenciar `http://localhost:5173/static/@vite/client` e `http://localhost:5173/static/main.js`, e editar um `.vue`/`.scss` deve atualizar a página.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e `DJANGO_VITE_DEV_MODE=True`, **Quando** uma página que estende `base.html` é renderizada, **Então** o HTML contém a tag do cliente HMR (`@vite/client`) e a tag do módulo `main.js` apontando para o servidor Vite na porta 5173 com o prefixo `/static/`.
2. **Dado** o servidor Vite em execução, **Quando** um arquivo em `_frontend/src` é alterado (inclusive em volume Docker), **Então** a mudança é detectada (observação por *polling*) e propagada ao navegador.
3. **Dado** `./startfront-dev.sh` executado em um diretório sem `node_modules`, **Quando** o script roda, **Então** ele executa `npm install` e em seguida `npm run dev`, escutando em `0.0.0.0:5173` sem abrir navegador.
4. **Dado** um erro de lint (ESLint com severidade *error*) em um arquivo do frontend, **Quando** o Vite processa o arquivo, **Então** o erro é exibido e a compilação do módulo falha; avisos (*warnings*) são apenas emitidos.

---

### História de Usuário 2 - Servir o frontend compilado em produção (Prioridade: P1)

Como operador, quero que `npm run build` gere pacotes otimizados que o Django referencie por meio de um manifesto, para que a aplicação em produção sirva os arquivos pelo Nginx em `/static/frontend/`.

**Por que esta prioridade**: É o caminho de entrega real do frontend; sem o build e o manifesto ajustado, nenhuma página tem JS/CSS em produção.

**Teste Independente**: Executar `npm run build` e conferir que `_frontend/dist/frontend/.vite/manifest.json` existe e que as chaves `file`, `css` e `assets` de cada entrada começam com `frontend/`; com `DJANGO_VITE_DEV_MODE=False`, `{% vite_asset 'main.js' %}` gera `<script type="module" src="/static/frontend/main-<hash>.js">` e `<link rel="stylesheet">` correspondentes.

**Cenários de Aceitação**:

1. **Dado** o código-fonte do frontend, **Quando** `npm run build` é executado, **Então** os arquivos são emitidos em `_frontend/dist/frontend/` (sem subpasta de assets), com manifesto do Vite habilitado e a pasta de saída esvaziada a cada build.
2. **Dado** o build concluído, **Quando** o plugin pós-build roda, **Então** o `.vite/manifest.json` é reescrito com o prefixo `frontend/` em `file`, `css` e `assets` de cada entrada, de modo que `django-vite` + `STATICFILES_DIRS` resolvam `frontend/<arquivo>` em `/static/`.
3. **Dado** `mode=production`, **Quando** o build roda, **Então** o `base` é `/static/frontend/`, `console.log`/`console.debug` são removidos do código por `esbuild.pure` e não são gerados *source maps*.
4. **Dado** pacotes de `node_modules`, **Quando** o Rollup divide os *chunks*, **Então** cada pacote vira um *chunk* próprio nomeado pelo pacote (para `@fortawesome/*`, pelo nome do subpacote, ex.: `free-solid-svg-icons`).
5. **Dado** `DEBUG=False`, **Quando** o Django inicializa, **Então** `DJANGO_VITE_DEV_MODE` é `False` mesmo que a variável de ambiente seja `True`, e o manifesto é lido de `STATIC_ROOT/frontend/.vite/manifest.json`.

---

### História de Usuário 3 - Páginas Django hospedam a aplicação Vue (Prioridade: P1)

Como usuário final, quero que as páginas renderizadas pelo Django (cabeçalho, menus, formulários, CRUD) funcionem com a camada Vue por cima, para ter componentes interativos sem abandonar o HTML do servidor.

**Por que esta prioridade**: O Django continua dono das páginas (Constituição, princípio V); a montagem do Vue em `#emf` é o ponto de contato entre os dois mundos.

**Teste Independente**: Abrir `/` e inspecionar o DOM: `div#emf` contém `<emf-app>` e o HTML do Django foi processado pelo Vue (slots), com `[[ ]]` como delimitadores de interpolação e `{{ }}` preservado para o Django.

**Cenários de Aceitação**:

1. **Dado** uma página que estende `base.html`, **Quando** o navegador carrega `main.js`, **Então** o aplicativo Vue é montado em `#emf` com os plugins Vue Router, Pinia e Bootstrap-Vue-Next, e `emf-app` renderiza o conteúdo do slot (HTML do Django) mais o contêiner de mensagens e um `div#modalApp`.
2. **Dado** o template contendo `{{ variavel }}` do Django, **Quando** o Vue processa o DOM, **Então** as chaves duplas não são interpretadas pelo Vue (delimitadores do Vue são `[[` e `]]`).
3. **Dado** um componente global registrado com prefixo `emf-` (ex.: `<emf-alert>`, `<emf-refresh-page>`), **Quando** usado em qualquer template/componente, **Então** é resolvido sem importação explícita, carregado sob demanda.
4. **Dado** requisições `axios` do frontend, **Quando** são métodos não seguros, **Então** enviam o token CSRF lido do cookie `csrftoken` no cabeçalho `X-CSRFToken`; requisições GET enviam cabeçalhos para desabilitar cache.
5. **Dado** elementos com `data-bs-toggle="popover"` na página, **Quando** o aplicativo inicializa, **Então** cada um recebe uma instância de `bootstrap.Popover`.

---

### História de Usuário 4 - Alternar tema claro, escuro ou automático (Prioridade: P2)

Como usuário final, quero escolher entre tema claro, escuro ou automático (seguindo o sistema operacional) e ter a escolha lembrada, para ler o site com conforto.

**Por que esta prioridade**: Funcionalidade visível a todos os usuários e presente em todas as páginas (rodapé), mas não bloqueia o restante.

**Teste Independente**: Abrir qualquer página, usar o seletor no rodapé (`#bd-theme`) e verificar que o atributo `data-bs-theme` de `<html>` muda, que `localStorage.theme` guarda `light`/`dark`/`auto` e que o tema persiste ao recarregar.

**Cenários de Aceitação**:

1. **Dado** nenhum tema salvo e preferência do sistema escura, **Quando** a página carrega, **Então** `data-bs-theme="dark"` é aplicado (claro se o sistema for claro).
2. **Dado** o menu do seletor, **Quando** o usuário clica em "Light", "Dark" ou "Auto", **Então** o valor é gravado em `localStorage` (chave `theme`), `data-bs-theme` é atualizado (em "auto", resolve-se pela preferência do sistema), o item ativo recebe a classe `active` e `aria-pressed="true"`, o ícone do botão reflete o tema e o foco volta ao botão.
3. **Dado** o tema salvo `auto` (ou ausente), **Quando** a preferência `prefers-color-scheme` do sistema muda, **Então** o tema é reaplicado sem recarregar; se o tema salvo for `light` ou `dark`, a mudança do sistema é ignorada.

---

### História de Usuário 5 - Instalar e usar como PWA (Prioridade: P2)

Como usuário final, quero poder instalar o site como aplicativo (PWA), para acessá-lo com ícone próprio em tela cheia.

**Por que esta prioridade**: Recurso complementar de experiência; depende do build de produção (P1).

**Teste Independente**: Em produção (HTTPS ou localhost), abrir o site, verificar `<link rel="manifest" href="/manifest.json">`, o registro do `service-worker.js` com escopo `/` e a oferta de instalação do navegador.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=False`, **Quando** `base.html` é renderizado, **Então** inclui `<link rel="manifest" href="/manifest.json">`; com `DEBUG=True` o link não é emitido.
2. **Dado** build de produção, **Quando** o manifesto é gerado, **Então** contém `id=br.leg.go.jatai.sddstart`, nome/nome curto/descrição `Sdd Start 2026`, `display=fullscreen`, `lang=pt-BR`, `background_color=#ffffff`, `theme_color=#114d81`, `start_url`/`scope` `/` e ícones 192x192 e 512x512 em `/static/frontend/imgs/icons/`.
3. **Dado** `import.meta.env.PROD` e navegador com suporte, **Quando** `main.js` executa, **Então** registra `/service-worker.js` com `scope: '/'` e `type: 'module'`; em desenvolvimento nenhum service worker é registrado.
4. **Dado** o service worker ativo, **Quando** instala/ativa, **Então** chama `skipWaiting()` e `clients.claim()` e pré-armazena em cache (Workbox `precacheAndRoute`) os arquivos do build com URLs prefixadas por `/static/frontend/`.

---

### História de Usuário 6 - Identidade visual, cabeçalho e página 404 (Prioridade: P2)

Como usuário final, quero um visual consistente da marca (cores, fontes, cabeçalho que encolhe ao rolar) e uma página 404 amigável, para navegar com clareza.

**Por que esta prioridade**: Dá a aparência do produto; os estilos são compartilhados por todas as features de interface (CRUD, login, menus).

**Teste Independente**: Rolar uma página e verificar que `#header-main` ganha a classe `header-scrolled`; abrir uma URL inexistente renderizando `404.html` e ver o componente `emf-error-404` com código 404 e link "Voltar para página inicial".

**Cenários de Aceitação**:

1. **Dado** uma página com `#header-main`, **Quando** `window.scrollY > 0`, **Então** o cabeçalho recebe `header-scrolled` (e perde ao voltar ao topo); a verificação é ativada 2 segundos após `DOMContentLoaded` e também executada imediatamente nesse momento.
2. **Dado** uma página sem `#header-main`, **Quando** o script de rolagem executa, **Então** nada acontece e nenhum erro é lançado.
3. **Dado** o template `404.html`, **Quando** renderizado, **Então** exibe `<emf-error-404>`: logotipo, "404", "Página não encontrada", mensagem explicativa e botão para `/`.
4. **Dado** o roteador Vue, **Quando** o caminho for `/wstest/`, **Então** carrega sob demanda a view `WsTest.vue` (feature 006); **Quando** o caminho não casar com nenhuma rota do roteador, **Então** a rota *catch-all* `error_404` renderiza `Error404.vue`.
5. **Dado** estilos SCSS, **Quando** compilados, **Então** disponibilizam utilitários Bootstrap `min-vh-{50..100}` e `avatar-{1..9}` (altura e largura em `rem`) e a paleta da marca (`#EE6600` primária, `#853d05` secundária, `#7D7E7F` plataforma), além de variantes para modo escuro e impressão.

---

### História de Usuário 7 - Consumir a API REST e o estado de autenticação (Prioridade: P3)

Como desenvolvedor de frontend, quero um cliente HTTP único para `/api/` e uma store de autenticação, para reutilizar chamadas nos componentes.

**Por que esta prioridade**: Infraestrutura para componentes futuros; hoje apenas `App.vue` consulta `/api/version`.

**Teste Independente**: No console do navegador/teste unitário, chamar `Resources.Utils.getVersion()` e ver `GET /api/version`; `authStore.loginStatus()` preenche `data_connect` com a resposta.

**Cenários de Aceitação**:

1. **Dado** `Resources.Utils`, **Quando** `login(username, password)` é chamado, **Então** envia `POST /api/auth/session` com `withCredentials`; `logout()` envia `DELETE /api/auth/session`; `getVersion()` envia `GET /api/version`.
2. **Dado** os métodos `fetch`, `patchModel`, `putModel`, `postModel`, `deleteModel`, **Quando** chamados com `{app, model, id, action, form, params|query_string}`, **Então** montam URLs `/api/<app>/<model>/[<id>/][<action>/][?query]` e usam o verbo correspondente.
3. **Dado** `App.vue` montado, **Quando** inicializa, **Então** chama `authStore.loginStatus()` e guarda a resposta em `data_connect`.
4. **Dado** `data_connect` sem os campos `is_authenticated`/`permissions` (o que o backend atual devolve), **Quando** `isAuthenticated`/`permissions`/`hasPermission(perm)` são lidos, **Então** retornam `false`/`[]`/`false`.

---

### História de Usuário 8 - Qualidade de código do frontend (Prioridade: P3)

Como mantenedor, quero ESLint + Prettier + EditorConfig padronizados, para manter o estilo (sem ponto e vírgula, aspas simples, 2 espaços).

**Por que esta prioridade**: Exigido pela Constituição (princípios V e VIII), mas não altera o comportamento do produto.

**Teste Independente**: Executar `npm run lint` e `npm run format` e `npm run build` sem erros em um clone limpo.

**Cenários de Aceitação**:

1. **Dado** `_frontend/src/**/*.{js,mjs,jsx,vue}`, **Quando** `npm run lint` roda, **Então** o ESLint (config plana) aplica `js.recommended`, `flat/strongly-recommended` do Vue e desativa regras de formatação conflitantes com o Prettier, com `vue/multi-word-component-names` desligada, e corrige automaticamente (`--fix`).
2. **Dado** `npm run format`, **Quando** executado, **Então** o Prettier formata `_frontend/src/` com `semi: false`, `singleQuote: true`, `arrowParens: "avoid"`.
3. **Dado** `.editorconfig`, **Quando** um editor abre arquivos `js/jsx/mjs/cjs/ts/tsx/mts/cts/vue`, **Então** aplica UTF-8, indentação por 2 espaços, nova linha final e remoção de espaços à direita.

---

### Casos de Borda

- **`DJANGO_VITE_DEV_MODE=True` com `DEBUG=False`**: o modo dev é desligado (a variável é combinada com `DEBUG` por E lógico); produção nunca aponta para o servidor Vite.
- **`DJANGO_VITE_DEV_MODE` ausente**: assume `True`, mas só vale quando `DEBUG=True`.
- **Servidor Vite fora do ar em dev**: as páginas Django carregam, porém sem JS/CSS/tema/Vue (o HTML referencia `localhost:5173`).
- **Build sem executar antes do `collectstatic`**: `STATICFILES_DIRS` inclui `_frontend/dist`; se `dist/frontend/.vite/manifest.json` não existir, `django-vite` falha ao renderizar `vite_asset` em modo produção.
- **Ativos do `publicDir`**: `_frontend/src/assets` é copiado para a raiz do build (`dist/frontend/favicon.ico`, `imgs/…`, `bootstrap-icons/…`); em `DEBUG=True` a mesma pasta também entra em `STATICFILES_DIRS`, de modo que `/static/imgs/logo_backend.svg` e `/static/bootstrap-icons/font/fonts/…` funcionam em dev; em produção esses caminhos só existem sob `/static/frontend/…`.
- **Placeholders `[[ ]]` vs `{{ }}`**: o Vue compila o HTML do Django em tempo de execução, por isso o alias `vue → vue/dist/vue.esm-bundler.js` (build com compilador) é obrigatório.
- **Componentes globais registrados após `mount()`**: `main.js` registra `globalComponents` depois de `.mount('#emf')`; funciona porque são componentes assíncronos resolvidos em renderizações posteriores, mas componentes globais usados na primeira renderização síncrona podem não resolver.
- **Ícone `#svg-emais` inexistente**: `base.html` referencia `<use href="#svg-emais">` (visível em telas `< lg`), mas não há `<symbol id="svg-emais">`; resultado é ícone vazio (legado).
- **Tema "auto" salvo**: `getPreferredTheme()` devolve `'auto'` quando `localStorage.theme='auto'`; só na ausência de valor usa-se a preferência do sistema.
- **Seletor de tema ausente**: se `#bd-theme` não existir na página, `showActiveTheme` retorna sem erro (o tema ainda é aplicado).
- **Service worker em desenvolvimento**: `devOptions.enabled=false` e o registro manual só ocorre com `import.meta.env.PROD`; o manifesto de dev aponta `start_url`/`scope` para `http://localhost:9099/` (valor herdado, não usado porque o `<link rel="manifest">` não é emitido com `DEBUG=True`).
- **`JsonViewer.vue` é legado/morto**: importa `~@/js/resources` (caminho inexistente) e chama `patchModel` com assinatura antiga; não é registrado em `registerComponents.js` nem usado em templates — não deve ser importado sem correção.
- **`AuthStore`/`hasPermission`**: `/api/version` devolve `name`, `description`, `version` e (autenticado) `user`; não devolve `is_authenticated` nem `permissions`; `Resources.Utils.hasPermission` usa `OPTIONS /api/auth/session/?perm=` que o backend não implementa (retorna `false` por `catch`).
- **`sw.js` vs `service-worker.js`**: `sw.js` é uma versão antiga (com *handler* de `fetch` vazio e comentário); apenas `service-worker.js` é usado pelo `VitePWA`.
- **Fontes do Google**: `styles.scss` importa Roboto Condensed e Rubik de `fonts.googleapis.com`; sem internet, caem nas fontes do sistema.
- **ESLint bloqueante**: com `failOnError: true`, um erro de lint interrompe o build de produção (e a imagem Docker).

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**Build, desenvolvimento e configuração**

- **FR-001**: O sistema DEVE usar o Vite (`root` = `_frontend/src`) com os plugins Vue (`@vitejs/plugin-vue`), `vite-plugin-pwa`, `@rollup/plugin-inject`, `@nabla/vite-plugin-eslint`, `unplugin-vue-components` (com `BootstrapVueNextResolver`) e um plugin próprio `postbuild-commands`.
- **FR-002**: O `base` do Vite DEVE ser `/static/` em desenvolvimento e `/static/frontend/` quando `mode === 'production'`.
- **FR-003**: O servidor de desenvolvimento DEVE escutar em `0.0.0.0:5173`, sem abrir navegador, usar *polling* na observação de arquivos e enviar o cabeçalho `Service-Worker-Allowed: /`.
- **FR-004**: O build DEVE emitir em `_frontend/dist/frontend` (`assetsDir: ''`, `manifest: true`, `emptyOutDir: true`, `copyPublicDir: true`, `target: 'esnext'`, `minify: 'esbuild'`), com a entrada única `main` = `_frontend/src/main.js` e `publicDir` = `_frontend/src/assets`.
- **FR-005**: Em `mode === 'production'` o build NÃO DEVE gerar *source maps* e DEVE remover `console.log` e `console.debug` (`esbuild.pure`); nos demais modos DEVE gerar *source maps*.
- **FR-006**: Cada pacote de `node_modules` DEVE ir para um *chunk* separado nomeado pelo primeiro segmento do caminho do pacote (para pacotes `@fortawesome/*`, o segundo segmento).
- **FR-007**: Após `vite build` (e somente nele), o plugin pós-build DEVE reescrever `_frontend/dist/frontend/.vite/manifest.json` prefixando `frontend/` em `file`, em cada item de `css` e em cada item de `assets` de todas as entradas.
- **FR-008**: O alias `~@` DEVE resolver para `_frontend/src`; `vue` DEVE resolver para `vue/dist/vue.esm-bundler.js`; as extensões resolvidas incluem `.js`, `.json` e `.vue`.
- **FR-009**: As variáveis globais `$` e `jQuery` (pacote `jquery`) e `_` (pacote `lodash`) DEVEM ser configuradas para injeção automática por `@rollup/plugin-inject` nos arquivos de `src/**/*.js` e `src/**/*.vue` (exceto `src/routers/**`).
- **FR-010**: Os componentes do `bootstrap-vue-next` (ex.: `BButton`) DEVEM ser resolvidos automaticamente em componentes Vue (`unplugin-vue-components`) sem importação explícita.
- **FR-011**: O ESLint DEVE ser executado durante o Vite com `failOnError: true`, `failOnWarning: false`, `cache: false`, emitindo avisos/erros, excluindo `node_modules`, `dist`, `dist-ssr` e `coverage`.
- **FR-012**: O `package.json` DEVE expor os scripts `dev` (`vite`), `build` (`vite build`), `preview` (`vite preview`), `lint` (`eslint _frontend/src/ --fix`) e `format` (`prettier --write _frontend/src/`), com `"type": "module"`.
- **FR-013**: `startfront-dev.sh` DEVE executar `npm install` e depois `npm run dev`.

**Integração com o Django**

- **FR-014**: `backend/settings/frontend.py` DEVE definir `TEMPLATES` (diretório `_templates`, `APP_DIRS=True`, *context processors* incluindo `backend.context_processors.debug`, `debug=DEBUG`), `CRISPY_*` para `bootstrap5`, `STATIC_URL = "static/"`, `STATIC_ROOT = <raiz>/collectedstatic`, `DJANGO_VITE_ASSETS_PATH = <raiz>/_frontend/dist` e `STATICFILES_DIRS = [DJANGO_VITE_ASSETS_PATH]`, acrescentando `_frontend/src/assets` somente quando `DEBUG=True`.
- **FR-015**: `DJANGO_VITE_DEV_MODE` DEVE ser lido da variável de ambiente (padrão `True`, tipo booleano) e combinado por E lógico com `DEBUG`; o dicionário `DJANGO_VITE["default"]` DEVE ter `dev_mode` e `manifest_path` = (`_frontend/dist` em dev, `collectedstatic` caso contrário) + `frontend/.vite/manifest.json`.
- **FR-016**: `_templates/base.html` DEVE carregar `django_vite`, emitir `{% vite_hmr_client %}` e `{% vite_asset 'main.js' %}` no `<head>`, envolver o corpo em `<div id="emf"><emf-app>…</emf-app></div>` e emitir `<link rel="manifest" href="/manifest.json">` somente quando `DEBUG` é falso.
- **FR-017**: `_templates/404.html` DEVE estender `base.html` e renderizar `<emf-error-404>` no bloco `base_content`.
- **FR-018**: `base.html` DEVE conter, antes do `#emf`, um `<svg>` oculto com os símbolos `bootstrap`, `check2`, `circle-half`, `moon-stars-fill`, `sun-fill` e `svg-perfil`.

**Aplicação Vue**

- **FR-019**: `main.js` DEVE: importar `~@/scss/styles.scss`; importar `bootstrap` (JS); registrar na biblioteca do FontAwesome os pacotes `fas`, `far` e `fab` e chamar `dom.watch()`; importar `./js/utils`; criar o app com `components = registerComponents.rootComponents` e `delimiters: ['[[', ']]']`; fornecer `EventBus` (`provide('EventBus')` e `globalProperties.$EventBus`); usar `router`, `createPinia()` e `createBootstrap()`; montar em `#emf`; registrar `globalComponents`.
- **FR-020**: `main.js` DEVE configurar `axios` com `xsrfCookieName='csrftoken'`, `xsrfHeaderName='X-CSRFToken'` e cabeçalhos GET `Cache-Control: no-cache, no-store, must-revalidate`, `Pragma: no-cache`, `Expires: 0`.
- **FR-021**: `registerComponents.js` DEVE exportar `rootComponents` (`emf-app` → `App.vue`; `emf-error-404` → `views/Error404.vue` assíncrono) e `globalComponents` (`FontAwesomeIcon`; `emf-alert` → `components/utils/message/Alert.vue`; `emf-refresh-page` → `components/utils/RefreshPage.vue`, ambos assíncronos). Componentes globais usam o prefixo `emf-`.
- **FR-022**: `App.vue` DEVE renderizar `<slot />`, `DisplayMessage` e `<div id="modalApp">`; no `setup`, DEVE inicializar o `SyncStore` (`initialize()` e `registerModels('utils', ['teste'])`, feature 006) e chamar `authStore.loginStatus()`.
- **FR-023**: O roteador (`js/routers.js`) DEVE usar `createWebHistory()` com a rota `/wstest/` (`name: 'index_link'`, carga preguiçosa de `WsTest.vue`) e a rota `/:pathMatch(.*)` (`name: 'error_404'`, `Error404.vue`, `meta.title='404 - Not Found'`).
- **FR-024**: `AuthStore` (Pinia id `authStore`) DEVE expor o estado `data_connect`, os *getters* `isAuthenticated`, `permissions`, `hasPermission(perm)` e as ações `loginStatus()`, `loginPortal(username, password)`, `logoutPortal()`, todas atualizando `data_connect` com a resposta de `GET /api/version`.
- **FR-025**: `TeleportStore.js` DEVE exportar `activeTeleportId` (`ref(null)`) para coordenar destinos de teleporte.
- **FR-026**: O cliente `js/utils/resources/index.js` DEVE expor `Resources.Utils` com `login`, `logout`, `hasPermission`, `getVersion`, `fetch`, `patchModel`, `putModel`, `postModel`, `deleteModel`, com base `/api`.
- **FR-027**: Os componentes utilitários DEVEM incluir: `Alert.vue` (alerta Bootstrap *info* dispensável com *slot*), `RefreshPage.vue` (recarrega a página após `timeout` ms e, se `show`, exibe contagem regressiva), `Markdown.vue` (renderiza `source` com `markdown-it` e plugins abbr, anchor, footnote, highlightjs, sub, sup, task-lists, toc-done-right) e `JsonViewer.vue` (visualizador/editor JSON legado, ver Casos de Borda).

**Tema, cabeçalho e estilos**

- **FR-028**: O modo de cores DEVE ser aplicado antes da renderização (no carregamento de `main.js`), definir `data-bs-theme` em `<html>`, persistir em `localStorage.theme`, reagir a `prefers-color-scheme` apenas quando o tema salvo não for `light`/`dark`, e acionar o seletor `#bd-theme` com itens `[data-bs-theme-value]` (`light`, `dark`, `auto`) no rodapé de `base.html`.
- **FR-029**: O utilitário `scrollheader` DEVE alternar a classe `header-scrolled` em `#header-main` conforme `window.scrollY > 0`.
- **FR-030**: Os estilos DEVEM definir a paleta da marca, utilitários `min-vh`/`avatar`, layout de `main`, rodapé, cabeçalho (`header.scss`), paginação fixa, ações de contexto do CRUD, tabela, formulários, bloco de login e variações para `color-mode(dark)`, telas ≥768/992/1200 px e impressão; importar Bootstrap 5, estilos do `bootstrap-vue-next` e `bootstrap-icons` (fonte em `/static/bootstrap-icons/font/fonts`).

**PWA**

- **FR-031**: O `VitePWA` DEVE usar `strategies: 'injectManifest'`, `registerType: 'autoUpdate'`, `scope: '/'`, `srcDir: ''`, `filename: 'service-worker.js'`, `manifestFilename: 'manifest.json'`, `devOptions.enabled=false`, `includeAssets: ['favicon.ico','robots.txt']`, `globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,svg,gif,woff2}']` e `manifestTransforms` que prefixam cada URL do *precache* com `/static/frontend/`.
- **FR-032**: O manifesto PWA DEVE conter os valores descritos na História 5; em modo não produtivo `start_url`/`scope` apontam para `http://localhost:9099/` e os ícones usam caminhos relativos `imgs/icons/…`.
- **FR-033**: `service-worker.js` DEVE chamar `precacheAndRoute(self.__WB_MANIFEST)`, `self.skipWaiting()` no `install` e `self.clients.claim()` no `activate`.
- **FR-034**: O registro do *service worker* DEVE ser manual em `main.js` e ocorrer somente quando `'serviceWorker' in navigator` e `import.meta.env.PROD` (URL `/service-worker.js`, `scope: '/'`, `type: 'module'`).

**Qualidade**

- **FR-035**: `eslint.config.js` DEVE aplicar-se a `_frontend/src/**/*.{js,mjs,jsx,vue}`, declarar globais de navegador e Node mais `EventBus` e `bootstrap` (somente leitura), ignorar `**/dist/**`, `**/dist-ssr/**`, `**/coverage/**`, e usar `js.configs.recommended`, `skipFormatting` e `pluginVue.configs['flat/strongly-recommended']`.
- **FR-036**: `.prettierrc.json` DEVE definir `semi: false`, `singleQuote: true`, `arrowParens: "avoid"`; `.editorconfig` DEVE restringir-se a arquivos de frontend.
- **FR-037**: O sistema NÃO DEVE incluir nenhum segredo no código do frontend; o frontend só se comunica com o backend por `/api/` e pelo WebSocket `/ws/sync/` (feature 006).

### Entidades-Chave

Não há tabelas novas. Estruturas relevantes (detalhes em `data-model.md`):

- **Configuração do Vite** (`vite.config.js`): modos, `base`, plugins, `build`, `server`.
- **Manifesto do Vite** (`.vite/manifest.json`): mapa de entradas → `file`, `css`, `assets`, `imports`, `dynamicImports`.
- **Manifesto PWA** (`manifest.json`) e *precache* do Workbox.
- **Settings Django** (`TEMPLATES`, `STATIC_*`, `STATICFILES_DIRS`, `DJANGO_VITE`).
- **Estado do frontend**: `AuthStore.data_connect`, `activeTeleportId`, `localStorage.theme`.
- **Registro de componentes** (`rootComponents`, `globalComponents`).

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: A partir de um clone limpo, `npm install && npm run build` conclui sem erros e gera `_frontend/dist/frontend/main-<hash>.js`, `main-<hash>.css`, `.vite/manifest.json`, `manifest.json` e `service-worker.js`.
- **SC-002**: 100% das entradas do `.vite/manifest.json` que possuem `file`, `css` ou `assets` têm esses valores iniciados por `frontend/` após o build.
- **SC-003**: Com `DEBUG=True` e `DJANGO_VITE_DEV_MODE=True`, `GET /` contém exatamente uma tag para `http://localhost:5173/static/@vite/client` e uma para `http://localhost:5173/static/main.js`; com `DEBUG=False`, nenhuma referência a `5173` aparece e `main.js` resolve para `/static/frontend/main-<hash>.js`.
- **SC-004**: `npm run lint` não reporta erros no código atual (`_frontend/src`).
- **SC-005**: Em produção, nenhum `console.log`/`console.debug` permanece nos *chunks* gerados e nenhum arquivo `.map` é emitido.
- **SC-006**: A alternância de tema altera `data-bs-theme` em menos de 100 ms e o valor sobrevive a recarregamento da página (verificável por `localStorage.theme`).
- **SC-007**: O Lighthouse/DevTools reconhece o manifesto PWA com os ícones de 192 e 512 px e o service worker ativo no escopo `/` em produção.
- **SC-008**: Ao acessar uma rota inexistente, o usuário vê a página 404 com link funcional para `/` (renderizada por `404.html` + `emf-error-404`).

## Premissas

- **Dependências de features**: `001-fundacao-projeto-django` (settings modulares, `zenv.py`, `PROJECT_DIR`, `DEBUG`, `django_vite` em `INSTALLED_APPS`, `backend.context_processors.debug`); `004-crud-generico-menus` e `002-autenticacao-usuarios-auditoria` (templates e classes CSS que `styles.scss`/`base.html` estilizam); `005-api-rest-automatica` (rotas `/api/version`, `/api/auth/session`, `/api/<app>/<modelo>/`); `006-sincronizacao-tempo-real` (SyncStore, MessageStore, EventBus, WebSocketManager, `WsTest.vue`, `DisplayMessage` usados por `App.vue`/`main.js`); `010`/`011` (execução do Vite em Docker e build de produção; Nginx serve `/service-worker.js`, `/manifest.json` e `/static/`).
- **Ambiente**: Node.js 26 (imagem `node:26.13.0-bookworm` no desenvolvimento), npm; as dependências são as de `package.json` (Vite 8, Vue 3.5, Pinia 4, Vue Router 5, Bootstrap 5.3, Bootstrap-Vue-Next 1.2, FontAwesome 7, Axios, jQuery 4, lodash, markdown-it).
- **Execução do Vite**: em desenvolvimento o servidor roda em contêiner separado (`front`) expondo `5173`; o navegador acessa `localhost:5173` diretamente (host/porta padrão do `django-vite`).
- **Navegadores**: suportam ES modules, `esnext`, service workers e `prefers-color-scheme`.
- **Fora do escopo**: testes automatizados de frontend (não há Jest/Vitest/Playwright no repositório); i18n no frontend (textos fixos em português); SSR.
- **jQuery/lodash**: estão configurados para injeção e como dependências, mas nenhum arquivo atual de `_frontend/src` usa `$`/`_`; a injeção só atua se o filtro do plugin casar com os arquivos (ver `research.md`).
- **Segurança**: CORS/`ALLOWED_HOSTS` abertos do esqueleto não são alterados aqui; o CSRF depende do cookie `csrftoken` emitido pelo Django.
