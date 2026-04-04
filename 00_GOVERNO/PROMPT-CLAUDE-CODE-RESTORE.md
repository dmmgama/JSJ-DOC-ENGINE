# URGENTE — app.py truncado — restaurar ficheiro completo

## PROBLEMA

O ficheiro `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` está **truncado na linha 1267**.
Termina a meio de `label_visibility="coll` — faltam ~130 linhas.

O ficheiro tem 1267 linhas mas deveria ter ~1400. Faltam:
1. Resto do tab TOC (linhas do checkbox, botões ↑↓, botão "Compilar DOCX")
2. **Tab "Estrutura" inteiro** (`with tab_est:`) — Camada 1
3. **Tab "Mapeamento" inteiro** (`with tab_map:`) — Camada 2

A app define 3 tabs na linha 1220:
```python
tab_toc, tab_est, tab_map = st.tabs(["TOC / Compilar", "Estrutura", "Mapeamento"])
```
Mas só o `with tab_toc:` existe (incompleto). Os blocos `with tab_est:` e `with tab_map:` **não existem** no ficheiro.

## TAREFA

1. **Verifica** se existe backup do app.py (git history, .bak, etc.)
2. Se **SIM** → restaura a versão mais recente completa (que tenha os 3 tabs)
3. Se **NÃO** → reconstrói o código dos tabs em falta usando o contexto abaixo

## CÓDIGO QUE FALTA — referência

### Fim do tab TOC (após linha 1266)

```python
            label_visibility="collapsed",
        )
        if novo_valor != el["incluir"]:
            st.session_state.elementos[idx]["incluir"] = novo_valor
            st.rerun()

        # Botão mover para cima
        if col_up.button("↑", key=f"up_{el['slug']}", disabled=(idx == 0)):
            mover_elemento_cima(idx)
            st.rerun()

        # Botão mover para baixo
        if col_dn.button("↓", key=f"dn_{el['slug']}", disabled=(idx == n_total - 1)):
            mover_elemento_baixo(idx)
            st.rerun()

    # Footer — botão Compilar DOCX (stub desactivado)
    st.divider()
    st.button(
        "Compilar DOCX",
        disabled=True,
        width="stretch",
        help="Disponível após configurar mapeamento (Camada 2)",
    )
```

### Tab Estrutura (Camada 1)

```python
# ===========================================================================
# TAB 2 — Editor de Estrutura (Camada 1)
# ===========================================================================
with tab_est:
    st.header("Editor de Estrutura")

    # Verificar se o ficheiro foi importado na sidebar — único entry point
    if not st.session_state.get("estrutura_yaml_raw"):
        st.info("Importe o ficheiro estrutura.yaml na sidebar para começar a editar.")
        st.stop()

    raw: dict = st.session_state.estrutura_yaml_raw

    # Mostrar qual o ficheiro activo
    st.caption(f"A editar: {st.session_state.get('estrutura_yaml_path', 'ficheiro importado')}")

    st.divider()

    # ── Metadados do documento ───────────────────────────────────────────
    with st.expander("Metadados do documento", expanded=False):
        col_dt, col_tit_doc = st.columns([2, 5])
        raw["doc_type"]  = col_dt.text_input("doc_type",  value=raw.get("doc_type", ""),  key="c1_doc_type")
        raw["doc_title"] = col_tit_doc.text_input("doc_title", value=raw.get("doc_title", ""), key="c1_doc_title")

    st.divider()

    # ── Tipos semânticos ──────────────────────────────────────────────────
    st.subheader("Tipos semânticos")
    st.caption("Tipos fixos definidos pelo sistema. Para cada elemento escolhe o tipo no editor abaixo.")

    # Tabela informativa dos tipos e section_role inferido
    dados_tipos = [
        {"Tipo": t, "Papel no documento": infer_section_role(t)}
        for t in SEMANTIC_TYPES
    ]
    st.dataframe(dados_tipos, width="stretch", hide_index=True)

    tipos = _obter_tipos(raw)
    st.divider()

    # ── Lista de elementos ────────────────────────────────────────────────
    st.subheader("Elementos")

    elementos_raw: list = raw.setdefault("elementos", [])

    # Cabeçalho das colunas
    ch1, ch2, ch3, ch4, ch5, ch6 = st.columns([2, 3, 2, 1, 1, 1])
    ch1.caption("Slug"); ch2.caption("Título"); ch3.caption("Tipo semântico")
    ch4.caption("Nível"); ch5.caption("Ordem"); ch6.caption("Inc.")

    _renderizar_lista_elementos(elementos_raw, 0, "c1_el", tipos, elementos_raw)

    # Limpar elementos raiz marcados para remoção
    raw["elementos"] = [el for el in elementos_raw if not el.get("_remover")]

    # Botão novo elemento no nível raiz
    if st.button("➕ Novo elemento", key="c1_btn_novo_el"):
        novo_slug = _auto_slug(raw["elementos"])
        raw["elementos"].append(_elemento_vazio(novo_slug))
        st.rerun()

    st.divider()

    # ── Validação e guardar ───────────────────────────────────────────────
    erros = _validar_elementos(raw.get("elementos", []))
    if erros:
        for msg_erro in erros:
            st.error(msg_erro)

    if st.button("💾 Guardar estrutura", key="c1_btn_guardar",
                 disabled=bool(erros), width="stretch"):
        # Usar o path de exportação definido na sidebar
        path_guardar = st.session_state.get("export_path_estrutura", "").strip()
        if not path_guardar:
            st.error("Defina o path de exportação na sidebar antes de guardar.")
        else:
            ok, msg = _guardar_estrutura_yaml_ficheiro(path_guardar, raw)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
```

### Tab Mapeamento (Camada 2)

```python
# ===========================================================================
# TAB 3 — Mapeamento de Conteúdo (Camada 2 MVP)
# ===========================================================================
with tab_map:
    st.header("Mapeamento de Conteúdo")

    # Verificar pré-condições
    if not st.session_state.get("estrutura_yaml_raw"):
        st.info("Carregue um projecto ou importe estrutura.yaml para começar.")
        st.stop()

    # Obter lista plana de elementos incluídos (include=True), recursivamente
    elementos_flat = _obter_elementos_flat(
        st.session_state.estrutura_yaml_raw.get("elementos", [])
    )

    if not elementos_flat:
        st.warning("Nenhum elemento com include=True encontrado na estrutura.")
        st.stop()

    # Obter mapeamento actual indexado por slug
    map_actual = _mapeamento_por_slug(st.session_state.get("mapeamento") or {})

    # Renderizar editor de mapeamento
    _renderizar_camada2(elementos_flat, map_actual)
```

## VERIFICAÇÃO

1. `app.py` tem os 3 blocos `with tab_toc:`, `with tab_est:`, `with tab_map:`
2. `streamlit run app.py` arranca sem erros
3. Os 3 tabs são visíveis e funcionais
4. Tab Mapeamento mostra os `md_source` do mapeamento.yaml (LEX e GERAL com paths)

## RESTRIÇÕES

- Não alterar funções acima da linha 1220 (já estão correctas)
- Não alterar `semantic_type_registry.py`, `compile.py`, `preprocessor.py`
- Se restaurares de git history, verifica que a versão restaurada inclui os bugfixes recentes (widget key init, fallback directório→ficheiro, confirmar_apagar_proj)
