# PROMPT IDE — JSJ-DOC-ENGINE — Camada 2 MVP: Mapeamento de Conteúdo

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Implementar Camada 2 MVP na app.py — mapeamento MD sources por elemento
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**
> **Scope:** MVP funcional — sem refinamentos de UX

---

## CONTEXTO

A app tem 2 tabs: `"TOC / Compilar"` e `"Estrutura"`.
A Camada 2 é um terceiro tab: `"Mapeamento"`.

O `mapeamento.yaml` já existe como estrutura de dados em session_state
(`st.session_state.mapeamento`) e já há funções de parse e export.
O que falta é a UI de edição.

**O que o mapeamento.yaml guarda por elemento:**
```yaml
elementos:
  - slug: LEX
    md_source: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/LEX.md"
    md_scope: ficheiro_inteiro   # ficheiro_inteiro | heading_especifico
    template_docx: default       # default | path absoluto para .docx
    nota: ""
```

**O que a Camada 2 tem de fazer:**
Para cada elemento da `estrutura.yaml` (com `include: true`), permitir ao
utilizador definir o `md_source`, `md_scope` e `template_docx`.

---

## ESTADO ACTUAL DO app.py

```python
# Tabs actuais:
tab_toc, tab_est = st.tabs(["TOC / Compilar", "Estrutura"])

# Session state relevante:
st.session_state.estrutura_yaml_raw   # dict com elementos hierárquicos
st.session_state.mapeamento           # dict: {meta, elementos: [{slug, md_source, ...}]}
st.session_state.mapeamento_yaml_path # path do mapeamento.yaml activo
```

Funções já existentes a reutilizar:
- `gerar_mapeamento_yaml(elementos, projecto)` — serializa para YAML
- `parse_mapeamento_yaml(conteudo)` — lê mapeamento.yaml
- `_guardar_estrutura_yaml_ficheiro(path, dict)` — escreve YAML no disco

---

## TAREFA

### 1. Adicionar terceiro tab "Mapeamento"

```python
# Substituir:
tab_toc, tab_est = st.tabs(["TOC / Compilar", "Estrutura"])

# Por:
tab_toc, tab_est, tab_map = st.tabs(["TOC / Compilar", "Estrutura", "Mapeamento"])
```

---

### 2. Implementar conteúdo do tab "Mapeamento"

**Lógica geral:**

```python
with tab_map:
    st.header("Mapeamento de Conteúdo")

    # Verificar pré-condições
    if not st.session_state.get("estrutura_yaml_raw"):
        st.info("Carregue um projecto ou importe estrutura.yaml para começar.")
        st.stop()

    # Obter lista plana de elementos incluídos (include=True), recursivamente
    # Usar a função _todos_slugs() já existente como base, mas precisamos
    # dos elementos completos (slug + titulo + semantic_type), não só slugs

    elementos_flat = _obter_elementos_flat(
        st.session_state.estrutura_yaml_raw.get("elementos", [])
    )
    # elementos_flat: lista de dicts [{slug, titulo, semantic_type, nivel}, ...]
    # apenas elementos com include=True

    # Obter mapeamento actual (dict slug → {md_source, md_scope, template_docx, nota})
    map_actual = _mapeamento_por_slug(st.session_state.mapeamento)

    # Renderizar editor
    _renderizar_camada2(elementos_flat, map_actual)
```

**Funções a criar:**

