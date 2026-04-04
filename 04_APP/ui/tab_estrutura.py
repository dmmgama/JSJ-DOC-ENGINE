"""
ui/tab_estrutura.py — Tab Editor de Estrutura (Camada 1).
Editor hierárquico de elementos do documento.
"""
import streamlit as st

from semantic_type_registry import SEMANTIC_TYPES, get_defaults, infer_section_role
from core.models import elemento_vazio
from core.services import auto_slug, obter_tipos, validar_elementos
from adapters.yaml_io import guardar_estrutura_yaml
from ui.state import (
    get_estrutura_raw, get_estrutura_path, get_export_path_estrutura,
    get_confirmar_remover, set_confirmar_remover,
)


def _renderizar_formulario_elemento(el: dict, prefixo: str,
                                     tipos: list, elementos_raiz: list) -> None:
    """Renderiza o formulário inline de um elemento (edit in place)."""
    col_slug, col_titulo, col_tipo, col_nivel, col_ord, col_inc = st.columns([2, 3, 2, 1, 1, 1])

    novo_slug = col_slug.text_input("Slug", value=el.get("slug", ""), key=f"{prefixo}_slug",
        help="⚠️ Imutável após criação — alterar aqui requer actualizar mapeamento.yaml",
        label_visibility="collapsed")
    el["slug"] = novo_slug.strip()

    novo_titulo = col_titulo.text_input("Título", value=el.get("titulo", ""),
        key=f"{prefixo}_titulo", label_visibility="collapsed")
    el["titulo"] = novo_titulo

    st_actual = el.get("semantic_type", "section")
    idx_st = SEMANTIC_TYPES.index(st_actual) if st_actual in SEMANTIC_TYPES else SEMANTIC_TYPES.index("section")
    novo_st = col_tipo.selectbox("Tipo semântico", SEMANTIC_TYPES, index=idx_st,
        key=f"{prefixo}_semantic_type", label_visibility="collapsed")
    el["semantic_type"] = novo_st
    section_role = el.get("section_role") or infer_section_role(novo_st)
    col_tipo.caption(f"↳ {section_role}")

    if novo_st == "section":
        nivel_actual = el.get("nivel", 1)
        if not isinstance(nivel_actual, int):
            nivel_actual = 1
        novo_nivel = col_nivel.number_input("Nível", min_value=1, max_value=4,
            value=nivel_actual, key=f"{prefixo}_nivel", label_visibility="collapsed")
        el["nivel"] = int(novo_nivel)
    else:
        col_nivel.markdown("")

    ordem_actual = el.get("display_order", 0)
    if not isinstance(ordem_actual, (int, float)):
        ordem_actual = 0
    novo_ordem = col_ord.number_input("Ordem", value=int(ordem_actual),
        key=f"{prefixo}_order", label_visibility="collapsed")
    el["display_order"] = int(novo_ordem)

    novo_inc = col_inc.checkbox("Incluir", value=bool(el.get("include", True)),
        key=f"{prefixo}_inc", label_visibility="collapsed")
    el["include"] = novo_inc

    # ── behavior (expander opcional) ──────────────────────────────────
    with st.expander("⚙ Comportamento (paginação / numeração / TOC)", expanded=False):
        beh = el.get("behavior", {}) or {}
        beh_page = beh.get("page", {}) or {}
        beh_num = beh.get("numbering", {}) or {}
        beh_toc = beh.get("toc", {}) or {}
        defaults = get_defaults(el.get("semantic_type", "section"))
        col_b1, col_b2, col_b3 = st.columns(3)

        toc_include = col_b1.checkbox("Entra no TOC",
            value=beh_toc.get("include", defaults["toc_include"]), key=f"{prefixo}_toc_include")
        page_break = col_b2.checkbox("Page break antes",
            value=beh_page.get("break_before", defaults["page_break_before"]), key=f"{prefixo}_page_break")
        section_break = col_b2.checkbox("Section break antes",
            value=beh_page.get("section_break_before", defaults["section_break_before"]),
            key=f"{prefixo}_section_break")

        ESQUEMAS = ["arabic", "roman_lower", "roman_upper", "alpha", "none"]
        num_scheme_actual = beh_num.get("scheme", defaults["num_scheme"])
        idx_scheme = ESQUEMAS.index(num_scheme_actual) if num_scheme_actual in ESQUEMAS else 0
        num_scheme = col_b3.selectbox("Esquema numeração", ESQUEMAS, index=idx_scheme,
            key=f"{prefixo}_num_scheme")
        num_visible = col_b3.checkbox("Número visível",
            value=beh_num.get("visible", defaults["num_visible"]), key=f"{prefixo}_num_visible")
        num_restart = col_b3.checkbox("Reiniciar numeração aqui",
            value=beh_num.get("restart", defaults["num_restart"]), key=f"{prefixo}_num_restart")

        # Guardar apenas overrides
        novo_beh = {}
        toc_blk = {}
        if toc_include != defaults["toc_include"]:
            toc_blk["include"] = toc_include
        if toc_blk:
            novo_beh["toc"] = toc_blk
        page_blk = {}
        if page_break != defaults["page_break_before"]:
            page_blk["break_before"] = page_break
        if section_break != defaults["section_break_before"]:
            page_blk["section_break_before"] = section_break
        if page_blk:
            novo_beh["page"] = page_blk
        num_blk = {}
        if num_scheme != defaults["num_scheme"]:
            num_blk["scheme"] = num_scheme
        if num_visible != defaults["num_visible"]:
            num_blk["visible"] = num_visible
        if num_restart != defaults["num_restart"]:
            num_blk["restart"] = num_restart
        if num_blk:
            novo_beh["numbering"] = num_blk

        if novo_beh:
            el["behavior"] = novo_beh
        else:
            el.pop("behavior", None)


