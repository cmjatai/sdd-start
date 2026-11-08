# Contrato: Integração Vite ↔ Django (build, manifesto, `base` e `STATIC`)

**Feature**: `007-frontend-vite-vue` | Referências: `vite.config.js`, `backend/settings/frontend.py`, `_templates/base.html`, `startfront-dev.sh`

## 1. Scripts npm (`package.json`)

| Script | Comando | Efeito |
|--------|---------|--------|
| `dev` | `vite` | Servidor de desenvolvimento em `0.0.0.0:5173` (HMR, polling, sem abrir navegador) |
| `build` | `vite build` | Gera `_frontend/dist/frontend/` com manifesto ajustado (ESLint bloqueante) |
| `preview` | `vite preview` | Serve o build localmente |
| `lint` | `eslint _frontend/src/ --fix` | Lint com correção automática |
| `format` | `prettier --write _frontend/src/` | Formatação |

`./startfront-dev.sh` (executável): `npm install` → `npm run dev`.

## 2. Matriz de URLs: dev × produção

| Aspecto | Desenvolvimento (`DEBUG=True` e `DJANGO_VITE_DEV_MODE=True`) | Produção (`DEBUG=False`) |
|---------|--------------------------------------------------------------|--------------------------|
| `mode` do Vite | `development` | `production` |
| `base` | `/static/` | `/static/frontend/` |
| Cliente HMR | `<script type="module" src="http://localhost:5173/static/@vite/client">` | (vazio) |
| Entrada | `<script type="module" src="http://localhost:5173/static/main.js">` | `<script type="module" src="/static/frontend/main-<hash>.js">` + `<link rel="stylesheet" href="/static/frontend/main-<hash>.css">` (+ `modulepreload` dos imports) |
| Fonte do manifesto Django | não lido | `STATIC_ROOT/frontend/.vite/manifest.json` (`collectedstatic/…`) |
| Arquivos de `publicDir` | `/static/imgs/…`, `/static/favicon.ico` via `STATICFILES_DIRS` (`_frontend/src/assets`) | `/static/frontend/imgs/…`, `/static/frontend/favicon.ico` (cópia do build) |
| `<link rel="manifest">` | não emitido | `<link rel="manifest" href="/manifest.json">` |
| Service worker | não registrado | `/service-worker.js` (escopo `/`) |

Regra de consistência: `base` ↔ `STATIC_URL ("static/")` ↔ Nginx `/static/` → `collectedstatic` ↔ prefixo `/static/frontend/` do `manifestTransforms` do PWA devem coincidir.

## 3. Saída do build

- `outDir`: `_frontend/dist/frontend` (esvaziado a cada build); `assetsDir: ''` (arquivos na raiz de `outDir`).
- Entrada única: `main` = `_frontend/src/main.js`.
- Arquivos esperados: `main-<hash>.js`, `main-<hash>.css`, *chunks* por pacote e por view/componente dinâmico, `.vite/manifest.json`, `manifest.json`, `service-worker.js`, `registerSW.js`, cópia de `_frontend/src/assets/**`.
- `collectstatic` (com `STATICFILES_DIRS=[_frontend/dist]`) produz `collectedstatic/frontend/…` → servido em `/static/frontend/…`.

## 4. Contrato do manifesto (`.vite/manifest.json`)

Pré-condição (saída crua do Vite): `file: "main-<hash>.js"`, `css: ["main-<hash>.css"]`.
Pós-condição (plugin `postbuild-commands`, hook `closeBundle`, somente se `command === 'build'`):

1. Lê `./_frontend/dist/frontend/.vite/manifest.json` (`fs.readFileSync`, `JSON.parse`).
2. Para cada chave: `entry.file = 'frontend/' + entry.file`; `entry.css = entry.css.map(c => 'frontend/' + c)` (se existir); `entry.assets = entry.assets.map(a => 'frontend/' + a)` (se existir).
3. `imports`/`dynamicImports` ficam inalterados (são chaves do manifesto).
4. Grava com `JSON.stringify(manifest, null, 2)`.

Consumo: `django-vite` aplica `static(entry.file)`; como `STATICFILES_DIRS` aponta para `_frontend/dist`, `frontend/main-<hash>.js` → `/static/frontend/main-<hash>.js`. A chave consultada pelo template é `main.js`.

## 5. Contrato de settings (`backend/settings/frontend.py`)

| Variável | Regra |
|----------|-------|
| `DJANGO_VITE_DEV_MODE` | env (padrão `True`, `bool`) **E** `DEBUG` |
| `DJANGO_VITE["default"]["dev_mode"]` | `DJANGO_VITE_DEV_MODE` |
| `DJANGO_VITE["default"]["manifest_path"]` | `(DJANGO_VITE_ASSETS_PATH if DJANGO_VITE_DEV_MODE else STATIC_ROOT)/frontend/.vite/manifest.json` |
| `STATICFILES_DIRS` | `[<raiz>/_frontend/dist]`, + `<raiz>/_frontend/src/assets` se `DEBUG` |
| `STATIC_URL` / `STATIC_ROOT` | `"static/"` / `<raiz>/collectedstatic` |
| `django-vite` (padrões) | `dev_server_protocol=http`, `dev_server_host=localhost`, `dev_server_port=5173`, `static_url_prefix=""` |

`backend.settings.fake` (usado no `collectstatic` da imagem de produção): `DJANGO_VITE_DEV_MODE=False`, `manifest_path = _frontend/dist/frontend/.vite/manifest.json`.

## 6. Contrato do template (`_templates/base.html`)

- `{% load i18n static django_vite common_tags menus %}`
- `<head>`: `{% vite_hmr_client %}` e `{% vite_asset 'main.js' %}` (nessa ordem).
- `<html data-bs-theme="auto" lang="pt-br">`.
- `<div id="emf"><emf-app> … </emf-app></div>` envolve todo o conteúdo da página.
- Âncoras exigidas pelos scripts: `#header-main` (scrollheader), `#bd-theme` e `[data-bs-theme-value]` (colormodes).
- `<link rel="manifest" href="/manifest.json">` somente com `{% if not DEBUG %}`.
- `_templates/404.html`: `{% extends 'base.html' %}` + `{% block base_content %}<emf-error-404></emf-error-404>{% endblock %}`.

## 7. Variáveis de ambiente

| Variável | Padrão | Efeito |
|----------|--------|--------|
| `DJANGO_VITE_DEV_MODE` | `True` | Liga o modo dev do `django-vite` (só vale com `DEBUG=True`) |
| `DEBUG` | (feature 001) | Ver matriz do item 2 |
| `VITE_*` | — | Apenas registrada em log por `loadEnv` |

## 8. Portas e serviços

| Porta | Serviço | Observação |
|-------|---------|------------|
| 5173 | Vite dev server (contêiner `front`, feature 010) | Acessado diretamente pelo navegador (`localhost:5173`) |
| 9099 | Aplicação Django em dev (valor usado no `start_url` do manifesto não produtivo) | Herdado |
| Nginx `/static/`, `/service-worker.js`, `/manifest.json` | feature 011 | `collectedstatic` e `collectedstatic/frontend/*` |
