"""
migrate_schema_v1_to_v2.py — JSJ-DOC-ENGINE
Script standalone: converte estrutura.yaml v1 → v2.

Uso:
    python migrate_schema_v1_to_v2.py <path_estrutura_v1.yaml>

O ficheiro original não é alterado.
O resultado é guardado em <nome_original>_v2.yaml.
"""

import sys
from pathlib import Path

import yaml

from semantic_type_registry import TIPO_V1_TO_SEMANTIC_TYPE

# Bloco defaults que é adicionado ao cabeçalho do documento v2
DEFAULTS_BLOCK = {
    "schema_version": 2,
    "defaults": {
        "behavior": {
            "toc": {"include": None},       # None = inferido pelo semantic_type
            "page": {"break_before": None},
            "numbering": {"visible": None},
        }
    },
}


def _migrar_elemento(elemento: dict, avisos: list) -> dict:
    """
    Migra um único elemento de v1 para v2 (recursivamente para filhos).
    Modifica o dict in-place e devolve-o.
    """
    slug = elemento.get("slug", "<sem slug>")

    # --- Migrar campo 'tipo' → 'semantic_type' ---
    tipo_v1 = elemento.get("tipo")
    if tipo_v1 is not None:
        semantic_type = TIPO_V1_TO_SEMANTIC_TYPE.get(tipo_v1)
        if semantic_type is None:
            aviso = f"  [AVISO] slug='{slug}': tipo v1 '{tipo_v1}' não reconhecido — mapeado para 'section'"
            avisos.append(aviso)
            semantic_type = "section"
        elemento["semantic_type"] = semantic_type
        del elemento["tipo"]
    else:
        # Campo 'tipo' ausente: usar 'section' como fallback silencioso
        if "semantic_type" not in elemento:
            elemento["semantic_type"] = "section"

    # --- Processar filhos recursivamente ---
    filhos = elemento.get("filhos", [])
    if filhos:
        elemento["filhos"] = [_migrar_elemento(f, avisos) for f in filhos]

    return elemento


def _migrar_documento(doc: dict, avisos: list) -> dict:
    """
    Migra o documento completo (cabeçalho + elementos).
    """
    # Adicionar campos de cabeçalho v2
    doc["schema_version"] = DEFAULTS_BLOCK["schema_version"]
    if "defaults" not in doc:
        doc["defaults"] = DEFAULTS_BLOCK["defaults"]

    # Migrar cada elemento da lista 'elementos'
    elementos = doc.get("elementos", [])
    doc["elementos"] = [_migrar_elemento(el, avisos) for el in elementos]

    return doc


def main():
    if len(sys.argv) < 2:
        print("Uso: python migrate_schema_v1_to_v2.py <path_estrutura_v1.yaml>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"ERRO: Ficheiro não encontrado: '{input_path}'", file=sys.stderr)
        sys.exit(1)

    # Ler YAML v1
    with input_path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    if not isinstance(doc, dict):
        print("ERRO: Ficheiro YAML inválido — conteúdo não é um mapeamento.", file=sys.stderr)
        sys.exit(1)

    # Migrar
    avisos: list = []
    doc_migrado = _migrar_documento(doc, avisos)

    # Determinar path de saída
    output_path = input_path.parent / (input_path.stem + "_v2.yaml")

    # Guardar resultado
    with output_path.open("w", encoding="utf-8") as fh:
        yaml.dump(
            doc_migrado,
            fh,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    # Relatório
    print(f"\nMigração concluída: {input_path.name} → {output_path.name}")
    print(f"Elementos migrados: {len(doc_migrado.get('elementos', []))}")

    if avisos:
        print("\nAvisos:")
        for aviso in avisos:
            print(aviso)
    else:
        print("Sem avisos — todos os tipos v1 foram reconhecidos.")


if __name__ == "__main__":
    main()
