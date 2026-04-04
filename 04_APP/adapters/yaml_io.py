"""
adapters/yaml_io.py — Leitura/escrita e serialização de ficheiros YAML

Operações de I/O e conversão de formato para estrutura.yaml, mapeamento.yaml.

REGRA: ZERO imports de streamlit.
"""

import os

import yaml

from core.services import aplanar_elementos


# ---------------------------------------------------------------------------
# I/O de ficheiros
# ---------------------------------------------------------------------------
def carregar_estrutura_yaml(caminho: str) -> dict:
    """Lê e faz parse de um ficheiro estrutura.yaml. Devolve dict ou {}."""
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
        return dados
    except Exception:
        return {}


def guardar_estrutura_yaml(caminho: str, dados: dict) -> tuple:
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
# Serialização — geração de YAML
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


# ---------------------------------------------------------------------------
# Deserialização — parse de YAML
# ---------------------------------------------------------------------------
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
    elementos = aplanar_elementos(elementos_yaml, None, contador)
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
