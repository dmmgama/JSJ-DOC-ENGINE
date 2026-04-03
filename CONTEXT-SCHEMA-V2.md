# JSJ-DOC-ENGINE — Contexto Schema v2 + Pipeline

> Para uso em novo chat LLM. Resume as decisões de arquitectura tomadas em 2026-04-03.

---

## O que é o sistema

Sistema local de produção de documentos técnicos JSJ.
Converte Markdown → DOCX via Pandoc, com UI em Streamlit local.
Agnóstico de documento — não é específico do CTE nem de nenhum doc concreto.

Stack: Python 3.x + Streamlit + PyYAML + Pandoc standalone + python-docx (residual).

---

## Schema v2 do estrutura.yaml — decisão fechada

O ficheiro `estrutura.yaml` define a hierarquia de cada documento.
A versão 2 substitui o campo `tipo` (v1) por dois conceitos separados:

**`semantic_type`** — o que o bloco *é*. Enum fechado, 12 tipos:
`cover`, `front_matter_note`, `revision_history`, `toc`, `list_of_figures`,
`list_of_tables`, `section`, `unnumbered_heading`, `subsection_group`,
`annexes`, `annex`, `glossary`.

**`behavior`** — overrides de layout/TOC/numeração. Só escrito no YAML quando
difere dos defaults do `semantic_type`. O YAML guarda intenção, não configuração
completa.

**`section_role`** — inferido automaticamente a partir do `semantic_type`:
`front_matter` / `main_matter` / `back_matter`. Pode ser overridden por elemento
quando necessário (ex: mover uma secção para back_matter a meio de construir um doc).

Os defaults por `semantic_type` ficam hardcoded em `semantic_type_registry.py`.
Nunca no YAML.

### Exemplo de estrutura v2 (caso base limpo)

```yaml
doc_type: CTE
doc_title: "CTE Fundações e Estruturas"
doc_version: "1.0"
doc_date: "2026-04-03"

defaults:
  page_size: A4
  orientation: portrait
  numbering_scheme: arabic
  toc_include: true

elementos:
  - slug: CAPA
    titulo: Capa
    semantic_type: cover      # defaults: sem TOC, page_break_before, sem numeração
    display_order: 1
    include: true
    # behavior: não escrito — os defaults de 'cover' já estão correctos

  - slug: TOC
    titulo: Índice Geral
    semantic_type: toc
    display_order: 2
    include: true

  - slug: SEC-I
    titulo: Disposições Gerais e Contratuais
    semantic_type: section    # defaults: TOC sim, numeração árabe contínua
    display_order: 3
    include: true
    filhos:
      - slug: LEX
        titulo: Léxico e Enquadramento Contratual
        semantic_type: section
        nivel: 1
        display_order: 3.1
        include: true

  - slug: ANEXOS
    titulo: Anexos
    semantic_type: annexes
    display_order: 4
    include: true
    filhos:
      - slug: ANX-GLOS
        titulo: Glossário Técnico
        semantic_type: annex  # defaults: page_break, numeração alfabética, restart
        display_order: 4.1
        include: true
```

### Exemplo com behavior override

```yaml
  - slug: PLANTA-A3
    titulo: Plantas de Estrutura
    semantic_type: section
    display_order: 5
    include: true
    behavior:
      page:
        section_break_before: true
        size: A3
        orientation: landscape
```

### Defaults do semantic_type registry

| semantic_type | section_role | toc | page_break | num_visible | num_scheme | num_restart |
|---|---|---|---|---|---|---|
| cover | front_matter | ✗ | ✓ | ✗ | none | ✗ |
| front_matter_note | front_matter | ✗ | ✓ | ✗ | roman_lower | ✗ |
| revision_history | front_matter | ✗ | ✓ | ✗ | none | ✗ |
| toc | front_matter | ✗ | ✓ | ✗ | none | ✗ |
| list_of_figures | front_matter | ✗ | ✓ | ✗ | none | ✗ |
| list_of_tables | front_matter | ✗ | ✓ | ✗ | none | ✗ |
| section | main_matter | ✓ | ✗ | ✓ | arabic | ✗ |
| unnumbered_heading | main_matter | ✓ | ✗ | ✗ | none | ✗ |
| subsection_group | main_matter | ✓ | ✗ | ✗ | none | ✗ |
| annexes | back_matter | ✗ | ✓ | ✗ | none | ✗ |
| annex | back_matter | ✓ | ✓ | ✓ | alpha | ✓ |
| glossary | back_matter | ✓ | ✓ | ✗ | none | ✗ |

