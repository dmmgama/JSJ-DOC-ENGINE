# DECISÃO — App Streamlit: Arquitectura Completa

> **Data:** 2026-04-03
> **Decisor:** David Gama
> **Estado:** FECHADA
> **Substitui:** DECISAO-APP-STREAMLIT.md (versão anterior — arquivar)
> **Impacto:** ARQUITECTURA.md, ROADMAP.md, SYSTEM_PROMPT.md, README.md

---

## 1. CONTEXTO

Esta decisão fecha a arquitectura completa da app Streamlit (Fase 2)
incluindo: camadas da app, gestão de estado, multi-projecto,
protocolo de integração LLM, e função de snapshot.

---

## 2. PRINCÍPIO BASE — APP STATELESS

A app não guarda estado internamente entre sessões.
Os ficheiros MD são a fonte de verdade persistente.
`estrutura.md` e `mapeamento.md` são o mecanismo de continuidade —
não um bonus de conveniência.

**Consequência:** export/import tem de estar funcional desde a
primeira versão da Camada 3. Sem isto a app não é utilizável
em sessões repetidas.

---

## 3. MULTI-PROJECTO — config.yaml

O `config.yaml` suporta múltiplos projectos. A app abre com
uma lista de projectos e o utilizador escolhe qual carregar.

### Schema config.yaml

```yaml
defaults:
  templates_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES"
  output_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/03_OUTPUT"

projects:
  - id: CTE-SecI
    name: "CTE Fundações e Estruturas"
    estrutura: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/estrutura.md"
    mapeamento: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/mapeamento.md"

  - id: MD-Projecto-X
    name: "Memória Descritiva — Projecto X"
    estrutura: "C:/Users/JSJ/JSJ AI/Projecto-X/estrutura.md"
    mapeamento: "C:/Users/JSJ/JSJ AI/Projecto-X/mapeamento.md"
```

### Comportamento de arranque

```
App abre → lê config.yaml → tem projectos?
    ├── SIM → lista de projectos → utilizador escolhe → carrega automaticamente
    └── NÃO → ecrã boas-vindas:
                [Novo documento] ou [Importar existente]
```

O utilizador pode sempre:
- Adicionar projecto à lista (regista path no config.yaml)
- Remover projecto da lista (não apaga ficheiros — só remove do config)
- Mudar de projecto activo sem fechar a app

---

## 4. AS 3 CAMADAS DA APP

### CAMADA 1 — Definição do Documento
O utilizador define o que é o documento e como está organizado.

- Tipo de documento (ex: CTE, Memória Descritiva, Relatório)
- Estrutura hierárquica: Secções → Headings H1–H4 → Anexos
- Elementos especiais: TOC geral, TOC de figuras, TOC de tabelas
- Output: `estrutura.md`

### CAMADA 2 — Mapeamento de Conteúdo
Para cada elemento da estrutura, o utilizador define:

- Qual ficheiro MD é a fonte (cobre secção inteira ou heading específico)
- Qual template DOCX aplicar (geral ou override por secção)
- Templates: file picker numa pasta definida em `config.yaml`
- Output: `mapeamento.md`

### CAMADA 3 — TOC Interactivo (tab dedicada)
Visualização e edição da estrutura completa:

- Toggle de visibilidade por elemento (N/A)
- Reordenação (setas ou drag)
- Preview de numeração em tempo real
- Export `estrutura.md` e `mapeamento.md`
- Import `estrutura.md` e `mapeamento.md`
- Botão "Compilar DOCX"

**Nota:** Export/Import funcional desde a primeira iteração da Camada 3.

---

## 5. DOIS FICHEIROS MD — FORMATO

### estrutura.md
Define o documento — reutilizável como template entre projectos.

```markdown
---
doc_type: CTE
doc_title: CTE Fundações e Estruturas
---

# estrutura

## seccao
slug: SEC-I
titulo: Disposições Gerais e Contratuais
tipo: seccao

### heading
slug: LEX
titulo: Léxico e Enquadramento Contratual
nivel: H1
pai: SEC-I

### heading
slug: GERAL
titulo: Disposições Gerais
nivel: H1
pai: SEC-I

## anexo
slug: ANX-GLOS
titulo: Glossário Técnico

## toc
tipo: geral
tipo: figuras
tipo: tabelas
```

### mapeamento.md
Define sources e templates — específico de cada instância/obra.

