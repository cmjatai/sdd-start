---
description: "Lista de tarefas para reconstruir mídia, arquivos e avatar do usuário"
---

# Tarefas: Mídia, Arquivos e Avatar do Usuário

**Entrada**: Documentos de design em `/specs/009-midia-arquivos-avatar/`
**Pré-requisitos**: plan.md (obrigatório), spec.md, research.md, data-model.md, contracts/ (2 arquivos); features `001-fundacao-projeto-django`, `002-autenticacao-usuarios-auditoria` e `005-api-rest-automatica` concluídas.

**Testes**: incluídos (princípio VIII da constituição) — `backend/test_media.py` (ver `quickstart.md`).

**Organização**: tarefas agrupadas por história de usuário (US1…US6). **Todas as tarefas estão desmarcadas**: este documento é um roteiro de reconstrução.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[História]**: US1…US6 conforme `spec.md`
- Detalhes de cada item: seções numeradas do `plan.md` ("Detalhamento de Implementação") e `contracts/`.

## Convenções de Caminhos

Aplicação web Django: `backend/` (código), `drfautoapi/` (lib interna), `_templates/`, `_docker/prod/nginx/` (infra), `specs/009-midia-arquivos-avatar/` (docs).

---

## Fase 1: Preparação

- [ ] T001 Confirmar dependências em `pyproject.toml`: `easy-thumbnails = "^2.10.1"`, `django-image-cropping = "^1.7"`, `pymupdf = "^2.1"` (Pillow via lock) e instalá-las com `poetry install`
- [ ] T002 [P] Garantir que `"easy_thumbnails"` e `"image_cropping"` estão em `INSTALLED_APPS` em `backend/settings/apps.py` (plan §1)
- [ ] T003 [P] Garantir `mkdir -p ${ROOT_HOME}/backend_media` e `VOLUME [... "${ROOT_HOME}/backend_media" ...]` em `_docker/dev/Dockerfile.Dev` e `_docker/prod/Dockerfile` (feature 010/011)

---

## Fase 2: Fundacional (bloqueia as histórias)

- [ ] T004 Criar `backend/settings/medias.py` com todas as settings do `plan.md` §1 (`MEDIA_URL`, `MEDIA_ROOT`, `MEDIA_CACHE_ROOT` com regra de debug, `IMAGE_CROPPING_*`, `THUMBNAIL_*`, limites de upload, `FILTERS_HELP_TEXT_FILTER`) e garantir que o pacote `backend/settings/__init__.py` o importe
- [ ] T005 [P] Em `backend/utilss.py`, implementar `get_mime_type_from_file_extension`, `pil_image` (delegando a `easy_thumbnails.source_generators.pil_image`) e `hash_sha512` (plan §5)
- [ ] T006 Teste de settings em `backend/test_media.py::test_settings_midia` (valores exatos do spec FR-007…FR-011)

**Checkpoint**: settings carregam sem erro (`python manage.py check`).

---

## Fase 3: História de Usuário 1 - Servir arquivos em `/media/` com segurança (Prioridade: P1) 🎯 MVP

**Objetivo**: rota pública `/media/<path>`, 404 para `private`, serve em debug, `X-Accel-Redirect` em produção.
**Teste Independente**: `quickstart.md` passos 2 e 5.

### Testes da História 1

- [ ] T007 [P] [US1] Testes `test_media_producao_x_accel`, `test_media_private_404` (debug e produção) e `test_media_debug_serve` em `backend/test_media.py`

### Implementação da História 1

- [ ] T008 [US1] Implementar `MediaPublicView` em `backend/utils/views.py` conforme plan §3 (bloqueio `private`, `view_static_server` em `DEBUG`, cabeçalhos e `X-Accel-Redirect` em produção; manter `file_path` não usado e a ramificação de imagem)
- [ ] T009 [US1] Registrar `re_path(r"^media/(?P<path>.*)$", views.MediaPublicView.as_view(), name="mediapublic_view")` em `backend/utils/urls.py` (e garantir `path("", include("backend.utils.urls"))` em `backend/urls.py`)
- [ ] T010 [P] [US1] Adicionar o bloco `location /mediaredirect/` (`internal; alias /var/project/backend_media/media/;` + cabeçalhos no-cache + `expires 0;`) e `client_max_body_size 4G;` em `_docker/prod/nginx/backend_docker.conf`

