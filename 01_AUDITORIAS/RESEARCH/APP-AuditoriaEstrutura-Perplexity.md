<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Estou a desenvolver um sistema local de produção de documentos técnicos de engenharia estrutural chamado JSJ-DOC-ENGINE.

## O que o sistema faz

Converte ficheiros Markdown em DOCX via Pandoc, com estilos JSJ aplicados através de um reference.docx. Tem uma UI em Streamlit local (sem deploy, sem servidor). É agnóstico de documento — não é específico de nenhum tipo de documento.

## Stack

- Python 3.x + PyYAML + Streamlit
- Pandoc (binário standalone, motor de compilação MD → DOCX)
- python-docx (pós-processamento pontual onde Pandoc não chega)
- Ficheiros YAML como fonte de verdade da estrutura
- SEM base de dados, SEM LLMs na pipeline de compilação, SEM frameworks pesadas


## Como está organizado agora

Cada documento tem dois ficheiros YAML:

**estrutura.yaml** — define a hierarquia do documento:

- Metadados (tipo, título, versão, data)
- Lista de elementos com: slug, titulo, tipo, nivel (1-4), include (bool), display_order, filhos[] (recursivo)
- Tipos actuais: front_matter, seccao, heading, toc, anexo, anexos

**mapeamento.yaml** — mapeia cada elemento a:

- md_source (path do ficheiro MD)
- md_scope (ficheiro_inteiro ou heading específico)
- template_docx (default ou override)

A app Streamlit tem:

- Tab "TOC / Compilar": visualização flat do documento com toggle N/A e reordenação
- Tab "Estrutura": editor hierárquico da estrutura (Camada 1 — implementada)
- Camada 2 (a fazer): mapeamento MD sources + templates por elemento
- compile.py: orquestrador que lê mapeamento.yaml, concatena MD processado e chama Pandoc


## O problema que preciso de resolver

Quero enriquecer o modelo de estrutura para suportar comportamentos de paginação, numeração e TOC — sem tornar o sistema desnecessariamente complexo.

A maioria dos documentos tem apenas: capa + TOC + uma secção de texto com numeração seguida + eventualmente anexos. O sistema deve funcionar bem por defeito para este caso simples, e permitir configuração avançada quando necessário.

## Funcionalidades que quero adicionar

1. **Tipologias semânticas hardcoded** — tipos com significado fixo que a app e o Pandoc reconhecem:
    - Capa (sem número, sem TOC, page break antes)
    - TOC geral (gerado pelo Pandoc --toc)
    - TOC de figuras
    - TOC de tabelas
    - Secção (bloco de texto com numeração seguida)
    - Anexo (numeração separada, tipicamente Letras ou Romano)
    - Possivelmente outros que me recomende um especialista em document engineering
2. **Comportamentos por elemento (configuráveis na app, guardados no estrutura.yaml)**:
    - Entra no TOC: sim/não
    - Page break antes: sim/não
    - Section break antes: sim/não (para mudar orientação ou formato de página)
    - Formato de página: A4 vertical (default), A4 horizontal, A3, etc.
    - Tipo de numeração: Árabe (1, 2, 3), Romano minúsculo (i, ii, iii), Romano maiúsculo (I, II, III), Letras (A, B, C)
    - Reinício de numeração: sim/não (ex: Anexos reiniciam em A ou I)
    - Numeração contínua entre secções: sim/não
3. **Defaults inteligentes por tipologia** — ao criar um elemento de tipo "Capa", os defaults já vêm preenchidos correctamente (sem número, sem TOC, page break). O utilizador só configura quando quer override.

## O que preciso que o Gemini responda

Actua como especialista em:

1. Document engineering e organização de documentos técnicos profissionais
2. Pandoc (capabilities reais para controlar paginação, numeração, TOC, secções)
3. Streamlit (padrões de UI para este tipo de editor)

Responde a:

**A) Modelo de dados** — como devo estruturar o schema do estrutura.yaml para suportar estas funcionalidades sem over-engineering? Que campos fazem sentido, quais são redundantes, o que estou a esquecer?

**B) Pandoc capabilities reais** — o que é que o Pandoc consegue fazer nativamente neste domínio (page breaks, section breaks, numeração, TOC parcial, formatos de página diferentes dentro do mesmo documento) e o que requer python-docx como fallback? Quais as limitações reais vs. workarounds comuns?