def _renderizar_elemento(el: dict, profundidade: int, prefixo: str,
                          tipos: list, elementos_raiz: list, idx_pai_path: str) -> None:
    """Renderiza recursivamente um elemento e os seus filhos."""
    margem = "　" * profundidade
    rotulo_tipo = el.get("semantic_type", "section")
    slug_disp = el.get("slug") or "—"

    with st.expander(f"{margem}**{slug_disp}** · *{rotulo_tipo}*", expanded=False):
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 1, 1, 1])
        c1.caption("Slug ⚠️"); c2.caption("Título"); c3.caption("Tipo")
        c4.caption("Nível"); c5.caption("Ordem"); c6.caption("Inc.")

        _renderizar_formulario_elemento(el, prefixo, tipos, elementos_raiz)

        col_filho, col_rem, _ = st.columns([2, 2, 6])
        if col_filho.button("➕ Filho", key=f"{prefixo}_add_filho"):
            filhos = el.setdefault("filhos", [])
            novo_slug = auto_slug(elementos_raiz)
            filhos.append(elemento_vazio(novo_slug))
            st.rerun()

        if get_confirmar_remover() == prefixo:
            st.warning("Confirmar remoção deste elemento?")
            col_sim, col_nao, _ = st.columns([1, 1, 8])
            if col_sim.button("Sim", key=f"{prefixo}_rem_sim"):
                set_confirmar_remover(None)
                el["_remover"] = True
                st.rerun()
            if col_nao.button("Não", key=f"{prefixo}_rem_nao"):
                set_confirmar_remover(None)
                st.rerun()
        else:
            if col_rem.button("🗑 Remover", key=f"{prefixo}_rem"):
                set_confirmar_remover(prefixo)
                st.rerun()

        filhos = el.get("filhos") or []
        if filhos:
            st.divider()
            _renderizar_lista_elementos(filhos, profundidade + 1, prefixo, tipos, elementos_raiz)
        if filhos:
            el["filhos"] = [f for f in filhos if not f.get("_remover")]


def _renderizar_lista_elementos(lista: list, profundidade: int, prefixo_base: str,
                                 tipos: list, elementos_raiz: list) -> None:
    """Itera a lista e renderiza cada elemento."""
    for i, el in enumerate(lista):
        if not isinstance(el, dict):
            continue
        _renderizar_elemento(el, profundidade, f"{prefixo_base}_{i}",
                             tipos, elementos_raiz, prefixo_base)


def render_tab_estrutura() -> None:
    """Renderiza o tab Editor de Estrutura (Camada 1)."""
    st.header("Editor de Estrutura")
    raw = get_estrutura_raw()
    if not raw:
        st.info("Importe o ficheiro estrutura.yaml na sidebar para começar a editar.")
        return

    st.caption(f"A editar: {get_estrutura_path() or 'ficheiro importado'}")
    st.divider()

    with st.expander("Metadados do documento", expanded=False):
        col_dt, col_tit_doc = st.columns([2, 5])
        raw["doc_type"] = col_dt.text_input("doc_type", value=raw.get("doc_type", ""), key="c1_doc_type")
        raw["doc_title"] = col_tit_doc.text_input("doc_title", value=raw.get("doc_title", ""), key="c1_doc_title")
    st.divider()

    st.subheader("Tipos semânticos")
    st.caption("Tipos fixos definidos pelo sistema. Para cada elemento escolhe o tipo no editor abaixo.")
    dados_tipos = [{"Tipo": t, "Papel no documento": infer_section_role(t)} for t in SEMANTIC_TYPES]
    st.dataframe(dados_tipos, width="stretch", hide_index=True)
    tipos = obter_tipos(raw)
    st.divider()

    st.subheader("Elementos")
    elementos_raw: list = raw.setdefault("elementos", [])
    ch1, ch2, ch3, ch4, ch5, ch6 = st.columns([2, 3, 2, 1, 1, 1])
    ch1.caption("Slug"); ch2.caption("Título"); ch3.caption("Tipo semântico")
    ch4.caption("Nível"); ch5.caption("Ordem"); ch6.caption("Inc.")

    _renderizar_lista_elementos(elementos_raw, 0, "c1_el", tipos, elementos_raw)
    raw["elementos"] = [el for el in elementos_raw if not el.get("_remover")]

    if st.button("➕ Novo elemento", key="c1_btn_novo_el"):
        novo_slug = auto_slug(raw["elementos"])
        raw["elementos"].append(elemento_vazio(novo_slug))
        st.rerun()
    st.divider()

    erros = validar_elementos(raw.get("elementos", []))
    if erros:
        for msg_erro in erros:
            st.error(msg_erro)

    if st.button("💾 Guardar estrutura", key="c1_btn_guardar",
                 disabled=bool(erros), width="stretch"):
        path_guardar = get_export_path_estrutura().strip()
        if not path_guardar:
            st.error("Defina o path de exportação na sidebar antes de guardar.")
        else:
            ok, msg = guardar_estrutura_yaml(path_guardar, raw)
            st.success(msg) if ok else st.error(msg)
