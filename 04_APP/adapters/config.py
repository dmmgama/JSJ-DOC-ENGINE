"""
adapters/config.py — Gestão de config.yaml

Leitura, escrita e gestão de projectos no config.yaml multi-projecto.

REGRA: ZERO imports de streamlit.
"""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def ler_paths_config() -> dict:
    """Tenta ler paths de estrutura e mapeamento do config.yaml.

    Devolve dict com chaves 'estrutura' e 'mapeamento' (strings vazias se ausentes).
    """
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        # Suporte a schema novo (campo projecto_activo) e schema antigo
        proj = cfg.get("projecto_activo", cfg)
        return {
            "estrutura":  proj.get("estrutura", ""),
            "mapeamento": proj.get("mapeamento", ""),
        }
    except Exception:
        return {"estrutura": "", "mapeamento": ""}


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
