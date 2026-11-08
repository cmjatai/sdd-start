# Contrato HTTP: Mídia e Avatar

**Feature**: `009-midia-arquivos-avatar`

## `GET /media/<path>` — `mediapublic_view`

- **Implementação**: `backend.utils.views.MediaPublicView` (rota em `backend/utils/urls.py`: `^media/(?P<path>.*)$`).
- **Permissão**: nenhuma (público, sem login). Somente `GET` (demais métodos → 405 pela `View` do Django).
- **Parâmetro**: `path` — caminho relativo a `MEDIA_ROOT` (pode conter `/`).

| Condição | Resposta |
|---|---|
| `"private"` em `path` (substring) | `404` |
| `DEBUG=True` e arquivo existe | `200`, conteúdo do arquivo (`django.views.static.serve`; MIME por `mimetypes`, `Last-Modified`, `Content-Length`, `If-Modified-Since` → `304`) |
| `DEBUG=True` e arquivo inexistente | `404` (do `serve`) |
| `DEBUG=False` | `200` com corpo vazio e cabeçalhos abaixo; o arquivo é entregue pelo Nginx |

Cabeçalhos com `DEBUG=False`:

| Cabeçalho | Valor |
|---|---|
| `Content-Type` | `application/<extensão>` (`odt` → `application/vnd.oasis.opendocument.text`) |
| `Content-Disposition` | `inline; filename="<último segmento do path>"` |
| `Cache-Control` | `no-cache` |
| `Pragma` | `no-cache` |
| `Expires` | `0` |
| `X-Accel-Redirect` | `/mediaredirect/<path>` |

## `GET /mediaredirect/<path>` (Nginx, interno)

- Definido em `_docker/prod/nginx/backend_docker.conf`; `internal` (requisição externa direta → 404 do Nginx).
- `alias /var/project/backend_media/media/;` — arquivo inexistente → 404 do Nginx.
- Cabeçalhos: `Pragma: no-cache`, `Cache-Control: no-cache`, `Expires: 0`, `expires 0`.
- Não há `location /media/`; o corpo máximo de requisição é `client_max_body_size 4G;`.

## `GET /api/version` — `AppVersionView`

- **Permissão**: `AllowAny`. Rota: `re_path(r'^api/version$', AppVersionView.as_view())` em `backend/api/urls.py`.
- **Resposta** `200` JSON: `name`, `description`, `version`; se autenticado, `user = {username, fullname, avatar}`.
- `user.avatar`: `"/static/imgs/perfil.png"` sem avatar; com avatar, URL da miniatura 128x128 recortada por `avatar_cropping` (formato `get_backend().get_thumbnail_url(...)`, sob `MEDIA_URL`).

## Upload do avatar (perfil)

- Formulário `BackendUserChangeForm` (`backend/eauth/forms_auth.py`), `multipart/form-data`, campos `avatar` (arquivo) e `avatar_cropping` (texto `x1,y1,x2,y2`).
- Erro de validação: arquivo > 10 MB → mensagem `The maximum file size is 10.0MiB` (traduzível).
- Limites globais do Django: `DATA_UPLOAD_MAX_NUMBER_FILES=1000`; `FILE_UPLOAD_MAX_MEMORY_SIZE`/`DATA_UPLOAD_MAX_MEMORY_SIZE` = 1512 MB.

## Actions de arquivo da API (contrato dormente)

Para campos `CustomFileField` em modelos derivados (rota esperada, não existente no esqueleto):

| Item | Valor |
|---|---|
| Nome da rota | `backend.api:<app_label>_<model_name>-<campo com '-' no lugar de '_'>`, `kwargs={"pk": <pk>}` |
| Sufixos aceitos | `png`, `jpg`, `jpeg` (opcionalmente `<N>` ou `c<N>` antes do ponto: `120.png`, `c120.jpg`), `pdf`, `zip` |
| Sem renderer compatível | `404` |
| Query de `ResponseFileMixin.response_file` | `text` (texto do PDF), `page` (PNG da página), `dpi` (72–300, arredondado para 72/100/150/200/300), `grade` (`N` ou `x0,y0,x1,y1`), `anon` (termos separados por vírgula; só superusuário), `nocache`, `original` |
| Respostas | PDF → `text/plain; charset=utf-8` ou `image/png`; imagens → arquivo ou miniatura (`N`: miniatura sem corte; `cN`: recorte por `<campo>_cropping`); outros → arquivo; `DEBUG=False` → vazio com `X-Accel-Redirect: /mediaredirect/<original__><nome>` e cabeçalhos no-cache |
| Erros | `404` (`NotFound`) sem item, sem atributo da action ou sem arquivo |

## Template tag

`{% avatar_user <usuário> '<classe-css>' %}` (`{% load common_tags %}`; padrão da classe: `avatar`) — com avatar renderiza `<img class src="{% cropped_thumbnail user 'avatar_cropping' %}">`; sem avatar, `<svg class title="<usuário>"><use href="#svg-perfil"></use></svg>`.
