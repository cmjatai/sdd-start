# Contrato: Formato dos layouts YAML (`<app_label>/layouts.yaml`)

Arquivo localizado via loaders de template (`_templates/<app_label>/layouts.yaml`; para o app `utils`: `_templates/utils/layouts.yaml`). É **renderizado como template Django** antes do parse (`{% load i18n %}`, `{% trans %}` permitidos) e lido com `yaml.full_load`.

## Versão 1 (padrão)

```yaml
{% load i18n %}
NomeDoModelo:                 # chave = view.layout_key (padrão: model.__name__)
  {% trans 'Legenda 1' %}:    # fieldset
  - campo_a:8 campo_b         # linha: 12 colunas
  - campo_c campo_d campo_e
  Outra legenda:
  - campo_f
```

Regras de linha (`line_to_namespans`):

- Palavras separadas por espaço; `nome:largura` fixa a largura (1–12); sem largura = 0.
- `restante = 12 - soma(larguras fixas)`; cada campo sem largura, em ordem, recebe `ceil(restante / campos_sem_largura_restantes)` e o restante diminui.
- Exemplos: `name:9 place tiny` → `(name,9) (place,2) (tiny,1)`; `field nature:2` → `(field,10) (nature,2)`; `kind:1 date unit:5 status` → `(kind,1) (date,3) (unit,5) (status,3)`; `equalA equalB equalC` → 4/4/4; `highlander` → 12.
- Nome de campo pode conter `|funcao` (método da view que devolve `(rótulo, valor)`) e `__` para navegação em relações.

Resultado Python: `[[legenda, linha1, linha2, ...], ...]`, onde cada linha é lista de tuplas `(nome, largura)`.

## Versão 2 (somente detalhe)

Declarada com a chave `version: 2` no nível do modelo (retirada por `base.pop("version", 1)`). Estrutura: grupos de colunas → fieldsets → colunas internas → linhas.

```yaml
Modelo:
  version: 2
  col-lg-6:                   # classe CSS do grupo de colunas
    Legenda do fieldset:
      col-12:                 # classe CSS da coluna interna
      - campo_a campo_b
      - campo_c
```

Resultado: `([[classe_grupo, [legenda, [classe_coluna, linha, ...], ...], ...], ...], 2)`.

## Consumo

| Consumidor | Uso |
|-----------|-----|
| `CrispyLayoutFormMixin.fields` | lista de nomes de todas as linhas (campos do `ModelForm`), quando não há `form_class` |
| `CrispyLayoutFormMixin.get_form` | `CustomFormLayout(*layout)` → fieldsets `Fieldset(legenda, rows)` + linha de botões |
| `CrispyLayoutFormMixin.list_field_names` | nomes da **primeira** legenda quando a `Crud` não define `list_field_names` |
| `layout_display` | detalhe (`crud/detail_content_widget.html`) |

Erros (arquivo ausente, chave ausente, YAML inválido) → `[]`.

## Exemplos reais

`_templates/utils/layouts.yaml`:

```yaml
{% load i18n %}
Teste:
  {% trans 'Modelo Teste'%}:
  - id teste teste teste
  - teste:5 teste teste
  - teste:3 teste teste
```

`_templates/eauth/layouts.yaml` (chaves `UserDetail`, `UserCreate`; detalhes em `002`):

```yaml
UserDetail:
  {% trans 'Usuário' %}:
  - email:8 is_active
  - first_name last_name
  - groups
  - user_permissions
UserCreate:
  {% trans 'Usuário' %}:
  - email first_name last_name is_active
  - new_password1 new_password2
```

Larguras resultantes do exemplo `Teste`: `[('id',3),('teste',3),('teste',3),('teste',3)]`, `[('teste',5),('teste',4),('teste',3)]`, `[('teste',3),('teste',5),('teste',4)]`.
