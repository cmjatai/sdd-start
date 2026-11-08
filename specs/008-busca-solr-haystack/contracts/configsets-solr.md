# Contrato: *Configsets* do Solr (`solr/arq1_configset` e `solr/arq2_configset`)

Ambos têm a mesma árvore e são enviados zipados (conteúdo de `conf/` na raiz do zip) para `/solr/admin/configs?action=UPLOAD&name=arqN_configset`.

```text
solr/arqN_configset/conf/
├── managed-schema.xml
├── solrconfig.xml
├── protwords.txt
├── stopwords.txt
├── synonyms.txt
└── lang/
    ├── stopwords_en.txt
    ├── stopwords_es.txt
    └── stopwords_pt.txt
```

Base: `_default` do Solr 9.x (`luceneMatchVersion` 9.9). Os arquivos `stopwords.txt`, `synonyms.txt` e `protwords.txt` são os modelos padrão do Solr (cabeçalho de licença Apache; sem entradas customizadas relevantes); `lang/stopwords_pt.txt` é a lista de stopwords do português usada por `text_pt`.

## `managed-schema.xml`

Seção "Django fields" (após `id`, `_version_`, `_text_`):

| Campo | `arq1` | `arq2` |
|---|---|---|
| `id` (`string`, required, uniqueKey) | ✔ | ✔ |
| `_version_` (`plong`, não indexado/armazenado) | ✔ | ✔ |
| `_text_` (`text_general`, indexado, **não** armazenado, multivalorado) | ✔ | ✔ |
| `django_ct` (`string`, indexed, stored) | ✔ | ✔ |
| `django_id` (`string`, indexed, stored) | ✔ | ✔ |
| `last_update` (`pdate`, `default="NOW"`, `docValues`) | ✔ | ✔ |
| `text` (`text_pt`, indexed, stored, single) | ✔ | ✔ |
| `at` (`pint`, `default="0"`, `docValues`, não obrigatório) | ✔ | — |
| `conta_classe_logica` (`string`, `docValues`) | — | ✔ |
| `conta_classe_estrutural` (`string`, `docValues`) | — | ✔ |
| `tipo` (`string`, `docValues`) | — | ✔ |
| `ano` (`pint`, `docValues`, não obrigatório) | comentado | ✔ |
| `data` (`pdate`, `docValues`, não obrigatório) | — | ✔ |

- `<uniqueKey>id</uniqueKey>`.
- `copyField source="*" dest="_text_"` **comentado** (sem cópia para `_text_`).
- `fieldType text_pt` (`solr.TextField`, `positionIncrementGap=100`): `charFilter htmlStrip` → `tokenizer standard` → `filter lowercase` → `filter stop ignoreCase=true words=lang/stopwords_pt.txt format=snowball` → `filter brazilianStem` (variantes `portugueseLightStem`/`Minimal`/`snowballPorter` comentadas).
- Demais tipos e campos dinâmicos: os do `_default` (ex.: `*_i`, `*_s`, `*_l`, `*_b`, `*_f`, `*_d`, `*_dt`, `*_t`, `*_txt`, `*_txt_pt`, `*_txt_en`, `*_txt_es`, `*_ws`, `random_*`, `ignored_*`, `attr_*`).

## `solrconfig.xml`

| Item | Valor (ambos, salvo indicação) |
|---|---|
| `luceneMatchVersion` | `9.9` |
| `autoCommit.maxTime` | `${solr.autoCommit.maxTime:300000}` |
| `autoSoftCommit.maxTime` | `${solr.autoSoftCommit.maxTime:30000}` |
| `/select` (SearchHandler) | `rows=50`, `df=text`, `defType=edismax`, `lowercaseOperators=true`, `q.op=AND`, `echoParams=explicit` |
| `/query` | `wt=json`, `indent=true` |
| `initParams` de `/update/**,/query,/select,/spell` | `df=text` |
| Corretor ortográfico (`spellchecker` `default`, `DirectSolrSpellChecker`) — campo | `arq1`: `text` · `arq2`: `_text_` |
| Realce — fragmentador `gap` (`hl.fragsize`) | `arq1`: `512` · `arq2`: `100` |
| Cadeia de atualização | `add-unknown-fields-to-the-schema` (padrão, `update.autoCreateFields:true`) |
| `/update/extract` | presente (herdado) |

Única diferença funcional entre os dois `solrconfig.xml`: `spellchecker.field` e `hl.fragsize` (além de linhas em branco).

## Como validar

```text
GET  <SOLR_URL>/solr/<projeto>_arq1/schema/fields   → inclui "at", não inclui "tipo"
GET  <SOLR_URL>/solr/<projeto>_arq2/schema/fields   → inclui "tipo","ano","data","conta_classe_*", não inclui "at"
GET  <SOLR_URL>/solr/<projeto>_arq1/config/requestHandler?componentName=/select
```
