# PROMPT IDE — JSJ-DOC-ENGINE — compile.py v2: Schema v2 (estrutura.yaml + mapeamento.yaml)

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Reescrever `compile.py` para ler `estrutura.yaml` + `mapeamento.yaml` em vez do schema v0 do `config.yaml`
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**

---

## CONTEXTO

O `compile.py` actual usa schema v0: lê campos `document`, `paths`, `sections` directamente
do `config.yaml`. Este schema foi abandonado — a estrutura do documento está agora em
`estrutura.yaml` (v2) e o mapeamento MD→elemento em `mapeamento.yaml`.

A tarefa é reescrever `compile.py` para usar o novo schema, mantendo toda a lógica de
Pandoc, Lua filter e `_injectar_marcadores()` já existente e correcta.

---

## FICHEIROS RELEVANTES

```
04_APP\
├── compile.py                  ← a reescrever
├── config.yaml                 ← schema multi-projecto (lê para localizar estrutura+mapeamento)
├── preprocessor.py             ← NÃO tocar
├── semantic_type_registry.py   ← NÃO tocar (resolve_behavior já importado)
├── filters\pagebreak.lua       ← NÃO tocar
```

---

## SCHEMA DOS FICHEIROS DE INPUT

### config.yaml (multi-projecto)
```yaml
defaults:
  templates_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES"
  output_dir:    "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/03_OUTPUT"
  reference_doc: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"
projects:
  - id:         CTE-SecI
    name:       "CTE Fundações e Estruturas"
    estrutura:  "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/estrutura_v2.yaml"
    mapeamento: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/mapeamento.yaml"
    variaveis:  ""
last_project: CTE-SecI
```

### estrutura.yaml (v2) — schema relevante
```yaml
meta:
  doc_id: CTE-SecI
  doc_title: "CTE Fundações e Estruturas"
  version: "2"

elementos:
  - slug: cover
    titulo: "Capa"
    semantic_type: cover
    include: true
    nivel: 0
    display_order: 1
    behavior: {}          # vazio = usar defaults do registry
    filhos: []

  - slug: LEX
    titulo: "Disposições Legais e Normativas"
    semantic_type: section
    include: true
    nivel: 1
    display_order: 10
    behavior: {}
    filhos:
      - slug: LEX-1
        titulo: "Legislação aplicável"
        semantic_type: subsection_group
        include: true
        nivel: 2
        display_order: 11
        behavior: {}
        filhos: []
```

**Regras:**
- Elementos com `include: false` são ignorados
- A árvore é percorrida recursivamente (filhos incluídos se pai incluído)
- `display_order` define a ordem — ordenar antes de processar
- `behavior: {}` → usar defaults do `semantic_type_registry`

### mapeamento.yaml — schema relevante
```yaml
doc_id: CTE-SecI
doc_title: "CTE Fundações e Estruturas"
estrutura_ref: "estrutura_v2.yaml"
templates:
  geral: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"
elementos:
  - slug: cover
    md_source: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/COVER.md"
    md_scope: ficheiro_inteiro     # ficheiro_inteiro | heading_especifico
    template_docx: default         # default | path absoluto
    nota: ""
  - slug: LEX
    md_source: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/LEX.md"
    md_scope: ficheiro_inteiro
    template_docx: default
    nota: ""
```

---

## TAREFA — reescrever compile.py

### Assinatura do ponto de entrada

O `compile.py` actual aceita `--config config.yaml`. Manter este argumento, mas o seu
significado muda: passa a ser o `config.yaml` multi-projecto. Adicionar argumento opcional
`--project <id>` para especificar qual projecto compilar (default: `last_project`).

```
python compile.py [--config config.yaml] [--project CTE-SecI]
```

---

### Funções a manter (já correctas, NÃO alterar lógica interna)

- `_find_pandoc()` — sem alterações
- `_injectar_marcadores(elemento)` — sem alterações
- `_run_pandoc(pandoc_bin, md_content, template_docx, output_path)` — sem alterações

---

### Funções a reescrever / criar

#### `_load_config(config_path: Path) -> dict`
```python
def _load_config(config_path: Path) -> dict:
    """Carrega config.yaml multi-projecto."""
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml não encontrado: '{config_path}'")
    with config_path.open(encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ValueError("config.yaml inválido: conteúdo não é um mapeamento YAML.")
    if 'projects' not in cfg:
        raise ValueError("config.yaml: campo 'projects' em falta.")
    return cfg
```

