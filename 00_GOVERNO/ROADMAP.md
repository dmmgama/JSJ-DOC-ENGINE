# ROADMAP — JSJ-DOC-ENGINE

> **Versão:** 1.4 — Abril 2026
> **Estado:** 🟢 Fase 1 concluída — Fase 2 em curso (Camada 3 ✅)
> **Documento de referência:** `README.md` (raiz)

---

## FASE 1 — MVP: Compilação MD → DOCX  ✅ CONCLUÍDA

**Objectivo:** Conseguir compilar a Secção I do CTE em DOCX via Pandoc.

- [x] Estrutura de pastas criada
- [x] README + ARQUITECTURA + ROADMAP escritos
- [x] DRs de pesquisa em 01_AUDITORIAS\
- [x] Pandoc instalado e verificado (v3.7.0.2)
- [x] reference.docx JSJ copiado para 02_TEMPLATES\
- [x] config.yaml criado para CTE Secção I
- [x] compile.py funcional (MD → DOCX via Pandoc)
- [x] preprocessor.py funcional (tags Excel → tabelas MD)
- [x] Teste: DOCX da Secção I gerado e abrível no Word

**Gate atingido:** DOCX da Secção I compilado, abrível, com estilos JSJ aplicados. ✅

---

## FASE 2 — App Streamlit  🟡 ← ACTUAL

**Objectivo:** App local para visualizar estrutura e compilar sem linha de comandos.

**Arquitectura:** 3 camadas + ficheiros `estrutura.yaml` / `mapeamento.yaml` + multi-projecto
→ Detalhe completo: `00_GOVERNO/ARQUITECTURA.md §4a` | Decisão: `DECISAO-APP-STREAMLIT-v2.md`

- [x] Camada 3: TOC interactivo com dados mock hardcoded
- [x] Camada 3: Export/Import `estrutura.yaml` e `mapeamento.yaml`
- [x] Camada 3: Preview de numeração em tempo real
- [x] Camada 3: Toggle N/A + reordenação com setas
- [ ] Camada 1: Editor de estrutura do documento
- [ ] Camada 2: Mapeamento MD sources + templates DOCX
- [ ] Função Snapshot (Modo A ficheiro inteiro + Modo B divisão por heading com filhos)
- [ ] Integração: app.py → compile.py → DOCX real
- [ ] config.yaml multi-projecto + auto-load no arranque

**Gate:** David consegue compilar um DOCX parcial sem abrir terminal.

---

## FASE 3 — LLM Guide e Integração entre Projectos  ⏳

**Objectivo:** Protocolo de integração entre projectos Cowork JSJ e o DOC-ENGINE.

- [ ] `LLM_GUIDE.md` — contrato de interface (formato estrutura.yaml + mapeamento.yaml, regras de slugs)
- [ ] Comando "exportar para JSJDOC" implementado nos projectos Cowork JSJ
- [ ] Teste de integração: CTE-TEMPLATE-CLAUDE → DOC-ENGINE

---

## FASE 4 — Backend Supabase  ⏳

**Objectivo:** Substituir ficheiros MD por tabelas Supabase sem reescrever lógica.

| Ficheiro MD agora | Tabela Supabase futura |
|-------------------|----------------------|
| `config.yaml` (projectos) | `projects` |
| `estrutura.yaml` | `document_templates` |
| `mapeamento.yaml` | `document_sections` + `project_chapters` |

- [ ] Migração config.yaml → tabela `projects`
- [ ] Migração estrutura.yaml → `document_templates`
- [ ] Migração mapeamento.yaml → `document_sections` + `project_chapters`

---

## DEPENDÊNCIAS EXTERNAS

| Dependência | Estado | Acção |
|-------------|--------|-------|
| Pandoc instalado | ✅ v3.7.0.2 | — |
| reference.docx JSJ | ✅ em 02_TEMPLATES\ | — |
| MD Secção I CTE | ✅ redigida | Path: CTE-TEMPLATE-CLAUDE\02_CONTRATUAL\ |

---

**Fim — ROADMAP.md v1.4 — 2026-04-03**