**C) Tipologias recomendadas** — que tipologias semânticas fazem sentido num document engine para documentos técnicos de engenharia? O que é standard na indústria (ex: DITA, DocBook, LaTeX \\frontmatter) que se aplica aqui, simplificado?

**D) Implementação Streamlit** — como estruturar o UI da tab "TOC / Compilar" para que mostre elementos agrupados por tipo com toggles hierárquicos (ex: toggle "Secção I" colapsa/expande todos os filhos), mantendo a simplicidade para o caso base (maioria dos documentos)?

**E) O que NÃO fazer** — o que seria over-engineering para este tipo de sistema local, usado por uma consultora de engenharia com documentos de 20-100 páginas?

Responde de forma estruturada, prática e directa. Prioriza soluções simples que funcionem com Pandoc standalone + python-docx. Não sugiras LangChain, IA na pipeline, bases de dados ou deploy web.

BLUF: modela isto com **duas camadas**: `semantic_type` + `layout_policy`. Não metas “regras mágicas” dispersas por flags soltas. Pandoc resolve bem TOC global, lista de figuras/tabelas, numbering global e page breaks simples; section breaks reais, mudança de orientação/tamanho de página a meio do DOCX e numeração por blocos sem hacks pedem OpenXML/Lua filter ou pós-processamento com `python-docx`.[^1][^2][^3]

## Outline

1. Pressupostos.
2. A) Modelo de dados recomendado.
3. B) Capacidades reais do Pandoc vs fallback.
4. C) Tipologias semânticas recomendadas.
5. D) Estrutura da UI Streamlit.
6. E) O que não fazer.

## Pressupostos

- P1. O alvo principal é DOCX Word, não PDF-first nem XML editorial puro.[^1]
- P2. O caso dominante é simples: capa, TOC, corpo numerado, anexos opcionais.[^1]
- P3. Queres manter `Pandoc standalone + reference.docx + python-docx`, sem introduzir motores alternativos nem modelo excessivamente genérico.[^1]
- P4. Aceitas um pequeno nível de hardcoding semântico na app e no compilador, desde que o YAML continue claro e editável.[^1]


## A) Modelo de dados

A decisão certa é: manter `estrutura.yaml` como fonte de verdade da **intenção editorial e de layout**, e deixar `mapeamento.yaml` apenas para origem de conteúdo. Misturar paginação, numbering e paths Markdown no mesmo ficheiro degrada manutenção rapidamente.[^1]

### Estrutura recomendada

Usa, por elemento, estes grupos de campos:

```yaml
document:
  id: memoria_descritiva
  title: "Memória Descritiva e Justificativa"
  version: "P01"
  date: 2026-04-03
  defaults:
    page:
      size: A4
      orientation: portrait
    numbering:
      scheme: arabic
      restart: false
      continuous_with_previous: true
    toc:
      include: true

elements:
  - id: cover
    slug: cover
    title: "Capa"
    semantic_type: cover
    level: 0
    include: true
    display_order: 10

    behavior:
      toc:
        include: false
      page:
        break_before: true
        section_break_before: false
        size: A4
        orientation: portrait
      numbering:
        visible: false
        scheme: none
        restart: false
        continuous_with_previous: false

    children: []

  - id: toc
    slug: toc
    title: "Índice"
    semantic_type: toc
    level: 0
    include: true
    display_order: 20

    behavior:
      toc:
        include: false
        kind: general
        depth: 3
      page:
        break_before: true
      numbering:
        visible: false
        scheme: none

  - id: sec_1
    slug: sec-introducao
    title: "Introdução"
    semantic_type: section
    level: 1
    include: true
    display_order: 30

    behavior:
      toc:
        include: true
      page:
        break_before: false
        section_break_before: false
      numbering:
        visible: true
        scheme: arabic
        restart: false
        continuous_with_previous: true

    children: []
```


### Campos que fazem sentido

Os mínimos úteis são estes:


| Campo | Manter? | Motivo |
| :-- | --: | :-- |
| `semantic_type` | Sim | É o pivô para defaults e lógica do compilador. |
| `level` | Sim | Continua útil para hierarquia editorial e numbering. |
| `include` | Sim | Essencial para toggle rápido e compilação. |
| `display_order` | Sim | Útil para UI flat e reorder explícito. |
| `children` | Sim | Mantém a árvore sem ambiguidade. |
| `behavior.toc.include` | Sim | Necessário; não assumes que todo heading entra no TOC. |
| `behavior.page.break_before` | Sim | Simples e frequente. |
| `behavior.page.section_break_before` | Sim | Necessário para casos reais de orientação/secção Word. |
| `behavior.page.size` | Sim | Só a nível do elemento que abre nova secção. |
| `behavior.page.orientation` | Sim | Idem. |
| `behavior.numbering.scheme` | Sim | Útil para anexos e preliminares. |
| `behavior.numbering.restart` | Sim | Útil e claro. |
| `behavior.numbering.visible` | Sim | Distingue “não numerado” de “numerado mas não exibido” no heading. |

### Campos redundantes ou perigosos

- `continuous_with_previous` é útil, mas só se tiver semântica restrita: aplica-se apenas quando `restart: false`. Caso contrário cria estados contraditórios.[^1]
- `tipo` e flags avulsas tipo `is_annex`, `is_toc`, `is_cover` são redundantes se já tens `semantic_type`.[^1]
- `template_docx` em `estrutura.yaml` é erro de separação de responsabilidades; isso pertence ao `mapeamento.yaml`.[^1]


### O que estás a esquecer

Faltam 4 coisas importantes:

1. **`page_number.format`** separado de `heading numbering.scheme`.[^1]
Uma coisa é numeração de títulos/anexos; outra é numeração de página Word. Não mistures.
2. **`section_role` editorial** para agrupar semântica macro, por exemplo `front_matter`, `main_matter`, `back_matter`.[^1]
Isto simplifica defaults e aproxima-te do modelo LaTeX/DocBook sem complicar.[^1]
3. **`start_page_number` opcional**.[^1]
Raro, mas útil quando queres preliminares em romano e corpo a começar em 1.
4. **`toc.kind`** com enum restrito: `general | figures | tables`.[^1]
Não cries um sistema genérico de “índices arbitrários”.

### Schema final recomendado

A tua abstração certa é:

- `semantic_type`: o que o bloco **é**.
- `section_role`: em que parte do documento cai.
- `behavior`: overrides de layout/TOC/numbering.
- defaults resolvidos por herança app-side no momento de edição/compilação.[^1]

Isto evita over-engineering porque o YAML guarda apenas intenção e overrides, enquanto os defaults por tipologia ficam hardcoded na app. Esse padrão é muito mais robusto do que gravar todos os defaults explicitamente em cada nó.[^1]

## B) Pandoc capabilities reais

### O que o Pandoc faz bem nativamente

Pandoc suporta nativamente, para `docx`:

- `--toc` / `--table-of-contents` para TOC global.[^1]
- `--toc-depth` para profundidade do TOC.[^1]
- `--number-sections` para numeração de headings.[^1]
- `--number-offset` para offset inicial de numeração.[^1]
- `--list-of-figures` e `--list-of-tables` para listas globais.[^1]
- `--reference-doc` para aplicar estilos, propriedades do documento, margens, page size, header e footer herdados do DOCX de referência.[^1]

Isto cobre bem o caso base: documento com capa fora do fluxo de headings, TOC global, corpo numerado, figuras/tabelas listadas.[^4][^1]

### O que o Pandoc faz mal ou não faz sozinho em DOCX

1. **Page breaks controlados por elemento**
O AST do Pandoc não tem paginação como conceito editorial forte; page breaks em DOCX são normalmente inseridos com Lua filter ou Raw OpenXML, não com metadata limpa e nativa.[^5][^3]
2. **Section breaks Word reais**
Pandoc não te dá uma API declarativa de alto nível para “aqui começa nova secção Word com orientação landscape”. Isso cai em OpenXML custom ou pós-processamento do DOCX.[^2][^1]
3. **Formatos de página diferentes dentro do mesmo DOCX**
`reference.docx` define propriedades gerais do documento, mas variar A4/A3/portrait/landscape dentro do mesmo ficheiro exige secções Word distintas. Pandoc, sozinho, não gere isso de forma robusta por elemento.[^6][^1]
4. **TOC parcial por bloco**
TOC global sim. TOC local “só para esta subtree” não é capacidade nativa limpa no writer DOCX. O workaround típico é filtro Lua/OpenXML para inserir campos específicos.[^2]
5. **Controlo fino da posição do TOC no DOCX**
O template OpenXML pode influenciar, e filtros também, mas não é tão trivial como `--toc` + “coloca aqui”. Há histórico de limitações e workarounds nesse ponto.[^7][^1]
6. **Heading numbering complexa por tipologia**
`--number-sections` funciona globalmente. “Corpo em árabe, anexos em letras, preliminares em romano” já sai do modo nativo simples.[^8][^1]