```python
def _obter_elementos_flat(elementos: list, nivel_max: int = 99) -> list:
    """
    Percorre a árvore recursivamente e devolve lista plana de todos os
    elementos com include=True.
    Cada item: {"slug": str, "titulo": str, "semantic_type": str, "nivel": int, "profundidade": int}
    """
    resultado = []
    def _percorrer(lista, prof):
        for el in lista:
            if el.get("include", True):
                resultado.append({
                    "slug":          el.get("slug", ""),
                    "titulo":        el.get("titulo", ""),
                    "semantic_type": el.get("semantic_type", "section"),
                    "nivel":         el.get("nivel", 0),
                    "profundidade":  prof,
                })
                filhos = el.get("filhos", []) or []
                if filhos:
                    _percorrer(filhos, prof + 1)
    _percorrer(elementos, 0)
    return resultado


def _mapeamento_por_slug(mapeamento: dict) -> dict:
    """
    Converte lista de elementos do mapeamento em dict {slug: {campos}}.
    Tolerante a mapeamento vazio ou None.
    """
    if not mapeamento:
        return {}
    elementos = mapeamento.get("elementos", []) or []
    return {el["slug"]: el for el in elementos if "slug" in el}


def _renderizar_camada2(elementos_flat: list, map_actual: dict) -> None:
    """
    Renderiza o editor de mapeamento: uma linha por elemento.
    Campos editáveis: md_source, md_scope, template_docx, nota.
    """
    MD_SCOPE_OPCOES = ["ficheiro_inteiro", "heading_especifico"]

    novo_mapeamento_elementos = []

    for el in elementos_flat:
        slug          = el["slug"]
        titulo        = el["titulo"]
        semantic_type = el["semantic_type"]
        prof          = el["profundidade"]

        # Indentação visual por profundidade
        margem = "　" * prof  # espaço em branco largo (U+3000)

        # Valores actuais do mapeamento (ou defaults vazios)
        map_el = map_actual.get(slug, {})
        md_source_actual    = map_el.get("md_source", "")
        md_scope_actual     = map_el.get("md_scope", "ficheiro_inteiro")
        template_docx_actual= map_el.get("template_docx", "default")
        nota_actual         = map_el.get("nota", "")

        with st.expander(
            f"{margem}**{slug}** · *{semantic_type}* — {titulo}",
            expanded=(md_source_actual == "")  # aberto se ainda sem source
        ):
            col1, col2 = st.columns([3, 1])

            md_source = col1.text_input(
                "Ficheiro MD (path absoluto)",
                value=md_source_actual,
                key=f"map_{slug}_md_source",
                placeholder=r"C:\caminho\para\ficheiro.md",
            )

            idx_scope = MD_SCOPE_OPCOES.index(md_scope_actual) \
                        if md_scope_actual in MD_SCOPE_OPCOES else 0
            md_scope = col2.selectbox(
                "Scope",
                MD_SCOPE_OPCOES,
                index=idx_scope,
                key=f"map_{slug}_md_scope",
            )

            col3, col4 = st.columns([3, 1])

            template_docx = col3.text_input(
                "Template DOCX (deixar 'default' para usar o geral)",
                value=template_docx_actual,
                key=f"map_{slug}_template",
            )

            nota = col4.text_input(
                "Nota",
                value=nota_actual,
                key=f"map_{slug}_nota",
            )

            # Validação simples: avisar se md_source não existe no disco
            if md_source and not Path(md_source).exists():
                st.warning(f"⚠️ Ficheiro não encontrado: {md_source}")
            elif md_source:
                st.success("✅ Ficheiro encontrado")

        novo_mapeamento_elementos.append({
            "slug":         slug,
            "md_source":    md_source,
            "md_scope":     md_scope,
            "template_docx":template_docx,
            "nota":         nota,
        })

    # Guardar em session_state continuamente
    if not st.session_state.mapeamento:
        st.session_state.mapeamento = {}
    st.session_state.mapeamento["elementos"] = novo_mapeamento_elementos

    st.divider()

    # Botão guardar
    path_map = st.session_state.get("mapeamento_yaml_path", "")
    col_path, col_btn = st.columns([4, 1])
    path_export = col_path.text_input(
        "Path de exportação",
        value=path_map,
        key="map_export_path",
        placeholder=r"C:\caminho\para\mapeamento.yaml",
    )
    if col_btn.button("💾 Guardar mapeamento.yaml", use_container_width=True, key="map_btn_guardar"):
        if not path_export.strip():
            st.error("Indica o path de exportação.")
        else:
            try:
                dados_export = {
                    "doc_id":        st.session_state.projecto_activo.get("id", ""),
                    "doc_title":     st.session_state.projecto_activo.get("name", ""),
                    "estrutura_ref": "estrutura.yaml",
                    "data":          str(__import__("datetime").date.today()),
                    "templates": {
                        "geral": st.session_state.projecto_activo.get(
                            "reference_doc",
                            "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"
                        )
                    },
                    "elementos": novo_mapeamento_elementos,
                }
                with open(path_export.strip(), "w", encoding="utf-8") as f:
                    yaml.dump(dados_export, f, allow_unicode=True,
                              default_flow_style=False, sort_keys=False)
                st.session_state.mapeamento_yaml_path = path_export.strip()
                st.success(f"✅ Guardado em: {path_export.strip()}")
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")
```

---

## RESTRIÇÕES

- **Não tocar** em tab "TOC / Compilar" nem tab "Estrutura"
- **Não tocar** em `compile.py`, `preprocessor.py`, `semantic_type_registry.py`
- MVP: sem drag-and-drop, sem file browser gráfico, sem preview de MD
- O path de MD é introduzido manualmente por texto — suficiente para MVP
- `template_docx` por defeito é a string `"default"` — não um path vazio
- Comentar código em **português**
- Não introduzir dependências novas

---

## VERIFICAÇÃO

1. `streamlit run app.py` arranca sem erros
2. Aparece terceiro tab "Mapeamento"
3. Tab mostra um expander por elemento incluído na estrutura
4. Campos md_source, md_scope, template_docx, nota são editáveis
5. Se md_source preenchido e ficheiro existe → ✅ verde; se não existe → ⚠️ aviso
6. Botão "Guardar mapeamento.yaml" escreve ficheiro no path indicado
7. O YAML gerado tem a estrutura correcta (slug, md_source, md_scope, template_docx, nota)
8. Tabs "TOC / Compilar" e "Estrutura" continuam funcionais

---

## ENTREGÁVEL

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ modificado — tab "Mapeamento" adicionado |

Após concluir, actualizar `04_APP\README.md` secção 10:
- `app.py` → ✅ Camada 2 MVP (mapeamento md_source por elemento)

---

**Fim — PROMPT-IDE-CAMADA2-MVP.md — 2026-04-03**
