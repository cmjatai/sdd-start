# Especificação da Funcionalidade: Mídia, Arquivos e Avatar do Usuário

**Branch da Funcionalidade**: `009-midia-arquivos-avatar`
**Criado em**: 2026-11-08
**Status**: Implementado (engenharia reversa)
**Entrada**: "Engenharia reversa do código existente: mídia e arquivos — `CustomFieldFile`/`CustomFileField` (`backend/fields.py`), settings de mídia (`backend/settings/medias.py`), `MediaPublicView` e rota `media/<path>` (`backend/utils/views.py`, `backend/utils/urls.py`), helpers de arquivo de `backend/utilss.py`, `SaveModelWithFileMixin` (`backend/model_mixins.py`), avatar do usuário (`backend/eauth/models.py`, `backend/utils/templatetags/common_tags.py`, `_templates/eauth/user/avatar.html`, `backend/api/views.py`), `ResponseFileMixin` (`backend/api/mixins.py`), renderers de arquivo de `drfautoapi/__init__.py` e o bloco `/mediaredirect/` do Nginx de produção."

**Pré-requisitos (features anteriores)**: `001-fundacao-projeto-django` (settings modulares, `zenv.py`, `backend/utilss.py`, `backend/model_mixins.py`), `002-autenticacao-usuarios-auditoria` (modelo `User`, formulário de perfil), `005-api-rest-automatica` (`drfautoapi`, namespace `backend.api`, `AppVersionView`). Docker/Nginx completos em `010-docker-desenvolvimento` e `011-docker-producao`; aqui só o que toca a mídia.

> **Escopo importante**: o esqueleto entrega a **infraestrutura de mídia** e o **avatar do usuário**. Nenhum modelo do esqueleto usa `CustomFileField`, nenhum modelo usa `SaveModelWithFileMixin` e nenhuma view usa `ResponseFileMixin`; ou seja, o suporte a "arquivo servido por action da API" está pronto, porém **dormente**, aguardando modelos derivados. O único campo de arquivo real é o `avatar` do `User` (que usa `ImageCropField`, não `CustomFileField`).

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Servir arquivos enviados em `/media/` com segurança (Prioridade: P1)

Como visitante ou usuário, quero abrir a URL pública de um arquivo enviado (`/media/<caminho>`) e receber o arquivo, enquanto arquivos em pastas privadas nunca são entregues por essa rota.

**Por que esta prioridade**: sem entrega de mídia nada do que é enviado (avatares, anexos) é visível; a regra de "private" é a barreira mínima de confidencialidade.

**Teste Independente**: com `DEBUG=True`, gravar `MEDIA_ROOT/avatars/x.png` e `MEDIA_ROOT/private/a.pdf`; `GET /media/avatars/x.png` → 200 com a imagem; `GET /media/private/a.pdf` → 404. Em produção (`DEBUG=False`), `GET /media/avatars/x.png` → resposta com `X-Accel-Redirect: /mediaredirect/avatars/x.png`.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e um arquivo existente em `MEDIA_ROOT`, **quando** `GET /media/<caminho>`, **então** o arquivo é servido pelo servidor de estáticos do Django (`django.views.static.serve`) a partir de `MEDIA_ROOT`.
2. **Dado** qualquer modo e um `<caminho>` que contenha a substring `private`, **quando** `GET /media/<caminho>`, **então** a resposta é 404 (sem consultar o disco).
3. **Dado** `DEBUG=False`, **quando** `GET /media/<caminho>`, **então** a resposta tem corpo vazio, `Content-Type` deduzido da extensão, `Content-Disposition: inline; filename="<nome>"`, cabeçalhos `Cache-Control: no-cache`, `Pragma: no-cache`, `Expires: 0` e `X-Accel-Redirect: /mediaredirect/<caminho>`.
4. **Dado** o Nginx de produção, **quando** ele recebe `X-Accel-Redirect: /mediaredirect/<caminho>`, **então** serve o arquivo de `/var/project/backend_media/media/<caminho>` (localização `internal`, inacessível diretamente pelo cliente) com cabeçalhos de não-cache.
5. **Dado** uma requisição sem autenticação, **quando** acessa `/media/<caminho>` público, **então** funciona (a rota não exige login).

