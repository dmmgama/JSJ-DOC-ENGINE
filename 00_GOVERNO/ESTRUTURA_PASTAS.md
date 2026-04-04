# ESTRUTURA DE PASTAS — JSJ-DOC-ENGINE

> **Versão:** 1.1 — Abril 2026

---

## ÁRVORE

```
JSJ-DOC-ENGINE\
│
├── README.md                        Ponto de entrada do projecto
│
├── 00_GOVERNO\                      Governo do projecto
│   ├── ARQUITECTURA.md              Stack, princípios, decisões técnicas
│   ├── ROADMAP.md                   Fases, gates, estado actual
│   ├── ESTRUTURA_PASTAS.md          Este ficheiro
│   └── SYSTEM_PROMPT.md             Instruções do agente Cowork
│
├── 01_AUDITORIAS\                   Pesquisa e avaliações externas
│   ├── DR-Gemini-DocEngine-2026-04-03.md
│   └── DR-Perplexity-DocEngine-2026-04-03.md
│
├── 02_TEMPLATES\                    Templates DOCX JSJ
│   └── JSJ-CTE-reference.docx      Reference doc para Pandoc (copiar de JSJ-Brand\)
│
├── 03_OUTPUT\                       DOCX compilados (não versionar)
│
└── 04_APP\                          Código fonte (VSCode + agente IDE)
    ├── app.py                       Routing (30-50 linhas pós-refactor D15)
    ├── core\                        Lógica pura — ZERO imports streamlit
    │   ├── models.py                Dataclasses: Elemento, Projecto, Estrutura
    │   └── services.py              Numeração, validação, parse/gerar YAML
    ├── adapters\                    I/O ficheiros — ZERO imports streamlit
    │   ├── yaml_io.py               Ler/escrever YAML
    │   └── config.py                Ler/escrever config.yaml
    ├── ui\                          Streamlit vive aqui e SÓ aqui
    │   ├── state.py                 Gestão session_state centralizada
    │   ├── sidebar.py               Sidebar: projectos, import/export
    │   ├── tab_toc.py               Tab TOC interactivo
    │   ├── tab_estrutura.py         Tab editor de estrutura
    │   └── tab_mapeamento.py        Tab mapeamento
    ├── compile.py                   Orquestrador de compilação
    ├── preprocessor.py              Preprocessador MD (Excel → tabelas MD)
    ├── semantic_type_registry.py    Registry de tipos semânticos
    ├── config.yaml                  Configuração multi-projecto
    ├── requirements.txt             Dependências Python
    ├── filters\
    │   └── pagebreak.lua            Lua filter Pandoc
    └── venv\                        Ambiente virtual (não versionar)
```

---

## REGRAS

| Regra | Detalhe |
|-------|---------|
| Cowork nunca toca em `04_APP\` | Só VSCode + agente IDE |
| `03_OUTPUT\` não é versionado | Ficheiros gerados automaticamente |
| `venv\` não é versionado | Recriado localmente |
| Decisões técnicas → `ARQUITECTURA.md` | Não dispersar por outros ficheiros |
| Estado do projecto → `ROADMAP.md` | Fonte única de verdade sobre progresso |

---

## CONVENÇÕES DE NOMEAÇÃO

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Ficheiros de governo | CAPS | `ARQUITECTURA.md` |
| Auditorias/DRs | `DR-[Fonte]-[Tema]-[Data].md` | `DR-Gemini-DocEngine-2026-04-03.md` |
| Templates DOCX | `JSJ-[Documento]-reference.docx` | `JSJ-CTE-reference.docx` |
| Output DOCX | `[DocID]_[versão].docx` | `CTE_SecI_v1.docx` |
| Config | `config.yaml` (um por sessão activa) | — |

---

**Fim — ESTRUTURA_PASTAS.md v1.1 — 2026-04-04**
