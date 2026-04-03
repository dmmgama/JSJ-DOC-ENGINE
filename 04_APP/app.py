"""
app.py — JSJ-DOC-ENGINE — Camada 3
TOC interactivo, export/import de estrutura.yaml e mapeamento.yaml.
"""

import copy
import os
from pathlib import Path

import streamlit as st
import yaml

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="JSJ-DOC-ENGINE",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Dados mock — representam um CTE típico
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
# Inicialização do estado da sessão
# ---------------------------------------------------------------------------
def inicializar_estado() -> None:
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


# ---------------------------------------------------------------------------
# Funções utilitárias — numeração
# ---------------------------------------------------------------------------
def calcular_numeracao(elementos: list) -> list:
    """Recalcula a numeração de todos os elementos.

    Elementos com incluir=True recebem número sequencial (1, 2, 3...).
    Elementos com incluir=False ficam com '—'.
    Devolve nova lista com campo 'ordem_display' adicionado.
    """
    resultado = []
    contador = 1
    for el in elementos:
        el_copia = dict(el)
        if el_copia["incluir"]:
            el_copia["ordem_display"] = str(contador)
            contador += 1
        else:
            el_copia["ordem_display"] = "—"
        resultado.append(el_copia)
    return resultado


# ---------------------------------------------------------------------------
# Funções de reordenação
# ---------------------------------------------------------------------------
def mover_elemento_cima(idx: int) -> None:
    """Troca o elemento na posição idx com o elemento anterior."""
    if idx <= 0:
        return
    els = st.session_state.elementos
    els[idx], els[idx - 1] = els[idx - 1], els[idx]
    # Actualizar campo ordem para reflectir nova posição na lista
    for i, el in enumerate(els):
        el["ordem"] = i + 1


def mover_elemento_baixo(idx: int) -> None:
    """Troca o elemento na posição idx com o elemento seguinte."""
    els = st.session_state.elementos
    if idx >= len(els) - 1:
        return
    els[idx], els[idx + 1] = els[idx + 1], els[idx]
    for i, el in enumerate(els):
        el["ordem"] = i + 1


# ---------------------------------------------------------------------------
# Funções de export — geração de conteúdo
# ---------------------------------------------------------------------------
def gerar_estrutura_yaml(elementos: list, projecto: dict) -> str:
    """Serializa o estado actual da estrutura para YAML.

    Todos os elementos são exportados (incluindo incluir=False).
    """
    elementos_yaml = []
    for el in elementos:
        item = {
            "slug":    el["slug"],
            "titulo":  el["titulo"],
            "tipo":    el.get("tipo", "heading"),
            "include": el["incluir"],
            "ordem":   el["ordem"],
        }
        # Adicionar campos opcionais apenas se presentes
        if el.get("nivel"):
            item["nivel"] = el["nivel"]
        if el.get("pai"):
            item["pai"] = el["pai"]
        elementos_yaml.append(item)

    dados = {
        "doc_type":  projecto.get("doc_type", "CTE"),
        "doc_title": projecto.get("name", ""),
        "elementos": elementos_yaml,
    }
    return yaml.dump(dados, allow_unicode=True, default_flow_style=False, sort_keys=False)


def gerar_mapeamento_yaml(elementos: list, projecto: dict) -> str:
    """Serializa o mapeamento para YAML.

    Inclui apenas elementos com incluir=True.
    Os campos md_source e template_docx ficam como placeholders.
    """
    dados = {
        "doc_id":        projecto.get("id", ""),
        "estrutura_ref": "estrutura.yaml",
        "templates": {
            "geral": "",
        },
        "elementos": [
            {
                "slug":          el["slug"],
                "md_source":     "",
                "md_scope":      "ficheiro_inteiro",
                "template_docx": "default",
            }
            for el in elementos
            if el.get("incluir")
        ],
    }
    return yaml.dump(dados, allow_unicode=True, default_flow_style=False, sort_keys=False)