### O que deve ficar no Pandoc

Mantém no Pandoc:

- compilação principal MD → DOCX;
- TOC geral;
- lista de figuras/tabelas, se precisares;
- numbering normal do corpo;
- estilos globais via `reference.docx`;
- concatenação e parsing de headings.[^1]


### O que deve ir para Lua filter / OpenXML

A solução mais limpa antes de `python-docx` é um **Lua filter pequeno** para:

- inserir page break antes de certos elementos;
- inserir marcadores TOC/LOF/LOT em posições específicas;
- injetar raw OpenXML para section break quando necessário.[^3][^2]

Isto encaixa melhor no teu pipeline do que tentar remendar tudo depois no DOCX final.[^3]

### O que deve ir para `python-docx`

Reserva `python-docx` para fallback de baixo volume:

- alterar orientação de uma secção;
- mudar page size numa secção;
- criar section break quando o Pandoc/OpenXML não ficou estável;
- acertos finais de header/footer por secção.[^1]

Mas não o uses para reconstruir numbering estrutural de headings. Isso é frágil e luta contra o Word internamente.[^8]

### Posição técnica

A arquitetura certa é esta:

- **Tier 1 — Pandoc nativo**: tudo o que for global e simples.[^1]
- **Tier 2 — Lua filter/OpenXML**: page breaks, placement de TOC/LOF/LOT, section breaks.[^2][^3]
- **Tier 3 — python-docx**: apenas reparação/local overrides de secção e page setup.[^1]

Se tentares fazer secções Word avançadas só com `python-docx` no fim, vais acabar com lógica opaca e difícil de testar. Se tentares fazer tudo só com Pandoc, vais bater em limitações reais do writer DOCX.[^2][^1]

## C) Tipologias recomendadas

Para o teu caso, não uses um catálogo de 20 tipos. Usa 8–10 semânticas sólidas, inspiradas em `frontmatter/mainmatter/backmatter` e em modelos tipo DocBook/LaTeX, mas simplificadas.[^1]

### Tipologias core

| `semantic_type` | Função | Default recomendado |
| :-- | :-- | :-- |
| `cover` | Capa | sem TOC, sem numbering, `break_before=true` |
| `toc` | Índice geral | sem entrada no TOC, `break_before=true` |
| `list_of_figures` | Índice de figuras | sem entrada no TOC, `break_before=true` |
| `list_of_tables` | Índice de tabelas | sem entrada no TOC, `break_before=true` |
| `section` | Secção numerada normal | TOC sim, numbering árabe contínua |
| `subsection_group` | Agrupador estrutural sem conteúdo próprio | TOC opcional, sem md_source obrigatório |
| `unnumbered_heading` | Título não numerado | TOC opcional, sem numbering |
| `annex` | Anexo individual | `break_before=true`, numbering separada |
| `annexes` | Contentor de anexos | normalmente sem md_source, organiza defaults dos filhos |
| `front_matter_note` | Resumo, notas prévias, aprovação, prefácio | numeração de página romana opcional, heading geralmente sem numbering |

### Tipologias opcionais úteis

- `revision_history` para tabela de revisões.[^1]
- `approvals` para assinaturas/aprovações.[^1]
- `bibliography` se houver referências técnicas.[^1]
- `glossary` apenas se existir necessidade real recorrente.[^1]


### O que vem da indústria e vale a pena importar

Da tradição editorial técnica, o que faz sentido trazer é:

- separação entre `front matter`, `main matter`, `back matter`.[^1]
- distinção entre conteúdo numerado e não numerado.[^1]
- índices especializados: TOC, figuras, tabelas.[^1]
- anexos como regime próprio de numbering.[^1]

