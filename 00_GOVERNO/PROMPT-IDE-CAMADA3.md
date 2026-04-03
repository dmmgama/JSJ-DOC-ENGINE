# PROMPT IDE — JSJ-DOC-ENGINE — Camada 3

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Criar `app.py` — Camada 3 completa (TOC interactivo)
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**

---

## CONTEXTO

**Projecto:** JSJ-DOC-ENGINE — sistema de produção de documentos técnicos JSJ.
Converte Markdown em DOCX via Pandoc com estilos JSJ.
UI Streamlit local, multi-projecto, **stateless entre sessões**.

**Raiz do projecto:** `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\`

**Stack aprovada:**
- Python 3.x + Streamlit
- PyYAML (já em requirements.txt)
- Pandoc (binário standalone, já instalado)
- python-docx (pós-processamento pontual)
- **Não usar:** LangChain, frameworks pesadas, LLMs na pipeline

---

## ESTADO ACTUAL DE `04_APP\`

```
04_APP\
├── compile.py          ✅ funcional — MD → DOCX via Pandoc
├── preprocessor.py     ✅ funcional — tags {{ excel }} → tabelas MD
├── config.yaml         ⚠️ schema antigo (single-projecto) — a substituir
├── requirements.txt    ✅ existente
└── venv\               ✅ existente
```

**`app.py` não existe ainda.** A criar nesta tarefa.

---

## TAREFA

Criar `04_APP\app.py` com a **Camada 3 completa**:

### 3.1 — Dados mock hardcoded

No arranque, a app carrega uma estrutura mock em memória (não lê ficheiros reais ainda).
O mock deve representar um CTE típico com:

```python
# Exemplo de estrutura mock
elementos = [
    {"slug": "LEX",   "titulo": "Léxico e Enquadramento Contratual", "nivel": "H1", "pai": "SEC-I", "incluir": True,  "ordem": 1},
    {"slug": "GERAL", "titulo": "Disposições Gerais",                 "nivel": "H1", "pai": "SEC-I", "incluir": True,  "ordem": 2},
    {"slug": "MAT",   "titulo": "Materiais",                          "nivel": "H1", "pai": "SEC-II","incluir": True,  "ordem": 3},
    {"slug": "EXEC",  "titulo": "Execução de Trabalhos",              "nivel": "H1", "pai": "SEC-II","incluir": True,  "ordem": 4},
    {"slug": "DIAG",  "titulo": "Diagnóstico",                        "nivel": "H1", "pai": "SEC-II","incluir": False, "ordem": 5},
    {"slug": "ANX-GLOS", "titulo": "Glossário Técnico",               "nivel": "ANX","pai": None,    "incluir": True,  "ordem": 6},
]
```

### 3.2 — TOC interactivo

Renderizar a lista de elementos como tabela/lista com:

| Coluna | Conteúdo |
|--------|---------|
| Ordem | Número gerado dinamicamente (só elementos com `incluir=True`) |
| Slug | Identificador |
| Título | Nome do elemento |
| N/A | Checkbox — toggle `incluir` True/False |
| ↑ ↓ | Botões de reordenação (trocar posição com elemento anterior/seguinte) |

**Regras de numeração:**
- Só elementos com `incluir=True` recebem número
- Numeração é sequencial: 1, 2, 3...
- Elementos com `incluir=False` mostram "—" na coluna Ordem
- Numeração recalculada automaticamente após qualquer toggle ou reordenação

### 3.3 — Export `estrutura.md`

Botão "Exportar estrutura.md" que gera o ficheiro no path definido em `config.yaml`
(campo `estrutura` do projecto activo) ou, se não definido, pede path via `st.text_input`.

**Formato de saída `estrutura.md`:**

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
incluir: true
ordem: 1

### heading
slug: GERAL
titulo: Disposições Gerais
nivel: H1
pai: SEC-I
incluir: true
ordem: 2

### heading
slug: DIAG
titulo: Diagnóstico
nivel: H1
pai: SEC-II
incluir: false
ordem: 5

## anexo
slug: ANX-GLOS
titulo: Glossário Técnico
incluir: true
ordem: 6
```

