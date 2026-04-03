# DECISÃO — App Agnóstica: Princípios e Implicações

> **Data:** 2026-04-03
> **Decisor:** David Gama
> **Estado:** FECHADA
> **Prioridade:** CRÍTICA — aplicar antes de qualquer desenvolvimento da Camada 1
> **Impacto:** ARQUITECTURA.md, SYSTEM_PROMPT.md, 04_APP\README.md, prompt IDE Camada 1

---

## 1. PROBLEMA IDENTIFICADO

O prompt IDE gerado para a Camada 1 usava terminologia específica
do CTE (MAT/EXEC/DIAG/REP, "obrigatorio") que não faz sentido
numa app agnóstica. A contaminação veio dos ficheiros de teste
criados para o CTE.

**Regra fundamental:** A app não conhece o CTE. Não conhece MAT,
EXEC, DIAG, REP, "vinculativo contratual", nem qualquer conceito
específico de qualquer documento JSJ.

---

## 2. O QUE "AGNÓSTICA" SIGNIFICA NA PRÁTICA

A app conhece apenas conceitos universais de estrutura documental:

| Conceito | O que é | Exemplos reais |
|----------|---------|----------------|
| `documento` | Qualquer doc técnico JSJ | CTE, Memória Descritiva, Relatório |
| `elemento` | Qualquer parte do documento | Secção, capítulo, anexo, índice |
| `slug` | Identificador único do elemento | Definido pelo utilizador — pode não fazer sentido em todos os docs |
| `tipo` | Classificação do elemento | Configurável — ver §3 |
| `nivel` | Profundidade hierárquica (1-4) | Heading 1, 2, 3, 4 |
| `include` | Incluído nesta instância | Toggle N/A |

A app não sabe o que significa "MAT-BET" ou "Vinculativo técnico".
Isso é conhecimento do projecto CTE, não da app.

---

## 3. TIPOS — CONFIGURÁVEIS PELO UTILIZADOR

Os tipos de elemento não são fixos na app. São configuráveis
por documento. A app tem tipos pré-definidos como ponto de partida,
mas o utilizador pode:
- Adicionar tipos novos
- Renomear tipos existentes
- Apagar tipos que não usa

### Tipos pré-definidos (ponto de partida)

| Tipo | Descrição genérica |
|------|-------------------|
| `seccao` | Agrupador de topo — não tem conteúdo próprio |
| `heading` | Elemento com conteúdo — tem nível (1-4) |
| `anexo` | Elemento final, fora da numeração principal |
| `toc` | Índice gerado automaticamente |
| `front_matter` | Elementos antes do corpo (capa, ficha, revisões) |

Estes tipos são sugestões. O utilizador pode apagar "front_matter"
se não fizer sentido no seu documento, ou criar "apendice" se precisar.

---

## 4. SLUG — EXPLICAÇÃO PARA O UTILIZADOR NA APP

O slug é o identificador único e imutável de cada elemento.
Serve para ligar o elemento ao seu conteúdo MD no `mapeamento.yaml`.

**Na app, o slug deve ser explicado assim:**
> "Código único deste elemento. Usado internamente para ligar
> ao ficheiro de conteúdo. Pode ser qualquer texto sem espaços
> (ex: SEC-1, INTRO, ANEXO-A). Não pode ser alterado depois
> de atribuído sem actualizar o mapeamento."

**Slug é opcional em alguns documentos.** Se o utilizador não
usar sistema de mapeamento externo (só quer compilar um MD simples),
o slug pode ser gerado automaticamente pela app (ex: `elem-001`).

---

## 5. REGRA DE COMPORTAMENTO DO COWORK

Quando há dúvida sobre se algo é específico do CTE ou universal:

**Perguntar a David antes de incluir no prompt IDE.**

Formato da pergunta:
```
"[X] faz sentido para qualquer documento JSJ ou só para o CTE?
Se só para o CTE → não entra na app, entra no estrutura.yaml do CTE."
```

Exemplos de conceitos que NÃO entram na app:
- MAT / EXEC / DIAG / REP (taxonomia CTE)
- "Vinculativo contratual / técnico" (linguagem CTE)
- "Hold Point / Witness Point" (conceito CTE)
- "Secção I / II / III" (estrutura CTE)
- "obrigatorio" como campo (conceito CTE)

Exemplos de conceitos que SÃO universais e ENTRAM na app:
- slug, titulo, tipo, nivel, include, display_order
- seccao, heading, anexo, toc, front_matter (tipos base)
- export/import YAML
- toggle N/A
- reordenação
- compilar DOCX

---

## 6. IMPLICAÇÕES NO SCHEMA YAML

