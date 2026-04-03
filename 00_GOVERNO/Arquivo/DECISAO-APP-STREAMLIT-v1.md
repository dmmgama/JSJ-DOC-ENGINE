# DECISÃO — Arquitectura da App Streamlit (Fase 2)

> **Data:** 2026-04-03
> **Decisor:** David Gama
> **Estado:** FECHADA
> **Impacto:** ARQUITECTURA.md, ROADMAP.md, SYSTEM_PROMPT.md

---

## 1. CONTEXTO

A Fase 2 do DOC-ENGINE é a UI Streamlit. Esta decisão define
o que a app faz, como está organizada internamente, e quais
os ficheiros que produz e consome.

---

## 2. AS 3 CAMADAS DA APP

A app opera em 3 camadas distintas com responsabilidades separadas:

### CAMADA 1 — Definição do Documento
O utilizador define o que é o documento e como está organizado.

- Tipo de documento (ex: CTE, Memória Descritiva, Relatório)
- Estrutura hierárquica: Secções → Headings H1–H4 → Anexos
- Elementos especiais: TOC geral, TOC de figuras, TOC de tabelas

### CAMADA 2 — Mapeamento de Conteúdo
Para cada elemento da estrutura, o utilizador define:

- Qual ficheiro MD é a fonte (pode cobrir secção inteira ou heading específico)
- Qual template DOCX aplicar (geral ou override por secção)
- Templates DOCX: selecção por ficheiro numa pasta (file picker)

### CAMADA 3 — TOC Interactivo (tab dedicada)
Visualização e edição da estrutura completa:

- Toggle de visibilidade por elemento (N/A)
- Reordenação (setas ou drag)
- Preview de numeração em tempo real
- Export/Import MD
- Botão "Compilar DOCX"

---

## 3. FICHEIROS DE EXPORT/IMPORT

A app produz e consome 2 ficheiros MD distintos:

| Ficheiro | Conteúdo | Uso |
|----------|----------|-----|
| `estrutura.md` | Tipo, hierarquia, elementos do documento | Template reutilizável — importar noutro projecto |
| `mapeamento.md` | MD sources + templates DOCX por elemento | Específico de cada instância/obra |

Os dois ficheiros são independentes e exportáveis/importáveis separadamente.
Exemplo de uso: importar `estrutura.md` do projecto CTE para criar
uma nova instância, depois definir novo `mapeamento.md` para outra obra.

---

## 4. TEMPLATES DOCX

- **Geral:** um `reference.docx` de fallback (em `02_TEMPLATES\`)
- **Override por secção:** o utilizador selecciona um ficheiro DOCX
  diferente para uma secção específica (ex: capa com layout diferente)
- A definição de templates vive no `mapeamento.md`
- File picker: abre selector de ficheiro numa pasta definida em `config.yaml`

---

## 5. PIPELINE COMPLETA (actualizada)

```
estrutura.md + mapeamento.md
        │
        ▼
app.py (Streamlit)
        ├── Camada 1: editor de estrutura do documento
        ├── Camada 2: mapeamento MD sources + templates
        ├── Camada 3: TOC interactivo (toggle, reorder, preview)
        └── botão "Compilar" →
                compile.py
                    ├── lê mapeamento.md
                    ├── lê ficheiros MD de cada elemento
                    ├── passa por preprocessor.py
                    │       └── {{ excel | ... }} → tabelas MD
                    ├── concatena MD processado
                    └── Pandoc → DOCX (template geral ou por secção)
                            └── output em 03_OUTPUT\
```

---

## 6. ESTRUTURA DE FICHEIROS EM 04_APP (actualizada)

```
04_APP\
├── app.py              ← UI Streamlit (3 camadas)
├── compile.py          ← orquestrador de compilação
├── preprocessor.py     ← tags Excel → tabelas MD
├── config.yaml         ← paths, pasta de templates, defaults
├── requirements.txt
└── venv\
```

Ficheiros de trabalho por documento (fora de 04_APP, definidos em config.yaml):
- `estrutura.md`   ← definição do documento
- `mapeamento.md`  ← sources MD + templates por elemento

---

## 7. FUTURO SUPABASE

A arquitectura de ficheiros MD é desenhada para migrar directamente
para tabelas Supabase sem reescrever a lógica:

| Ficheiro MD agora | Tabela Supabase futura |
|-------------------|----------------------|
| `estrutura.md` | `document_templates` |
| `mapeamento.md` | `document_sections` + `project_chapters` |

Esta decisão está tomada mas fora do scope MVP.

---

## 8. TAREFAS PARA O COWORK

### 8.1 Actualizar ARQUITECTURA.md
- Substituir secção "4. ARQUITECTURA DO SISTEMA" com pipeline completa (§5)
- Substituir estrutura de 04_APP com versão actualizada (§6)
- Adicionar secção "CAMADAS DA APP" (§2)
- Adicionar decisão D7 (Supabase futuro — §7) na tabela de decisões

### 8.2 Actualizar ROADMAP.md
- Expandir FASE 2 com as 3 camadas como sub-itens
- Adicionar FASE 3 — Supabase (placeholder)

### 8.3 Actualizar SYSTEM_PROMPT.md
- Adicionar ficheiros `estrutura.md` e `mapeamento.md` ao conhecimento do agente
- Actualizar estrutura de 04_APP

### 8.4 Preparar prompt IDE para app.py
Quando os ficheiros de governo estiverem actualizados, preparar
prompt IDE para desenvolver app.py com as 3 camadas.
Arrancar pela Camada 3 (TOC interactivo) — é a mais visível
e permite validar a estrutura antes de construir as camadas 1 e 2.

---

## 9. ORDEM DE DESENVOLVIMENTO RECOMENDADA

Arrancar pela Camada 3 (TOC interactivo) porque:
- É a mais visível — David vê imediatamente se faz sentido
- Valida a estrutura de dados antes de construir as camadas 1 e 2
- Pode ser testada com dados mock sem precisar das camadas 1 e 2

Sequência:
1. Camada 3 — TOC interactivo com dados mock
2. Camada 1 — Editor de estrutura (alimenta Camada 3)
3. Camada 2 — Mapeamento MD sources + templates
4. Integração compile.py → output DOCX real

---

**Fim — DECISAO-APP-STREAMLIT.md — 2026-04-03**