---

### História de Usuário 2 - Avatar do usuário com enquadramento (Prioridade: P1)

Como usuário autenticado, quero enviar uma foto de perfil, definir o enquadramento quadrado (128x128) e vê-la no cabeçalho das páginas e na identificação da sessão do frontend; sem foto, quero ver uma imagem padrão.

**Por que esta prioridade**: é a única funcionalidade de arquivo visível ao usuário final no esqueleto.

**Teste Independente**: no perfil (`BackendUserChangeForm`), enviar uma imagem de até 10 MB e salvar; `GET /api/version` (rota de `AppVersionView`, ver feature 005) autenticado devolve `user.avatar` apontando para uma miniatura 128x128 sob `/media/`; sem avatar devolve `/static/imgs/perfil.png`.

**Cenários de Aceitação**:

1. **Dado** um usuário sem avatar, **quando** `AppVersionView` responde, **então** `user.avatar == "/static/imgs/perfil.png"`; e o template `avatar_user` mostra o ícone SVG `#svg-perfil` com `title` igual ao usuário.
2. **Dado** um usuário com avatar e `avatar_cropping` definido, **quando** `AppVersionView` responde, **então** `user.avatar` é a URL da miniatura gerada com `size=(128,128)`, `box=avatar_cropping`, `crop=True`, `detail=True`.
3. **Dado** um arquivo de avatar maior que 10 MB, **quando** o formulário é validado, **então** ocorre erro de validação "The maximum file size is 10.0MiB" (traduzível) no campo avatar.
4. **Dado** um usuário com avatar, **quando** o template `{% avatar_user user 'avatar-2' %}` é renderizado, **então** produz `<img class="avatar-2" src="<miniatura enquadrada por avatar_cropping>">`.
5. **Dado** a edição de perfil, **quando** o formulário é exibido, **então** o campo `avatar` usa `ImageCropWidget` e `avatar_cropping` usa `CropWidget` (seleção visual do enquadramento), sem a classe CSS padrão no widget do avatar.
6. **Dado** um usuário sem foto, **quando** abre o formulário, **então** a seleção de enquadramento mostra o texto de ajuda "A configuração do Avatar é possível após a atualização da fotografia.".

---

### História de Usuário 3 - Limites de upload e geração de miniaturas configurados (Prioridade: P2)

Como operador, quero que o projeto aceite uploads grandes (documentos até 1512 MB, até 1000 arquivos por requisição, imagens de até 10 MB) e gere miniaturas com recorte configurável, sem ajustes manuais.

**Por que esta prioridade**: a infraestrutura de mídia só é utilizável por modelos derivados com esses limites e o pipeline de miniaturas corretos.

**Teste Independente**: importar `django.conf.settings` e verificar `MAX_DOC_UPLOAD_SIZE == 1512*1024*1024`, `MAX_IMAGE_UPLOAD_SIZE == 10*1024*1024`, `DATA_UPLOAD_MAX_NUMBER_FILES == 1000`, `THUMBNAIL_PROCESSORS[0] == "image_cropping.thumbnail_processors.crop_corners"`, `THUMBNAIL_SOURCE_GENERATORS == ("backend.utilss.pil_image",)`.

**Cenários de Aceitação**:

1. **Dado** `DEBUG=True` e o projeto fora do contêiner (caminho do projeto sem `/var/project`), **quando** as settings carregam, **então** `MEDIA_ROOT = /mnt/volumes/backend_media/media` e `MEDIA_CACHE_ROOT = /mnt/volumes/backend_media/media_cache`.
2. **Dado** produção ou contêiner de dev (`/var/project/backend`), **quando** as settings carregam, **então** `MEDIA_ROOT = <pai do projeto>/backend_media/media` (ex.: `/var/project/backend_media/media`) e `MEDIA_CACHE_ROOT = <pai>/backend_media/media_cache`.
3. **Dado** `MEDIA_URL = "/media/"`, **quando** um arquivo é referenciado por `.url` padrão do Django, **então** a URL começa com `/media/`.
4. **Dado** uma miniatura solicitada com `box`, **quando** `easy-thumbnails` processa, **então** o recorte `crop_corners` é aplicado antes dos processadores padrão.
5. **Dado** o campo `User.avatar`, **quando** o `easy-thumbnails` abre a imagem de origem, **então** usa `backend.utilss.pil_image` (que delega ao gerador `pil_image` da biblioteca, com `exif_orientation` repassado).

---

### História de Usuário 4 - Campo de arquivo servido pela API (`CustomFileField`) (Prioridade: P3)

Como pessoa desenvolvedora de um projeto derivado, quero declarar campos `CustomFileField` em modelos e obter automaticamente a URL da action de arquivo correspondente na API (`backend.api:<app>_<modelo>-<campo>`), além de nomes de arquivo longos encurtados e exclusão que remove o arquivo do disco.

**Por que esta prioridade**: capacidade para projetos derivados; nada no esqueleto a exercita (nenhum modelo declara `CustomFileField` e as actions de arquivo não existem), logo é P3.

**Teste Independente**: com um modelo de teste com `CustomFileField` e uma rota registrada `backend.api:<app>_<modelo>-<campo>` (kwarg `pk`), `instancia.campo.url` devolve a rota (com sufixo `.<ext>` se terminar em `/`); sem a rota devolve `""`.

**Cenários de Aceitação**:

1. **Dado** um campo `arquivo` preenchido, **quando** `.url` é lido e a rota `backend.api:<app>_<modelo>-arquivo` (underscores do nome do campo trocados por `-`) existe com `pk`, **então** devolve a URL reversa; se ela termina em `/`, a barra é removida e `.<extensão do arquivo>` é anexada.
2. **Dado** um campo vazio ou uma rota inexistente, **quando** `.url` é lido, **então** devolve `""` (nenhuma exceção é propagada).
3. **Dado** um nome de arquivo (último segmento) com 128 caracteres ou mais, **quando** `shorten_file_name()` é chamado, **então** o arquivo é renomeado no disco para `f_` + últimos 20 caracteres do nome, o campo é atualizado e a instância é salva; nomes menores não mudam.
4. **Dado** um arquivo preenchido, **quando** `campo.delete(save=True)` é chamado, **então** o arquivo é fechado, removido do armazenamento, o campo fica `None` e a instância é salva; com `save=False` não salva; campo vazio é no-op.
5. **Dado** a negociação de conteúdo da API, **quando** a URL termina com sufixo `png`, `jpg`, `jpeg`, `pdf` ou `zip` (ou `<tamanho>.png` etc.), **então** só renderers cujo `format` combine são considerados; sem combinação resulta 404.

---

### História de Usuário 5 - Salvar modelos com arquivo (`SaveModelWithFileMixin`) e validar formulários (`FileFieldCheckMixin`) (Prioridade: P3)

Como pessoa desenvolvedora, quero que o arquivo seja gravado só depois de o registro ter `pk` (para `upload_to` dependente do `pk`) e que formulários com arquivo informem erros claros.

**Por que esta prioridade**: utilitários para modelos derivados; não usados pelo esqueleto.

**Teste Independente**: modelo de teste com `SaveModelWithFileMixin` e `FIELDFILE_NAME = ("arquivo",)`: ao criar com arquivo, o primeiro `save()` ocorre sem arquivo, o segundo com; formulário com `FileFieldCheckMixin` e arquivo ausente do disco acusa a mensagem de arquivo inexistente.

