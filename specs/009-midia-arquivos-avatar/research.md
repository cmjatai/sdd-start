# Pesquisa e Decisões Técnicas: Mídia, Arquivos e Avatar do Usuário

**Feature**: `009-midia-arquivos-avatar` | **Data**: 2026-11-08

## Decisões

### D1. Entrega de mídia pelo Django com `X-Accel-Redirect` em produção
- **Decisão**: `/media/<path>` sempre passa pelo Django (`MediaPublicView`); em produção o Django só decide (bloqueio de `private`) e delega a transferência ao Nginx com `X-Accel-Redirect: /mediaredirect/<path>`; em debug usa `django.views.static.serve`.
- **Justificativa**: permite aplicar regras de acesso em Python sem trafegar bytes pelo Python; o Nginx (`internal`) mantém desempenho e impede acesso direto a `/mediaredirect/`.
- **Alternativas**: `location /media/` direto no Nginx (não permitiria a regra `private`); `FileResponse` do Django (carrega workers Gunicorn); S3/objeto (fora do escopo do esqueleto).

### D2. Convenção `private` por substring no caminho
- **Decisão**: qualquer caminho contendo `private` retorna 404 na rota pública.
- **Justificativa**: convenção simples para que modelos derivados armazenem arquivos sensíveis em `.../private/...` e os sirvam apenas por actions autenticadas da API (por exemplo via `ResponseFileMixin`, que também usa `/mediaredirect/`).
- **Alternativas**: lista de pastas, autenticação na rota, URLs assinadas.

### D3. `MEDIA_ROOT` fora da árvore do código e com caso especial para debug no host
- **Decisão**: `PROJECT_DIR.parent/backend_media/media`; se `DEBUG` e o projeto não está em `/var/project`, usa `/mnt/volumes/backend_media/media`.
- **Justificativa**: em contêiner o volume `backend_media` é montado ao lado do código (`/var/project/backend_media`); no host o mesmo volume fica em `/mnt/volumes` para compartilhar arquivos com os contêineres de dev.
- **Alternativas**: variável de ambiente `MEDIA_ROOT` (não adotada; ver item 13 da tabela de riscos).

### D4. Limites de upload altos e em memória
- **Decisão**: 1512 MB para documentos e `FILE_UPLOAD_MAX_MEMORY_SIZE`/`DATA_UPLOAD_MAX_MEMORY_SIZE` iguais; 1000 arquivos por requisição; 10 MB para imagens.
- **Justificativa**: o domínio de origem do esqueleto trata PDFs grandes e lotes de anexos; evita arquivos temporários em disco para uploads comuns.
- **Alternativas**: valores padrão do Django (2,5 MB) e streaming para disco.

### D5. Miniaturas com `easy-thumbnails` + `django-image-cropping`
- **Decisão**: `crop_corners` como primeiro processador; gerador de origem `backend.utilss.pil_image` (wrapper que delega ao da biblioteca); avatar 128x128 com `ImageRatioField`; jQuery do cropping desativado (`IMAGE_CROPPING_JQUERY_URL=None`) pois o projeto já fornece jQuery/JS próprio.
- **Justificativa**: recorte por seleção do usuário com cache de miniaturas em disco; o wrapper permite customizar o gerador sem alterar settings futuramente.
- **Alternativas**: `sorl-thumbnail`, Pillow direto, recorte no frontend.

### D6. `CustomFileField` aponta o `url` para a action de API do campo
- **Decisão**: a URL do arquivo é a rota `backend.api:<app>_<modelo>-<campo>` (com `pk`), permitindo autorização por modelo (princípio IV) e extensão no final (`.pdf`, `.png`).
- **Justificativa**: arquivos de modelos protegidos não ficam acessíveis pela URL pública; renderers e negociação por sufixo dão compatibilidade com visualizadores que dependem da extensão.
- **Alternativas**: `storage.url` (comentado no código para debug).

### D7. Renderers "vazios" para negociação por sufixo
- **Decisão**: renderers de arquivo existem só para que a negociação aceite sufixos (`pdf`, `png`, `jpg`, `jpeg`, `zip`, `<tamanho>.png`...) e `render` levanta 404; a entrega real ocorre na action que devolve `HttpResponse` direto.
- **Justificativa**: o DRF recusa formatos sem renderer correspondente.
- **Alternativas**: renderers que serializam bytes (exigem passar o conteúdo pelo DRF).

### D8. Gravar o arquivo só após existir `pk` (`SaveModelWithFileMixin`)
- **Decisão**: salvar o objeto sem os arquivos, restaurá-los e salvar novamente.
- **Justificativa**: permite `upload_to` baseado em `instance.pk`.
- **Alternativas**: `post_save` com segundo save; `upload_to` sem `pk` (UUID).

## Particularidades, dívidas técnicas e riscos observados

Recomendação geral: **o estado atual é replicar para fidelidade**; as correções sugeridas devem entrar em evolução controlada (atualizando esta especificação).

