# LLM_GUIDE — Contrato de Interface JSJ-DOC-ENGINE

> **Data:** 2026-04-03
> **Versão:** 1.0
> **Público:** Qualquer agente LLM que produza ficheiros para o JSJ-DOC-ENGINE

---

## O QUE É ISTO

O JSJ-DOC-ENGINE é um sistema local que compila documentos técnicos JSJ a partir de Markdown.
A pipeline: **Markdown → Pandoc → DOCX** com estilos JSJ.

Para que o DOC-ENGINE possa compilar um documento, precisa de 2 ficheiros YAML:
1. **`estrutura.yaml`** — define *o que* o documento contém (schema, hierarquia, tipos)
2. **`mapeamento.yaml`** — define *onde* está o conteúdo (paths MD, templates DOCX)

Este guia define como gerar estes ficheiros correctamente.

---

## FICHEIRO 1: estrutura.yaml

### Metadados obrigatórios (cabeçalho)

```yaml
doc_type: CTE                           # tipo do documento (ex: CTE, MQT, relatório)
doc_title: "CTE Fundações e Estruturas" # título completo
doc_version: "1.0"
doc_date: "2026-04-03"
schema_version: 2                       # SEMPRE 2 — não usar v1
```

### Bloco `defaults` (opcional)

```yaml
defaults:
  behavior:
    toc:
      include: null
    page:
      break_before: null
    numbering:
      visible: null
```

Omitir o bloco `defaults` é seguro — a app usa os defaults do registry interno.

### Lista `elementos`

```yaml
elementos:
- slug: CAPA
  titulo: Capa
  display_order: 1
  include: true
  semantic_type: cover
  nota: ""
  filhos:
  - slug: ...
```

### Bloco `behavior` (overrides — só quando difere dos defaults)

```yaml
behavior:
  toc:
    include: false
  page:
    break_before: true
    section_break_before: false
  numbering:
    visible: false
    scheme: none
    restart: false
    start_at: 1
```

---

## SEMANTIC TYPES — ENUM FECHADO

| semantic_type | Quando usar | section_role | No TOC? | Page break? | Numerado? |
|---|---|---|---|---|---|
| `cover` | Capa do documento | front_matter | não | sim | não |
| `front_matter_note` | Fichas, instruções, revisões | front_matter | não | sim | não |
| `revision_history` | Quadro de revisões | front_matter | não | sim | não |
| `toc` | Índice geral | front_matter | não | sim | não |
| `list_of_figures` | Lista de figuras | front_matter | não | sim | não |
| `list_of_tables` | Lista de tabelas | front_matter | não | sim | não |
| `section` | Capítulos, sub-capítulos, artigos técnicos | main_matter | sim | não | sim |
| `unnumbered_heading` | Heading sem número | main_matter | sim | não | não |
| `subsection_group` | Agrupador lógico sem conteúdo próprio | main_matter | sim | não | não |
| `annexes` | Container "Anexos" (agrupador de topo) | back_matter | não | sim | não |
| `annex` | Um anexo individual | back_matter | sim | sim | sim (letras) |
| `glossary` | Glossário técnico | back_matter | sim | sim | não |

---

## REGRAS DE SLUGS

1. UPPER_CASE com hífens — ex: `MAT-BET`, `EXEC-FUN`, `ANX-GLOS`
2. Únicos em todo o documento
3. Estáveis — nunca mudam após atribuição
4. Apenas `[A-Z0-9-]`

Prefixos JSJ (convenção, não impostos pela app):
`SEC-` / `LEX-` / `GERAL-` / `MAT-` / `EXEC-` / `DIAG-` / `REP-` / `NORM` / `ANX-`

---

## FICHEIRO 2: mapeamento.yaml

Flat (sem hierarquia filhos). Uma entrada por slug.

```yaml
doc_id: CTE-SecI
estrutura_ref: estrutura.yaml
schema_version: "2"
obra: "Nome da Obra"

templates:
  geral: "C:/caminho/para/reference.docx"

elementos:
- slug: LEX
  md_source: "C:/Users/JSJ/.../02_CONTRATUAL/LEX.md"
  template_docx: default
  nota: ""

- slug: MAT-BET
  md_source: ""
  template_docx: default
  nota: "Aguarda redacção A6"
```

---

## CHECKLIST DE VALIDAÇÃO

- [ ] Todos os slugs únicos
- [ ] Todos os `semantic_type` válidos (tabela acima)
- [ ] `schema_version: 2` presente
- [ ] Mapeamento cobre todos os slugs com `include: true`
- [ ] Paths com forward slashes
- [ ] Sem blocos `behavior` desnecessários

---

## ANTI-PADRÕES

| Fazer | Não fazer |
|-------|-----------|
| `semantic_type: section` para artigos | Inventar tipos novos |
| `behavior` só com overrides | Copiar todos os defaults |
| Slugs estáveis | Mudar slugs entre versões |
| Mapeamento flat | Hierarquia no mapeamento |
| Forward slashes nos paths | Backslashes ou paths relativos |

---

**Criado:** 2026-04-03 | **Agente:** Cowork Governo
