"""
app.py — JSJ-DOC-ENGINE — Camadas 1 e 3
Camada 1: Editor de Estrutura do Documento
Camada 3: TOC interactivo, export/import de estrutura.yaml e mapeamento.yaml.
"""

import copy
import os
import re
from pathlib import Path

import streamlit as st
import yaml

from semantic_type_registry import (
    SEMANTIC_TYPES,
    TIPO_V1_TO_SEMANTIC_TYPE,
    get_defaults,
    infer_section_role,
    resolve_behavior,
)

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
    # Camada 1 — estrutura YAML completa (dict raw) do projecto activo
    if "estrutura_yaml_raw" not in st.session_state:
        st.session_state.estrutura_yaml_raw = {}
    # Camada 1 — path do estrutura.yaml carregado
    if "estrutura_yaml_path" not in st.session_state:
        st.session_state.estrutura_yaml_path = ""
    # Camada 1 — flag para confirmar remoção de elemento
    if "confirmar_remover" not in st.session_state:
        st.session_state.confirmar_remover = None
    # Multi-projecto — flag de projecto já carregado nesta sessão
    if "projecto_carregado" not in st.session_state:
        st.session_state.projecto_carregado = False
    # Multi-projecto — path do mapeamento.yaml carregado
    if "mapeamento_yaml_path" not in st.session_state:
        st.session_state.mapeamento_yaml_path = ""
    # Confirmação de apagar projecto (dois passos)
    if "confirmar_apagar_proj" not in st.session_state:
        st.session_state.confirmar_apagar_proj = False


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
            "slug":          el["slug"],
            "titulo":        el["titulo"],
            "semantic_type": el.get("semantic_type", "section"),
            "include":       el["incluir"],
            "ordem":         el["ordem"],
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
        # Compatibilidade retroactiva: converter tipo v1 → semantic_type v2
        if "tipo" in el and "semantic_type" not in el:
            el["semantic_type"] = TIPO_V1_TO_SEMANTIC_TYPE.get(el["tipo"], "section")
            del el["tipo"]

        tipo = el.get("tipo")  # None se já convertido (v1 → v2)
        nivel_raw = el.get("nivel")  # int (1, 2) ou None
        # Mapear tipo+nivel para string interna de nível (compatibilidade v1)
        if tipo == "seccao":
            nivel_str = "seccao"
        elif tipo == "anexo":
            nivel_str = "ANX"
        elif tipo in ("front_matter", "toc"):
            nivel_str = tipo
        else:
            nivel_str = f"H{nivel_raw}" if nivel_raw else "H1"

        item = {
            "slug":          el.get("slug", ""),
            "titulo":        el.get("titulo", ""),
            "semantic_type": el.get("semantic_type", "section"),
            "nivel":         nivel_str,
            "pai":           pai,
            "incluir":       bool(el.get("include", True)),
            "ordem":         contador[0],
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
# CAMADA 1 — EDITOR DE ESTRUTURA: funções auxiliares
# ===========================================================================

def _obter_tipos(raw: dict) -> list:
    """Tipos semânticos disponíveis — sempre do registry, nunca do YAML."""
    return list(SEMANTIC_TYPES)


def _todos_slugs(elementos: list) -> list:
    """Recolhe recursivamente todos os slugs presentes na lista de elementos."""
    slugs = []
    for el in elementos:
        if isinstance(el, dict):
            s = el.get("slug", "")
            if s:
                slugs.append(s)
            filhos = el.get("filhos") or []
            if filhos:
                slugs.extend(_todos_slugs(filhos))
    return slugs


def _auto_slug(elementos: list) -> str:
    """Gera um slug único no formato elem-NNN."""
    slugs_existentes = set(_todos_slugs(elementos))
    i = 1
    while True:
        candidato = f"elem-{i:03d}"
        if candidato not in slugs_existentes:
            return candidato
        i += 1


def _elemento_vazio(slug: str) -> dict:
    """Cria um elemento novo com valores por defeito."""
    return {
        "slug":          slug,
        "titulo":        "",
        "semantic_type": "section",   # era "tipo": "heading"
        "nivel":         1,
        "display_order": 0,
        "include":       True,
        "filhos":        [],
    }


def _validar_elementos(elementos: list) -> list:
    """Valida slugs únicos e títulos não vazios. Devolve lista de mensagens de erro."""
    erros = []
    slugs = _todos_slugs(elementos)
    vistos = set()
    duplicados = set()
    for s in slugs:
        if s in vistos:
            duplicados.add(s)
        vistos.add(s)
    for slug in duplicados:
        erros.append(f"Slug duplicado: **{slug}**")

    def _verificar_titulos(lista: list) -> None:
        for el in lista:
            if not isinstance(el, dict):
                continue
            if not el.get("titulo", "").strip():
                erros.append(f"Título vazio no elemento `{el.get('slug', '?')}`")
            filhos = el.get("filhos") or []
            if filhos:
                _verificar_titulos(filhos)

    _verificar_titulos(elementos)
    return erros


def _renderizar_formulario_elemento(el: dict, prefixo: str, tipos: list, elementos_raiz: list) -> None:
    """Renderiza o formulário inline de um elemento (edit in place).

    Modifica el directamente via st widgets com chaves únicas por prefixo.
    """
    col_slug, col_titulo, col_tipo, col_nivel, col_ord, col_inc = st.columns(
        [2, 3, 2, 1, 1, 1]
    )

    # ── slug ──────────────────────────────────────────────────────────────
    novo_slug = col_slug.text_input(
        "Slug",
        value=el.get("slug", ""),
        key=f"{prefixo}_slug",
        help="⚠️ Imutável após criação — alterar aqui requer actualizar mapeamento.yaml",
        label_visibility="collapsed",
    )
    el["slug"] = novo_slug.strip()

    # ── titulo ────────────────────────────────────────────────────────────
    novo_titulo = col_titulo.text_input(
        "Título",
        value=el.get("titulo", ""),
        key=f"{prefixo}_titulo",
        label_visibility="collapsed",
    )
    el["titulo"] = novo_titulo

    # ── semantic_type ──────────────────────────────────────────────────────────────────
    st_actual = el.get("semantic_type", "section")
    idx_st = SEMANTIC_TYPES.index(st_actual) if st_actual in SEMANTIC_TYPES else SEMANTIC_TYPES.index("section")
    novo_st = col_tipo.selectbox(
        "Tipo semântico",
        SEMANTIC_TYPES,
        index=idx_st,
        key=f"{prefixo}_semantic_type",
        label_visibility="collapsed",
    )
    el["semantic_type"] = novo_st

    # section_role inferido (ou override manual)
    section_role = el.get("section_role") or infer_section_role(novo_st)
    col_tipo.caption(f"↳ {section_role}")

    # ── nivel (só para headings) ──────────────────────────────────────────────────
    if novo_st == "section":
        nivel_actual = el.get("nivel", 1)
        if not isinstance(nivel_actual, int):
            nivel_actual = 1
        novo_nivel = col_nivel.number_input(
            "Nível",
            min_value=1, max_value=4,
            value=nivel_actual,
            key=f"{prefixo}_nivel",
            label_visibility="collapsed",
        )
        el["nivel"] = int(novo_nivel)
    else:
        col_nivel.markdown("")

    # ── display_order ─────────────────────────────────────────────────────
    ordem_actual = el.get("display_order", 0)
    if not isinstance(ordem_actual, (int, float)):
        ordem_actual = 0
    novo_ordem = col_ord.number_input(
        "Ordem",
        value=int(ordem_actual),
        key=f"{prefixo}_order",
        label_visibility="collapsed",
    )
    el["display_order"] = int(novo_ordem)

    # ── include ───────────────────────────────────────────────────────────
    novo_inc = col_inc.checkbox(
        "Incluir",
        value=bool(el.get("include", True)),
        key=f"{prefixo}_inc",
        label_visibility="collapsed",
    )
    el["include"] = novo_inc

    # ── behavior (expander opcional) ──────────────────────────────────────
    with st.expander("⚙ Comportamento (paginação / numeração / TOC)", expanded=False):
        beh      = el.get("behavior", {}) or {}
        beh_page = beh.get("page", {}) or {}
        beh_num  = beh.get("numbering", {}) or {}
        beh_toc  = beh.get("toc", {}) or {}

        defaults = get_defaults(el.get("semantic_type", "section"))

        col_b1, col_b2, col_b3 = st.columns(3)

        # TOC
        toc_include = col_b1.checkbox(
            "Entra no TOC",
            value=beh_toc.get("include", defaults["toc_include"]),
            key=f"{prefixo}_toc_include",
        )

        # Paginação
        page_break = col_b2.checkbox(
            "Page break antes",
            value=beh_page.get("break_before", defaults["page_break_before"]),
            key=f"{prefixo}_page_break",
        )
        section_break = col_b2.checkbox(
            "Section break antes",
            value=beh_page.get("section_break_before", defaults["section_break_before"]),
            key=f"{prefixo}_section_break",
        )

        # Numeração
        ESQUEMAS = ["arabic", "roman_lower", "roman_upper", "alpha", "none"]
        num_scheme_actual = beh_num.get("scheme", defaults["num_scheme"])
        idx_scheme = ESQUEMAS.index(num_scheme_actual) if num_scheme_actual in ESQUEMAS else 0
        num_scheme = col_b3.selectbox(
            "Esquema numeração",
            ESQUEMAS,
            index=idx_scheme,
            key=f"{prefixo}_num_scheme",
        )
        num_visible = col_b3.checkbox(
            "Número visível",
            value=beh_num.get("visible", defaults["num_visible"]),
            key=f"{prefixo}_num_visible",
        )
        num_restart = col_b3.checkbox(
            "Reiniciar numeração aqui",
            value=beh_num.get("restart", defaults["num_restart"]),
            key=f"{prefixo}_num_restart",
        )

        # Guardar apenas overrides (não gravar se igual ao default do semantic_type)
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


def _renderizar_elemento(el: dict, profundidade: int, prefixo: str,
                          tipos: list, elementos_raiz: list, idx_pai_path: str) -> None:
    """Renderiza recursivamente um elemento e os seus filhos."""
    margem = "　" * profundidade  # espaço de indentação visual
    rotulo_tipo = el.get("semantic_type", "section")
    slug_disp   = el.get("slug") or "—"

    with st.expander(f"{margem}**{slug_disp}** · *{rotulo_tipo}*", expanded=False):
        # Cabeçalho das colunas do formulário
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 1, 1, 1])
        c1.caption("Slug ⚠️"); c2.caption("Título"); c3.caption("Tipo")
        c4.caption("Nível"); c5.caption("Ordem"); c6.caption("Inc.")

        _renderizar_formulario_elemento(el, prefixo, tipos, elementos_raiz)

        # Botões de acção
        col_filho, col_rem, _ = st.columns([2, 2, 6])

        if col_filho.button("➕ Filho", key=f"{prefixo}_add_filho"):
            filhos = el.setdefault("filhos", [])
            novo_slug = _auto_slug(elementos_raiz)
            filhos.append(_elemento_vazio(novo_slug))
            st.rerun()

        # Confirmação de remoção
        if st.session_state.confirmar_remover == prefixo:
            st.warning("Confirmar remoção deste elemento?")
            col_sim, col_nao, _ = st.columns([1, 1, 8])
            if col_sim.button("Sim", key=f"{prefixo}_rem_sim"):
                st.session_state.confirmar_remover = None
                # Sinaliza remoção via flag no próprio elemento
                el["_remover"] = True
                st.rerun()
            if col_nao.button("Não", key=f"{prefixo}_rem_nao"):
                st.session_state.confirmar_remover = None
                st.rerun()
        else:
            if col_rem.button("🗑 Remover", key=f"{prefixo}_rem"):
                st.session_state.confirmar_remover = prefixo
                st.rerun()

        # Filhos recursivos
        filhos = el.get("filhos") or []
        if filhos:
            st.divider()
            _renderizar_lista_elementos(filhos, profundidade + 1, prefixo, tipos, elementos_raiz)

        # Limpar filhos marcados para remoção
        if filhos:
            el["filhos"] = [f for f in filhos if not f.get("_remover")]