**Cenários de Aceitação**:

1. **Dado** um objeto novo (sem `pk`) com arquivos, **quando** `save()`, **então** os campos listados em `FIELDFILE_NAME` são zerados, o objeto é salvo (obtém `pk`), os arquivos são restaurados e salvos em seguida.
2. **Dado** um objeto existente, **quando** `save()`, **então** salva diretamente uma vez.
3. **Dado** um formulário com `FileFieldCheckMixin` cujo campo de arquivo referencia um arquivo inexistente no disco, **quando** `clean()`, **então** levanta `ValidationError` com "Arquivo referenciado no campo '<rótulo>' inexistente! Marque a opção Limpar e Salve.".
4. **Dado** um erro de validação do campo de arquivo que começa com "Certifique-se de que o arquivo" (nome longo), **quando** `clean()`, **então** a mensagem é reescrita para "Certifique-se de que o nome do arquivo no campo '<rótulo>' …".

---

### História de Usuário 6 - Helpers de arquivo reutilizáveis (Prioridade: P3)

Como pessoa desenvolvedora, quero funções utilitárias para tipo MIME por extensão, hash de arquivo e `ResponseFileMixin` para entregar arquivos/PDF por actions de ViewSet.

**Por que esta prioridade**: biblioteca de apoio sem consumidor no esqueleto.

**Teste Independente**: `get_mime_type_from_file_extension("a.odt") == "application/vnd.oasis.opendocument.text"`, `("a.pdf") == "application/pdf"`, `("a.png") == "application/png"`; `hash_sha512(<caminho ou arquivo aberto>)` devolve o SHA-512 hexadecimal (128 caracteres).

**Cenários de Aceitação**:

1. **Dado** um nome de arquivo, **quando** `get_mime_type_from_file_extension`, **então** `odt` vira o MIME OpenDocument e qualquer outra extensão vira `application/<extensão>`.
2. **Dado** um caminho (str) ou arquivo binário, **quando** `hash_sha512`, **então** lê em blocos de 4096 bytes e devolve o hexdigest; arquivos abertos pela função são fechados, os recebidos não.
3. **Dado** uma view com `ResponseFileMixin` e `action` igual ao nome de um campo de arquivo, **quando** `response_file` roda, **então** aplica as regras detalhadas em FR-032 a FR-040.

---

### Casos de Borda

- `MediaPublicView` testa `"private" in path` como **substring** (ex.: `/media/docs/nao_privateX.pdf` também dá 404, e `deprivate` idem); não há checagem de `..`, delegada ao `view_static_server` em DEBUG e ao Nginx em produção.
- Em produção a view **não verifica existência** do arquivo: responde 200 com `X-Accel-Redirect` mesmo que o arquivo não exista; quem devolve 404 é o Nginx. Sem Nginx (ex.: `runserver` com `DEBUG=False`) o cliente recebe 200 vazio.
- O MIME em produção vem de `get_mime_type_from_file_extension` (`application/<ext>`); a ramificação "imagem" só ocorre se esse retorno for falso (nunca ocorre, pois a função sempre devolve texto), portanto `foo.png` sai como `application/png`, não `image/png`.
- `CustomFieldFile.url` engole **qualquer** exceção e devolve `""`; no esqueleto isso é sempre o caso (não há actions de arquivo registradas).
- `shorten_file_name` usa `MEDIA_ROOT` + caminho relativo para renomear com `os.rename`; se o arquivo não existir no disco levanta `FileNotFoundError`.
- `CustomFieldFile.delete()` não usa `FieldFile.delete` padrão: seta `name=None`, atualiza o atributo da instância e marca `_committed=False`.
- Avatar: `User.FIELDFILE_NAME = ('avatar',)` está declarado, porém `User` **não** herda `SaveModelWithFileMixin`; portanto o arquivo é gravado no primeiro `save()` normal.
- A validação de 10 MB vale para o campo do modelo (`avatar_validation`), logo também para formulários ModelForm; `MAX_IMAGE_UPLOAD_SIZE` (setting) não é lida por nenhum código do esqueleto (o limite do avatar está fixo na função).
- `FILE_UPLOAD_MAX_MEMORY_SIZE` e `DATA_UPLOAD_MAX_MEMORY_SIZE` são iguais a `MAX_DOC_UPLOAD_SIZE` (1512 MB): uploads são mantidos em memória até esse tamanho.
- O Nginx de produção tem `client_max_body_size 4G`, superior ao limite do Django.
- `ResponseFileMixin` importa `fitz` e `pymupdf` no topo; como nenhuma view o importa, o módulo `backend/api/mixins.py` só é carregado se alguém o importar.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

