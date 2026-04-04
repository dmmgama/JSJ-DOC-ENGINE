# JSJ-DOC-ENGINE — 04_APP

> Ponto de entrada para o agente IDE.
> Ler antes de qualquer acção nesta pasta.

---

## 1. O QUE É ESTA PASTA

Código fonte da app JSJ-DOC-ENGINE.
Não tocar fora desta pasta — o resto do projecto é governo (Cowork).

---

## 2. CONTEXTO DO SISTEMA

Sistema de produção de documentos técnicos JSJ.
Converte Markdown em DOCX via Pandoc com estilos JSJ.
UI Streamlit local — multi-projecto, stateless entre sessões.

Arquitectura completa → `00_GOVERNO\ARQUITECTURA.md`
Estado do projecto → `00_GOVERNO\ROADMAP.md`

---

## 3. STACK

| Componente | Ferramenta |
|------------|-----------|
| UI | Streamlit |
| Motor compilação | Pandoc (binário standalone) |
| Estilos DOCX | reference.docx em `02_TEMPLATES\` |
| Orquestrador | compile.py |
| Preprocessador | preprocessor.py |
| Configuração | config.yaml |
| Runtime | Python 3.x + venv |

---

## 4. FICHEIROS DESTA PASTA

> **⚠️ REFACTORIZAÇÃO EM CURSO (D15)** — ver `DECISAO-REFACTOR-CLEAN.md`

### Estrutura actual (Clean Architecture — Step 1 concluído)

```
04_APP\
├── app.py                          ← 1051 linhas: UI + routing (Step 2 partirá em ui/)
├── core/                           ← lógica pura — ZERO imports streamlit ✅
│   ├── __init__.py
│   ├── models.py                   ← elemento_vazio() factory
│   └── services.py                 ← 9 funções: numeração, slugs, validação, migração, aplanar
├── adapters/                       ← I/O + serialização — ZERO imports streamlit ✅
│   ├── __init__.py
│   ├── yaml_io.py                  ← 7 funções: ler/escrever YAML + gerar/parse estrutura e mapeamento
│   └── config.py                   ← 3 funções: ler/escrever config.yaml + CONFIG_PATH
├── ui/                             ← placeholder para Step 2
│   ├── __init__.py
│   ├── state.py                    ← (futuro) init_state(), clear_project_state()
│   ├── sidebar.py                  ← (futuro) selecção projecto, criar/apagar
│   ├── tab_toc.py                  ← (futuro) Tab TOC interactivo + compilação
│   ├── tab_estrutura.py            ← (futuro) Tab editor de estrutura (Camada 1)
│   └── tab_mapeamento.py           ← (futuro) Tab mapeamento (Camada 2)
```

### Ficheiros standalone (sem alteração)

| Ficheiro | Responsabilidade |
|----------|----------------|
| `compile.py` | Orquestrador: resolve behavior → injeccta marcadores → Pandoc + Lua filter → DOCX |
| `preprocessor.py` | Substitui `{{ excel \| ... }}` por tabelas MD e `{{ VARIAVEL }}` por variaveis.yaml |
| `semantic_type_registry.py` | Registry de tipos semânticos: defaults hardcoded + `resolve_behavior()` |
| `migrate_schema_v1_to_v2.py` | Script standalone: migra `estrutura.yaml` v1 (campo `tipo`) → v2 (`semantic_type`) |
| `config.yaml` | Multi-projecto: `defaults` + `projects[]` + `last_project` ✅ |
| `filters\pagebreak.lua` | Lua filter Pandoc: converte `<!-- pagebreak -->` / `<!-- sectionbreak -->` em OpenXML |
| `requirements.txt` | Dependências Python |
| `venv\` | Ambiente virtual — não versionar |

---

## 5. FICHEIROS EXTERNOS (fora desta pasta)

Cada projecto/documento tem dois ficheiros YAML próprios,
cujos paths estão definidos no `config.yaml`:

| Ficheiro | Conteúdo |
|----------|---------|
| `estrutura.yaml` | Schema v2: `semantic_type` + `behavior` (overrides) + `filhos[]` recursivo |
| `mapeamento.yaml` | MD sources + templates DOCX por elemento |
| `variaveis.yaml` | (opcional) Variáveis `{{ VAR }}` para substituição no preprocessor |

Estes ficheiros vivem junto dos projectos-fonte (ex: CTE-TEMPLATE-CLAUDE),
não dentro de 04_APP.

> Formato YAML — Python parseia com `yaml.safe_load()`.
> Gerados e exportados pela app — não editar manualmente.

---

## 6. ARRANQUE

```bash
cd 04_APP
venv\Scripts\activate
streamlit run app.py
```

Se venv não existir:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Pandoc tem de estar instalado como binário standalone:
https://pandoc.org/installing.html

---

## 7. ARQUITECTURA DA APP

### 7a. Clean Architecture (D15) — Regra de Dependência

```
core/  ←  adapters/  ←  ui/  ←  app.py
```

- **`core/`** — lógica pura Python. ZERO imports de streamlit, adapters, ou ui.
- **`adapters/`** — I/O de ficheiros. ZERO imports de streamlit ou ui.
- **`ui/`** — Streamlit. Pode importar core/ e adapters/.
- **`app.py`** — routing. Importa ui/.

### 7b. 3 Camadas Funcionais (tabs da UI)

```
CAMADA 1 — Editor de Estrutura do Documento (ui/tab_estrutura.py)
    Criar/editar/remover elementos de qualquer documento
    Campos universais: slug, titulo, tipo, nivel, include, display_order
    Tipos configuráveis: pré-definidos mas editáveis/apagáveis pelo utilizador
    Slug: identificador único — explicado ao utilizador, pode ser auto-gerado
    Agnóstico: sem referência a CTE, MAT, EXEC ou qualquer doc específico
    Output: estrutura.yaml

