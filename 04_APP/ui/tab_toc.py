"""
ui/tab_toc.py — Tab TOC Interactivo (Camada 3).

TOC hierárquico, preview numeração, toggle N/A, reordenação, compilação.
Expor: render_tab_toc()
"""
import streamlit as st

from core.services import calcular_numeracao
from ui.state import get_elementos


# ---------------------------------------------------------------------------
# Funções de reordenação
# ---------------------------------------------------------------------------
def _mover_elemento_cima(idx: int) -> None:
    """Troca o elemento na posição idx com o elemento anterior."""
    if idx <= 0:
        return
    els = get_elementos()
    els[idx], els[idx - 1] = els[idx - 1], els[idx]
    for i, el in enumerate(els):
        el["ordem"] = i + 1


def _mover_elemento_baixo(idx: int) -> None:
    """Troca o elemento na posição idx com o elemento seguinte."""
    els = get_elementos()
    if idx >= len(els) - 1:
        return
    els[idx], els[idx + 1] = els[idx + 1], els[idx]
    for i, el in enumerate(els):
        el["ordem"] = i + 1


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------
def render_tab_toc() -> None:
    """Renderiza o tab TOC / Compilar."""
    st.header("TOC — Estrutura do Documento")

    elementos_com_num = calcular_numeracao(get_elementos())
    n_total = len(elementos_com_num)

    # Cabeçalho da tabela
    col_h_ord, col_h_slug, col_h_tit, col_h_na, col_h_up, col_h_dn = st.columns(
        [1, 2, 7, 1, 1, 1]
    )
    col_h_ord.markdown("**#**")
    col_h_slug.markdown("**Slug**")
    col_h_tit.markdown("**Título**")
    col_h_na.markdown("**N/A**")
    col_h_up.markdown("**↑**")
    col_h_dn.markdown("**↓**")
    st.divider()

    # Linhas do TOC
    for idx, el in enumerate(elementos_com_num):
        col_ord, col_slug, col_tit, col_na, col_up, col_dn = st.columns(
            [1, 2, 7, 1, 1, 1]
        )

        col_ord.markdown(el["ordem_display"])
        col_slug.markdown(f"`{el['slug']}`")

        # Título — riscado se não incluído
        if el["incluir"]:
            col_tit.markdown(el["titulo"])
        else:
            col_tit.markdown(f"~~{el['titulo']}~~")

        # Checkbox incluir — toggle N/A
        novo_valor = col_na.checkbox(
            label="incluir",
            value=el["incluir"],
            key=f"chk_{el['slug']}",
            label_visibility="collapsed",
        )
        if novo_valor != el["incluir"]:
            get_elementos()[idx]["incluir"] = novo_valor
            st.rerun()

        # Botão mover para cima
        if col_up.button("↑", key=f"up_{el['slug']}", disabled=(idx == 0)):
            _mover_elemento_cima(idx)
            st.rerun()

        # Botão mover para baixo
        if col_dn.button("↓", key=f"dn_{el['slug']}", disabled=(idx == n_total - 1)):
            _mover_elemento_baixo(idx)
            st.rerun()

    # Footer — botão Compilar DOCX (stub desactivado)
    st.divider()
    st.button(
        "Compilar DOCX",
        disabled=True,
        width="stretch",
        help="Disponível após configurar mapeamento (Camada 2)",
    )