**Rota e entrega de mídia**

- **FR-001**: O sistema DEVE expor a rota `re_path(r"^media/(?P<path>.*)$", views.MediaPublicView.as_view(), name="mediapublic_view")` no app `backend.utils` (incluído na raiz em `backend/urls.py`), sem exigir autenticação.
- **FR-002**: `MediaPublicView.get` DEVE responder 404 (`Http404`) para qualquer `path` que contenha a substring `private`, antes de qualquer outra ação.
- **FR-003**: Com `settings.DEBUG` verdadeiro, DEVE delegar a `django.views.static.serve(request, path, document_root=settings.MEDIA_ROOT)`.
- **FR-004**: Com `DEBUG` falso, DEVE devolver `HttpResponse` vazio com `Content-Type` = `get_mime_type_from_file_extension(<nome do arquivo>)` (com a ramificação de imagem descrita em Casos de Borda), `Content-Disposition: inline; filename="<nome>"`, `Cache-Control: no-cache`, `Pragma: no-cache`, `Expires: 0` e `X-Accel-Redirect: /mediaredirect/<path>`.
- **FR-005**: O Nginx de produção DEVE ter `location /mediaredirect/ { internal; alias /var/project/backend_media/media/; ... }` com `Pragma "no-cache"`, `Cache-Control "no-cache"`, `Expires 0` e `expires 0`.
- **FR-006**: A rota `/media/` NÃO DEVE ser servida diretamente pelo Nginx (não há `location /media/`): toda requisição passa pelo Django.

**Settings de mídia** (`backend/settings/medias.py`)

- **FR-007**: DEVE definir `MEDIA_URL = "/media/"`, `MEDIA_ROOT = PROJECT_DIR.parent / "backend_media" / "media"` e `MEDIA_CACHE_ROOT = PROJECT_DIR.parent / "backend_media" / "media_cache"`.
- **FR-008**: Se `DEBUG` e `"/var/project" not in str(PROJECT_DIR)`, DEVE redefinir `MEDIA_ROOT = Path("/mnt/volumes")/"backend_media"/"media"` e `MEDIA_CACHE_ROOT = Path("/mnt/volumes")/"backend_media"/"media_cache"`.
- **FR-009**: DEVE definir `MAX_DOC_UPLOAD_SIZE = 1512 * 1024 * 1024`, `MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024`, `FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE`, `DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE` e `DATA_UPLOAD_MAX_NUMBER_FILES = 1000`.
- **FR-010**: DEVE definir `THUMBNAIL_PROCESSORS = ("image_cropping.thumbnail_processors.crop_corners",) + easy_thumbnails.conf.Settings.THUMBNAIL_PROCESSORS` e `THUMBNAIL_SOURCE_GENERATORS = ("backend.utilss.pil_image",)`.
- **FR-011**: DEVE definir `IMAGE_CROPPING_SIZE_WARNING = True`, `IMAGE_CROPPING_JQUERY_URL = None` e `FILTERS_HELP_TEXT_FILTER = False`.
- **FR-012**: `easy_thumbnails` e `image_cropping` DEVEM estar em `INSTALLED_APPS` (`backend/settings/apps.py`).

