# ARQUITECTURA — JSJ-DOC-ENGINE

> **Versão:** 1.0 — Abril 2026
> **Estado:** MVP em desenvolvimento

---

## 1. OBJECTIVO

Produzir DOCX técnicos JSJ a partir de fontes Markdown,
de forma determinística, reprodutível e maintível por
qualquer colaborador JSJ — sem dependência do autor original.

**Não é:** um substituto do Word. O output é sempre DOCX.
**Não é:** um sistema web. É local, simples, sem servidor.
**Não é:** específico do CTE. É agnóstico de documento.

---

## 2. PRINCÍPIOS

### P1 — Determinismo
O mesmo input produz sempre o mesmo output.
Pandoc + reference.docx = zero comportamento emergente.

### P2 — Maintibilidade
3 peças independentes e substituíveis:
- `config.yaml` — estrutura e ordem dos documentos
- `compile.py` — orquestrador de compilação
- `app.py` — UI Streamlit

Se a app desaparecer → `compile.py` funciona standalone.
Se `compile.py` desaparecer → Pandoc funciona directamente.
Se o Supabase (futuro) desaparecer → os MD são a fonte de verdade.

### P3 — MD como fonte de verdade
O conteúdo vive em ficheiros Markdown.
A numeração é gerada no compile step — nunca embebida nos MD.
Referências entre secções usam slug, nunca número.

### P4 — Output sempre DOCX
A JSJ trabalha em Word. O sistema adapta-se à JSJ,
não o contrário. Qualquer evolução futura mantém este output.

### P5 — Agnóstico de documento
O sistema não conhece o CTE, nem memórias descritivas,
nem qualquer documento específico. Conhece apenas:
secções com slug, título, path MD, ordem e inclusão.
O documento é definido no `config.yaml`.

---

## 3. STACK

| Componente | Ferramenta | Justificação |
|------------|-----------|-------------|
| Motor compilação | Pandoc (binário standalone) | Padrão de facto MD→DOCX. Estável há 15 anos. |
| Estilos DOCX | reference.docx JSJ | Template Word com estilos definidos. Pandoc mapeia directamente. |
| Orquestrador | Python 3.x + PyYAML | Simples, legível, maintível. |
| UI | Streamlit | Local, sem deploy, sem infra. |
| Pós-processamento | python-docx | Pontual — só onde Pandoc não chega. |
| Preprocessador Excel | preprocessor.py + openpyxl/pandas | Injecta tabelas Excel em MD antes do Pandoc. |
| Configuração | config.yaml | Fonte de verdade da estrutura de cada documento. |
| Supabase | — | Fora do scope MVP. Fase posterior. |

**Não usar:** LangChain, frameworks pesadas, dependências exóticas,
qualquer LLM na pipeline de compilação.

---

## 4. ARQUITECTURA DO SISTEMA

```
config.yaml
    │
    ▼
compile.py
    ├── lê secções aplicáveis (include: true)
    ├── ordena por display_order
    ├── lê ficheiros MD de cada secção
    ├── passa cada MD por preprocessor.py
    │       └── substitui {{ excel | path | sheet | range }}
    │           por tabelas Markdown geradas do Excel
    ├── concatena MD processado em stream temporário
    └── chama Pandoc → DOCX em 03_OUTPUT\
            │
            └── usa 02_TEMPLATES\reference.docx
                    (estilos JSJ)

app.py (Streamlit)
    ├── lê config.yaml
    ├── mostra árvore de secções
    ├── permite reordenar (drag ou setas)
    ├── permite toggle N/A por secção
    ├── mostra preview de numeração
    └── botão "Compilar" → chama compile.py
```

---

## 5. SCHEMA config.yaml

```yaml
document:
  id: "CTE-SecI"
  title: "CTE Fundações e Estruturas — Secção I"
  output_filename: "CTE_SecI_v1.docx"

paths:
  source_root: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE"
  template_docx: "../02_TEMPLATES/JSJ-CTE-reference.docx"
  output_dir: "../03_OUTPUT"

sections:
  - slug: LEX
    title: "Léxico e Enquadramento Contratual"
    path: "02_CONTRATUAL/LEX.md"
    part: "0"
    display_order: 1
    include: true

  - slug: GERAL
    title: "Disposições Gerais"
    path: "02_CONTRATUAL/GERAL.md"
    part: "I"
    display_order: 2
    include: true
```

---

## 6. DECISÕES DE ARQUITECTURA

| # | Decisão | Escolha | Alternativa rejeitada |
|---|---------|---------|----------------------|
| D1 | Motor compilação | Pandoc | python-docx como motor principal |
| D2 | Numeração | Gerada no compile step | Embebida nos MD / delegada no Word |
| D3 | Configuração | config.yaml por documento | Base de dados (Supabase) — fase posterior |
| D4 | UI | Streamlit local | Web app com deploy |
| D5 | Scope MVP | Agnóstico de documento | Específico do CTE |
| D6 | Preprocessador Excel | preprocessor.py independente chamado por compile.py | Excel embedido directamente no MD |

---

## 7. FORA DO SCOPE (MVP)

- Supabase / base de dados
- Editor de conteúdo MD na app
- Versionamento de secções
- Multi-utilizador
- Deploy web
- Integração com outros sistemas JSJ

---

**Fim — ARQUITECTURA.md v1.0 — 2026-04-03**
