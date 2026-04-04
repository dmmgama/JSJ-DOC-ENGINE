"""
ui/state.py — Gestão centralizada de session_state.

ÚNICO módulo que acede directamente a st.session_state.
Todos os outros módulos ui/ usam os helpers daqui.
"""
import copy

import streamlit as st


# ---------------------------------------------------------------------------
# Dados mock — defaults quando não há projecto carregado
# ---------------------------------------------------------------------------
ELEMENTOS_MOCK = [
    {"slug": "LEX",      "titulo": "Léxico e Enquadramento Contratual", "nivel": "H1", "pai": "SEC-I",  "incluir": True,  "ordem": 1},
    {"slug": "GERAL",    "titulo": "Disposições Gerais",                 "nivel": "H1", "pai": "SEC-I",  "incluir": True,  "ordem": 2},
    {"slug": "MAT",      "titulo": "Materiais",                          "nivel": "H1", "pai": "SEC-II", "incluir": True,  "ordem": 3},
    {"slug": "EXEC",     "titulo": "Execução de Trabalhos",              "nivel": "H1", "pai": "SEC-II", "incluir": True,  "ordem": 4},
    {"slug": "DIAG",     "titulo": "Diagnóstico",                        "nivel": "H1", "pai": "SEC-II", "incluir": False, "ordem": 5},
    {"slug": "ANX-GLOS", "titulo": "Glossário Técnico",                  "nivel": "ANX","pai": None,     "incluir": True,  "ordem": 6},
]

PROJECTO_MOCK = {
    "id":       "CTE-SecI",
    "name":     "CTE Fundações e Estruturas",
    "doc_type": "CTE",
}


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------
def init_state() -> None:
    """Garante que todas as chaves de session_state existem."""
    if "elementos" not in st.session_state:
        st.session_state.elementos = copy.deepcopy(ELEMENTOS_MOCK)
    if "mapeamento" not in st.session_state:
        st.session_state.mapeamento = {}
    if "projecto_activo" not in st.session_state:
        st.session_state.projecto_activo = PROJECTO_MOCK.copy()
    if "export_path_estrutura" not in st.session_state:
        st.session_state.export_path_estrutura = ""
    if "export_path_mapeamento" not in st.session_state:
        st.session_state.export_path_mapeamento = ""
    if "estrutura_yaml_raw" not in st.session_state:
        st.session_state.estrutura_yaml_raw = {}
    if "estrutura_yaml_path" not in st.session_state:
        st.session_state.estrutura_yaml_path = ""
    if "confirmar_remover" not in st.session_state:
        st.session_state.confirmar_remover = None
    if "projecto_carregado" not in st.session_state:
        st.session_state.projecto_carregado = False
    if "mapeamento_yaml_path" not in st.session_state:
        st.session_state.mapeamento_yaml_path = ""
    if "confirmar_apagar_proj" not in st.session_state:
        st.session_state.confirmar_apagar_proj = False


# ---------------------------------------------------------------------------
# Limpeza de state
# ---------------------------------------------------------------------------
def clear_project_state() -> None:
    """Limpa state relacionado com o projecto activo (map_*, chk_*, paths)."""
    st.session_state.estrutura_yaml_raw = {}
    st.session_state.estrutura_yaml_path = ""
    st.session_state.mapeamento = {}
    st.session_state.mapeamento_yaml_path = ""
    st.session_state.projecto_carregado = False
    # Limpar widget keys dinâmicas da Camada 2 e checkboxes do TOC
    keys_to_del = [k for k in st.session_state
                   if k.startswith("map_") or k.startswith("chk_")]
    for k in keys_to_del:
        del st.session_state[k]


def clear_checkboxes(elementos: list) -> None:
    """Remove do session_state as chaves de checkbox dos elementos dados."""
    for el in elementos:
        key = f"chk_{el['slug']}"
        if key in st.session_state:
            del st.session_state[key]


def clear_map_keys(elementos: list) -> None:
    """Remove widget keys da Camada 2 para forçar reinicialização."""
    for el in elementos:
        slug = el.get("slug", "")
        for sufixo in ("_md_source", "_md_scope", "_template", "_nota"):
            key = f"map_{slug}{sufixo}"
            if key in st.session_state:
                del st.session_state[key]


# ---------------------------------------------------------------------------
# Getters / Setters — elementos
# ---------------------------------------------------------------------------
def get_elementos() -> list:
    return st.session_state.get("elementos", [])


def set_elementos(elementos: list) -> None:
    st.session_state.elementos = elementos


# ---------------------------------------------------------------------------
# Getters / Setters — projecto activo
# ---------------------------------------------------------------------------
def get_projecto_activo() -> dict:
    return st.session_state.get("projecto_activo", {})


def set_projecto_activo(proj: dict) -> None:
    st.session_state.projecto_activo = proj


# ---------------------------------------------------------------------------
# Getters / Setters — estrutura YAML raw
# ---------------------------------------------------------------------------
def get_estrutura_raw() -> dict:
    return st.session_state.get("estrutura_yaml_raw", {})


def set_estrutura_raw(raw: dict) -> None:
    st.session_state.estrutura_yaml_raw = raw


def get_estrutura_path() -> str:
    return st.session_state.get("estrutura_yaml_path", "")


def set_estrutura_path(path: str) -> None:
    st.session_state.estrutura_yaml_path = path


# ---------------------------------------------------------------------------
# Getters / Setters — mapeamento
# ---------------------------------------------------------------------------
def get_mapeamento() -> dict:
    return st.session_state.get("mapeamento", {})


def set_mapeamento(mapeamento: dict) -> None:
    st.session_state.mapeamento = mapeamento


def get_mapeamento_path() -> str:
    return st.session_state.get("mapeamento_yaml_path", "")


def set_mapeamento_path(path: str) -> None:
    st.session_state.mapeamento_yaml_path = path


# ---------------------------------------------------------------------------
# Getters / Setters — export paths
# ---------------------------------------------------------------------------
def get_export_path_estrutura() -> str:
    return st.session_state.get("export_path_estrutura", "")


def set_export_path_estrutura(path: str) -> None:
    st.session_state.export_path_estrutura = path


def get_export_path_mapeamento() -> str:
    return st.session_state.get("export_path_mapeamento", "")


def set_export_path_mapeamento(path: str) -> None:
    st.session_state.export_path_mapeamento = path


# ---------------------------------------------------------------------------
# Getters / Setters — flags
# ---------------------------------------------------------------------------
def get_projecto_carregado() -> bool:
    return st.session_state.get("projecto_carregado", False)


def set_projecto_carregado(valor: bool) -> None:
    st.session_state.projecto_carregado = valor


def get_confirmar_remover():
    return st.session_state.get("confirmar_remover")


def set_confirmar_remover(valor) -> None:
    st.session_state.confirmar_remover = valor


def get_confirmar_apagar_proj() -> bool:
    return st.session_state.get("confirmar_apagar_proj", False)


def set_confirmar_apagar_proj(valor: bool) -> None:
    st.session_state.confirmar_apagar_proj = valor
