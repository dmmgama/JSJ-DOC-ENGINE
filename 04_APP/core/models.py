"""
core/models.py — Tipos de dados do JSJ-DOC-ENGINE

Factory methods para criação de elementos.

REGRA: ZERO imports de streamlit, adapters ou ui.
"""


def elemento_vazio(slug: str) -> dict:
    """Cria um elemento novo com valores por defeito."""
    return {
        "slug":          slug,
        "titulo":        "",
        "semantic_type": "section",
        "nivel":         1,
        "display_order": 0,
        "include":       True,
        "filhos":        [],
    }
