# DECISÃO — Mudança de MD para YAML nos ficheiros de estrutura

> **Data:** 2026-04-03
> **Decisor:** David Gama
> **Estado:** FECHADA
> **Impacto:** ARQUITECTURA.md, ROADMAP.md, SYSTEM_PROMPT.md, 04_APP\README.md

---

## 1. CONTEXTO E PROBLEMA

Durante os primeiros testes da app Streamlit (Camada 3), o import
do `estrutura.md` falhou — o parser retornou "Nenhum elemento encontrado".

**Causa raiz:** O ficheiro `estrutura.md` usava blocos Markdown com
campos `key: value` dentro de cada bloco. O parser foi escrito para
um formato diferente. Qualquer mudança de convenção quebrava o parser.

**Problema estrutural identificado:** Markdown não é um formato de
dados — é um formato de apresentação. Usá-lo como ficheiro de
configuração obriga a escrever um parser custom frágil que quebra
com qualquer variação de formatação.

---

## 2. DECISÃO

**Mudar `estrutura.md` e `mapeamento.md` para `estrutura.yaml`
e `mapeamento.yaml`.**

YAML é o formato canónico para ficheiros de configuração hierárquicos
em pipelines docs-as-code. É o que a comunidade usa. É o que o
ecossistema Python parseia nativamente com `yaml.safe_load()` — uma
linha de código, sem parser custom.

---

## 3. PORQUÊ YAML — ARGUMENTOS

| Critério | YAML | MD com blocos |
|----------|------|---------------|
| Parse Python | `yaml.safe_load()` — 1 linha, nativo | Parser custom — frágil, quebra com variações |
| Hierarquia | `filhos:` — explícita e inequívoca | Implícita no marcador — ambígua |
| Extensível | Novo campo = nova chave YAML | Novo campo = risco de quebrar parser |
| Alinhado com Pandoc | ✅ nível numérico directo (`nivel: 1`) | ⚠️ marcador MD (`##`) confunde hierarquia de conteúdo com hierarquia de estrutura |
| Legível por LLM | ✅ | ✅ |
| Standard comunidade | ✅ padrão docs-as-code | ❌ não standard |

---

## 4. O QUE CADA FICHEIRO FAZ

### `estrutura.yaml` — o esqueleto do documento
Responde a: *"O que compõe este documento e em que ordem?"*

Não tem conteúdo. Tem apenas a lista de elementos, hierarquia,
e se estão incluídos ou não. É o TOC da app.

```yaml
doc_type: CTE
doc_title: CTE Fundações e Estruturas

elementos:
  - slug: SEC-I
    titulo: Disposições Gerais e Contratuais
    tipo: seccao
    display_order: 1
    include: true
    filhos:
      - slug: LEX
        titulo: Léxico e Enquadramento Contratual
        tipo: heading
        nivel: 1
        display_order: 1.1
        include: true
        filhos:
          - slug: LEX-1
            titulo: Léxico Anti-Ambiguidade
            tipo: heading
            nivel: 2
            display_order: 1.1.1
            include: true
```

**Quem usa:** app Streamlit — TOC, toggles N/A, reordenação.

### `mapeamento.yaml` — as ligações ao conteúdo real
Responde a: *"Para cada elemento, onde está o MD e qual o template DOCX?"*

```yaml
doc_id: CTE-SecI
estrutura_ref: estrutura.yaml

templates:
  geral: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"

elementos:
  - slug: LEX
    md_source: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/02_CONTRATUAL/LEX.md"
    md_scope: ficheiro_inteiro
    template_docx: default

  - slug: MAT-MAD
    md_source: ""
    md_scope: ficheiro_inteiro
    template_docx: default
    nota: MD não produzido ainda — N/A por defeito
```

**Quem usa:** `compile.py` — sabe o que compilar e de onde.

---

## 5. FLUXO COMPLETO ACTUALIZADO

```
estrutura.yaml              mapeamento.yaml
      │                           │
      ▼                           ▼
  app.py                    compile.py
  (TOC, toggles N/A,        (lê md_source por slug,
   reordenação,              agrega MD ordenado,
   preview numeração)        injjecta nível heading,
      │                      preprocessor.py,
      │                      Pandoc → DOCX)
      │                           │
      └──── "Compilar" ───────────┘
                    ↓
                 DOCX final
```

**Ligação entre os dois ficheiros:** `estrutura.yaml` define a ordem
e inclusão. `mapeamento.yaml` define o conteúdo. O `compile.py` junta
os dois: para cada slug incluído em `estrutura.yaml` (ordenado por
`display_order`), lê o `md_source` do `mapeamento.yaml`.

---

## 6. ONDE VIVEM OS FICHEIROS

Junto do projecto-fonte — não dentro de `04_APP\`:

```
CTE-TEMPLATE-CLAUDE\
├── estrutura.yaml     ← hierarquia do CTE
└── mapeamento.yaml    ← sources MD + templates
```

Os paths são registados no `config.yaml` da app:

```yaml
projects:
  - id: CTE-SecI
    name: "CTE Fundações e Estruturas"
    estrutura: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/estrutura.yaml"
    mapeamento: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/mapeamento.yaml"
