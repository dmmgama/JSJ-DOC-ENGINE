# ROADMAP — JSJ-DOC-ENGINE

> **Versão:** 1.8 — Abril 2026
> **Estado:** 🟢 Fase 1 concluída — Fase 2 em curso (Camada 3 ✅, D11 YAML ✅, Camada 1 ✅, D12 schema v2 + Lua filter ⏳ prompt IDE pronto)
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
- [x] Migração parsers MD → YAML (D11) — `parse_estrutura_yaml()`, `parse_mapeamento_yaml()` — testado com 68 elementos ✅
- [x] Camada 1: Editor de estrutura do documento
- [ ] **Schema v2** (D12): `semantic_type` + `behavior` + `section_role` inferido + Lua filter + migração v1→v2
      → Prompt IDE: `PROMPT-IDE-SCHEMA-V2.md` | Decisão: `DECISAO-SCHEMA-V2.md`
      → Entregas: `semantic_type_registry.py`, `migrate_schema_v1_to_v2.py`, `filters/pagebreak.lua`, compile.py actualizado
- [ ] Migração manual `estrutura.yaml` CTE → v2 (executar `migrate_schema_v1_to_v2.py`)
- [ ] config.yaml multi-projecto + auto-load no arranque → Prompt IDE: `PROMPT-IDE-CONFIG-YAML.md`
- [ ] `variaveis.yaml` por projecto + substituição `{{ VARIAVEL }}` no preprocessor.py  *(depende do config.yaml multi-projecto)*
- [ ] Camada 2: Mapeamento MD sources + templates DOCX → Prompt IDE: `PROMPT-IDE-CAMADA2-MVP.md`
- [ ] Camada 1 v2: `semantic_type` + editor `behavior` por elemento → Prompt IDE: `PROMPT-IDE-CAMADA1-V2.md`
- [ ] Função Snapshot (Modo A ficheiro inteiro + Modo B divisão por heading com filhos)
- [ ] Integração: app.py → compile.py → DOCX real

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

---

## DETALHE CAMADA 1 (implementado 2026-04-03)

Funções auxiliares em `app.py`:

| Função | Responsabilidade |
|--------|-----------------|
| `_obter_tipos(raw)` | Lê `tipos_disponiveis` do YAML ou usa os pré-definidos |
| `_todos_slugs(lista)` | Recolhe recursivamente todos os slugs (incluindo filhos) |
| `_auto_slug(lista)` | Gera slug único `elem-001`, `elem-002`, … |
| `_elemento_vazio(slug)` | Cria elemento novo com valores por defeito |
| `_validar_elementos(lista)` | Detecta slugs duplicados e títulos vazios |
| `_renderizar_formulario_elemento(...)` | Formulário inline por elemento (6 colunas) |
| `_renderizar_elemento(...)` | Expander por elemento + botões Filho/Remover + recursão |
| `_renderizar_lista_elementos(...)` | Itera a lista e delega para `_renderizar_elemento` |
| `_carregar_estrutura_yaml_ficheiro(path)` | Lê e faz parse do YAML do disco |
| `_guardar_estrutura_yaml_ficheiro(path, dict)` | Serializa e escreve de volta ao disco |

Estado de sessão adicionado (sem conflito com Camada 3):
- `estrutura_yaml_raw` — dict raw do YAML carregado
- `estrutura_yaml_path` — path do ficheiro activo
- `confirmar_remover` — flag de confirmação de remoção

Layout: `st.tabs(["TOC / Compilar", "Estrutura"])` — TOC é o tab default.

Tab "Estrutura": carregar ficheiro → metadados → tipos disponíveis (adicionar/renomear/apagar) → lista de elementos hierárquica editável → validação inline → guardar.

---

**Fim — ROADMAP.md v1.8 — 2026-04-03**
