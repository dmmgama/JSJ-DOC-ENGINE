# RELATÓRIO DE REORGANIZAÇÃO — JSJ-DOC-ENGINE
## 2026-04-03 | Cowork Governo

---

## RESUMO EXECUTIVO

✅ **Estrutura de pastas criada e validada.**
✅ **Ficheiros de governo movidos para 00_GOVERNO\.**
✅ **DRs arquivados em 01_AUDITORIAS\RESEARCH\.**
✅ **SYSTEM_PROMPT.md criado em 00_GOVERNO\.**
✅ **.gitignore criado na raiz.**
⚠️ **reference.docx JSJ ainda não copiado** — via CTE-TEMPLATE-CLAUDE (fora do workspace atual).

**Estado:** Estrutura de pastas **100% operacional**. Pronto para Phase 1 MVP.

---

## CHECKLIST DETALHADO

### 1. CRIAR PASTAS ✅

| Pasta | Path | Status |
|-------|------|--------|
| `00_GOVERNO` | `/00_GOVERNO/` | ✅ |
| `01_AUDITORIAS` | `/01_AUDITORIAS/` | ✅ |
| `02_TEMPLATES` | `/02_TEMPLATES/` | ✅ |
| `03_OUTPUT` | `/03_OUTPUT/` | ✅ |
| `04_APP` | `/04_APP/` | ✅ |

### 2. MOVER FICHEIROS PARA 00_GOVERNO ✅

| Ficheiro | De | Para | Status |
|----------|----|----|--------|
| ARQUITECTURA.md | `/ ` | `/00_GOVERNO/ARQUITECTURA.md` | ✅ |
| ROADMAP.md | `/` | `/00_GOVERNO/ROADMAP.md` | ✅ |
| ESTRUTURA_PASTAS.md | `/` | `/00_GOVERNO/ESTRUTURA_PASTAS.md` | ✅ |
| SYSTEM_PROMPT.md (novo) | — | `/00_GOVERNO/SYSTEM_PROMPT.md` | ✅ Criado |

### 3. MANTER NA RAIZ ✅

| Ficheiro | Path | Status |
|----------|------|--------|
| README.md | `/README.md` | ✅ Mantido |

### 4. PROCESSAR PASTA RESEARCH ✅

| Item | De | Para | Status |
|------|----|----|--------|
| Pasta RESEARCH | `/RESEARCH/` | `/01_AUDITORIAS/RESEARCH/` | ✅ |

**Conteúdo de `/01_AUDITORIAS/RESEARCH/`:**

| Ficheiro | Descrição | Status |
|----------|-----------|--------|
| `DR-Gemini-DocEngine-2026-04-03.md` | Pesquisa técnica via Gemini — stack docs-as-code, Pandoc, Supabase schema. Recomendação: Markdown modular + Pandoc + Supabase. | ✅ Arquivado |
| `DR-Perplexity-DocEngine-2026-04-03.md` | Pesquisa via Perplexity — padrões docs-as-code, pipeline Markdown→DOCX, schema relacional. Conclusão: **Opção B** (Supabase + UI custom + Pandoc). | ✅ Arquivado |

### 5. CRIAR .GITIGNORE ✅

| Item | Conteúdo | Status |
|------|----------|--------|
| .gitignore | venv/, 03_OUTPUT/, __pycache__/, *.pyc, .env, *.docx | ✅ Criado |

### 6. COPIAR reference.docx ⚠️

| Item | De | Para | Status |
|------|----|----|--------|
| JSJ-CTE-reference.docx | `C:\Users\JSJ\JSJ AI\CTE-TEMPLATE-CLAUDE\JSJ-Brand\000-EST-MDJ-PE-E00-0.docx` | `/02_TEMPLATES/JSJ-CTE-reference.docx` | ⚠️ **Pendente** |

**Motivo:** CTE-TEMPLATE-CLAUDE está fora do workspace montado. Ficheiro não acessível via Cowork.

**Próximo passo:** Cowork → David → Decisão: (a) Copiar manualmente via Windows ou (b) Fornecer path alternativo.

---

## ESTRUTURA FINAL VALIDADA

