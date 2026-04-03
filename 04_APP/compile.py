"""
compile.py — JSJ-DOC-ENGINE
Orquestrador principal de compilação MD → DOCX via Pandoc.

Uso:
    python compile.py [--config config.yaml]

Fluxo (conforme ARQUITECTURA.md §4):
    1. Lê config.yaml
    2. Filtra secções com include: true
    3. Ordena por display_order
    4. Lê cada MD e passa por preprocessor.process_markdown()
    5. Concatena MD processado
    6. Chama Pandoc com --reference-doc, --from=markdown, --to=docx
    7. Reporta sucesso ou erro
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

import preprocessor
from semantic_type_registry import resolve_behavior


PANDOC_INSTALL_URL = "https://pandoc.org/installing.html"


def _find_pandoc() -> str:
    """Devolve o nome/path do executável Pandoc, ou lança RuntimeError."""
    import shutil
    pandoc = shutil.which('pandoc')
    if pandoc is None:
        raise RuntimeError(
            "Pandoc não encontrado no PATH.\n"
            f"Instale o Pandoc standalone em: {PANDOC_INSTALL_URL}\n"
            "Após instalação, reinicie o terminal e tente novamente."
        )
    return pandoc


def _load_config(config_path: Path) -> dict:
    """Carrega e valida config.yaml."""
    if not config_path.exists():
        raise FileNotFoundError(f"Ficheiro de configuração não encontrado: '{config_path}'")
    with config_path.open(encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ValueError(f"config.yaml inválido: conteúdo não é um mapeamento YAML.")
    for key in ('document', 'paths', 'sections'):
        if key not in cfg:
            raise ValueError(f"config.yaml: campo obrigatório '{key}' em falta.")
    return cfg


def _resolve_paths(cfg: dict, config_dir: Path) -> tuple[Path, Path, Path]:
    """
    Resolve e valida os três paths principais do config.

    Returns:
        (source_root, template_docx, output_dir)
    """
    p = cfg['paths']

    source_root = Path(p['source_root'])
    if not source_root.is_absolute():
        source_root = (config_dir / source_root).resolve()

    template_docx = Path(p['template_docx'])
    if not template_docx.is_absolute():
        template_docx = (config_dir / template_docx).resolve()

    output_dir = Path(p['output_dir'])
    if not output_dir.is_absolute():
        output_dir = (config_dir / output_dir).resolve()

    if not source_root.exists():
        raise FileNotFoundError(
            f"source_root não existe: '{source_root}'\n"
            "Verifique paths.source_root em config.yaml."
        )
    if not template_docx.exists():
        raise FileNotFoundError(
            f"reference.docx não encontrado: '{template_docx}'\n"
            "Verifique paths.template_docx em config.yaml."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    return source_root, template_docx, output_dir


def _collect_sections(cfg: dict, source_root: Path) -> list[dict]:
    """Filtra, ordena e valida as secções a incluir."""
    sections = cfg.get('sections', [])
    included = [s for s in sections if s.get('include', False)]

    if not included:
        raise ValueError(
            "Nenhuma secção com 'include: true' encontrada em config.yaml.\n"
            "Active pelo menos uma secção para compilar."
        )

    included.sort(key=lambda s: s.get('display_order', 9999))

    for sec in included:
        md_path = source_root / sec['path']
        if not md_path.exists():
            raise FileNotFoundError(
                f"Ficheiro MD não encontrado para secção '{sec['slug']}': '{md_path}'"
            )

    return included


def _injectar_marcadores(elemento: dict) -> str:
    """
    Retorna string MD com marcadores de paginação a injectar
    antes do conteúdo do elemento, com base no behavior resolvido.
    """
    behavior = resolve_behavior(elemento)
    marcadores = []

    if behavior["section_break_before"]:
        if behavior["orientation"] == "landscape":
            marcadores.append("<!-- sectionbreak-landscape -->")
        else:
            marcadores.append("<!-- sectionbreak -->")
    elif behavior["page_break_before"]:
        marcadores.append("<!-- pagebreak -->")

    return "\n".join(marcadores) + "\n" if marcadores else ""


def _build_combined_md(sections: list[dict], source_root: Path) -> str:
    """Lê, pré-processa e concatena os MD das secções activas."""
    parts = []
    for sec in sections:
        md_path = source_root / sec['path']
        md_text = md_path.read_text(encoding='utf-8')
        processed = preprocessor.process_markdown(md_text, base_path=md_path.parent)
        # Injectar marcadores de paginação antes do conteúdo da secção
        marcadores = _injectar_marcadores(sec)
        parts.append(marcadores + processed)

    # Separador entre secções: linha em branco
    return '\n\n'.join(parts)


def _run_pandoc(pandoc_bin: str, md_content: str, template_docx: Path, output_path: Path):
    """Escreve MD num ficheiro temporário e invoca Pandoc como subprocess."""
    with tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8', suffix='.md', delete=False
    ) as tmp:
        tmp.write(md_content)
        tmp_path = Path(tmp.name)

    try:
        lua_filter = Path(__file__).parent / "filters" / "pagebreak.lua"

        cmd = [
            pandoc_bin,
            str(tmp_path),
            '--from=markdown',
            '--to=docx',
            f'--reference-doc={template_docx}',
            '--lua-filter', str(lua_filter),
            '--output', str(output_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(
                f"Pandoc terminou com erro (código {result.returncode}):\n{stderr}"
            )

        if result.stderr.strip():
            print(f"[AVISO Pandoc] {result.stderr.strip()}", file=sys.stderr)

    finally:
        tmp_path.unlink(missing_ok=True)


def compile_document(config_path: Path):
    """Executa o pipeline completo de compilação."""
    pandoc_bin = _find_pandoc()

    cfg = _load_config(config_path)
    config_dir = config_path.resolve().parent

    source_root, template_docx, output_dir = _resolve_paths(cfg, config_dir)
    sections = _collect_sections(cfg, source_root)

    doc_id = cfg['document'].get('id', 'DOC')
    output_filename = cfg['document']['output_filename']
    output_path = output_dir / output_filename

    print(f"[{doc_id}] Compilando {len(sections)} secção(ões)…")
    for sec in sections:
        print(f"  + [{sec['display_order']}] {sec['slug']} — {sec['title']}")

    combined_md = _build_combined_md(sections, source_root)

    print(f"[{doc_id}] A chamar Pandoc → {output_path}")
    _run_pandoc(pandoc_bin, combined_md, template_docx, output_path)

    print(f"Compilado: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='JSJ-DOC-ENGINE — Compilador MD → DOCX via Pandoc'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Caminho para o ficheiro config.yaml (default: config.yaml)',
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Resolve relativo ao directório onde compile.py está localizado
        config_path = (Path(__file__).parent / config_path).resolve()

    try:
        compile_document(config_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