def exportar_ficheiro(conteudo: str, caminho: str) -> tuple:
    """Escreve conteudo para o caminho especificado.

    Devolve (sucesso: bool, mensagem: str).
    """
    try:
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return True, f"Ficheiro exportado: {caminho}"
    except Exception as exc:
        return False, f"Erro ao exportar: {exc}"


# ---------------------------------------------------------------------------
# Funções de import — parse YAML
# ---------------------------------------------------------------------------
def _aplanar_elementos(elementos_yaml: list, pai: str | None, contador: list) -> list:
    """Recursivamente aplana a hierarquia de filhos numa lista plana.

    Preserva pai, tipo e nivel para re-exportação correcta.
    """
    resultado = []
    for el in elementos_yaml:
        if not isinstance(el, dict):
            continue
        tipo = el.get("tipo", "heading")
        nivel_raw = el.get("nivel")  # int (1, 2) ou None
        # Mapear tipo+nivel para string interna de nível
        if tipo == "seccao":
            nivel_str = "seccao"
        elif tipo == "anexo":
            nivel_str = "ANX"
        elif tipo in ("front_matter", "toc"):
            nivel_str = tipo
        else:
            nivel_str = f"H{nivel_raw}" if nivel_raw else "H1"

        item = {
            "slug":    el.get("slug", ""),
            "titulo":  el.get("titulo", ""),
            "tipo":    tipo,
            "nivel":   nivel_str,
            "pai":     pai,
            "incluir": bool(el.get("include", True)),
            "ordem":   contador[0],
        }
        contador[0] += 1
        resultado.append(item)

        # Recursão para elementos filhos
        filhos = el.get("filhos") or []
        if filhos:
            resultado.extend(
                _aplanar_elementos(filhos, el.get("slug"), contador)
            )
    return resultado


def parse_estrutura_yaml(conteudo: str) -> list:
    """Faz parse de estrutura.yaml e devolve lista plana de elementos.

    Usa yaml.safe_load() — sem parser custom.
    A hierarquia de filhos é aplanada preservando o campo pai.
    """
    try:
        dados = yaml.safe_load(conteudo) or {}
    except yaml.YAMLError:
        return []

    elementos_yaml = dados.get("elementos", [])
    if not isinstance(elementos_yaml, list):
        return []

    contador = [1]
    elementos = _aplanar_elementos(elementos_yaml, None, contador)
    # Filtrar elementos sem slug (mínimo necessário para existir)
    return [el for el in elementos if el.get("slug")]


def parse_mapeamento_yaml(conteudo: str) -> dict:
    """Faz parse de mapeamento.yaml e devolve dict com meta, elementos e templates.

    Usa yaml.safe_load() — sem parser custom.
    """
    try:
        dados = yaml.safe_load(conteudo) or {}
    except yaml.YAMLError:
        return {"meta": {}, "elementos": [], "templates": {}}

    return {
        "meta": {
            "doc_id":        dados.get("doc_id", ""),
            "estrutura_ref": dados.get("estrutura_ref", ""),
        },
        "elementos":  dados.get("elementos") or [],
        "templates":  dados.get("templates") or {},
    }


# ---------------------------------------------------------------------------
# Leitura de paths a partir do config.yaml (schema novo — campos opcionais)
# ---------------------------------------------------------------------------
def ler_paths_config() -> dict:
    """Tenta ler paths de estrutura e mapeamento do config.yaml.

    Devolve dict com chaves 'estrutura' e 'mapeamento' (strings vazias se ausentes).
    """
    config_path = Path(__file__).parent / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        # Suporte a schema novo (campo projecto_activo) e schema antigo
        proj = cfg.get("projecto_activo", cfg)
        return {
            "estrutura":  proj.get("estrutura", ""),
            "mapeamento": proj.get("mapeamento", ""),
        }
    except Exception:
        return {"estrutura": "", "mapeamento": ""}


# ---------------------------------------------------------------------------
# Limpar chaves de checkbox do session_state (usado antes de import)
# ---------------------------------------------------------------------------
def limpar_chaves_checkboxes(elementos: list) -> None:
    """Remove do session_state as chaves de checkbox dos elementos dados."""
    for el in elementos:
        key = f"chk_{el['slug']}"
        if key in st.session_state:
            del st.session_state[key]