#### `_resolve_project(cfg: dict, project_id: str | None) -> dict`
```python
def _resolve_project(cfg: dict, project_id: str | None) -> dict:
    """
    Devolve o dict do projecto a compilar.
    Usa project_id se fornecido, senão usa last_project, senão usa projects[0].
    Lança ValueError se não encontrar projecto.
    """
    projects = cfg.get('projects', [])
    if not projects:
        raise ValueError("config.yaml: lista 'projects' vazia.")

    pid = project_id or cfg.get('last_project', '')
    if pid:
        proj = next((p for p in projects if p.get('id') == pid), None)
        if proj:
            return proj
        print(f"[AVISO] Projecto '{pid}' não encontrado — a usar o primeiro.", file=sys.stderr)

    return projects[0]
```

#### `_load_estrutura(path: str) -> dict`
```python
def _load_estrutura(path: str) -> dict:
    """Carrega estrutura.yaml v2."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"estrutura.yaml não encontrado: '{path}'")
    with p.open(encoding='utf-8') as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or 'elementos' not in data:
        raise ValueError(f"estrutura.yaml inválido (campo 'elementos' em falta): '{path}'")
    return data
```

#### `_load_mapeamento(path: str) -> dict`
```python
def _load_mapeamento(path: str) -> dict:
    """Carrega mapeamento.yaml. Devolve dict vazio se path vazio ou ficheiro não existe."""
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"[AVISO] mapeamento.yaml não encontrado: '{path}' — compilação sem MD sources.", file=sys.stderr)
        return {}
    with p.open(encoding='utf-8') as fh:
        data = yaml.safe_load(fh) or {}
    return data
```

#### `_collect_elements_flat(elementos: list) -> list[dict]`
```python
def _collect_elements_flat(elementos: list) -> list[dict]:
    """
    Percorre a árvore de elementos recursivamente.
    Devolve lista plana ordenada por display_order, apenas elementos com include=True.
    Cada item é o dict original do elemento (com slug, semantic_type, behavior, etc.).
    """
    resultado = []

    def _percorrer(lista):
        activos = [el for el in lista if el.get('include', True)]
        activos.sort(key=lambda e: e.get('display_order', 9999))
        for el in activos:
            resultado.append(el)
            filhos = el.get('filhos', []) or []
            if filhos:
                _percorrer(filhos)

    _percorrer(elementos)
    return resultado
```

#### `_build_mapa_md(mapeamento: dict) -> dict`
```python
def _build_mapa_md(mapeamento: dict) -> dict:
    """
    Converte lista de elementos do mapeamento em dict {slug: {md_source, md_scope, template_docx, nota}}.
    """
    elementos = mapeamento.get('elementos', []) or []
    return {el['slug']: el for el in elementos if 'slug' in el}
```

#### `_resolve_template_docx(el_map: dict, cfg_defaults: dict, mapeamento: dict) -> Path`
```python
def _resolve_template_docx(el_map: dict, cfg_defaults: dict, mapeamento: dict) -> Path:
    """
    Resolve o template DOCX para um elemento.
    Prioridade: el_map['template_docx'] (se não for 'default') > mapeamento['templates']['geral'] > cfg_defaults['reference_doc']
    """
    td = el_map.get('template_docx', 'default')
    if td and td != 'default':
        return Path(td)

    geral = mapeamento.get('templates', {}).get('geral', '')
    if geral:
        return Path(geral)

    ref = cfg_defaults.get('reference_doc', '')
    if ref:
        return Path(ref)

    raise RuntimeError("Nenhum template DOCX encontrado (config defaults, mapeamento.templates.geral ou elemento).")
```

#### `_build_combined_md(elements_flat: list, mapa_md: dict) -> str`

Reescrever completamente:

```python
def _build_combined_md(elements_flat: list, mapa_md: dict) -> str:
    """
    Para cada elemento incluído:
      1. Verifica se tem md_source no mapeamento
      2. Se não tem → pula com warning
      3. Se tem → lê ficheiro, passa por preprocessor, injeta marcadores
    Concatena tudo com '\n\n' como separador.
    """
    parts = []

    for el in elements_flat:
        slug = el.get('slug', '?')
        el_map = mapa_md.get(slug, {})
        md_source = el_map.get('md_source', '').strip()

        if not md_source:
            print(f"  [SKIP] {slug} — sem md_source no mapeamento", file=sys.stderr)
            continue

        md_path = Path(md_source)
        if not md_path.exists():
            print(f"  [AVISO] {slug} — ficheiro MD não encontrado: '{md_source}'", file=sys.stderr)
            continue

        md_text = md_path.read_text(encoding='utf-8')
        processed = preprocessor.process_markdown(md_text, base_path=md_path.parent)

        # Injectar marcadores de paginação com base no semantic_type + behavior
        marcadores = _injectar_marcadores(el)
        parts.append(marcadores + processed)

    if not parts:
        raise ValueError(
            "Nenhum elemento tem md_source válido no mapeamento.\n"
            "Preencha o mapeamento.yaml antes de compilar."
        )

    return '\n\n'.join(parts)
```