---

## Pipeline de compilação — 3 tiers

```
estrutura.yaml (v2)
    ↓
compile.py
    ├── semantic_type_registry.resolve_behavior(elemento)
    │       → resolve defaults + aplica overrides do behavior block
    ├── mapeamento.yaml → MD sources por elemento
    ├── preprocessor.py → {{ excel }} e {{ VARIAVEL }} → MD
    ├── injeccta marcadores antes de cada elemento:
    │       <!-- pagebreak -->             se page_break_before
    │       <!-- sectionbreak -->          se section_break_before
    │       <!-- sectionbreak-landscape --> se landscape
    └── Pandoc
            ├── --lua-filter filters/pagebreak.lua
            │       converte marcadores HTML → Raw OpenXML (w:br, w:sectPr)
            └── --reference-doc JSJ-CTE-reference.docx
                    → DOCX final em 03_OUTPUT\
```

**Tier 1 — Pandoc nativo:** TOC geral, lista figuras/tabelas, numeração do corpo, estilos.
**Tier 2 — Lua filter:** page breaks, section breaks, placement de TOC/LOF/LOT.
**Tier 3 — python-docx:** orientação de página, page size por secção — fase posterior, fora do scope actual.

---

## Ficheiros em 04_APP\

| Ficheiro | Estado | Função |
|---|---|---|
| `app.py` | ✅ | UI Streamlit — Camada 1 (editor estrutura) + Camada 3 (TOC interactivo) |
| `compile.py` | ⏳ actualizar | Orquestrador — adicionar injecção de marcadores + --lua-filter |
| `preprocessor.py` | ✅ | Tags {{ excel }} + {{ VARIAVEL }} → MD |
| `semantic_type_registry.py` | ⏳ criar | Registry hardcoded + resolve_behavior() |
| `migrate_schema_v1_to_v2.py` | ⏳ criar | Migração estrutura.yaml v1 → v2 (standalone) |
| `filters/pagebreak.lua` | ⏳ criar | Lua filter Pandoc para page/section breaks |
| `config.yaml` | ⏳ criar | Multi-projecto + paths |

Prompt IDE para estas entregas: `00_GOVERNO/PROMPT-IDE-SCHEMA-V2.md`

---

## Ficheiros de trabalho por documento (fora de 04_APP\)

| Ficheiro | Conteúdo |
|---|---|
| `estrutura.yaml` | Schema v2: semantic_type + behavior (overrides) + filhos[] |
| `mapeamento.yaml` | MD sources + templates DOCX por elemento |
| `variaveis.yaml` | (opcional) Variáveis {{ VAR }} para o preprocessor |

Paths definidos em `config.yaml` por projecto.

---

## O que ainda não está feito (próximos passos por ordem)

1. IDE executa `PROMPT-IDE-SCHEMA-V2.md` → cria semantic_type_registry.py, migrate script, Lua filter, actualiza compile.py
2. David corre `migrate_schema_v1_to_v2.py` manualmente no estrutura.yaml do CTE e valida
3. config.yaml multi-projecto
4. variaveis.yaml + preprocessor {{ VARIAVEL }}
5. Camada 2 (mapeamento MD sources na app)
6. Camada 1 v2 (editor do bloco behavior por elemento)
7. Função Snapshot
8. Integração completa app → compile → DOCX real

---

*JSJ-DOC-ENGINE | 2026-04-03 | Cowork Governo*
