# PROMPT IDE — Migração parsers MD → YAML

> **Data:** 2026-04-03
> **Contexto:** Decisão D11 — DECISAO-YAML-ESTRUTURA.md
> **Para:** Agente IDE (VSCode)

---

## CONTEXTO

Stack: Python + Streamlit + Pandoc + PyYAML
Pasta de trabalho: `04_APP\`
Raiz do projecto: `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\`

Os ficheiros de estrutura mudaram de `.md` para `.yaml`.
Decisão documentada em `00_GOVERNO\DECISAO-YAML-ESTRUTURA.md`.

---

## ESTADO ACTUAL

`app.py` tem parsers para `.md` que falharam nos testes
(retornavam "Nenhum elemento encontrado").

Decisão tomada: migrar para YAML puro.

Ficheiros YAML de teste disponíveis em:
- `C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\estrutura.yaml`
- `C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\mapeamento.yaml`

Estrutura do `estrutura.yaml`:

```yaml
doc_type: CTE
doc_title: CTE Fundações e Estruturas

elementos:
  - slug: SEC-I
    titulo: Disposições Gerais e Contratuais
    tipo: seccao
    display_order: 1
    include: true
    filhos:
      - slug: LEX
        titulo: Léxico e Enquadramento Contratual
        tipo: heading
        nivel: 1
        display_order: 1.1
        include: true
        filhos:
          - slug: LEX-1
            titulo: Léxico Anti-Ambiguidade
            tipo: heading
            nivel: 2
            display_order: 1.1.1
            include: true
```

Estrutura do `mapeamento.yaml`:

```yaml
doc_id: CTE-SecI
estrutura_ref: estrutura.yaml

templates:
  geral: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"

elementos:
  - slug: LEX
    md_source: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/LEX.md"
    md_scope: ficheiro_inteiro
    template_docx: default

  - slug: MAT-MAD
    md_source: ""
    md_scope: ficheiro_inteiro
    template_docx: default
    nota: MD não produzido ainda — N/A por defeito
```

---

## TAREFA

1. Substituir `parse_estrutura_md()` por `parse_estrutura_yaml()`
   usando `yaml.safe_load()` — sem parser custom.
   O YAML tem estrutura hierárquica com campo `filhos` para
   elementos aninhados (secções → headings → sub-headings).

2. Substituir `gerar_estrutura_md()` por `gerar_estrutura_yaml()`
   que serializa o estado actual da estrutura para YAML.

3. Substituir `parse_mapeamento_md()` por `parse_mapeamento_yaml()`
   usando `yaml.safe_load()`.

4. Verificar que `pyyaml` está em `requirements.txt`.
   Se não estiver: `pip install pyyaml` e actualizar `requirements.txt`.

5. Testar import do `estrutura.yaml` real — deve carregar todos
   os elementos sem erros.

---

## RESTRIÇÕES

- Não alterar lógica de TOC, toggles N/A, reordenação
- Não alterar `compile.py` nem `preprocessor.py`
- Comentar em português
- Não introduzir dependências além de `pyyaml`

---

## VERIFICAÇÃO

- Import de `estrutura.yaml` carrega ~60 elementos sem erros
- TOC da app mostra hierarquia completa do CTE
- Export gera ficheiro YAML bem-formado (verificar com `yaml.safe_load()`)
- Import do YAML exportado re-renderiza o TOC sem erros

---

## ENTREGÁVEL

- `04_APP\app.py` actualizado (parsers YAML substituídos)
- `04_APP\requirements.txt` com `pyyaml`

Após concluído: confirmar ao Cowork (JSJ-DOC-ENGINE) que YAML funciona
para autorização de apagar `estrutura.md` e `mapeamento.md` obsoletos.

---

**Fim — PROMPT-IDE-YAML-MIGRATION.md — 2026-04-03**