**Campo de arquivo customizado** (`backend/fields.py`)

- **FR-013**: DEVE existir `CustomFileField(models.FileField)` com `attr_class = CustomFieldFile`.
- **FR-014**: `CustomFieldFile._url` DEVE exigir arquivo (`_require_file`) e reverter `"backend.api:<app_label>_<model_name>-<campo com '_' trocado por '-'>"` com `kwargs={"pk": instance.pk}`; qualquer exceção → `""`.
- **FR-015**: `CustomFieldFile.url` DEVE devolver `_url`; se não vazio e terminar em `/`, DEVE remover a barra final e anexar `.<extensão do nome do arquivo>`; qualquer exceção → `""`.
- **FR-016**: `CustomFieldFile.shorten_file_name()` DEVE: ignorar nomes vazios; ignorar quando o último segmento tem < 128 caracteres; senão renomear para `f_<últimos 20 caracteres>`, mover o arquivo com `os.rename(self.path, f"{settings.MEDIA_ROOT}/<novo caminho>")`, atualizar `self.name` e chamar `self.instance.save()`.
- **FR-017**: `CustomFieldFile.delete(save=True)` DEVE ser no-op se o arquivo for falso; senão fechar/descartar o arquivo aberto, apagar do `storage`, definir `name=None`, atualizar o atributo da instância, `_committed=False` e salvar a instância se `save`.

**Avatar**

- **FR-018**: `User.avatar` DEVE ser `ImageCropField(upload_to='avatars/', verbose_name='Avatar', validators=[avatar_validation], null=True, blank=True)`.
- **FR-019**: `User.avatar_cropping` DEVE ser `ImageRatioField('avatar', '128x128', verbose_name='Seleção (Enquadramento)', help_text='A configuração do Avatar é possível após a atualização da fotografia.')`.
- **FR-020**: `avatar_validation(image)` DEVE levantar `forms.ValidationError(_('The maximum file size is {0}').format(sizeof_fmt(10*1024*1024)))` quando `image.size` exceder 10 MB; `sizeof_fmt` formata em Ki/Mi/Gi… com sufixo `B` (ex.: `10.0MiB`).
- **FR-021**: `AppVersionView` (feature 005) DEVE, para usuário autenticado, incluir `user.avatar` = `/static/imgs/perfil.png` se não houver avatar, senão `image_cropping.utils.get_backend().get_thumbnail_url(avatar, {'size': (128,128), 'box': user.avatar_cropping, 'crop': True, 'detail': True})`.
- **FR-022**: A tag de inclusão `avatar_user(user_render=None, css_class="avatar")` (`backend/utils/templatetags/common_tags.py`) DEVE renderizar `_templates/eauth/user/avatar.html`: com avatar, `<img class="{{ css_class }}" src="{% cropped_thumbnail user_render 'avatar_cropping' %}">`; sem avatar, `<svg class="{{ css_class }}" title="{{user_render}}"><use href="#svg-perfil"></use></svg>`.
- **FR-023**: `_templates/base.html` DEVE definir o símbolo SVG `svg-perfil` e usar `{% avatar_user user 'avatar-2' %}`.
- **FR-024**: `BackendUserChangeForm` DEVE incluir `avatar` e `avatar_cropping` com os widgets `ImageCropWidget` e `CropWidget` e, no `__init__`, aplicar `get_attrs(self.instance.avatar, 'avatar')` ao widget do avatar removendo a chave `class`.
- **FR-025**: `User.FIELDFILE_NAME` DEVE ser `('avatar',)`.

**Helpers e mixins** (`backend/utilss.py`, `backend/model_mixins.py`)