O que **não** vale a pena importar é o detalhe inteiro de DITA/DocBook: topic types ultra-específicos, profiling, conditional publishing, IDs canónicos complexos, transclusion pesada. Para 20–100 páginas em consultora, isso é ruído.[^1]

## D) Implementação Streamlit

A tab “TOC / Compilar” deve servir dois modos: **modo simples por defeito** e **modo avançado progressivo**. Se mostrares todos os controlos de paginação/numeração logo à cabeça, tornas o caso base pior.[^1]

### Estrutura recomendada da tab

1. **Toolbar no topo**

- Compilar.
- Validar estrutura.
- Expandir/colapsar tudo.
- Toggle “modo avançado”.

2. **Lista hierárquica flat-indentada**

- uma linha por elemento;
- indentação visual por `level`;
- ícone/label do `semantic_type`;
- toggle `include`;
- botão expand/collapse se tiver filhos;
- drag/reorder no mesmo nível ou ações subir/descer.[^1]

3. **Painel lateral ou expander por linha**

- no modo simples: só `include`, título, tipo, ordem;
- no modo avançado: TOC, break before, section break, orientação, numbering scheme, restart.[^1]


### Padrão de interação certo

Usa comportamento de árvore com estado herdado, mas sem automações agressivas:

- Toggle no pai pode aplicar aos filhos por ação explícita: “aplicar a descendentes”.[^1]
- Colapsar/expandir atua só na visualização, não no `include`.[^1]
- Um contentor `annexes` deve poder mostrar estado agregado dos filhos.[^1]


### Agrupamento por tipo sem perder hierarquia

Não recomendo uma vista “agrupada por tipo” como principal, porque destrói a ordem real do documento. Faz antes isto:

- vista principal: ordem documental hierárquica;
- filtros rápidos no topo: `Todos | Corpo | Anexos | TOCs | Front matter`.[^1]

Isto dá o benefício de “agrupar por tipo” sem perder a árvore.

### Caso base simplificado

Para a maioria dos documentos, a tab deve mostrar apenas:

- Capa.
- TOC.
- Secções principais.
- Anexos.[^1]

E só quando o utilizador ativa “Avançado” aparecem:

- listas de figuras/tabelas;
- numbering scheme;
- section break;
- formato/orientação de página.[^1]


### Estado visual recomendado por linha

Cada linha pode ter esta estrutura:

- `[▸] [toggle include] [badge tipo] [título]`
- à direita: `TOC`, `PB`, `SB`, `Num: 1/A/i/-` como chips compactos.[^1]

Isso dá leitura técnica imediata sem abrir detalhes.

### Regra de UI importante

Não deixes editar tudo em massa via grid tipo spreadsheet. Para árvore editorial, isso degrada clareza. Melhor:

- ações por linha;
- batch actions explícitas;
- painel de detalhes do nó selecionado.[^1]


## E) O que NÃO fazer

### 1. Não cries um meta-modelo genérico de publishing

Não inventes abstrações tipo “render phases”, “layout engines”, “output policies” e “rule resolvers” para um sistema local DOCX-first. O teu problema é concreto e Word-centric.[^1]

### 2. Não metas secção Word como conceito em todos os nós

`section_break_before` deve ser raro. Se cada elemento puder livremente abrir secção Word, o modelo fica impossível de prever e testar.[^1]

### 3. Não tentes suportar numbering arbitrária de tudo

Suporta bem:

- corpo: árabe;
- preliminares: romano opcional;
- anexos: letras ou romano.[^1]

Mais do que isso é custo sem retorno para o teu contexto.

### 4. Não uses `python-docx` como compilador principal

`python-docx` é fraco como engine de composição documental comparado com Pandoc. Usa-o como bisturi, não como motor.[^1]

### 5. Não transformes o `estrutura.yaml` num dump de defaults resolvidos

Se cada nó guardar 20 campos sempre preenchidos, o YAML fica ruidoso e difícil de manter. Guarda apenas overrides e resolve defaults por `semantic_type` na app/compiler.[^1]

### 6. Não tentes “TOC parcial por todo o lado”

TOC geral, lista de figuras, lista de tabelas: sim. Mini-TOCs por secção/subárvore só quando houver caso de uso recorrente comprovado, porque em DOCX isso já entra em workaround territory.[^2]