```markdown
---
doc_id: CTE-SecI
estrutura_ref: estrutura.md
---

# mapeamento

## elemento
slug: LEX
md_source: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/LEX.md"
md_scope: ficheiro_inteiro
template_docx: default

## elemento
slug: GERAL
md_source: "C:/Users/JSJ/JSJ AI/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/GERAL.md"
md_scope: ficheiro_inteiro
template_docx: default

## templates
geral: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"
```

---

## 6. PROTOCOLO DE INTEGRAÇÃO LLM (LLM Guide)

Qualquer agente LLM (Cowork CTE, Cowork MQT, etc.) pode produzir
ficheiros compatíveis com o DOC-ENGINE usando este protocolo.

### Comando: "exportar para JSJDOC"

Quando um agente recebe este comando, produz:

1. `estrutura.md` — com a hierarquia completa do documento
2. `mapeamento.md` — com paths MD reais e templates

O agente conhece a sua própria estrutura e produz os ficheiros
directamente — a app consome sem reconstrução.

### LLM Guide (a criar como ficheiro separado)

Ficheiro: `00_GOVERNO/LLM_GUIDE.md`
Conteúdo: formato exacto de `estrutura.md` e `mapeamento.md`,
regras de slugs, como referenciar headings parciais vs ficheiro inteiro.

**Este ficheiro é o contrato de interface entre projectos e o DOC-ENGINE.**
Qualquer projecto JSJ que queira integrar com o DOC-ENGINE lê este ficheiro.

---

## 7. FUNÇÃO SNAPSHOT

Congela o estado do documento numa pasta escolhida pelo utilizador,
sem tocar nos ficheiros originais.

### Estrutura criada

```
[NomeDocumento]_[YYYY-MM-DD]\
├── ESTRUTURA\
│   ├── estrutura.md
│   └── mapeamento.md
│
└── MDS\
    ├── [Modo A] ficheiros MD copiados tal como estão
    └── [Modo B] MD divididos por heading escolhido
```

### Dois modos de cópia de MD

| Modo | Comportamento |
|------|--------------|
| A — Ficheiro inteiro | Copia cada MD tal como está — 1 ficheiro por secção |
| B — Dividir por Heading | Divide ao nível escolhido (H1/H2/H3/H4) — cada heading com filhos incluídos |

**Regra Modo B:** se dividir ao nível H2, o ficheiro do H2 contém
todos os H3 e H4 filhos. Não explode para além do nível escolhido.

### Nomeação dos ficheiros (Modo B)

```
[ordem]_[slug]_[titulo-truncado].md
ex: 01_LEX_Lexico-Enquadramento.md
    02_GERAL_Disposicoes-Gerais.md
    02-01_GERAL-H2_Ambito.md
```

### Comportamento

- Utilizador escolhe pasta destino (file picker)
- Utilizador escolhe modo A ou B
- Se modo B: escolhe nível de divisão (H1/H2/H3/H4)
- App cria pasta com nome + data
- Nunca toca nos ficheiros originais
- Repetível — cada snapshot é independente

---

## 8. PIPELINE COMPLETA ACTUALIZADA

```
config.yaml (multi-projecto)
        │
        ▼
app.py abre → escolha de projecto
        │
        ▼
estrutura.md + mapeamento.md (auto-load ou import)
        │
        ├── Camada 1: editor de estrutura → estrutura.md
        ├── Camada 2: mapeamento sources + templates → mapeamento.md
        ├── Camada 3: TOC interactivo + export/import + snapshot
        │
        └── "Compilar" →
                compile.py
                    ├── lê mapeamento.md
                    ├── lê MD de cada elemento
                    ├── preprocessor.py ({{ excel }} → tabelas MD)
                    ├── concatena MD processado
                    └── Pandoc → DOCX (template geral ou por elemento)
                            └── 03_OUTPUT\
```

---

## 9. ESTRUTURA 04_APP ACTUALIZADA

```
04_APP\
├── app.py              ← UI Streamlit (3 camadas + snapshot)
├── compile.py          ← orquestrador de compilação
├── preprocessor.py     ← tags {{ excel }} → tabelas MD
├── config.yaml         ← multi-projecto + paths defaults
├── requirements.txt
└── venv\
```

Ficheiros por projecto (fora de 04_APP, paths em config.yaml):
- `estrutura.md`   ← definição do documento (Camada 1)
- `mapeamento.md`  ← sources MD + templates (Camada 2)

---

## 10. FUTURO SUPABASE

A arquitectura de ficheiros MD migra directamente para tabelas:

| Ficheiro MD | Tabela Supabase |
|-------------|----------------|
| `estrutura.md` | `document_templates` |
| `mapeamento.md` | `document_sections` + `project_chapters` |
| `config.yaml` (projectos) | `projects` |

Fora do scope MVP — decisão tomada para garantir compatibilidade futura.

---

## 11. ORDEM DE DESENVOLVIMENTO

1. **Camada 3** — TOC interactivo com dados mock + export/import funcional
2. **Camada 1** — Editor de estrutura (alimenta Camada 3)
3. **Camada 2** — Mapeamento MD sources + templates
4. **Snapshot** — Função de cópia após Camadas 1+2 estarem estáveis
5. **Integração** — compile.py → output DOCX real
6. **LLM Guide** — depois da estrutura de ficheiros estar validada

---

## 12. TAREFAS PARA O COWORK

### 12.1 Arquivar versão anterior
Mover `00_GOVERNO/DECISAO-APP-STREAMLIT.md` para
`00_GOVERNO/Arquivo/DECISAO-APP-STREAMLIT-v1.md`

### 12.2 Actualizar ARQUITECTURA.md
- Substituir secção "4. ARQUITECTURA DO SISTEMA" com pipeline de §8
- Substituir estrutura 04_APP com §9
- Adicionar secção "CAMADAS DA APP" com §4
- Adicionar secção "FICHEIROS POR PROJECTO" com §5 (formato dos MD)
- Actualizar tabela de decisões:
  - D6: Multi-projecto via config.yaml (escolha na abertura da app)
  - D7: App stateless — estrutura.md + mapeamento.md como continuidade
  - D8: Snapshot sem tocar em originais (Modo A ficheiro inteiro / Modo B por heading com filhos)
  - D9: LLM Guide como contrato de interface entre projectos
  - D10: Supabase — fora do scope MVP, arquitectura compatível

### 12.3 Actualizar ROADMAP.md
Substituir FASE 2 por:

```
## FASE 2 — App Streamlit  ⏳ ← ACTUAL

- [ ] Camada 3: TOC interactivo com dados mock
- [ ] Camada 3: Export/Import estrutura.md e mapeamento.md (obrigatório desde início)
- [ ] Camada 3: Preview numeração em tempo real
- [ ] Camada 3: Toggle N/A + reordenação
- [ ] Camada 1: Editor de estrutura do documento
- [ ] Camada 2: Mapeamento MD sources + templates DOCX
- [ ] Função Snapshot (Modo A + Modo B com divisão por heading)
- [ ] Integração: app.py → compile.py → DOCX real
- [ ] config.yaml multi-projecto + auto-load

## FASE 3 — LLM Guide e Integração entre Projectos  ⏳
- [ ] LLM_GUIDE.md (contrato de interface)
- [ ] Comando "exportar para JSJDOC" nos projectos Cowork JSJ
- [ ] Teste de integração CTE → DOC-ENGINE

## FASE 4 — Supabase  ⏳
- [ ] Migração config.yaml → tabela projects
- [ ] Migração estrutura.md → document_templates
- [ ] Migração mapeamento.md → document_sections + project_chapters
```

### 12.4 Actualizar README.md
- Actualizar secção "Estrutura de Pastas" — adicionar nota sobre
  ficheiros por projecto (estrutura.md + mapeamento.md) fora de 04_APP
- Actualizar "Arranque Rápido" — mencionar escolha de projecto no arranque

### 12.5 Actualizar SYSTEM_PROMPT.md
- Adicionar conhecimento sobre estrutura.md e mapeamento.md
- Adicionar LLM Guide como ficheiro futuro em 00_GOVERNO
- Actualizar estrutura 04_APP
- Adicionar à secção "O QUE É":
  "Multi-projecto: config.yaml define múltiplos documentos,
  utilizador escolhe qual carregar no arranque."

### 12.6 Criar pasta Arquivo
Criar `00_GOVERNO/Arquivo/` para versões anteriores de decisões.

### 12.7 Preparar prompt IDE — Camada 3
Após 12.1–12.6 concluídos, preparar prompt IDE para desenvolver
app.py começando pela Camada 3:
- TOC interactivo com dados mock hardcoded
- Export estrutura.md e mapeamento.md funcional
- Import estrutura.md e mapeamento.md funcional
- Toggle N/A por elemento
- Reordenação com setas (drag é fase posterior)
- Preview de numeração

---

**Fim — DECISAO-APP-STREAMLIT-v2.md — 2026-04-03**