**Checkpoint**: `curl /media/private/x` → 404; `curl /media/<arquivo>` → 200 em debug.

---

## Fase 4: História de Usuário 2 - Avatar do usuário com enquadramento (Prioridade: P1)

**Objetivo**: campos `avatar`/`avatar_cropping`, validação de 10 MB, widgets no perfil, tag `avatar_user`, miniatura em `/api/version`.
**Teste Independente**: `quickstart.md` passos 3 e 4.

### Testes da História 2

- [ ] T011 [P] [US2] Testes de `avatar_validation`/`sizeof_fmt` (limite 10 MiB) e de `AppVersionView` (anônimo, sem avatar, com avatar) em `backend/test_media.py`

### Implementação da História 2

- [ ] T012 [US2] Em `backend/eauth/models.py`: `sizeof_fmt`, `avatar_validation`, `User.FIELDFILE_NAME = ('avatar',)`, `avatar = ImageCropField(...)`, `avatar_cropping = ImageRatioField('avatar', '128x128', ...)` (plan §7; data-model §1)
- [ ] T013 [US2] Garantir os campos `avatar` e `avatar_cropping` em `backend/eauth/migrations/0001_initial.py` (gerar com `python manage.py makemigrations eauth` se a migração ainda não existir; manter `validators=[backend.eauth.models.avatar_validation]`)
- [ ] T014 [P] [US2] Em `backend/eauth/forms_auth.py` (`BackendUserChangeForm`): `fields` com `avatar` e `avatar_cropping`, `widgets` `ImageCropWidget()`/`CropWidget()`, layout `('avatar', 7), ('avatar_cropping', 5)` e ajuste de atributos com `get_attrs` removendo `class`
- [ ] T015 [P] [US2] Em `backend/utils/templatetags/common_tags.py`: inclusion tag `avatar_user(user_render=None, css_class="avatar")`; criar `_templates/eauth/user/avatar.html` (plan §7)
- [ ] T016 [P] [US2] Em `_templates/base.html`: símbolo SVG `svg-perfil` e chamada `{% avatar_user user 'avatar-2' %}`; garantir `_frontend/src/assets/imgs/perfil.png` (servido como `/static/imgs/perfil.png`)
- [ ] T017 [US2] Em `backend/api/views.py` (`AppVersionView`): `user.avatar` com padrão `/static/imgs/perfil.png` ou `get_backend().get_thumbnail_url(...)` com `size=(128,128)`, `box=avatar_cropping`, `crop=True`, `detail=True`; rota `^api/version$` em `backend/api/urls.py`

**Checkpoint**: upload > 10 MB rejeitado; `/api/version` devolve a miniatura.

---

## Fase 5: História de Usuário 3 - Limites de upload e miniaturas (Prioridade: P2)

**Objetivo**: confirmar limites e pipeline de miniaturas configurados.
**Teste Independente**: `quickstart.md` passo 1 e `test_settings_midia`.

- [ ] T018 [US3] Verificar que `THUMBNAIL_PROCESSORS` começa por `crop_corners` e `THUMBNAIL_SOURCE_GENERATORS = ("backend.utilss.pil_image",)` gerando uma miniatura de avatar real (smoke manual)
- [ ] T019 [P] [US3] Teste de que `pil_image` delega a `easy_thumbnails.source_generators.pil_image` (monkeypatch) em `backend/test_media.py`

---

## Fase 6: História de Usuário 4 - `CustomFileField` (Prioridade: P3)

**Objetivo**: campo de arquivo que devolve a URL da action da API.
**Teste Independente**: modelo de teste com `CustomFileField`.

