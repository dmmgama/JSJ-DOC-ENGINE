# ARQUITECTURA — JSJ-DOC-ENGINE

> **Versão:** 1.2 — Abril 2026
> **Estado:** Fase 1 concluída — Fase 2 em desenvolvimento

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
A app não conhece o CTE nem qualquer documento JSJ específico.
Conhece elementos com: slug, titulo, tipo (configurável),
nivel (1-4), include (bool), display_order.
Os tipos são configuráveis por documento — pré-definidos como
ponto de partida, mas editáveis, renomeáveis e apagáveis.
O slug é opcional — pode ser gerado automaticamente pela app.

---

## 2a. AGNOSTICISMO DA APP

A app não conhece nenhum documento JSJ específico.
Conhece apenas: slug, titulo, tipo, nivel, include, display_order.
Os tipos são configuráveis pelo utilizador por documento.
O slug é o identificador único — pode ser gerado automaticamente.

Qualquer conceito específico de um documento (ex: MAT, EXEC,
"vinculativo") vive nos ficheiros YAML do projecto, não na app.

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
config.yaml (multi-projecto)
        │
        ▼
app.py abre → escolha de projecto
        │
        ▼
estrutura.yaml + mapeamento.yaml (auto-load ou import)
        │
        ├── Camada 1: editor de estrutura → estrutura.yaml
        ├── Camada 2: mapeamento sources + templates → mapeamento.yaml
        ├── Camada 3: TOC interactivo + export/import + snapshot
        │
        └── "Compilar" →
                compile.py
                    ├── lê estrutura.yaml → resolve behavior por elemento (semantic_type_registry.py)
                    ├── lê mapeamento.yaml
                    ├── lê MD de cada elemento
                    ├── preprocessor.py ({{ excel }} → tabelas MD; {{ VARIAVEL }} → variaveis.yaml)
                    ├── injeccta marcadores <!-- pagebreak --> / <!-- sectionbreak --> no MD
                    ├── concatena MD processado
                    └── Pandoc → DOCX
                            ├── --lua-filter filters/pagebreak.lua (page/section breaks)
                            ├── template geral: 02_TEMPLATES\JSJ-CTE-reference.docx
                            └── 03_OUTPUT\
```

---

## 4a. CAMADAS DA APP

### Camada 1 — Definição do Documento
O utilizador define o que é o documento e como está organizado:
- `semantic_type` por elemento (enum fechado: cover, toc, section, annex, etc.)
- Estrutura hierárquica: Secções → Headings H1–H4 → Anexos com `filhos[]` recursivo
- `section_role` inferido (`front_matter` / `main_matter` / `back_matter`) — overridável por elemento
- `behavior` por elemento: paginação, numeração, TOC (só escrito quando difere dos defaults)
- Defaults inteligentes por `semantic_type` — hardcoded em `semantic_type_registry.py`
- Output: `estrutura.yaml` (schema v2)

### Camada 2 — Mapeamento de Conteúdo
Para cada elemento da estrutura:
- Qual ficheiro MD é a fonte (pode cobrir secção inteira ou heading específico)
- Qual template DOCX aplicar (geral ou override por secção)
- File picker: abre selector de ficheiro numa pasta definida em `config.yaml`
- Output: `mapeamento.yaml`

### Camada 3 — TOC Interactivo (tab dedicada)
Visualização e edição da estrutura completa:
- Toggle de visibilidade por elemento (N/A)
- Reordenação (setas ou drag)
- Preview de numeração em tempo real
- Export/Import `estrutura.yaml` e `mapeamento.yaml` — **funcional desde a primeira iteração**
- Botão "Compilar DOCX"
- Função Snapshot (Modo A — ficheiro inteiro / Modo B — divisão por heading com filhos)

---

## 4b. FICHEIROS DE TRABALHO POR DOCUMENTO

| Ficheiro | Conteúdo | Scope |
|----------|----------|-------|
| `estrutura.yaml` | Hierarquia do documento (tipo, secções, headings H1-H4, anexos) em YAML | Template reutilizável entre projectos |
| `mapeamento.yaml` | MD source + template DOCX por elemento em YAML | Específico de cada instância/obra |
| `variaveis.yaml` *(opcional)* | Variáveis `{{ VARIAVEL }}` substituídas pelo preprocessor.py antes da compilação | Específico de cada instância/obra |

Os ficheiros são independentes e exportáveis/importáveis separadamente.
Path de cada ficheiro definido em `config.yaml` (campo `variaveis:` opcional).

> Formato YAML escolhido sobre Markdown por ser parseável nativamente
> em Python (`yaml.safe_load()`), sem parser custom. Standard da
> comunidade docs-as-code para ficheiros de configuração hierárquicos.

---

## 5. ESTRUTURA DE FICHEIROS EM 04_APP

```
04_APP\
├── app.py                      ← UI Streamlit (3 camadas + snapshot)
├── compile.py                  ← orquestrador de compilação
├── preprocessor.py             ← tags {{ excel }} e {{ VARIAVEL }} → MD
├── semantic_type_registry.py   ← registry de tipos semânticos + defaults + resolve_behavior()
├── migrate_schema_v1_to_v2.py  ← script standalone: migra estrutura.yaml v1 → v2
├── config.yaml                 ← multi-projecto + paths defaults  ⏳
├── requirements.txt
├── filters\
│   └── pagebreak.lua           ← Lua filter Pandoc: page/section breaks via comentários HTML
└── venv\
```

Ficheiros de trabalho por projecto (fora de `04_APP\`, paths definidos em `config.yaml`):
- `estrutura.yaml`   ← schema v2: semantic_type + behavior + filhos[] — reutilizável como template
- `mapeamento.yaml`  ← MD sources + templates DOCX por elemento — específico de cada instância/obra
- `variaveis.yaml`   ← (opcional) variáveis `{{ VAR }}` para o preprocessor

---

## 6. SCHEMA config.yaml (multi-projecto)

```yaml
defaults:
  templates_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES"
  output_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/03_OUTPUT"

