# Contrato: Utilitários Python, Mixins e Template Tags

**Feature**: `001-fundacao-projeto-django` | Referências: [plan.md](../plan.md) (§11–§14), [data-model.md](../data-model.md)

## 1. `backend/utilss.py`

Import: `from backend.utilss import <item>`. Logger do módulo: `logger = logging.getLogger(__name__)`.

| Item | Assinatura | Retorno / comportamento |
|------|-----------|-------------------------|
| `YES_NO_CHOICES` | constante | `[(True, _("Sim")), (False, _("Não"))]` |
| `NONE_YES_NO_CHOICES` | constante | `[(None, _("---------")), (True, _("Sim")), (False, _("Não"))]` |
| `DECIMAL_PLACES` | constante | `{i: Decimal(10) ** -i for i in range(0, 10)}` |
| `get_mime_type_from_file_extension(filename)` | `str -> str` | extensão após o último `.`; `odt` → `application/vnd.oasis.opendocument.text`; demais `application/<ext>` (sem normalizar caixa) |
| `quantize(value, decimal_places=2, rounding=ROUND_HALF_DOWN)` | `-> Decimal` | `int` → usa `DECIMAL_PLACES[dp]`; senão o próprio valor (`Decimal`) como expoente |
| `decimal2str(value, decimal_places=2, rounding=ROUND_HALF_DOWN, force_grouping=True, use_l10n=True)` | `-> str` | quantiza e formata com `django.utils.formats.number_format(decimal_pos=..., use_l10n, force_grouping)`; `Decimal("1234.565")` → `"1.234,56"` (pt-br); qualquer exceção → `logger.error` + `str(value)` |
| `normalize(txt)` | `str -> str` | NFKD → ASCII ignorando não-ASCII (`"Ação ç"` → `"Acao c"`) |
| `dict2attr(value)` | `dict -> d2a` | objeto `dict` com cada chave também como atributo |
| `get_settings_auth_user_model()` | `-> str` | `getattr(settings, "AUTH_USER_MODEL", "auth.User")` |
| `register_all_models_in_admin(module_name)` | `str -> None` | `backend.<app>.admin` → app `<app>` (senão `parts[0]`); registra em `admin.site` cada modelo de `apps.get_app_config(app).get_models()` ainda não registrado |
| `save_in_metadata(obj, mdict=None)` | `-> Metadata` | `get_or_create` por (`ContentType`, `obj.id`); **substitui** `metadata` por `mdict`; salva (import tardio de `ContentType`/`Metadata`) |
| `run_sql(sql)` | `str -> list|None` | executa em `connection.cursor()`; `fetchall()` com exceção ignorada |
| `show_results_filter_set(qr)` | `QueryDict -> bool` | `False` se vazio ou só `{"iframe"}`; senão `True` |
| `pil_image(source, exif_orientation=False, **options)` | | delega a `easy_thumbnails.source_generators.pil_image` |
| `clean_text(text, _normalizes=None)` | `str -> str` | lista de (regex, substituição) aplicada repetidamente até não casar; exceção → texto original. Pares: `\n ?\d+ ?/ ?\d+ ?\n`→`\n`; `[ ]{2,}`→` `; ` \n`→`\n`; `(\w)\n(.)`→`\1 \2`; `(,\|\.)\n(.)`→`\1 \2`; `\n\n`→`\n`; `-\n`→`-`; `^\n`→``; `–`→`-`; `•`→`*`; `[“”]`→`"` |
| `intervalos_tem_intersecao(a_inicio, a_fim, b_inicio, b_fim)` | `-> bool` | `max(inícios) <= min(fins)` (extremos inclusivos) |
| `hash_sha512(arquivo)` | `str\|file -> str` | caminho (abre/fecha) ou arquivo binário; blocos de 4096 bytes; `hexdigest()` |
| `DisableSignals(disabled_signals=None)` | context manager | desativa por padrão `pre_init, post_init, pre_save, post_save, pre_delete, post_delete, pre_migrate, post_migrate, m2m_changed`; restaura receptores e limpa `sender_receivers_cache` ao sair |
| `TimeExecution(print_date=False)` | context manager | imprime `"TimeExecution:", fim - início` (e datas se `print_date`) |
| `FileFieldCheckMixin(BaseForm)` | mixin de formulário | `_check()` reescreve erros de `FileField` e valida existência do arquivo referenciado; `clean()` = `_check()` |

## 2. `backend/model_mixins.py`

| Mixin | Contrato |
|-------|----------|
| `DateModelMixin` (abstrato) | `created_at`, `modified_at` |
| `AuditoriaModelMixin` (abstrato) | `created_by`, `modified_by` (FK para `AUTH_USER_MODEL`, `PROTECT`, `related_name="+"`) |
| `SearchModelMixin` (abstrato) | `fields_search`, `search`; `save(..., auto_update_search=True)` |
| `CleanModelMixin` | `clean()` com `unique_together` e `NULL`; `save(..., clean=True)` |
| `SaveModelWithFileMixin` | `FIELDFILE_NAME=("arquivo",)`; `save(..., clean=True)` salva duas vezes para objetos novos (defeito conhecido no Django 6) |

Sintaxe de `fields_search`: `["campo"]`, `[("nome", "sobrenome")]` (tupla concatenada sem separador), `["fk__campo"]` (navegação encadeada). Detalhes em `data-model.md` §5.

