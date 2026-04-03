# semantic_type_registry.py
# Registry de tipos semânticos — defaults hardcoded
# O YAML guarda apenas overrides; estes são os valores base.

SEMANTIC_TYPES = [
    "cover",
    "front_matter_note",
    "revision_history",
    "toc",
    "list_of_figures",
    "list_of_tables",
    "section",
    "unnumbered_heading",
    "subsection_group",
    "annexes",
    "annex",
    "glossary",
]

# Defaults por semantic_type
# Campos: toc_include, page_break_before, section_break_before,
#         num_visible, num_scheme, num_restart, section_role
SEMANTIC_TYPE_DEFAULTS = {
    "cover":             {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "front_matter_note": {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "roman_lower", "num_restart": False, "section_role": "front_matter"},
    "revision_history":  {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "toc":               {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "list_of_figures":   {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "list_of_tables":    {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "front_matter"},
    "section":           {"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": True,  "num_scheme": "arabic",      "num_restart": False, "section_role": "main_matter"},
    "unnumbered_heading":{"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "main_matter"},
    "subsection_group":  {"toc_include": True,  "page_break_before": False, "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "main_matter"},
    "annexes":           {"toc_include": False, "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "back_matter"},
    "annex":             {"toc_include": True,  "page_break_before": True,  "section_break_before": False, "num_visible": True,  "num_scheme": "alpha",       "num_restart": True,  "section_role": "back_matter"},
    "glossary":          {"toc_include": True,  "page_break_before": True,  "section_break_before": False, "num_visible": False, "num_scheme": "none",        "num_restart": False, "section_role": "back_matter"},
}

# Mapeamento de migração v1 → v2
TIPO_V1_TO_SEMANTIC_TYPE = {
    "front_matter": "front_matter_note",
    "seccao":       "section",
    "heading":      "section",
    "toc":          "toc",
    "anexo":        "annex",
    "anexos":       "annexes",
}


def get_defaults(semantic_type: str) -> dict:
    """Retorna os defaults para um semantic_type. Fallback para 'section'."""
    return SEMANTIC_TYPE_DEFAULTS.get(semantic_type, SEMANTIC_TYPE_DEFAULTS["section"]).copy()


def infer_section_role(semantic_type: str) -> str:
    """Infere section_role a partir do semantic_type."""
    return get_defaults(semantic_type)["section_role"]


def resolve_behavior(element: dict) -> dict:
    """
    Resolve o behavior efectivo de um elemento.
    Começa pelos defaults do semantic_type e aplica overrides do YAML.
    """
    semantic_type = element.get("semantic_type", "section")
    defaults = get_defaults(semantic_type)
    behavior = element.get("behavior", {}) or {}

    # Resolver section_role: manual override ou inferido
    section_role = element.get("section_role") or defaults["section_role"]

    # Resolver behavior com overrides
    toc_block       = behavior.get("toc", {}) or {}
    page_block      = behavior.get("page", {}) or {}
    numbering_block = behavior.get("numbering", {}) or {}

    return {
        "section_role":         section_role,
        "toc_include":          toc_block.get("include",              defaults["toc_include"]),
        "page_break_before":    page_block.get("break_before",        defaults["page_break_before"]),
        "section_break_before": page_block.get("section_break_before",defaults["section_break_before"]),
        "page_size":            page_block.get("size",                "A4"),
        "orientation":          page_block.get("orientation",         "portrait"),
        "num_visible":          numbering_block.get("visible",        defaults["num_visible"]),
        "num_scheme":           numbering_block.get("scheme",         defaults["num_scheme"]),
        "num_restart":          numbering_block.get("restart",        defaults["num_restart"]),
        "num_start_at":         numbering_block.get("start_at",       1),
    }
