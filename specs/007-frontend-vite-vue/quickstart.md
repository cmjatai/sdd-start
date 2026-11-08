# Quickstart: validar o Frontend Vite + Vue 3

**Feature**: `007-frontend-vite-vue` | Pré-requisitos: features 001–006 concluídas; Node.js 26 + npm; Python/Django configurados (`.env` com `DEBUG`).

## 1. Instalar dependências e checar a qualidade

```bash
npm install
npm run lint      # ESLint 9 (--fix); deve terminar sem erros
npm run format    # Prettier em _frontend/src/
```

Esperado: nenhuma saída de erro (SC-004). `git diff` mostra apenas ajustes de formatação, se houver.

## 2. Build de produção

```bash
npm run build
```

Esperado (SC-001/SC-002/SC-005):

```bash
ls _frontend/dist/frontend                      # main-<hash>.js, main-<hash>.css, manifest.json, service-worker.js, imgs/, favicon.ico
grep -c '"file": "frontend/' _frontend/dist/frontend/.vite/manifest.json   # todas as entradas com prefixo frontend/
find _frontend/dist/frontend -name '*.map' | wc -l                         # 0
grep -l 'console.log\|console.debug' _frontend/dist/frontend/main-*.js     # sem resultados
```

Um erro do ESLint deve interromper o build (`failOnError: true`).

## 3. Integração Django — modo desenvolvimento

```bash
export DEBUG=True DJANGO_VITE_DEV_MODE=True
./startfront-dev.sh &                           # npm install && npm run dev -> http://localhost:5173
python manage.py runserver 0.0.0.0:9099
curl -s http://localhost:9099/ | grep -E '5173/static/(@vite/client|main.js)'
curl -sI http://localhost:5173/static/main.js   # 200
```

Esperado (SC-003): uma tag para `@vite/client` e uma para `main.js`, ambas em `http://localhost:5173/static/`; nenhum `<link rel="manifest">`. No navegador, editar um `.vue`/`.scss` atualiza a página (HMR, polling).

## 4. Integração Django — modo produção

```bash
npm run build
DEBUG=False DJANGO_VITE_DEV_MODE=True python manage.py collectstatic --noinput
DEBUG=False python manage.py shell -c "from django.conf import settings as s; print(s.DJANGO_VITE)"
```

Esperado: `dev_mode: False` mesmo com `DJANGO_VITE_DEV_MODE=True` (E lógico com `DEBUG`); `manifest_path` em `collectedstatic/frontend/.vite/manifest.json`. A página renderizada contém `/static/frontend/main-<hash>.js`, `<link rel="manifest" href="/manifest.json">` e nenhuma referência a `5173`. Arquivos em `/static/frontend/…` (via Nginx na feature 011 ou `collectstatic`).

## 5. Verificação manual no navegador

| Verificação | Como | Esperado |
|-------------|------|----------|
| Vue montado | Inspecionar `#emf` | `<emf-app>` renderizado, `#modalApp` presente, `{{ }}` do Django resolvido no servidor |
| Tema | Menu `#bd-theme` no rodapé: Light/Dark/Auto | `html[data-bs-theme]` muda; `localStorage.theme` guarda o valor; persiste ao recarregar; `auto` acompanha `prefers-color-scheme` |
| Cabeçalho | Rolar a página | `#header-main` recebe/perde `header-scrolled` |
| 404 | Abrir `/rota-inexistente/` | Página com logo, "404", "Página não encontrada" e link para `/` |
| PWA (produção) | DevTools → Application | Manifest `Sdd Start 2026` com ícones 192/512; SW `/service-worker.js` ativo, escopo `/` |
| CSRF | Requisição `POST` pelo `Resources.Utils` | Cabeçalho `X-CSRFToken` presente |
| API | Console: `Resources.Utils.getVersion().then(r => console.log(r.data))` | `GET /api/version` → `{name, description, version, …}` |
| Rota Vue | Abrir `/wstest/` (se a 006 expõe a rota Django) | Carrega `WsTest.vue` sob demanda |

## 6. Testes automatizados sugeridos (pytest com cliente Django)

Não há testes JS. Cobertura recomendada em `backend/tests.py` ou módulo dedicado:

```python
import pytest
from django.test import override_settings

@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_base_html_inclui_manifest_somente_sem_debug(client):
    resp = client.get("/")
    assert b'rel="manifest"' not in resp.content

def test_settings_dev_mode_depende_de_debug(settings):
    assert settings.DJANGO_VITE["default"]["dev_mode"] in (True, False)
    assert str(settings.STATICFILES_DIRS[0]).endswith("_frontend/dist")

def test_template_404_renderiza_componente(client):
    resp = client.get("/rota-inexistente/")
    assert resp.status_code == 404
    assert b"<emf-error-404>" in resp.content
```

(O 404 depende de `DEBUG=False` e `handler404`/template `404.html`; ajuste conforme a feature 001.)

## 7. Solução de problemas

| Sintoma | Causa provável |
|---------|----------------|
| Página sem estilo/JS em dev | Servidor Vite fora do ar (`localhost:5173`) |
| `django_vite` falha com manifesto ausente | `npm run build` (e `collectstatic`) não executados com `DEBUG=False` |
| Build interrompido por ESLint | Erro de lint em `_frontend/src` (ver `npm run lint`) |
| Ícones `bi-*` ou logo 404 quebrados em produção | Caminhos `/static/…` sem `frontend/` (research P12/P13) |