## 3. App `backend.utils` — API pública

| Símbolo | Contrato |
|---------|----------|
| `Teste`, `Metadata`, `MetadataManager` | `data-model.md` §1–§2 |
| `Metadata.objects.get_metadata(obj)` | `Metadata` ou `None` |
| `Metadata.objects.set_or_update_metadata(obj, dict)` | cria ou **mescla** (`dict.update`) |
| `UtilsConfig.ready()` | importa `backend.utils.services.signals` e `signals_syncrefresh` (feature 006) |
| `backend/utils/admin.py` | `register_all_models_in_admin(__name__)` |

## 4. Template tags — biblioteca `common_tags`

Uso: `{% load common_tags %}` (`backend/utils/templatetags/common_tags.py`; `register = template.Library()`; o pacote `templatetags` não tem `__init__.py`).

### 4.1 Filtros

| Filtro | Entrada → Saída |
|--------|-----------------|
| `decimal2str` | `decimal2str(value)` (2 casas, pt-br) |
| `startswith:"x"` | `str` → bool (`False` se não for `str`) |
| `jsonify` | `QuerySet` → `serialize("json")` seguro; outro → `json.dumps` seguro |
| `to_dict` | `obj.__dict__` |
| `islist` | `isinstance(obj, list)` |
| `meta_model_value:"attr"` | `getattr(instance._meta, attr)` ou `""` |
| `lookup:chave` | `d[chave]` se existir, senão `[]` |
| `map_field_from_queryset:"campo"` | `map` com `getattr(obj, campo)` |
| `search_value` | `request.GET/POST["q"]` conforme método; `""` em erro (loga) |
| `isinst:"Classe"` | compara `value.__class__.__name__` |
| `age:max_age` | tempo decorrido (ver `plan.md` §14): "N ano(s), N mes(es), N dia(s)" ou "N dia(s), N hora(s), N minuto(s)"; com `max_age` (dias) excedido → `d \d\e M \d\e Y`; falsy → `""` |
| `str2intabs` | `str` numérica → `abs(int)`; senão `""` |
| `url` | começa com `http://` ou `https://` |
| `component_frontend:prefix` | `startswith(prefix)` (padrão `"<emf-"`) |
| `settings_key_filter` | `getattr(settings, nome)` |
| `dont_break_out` | `<div class="dont-break-out">…</div>` (`is_safe`, `stringfilter`) |
| `timedelta_filter:dias` | `data + timedelta(days=int(dias))` (`data` vazia → `timezone.now()`) |
| `now_year` | ano corrente |
| `parse_datetime` | `django.utils.dateparse.parse_datetime` (`expects_localtime`) |
| `valor_por_extenso` | `num2words(valor, to="currency", lang="pt_BR")` |
| `valor_str` | `number_format(valor, force_grouping=True)` |
| `valor_abs_str` | idem com `valor.copy_abs()` |
| `audio_url` | URL terminada em `mp3` |
| `is_video_url` | URL terminada em `mp4, ogg, webm, 3gp, ogv` |
| `youtube_url` | casa `youtube.com/watch?v=` ou `youtu.be/` (minúsculas) |
| `facebook_url` | casa URL de vídeo do Facebook |
| `youtube_id` | `"<id>?start=<t>"` (`t` padrão `0`; id da query `v` ou do path) |
| `file_extension` | sufixo sem ponto |
| `params_search_to_api` | itens `(k, v)` não vazios exceto `tipo_listagem` → `k=v&…`; `_b=`, `_i=`, `_is=` → `=`; `autoria` → `autores` |
| `obfuscate_value:chave` | `"***************"` se a chave ∈ {`hash`, `google_recaptcha_secret_key`, `password`, `google_recaptcha_site_key`, `hash_code`, `jdata`} |

### 4.2 Tags simples

| Tag | Resultado |
|-----|-----------|
| `{% field_verbose_name instance "campo" %}` | `verbose_name` do campo da instância |
| `{% fieldclass_verbose_name "app.Modelo" "campo" %}` | idem via classe/string (`get_class`) |
| `{% model_verbose_name "app.Modelo" %}` | `verbose_name` |
| `{% model_verbose_name_plural "app.Modelo" %}` | `verbose_name_plural` ou `""` |
| `{% settings_key_tag "NOME" %}` | valor de `settings.NOME` |
| `{% yaml_render "template.yaml" 4 %}` (`takes_context`) | renderiza o template e indenta cada linha em N espaços |
| `{% container_css_class %}` (`takes_context`) | `context["container_css_class"]` → `view.crud.container_css_class` → `"container"` |
| `{% view_class_name %}` (`takes_context`) | nome da classe da `view` ou `"main-content"` |

### 4.3 Tag de inclusão

`{% avatar_user user_render css_class %}` → template `eauth/user/avatar.html` com `{"user_render", "css_class"}` (`css_class` padrão `"avatar"`; template pertence à feature 002/009).

### 4.4 Função auxiliar (não registrada)

`get_class(class_string)`: se não for classe, divide no último `.`; tenta `ContentType.objects.get_by_natural_key(mod, classe.lower()).model_class()`; em qualquer exceção importa o módulo e usa `getattr`. Se já for classe, devolve `None`.

Total: 39 itens registrados (filtros + tags).
