# JSJ-DOC-ENGINE — 04_APP

> Ponto de entrada para o agente IDE.
> Ler antes de qualquer acção nesta pasta.

---

## 1. O QUE É ESTA PASTA

Código fonte da app JSJ-DOC-ENGINE.
Não tocar fora desta pasta — o resto do projecto é governo (Cowork).

---

## 2. CONTEXTO DO SISTEMA

Sistema de produção de documentos técnicos JSJ.
Converte Markdown em DOCX via Pandoc com estilos JSJ.
UI Streamlit local — multi-projecto, stateless entre sessões.

Arquitectura completa → `00_GOVERNO\ARQUITECTURA.md`
Estado do projecto → `00_GOVERNO\ROADMAP.md`

---

## 3. STACK

| Componente | Ferramenta |
|------------|-----------|
| UI | Streamlit |
| Motor compilação | Pandoc (binário standalone) |
| Estilos DOCX | reference.docx em `02_TEMPLATES\` |
| Orquestrador | compile.py |
| Preprocessador | preprocessor.py |
| Configuração | config.yaml |
| Runtime | Python 3.x + venv |

---

## 4. FICHEIROS DESTA PASTA

| Ficheiro | Responsabilidade |
|----------|----------------|
| `app.py` | UI Streamlit — lê `estrutura.yaml`, `mapeamento.yaml` — 3 camadas + snapshot |
| `compile.py` | Orquestrador: lê mapeamento → agrega MD → Pandoc → DOCX |
| `preprocessor.py` | Substitui tags `{{ excel \| ... }}` por tabelas MD |
| `config.yaml` | Multi-projecto: paths de estrutura.yaml e mapeamento.yaml por projecto |
| `requirements.txt` | Dependências Python |
| `venv\` | Ambiente virtual — não versionar |

---

## 5. FICHEIROS EXTERNOS (fora desta pasta)

Cada projecto/documento tem dois ficheiros YAML próprios,
cujos paths estão definidos no `config.yaml`:

| Ficheiro | Conteúdo |
|----------|---------|
| `estrutura.yaml` | Hierarquia do documento (tipo, secções, headings, anexos) |
| `mapeamento.yaml` | MD sources + templates DOCX por elemento |

Estes ficheiros vivem junto dos projectos-fonte (ex: CTE-TEMPLATE-CLAUDE),
não dentro de 04_APP.

> Formato YAML — Python parseia com `yaml.safe_load()`.
> Gerados e exportados pela app — não editar manualmente.

---

## 6. ARRANQUE

```bash
cd 04_APP
venv\Scripts\activate
streamlit run app.py
```

Se venv não existir:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Pandoc tem de estar instalado como binário standalone:
https://pandoc.org/installing.html

---

## 7. ARQUITECTURA DA APP — 3 CAMADAS

```
CAMADA 1 — Definição do Documento
    Tipo, estrutura hierárquica (H1-H4), anexos, TOCs
    Output: estrutura.yaml

CAMADA 2 — Mapeamento de Conteúdo
    MD source por elemento, template DOCX por elemento
    Output: mapeamento.yaml

CAMADA 3 — TOC Interactivo (tab principal)
    Toggle N/A, reordenação, preview numeração
    Export/Import estrutura.yaml + mapeamento.yaml
    Botão "Compilar DOCX"
    Função Snapshot
```

---

## 8. PIPELINE DE COMPILAÇÃO

```
config.yaml → escolha de projecto
        ↓
estrutura.yaml + mapeamento.yaml (auto-load ou import)
        ↓
compile.py
    ├── lê mapeamento.yaml
    ├── lê MD de cada elemento
    ├── preprocessor.py → {{ excel | ... }} substituído por tabelas MD
    ├── concatena MD processado
    └── Pandoc → DOCX
            ├── template geral: 02_TEMPLATES\JSJ-CTE-reference.docx
            └── template por elemento: definido em mapeamento.yaml
```

Output em: `03_OUTPUT\`

---

## 9. FUNÇÃO SNAPSHOT

Congela o estado do documento numa pasta escolhida pelo utilizador.
Nunca toca nos ficheiros originais.

```
[NomeDocumento]_[YYYY-MM-DD]\
├── ESTRUTURA\
│   ├── estrutura.yaml
│   └── mapeamento.yaml
└── MDS\
    ├── Modo A: ficheiros MD copiados tal como estão
    └── Modo B: MD divididos por heading (H2 contém filhos H3/H4)
```

---

## 10. ESTADO ACTUAL

Ver `00_GOVERNO\ROADMAP.md` para estado detalhado.

Resumo:
- `compile.py` ✅ funcional — exportou Secção I do CTE
- `preprocessor.py` ✅ criado
- `app.py` ✅ Camada 3 funcional (TOC interactivo, export/import estrutura.yaml + mapeamento.yaml)
- `config.yaml` ⏳ a criar com schema multi-projecto

---

## 11. REGRAS PARA O AGENTE IDE

- Nunca criar ficheiros fora de `04_APP\`
- Nunca editar ficheiros de governo (`00_GOVERNO\`)
- Se precisar de contexto de arquitectura → ler `00_GOVERNO\ARQUITECTURA.md`
- Se precisar de saber o estado → ler `00_GOVERNO\ROADMAP.md`
- Comentar código em português
- Funções curtas com responsabilidade única
- Não introduzir dependências não listadas em requirements.txt sem avisar

---

## 12. MANUTENÇÃO DESTE README

O agente IDE deve actualizar este ficheiro quando:
- Criar um ficheiro novo em `04_APP\` → adicionar à secção 4
- Alterar a pipeline de compilação → actualizar secção 8
- Completar uma funcionalidade → actualizar secção 10 (Estado Actual)
- Alterar dependências → actualizar secções 3 e 6

Não alterar: secções 1, 2, 7, 9 — são decisões de arquitectura,
geridas pelo Cowork via `00_GOVERNO\ARQUITECTURA.md`.

Se algo nessas secções estiver errado → reportar ao Cowork,
não corrigir directamente.

---

**Fim �