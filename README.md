# JSJ-DOC-ENGINE — Mapa do Projecto

> Ponto de entrada. Ler antes de qualquer acção.

---

## 1. O QUE É

Sistema de produção de documentos técnicos JSJ.
Converte fontes Markdown em DOCX com estilos JSJ via Pandoc.
UI Streamlit local para visualizar estrutura, reordenar secções e compilar.

Output sempre DOCX — compatível com Microsoft Word.
Agnóstico de documento — serve CTE, memórias descritivas, ou qualquer
documento técnico JSJ estruturado em Markdown.

---

## 2. DOIS PLANOS — NUNCA MISTURAR

| Plano | O que define | Ficheiro-chave |
|-------|-------------|----------------|
| **Arquitectura do SISTEMA** | O que é, como funciona, decisões técnicas | `00_GOVERNO/ARQUITECTURA.md` |
| **Arquitectura do PROJECTO** | Como produzimos, fases, estado | Este ficheiro + `00_GOVERNO/ROADMAP.md` |

---

## 3. ESTRUTURA DE PASTAS

| Pasta | Função | Quem toca |
|-------|--------|-----------|
| `00_GOVERNO\` | Arquitectura, decisões, roadmap | Cowork (estratégia) |
| `01_AUDITORIAS\` | DRs, avaliações externas | Cowork (leitura) |
| `02_TEMPLATES\` | reference.docx JSJ | Cowork (gestão ficheiros) |
| `03_OUTPUT\` | DOCX compilados | App (geração automática) |
| `04_APP\` | Código fonte: compile.py, preprocessor.py, app.py | VSCode + agente IDE |

**Regra:** Cowork nunca toca em `04_APP\`.
Cowork prepara prompts para o agente IDE quando há desenvolvimento.

---

## 4. PAPÉIS

| Agente | Função | Exemplos |
|--------|--------|---------|
| **Cowork** | Governo, estratégia, prompts IDE | Decisões de arquitectura, reorganizar pastas, preparar prompts |
| **VSCode + agente IDE** | Desenvolvimento | Escrever compile.py, app.py, config.yaml |
| **David** | Decisão e validação | Aprovar arquitectura, testar output DOCX |

---

## 5. FICHEIROS DE GOVERNO

| Ficheiro | Responsabilidade única |
|----------|----------------------|
| `00_GOVERNO/ARQUITECTURA.md` | Stack, princípios, decisões técnicas |
| `00_GOVERNO/ROADMAP.md` | Fases, gates, estado actual |
| `00_GOVERNO/ESTRUTURA_PASTAS.md` | Árvore de pastas e convenções |

---

## 6. ONDE ESTAMOS

→ `00_GOVERNO/ROADMAP.md`

---

## 7. ARRANQUE RÁPIDO (para o agente IDE)

```
1. Instalar Pandoc: https://pandoc.org/installing.html
2. cd 04_APP
3. python -m venv venv
4. venv\Scripts\activate
5. pip install -r requirements.txt
   (inclui openpyxl ou pandas — para preprocessor.py)
6. streamlit run app.py
```

---

**Fim — README.md — 2026-04-03**