```

---

## 7. IMPACTO NO DESENVOLVIMENTO

### O que muda no IDE
- `parse_estrutura_md()` → substituir por `parse_estrutura_yaml()`
  usando `yaml.safe_load()` — sem parser custom
- `gerar_estrutura_md()` → substituir por `gerar_estrutura_yaml()`
- `parse_mapeamento_md()` → substituir por `parse_mapeamento_yaml()`
- Adicionar `pyyaml` ao `requirements.txt` se não estiver já

### O que não muda
- Lógica de TOC, toggles, reordenação — só o parser muda
- `compile.py` — a interface slug→md_source mantém-se
- `preprocessor.py` — não afectado
- Pandoc — não afectado

---

## 8. TAREFAS PARA O COWORK

### 8.1 Actualizar ARQUITECTURA.md

Na secção "FICHEIROS DE TRABALHO POR DOCUMENTO", substituir:

| Ficheiro | Conteúdo | Scope |
|----------|----------|-------|
| `estrutura.yaml` | Hierarquia do documento (tipo, secções, headings H1-H4, anexos) em YAML | Template reutilizável entre projectos |
| `mapeamento.yaml` | MD source + template DOCX por elemento em YAML | Específico de cada instância/obra |

Adicionar nota:
> Formato YAML escolhido sobre Markdown por ser parseável nativamente
> em Python (`yaml.safe_load()`), sem parser custom. Standard da
> comunidade docs-as-code para ficheiros de configuração hierárquicos.

Na secção "DECISÕES DE ARQUITECTURA", adicionar:

| D11 | Formato ficheiros de estrutura | YAML puro (`estrutura.yaml`, `mapeamento.yaml`) | MD com blocos key:value — frágil, não standard |

### 8.2 Actualizar SYSTEM_PROMPT.md

Na secção "FICHEIROS DE TRABALHO POR DOCUMENTO", substituir
referências a `.md` por `.yaml`:

| Ficheiro | Conteúdo | Scope |
|----------|----------|-------|
| `estrutura.yaml` | Hierarquia do documento em YAML | Template reutilizável |
| `mapeamento.yaml` | MD sources + templates DOCX em YAML | Específico de cada obra |

Actualizar nota:
> Estes ficheiros são produzidos e consumidos pela app.py.
> Os paths são definidos em `config.yaml`.
> Formato YAML — parseável com `yaml.safe_load()`, sem parser custom.
> Nunca editar manualmente — gerados/exportados pela Camada 3 da app.

### 8.3 Actualizar 04_APP\README.md

Na secção "5. FICHEIROS EXTERNOS", substituir:

| Ficheiro | Conteúdo |
|----------|---------|
| `estrutura.yaml` | Hierarquia do documento (tipo, secções, headings, anexos) |
| `mapeamento.yaml` | MD sources + templates DOCX por elemento |

Adicionar nota no fim da secção:
> Formato YAML — Python parseia com `yaml.safe_load()`.
> Gerados e exportados pela app — não editar manualmente.

Na secção "4. FICHEIROS DESTA PASTA", actualizar descrição de `app.py`:
> `app.py` — UI Streamlit — lê `estrutura.yaml`, `mapeamento.yaml`

Na secção "8. PIPELINE DE COMPILAÇÃO", substituir referências
a `estrutura.md` e `mapeamento.md` por `estrutura.yaml` e `mapeamento.yaml`.

### 8.4 Preparar prompt IDE

Após 8.1–8.3 concluídos, preparar prompt IDE com:

```
## CONTEXTO
Stack: Python + Streamlit + Pandoc + PyYAML
Pasta de trabalho: 04_APP\
Ficheiros de estrutura mudaram de .md para .yaml

## ESTADO ACTUAL
app.py tem parser para .md que falhou nos testes.
Decisão tomada: migrar para YAML puro.
Ficheiros yaml de teste disponíveis em:
- C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\estrutura.yaml
- C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\mapeamento.yaml

## TAREFA
1. Substituir parse_estrutura_md() por parse_estrutura_yaml()
   usando yaml.safe_load() — sem parser custom
   O YAML tem estrutura hierárquica com campo "filhos" para
   elementos aninhados (secções → headings → sub-headings)

2. Substituir gerar_estrutura_md() por gerar_estrutura_yaml()

3. Substituir parse_mapeamento_md() por parse_mapeamento_yaml()

4. Verificar que pyyaml está em requirements.txt
   Se não estiver: pip install pyyaml e actualizar requirements.txt

5. Testar import do estrutura.yaml real — deve carregar todos
   os elementos sem erros

## RESTRIÇÕES
- Não alterar lógica de TOC, toggles, reordenação
- Não alterar compile.py nem preprocessor.py
- Comentar em português

## VERIFICAÇÃO
Import de estrutura.yaml carrega ~60 elementos sem erros.
TOC da app mostra hierarquia completa do CTE.

## ENTREGÁVEL
- 04_APP\app.py actualizado (parsers YAML)
- 04_APP\requirements.txt com pyyaml
```

### 8.5 Apagar ficheiros MD obsoletos

Após IDE confirmar que YAML funciona, apagar do CTE-TEMPLATE-CLAUDE:
- `estrutura.md` ← substituído por `estrutura.yaml`
- `mapeamento.md` ← substituído por `mapeamento.yaml`

Não apagar antes — manter como referência durante a migração.

---

## 9. NOTA PARA SESSÕES FUTURAS

Sempre que se falar em "ficheiro de estrutura" ou "ficheiro de
mapeamento" neste projecto — é YAML, não MD.

Se alguém (LLM ou humano) sugerir usar MD para configuração
de estrutura → recusar. A decisão está fechada (D11).

---

**Fim — DECISAO-YAML-ESTRUTURA.md — 2026-04-03**