| # | Observação | Local | Recomendação |
|---|---|---|---|
| 1 | `CustomFieldFile.url` devolve `""` sempre no esqueleto, pois não existem actions `backend.api:<app>_<modelo>-<campo>`; o `except:` nu esconde também erros reais. | `backend/fields.py` | Replicar; em evolução, capturar `NoReverseMatch` e `ValueError` e registrar log. |
| 2 | `shorten_file_name` renomeia nomes com ≥ 128 caracteres para `f_` + últimos 20 caracteres; pode colidir com outro arquivo (sem unicidade) e usa `os.rename` direto (falha se o arquivo não existe). | `backend/fields.py` | Replicar; corrigir com sufixo único/`get_available_name`. |
| 3 | `delete()` customizado muda `_committed=False` e `name=None` e salva a instância; não usa `FieldFile.delete`. | `backend/fields.py` | Replicar. |
| 4 | Dentro de `_url` há código comentado (`if settings.DEBUG: return self.storage.url(self.name)`). | `backend/fields.py` | Replicar (inerte). |
| 5 | Nenhum modelo usa `CustomFileField` nem `SaveModelWithFileMixin`; o `User` declara `FIELDFILE_NAME = ('avatar',)` mas **não** herda o mixin (atributo inerte). `avatar` é `ImageCropField` (não `CustomFileField`). | `backend/eauth/models.py` | Replicar; ao adotar o mixin, colocá-lo antes de `models.Model`. |
| 6 | `SaveModelWithFileMixin.save` ignora `clean` e repassa `force_insert=True` também no segundo `save` (um INSERT duplicado falharia). | `backend/model_mixins.py` | Corrigir (zerar `force_insert` após o 1º save); estado atual: replicar. |
| 7 | `MediaPublicView` em produção não verifica a existência do arquivo; depende do Nginx (404 vem dele). Sem Nginx (ex.: `DEBUG=False` com `runserver`) responde 200 vazio. | `backend/utils/views.py` | Replicar; documentar a dependência. |
| 8 | O teste `"private" in path` é por substring (pega `nao_private.pdf`, `deprivate/`) e a rota é pública — não há autenticação; arquivos em outras pastas são públicos para quem souber a URL. | `backend/utils/views.py` | Replicar; para segredos usar pasta `private` e actions autenticadas. |
| 9 | Código morto na view: `file_path` calculado e não usado; ramificação `if not mime and ext in [...]` nunca é verdadeira (a função devolve sempre texto) e o `else` repete o cálculo; MIME de imagens sai como `application/png`. | `backend/utils/views.py` | Replicar (corrigir a função `get_mime_type_from_file_extension` com `mimetypes`). |
| 10 | `get_mime_type_from_file_extension` devolve `application/<ext>` para tudo (ex.: `application/jpg`, `application/txt`); há `TODO` para `python-magic`/`mimetypes`. `ResponseFileMixin` corrige só `png/jpg/jpeg`. | `backend/utilss.py` | Replicar; corrigir com `mimetypes.guess_type`. |
| 11 | `MAX_IMAGE_UPLOAD_SIZE` e `MAX_DOC_UPLOAD_SIZE` não são lidos por nenhum código do esqueleto; `avatar_validation` tem 10 MB fixo no código. | `backend/settings/medias.py`, `backend/eauth/models.py` | Replicar; evoluir usando a setting. |
| 12 | `FILE_UPLOAD_MAX_MEMORY_SIZE = 1512 MB` mantém uploads grandes na RAM do worker (risco de memória/DoS); o Nginx aceita 4 GB. | `backend/settings/medias.py`, nginx | Replicar; em produção real reduzir. |
| 13 | `MEDIA_ROOT` não é configurável por variável de ambiente; depende do caminho `/var/project` e do `DEBUG`. Fora do contêiner e sem `DEBUG`, aponta para `<repo>/../backend_media/media`. `MEDIA_CACHE_ROOT` é definido mas não consumido por nenhum código do esqueleto. | `backend/settings/medias.py` | Replicar. |
| 14 | `ResponseFileMixin` não é usado por nenhuma view; importa `fitz` e `pymupdf` (dependência pesada) no topo; em `DEBUG` o método `anon` grava em `/home/leandro/TEMP/pdf_anon.pdf` (caminho pessoal; falha silenciosa pois a exceção é impressa e ignorada); fora de debug **sobrescreve** o PDF original com a versão redigida (destrutivo e irreversível). | `backend/api/mixins.py` | Replicar para fidelidade; corrigir (cópia redigida, caminho configurável) antes de uso real. |
| 15 | `ResponseFileMixin.response_file`: `?original` na miniatura é ignorado; `page` e `dpi` inválidos em `int()` levantam exceção (`page` não está dentro do `try`); `custom_filename` é opcional. Imprime com `print` em `anon`. | `backend/api/mixins.py` | Replicar. |
| 16 | `drfautoapi.JpegRenderer` e `JpgRenderer` aceitam ambos os sufixos (`jpg`/`jpeg`) e `FilesRenderer.render` sempre levanta 404: apenas negocia, não renderiza. | `drfautoapi/__init__.py` | Replicar. |
| 17 | `avatar_validation` usa mensagem em inglês (`'The maximum file size is {0}'`) com `gettext_lazy`: só fica em português se existir tradução no catálogo. | `backend/eauth/models.py` | Replicar; adicionar tradução ao `locale`. |
| 18 | `User.avatar` não valida tipo de arquivo além do que `ImageField` (Pillow) valida; não limpa arquivos antigos ao trocar o avatar (órfãos em `avatars/`). | `backend/eauth/models.py` | Replicar; evoluir com sinal de limpeza. |
| 19 | `AppVersionView` calcula a miniatura com tamanho fixo (128,128) e `get_thumbnail_url` do backend de cropping; se o arquivo do avatar não existir no disco, a geração da miniatura tende a falhar (suposição: a exceção não é tratada na view). | `backend/api/views.py` | Replicar. |
| 20 | `FileFieldCheckMixin._check` produz a mensagem com dois espaços ("campo  'X'") por concatenação de strings; o mixin foi escrito para formulários em PT-BR. | `backend/utilss.py` | Replicar. |
| 21 | O Nginx tem `client_max_body_size 4G` e não há `location /media/`; o cache de mídia é desativado (`no-cache`), então nenhuma mídia é cacheada pelo navegador/proxy. | `_docker/prod/nginx/backend_docker.conf` | Replicar. |
