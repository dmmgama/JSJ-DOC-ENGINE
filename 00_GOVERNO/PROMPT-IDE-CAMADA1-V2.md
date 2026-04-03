# PROMPT IDE — JSJ-DOC-ENGINE — Camada 1 v2: semantic_type + behavior

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Actualizar app.py — Camada 1 para usar schema v2 (semantic_type + behavior)
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**
> **Pré-requisito:** `semantic_type_registry.py` já existe em `04_APP\`

---

## CONTEXTO

O `app.py` tem duas camadas implementadas:
- **Camada 3** (tab "TOC / Compilar"): TOC interactivo, export/import, toggle N/A, setas
- **Camada 1** (tab "Estrutura"): editor hierárquico da estrutura do documento

A Camada 1 usa actualmente o campo `tipo` (schema v1) com valores:
`seccao`, `heading`, `anexo`, `toc`, `front_matter`.

O schema v2 substitui `tipo` por `semantic_type` (12 valores do registry) e
adiciona um bloco `behavior` opcional por elemento.

O ficheiro `semantic_type_registry.py` já existe em `04_APP\` com:
- `SEMANTIC_TYPES` — lista dos 12 tipos válidos
- `SEMANTIC_TYPE_DEFAULTS` — defaults por tipo
- `get_defaults(semantic_type)` — devolve defaults para um tipo
- `infer_section_role(semantic_type)` — devolve front/main/back_matter
- `resolve_behavior(element)` — resolve behavior efectivo com overrides

---

## ESTADO ACTUAL DO app.py (o que precisa de mudar)

```python
# ACTUAL — a substituir:
TIPOS_PREDEFINIDOS = ["seccao", "heading", "anexo", "toc", "front_matter"]

# em _obter_tipos():
return list(TIPOS_PREDEFINIDOS)  # ← ignorar SEMANTIC_TYPES

# em _elemento_vazio():
"tipo": "heading"                 # ← campo errado

# em _renderizar_formulario_elemento():
el["tipo"] = selectbox(...)       # ← selectbox com tipos v1

# em _renderizar_elemento():
rotulo_tipo = el.get("tipo", "heading")  # ← campo errado

# em parse_estrutura_yaml() / export:
tipo = el.get("tipo", "heading")  # ← campo errado
```

---

## TAREFA — 3 alterações ao app.py

### Alteração 1 — Importar registry e substituir TIPOS_PREDEFINIDOS

No topo do ficheiro, após os imports existentes, adicionar:

```python
from semantic_type_registry import (
    SEMANTIC_TYPES,
    get_defaults,
    infer_section_role,
    resolve_behavior,
)
```

Remover a constante `TIPOS_PREDEFINIDOS` e todas as suas referências.

---

### Alteração 2 — Camada 1: substituir `tipo` por `semantic_type`

**2a. `_obter_tipos(raw)`**

Ignorar `tipos_disponiveis` do YAML (campo v1 que deixa de existir).
A lista de tipos vem sempre do registry:

```python
def _obter_tipos(raw: dict) -> list:
    """Tipos semânticos disponíveis — sempre do registry, nunca do YAML."""
    return list(SEMANTIC_TYPES)
```

**2b. `_elemento_vazio(slug)`**

Substituir `"tipo": "heading"` por `"semantic_type": "section"`:

```python
def _elemento_vazio(slug: str) -> dict:
    return {
        "slug":          slug,
        "titulo":        "",
        "semantic_type": "section",   # ← era "tipo": "heading"
        "nivel":         1,
        "display_order": 0,
        "include":       True,
        "filhos":        [],
    }
```

**2c. `_renderizar_formulario_elemento(...)`**

Substituir o selectbox de `tipo` por selectbox de `semantic_type`:

```python
# ANTES:
tipo_actual = el.get("tipo", "heading")
idx_tipo = tipos.index(tipo_actual) if tipo_actual in tipos else 0
novo_tipo = col_tipo.selectbox("Tipo", tipos, index=idx_tipo, key=f"{prefixo}_tipo")
el["tipo"] = novo_tipo

# DEPOIS:
st_actual = el.get("semantic_type", "section")
idx_st = SEMANTIC_TYPES.index(st_actual) if st_actual in SEMANTIC_TYPES else SEMANTIC_TYPES.index("section")
novo_st = col_tipo.selectbox("Tipo semântico", SEMANTIC_TYPES, index=idx_st, key=f"{prefixo}_semantic_type")
el["semantic_type"] = novo_st

# Após mudar o tipo, inferir e mostrar section_role
section_role = el.get("section_role") or infer_section_role(novo_st)
col_tipo.caption(f"↳ {section_role}")
```

**2d. `_renderizar_elemento(...)`**

Substituir o rótulo do expander:

```python
# ANTES:
rotulo_tipo = el.get("tipo", "heading")

# DEPOIS:
rotulo_tipo = el.get("semantic_type", "section")
```

**2e. Secção "Tipos disponíveis" da tab Estrutura**

Esta secção mostrava a lista editável de tipos v1 (adicionar/renomear/apagar).
Com o schema v2, os tipos são fixos (vêm do registry) e não são editáveis pelo utilizador.

Substituir toda a secção "Tipos disponíveis" por uma secção informativa simples:

```python
st.subheader("Tipos semânticos")
st.caption("Tipos fixos definidos pelo sistema. Para cada elemento escolhe o tipo no editor abaixo.")

