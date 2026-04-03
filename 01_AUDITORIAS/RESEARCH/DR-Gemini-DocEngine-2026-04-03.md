**BLUF**
A stack *state-of-the-art* para "docs-as-code" determinístico e focado em engenharia/contratos assenta no **Pandoc** (motor de conversão) gerido por um **script orquestrador** (Python ou Node/TS), com **Supabase** como *single source of truth* e interface customizada (React/Next.js). Sistemas de Headless CMS genéricos (Strapi, Contentful) ou frameworks de documentação (Docusaurus) falham na exportação nativa para DOCX estruturado ou introduzem *overhead* desnecessário para o teu caso de uso.

Abaixo, o *outline* da arquitectura estruturada para validação.

---

### 1. Motor de Compilação (Markdown → DOCX)
A dependência de LLMs para compilar DOCX estruturados é um anti-padrão. A comunidade técnica adopta o **Pandoc** como padrão absoluto para transformações determinísticas.

* **Ferramenta Central:** `pandoc` executado *server-side* ou via *worker*.
* **Template:** Utilização obrigatória da flag `--reference-doc=template.docx`. Cria-se um ficheiro DOCX vazio com os estilos da empresa rigorosamente definidos (Cabeçalhos, Margens, Fontes, Tabelas). O Pandoc mapeia a AST (Abstract Syntax Tree) do Markdown diretamente para os estilos OOXML deste ficheiro.
* **Orquestrador:** Um script de compilação (Python ou Node) que:
    1. Faz query ao Supabase filtrando os capítulos aplicáveis (`is_applicable = true`) e ordenando por `display_order`.
    2. Concatena os *chunks* de Markdown num único ficheiro/stream virtual em memória.
    3. Injecta numeração (ver secção 3) e meta-dados (frontmatter).
    4. Passa o resultado ao Pandoc e devolve o DOCX gerado (armazenando no Supabase Storage).

### 2. Schema Supabase (Slugs como PKs)
Para suportar o caderno de encargos (~600pp, 29 capítulos, reutilizável), a melhor prática relacional separa o "Dicionário Master" da "Instância do Projecto".

```sql
-- Tabela de Domínio / Template
CREATE TABLE base_chapters (
    slug TEXT PRIMARY KEY,           -- e.g., 'betão-armado', 'movimento-terras' (Imutável)
    title TEXT NOT NULL,             -- e.g., 'Betão Armado'
    default_content_md TEXT NOT NULL,-- Conteúdo standard da empresa
    default_order FLOAT NOT NULL     -- Ordem base
);

-- Tabela de Instância (Obra)
CREATE TABLE project_chapters (
    project_id UUID REFERENCES projects(id),
    chapter_slug TEXT REFERENCES base_chapters(slug),
    is_applicable BOOLEAN DEFAULT true,  -- Triagem (N/A)
    display_order FLOAT NOT NULL,        -- Permite reordenação específica por obra
    custom_content_md TEXT,              -- Se NULL, consome o default. Se preenchido, faz override.
    PRIMARY KEY (project_id, chapter_slug)
);
```

### 3. Mecanismo de Reordenação e Numeração
O cruzamento entre a reordenação flexível na UI e a numeração rígida de um contrato exige separação clara de responsabilidades. 

* **UI e Reordenação (Frontend + Supabase):**
    * Uso de bibliotecas *drag-and-drop* (ex: `dnd-kit` em React).
    * *Database Strategy:* Usar ordenação por **números de vírgula flutuante (Float)** para o campo `display_order`. Se o capítulo A está na posição 1.0 e o B na 2.0, arrastar o C para o meio actualiza o C para 1.5. Isto evita cascata de updates na base de dados (uma única query `UPDATE`). Em sistemas de escala maciça usa-se *LexoRank*, mas `Float` é suficiente e mais prático para ~30 capítulos.
* **Numeração Automática (O Conflito Rigor vs. Flexibilidade):**
    * *Opção A (Delegar no Word):* O script agrupa o Markdown (`# Título`) e o `reference.docx` tem o estilo "Heading 1" configurado com auto-numeração. *Risco:* A numeração do Word quebra frequentemente quando o documento é editado por terceiros após a exportação.
    * *Opção B (Recomendada para Contratos):* Numeração gerada deterministicamente no script orquestrador. A UI define a ordem (1.0, 1.5, 2.0), mas no momento do *build*, o script lê a ordem sequencial aplicável e reescreve os cabeçalhos Markdown antes de enviar para o Pandoc (Substitui `# Título` por `# 1. Título`). O Pandoc usa um DOCX *sem* auto-numeração.
    * *Heurística Técnica:* A **Opção B** é preferível porque elimina o comportamento emergente/indesejado do MS Word, tornando o output de facto "docs-as-code" (o ficheiro fonte é a única verdade).

### 4. Avaliação Estratégica
* **Prós da Abordagem:** Elimina "caixas negras" de agentes LLM num documento com implicações legais. O output é 100% reprodutível. A estrutura de dados permite futuras análises sistémicas entre obras (saber em que obras o capítulo X sofreu *override* e porquê).
* **Limitações / Edge Cases a Considerar:** O tratamento de tabelas complexas e figuras em Markdown. O Pandoc lida bem com tabelas simples, mas em cadernos de encargos podes precisar de tabelas de medição complexas. *Solução:* Extensões do Pandoc (grid tables) ou suporte para blocos HTML nativos dentro do Markdown que o Pandoc saiba ler.

Aguardo validação desta arquitectura antes de expandir em detalhes de implementação (scripts de automação, configuração de reference.docx, ou RLS no Supabase, se necessário).