CAMADA 2 — Mapeamento de Conteúdo (ui/tab_mapeamento.py)
    MD source por elemento, template DOCX por elemento
    Output: mapeamento.yaml

CAMADA 3 — TOC Interactivo (ui/tab_toc.py)
    Toggle N/A, reordenação, preview numeração
    Export/Import estrutura.yaml + mapeamento.yaml
    Botão "Compilar DOCX"
    Função Snapshot
```

---

## 8. PIPELINE DE COMPILAÇÃO

```
config.yaml → escolha de projecto
        ↓
estrutura.yaml (v2) + mapeamento.yaml (auto-load ou import)
        ↓
compile.py
    ├── lê estrutura.yaml → semantic_type_registry.resolve_behavior() por elemento
    ├── lê mapeamento.yaml
    ├── lê MD de cada elemento
    ├── preprocessor.py → {{ excel }} → tabelas MD; {{ VARIAVEL }} → variaveis.yaml
    ├── injeccta marcadores antes de cada elemento:
    │       <!-- pagebreak -->          (se behavior.page_break_before)
    │       <!-- sectionbreak -->       (se behavior.section_break_before)
    │       <!-- sectionbreak-landscape --> (se orientation=landscape)
    ├── concatena MD processado
    └── Pandoc → DOCX
            ├── --lua-filter filters/pagebreak.lua  (converte marcadores em OpenXML)
            └── --reference-doc 02_TEMPLATES\JSJ-CTE-reference.docx
```

Output em: `03_OUTPUT\`

**Semantic Type Registry** (`semantic_type_registry.py`):
- 12 tipos semânticos: `cover`, `toc`, `list_of_figures`, `list_of_tables`,
  `front_matter_note`, `revision_history`, `section`, `unnumbered_heading`,
  `subsection_group`, `annexes`, `annex`, `glossary`
- `section_role` inferido: `front_matter` / `main_matter` / `back_matter`
- Overridável por elemento no `estrutura.yaml` (campo `section_role` ou bloco `behavior`)

---

## 9. FUNÇÃO SNAPSHOT

Congela o estado do documento numa pasta escolhida pelo utilizador.
Nunca toca nos ficheiros originais.

```
[NomeDocumento]_[YYYY-MM-DD]\
├── ESTRUTURA\
│   ├── estrutura.yaml
│   └── mapeamento.yaml
└── MDS\
    ├── Modo A: ficheiros MD copiados tal como estão
    └── Modo B: MD divididos por heading (H2 contém filhos H3/H4)
```

---

## 10. ESTADO ACTUAL

Ver `00_GOVERNO\ROADMAP.md` para estado detalhado.

**⚠️ REFACTORIZAÇÃO CLEAN ARCHITECTURE (D15) EM CURSO**

| Componente | Estado | Nota |
|------------|--------|------|
| **Refactor Step 1** (core/ + adapters/) | ✅ **concluído** | `core/models.py`, `core/services.py`, `adapters/yaml_io.py`, `adapters/config.py` |
| **Refactor Step 2** (ui/ + app.py routing) | ⏳ **← PRÓXIMO** | `PROMPT-IDE-REFACTOR-STEP2.md` |
| `preprocessor.py` | ✅ funcional | sem alteração |
| `semantic_type_registry.py` | ✅ criado | sem alteração |
| `migrate_schema_v1_to_v2.py` | ✅ criado | sem alteração |
| `filters\pagebreak.lua` | ✅ criado | sem alteração |
| `config.yaml` | ✅ schema multi-projecto | sem alteração |
| `compile.py` | ⚠️ schema v0 | SUSPENSO até após refactorização |

**Próxima acção:** executar `00_GOVERNO\PROMPT-IDE-REFACTOR-STEP2.md`.

---

## 11. REGRAS PARA O AGENTE IDE

### Regras gerais
- Nunca criar ficheiros fora de `04_APP\`
- Nunca editar ficheiros de governo (`00_GOVERNO\`)
- Se precisar de contexto de arquitectura → ler `00_GOVERNO\ARQUITECTURA.md`
- Se precisar de saber o estado → ler `00_GOVERNO\ROADMAP.md`
- Comentar código em português
- Funções curtas com responsabilidade única
- Não introduzir dependências não listadas em requirements.txt sem avisar

### Regras de arquitectura Clean (D15) — INVIOLÁVEIS
1. Nunca importar `streamlit` em ficheiros `core/` ou `adapters/`
2. Nunca importar `adapters/` ou `ui/` em ficheiros `core/`
3. Lógica de negócio nova → `core/services.py`
4. I/O de ficheiros novo → `adapters/`
5. UI nova → `ui/` (módulo existente ou novo)
6. `app.py` nunca excede 60 linhas
7. Nenhum ficheiro em `ui/` excede 300 linhas — partir se necessário
8. Session state: só aceder via `ui/state.py` helpers

---

## 12. MANUTENÇÃO DESTE README

O agente IDE deve actualizar este ficheiro quando:
- Criar um ficheiro novo em `04_APP\` → adicionar à secção 4
- Alterar a pipeline de compilação → actualizar secção 8
- Completar uma funcionalidade → actualizar secção 10 (Estado Actual)
- Alterar dependências → actualizar secções 3 e 6

Não alterar: secções 1, 2, 7, 9 — são decisões de arquitectura,
geridas pelo Cowork via `00_GOVERNO\ARQUITECTURA.md`.

Se algo nessas secções estiver errado → reportar ao Cowork,
não corrigir directamente.

---

**Fim �                                                                                  