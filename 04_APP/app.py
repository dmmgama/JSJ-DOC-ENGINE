"""
app.py — JSJ-DOC-ENGINE
Ponto de entrada Streamlit — apenas configuração e routing.
"""
import streamlit as st

from ui.state import init_state
from ui.sidebar import render_sidebar
from ui.tab_toc import render_tab_toc
from ui.tab_estrutura import render_tab_estrutura
from ui.tab_mapeamento import render_tab_mapeamento
from adapters.config import carregar_config, ler_paths_config

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="JSJ-DOC-ENGINE", layout="wide")

# Inicializar estado
init_state()

# Carregar configuração
config = carregar_config()
paths_cfg = ler_paths_config()

# Sidebar (inclui auto-load do projecto no arranque)
render_sidebar(config, paths_cfg)

# ---------------------------------------------------------------------------
# Tabs principais
# ---------------------------------------------------------------------------
tab_toc, tab_est, tab_map = st.tabs([
    "TOC / Compilar",
    "Estrutura",
    "Mapeamento",
])

with tab_toc:
    render_tab_toc()

with tab_est:
    render_tab_estrutura()

with tab_map:
    render_tab_mapeamento()
