"""
ui/tab_mapeamento.py — Tab Mapeamento (Camada 2).

Editor de MD sources e templates DOCX por elemento.
Expor: render_tab_mapeamento()
"""
import datetime
from pathlib import Path

import streamlit as st
import yaml

from core.services import obter_elementos_flat, mapeamento_por_slug
from adapters.config import carregar_config
from ui.state import (
    get_estrutura_raw,
    get_mapeamento,
    get_mapeamento_path,
    get_projecto_activo,
    set_mapeamento,
    set_mapeamento_path,
)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MD_SCOPE_OPCOES = ["ficheiro_inteiro", "heading_especifico"]


# ---------------------------------------------------------------------------
# Renderização do editor de mapeamento
# ---------------------------------------------------------------------------
def _renderizar_camada2(elementos_flat: list, map_actual: dict) -> None:
    """Renderiza o editor de mapeamento: uma linha por elemento."""
    novo_mapeamento_elementos = []

    for el in elementos_flat:
        slug = el["slug"]
        titulo = el["titulo"]
        semantic_type = el["semantic_type"]
        prof = el["profundidade"]

        # Indentação visual por profundidade
        margem = "\u3000" * prof

        # Valores do mapeamento carregado
        map_el = map_actual.get(slug, {})

        # Inicializar widget keys no session_state SE ainda não existirem
        key_md = f"map_{slug}_md_source"
        key_sc = f"map_{slug}_md_scope"
        key_tpl = f"map_{slug}_template"
        key_nota = f"map_{slug}_nota"

        if key_md not in st.session_state:
            st.session_state[key_md] = map_el.get("md_source", "")
        if key_sc not in st.session_state:
            scope_val = map_el.get("md_scope", "ficheiro_inteiro")
            st.session_state[key_sc] = scope_val if scope_val in MD_SCOPE_OPCOES else MD_SCOPE_OPCOES[0]
        if key_tpl not in st.session_state:
            st.session_state[key_tpl] = map_el.get("template_docx", "default")
        if key_nota not in st.session_state:
            st.session_state[key_nota] = map_el.get("nota", "")

        with st.expander(
            f"{margem}**{slug}** · *{semantic_type}* — {titulo}",
            expanded=(st.session_state[key_md] == ""),
        ):
            col1, col2 = st.columns([3, 1])

            md_source = col1.text_input(
                "Ficheiro MD (path absoluto)",
                key=key_md,
                placeholder=r"C:\caminho\para\ficheiro.md",
            )

            md_scope = col2.selectbox(
                "Scope",
                MD_SCOPE_OPCOES,
                key=key_sc,
            )

            col3, col4 = st.columns([3, 1])

            template_docx = col3.text_input(
                "Template DOCX (deixar 'default' para usar o geral)",
                key=key_tpl,
            )

            nota = col4.text_input(
                "Nota",
                key=key_nota,
            )

            # Validação: avisar se md_source não existe no disco
            if md_source and not Path(md_source).exists():
                st.warning(f"⚠️ Ficheiro não encontrado: {md_source}")
            elif md_source:
                st.success("✅ Ficheiro encontrado")

        novo_mapeamento_elementos.append({
            "slug":          slug,
            "md_source":     md_source,
            "md_scope":      md_scope,
            "template_docx": template_docx,
            "nota":          nota,
        })

    # Guardar em session_state continuamente
    mapeamento = get_mapeamento()
    if not mapeamento:
        mapeamento = {}
    mapeamento["elementos"] = novo_mapeamento_elementos
    set_mapeamento(mapeamento)

    st.divider()

    # ── Botão guardar mapeamento.yaml ────────────────────────────────
    path_map = get_mapeamento_path()
    col_path, col_btn = st.columns([4, 1])
    path_export = col_path.text_input(
        "Path de exportação",
        value=path_map,
        key="map_export_path",
        placeholder=r"C:\caminho\para\mapeamento.yaml",
    )
    if col_btn.button("💾 Guardar mapeamento.yaml", width="stretch", key="map_btn_guardar"):
        if not path_export.strip():
            st.error("Indica o path de exportação.")
        else:
            try:
                defaults_cfg = carregar_config().get("defaults", {})
                proj_activo = get_projecto_activo()
                ref_doc = (
                    proj_activo.get("reference_doc")
                    or defaults_cfg.get("reference_doc", "")
                )
                dados_export = {
                    "doc_id":        proj_activo.get("id", ""),
                    "doc_title":     proj_activo.get("name", ""),
                    "estrutura_ref": "estrutura.yaml",
                    "data":          str(datetime.date.today()),
                    "templates": {
                        "geral": ref_doc,
                    },
                    "elementos": novo_mapeamento_elementos,
                }
                with open(path_export.strip(), "w", encoding="utf-8") as f:
                    yaml.dump(dados_export, f, allow_unicode=True,
                              default_flow_style=False, sort_keys=False)
                set_mapeamento_path(path_export.strip())
                st.success(f"✅ Guardado em: {path_export.strip()}")
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------
def render_tab_mapeamento() -> None:
    """Renderiza o tab Mapeamento de Conteúdo (Camada 2)."""
    st.header("Mapeamento de Conteúdo")

    # Verificar pré-condições
    if not get_estrutura_raw():
        st.info("Carregue um projecto ou importe estrutura.yaml para começar.")
        st.stop()

    # Obter lista plana de elementos incluídos (include=True), recursivamente
    elementos_flat = obter_elementos_flat(
        get_estrutura_raw().get("elementos", [])
    )

    if not elementos_flat:
        st.warning("Nenhum elemento com include=True encontrado na estrutura.")
        st.stop()

    # Obter mapeamento actual indexado por slug
    map_actual = mapeamento_por_slug(get_mapeamento())

    # Renderizar editor de mapeamento
    _renderizar_camada2(elementos_flat, map_actual)
