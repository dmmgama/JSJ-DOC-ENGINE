# ROADMAP — JSJ-DOC-ENGINE

> **Versão:** 1.0 — Abril 2026
> **Estado:** 🟡 MVP em desenvolvimento
> **Documento de referência:** `README.md` (raiz)

---

## FASE 1 — MVP: Compilação MD → DOCX  ⏳ ← ACTUAL

**Objectivo:** Conseguir compilar a Secção I do CTE em DOCX via Pandoc.

- [x] Estrutura de pastas criada
- [x] README + ARQUITECTURA + ROADMAP escritos
- [x] DRs de pesquisa em 01_AUDITORIAS\
- [ ] Pandoc instalado e verificado
- [ ] reference.docx JSJ copiado para 02_TEMPLATES\
- [ ] config.yaml criado para CTE Secção I
- [ ] compile.py funcional (MD → DOCX via Pandoc)
- [ ] preprocessor.py funcional (tags Excel → tabelas MD)
- [ ] Teste: DOCX da Secção I gerado e abrível no Word

**Gate:** DOCX da Secção I compilado, abrível, com estilos JSJ aplicados.

---

## FASE 2 — UI Streamlit  ⏳

**Objectivo:** App local para visualizar estrutura e compilar sem linha de comandos.

- [ ] app.py com árvore de secções
- [ ] Reordenação de secções (setas ou drag)
- [ ] Toggle N/A por secção
- [ ] Preview de numeração em tempo real
- [ ] Botão "Compilar" → chama compile.py
- [ ] Relatório de alterações (para passar ao Cowork CTE)

**Gate:** David consegue compilar um DOCX parcial sem abrir terminal.

---

## FASE 3 — Expansão e Melhorias  ⏳

- [ ] Suporte a outros documentos JSJ (além do CTE)
- [ ] Melhorias ao reference.docx (tabelas, avisos HP/WP, gráficos)
- [ ] Múltiplos config.yaml (um por documento)
- [ ] Supabase como backend (a decidir)

---

## DEPENDÊNCIAS EXTERNAS

| Dependência | Estado | Acção |
|-------------|--------|-------|
| Pandoc instalado | ❓ | Verificar — instalar se necessário |
| reference.docx JSJ | ✅ existe em JSJ-Brand\ | Copiar para 02_TEMPLATES\ |
| MD Secção I CTE | ✅ redigida | Path: CTE-TEMPLATE-CLAUDE\02_CONTRATUAL\ |

---

**Fim — ROADMAP.md v1.0 — 2026-04-03**
