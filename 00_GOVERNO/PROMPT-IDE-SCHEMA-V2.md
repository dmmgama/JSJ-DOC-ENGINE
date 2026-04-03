# PROMPT IDE — JSJ-DOC-ENGINE — Schema v2 + Lua Filter + Migração

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Implementar schema v2 do estrutura.yaml + Semantic Type Registry + Lua filter + migração
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**
> **Decisão de arquitectura:** `00_GOVERNO/DECISAO-SCHEMA-V2.md`

---

## CONTEXTO

**Projecto:** JSJ-DOC-ENGINE — sistema local MD → DOCX via Pandoc + Streamlit.
**Raiz:** `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\`

**Stack aprovada:**
- Python 3.x + Streamlit + PyYAML
- Pandoc (binário standalone)
- python-docx (pós-processamento — fora do scope desta tarefa)
- **Não usar:** LangChain, IA na pipeline, bases de dados, deploy web

---

## ESTADO ACTUAL DE `04_APP\`

```
04_APP\
├── app.py              ✅ Camada 1 + Camada 3 implementadas
├── compile.py          ✅ funcional (MD → DOCX via Pandoc)
├── preprocessor.py     ✅ funcional ({{ excel }} → tabelas MD)
├── config.yaml         ⚠️ schema antigo
├── requirements.txt    ✅
└── venv\               ✅
```

**Schema actual do estrutura.yaml (v1):**
```yaml
doc_type: CTE
doc_title: "..."
elementos:
  - slug: CAPA
    titulo: Capa
    tipo: front_matter        # ← campo a substituir por semantic_type
    display_order: 1
    include: true
    filhos: []
```

**O campo `tipo` tem estes valores actuais:** `front_matter`, `seccao`, `heading`,
`toc`, `anexo`, `anexos`.

---

## TAREFA — 4 ENTREGAS

### ENTREGA 1 — `semantic_type_registry.py`

Criar `04_APP\semantic_type_registry.py` com o registry completo dos tipos semânticos.

**Conteúdo obrigatório:**

```python
# semantic_type_registry.py
# Registry de tipos semânticos — defaults hardcoded
# O YAML guarda apenas overrides; estes são os valores base.

SEMANTIC_TYPES = [
    "cover",
    "front_matter_note",
    "revision_history",
    "toc",
    "list_of_figures",
    "list_of_tables",
    "section",
    "unnumbered_heading",
    "subsection_group",
    "annexes",
    "annex",
    "glossary",
]