# ===========================================================================
# LAYOUT PRINCIPAL
# ===========================================================================
inicializar_estado()
paths_cfg = ler_paths_config()

# ---------------------------------------------------------------------------
# Sidebar — informação do projecto + import/export
# ---------------------------------------------------------------------------
with st.sidebar:
    proj = st.session_state.projecto_activo
    st.title("JSJ-DOC-ENGINE")
    st.markdown(f"**Projecto:** {proj['name']}")
    st.markdown(f"**ID:** `{proj['id']}`")
    st.divider()

    # ── estrutura.yaml ───────────────────────────────────────────────────────
    st.subheader("estrutura.yaml")

    export_path_est = st.text_input(
        "Path de exportação",
        value=st.session_state.export_path_estrutura or paths_cfg.get("estrutura", ""),
        key="input_path_estrutura",
        placeholder=r"C:\caminho\para\estrutura.yaml",
    )
    # Persistir o path entre reruns
    st.session_state.export_path_estrutura = export_path_est

    if st.button("Exportar estrutura.yaml", use_container_width=True):
        if not export_path_est.strip():
            st.error("Defina o path de exportação antes de exportar.")
        else:
            conteudo = gerar_estrutura_yaml(
                st.session_state.elementos,
                st.session_state.projecto_activo,
            )
            ok, msg = exportar_ficheiro(conteudo, export_path_est.strip())
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    ficheiro_est = st.file_uploader(
        "Importar estrutura.yaml",
        type=["yaml", "yml"],
        key="uploader_estrutura",
    )
    if ficheiro_est is not None:
        conteudo_est = ficheiro_est.read().decode("utf-8")
        novos_elementos = parse_estrutura_yaml(conteudo_est)
        if novos_elementos:
            limpar_chaves_checkboxes(st.session_state.elementos)
            st.session_state.elementos = novos_elementos
            st.success(f"Importados {len(novos_elementos)} elementos.")
            st.rerun()
        else:
            st.warning("Nenhum elemento encontrado no ficheiro importado.")

    st.divider()

    # ── mapeamento.yaml ──────────────────────────────────────────────────────
    st.subheader("mapeamento.yaml")

    export_path_map = st.text_input(
        "Path de exportação",
        value=st.session_state.export_path_mapeamento or paths_cfg.get("mapeamento", ""),
        key="input_path_mapeamento",
        placeholder=r"C:\caminho\para\mapeamento.yaml",
    )
    st.session_state.export_path_mapeamento = export_path_map

    if st.button("Exportar mapeamento.yaml", use_container_width=True):
        if not export_path_map.strip():
            st.error("Defina o path de exportação antes de exportar.")
        else:
            conteudo = gerar_mapeamento_yaml(
                st.session_state.elementos,
                st.session_state.projecto_activo,
            )
            ok, msg = exportar_ficheiro(conteudo, export_path_map.strip())
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    ficheiro_map = st.file_uploader(
        "Importar mapeamento.yaml",
        type=["yaml", "yml"],
        key="uploader_mapeamento",
    )
    if ficheiro_map is not None:
        conteudo_map = ficheiro_map.read().decode("utf-8")
        mapeamento_importado = parse_mapeamento_yaml(conteudo_map)
        st.session_state.mapeamento = mapeamento_importado
        n_el = len(mapeamento_importado.get("elementos", []))
        st.success(f"Mapeamento importado: {n_el} elementos.")

# ---------------------------------------------------------------------------
# Main — TOC interactivo
# ---------------------------------------------------------------------------
st.header("TOC — Estrutura do Documento")

elementos_com_num = calcular_numeracao(st.session_state.elementos)
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

    # Número ou travessão
    col_ord.markdown(el["ordem_display"])

    # Slug em código
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

# ---------------------------------------------------------------------------
# Footer — botão Compilar DOCX (stub desactivado)
# ---------------------------------------------------------------------------
st.divider()
st.button(
    "Compilar DOCX",
    disabled=True,
    use_container_width=True,
    help="Disponível após configurar mapeamento (Camada 2)",
)