- [ ] T020 [P] [US4] Testes de `CustomFieldFile.url` (sem rota → `""`, com rota terminando em `/` → `.ext`), `shorten_file_name` (≥ 128 → `f_` + 20) e `delete` em `backend/test_media.py`
- [ ] T021 [US4] Criar `backend/fields.py` com `CustomFieldFile` (`_url`, `url`, `shorten_file_name`, `delete`) e `CustomFileField` (plan §2)
- [ ] T022 [P] [US4] Em `drfautoapi/__init__.py`: `DrfautoapiNegotiation`, `FilesRenderer`, `JpegRenderer`, `JpgRenderer`, `PngRenderer`, `PDFRenderer`, `ZIPRenderer` (plan §9)
- [ ] T023 [US4] Em `backend/settings/drf.py`: `DEFAULT_RENDERER_CLASSES` (JSON + 5 renderers de arquivo), `DEFAULT_CONTENT_NEGOTIATION_CLASS = "drfautoapi.DrfautoapiNegotiation"`, parsers JSON/MultiPart/FileUpload
- [ ] T024 [P] [US4] Em `drfautoapi/drfautoapi.py`: `ApiFilterSetMixin.Meta.filter_overrides[FileField]` como `CharFilter` exato e `format_suffix_patterns(..., allowed=["[a-zA-Z.0-9]+"])` no `DrfautoapiRouter.get_urls`
- [ ] T025 [P] [US4] Teste de `DrfautoapiNegotiation.filter_renderers` (`120.png` → `PngRenderer`; sufixo inválido → `Http404`) em `backend/test_media.py`

---

## Fase 7: História de Usuário 5 - `SaveModelWithFileMixin` e `FileFieldCheckMixin` (Prioridade: P3)

- [ ] T026 [P] [US5] Testes do `SaveModelWithFileMixin` (primeiro `save()` sem arquivo, depois com) e do `FileFieldCheckMixin` (arquivo inexistente; reescrita de "Certifique-se de que o arquivo") em `backend/test_media.py`
- [ ] T027 [US5] Implementar `SaveModelWithFileMixin` em `backend/model_mixins.py` (plan §6)
- [ ] T028 [P] [US5] Implementar `FileFieldCheckMixin(BaseForm)` com `_check()`/`clean()` em `backend/utilss.py` (plan §5)

---

## Fase 8: História de Usuário 6 - Helpers e `ResponseFileMixin` (Prioridade: P3)

- [ ] T029 [P] [US6] Testes de `get_mime_type_from_file_extension` e `hash_sha512` (caminho e arquivo aberto) em `backend/test_media.py`
- [ ] T030 [US6] Criar `backend/api/mixins.py` com `ResponseFileMixin` (`response_pagepdftoimage`, `anon`, `response_pdftotext`, `response_file`, `thumbnail`) conforme plan §8 e FR-032…FR-037 (não ligar a nenhuma view)

---

## Fase 9: Acabamento e Preocupações Transversais

- [ ] T031 [P] Rodar `ruff check .` e `ruff format --check` nos arquivos da feature e corrigir apontamentos (regras `E`, `F`, `I`)
- [ ] T032 [P] Rodar `pytest backend/test_media.py -q` e a suíte completa (`pytest`)
- [ ] T033 [P] Executar o roteiro completo de `quickstart.md` (debug e, se possível, produção com Nginx)
- [ ] T034 Atualizar `specs/009-midia-arquivos-avatar/` se algum comportamento mudar durante a reconstrução (constituição, Fluxo de Desenvolvimento item 3)

---

## Dependências e Ordem de Execução

- **Preparação (Fase 1)** → **Fundacional (Fase 2)** → histórias.
- **US1 e US2 (P1)** podem seguir em paralelo após a Fase 2; US2 depende da feature 002 (modelo `User`) e T005 não é necessário para o avatar, mas `pil_image` (T005) é exigido pelas miniaturas.
- **US3 (P2)** depende de T004/T005 e de US2 para o smoke test.
- **US4** depende de feature 005 (`drfautoapi`); T021 é independente de T022–T025.
- **US5 e US6** são independentes entre si; T030 depende de T005 (`get_mime_type_from_file_extension`) e de `clean_text` de `backend/utilss.py` (feature 001).
- Dentro de cada história: testes → implementação → checkpoint.

## Estratégia de Implementação

1. **MVP**: Fases 1–2 + US1 + US2 (mídia servida + avatar) → validar `quickstart.md` 1–5.
2. Adicionar US3 (confirmação de limites/miniaturas).
3. Adicionar US4–US6 (capacidades dormentes para projetos derivados), cada uma com seus testes.
4. Acabamento (Fase 9). Replicar as particularidades de `research.md` para fidelidade (não "corrigir" sem atualizar a especificação).