# Defaults por semantic_type
# Campos: toc_include, page_break_before, section_break_before,
#         num_visible, num_scheme, num_restart, section_role
SEMANTIC_TYPE_DEFAULTS = {
    "cover":             {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "front_matter_note": {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "roman_lower", "num_restart": False, "section_role": "front_matter"},
    "revision_history":  {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "toc":               {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "list_of_figures":   {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "list_of_tables":    {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "section":           {"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": True,  "num_scheme": "arabic",      "num_restart": False, "section_role": "main_matter"},
    "unnumbered_heading":{"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "main_matter"},
    "subsection_group":  {"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "main_matter"},
    "annexes":           {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "back_matter"},
    "annex":             {"toc_include": True,  "page_break_before": True,  "section_break_before": False, "num_visible": True,  "num_scheme": "alpha",       "num_restart": True,  "section_role": "back_matter"},
    "glossary":          {"toc_include": True,  "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "back_matter"},
}

# Mapeamento de migração v1 → v2
TIPO_V1_TO_SEMANTIC_TYPE = {
    "front_matter": "front_matter_note",
    "seccao":       "section",
    "heading":      "section",
    "toc":          "toc",
    "anexo":        "annex",
    "anexos":       "annexes",
}

def get_defaults(semantic_type: str) -> dict:
    """Retorna os defaults para um semantic_type. Fallback para 'section'."""
    return SEMANTIC_TYPE_DEFAULTS.get(semantic_type, SEMANTIC_TYPE_DEFAULTS["section"]).copy()

def infer_section_role(semantic_type: str) -> str:
    """Infere section_role a partir do semantic_type."""
    return get_defaults(semantic_type)["section_role"]

def resolve_behavior(element: dict) -> dict:
    """
    Resolve o behavior efectivo de um elemento.
    Começa pelos defaults do semantic_type e aplica overrides do YAML.
    """
    semantic_type = element.get("semantic_type", "section")
    defaults = get_defaults(semantic_type)
    behavior = element.get("behavior", {}) or {}

    # Resolver section_role: manual override ou inferido
    section_role = element.get("section_role") or defaults["section_role"]

    # Resolver behavior com overrides
    toc_block      = behavior.get("toc", {}) or {}
    page_block     = behavior.get("page", {}) or {}
    numbering_block= behavior.get("numbering", {}) or {}

    return {
        "section_role":          section_role,
        "toc_include":           toc_block.get("include",           defaults["toc_include"]),
        "page_break_before":     page_block.get("break_before",     defaults["page_break_before"]),
        "section_break_before":  page_block.get("section_break_before", defaults["section_break_before"]),
        "page_size":             page_block.get("size",              "A4"),
        "orientation":           page_block.get("orientation",       "portrait"),
        "num_visible":           numbering_block.get("visible",      defaults["num_visible"]),
        "num_scheme":            numbering_block.get("scheme",       defaults["num_scheme"]),
        "num_restart":           numbering_block.get("restart",      defaults["num_restart"]),
        "num_start_at":          numbering_block.get("start_at",     1),
    }
```

---

### ENTREGA 2 — `migrate_schema_v1_to_v2.py`

Criar `04_APP\migrate_schema_v1_to_v2.py` — script standalone que converte
um `estrutura.yaml` v1 para v2.

**Comportamento:**
1. Recebe o path do ficheiro como argumento: `python migrate_schema_v1_to_v2.py <path>`
2. Lê o YAML v1
3. Para cada elemento (recursivamente incluindo `filhos`):
   - Renomeia `tipo` → `semantic_type` usando `TIPO_V1_TO_SEMANTIC_TYPE`
   - Se `tipo` era `heading` e `nivel` existe → manter `semantic_type: section`
   - Remove o campo `tipo` antigo
   - Não escreve `behavior` (fica vazio — os defaults são inferidos)
   - Não escreve `section_role` (fica inferido)
4. Adiciona ao cabeçalho do documento o bloco `defaults:` com valores standard
5. Guarda o resultado em `<nome_original>_v2.yaml` (não sobrescreve o original)
6. Imprime no terminal: lista de elementos migrados e aviso se algum `tipo` v1 não foi reconhecido

**Restrições:**
- Script standalone — não depende de `app.py`
- Importa `semantic_type_registry.py` para o mapeamento
- Tratar KeyError graciosamente: se `tipo` não existir, usar `"section"` como fallback
- Preservar todos os outros campos (`nota`, `nivel`, `include`, `display_order`, `filhos`, etc.)

---

### ENTREGA 3 — `filters\pagebreak.lua`

Criar `04_APP\filters\pagebreak.lua` — Lua filter para Pandoc.

**Função:** inserir page breaks e section breaks no DOCX com base em
comentários HTML injectados no MD processado pelo `compile.py`.

**Protocolo de comunicação (compile.py → Lua filter):**
O `compile.py` injeta comentários HTML especiais no MD concatenado antes
de chamar o Pandoc. O Lua filter interpreta esses comentários e insere
o OpenXML correcto.

**Comentários que o Lua filter deve reconhecer:**

| Comentário MD | Acção no DOCX |
|---|---|
| `<!-- pagebreak -->` | Insere `<w:br w:type="page"/>` |
| `<!-- sectionbreak -->` | Insere `<w:sectPr>` com continuação |
| `<!-- sectionbreak-landscape -->` | Insere section break com orientação landscape |

**Implementação Lua:**

```lua
-- filters/pagebreak.lua
-- Interpreta marcadores de paginação injectados pelo compile.py
-- e converte em Raw OpenXML para DOCX

local function is_pagebreak(el)
  return el.text and el.text:match("^%s*<!%-%-%s*pagebreak%s*%-%->%s*$")
end

local function is_sectionbreak(el)
  return el.text and el.text:match("^%s*<!%-%-%s*sectionbreak%s*%-%->%s*$")
end

local function is_sectionbreak_landscape(el)
  return el.text and el.text:match("^%s*<!%-%-%s*sectionbreak%-landscape%s*%-%->%s*$")
end

local PAGE_BREAK_XML = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

local SECTION_BREAK_XML = '<w:p><w:pPr><w:sectPr><w:type w:val="nextPage"/></w:sectPr></w:pPr></w:p>'

local SECTION_BREAK_LANDSCAPE_XML = [[
<w:p><w:pPr><w:sectPr>
  <w:type w:val="nextPage"/>
  <w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>
</w:sectPr></w:pPr></w:p>]]

function RawBlock(el)
  if el.format == "html" then
    if is_pagebreak(el) then
      return pandoc.RawBlock("openxml", PAGE_BREAK_XML)
    elseif is_sectionbreak_landscape(el) then
      return pandoc.RawBlock("openxml", SECTION_BREAK_LANDSCAPE_XML)
    elseif is_sectionbreak(el) then
      return pandoc.RawBlock("openxml", SECTION_BREAK_XML)
    end
  end
end
```

---

### ENTREGA 4 — Actualizar `compile.py`

Modificar `compile.py` para:

1. **Importar** `semantic_type_registry.resolve_behavior` e `semantic_type_registry.get_defaults`

2. **Antes de concatenar o MD de cada elemento**, injectar os marcadores
   de paginação baseados no behavior resolvido:

```python
# Conceito — adaptar ao código existente do compile.py
def _injectar_marcadores(elemento: dict) -> str:
    """
    Retorna string MD com marcadores de paginação a injectar
    antes do conteúdo do elemento.
    """
    behavior = resolve_behavior(elemento)
    marcadores = []

    if behavior["section_break_before"]:
        if behavior["orientation"] == "landscape":
            marcadores.append("<!-- sectionbreak-landscape -->")
        else:
            marcadores.append("<!-- sectionbreak -->")
    elif behavior["page_break_before"]:
        marcadores.append("<!-- pagebreak -->")

    return "\n".join(marcadores) + "\n" if marcadores else ""
```

3. **Activar o Lua filter** na chamada ao Pandoc:
```python
# Adicionar ao comando Pandoc existente:
"--lua-filter", str(Path(__file__).parent / "filters" / "pagebreak.lua"),
```

4. **Não alterar** nenhuma outra lógica do `compile.py` existente.

---

## RESTRIÇÕES

- **Nunca criar ficheiros fora de `04_APP\`**
- **Não modificar** `app.py`, `preprocessor.py`, `requirements.txt`
- **Não migrar** o `estrutura.yaml` do CTE automaticamente — o script de migração
  é gerado mas só executado manualmente por David
- Comentar código em **português**
- Funções curtas com responsabilidade única
- `semantic_type_registry.py` deve ser importável sem Streamlit (é usado pelo compile.py)
- O Lua filter deve ser silencioso — não imprimir nada em caso de sucesso

---

## VERIFICAÇÃO

A tarefa está concluída quando:

1. `python -c "from semantic_type_registry import get_defaults; print(get_defaults('cover'))"` retorna dict correcto
2. `python migrate_schema_v1_to_v2.py <path_estrutura_v1>` gera `*_v2.yaml` sem erros
3. O ficheiro `_v2.yaml` tem `semantic_type` em vez de `tipo` em todos os elementos
4. O ficheiro `_v2.yaml` tem o bloco `defaults:` no cabeçalho
5. `filters\pagebreak.lua` existe e o Pandoc aceita `--lua-filter filters/pagebreak.lua` sem erro
6. `compile.py` importa `semantic_type_registry` sem erro
7. Um documento com `page_break_before: true` num elemento produz page break no DOCX final

---

## ENTREGÁVEIS

| Path | Estado esperado |
|------|----------------|
| `04_APP\semantic_type_registry.py` | ✅ criado |
| `04_APP\migrate_schema_v1_to_v2.py` | ✅ criado |
| `04_APP\filters\pagebreak.lua` | ✅ criado |
| `04_APP\compile.py` | ✅ modificado (injecção marcadores + lua filter) |
| `04_APP\README.md` | ✅ secção 4 e 8 actualizadas |

**NÃO criar:**
- `estrutura_v2.yaml` (migração manual por David)
- Qualquer ficheiro fora de `04_APP\`

---

**Fim — PROMPT-IDE-SCHEMA-V2.md — 2026-04-03**