O schema agnóstico do `estrutura.yaml` usa apenas campos universais:

```yaml
doc_type: "CTE"           # livre — definido pelo utilizador
doc_title: "..."          # livre

tipos_disponiveis:         # configurável por documento
  - seccao
  - heading
  - anexo
  - toc
  - front_matter

elementos:
  - slug: SEC-I            # identificador único — pode ser qualquer string
    titulo: "..."          # livre
    tipo: seccao           # um dos tipos_disponiveis
    nivel: 1               # 1-4, só relevante para headings
    display_order: 1       # ordem de apresentação
    include: true          # incluído nesta instância
    filhos: [...]          # hierarquia — qualquer profundidade
```

Campos que foram removidos por serem específicos do CTE:
- `nota: Vinculativo contratual` → pertence ao estrutura.yaml do CTE, não ao schema
- tipos MAT/EXEC/DIAG/REP → são slugs CTE, não tipos da app

---

## 7. TAREFAS PARA O COWORK

### 7.1 Actualizar ARQUITECTURA.md

Adicionar secção "AGNOSTICISMO DA APP":

```
## AGNOSTICISMO DA APP

A app não conhece nenhum documento JSJ específico.
Conhece apenas: slug, titulo, tipo, nivel, include, display_order.
Os tipos são configuráveis pelo utilizador por documento.
O slug é o identificador único — pode ser gerado automaticamente.

Qualquer conceito específico de um documento (ex: MAT, EXEC,
"vinculativo") vive nos ficheiros YAML do projecto, não na app.
```

Actualizar P5 (Agnóstico de documento):
```
P5 — Agnóstico de documento
A app não conhece o CTE nem qualquer documento JSJ específico.
Conhece elementos com: slug, titulo, tipo (configurável),
nivel (1-4), include (bool), display_order.
Os tipos são configuráveis por documento — pré-definidos como
ponto de partida, mas editáveis, renomeáveis e apagáveis.
O slug é opcional — pode ser gerado automaticamente pela app.
```

### 7.2 Actualizar SYSTEM_PROMPT.md

Adicionar à secção "REGRAS FUNDAMENTAIS / NUNCA":

```
- Incluir no prompt IDE conceitos específicos do CTE
  (MAT, EXEC, DIAG, REP, "vinculativo", "Hold Point", etc.)
- Assumir que a app conhece a estrutura do CTE
- Quando há dúvida se algo é universal ou CTE → perguntar a David
```

### 7.3 Actualizar 04_APP\README.md

Na secção "7. ARQUITECTURA DA APP — 3 CAMADAS", actualizar Camada 1:

```
CAMADA 1 — Editor de Estrutura do Documento
    Criar/editar/remover elementos de qualquer documento
    Campos universais: slug, titulo, tipo, nivel, include, display_order
    Tipos configuráveis: pré-definidos mas editáveis/apagáveis pelo utilizador
    Slug: identificador único — explicado ao utilizador, pode ser auto-gerado
    Agnóstico: sem referência a CTE, MAT, EXEC ou qualquer doc específico
```

### 7.4 Gerar prompt IDE corrigido para Camada 1

Após 7.1–7.3 concluídos, gerar prompt IDE com estas restrições:

```
## CONTEXTO
App Streamlit agnóstica — não conhece CTE nem qualquer documento específico.
Camada 3 já implementada (TOC interactivo, export/import YAML, toggle N/A).
Schema YAML: slug, titulo, tipo, nivel, display_order, include, filhos.

## TAREFA — Camada 1: Editor de Estrutura
1. UI para criar/editar/remover elementos no estrutura.yaml
2. Campos editáveis: slug (com aviso de imutabilidade), titulo,
   tipo (dropdown dos tipos_disponiveis), nivel (1-4, só para headings),
   display_order, include (bool)
3. Gestão de tipos: UI para adicionar/renomear/apagar tipos disponíveis.
   Tipos pré-definidos: seccao, heading, anexo, toc, front_matter
4. Slug auto-gerado se vazio (ex: elem-001, elem-002)
5. Validação inline: slug único, titulo não vazio
6. Persistência: guardar alterações de volta ao estrutura.yaml
7. Integrar como tab separada da Camada 3 sem a quebrar

## RESTRIÇÕES
- Zero referências a CTE, MAT, EXEC, DIAG, REP, ou qualquer doc específico
- Não alterar schema YAML existente (só adicionar tipos_disponiveis se não existir)
- Streamlit nativo — sem dependências novas
- Comentar em português
```

---

**Fim — DECISAO-AGNOSTICA.md — 2026-04-03**