- **FR-026**: `get_mime_type_from_file_extension(filename)` DEVE devolver `application/vnd.oasis.opendocument.text` para extensão `odt` e `application/<ext>` para as demais (`ext` = último segmento após `.`; sem `.`, o nome inteiro).
- **FR-027**: `pil_image(source, exif_orientation=False, **options)` DEVE delegar a `easy_thumbnails.source_generators.pil_image(source, exif_orientation, **options)`.
- **FR-028**: `hash_sha512(arquivo)` DEVE aceitar `str` (caminho; abre em `rb` e fecha) ou objeto de arquivo aberto, ler em blocos de 4096 bytes e devolver o hexdigest SHA-512.
- **FR-029**: `FileFieldCheckMixin(BaseForm)` DEVE sobrescrever `clean()` (alias de `_check()`) conforme as regras da História 5.
- **FR-030**: `SaveModelWithFileMixin` com `FIELDFILE_NAME = ("arquivo",)` DEVE, em `save()` de objeto sem `pk`, guardar e zerar os campos de arquivo, chamar `super().save(force_insert, force_update, using, update_fields)`, restaurar os arquivos não vazios e, em seguida, chamar `super().save(...)` novamente (em todos os casos há um `save` final).
- **FR-031**: A assinatura de `SaveModelWithFileMixin.save` DEVE aceitar `clean=True` (não utilizado nesse mixin).

**ResponseFileMixin** (`backend/api/mixins.py`; sem consumidores)

- **FR-032**: `response_file(request, *args, **kwargs)` DEVE buscar `self.item = self.get_queryset().filter(pk=kwargs['pk']).first()`; 404 (`NotFound`) se não houver item, se o item não tiver atributo igual a `self.action` ou se o arquivo estiver vazio.
- **FR-033**: DEVE ler `text`, `page`, `dpi`, `grade`, `anon` de `request.GET`; `dpi` é limitado a 72–300 e arredondado para cima ao valor de (72, 100, 150, 200, 300), inválido → 72.
- **FR-034**: Para PDF, superusuário e `anon`, DEVE redigir (tarja preta) os termos de `anon` (separados por vírgula) via PyMuPDF; `text` devolve texto limpo (`text/plain; charset=utf-8`); `page` devolve PNG da página (com cache em `<arquivo>-p<NNN>-d<NNN>.png` salvo `nocache`, e grade de apoio quando `grade >= 10`).
- **FR-035**: MIMEs `application/png|jpg|jpeg` DEVEM ser corrigidos para `image/png|jpg|jpeg`; o nome do arquivo na resposta vem de `custom_filename(item)` se existir, senão do último segmento do nome.
- **FR-036**: Se `self.format_kwarg` e o MIME é imagem, DEVE gerar miniatura (`get_thumbnailer`): formato `<N>.<ext>` → miniatura `N x N` sem corte; formato `c<N>.<ext>` → miniatura `N x N` recortada com `box = <campo>_cropping`.
- **FR-037**: Em `DEBUG`, DEVE abrir e devolver o arquivo (ou a miniatura, ou o original com `?original`); fora de `DEBUG`, devolver vazio com `X-Accel-Redirect: /mediaredirect/<original__><nome>` e cabeçalhos no-cache (`?original` prefixa `original__` ao nome, exceto quando há miniatura).

**Renderers de arquivo** (`drfautoapi/__init__.py`, `backend/settings/drf.py`)

- **FR-038**: DEVEM existir `DrfautoapiNegotiation` (filtra renderers cujo `format` combina com `re.match` no sufixo; vazio → `Http404`), `FilesRenderer` (render sempre levanta `Http404`) e os renderers `JpegRenderer` (`image/jpeg`, `[a-zA-Z0-9]*\.?(jpeg|jpg)`), `JpgRenderer` (`image/jpg`, `[a-zA-Z0-9]*\.?(jpg|jpeg)`), `PngRenderer` (`image/png`, `[a-zA-Z0-9]*\.?png`), `PDFRenderer` (`application/pdf`, `pdf`) e `ZIPRenderer` (`application/zip`, `zip`).
- **FR-039**: `REST_FRAMEWORK` DEVE listar, após `JSONRenderer`, `drfautoapi.PDFRenderer`, `PngRenderer`, `JpgRenderer`, `JpegRenderer`, `ZIPRenderer` e `DEFAULT_CONTENT_NEGOTIATION_CLASS = "drfautoapi.DrfautoapiNegotiation"`; os parsers incluem `MultiPartParser` e `FileUploadParser`.
- **FR-040**: O filtro automático `ApiFilterSetMixin` DEVE tratar `FileField` como `CharFilter` com `lookup_expr="exact"`.