#### `compile_document(config_path: Path, project_id: str | None = None)`

Reescrever completamente:

```python
def compile_document(config_path: Path, project_id: str | None = None):
    """Executa o pipeline completo de compilação (schema v2)."""
    pandoc_bin = _find_pandoc()

    cfg = _load_config(config_path)
    cfg_defaults = cfg.get('defaults', {})

    projecto = _resolve_project(cfg, project_id)
    doc_id   = projecto.get('id', 'DOC')
    doc_name = projecto.get('name', doc_id)

    print(f"[{doc_id}] Projecto: {doc_name}")

    # Carregar estrutura e mapeamento
    estrutura  = _load_estrutura(projecto['estrutura'])
    mapeamento = _load_mapeamento(projecto.get('mapeamento', ''))

    # Resolver output
    output_dir = Path(cfg_defaults.get('output_dir', '.'))
    output_dir.mkdir(parents=True, exist_ok=True)

    meta = estrutura.get('meta', {})
    output_filename = meta.get('output_filename', f"{doc_id}.docx")
    output_path = output_dir / output_filename

    # Resolver template DOCX (usar o geral do mapeamento ou defaults)
    template_docx = _resolve_template_docx({}, cfg_defaults, mapeamento)
    if not template_docx.exists():
        raise FileNotFoundError(
            f"reference.docx não encontrado: '{template_docx}'\n"
            "Verifique paths.reference_doc em config.yaml."
        )

    # Recolher elementos
    elements_flat = _collect_elements_flat(estrutura.get('elementos', []))
    mapa_md       = _build_mapa_md(mapeamento)

    print(f"[{doc_id}] {len(elements_flat)} elemento(s) incluído(s):")
    for el in elements_flat:
        slug = el.get('slug', '?')
        md   = mapa_md.get(slug, {}).get('md_source', '—')
        print(f"  [{el.get('display_order', '?')}] {slug} ({el.get('semantic_type', '?')}) → {md}")

    combined_md = _build_combined_md(elements_flat, mapa_md)

    print(f"[{doc_id}] A chamar Pandoc → {output_path}")
    _run_pandoc(pandoc_bin, combined_md, template_docx, output_path)

    print(f"Compilado: {output_path}")
```

---

### `main()` — adicionar argumento `--project`

```python
def main():
    parser = argparse.ArgumentParser(
        description='JSJ-DOC-ENGINE — Compilador MD → DOCX via Pandoc (schema v2)'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Caminho para config.yaml multi-projecto (default: config.yaml)',
    )
    parser.add_argument(
        '--project',
        default=None,
        help='ID do projecto a compilar (default: last_project no config.yaml)',
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (Path(__file__).parent / config_path).resolve()

    try:
        compile_document(config_path, project_id=args.project)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        sys.exit(1)
```

---

## NOTA SOBRE output_filename

O `meta` do `estrutura.yaml` pode não ter `output_filename`. Se ausente, usar `f"{doc_id}.docx"`.
Verificar se o campo existe antes de usar:

```python
output_filename = meta.get('output_filename') or f"{doc_id}.docx"
```

---

## RESTRIÇÕES

- **NÃO tocar** em `_find_pandoc()`, `_injectar_marcadores()`, `_run_pandoc()`
- **NÃO tocar** em `preprocessor.py`, `semantic_type_registry.py`, `filters\pagebreak.lua`
- `_load_mapeamento()` deve ser tolerante: se ficheiro não existe → continua (aviso) sem crashar
- `_collect_elements_flat()` deve ser recursivo e respeitar `display_order` em cada nível
- Comentar código em **português**
- Não introduzir dependências novas (yaml, pathlib, subprocess, tempfile, shutil já importados)
- Manter importações existentes: `preprocessor`, `semantic_type_registry.resolve_behavior`

---

## VERIFICAÇÃO

1. `python compile.py --help` mostra `--config` e `--project`
2. `python compile.py` (sem argumentos) usa `config.yaml` e `last_project: CTE-SecI`
3. Elementos sem `md_source` → `[SKIP]` no output, sem crash
4. Elementos com `md_source` inexistente → `[AVISO]` no output, sem crash
5. Se nenhum elemento tem MD válido → erro claro com instrução de acção
6. DOCX gerado em `defaults.output_dir` com nome `{doc_id}.docx` (ou `output_filename` se definido no meta)
7. `python compile.py --project CTE-SecI` compila projecto especificado

---

## ENTREGÁVEIS

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\compile.py` | ✅ reescrito — schema v2 |

Após concluir, actualizar `04_APP\README.md` secção 10:
- `compile.py` → ✅ schema v2 (lê estrutura.yaml + mapeamento.yaml)

---

**Fim — PROMPT-IDE-COMPILE-V2.md — 2026-04-03**