projects:
  - id: CTE-SecI
    name: "CTE Fundações e Estruturas"
    estrutura: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/estrutura.yaml"
    mapeamento: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/mapeamento.yaml"
    variaveis: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/variaveis.yaml"  # opcional

  - id: MD-Projecto-X
    name: "Memória Descritiva — Projecto X"
    estrutura: "C:/Users/JSJ/JSJ AI/Projecto-X/estrutura.yaml"
    mapeamento: "C:/Users/JSJ/JSJ AI/Projecto-X/mapeamento.yaml"
```

### Comportamento de arranque

```
App abre → lê config.yaml → tem projectos?
    ├── SIM → lista de projectos → utilizador escolhe → carrega automaticamente
    └── NÃO → ecrã boas-vindas: [Novo documento] ou [Importar existente]
```

O utilizador pode sempre adicionar/remover projectos da lista sem apagar ficheiros.

---

## 8. DECISÕES DE ARQUITECTURA

| # | Decisão | Escolha | Alternativa rejeitada |
|---|---------|---------|----------------------|
| D1 | Motor compilação | Pandoc | python-docx como motor principal |
| D2 | Numeração | Gerada no compile step | Embebida nos MD / delegada no Word |
| D3 | Configuração | config.yaml multi-projecto | Base de dados (Supabase) — fase posterior |
| D4 | UI | Streamlit local | Web app com deploy |
| D5 | Scope MVP | Agnóstico de documento | Específico do CTE |
| D6 | Multi-projecto | config.yaml lista de projectos, escolha no arranque da app | Um config.yaml por documento |
| D7 | App stateless | estrutura.yaml + mapeamento.yaml como mecanismo de continuidade entre sessões | Estado interno da app |
| D8 | Snapshot | Sem tocar nos originais; Modo A (ficheiro inteiro) / Modo B (divisão por heading com filhos) | Versionamento inline |
| D9 | LLM Guide | Ficheiro de contrato de interface entre projectos JSJ e o DOC-ENGINE (`00_GOVERNO/LLM_GUIDE.md`) | Protocolo informal |
| D10 | Supabase | Fora do scope MVP — arquitectura de MD compatível com migração futura | Supabase no MVP |
| D11 | Formato ficheiros de estrutura | YAML puro (`estrutura.yaml`, `mapeamento.yaml`) | MD com blocos key:value — frágil, não standard |
| D12 | Schema estrutura.yaml | v2: `semantic_type` + `behavior` (overrides) + `section_role` inferido; defaults hardcoded em `semantic_type_registry.py` | Flags avulsas (`is_annex`, `is_toc`…) — redundantes e contraditórias |
| D12a | Pipeline paginação | 3 tiers: Pandoc nativo → Lua filter (`filters/pagebreak.lua`) → python-docx (fase posterior) | Tudo no Pandoc (não chega) ou tudo no python-docx (frágil) |
| D12b | `section_role` | Inferido do `semantic_type`; overridável por elemento quando necessário | Campo obrigatório manual — ruído no YAML |

---

## 9. FORA DO SCOPE (MVP)

- Supabase / base de dados
- Editor de conteúdo MD na app
- Versionamento de secções
- Multi-utilizador
- Deploy web
- Integração com outros sistemas JSJ

---

**Fim — ARQUITECTURA.md v1.3 — 2026-04-03**