### Entidades-Chave

- **User.avatar / avatar_cropping**: foto de perfil (`avatars/`) e retângulo de enquadramento (`x1,y1,x2,y2` no formato do `django-image-cropping`, razão 128x128).
- **Arquivo de mídia**: arquivo sob `MEDIA_ROOT`, referenciado por caminho relativo; pasta `private` nunca é servida por `/media/`.
- **Miniatura (thumbnail)**: derivado de imagem gerado por `easy-thumbnails` com recorte opcional; armazenado ao lado do original sob `MEDIA_ROOT`.
- **CustomFieldFile**: wrapper de `FieldFile` com URL de action da API, encurtamento de nome e exclusão customizada.
- **Renderers de arquivo**: classes que só existem para participar da negociação de conteúdo por sufixo (a entrega real é feita pela action).

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **SC-001**: `GET /media/<caminho com private>` retorna 404 em 100% dos casos, em `DEBUG` ou produção.
- **SC-002**: Com `DEBUG=False`, 100% das respostas de `/media/<p>` com caminho público contêm o cabeçalho `X-Accel-Redirect` igual a `/mediaredirect/<p>` e `Cache-Control: no-cache`.
- **SC-003**: Com `DEBUG=True`, um arquivo existente em `MEDIA_ROOT` é baixável por `/media/<p>` com status 200 e conteúdo idêntico.
- **SC-004**: As settings expostas (`MEDIA_URL`, `MAX_DOC_UPLOAD_SIZE`, `MAX_IMAGE_UPLOAD_SIZE`, `DATA_UPLOAD_MAX_NUMBER_FILES`, `THUMBNAIL_*`, `IMAGE_CROPPING_*`) têm exatamente os valores desta especificação.
- **SC-005**: Um avatar > 10 MB é rejeitado e ≤ 10 MB é aceito; `/api/version` devolve a miniatura 128x128 ou `/static/imgs/perfil.png`.
- **SC-006**: `CustomFieldFile.url` devolve `""` sem exceção quando não há rota/arquivo; `shorten_file_name` encurta 100% dos nomes com ≥ 128 caracteres para ≤ 22 caracteres (`f_` + 20).
- **SC-007**: `ruff check .` sem erros nos arquivos da feature e testes `pytest` propostos em `quickstart.md` passando.

## Premissas

- O volume `backend_media` é montado em `/var/project/backend_media` nos contêineres e em `/mnt/volumes/backend_media` quando o Django roda no host em modo debug (feature 010/011).
- Em produção a entrega depende do Nginx configurado como na feature 011; sem ele `MediaPublicView` devolve respostas vazias.
- O namespace de URLs `backend.api` e o nome de actions `<app>_<modelo>-<campo>` pertencem à `drfautoapi` (feature 005); o esqueleto não registra actions de arquivo, então `CustomFieldFile.url` retorna `""` na prática.
- Pillow 13 e PyMuPDF 2.1 estão instalados (via `poetry.lock`); `fitz` é fornecido pela distribuição do PyMuPDF.
- O arquivo estático `/static/imgs/perfil.png` vem do frontend (`_frontend/src/assets/imgs/perfil.png`, copiado pelo build/`collectstatic`; feature 007).
- Autorização de edição do perfil/avatar é a da feature 002; nenhuma permissão adicional é criada aqui.
- Os testes automatizados citados são propostos (nenhum teste existente cobre a feature).