def _renderizar_lista_elementos(lista: list, profundidade: int, prefixo_base: str,
                                 tipos: list, elementos_raiz: list) -> None:
    """Itera a lista e renderiza cada elemento."""
    for i, el in enumerate(lista):
        if not isinstance(el, dict):
            continue
        prefixo = f"{prefixo_base}_{i}"
        _renderizar_elemento(el, profundidade, prefixo, tipos, elementos_raiz, prefixo_base)


def _carregar_estrutura_yaml_ficheiro(caminho: str) -> dict:
    """Lê e faz parse de um ficheiro estrutura.yaml. Devolve dict ou {}."""
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
        return dados
    except Exception:
        return {}


def _guardar_estrutura_yaml_ficheiro(caminho: str, dados: dict) -> tuple:
    """Serializa e escreve o dict para o ficheiro. Devolve (ok, msg)."""
    try:
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            yaml.dump(dados, f, allow_unicode=True,
                      default_flow_style=False, sort_keys=False)
        return True, f"Estrutura guardada em: {caminho}"
    except Exception as exc:
        return False, f"Erro ao guardar: {exc}"


def _migrar_v1_para_v2(elementos: list) -> None:
    """Converte campos tipo v1 → semantic_type v2 em todos os elementos (recursivo)."""
    for el in elementos:
        if not isinstance(el, dict):
            continue
        if "tipo" in el and "semantic_type" not in el:
            el["semantic_type"] = TIPO_V1_TO_SEMANTIC_TYPE.get(el["tipo"], "section")
            del el["tipo"]
        filhos = el.get("filhos") or []
        if filhos:
            _migrar_v1_para_v2(filhos)


