# DECISÃO — Schema estrutura.yaml v2

> **Data:** 2026-04-03
> **Decisão:** D12
> **Estado:** FECHADA

---

## Contexto

O schema v1 do `estrutura.yaml` tem campos planos por elemento:
`slug`, `titulo`, `tipo`, `nivel`, `include`, `display_order`, `filhos[]`, `nota`.

Para suportar comportamentos de paginação, numeração e TOC por elemento,
o schema precisa de ser enriquecido — sem over-engineering.

Fontes de decisão: `01_AUDITORIAS/RESEARCH/APP-AuditoriaEstrutura-gemini.md`
e `APP-AuditoriaEstrutura-Perplexity.md`.

---

## Decisões fechadas

### D12a — Dois conceitos separados por elemento

- `semantic_type` — o que o bloco *é* (enum fechado, hardcoded na app)
- `behavior` — overrides de layout/TOC/numeração (só escrito quando difere dos defaults)

O YAML guarda apenas overrides. Os defaults por `semantic_type` ficam
hardcoded na app num registry (`SEMANTIC_TYPE_REGISTRY`). Isto evita
20 campos preenchidos por nó no caso base.

### D12b — `section_role` inferido, não manual

`section_role` (`front_matter` / `main_matter` / `back_matter`) é
inferido pelo app a partir do `semantic_type`, mas pode ser overridden
por elemento quando necessário (ex: mover uma secção para back_matter
a meio de construir um documento).

Quando há override manual, o campo `section_role` é escrito no YAML.
Quando é inferido, não é escrito (defaults limpos).

### D12c — Pipeline de compilação: 3 tiers

- **Tier 1 — Pandoc nativo:** compilação principal, TOC geral,
  lista figuras/tabelas, numeração do corpo, estilos via reference.docx
- **Tier 2 — Lua filter:** page breaks, section breaks, placement TOC/LOF/LOT
- **Tier 3 — python-docx:** orientação de página, page size por secção,
  acertos finais (fase posterior — fora do scope desta iteração)

Lua filter vive em `04_APP/filters/pagebreak.lua`.

### D12d — Migração schema: agora, antes da Camada 2

O schema v2 é implementado antes da Camada 2. A Camada 2 vai ler
`semantic_type` para saber o que mostrar por elemento — implementá-la
com o schema v1 e migrar depois é retrabalho garantido.

---

## Schema v2 — estrutura completa

### Metadados do documento (cabeçalho)

```yaml
doc_type: CTE
doc_title: "CTE Fundações e Estruturas"
doc_version: "1.0"
doc_date: "2026-04-03"

# Defaults globais do documento (overridáveis por elemento via behavior)
defaults:
  page_size: A4
  orientation: portrait
  numbering_scheme: arabic    # arabic | roman_lower | roman_upper | alpha | none
  toc_include: true
```

### Por elemento

```yaml
- slug: CAPA
  titulo: Capa
  semantic_type: cover        # enum — ver registry abaixo
  section_role: front_matter  # só presente se override do inferido
  nivel: 0
  display_order: 1
  include: true
  nota: ""                    # campo livre, não obrigatório

  # behavior: só presente se difere dos defaults do semantic_type
  behavior:
    toc:
      include: false
    page:
      break_before: true
      section_break_before: false
      size: A4
      orientation: portrait
    numbering:
      visible: false
      scheme: none
      restart: false
```

**Regra:** se o `behavior` de um elemento é idêntico aos defaults do seu
`semantic_type`, o bloco `behavior` não é escrito no YAML.
Isto mantém o YAML limpo para o caso base.

---

## Semantic Type Registry (hardcoded na app)

| semantic_type | section_role inferido | toc | page_break | num_visible | num_scheme | num_restart |
|---|---|---|---|---|---|---|
| `cover` | front_matter | false | true | false | none | false |
| `front_matter_note` | front_matter | false | true | false | roman_lower | false |
| `revision_history` | front_matter | false | true | false | none | false |
| `toc` | front_matter | false | true | false | none | false |
| `list_of_figures` | front_matter | false | true | false | none | false |
| `list_of_tables` | front_matter | false | true | false | none | false |
| `section` | main_matter | true | false | true | arabic | false |
| `unnumbered_heading` | main_matter | true | false | false | none | false |
| `subsection_group` | main_matter | true | false | false | none | false |
| `annexes` | back_matter | false | true | false | none | false |
| `annex` | back_matter | true | true | true | alpha | true |
| `glossary` | back_matter | true | true | false | none | false |

---

## Campos behavior — referência completa

```yaml
behavior:
  toc:
    include: bool           # entra no índice geral?
    kind: general           # general | figures | tables (só para tipo toc/lof/lot)
    depth: 3                # profundidade (só para toc)

  page:
    break_before: bool      # page break antes deste elemento
    section_break_before: bool  # section break Word (para mudar orientação/tamanho)
    size: A4                # A4 | A3 | A4_landscape
    orientation: portrait   # portrait | landscape

  numbering:
    visible: bool           # número aparece no heading?
    scheme: arabic          # arabic | roman_lower | roman_upper | alpha | none
    restart: bool           # reinicia contagem aqui?
    start_at: 1             # valor inicial (quando restart: true)
```

---

## Compatibilidade com schema v1

O campo `tipo` (v1) é substituído por `semantic_type` (v2).
Mapeamento de migração:

| tipo v1 | semantic_type v2 |
|---|---|
| front_matter | front_matter_note |
| seccao | section |
| heading | section (nivel > 0) ou subsection_group |
| toc | toc |
| anexo | annex |
| anexos | annexes |

A migração do `estrutura.yaml` existente é feita pelo script de migração
gerado pelo IDE: `04_APP/migrate_schema_v1_to_v2.py`.

---

## Alternativa rejeitada

**Schema plano com flags avulsas** (`is_annex`, `is_toc`, `is_cover`, etc.)
— rejeitado por criar estados contraditórios e redundância com `semantic_type`.

**Gravar todos os defaults por nó** — rejeitado por tornar o YAML ruidoso
e difícil de manter. 68 elementos × 10 campos = 680 linhas de ruído.

---

**Criado:** 2026-04-03 | **Agente:** Cowork Governo