```
/sessions/trusting-nifty-franklin/mnt/JSJ-DOC-ENGINE/
├── README.md ✅
├── .gitignore ✅
│
├── 00_GOVERNO/ ✅
│   ├── ARQUITECTURA.md ✅
│   ├── ESTRUTURA_PASTAS.md ✅
│   ├── ROADMAP.md ✅
│   ├── SYSTEM_PROMPT.md ✅ (novo)
│   └── RELATORIO_REORGANIZACAO_2026-04-03.md ✅ (este ficheiro)
│
├── 01_AUDITORIAS/ ✅
│   └── RESEARCH/ ✅
│       ├── DR-Gemini-DocEngine-2026-04-03.md ✅
│       └── DR-Perplexity-DocEngine-2026-04-03.md ✅
│
├── 02_TEMPLATES/ ✅ (vazio — aguarda reference.docx)
│
├── 03_OUTPUT/ ✅ (vazio — para DOCX compilados)
│
└── 04_APP/ ✅ (vazio — aguarda desenvolvimento IDE)
```

---

## RESUMO DE PESQUISA (RESEARCH)

**Ficheiro:** `DR-Gemini-DocEngine-2026-04-03.md`

**BLUF:** Stack state-of-the-art para docs-as-code determinístico assenta em **Pandoc** (motor conversão) + **Python/Node orquestrador** + **Supabase** (SoT) + **React/Next** (UI custom).

**Recomendações chave:**
- Usar `reference.docx` com estilos da empresa como template do Pandoc.
- Schema Supabase com slugs como PKs (primárias), display_order para reordenação.
- Numeração gerada no compile step (Opção B), não embebida em Markdown.
- Rejeitar Docusaurus, Strapi genéricos — inadequados para contratos jurídicos.

**Decisão:** Alinhado com Princípios P1-P5 do projecto.

---

**Ficheiro:** `DR-Perplexity-DocEngine-2026-04-03.md`

**BLUF:** Mercado converge em docs-as-code + Pandoc. Não há solução off-the-shelf que combine Supabase + reorder + auto-numbering + DOCX nativamente. Solução real: composição de peças (backend estruturado + editor custom + Pandoc compiler).

**Recomendação:** **Opção B** — Supabase + UI custom (Tiptap/Markdown) + Pandoc compiler.

- `sections` (slug PK, title, markdown_body, metadata_jsonb)
- `documents` (id PK, template_id, project_id, version)
- `document_sections` (document_id, section_slug, sort_order, include_bool, override_markdown)
- Numeração calculada em memória ou SQL view, nunca persistida no conteúdo.

**Pipeline editorial:**
1. Utilizador escolhe obra/template.
2. UI carrega secções ordenadas por sort_order.
3. Drag-and-drop muda apenas sort_order.
4. Toggle N/A muda include_bool.
5. Preview calcula numeração (1, 1.1, 1.2, 2...) em memória.
6. Compile gera Markdown temporário e passa para Pandoc.

**Decisão:** Alinhado com P2 (maintibilidade) e P3 (MD fonte de verdade).

---

## IMPACTO NA ROADMAP

**Fase 1 (MVP) — Status:** 🟢 **Desbloqueada**

| Item | Antes | Depois |
|------|-------|--------|
| Estrutura de pastas | ❓ Pendente | ✅ Operacional |
| SYSTEM_PROMPT para Cowork | ❌ Não existia | ✅ Criado |
| Contexto de pesquisa | 📄 DRs dispersos | 📂 Arquivados + indexados |
| .gitignore | ❌ Não existia | ✅ Criado |

**Bloqueadores remanescentes para Fase 1:**
- ⚠️ reference.docx em 02_TEMPLATES\ (David decidir)
- Pandoc instalação e teste
- config.yaml (CTE Secção I)
- compile.py funcional

---

## PRÓXIMOS PASSOS

### Imediato (David)
1. Fornecer reference.docx ou path alternativo para copiar.
2. Validar estrutura no Windows Explorer.

### Para Agente IDE
1. Ler `/00_GOVERNO/SYSTEM_PROMPT.md` antes de qualquer desenvolvimento em `04_APP\`.
2. Próximo prompt IDE conterá inicialização de Pandoc + config.yaml.

### Para Cowork (próxima sessão)
1. Confirmar reference.docx copiado.
2. Atualizar ROADMAP.md quando fases avançarem.
3. Documentar decisões em 00_GOVERNO\ conforme necessário.

---

**Relatório criado:** 2026-04-03 23:15 UTC
**Executante:** Cowork Governo JSJ-DOC-ENGINE
**Validação:** Estrutura 100% alinhada com project instructions.
