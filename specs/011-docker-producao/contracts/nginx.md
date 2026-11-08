# Contrato: Nginx (HTTP e WebSocket)

Arquivos: `_docker/prod/nginx/nginx_docker.conf` (→ `/etc/nginx/nginx.conf`) e `_docker/prod/nginx/backend_docker.conf` (→ `/etc/nginx/conf.d/backend_docker.conf`). Escuta: porta 80 do contêiner `app`.

## Configuração global (`nginx_docker.conf`)

| Diretiva | Valor |
|---|---|
| `user` | `nginx root` |
| `worker_processes` / `worker_connections` | 1 / 1024 |
| `error_log` / `pid` | `/var/log/nginx/error.log warn` / `/var/run/nginx.pid` |
| `include` | `/etc/nginx/mime.types`; `default_type application/octet-stream` |
| `log_format main` | `$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"`; `access_log /var/log/nginx/access.log main` |
| `sendfile` | `off` |
| `server_tokens` | `off` |
| `keepalive_timeout` | 300 |
| `proxy_connect_timeout` / `proxy_read_timeout` | 75s / 300s |
| gzip | `on`; `gzip_disable "MSIE [1-6]\\.(?!.*SV1)"`; `gzip_proxied any`; `gzip_comp_level 5`; `gzip_vary on`; `gzip_types text/plain text/css text/javascript application/javascript application/x-javascript text/xml application/xml application/rss+xml image/gif image/png image/x-icon image/jpeg image/svg+xml` |
| `include /etc/nginx/conf.d/*.conf` | sim |

## Upstreams (`backend_docker.conf`)

| Nome | Servidor |
|---|---|
| `backend_leg_app_server` | `unix:/var/project/backend/run/gunicorn.sock fail_timeout=0` |
| `backend_channels_server` | `unix:/var/project/backend/run/daphne.sock` |

## Servidor

`listen 80; client_max_body_size 4G; access_log /var/project/backend/logs/nginx-access.log; error_log /var/project/backend/logs/nginx-error.log;`

## Locations (nesta ordem)

| Location | Comportamento |
|---|---|
| `= /robots.txt` | `alias /var/project/backend/collectedstatic/robots.txt` |
| `= /favicon.ico` | `alias /var/project/backend/collectedstatic/favicon.ico` |
| `= /service-worker.js` | `alias /var/project/backend/collectedstatic/frontend/service-worker.js` |
| `= /manifest.json` | `alias /var/project/backend/collectedstatic/frontend/manifest.json` |
| `/static/` | `alias /var/project/backend/collectedstatic/`; `gzip_static on`; `expires 7d`; `add_header Pragma public`; `add_header Cache-Control "public"` (há uma linha comentada de `Access-Control-Allow-Origin` de um domínio do autor) |
| `/mediaredirect/` | `internal`; `alias /var/project/backend_media/media/`; `Pragma: "no-cache"`, `Cache-Control: "no-cache"`, `Expires 0`, `expires 0` |
| `/ws/` | `try_files $uri @proxy_to_ws` |
| `/api` | `try_files $uri @proxy_to_app_api` |
| `/` | `try_files $uri @proxy_to_app` |

## Locations nomeadas

### `@proxy_to_ws` → `http://backend_channels_server`
`proxy_http_version 1.1`; `Upgrade $http_upgrade`; `Connection "upgrade"`; `Host $host`; `X-Real-IP $remote_addr`; `X-Forwarded-For $proxy_add_x_forwarded_for`; `X-Forwarded-Proto https`; `X-Forwarded-Host $server_name`; `proxy_redirect off`.

### `@proxy_to_app` → `http://backend_leg_app_server`
`X-Forwarded-For $proxy_add_x_forwarded_for`; `X-Forwarded-Proto https`; `Host $http_host`; `proxy_connect_timeout 75s`; `proxy_read_timeout 600s`; `proxy_redirect off`.

### `@proxy_to_app_api` → `http://backend_leg_app_server`
Cabeçalhos de resposta: `Access-Control-Allow-Origin '*'`, `Access-Control-Allow-Credentials 'true'`, `Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, HEAD, OPTIONS'`, `Access-Control-Allow-Headers` e `Access-Control-Expose-Headers` com `Access-Control-Allow-Origin,XMLHttpRequest,Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,Keep-Alive,Origin,User-Agent,X-Mx-ReqToken,X-Requested-With`.
Preflight (`$request_method = 'OPTIONS'`): `Allow-Origin '*'`, `Allow-Methods 'GET, POST, PUT, DELETE, HEAD, OPTIONS'`, `Allow-Headers 'Authorization,Accept,DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range'`, `Expose-Headers 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range'`, `Max-Age 1728000`, `Content-Type 'text/plain; charset=utf-8'`, `Content-Length 0`, `return 204`.
Demais: `X-Forwarded-For`, `X-Forwarded-Proto https`, `Host $http_host`, timeouts 75s/600s, `proxy_redirect off`.

## Rotas observáveis (exemplos)

| Requisição | Resultado esperado |
|---|---|
| `GET /static/frontend/favicon.ico` | 200 estático (`Cache-Control: public`) |
| `GET /service-worker.js` | 200, JS do PWA |
| `GET /mediaredirect/x` | 404 (interna) |
| `OPTIONS /api/` | 204 com CORS |
| `GET /api/` | proxy ao Gunicorn + CORS `*` |
| `GET /ws/sync/` (upgrade) | proxy ao Daphne (feature 006) |
| `GET /` | proxy ao Gunicorn |