# ---------------------------------------------------------------------------
# Configuração multi-projecto
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def carregar_config() -> dict:
    """Lê config.yaml. Devolve dict vazio se não existir ou estiver corrompido."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    return {}


def guardar_config(config: dict) -> None:
    """Escreve config.yaml com o estado actualizado."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def carregar_projecto(projecto: dict) -> None:
    """
    Carrega estrutura.yaml e mapeamento.yaml do projecto para session_state.
    Actualiza estrutura_yaml_raw, estrutura_yaml_path, mapeamento e mapeamento_yaml_path.
    Se o path é um directório, tenta append dos nomes de ficheiro esperados.
    """
    path_estrutura  = projecto.get("estrutura", "")
    path_mapeamento = projecto.get("mapeamento", "")

    # Fallback: se path é directório, tentar append do nome de ficheiro
    if path_estrutura and Path(path_estrutura).is_dir():
        for candidato in ("estrutura_v2.yaml", "estrutura.yaml"):
            p_cand = Path(path_estrutura) / candidato
            if p_cand.is_file():
                path_estrutura = str(p_cand)
                break
    if path_mapeamento and Path(path_mapeamento).is_dir():
        p_cand = Path(path_mapeamento) / "mapeamento.yaml"
        if p_cand.is_file():
            path_mapeamento = str(p_cand)

    if path_estrutura and Path(path_estrutura).is_file():
        with open(path_estrutura, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        _migrar_v1_para_v2(raw.get("elementos", []))
        st.session_state.estrutura_yaml_raw  = raw
        st.session_state.estrutura_yaml_path = path_estrutura
        # Actualizar também a lista plana de elementos usada no TOC
        novos_elementos = parse_estrutura_yaml(
            yaml.dump(raw, allow_unicode=True, default_flow_style=False)
        )
        if novos_elementos:
            limpar_chaves_checkboxes(st.session_state.elementos)
            st.session_state.elementos = novos_elementos
    else:
        if path_estrutura:
            st.warning(f"estrutura.yaml não encontrado: {path_estrutura}")

    if path_mapeamento and Path(path_mapeamento).is_file():
        with open(path_mapeamento, "r", encoding="utf-8") as f:
            conteudo_map = f.read()
        mapeamento_novo = parse_mapeamento_yaml(conteudo_map)

        # Limpar widget keys da Camada 2 para forçar reinicialização com novos valores
        for el in mapeamento_novo.get("elementos", []):
            slug = el.get("slug", "")
            for sufixo in ("_md_source", "_md_scope", "_template", "_nota"):
                key = f"map_{slug}{sufixo}"
                if key in st.session_state:
                    del st.session_state[key]

        st.session_state.mapeamento           = mapeamento_novo
        st.session_state.mapeamento_yaml_path = path_mapeamento

    st.session_state.projecto_activo = {
        "id":            projecto.get("id", ""),
        "name":          projecto.get("name", ""),
        "reference_doc": projecto.get("reference_doc", ""),
    }


# ===========================================================================
# CAMADA 2 — MAPEAMENTO: funções auxiliares
# ===========================================================================

def _obter_elementos_flat(elementos: list, nivel_max: int = 99) -> list:
    """Percorre a árvore recursivamente e devolve lista plana de todos os
    elementos com include=True.
    Cada item: {slug, titulo, semantic_type, nivel, profundidade}
    """
    resultado = []

    def _percorrer(lista: list, prof: int) -> None:
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
    """Converte lista de elementos do mapeamento em dict {slug: {campos}}.
    Tolerante a mapeamento vazio ou None.
    """
    if not mapeamento:
        return {}
    elementos = mapeamento.get("elementos", []) or []
    return {el["slug"]: el for el in elementos if "slug" in el}


def _renderizar_camada2(elementos_flat: list, map_actual: dict) -> None:
    """Renderiza o editor de mapeamento: uma linha por elemento.
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
        margem = "\u3000" * prof  # espaço largo U+3000

        # Valores do mapeamento carregado
        map_el = map_actual.get(slug, {})

        # Inicializar widget keys no session_state SE ainda não existirem.
        # Garante que o primeiro rerun usa os valores do mapeamento,
        # e reruns seguintes preservam o que o utilizador editou.
        key_md   = f"map_{slug}_md_source"
        key_sc   = f"map_{slug}_md_scope"
        key_tpl  = f"map_{slug}_template"
        key_nota = f"map_{slug}_nota"

        if key_md not in st.session_state:
            st.session_state[key_md]   = map_el.get("md_source", "")
        if key_sc not in st.session_state:
            scope_val = map_el.get("md_scope", "ficheiro_inteiro")
            st.session_state[key_sc] = scope_val if scope_val in MD_SCOPE_OPCOES else MD_SCOPE_OPCOES[0]
        if key_tpl not in st.session_state:
            st.session_state[key_tpl]  = map_el.get("template_docx", "default")
        if key_nota not in st.session_state:
            st.session_state[key_nota] = map_el.get("nota", "")

        with st.expander(
            f"{margem}**{slug}** · *{semantic_type}* — {titulo}",
            expanded=(st.session_state[key_md] == ""),  # aberto se ainda sem source
        ):
            col1, col2 = st.columns([3, 1])

            # NÃO passar value= — o Streamlit usa o valor de session_state[key]
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
    if not st.session_state.get("mapeamento"):
        st.session_state.mapeamento = {}
    st.session_state.mapeamento["elementos"] = novo_mapeamento_elementos

    st.divider()

    # ── Botão guardar mapeamento.yaml ────────────────────────────────────
    path_map = st.session_state.get("mapeamento_yaml_path", "")
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
                # Resolver reference_doc: projecto_activo > defaults do config
                _defaults_cfg = carregar_config().get("defaults", {})
                _ref_doc = (
                    st.session_state.projecto_activo.get("reference_doc")
                    or _defaults_cfg.get("reference_doc", "")
                )
                dados_export = {
                    "doc_id":        st.session_state.projecto_activo.get("id", ""),
                    "doc_title":     st.session_state.projecto_activo.get("name", ""),
                    "estrutura_ref": "estrutura.yaml",
                    "data":          str(__import__("datetime").date.today()),
                    "templates": {
                        "geral": _ref_doc,
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


# ===========================================================================
# LAYOUT PRINCIPAL
# ===========================================================================
inicializar_estado()

# Auto-load do projecto no arranque (uma vez por sessão)
_config_boot   = carregar_config()
_projectos     = _config_boot.get("projects", [])
_last_id       = _config_boot.get("last_project", "")

if _projectos and not st.session_state.projecto_carregado:
    _proj_default = next(
        (p for p in _projectos if p["id"] == _last_id), _projectos[0]
    )
    carregar_projecto(_proj_default)
    st.session_state.projecto_carregado = True

paths_cfg = ler_paths_config()

# ---------------------------------------------------------------------------
# Sidebar — selecção de projecto + import/export
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("JSJ-DOC-ENGINE")
    st.divider()

    # ── Selecção de projecto ──────────────────────────────────────────────
    _cfg_sb = carregar_config()
    _projs_sb = _cfg_sb.get("projects", [])

    st.subheader("Projecto activo")

    if _projs_sb:
        _nomes_sb = [p.get("name", p.get("id", "sem nome")) for p in _projs_sb]
        _id_actual = st.session_state.projecto_activo.get("id", "")
        _idx_actual = next(
            (i for i, p in enumerate(_projs_sb) if p["id"] == _id_actual), 0
        )
        _idx_sel = st.selectbox(
            "Projecto",
            options=range(len(_nomes_sb)),
            format_func=lambda i: _nomes_sb[i],
            index=_idx_actual,
            key="sel_projecto",
            label_visibility="collapsed",
        )
        col_load, col_del = st.columns([3, 1])
        if col_load.button("Carregar", width="stretch", key="btn_carregar_proj"):
            _proj_sel = _projs_sb[_idx_sel]
            carregar_projecto(_proj_sel)
            st.session_state.projecto_carregado = True
            # Registar último projecto usado no config.yaml
            _cfg_sb["last_project"] = _proj_sel["id"]
            guardar_config(_cfg_sb)
            st.toast(f"✅ Projecto carregado: {_proj_sel['name']}", icon="✅")
            st.rerun()

        # Confirmação em dois passos para apagar projecto
        if st.session_state.confirmar_apagar_proj:
            st.warning(f"Apagar projecto **{_projs_sb[_idx_sel]['name']}** e os seus ficheiros do disco?")
            col_sim, col_nao = st.columns(2)
            if col_sim.button("✅ Sim, apagar", key="btn_confirm_del_proj"):
                _proj_a_apagar = _projs_sb[_idx_sel]
                # Apagar ficheiros YAML do disco
                for campo in ("estrutura", "mapeamento", "variaveis"):
                    path_f = _proj_a_apagar.get(campo, "")
                    if path_f and Path(path_f).is_file():
                        try:
                            os.remove(path_f)
                        except Exception:
                            pass
                # Remover do config.yaml
                _cfg_sb["projects"] = [
                    p for p in _cfg_sb["projects"] if p["id"] != _proj_a_apagar["id"]
                ]
                if _cfg_sb.get("last_project") == _proj_a_apagar["id"]:
                    _cfg_sb["last_project"] = (
                        _cfg_sb["projects"][0]["id"] if _cfg_sb["projects"] else ""
                    )
                guardar_config(_cfg_sb)
                # Limpar session_state se era o projecto activo
                if st.session_state.projecto_activo.get("id") == _proj_a_apagar["id"]:
                    st.session_state.estrutura_yaml_raw   = {}
                    st.session_state.estrutura_yaml_path  = ""
                    st.session_state.mapeamento           = {}
                    st.session_state.mapeamento_yaml_path = ""
                    st.session_state.projecto_activo      = {"id": "", "name": "", "reference_doc": ""}
                    st.session_state.projecto_carregado   = False
                    # Limpar widget keys da Camada 2
                    keys_to_del = [k for k in st.session_state if k.startswith("map_")]
                    for k in keys_to_del:
                        del st.session_state[k]
                st.session_state.confirmar_apagar_proj = False
                st.toast(f"✅ Projecto apagado: {_proj_a_apagar['name']}", icon="✅")
                st.rerun()
            if col_nao.button("❌ Cancelar", key="btn_cancel_del_proj"):
                st.session_state.confirmar_apagar_proj = False
                st.rerun()
        else:
            if col_del.button("🗑", key="btn_del_proj", help="Apagar projecto e ficheiros"):
                st.session_state.confirmar_apagar_proj = True
                st.rerun()
    else:
        _proj_disp = st.session_state.projecto_activo
        st.markdown(f"**{_proj_disp['name']}**")
        st.caption(f"ID: `{_proj_disp['id']}`")

    st.divider()

    # ── Novo projecto ─────────────────────────────────────────────────────
    with st.expander("+ Novo projecto", expanded=False):
        # st.form impede reruns intermédios enquanto o utilizador preenche os campos
        with st.form(key="form_novo_proj", clear_on_submit=True):
            _np_nome       = st.text_input("Nome do projecto")
            _np_estrutura  = st.text_input("Path estrutura.yaml",
                                            placeholder=r"C:\caminho\para\estrutura.yaml")
            st.caption("Path do ficheiro .yaml, não da pasta")
            _np_mapeamento = st.text_input("Path mapeamento.yaml",
                                            placeholder=r"C:\caminho\para\mapeamento.yaml")
            st.caption("Path do ficheiro .yaml, não da pasta")
            _np_variaveis  = st.text_input("Path variaveis.yaml (opcional)",
                                            placeholder=r"C:\caminho\para\variaveis.yaml")
            _np_reference  = st.text_input("Template DOCX (reference.docx)",
                                            placeholder=r"C:\caminho\para\reference.docx",
                                            value=_cfg_sb.get("defaults", {}).get("reference_doc", ""))
            st.caption("Deixar vazio para usar o template por defeito em defaults.")
            _submitted = st.form_submit_button("💾 Gravar projecto", use_container_width=True)

        if _submitted:
            if not _np_nome.strip():
                st.error("O nome do projecto não pode estar vazio.")
            elif not _np_estrutura.strip():
                st.error("O path de estrutura.yaml não pode estar vazio.")
            else:
                # Gerar id a partir do nome (ex: "CTE Projecto X" → "cte-projecto-x")
                _novo_id = re.sub(r"[^a-z0-9]+", "-",
                                  _np_nome.strip().lower()).strip("-")
                _cfg_add = carregar_config()
                _ids_existentes = {p["id"] for p in _cfg_add.get("projects", [])}
                # Garantir unicidade do id
                if _novo_id in _ids_existentes:
                    _novo_id = f"{_novo_id}-{len(_ids_existentes) + 1}"
                # Auto-append nome de ficheiro se o path é um directório
                _est_path = _np_estrutura.strip()
                if _est_path and Path(_est_path).is_dir():
                    for _cand in ("estrutura_v2.yaml", "estrutura.yaml"):
                        if (Path(_est_path) / _cand).is_file():
                            _est_path = str(Path(_est_path) / _cand)
                            break
                    else:
                        _est_path = str(Path(_est_path) / "estrutura.yaml")
                _map_path = _np_mapeamento.strip()
                if _map_path and Path(_map_path).is_dir():
                    _map_path = str(Path(_map_path) / "mapeamento.yaml")

                _novo_proj = {
                    "id":            _novo_id,
                    "name":          _np_nome.strip(),
                    "estrutura":     _est_path,
                    "mapeamento":    _map_path,
                    "variaveis":     _np_variaveis.strip(),
                    "reference_doc": _np_reference.strip(),
                }
                if "projects" not in _cfg_add:
                    _cfg_add["projects"] = []
                _cfg_add["projects"].append(_novo_proj)
                _cfg_add["last_project"] = _novo_id
                guardar_config(_cfg_add)
                carregar_projecto(_novo_proj)
                st.session_state.projecto_carregado = True
                st.toast(f"✅ Projecto gravado: {_np_nome.strip()}", icon="✅")
                st.rerun()

    st.divider()

    # ── Importar manualmente (fallback) ──────────────────────────────────
    with st.expander("Importar manualmente", expanded=False):

        # ── estrutura.yaml ───────────────────────────────────────────────
        st.subheader("estrutura.yaml")

        export_path_est = st.text_input(
            "Path de exportação",
            value=(
                st.session_state.export_path_estrutura
                or st.session_state.get("estrutura_yaml_path", "")
                or paths_cfg.get("estrutura", "")
            ),
            key="input_path_estrutura",
            placeholder=r"C:\caminho\para\estrutura.yaml",
        )
        # Persistir o path entre reruns
        st.session_state.export_path_estrutura = export_path_est

        if st.button("Exportar estrutura.yaml", width="stretch"):
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
            # Armazenar YAML em bruto e nome do ficheiro para o editor de estrutura (Camada 1)
            dados_raw = yaml.safe_load(conteudo_est) or {}
            # Compatibilidade retroactiva: converter campos tipo v1 → semantic_type v2
            _migrar_v1_para_v2(dados_raw.get("elementos", []))
            if dados_raw != st.session_state.estrutura_yaml_raw:
                st.session_state.estrutura_yaml_raw  = dados_raw
                st.session_state.estrutura_yaml_path = ficheiro_est.name
            novos_elementos = parse_estrutura_yaml(conteudo_est)
            if novos_elementos:
                # Evitar reimport em cada rerun — só actualiza se slug set mudar
                slugs_novos   = {el["slug"] for el in novos_elementos}
                slugs_actuais = {el["slug"] for el in st.session_state.elementos}
                if slugs_novos != slugs_actuais:
                    limpar_chaves_checkboxes(st.session_state.elementos)
                    st.session_state.elementos = novos_elementos
                    st.toast(f"✅ Estrutura importada: {len(novos_elementos)} elementos.", icon="✅")
                    st.rerun()
            else:
                st.warning("Nenhum elemento encontrado no ficheiro importado.")

        st.divider()

        # ── mapeamento.yaml ──────────────────────────────────────────────
        st.subheader("mapeamento.yaml")

        export_path_map = st.text_input(
            "Path de exportação",
            value=st.session_state.export_path_mapeamento or paths_cfg.get("mapeamento", ""),
            key="input_path_mapeamento",
            placeholder=r"C:\caminho\para\mapeamento.yaml",
        )
        st.session_state.export_path_mapeamento = export_path_map

        if st.button("Exportar mapeamento.yaml", width="stretch"):
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
            # Limpar widget keys da Camada 2 para forçar reinicialização com novos valores
            for el in mapeamento_importado.get("elementos", []):
                slug = el.get("slug", "")
                for sufixo in ("_md_source", "_md_scope", "_template", "_nota"):
                    key = f"map_{slug}{sufixo}"
                    if key in st.session_state:
                        del st.session_state[key]
            st.session_state.mapeamento = mapeamento_importado
            n_el = len(mapeamento_importado.get("elementos", []))
            st.toast(f"✅ Mapeamento importado: {n_el} elementos.", icon="✅")

# ---------------------------------------------------------------------------
# Tabs principais — Camada 3 (TOC), Camada 1 (Estrutura) e Camada 2 (Mapeamento)
# ---------------------------------------------------------------------------
tab_toc, tab_est, tab_map = st.tabs(["TOC / Compilar", "Estrutura", "Mapeamento"])


# ===========================================================================
# TAB 1 — TOC / Compilar (Camada 3, sem alterações)
# ===========================================================================
with tab_toc:
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

    # Footer — botão Compilar DOCX (stub desactivado)
    st.divider()
    st.button(
        "Compilar DOCX",
        disabled=True,
        width="stretch",
        help="Disponível após configurar mapeamento (Camada 2)",
    )


# ===========================================================================
# TAB 2 — Editor de Estrutura (Camada 1)
# ===========================================================================
with tab_est:
    st.header("Editor de Estrutura")

    # Verificar se o ficheiro foi importado na sidebar — único entry point
    # Nota: NÃO usar st.stop() aqui — mata tabs seguintes (Mapeamento)
    _tem_estrutura = bool(st.session_state.get("estrutura_yaml_raw"))
    if not _tem_estrutura:
        st.info("Importe o ficheiro estrutura.yaml na sidebar para começar a editar.")

    if _tem_estrutura:
        raw: dict = st.session_state.estrutura_yaml_raw

        # Mostrar qual o ficheiro activo
        st.caption(f"A editar: {st.session_state.get('estrutura_yaml_path', 'ficheiro importado')}")

        st.divider()

        # ── Metadados do documento ───────────────────────────────────────
        with st.expander("Metadados do documento", expanded=False):
            col_dt, col_tit_doc = st.columns([2, 5])
            raw["doc_type"]  = col_dt.text_input("doc_type",  value=raw.get("doc_type", ""),  key="c1_doc_type")
            raw["doc_title"] = col_tit_doc.text_input("doc_title", value=raw.get("doc_title", ""), key="c1_doc_title")

        st.divider()

        # ── Tipos semânticos ──────────────────────────────────────────────
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

        # ── Lista de elementos ────────────────────────────────────────────
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

        # ── Validação e guardar ───────────────────────────────────────────
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
    map_actual = _mapeamento_por_slug(st.session_state.get("mapeamento", {}))

    # Renderizar editor de mapeamento
    _renderizar_camada2(elementos_flat, map_actual)