## Decisão recomendada

Tomava esta opção, sem hesitação:


| Opção | Posição |
| :-- | :-- |
| 1. Tudo em Pandoc puro | Rejeitar; não chega para secções Word e paginação avançada.[^1][^2] |
| 2. Pandoc + schema semântico + Lua filter pequeno + `python-docx` residual | **Escolha certa**; simples, robusto, extensível.[^2][^3][^1] |
| 3. Passar grande parte para `python-docx` | Rejeitar; manutenção pior e menos previsibilidade.[^1] |
| 4. Modelo editorial complexo tipo DITA-lite | Rejeitar para 20–100 páginas; demasiado pesado.[^1] |

A melhor forma de fechar isto é definires já um `semantic_type registry` hardcoded na app, com defaults por tipo e validações de consistência. Depois, o `estrutura.yaml` guarda só árvore + overrides. Isso dá-te simplicidade no caso base e poder suficiente para os edge cases reais.[^1]

Pergunta útil para a próxima iteração: queres que eu te proponha já um **schema YAML v2 completo** com enums, defaults e regras de validação Pydantic-ready?
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^9]</span>

<div align="center">⁂</div>

[^1]: https://github.com/jgm/pandoc/issues/6886

[^2]: https://github.com/pandocker/pandocker-lua-filters/blob/master/lua/docx-pagebreak-toc.lua

[^3]: https://github.com/pandoc/lua-filters/blob/master/pagebreak/pagebreak.lua

[^4]: https://www.reddit.com/r/LaTeX/comments/u4xzpl/how_do_i_exclude_a_title_from_the_toc_using_pandoc/

[^5]: https://inbox.vuxu.org/pandoc-discuss/87fvf5ckhv.fsf@jhu.edu/

[^6]: https://www.scribd.com/document/719868548/PANDOC-MANUAL

[^7]: https://inbox.vuxu.org/pandoc-discuss/a9967f45-314e-484c-a642-ecb03c315e10n@googlegroups.com/T/

[^8]: https://github.com/jgm/pandoc/issues/2582

[^9]: https://github.com/jgm/pandoc/issues/10923

[^10]: https://inbox.vuxu.org/pandoc-discuss/2f0fdd14-9f3e-4aa7-9d9c-756cc82f3a5d@googlegroups.com/

[^11]: https://inbox.vuxu.org/pandoc-discuss/d560de22-bbac-40e0-ae25-75f02627175d@googlegroups.com/T/

[^12]: https://github.com/pandocker/pandoc-docx-pagebreak-py

[^13]: https://github.com/jgm/pandoc/discussions/9674

[^14]: https://stackoverflow.com/questions/79671248/how-to-insert-page-breaks-when-creating-docx-with-pandoc-and-php

[^15]: https://pandoc.org/demo/example33/3.2-reader-options.html

[^16]: https://pandoc.org/MANUAL.html

[^17]: https://stackoverflow.com/questions/24208889/how-to-specify-numbered-sections-in-pandocs-front-matter

[^18]: https://github.com/jgm/pandoc/issues/10089

[^19]: https://forum.literatureandlatte.com/t/setting-up-numbering-and-heading-formats-in-pandoc-and-typst/147315

[^20]: https://forum.literatureandlatte.com/t/using-pandoc-to-convert-tutorial-project-to-a-docx-file/140789

[^21]: https://inbox.vuxu.org/pandoc-discuss/a8b62516-e052-46a8-92e7-1d313e980b78@www.fastmail.com/T/

[^22]: https://inbox.vuxu.org/pandoc-discuss/66ad3d8e-49d5-4117-85e7-350f87555920n@googlegroups.com/T/

[^23]: https://stackoverflow.com/questions/76260009/pandoc-markdown-to-docx-with-title-page-toc-and-placeholder-replacement

[^24]: https://stackoverflow.com/questions/64552367/detecting-a-docx-page-break-in-pandoc

[^25]: https://github.com/jgm/pandoc/issues/9645

[^26]: https://github.com/jgm/pandoc/discussions/9596

[^27]: https://pandoc.org/lua-filters.html

[^28]: https://pandoc-discuss.narkive.com/wANvjTEe/toc-title-on-docx-always-in-english