### 3.4 — Import `estrutura.md`

Botão "Importar estrutura.md" + `st.file_uploader` (aceita `.md`).
Ao importar:
1. Faz parse do ficheiro
2. Substitui o estado em memória
3. Re-renderiza o TOC

**Parser deve ser robusto:** ignorar linhas desconhecidas sem falhar.

### 3.5 — Export `mapeamento.md`

Botão "Exportar mapeamento.md".
Nesta fase, gerar um mapeamento com placeholders para os campos que ainda não existem (md_source, template_docx).

**Formato de saída `mapeamento.md`:**

```markdown
---
doc_id: CTE-SecI
estrutura_ref: estrutura.md
---

# mapeamento

## elemento
slug: LEX
md_source: ""
md_scope: ficheiro_inteiro
template_docx: default

## elemento
slug: GERAL
md_source: ""
md_scope: ficheiro_inteiro
template_docx: default

## templates
geral: ""
```

Só incluir elementos com `incluir=True`.

### 3.6 — Import `mapeamento.md`

Botão "Importar mapeamento.md" + `st.file_uploader`.
Ao importar: fazer parse e guardar em memória (usado em fases futuras pelas Camadas 1 e 2).

### 3.7 — Botão "Compilar DOCX" (stub)

Botão visível mas desactivado (`st.button(..., disabled=True)`) com tooltip:
`"Disponível após configurar mapeamento (Camada 2)"`

---

## ESTRUTURA DA APP

```
st.set_page_config(layout="wide")

# Sidebar: info do projecto activo (nome, id) + botões import/export
# Main: TOC interactivo (tabela com toggle N/A + setas)
# Footer: botão Compilar DOCX (stub)
```

Usar `st.session_state` para:
- `elementos` — lista de dicts (estado do TOC)
- `mapeamento` — dict (importado de mapeamento.md, vazio por defeito)
- `projecto_activo` — dict com id, name (mock por agora)

---

## RESTRIÇÕES

- **Nunca criar ficheiros fora de `04_APP\`**
- **Não modificar** `compile.py`, `preprocessor.py`, `requirements.txt`
- Não introduzir dependências novas sem avisar (o que está em requirements.txt é suficiente para esta tarefa)
- Comentar código em **português**
- Funções curtas com responsabilidade única
- Não usar `st.experimental_rerun()` (deprecated) — usar `st.rerun()`
- Não usar drag-and-drop (fase posterior) — apenas setas ↑ ↓
- Parser de `estrutura.md` e `mapeamento.md` deve ser tolerante a falhas (ignorar campos desconhecidos)

---

## VERIFICAÇÃO

A tarefa está concluída quando:

1. `streamlit run app.py` arranca sem erros
2. TOC mock é visível com 6 elementos
3. Toggle N/A funciona: desactivar um elemento remove-o da numeração em tempo real
4. Setas ↑ ↓ reordenam elementos correctamente
5. "Exportar estrutura.md" gera ficheiro com o formato especificado em §3.3
6. "Importar estrutura.md" lê o ficheiro exportado e re-renderiza o TOC sem erros
7. "Exportar mapeamento.md" gera ficheiro com o formato especificado em §3.5
8. "Importar mapeamento.md" lê sem erros
9. Botão "Compilar DOCX" está visível mas desactivado

---

## ENTREGÁVEL

Ficheiro único criado ou modificado:

| Path | Estado esperado |
|------|----------------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ criado e funcional |

Após concluir, actualizar `04_APP\README.md` secção 10 (Estado Actual):
- `app.py` → ✅ Camada 3 funcional (TOC interactivo, export/import estrutura.md + mapeamento.md)

---

**Fim — PROMPT-IDE-CAMADA3.md — 2026-04-03**