# Mostrar tabela informativa dos tipos e section_role inferido
dados_tipos = [
    {"Tipo": t, "Papel no documento": infer_section_role(t)}
    for t in SEMANTIC_TYPES
]
st.dataframe(dados_tipos, use_container_width=True, hide_index=True)
```

---

### Alteração 3 — Camada 1: adicionar editor de behavior por elemento

No `_renderizar_formulario_elemento(...)`, após o selectbox de `semantic_type`,
adicionar um expander "⚙ Comportamento" que só aparece quando aberto:

```python
with st.expander("⚙ Comportamento (paginação / numeração / TOC)", expanded=False):
    beh = el.get("behavior", {}) or {}
    beh_page = beh.get("page", {}) or {}
    beh_num  = beh.get("numbering", {}) or {}
    beh_toc  = beh.get("toc", {}) or {}

    defaults = get_defaults(el.get("semantic_type", "section"))

    col_b1, col_b2, col_b3 = st.columns(3)

    # TOC
    toc_include = col_b1.checkbox(
        "Entra no TOC",
        value=beh_toc.get("include", defaults["toc_include"]),
        key=f"{prefixo}_toc_include"
    )

    # Paginação
    page_break = col_b2.checkbox(
        "Page break antes",
        value=beh_page.get("break_before", defaults["page_break_before"]),
        key=f"{prefixo}_page_break"
    )
    section_break = col_b2.checkbox(
        "Section break antes",
        value=beh_page.get("section_break_before", defaults["section_break_before"]),
        key=f"{prefixo}_section_break"
    )

    # Numeração
    ESQUEMAS = ["arabic", "roman_lower", "roman_upper", "alpha", "none"]
    num_scheme_actual = beh_num.get("scheme", defaults["num_scheme"])
    idx_scheme = ESQUEMAS.index(num_scheme_actual) if num_scheme_actual in ESQUEMAS else 0
    num_scheme = col_b3.selectbox(
        "Esquema numeração",
        ESQUEMAS,
        index=idx_scheme,
        key=f"{prefixo}_num_scheme"
    )
    num_visible = col_b3.checkbox(
        "Número visível",
        value=beh_num.get("visible", defaults["num_visible"]),
        key=f"{prefixo}_num_visible"
    )
    num_restart = col_b3.checkbox(
        "Reiniciar numeração aqui",
        value=beh_num.get("restart", defaults["num_restart"]),
        key=f"{prefixo}_num_restart"
    )

    # Guardar apenas overrides (não gravar se igual ao default)
    # Regra: só escreve o campo se difere do default do semantic_type
    novo_beh = {}

    toc_blk = {}
    if toc_include != defaults["toc_include"]:
        toc_blk["include"] = toc_include
    if toc_blk:
        novo_beh["toc"] = toc_blk

    page_blk = {}
    if page_break   != defaults["page_break_before"]:
        page_blk["break_before"] = page_break
    if section_break != defaults["section_break_before"]:
        page_blk["section_break_before"] = section_break
    if page_blk:
        novo_beh["page"] = page_blk

    num_blk = {}
    if num_scheme  != defaults["num_scheme"]:
        num_blk["scheme"]  = num_scheme
    if num_visible != defaults["num_visible"]:
        num_blk["visible"] = num_visible
    if num_restart != defaults["num_restart"]:
        num_blk["restart"] = num_restart
    if num_blk:
        novo_beh["numbering"] = num_blk

    # Só escreve behavior se tiver overrides
    if novo_beh:
        el["behavior"] = novo_beh
    else:
        el.pop("behavior", None)   # limpa behavior se não há overrides
```

---

## RESTRIÇÕES

- **Não tocar** em nada fora da Camada 1 (tab "Estrutura") e nos imports do topo
- **Não tocar** na Camada 3 (tab "TOC / Compilar") — continua a funcionar com o estado actual
- **Não tocar** em `compile.py`, `preprocessor.py`, `semantic_type_registry.py`
- Comentar código em **português**
- O campo `tipo` (v1) pode ser lido pelo parser de import para compatibilidade retroactiva,
  mas nunca escrito no export — só `semantic_type`
- **Compatibilidade retroactiva no import:** se um elemento carregado tiver `tipo` mas não
  `semantic_type`, fazer a conversão automática usando `TIPO_V1_TO_SEMANTIC_TYPE` do registry

```python
# Adicionar ao parser de import (onde lê elementos do YAML):
from semantic_type_registry import TIPO_V1_TO_SEMANTIC_TYPE

# Para cada elemento:
if "tipo" in el and "semantic_type" not in el:
    el["semantic_type"] = TIPO_V1_TO_SEMANTIC_TYPE.get(el["tipo"], "section")
    del el["tipo"]
```

---

## VERIFICAÇÃO

A tarefa está concluída quando:

1. `streamlit run app.py` arranca sem erros
2. Tab "Estrutura" — secção "Tipos semânticos" mostra tabela com os 12 tipos e section_role
3. Cada elemento mostra selectbox com os 12 `semantic_type` do registry (não os 5 v1)
4. Ao mudar o tipo de um elemento, aparece o `section_role` inferido debaixo do selectbox
5. O expander "⚙ Comportamento" abre e permite editar TOC, page break, numeração
6. Os campos do behavior mostram os defaults do `semantic_type` seleccionado
7. Ao exportar `estrutura.yaml`, o campo gerado é `semantic_type`, não `tipo`
8. Importar um `estrutura.yaml` v1 (com `tipo`) converte automaticamente para `semantic_type`
9. Tab "TOC / Compilar" continua a funcionar sem alterações

---

## ENTREGÁVEL

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ modificado |

Após concluir, actualizar `04_APP\README.md` secção 10:
- `app.py` → ✅ Camada 1 v2 (semantic_type + behavior editor) + Camada 3 funcional

---

**Fim — PROMPT-IDE-CAMADA1-V2.md — 2026-04-03**
