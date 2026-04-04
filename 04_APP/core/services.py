"""
core/services.py — Lógica pura do JSJ-DOC-ENGINE

Funções de negócio sem dependência de UI ou I/O.

REGRA: ZERO imports de streamlit, adapters ou ui.
"""

from semantic_type_registry import (
    SEMANTIC_TYPES,
    TIPO_V1_TO_SEMANTIC_TYPE,
)


# ---------------------------------------------------------------------------
# Numeração
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
# Aplanar hierarquia de elementos YAML
# ---------------------------------------------------------------------------
def aplanar_elementos(elementos_yaml: list, pai: str | None, contador: list) -> list:
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
                aplanar_elementos(filhos, el.get("slug"), contador)
            )
    return resultado


# ---------------------------------------------------------------------------
# Tipos semânticos e slugs
# ---------------------------------------------------------------------------
def obter_tipos(raw: dict) -> list:
    """Tipos semânticos disponíveis — sempre do registry, nunca do YAML."""
    return list(SEMANTIC_TYPES)


def todos_slugs(elementos: list) -> list:
    """Recolhe recursivamente todos os slugs presentes na lista de elementos."""
    slugs = []
    for el in elementos:
        if isinstance(el, dict):
            s = el.get("slug", "")
            if s:
                slugs.append(s)
            filhos = el.get("filhos") or []
            if filhos:
                slugs.extend(todos_slugs(filhos))
    return slugs


def auto_slug(elementos: list) -> str:
    """Gera um slug único no formato elem-NNN."""
    slugs_existentes = set(todos_slugs(elementos))
    i = 1
    while True:
        candidato = f"elem-{i:03d}"
        if candidato not in slugs_existentes:
            return candidato
        i += 1


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def validar_elementos(elementos: list) -> list:
    """Valida slugs únicos e títulos não vazios. Devolve lista de mensagens de erro."""
    erros = []
    slugs = todos_slugs(elementos)
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


# ---------------------------------------------------------------------------
# Camada 2 — funções auxiliares
# ---------------------------------------------------------------------------
def obter_elementos_flat(elementos: list, nivel_max: int = 99) -> list:
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


def mapeamento_por_slug(mapeamento: dict) -> dict:
    """Converte lista de elementos do mapeamento em dict {slug: {campos}}.
    Tolerante a mapeamento vazio ou None.
    """
    if not mapeamento:
        return {}
    elementos = mapeamento.get("elementos", []) or []
    return {el["slug"]: el for el in elementos if "slug" in el}


# ---------------------------------------------------------------------------
# Migração v1 → v2
# ---------------------------------------------------------------------------
def migrar_v1_para_v2(elementos: list) -> None:
    """Converte campos tipo v1 → semantic_type v2 em todos os elementos (recursivo)."""
    for el in elementos:
        if not isinstance(el, dict):
            continue
        if "tipo" in el and "semantic_type" not in el:
            el["semantic_type"] = TIPO_V1_TO_SEMANTIC_TYPE.get(el["tipo"], "section")
            del el["tipo"]
        filhos = el.get("filhos") or []
        if filhos:
            migrar_v1_para_v2(filhos)
