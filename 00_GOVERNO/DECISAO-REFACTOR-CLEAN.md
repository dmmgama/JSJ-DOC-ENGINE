# DECISÃO D15 — Refactorização Clean Architecture de app.py

> **Data:** 2026-04-04
> **Estado:** APROVADA
> **Impacto:** 04_APP\ (estrutura de ficheiros e módulos)
> **Trigger:** app.py atingiu 1.403 linhas — monólito com 5 responsabilidades misturadas

---

## PROBLEMA

O `app.py` acumula UI Streamlit, lógica de negócio, I/O de ficheiros, gestão de session_state e gestão de projectos num único ficheiro. Consequências:

1. **Agentes IDE não conseguem resolver bugs** — contexto do ficheiro excede a janela útil
2. **Cada feature adicionada por acreção** piora o acoplamento
3. **Lógica de negócio não é testável** — depende de `st.session_state`
4. **Session state partilhado** entre 12+ keys sem gestão centralizada

---

## DECISÃO

Refactorizar `04_APP\` seguindo princípios de Clean Architecture adaptados a Streamlit:

### Regra de Dependência (inviolável)

```
core/  ←  adapters/  ←  ui/  ←  app.py
```

**`core/` nunca importa `streamlit`.** Nunca importa `adapters/` ou `ui/`.
**`adapters/` nunca importa `streamlit`.** Nunca importa `ui/`.
**`ui/` pode importar `core/` e `adapters/`.** Só `ui/` importa `streamlit`.

### Estrutura alvo

```
04_APP\
├── app.py                          ← 30-50 linhas: config página + routing
├── core/
│   ├── __init__.py
│   ├── models.py                   ← dataclasses: Elemento, Projecto, Estrutura, Mapeamento
│   └── services.py                 ← lógica pura: calcular_numeracao, validar, gerar_yaml, parse_yaml, aplanar
├── adapters/
│   ├── __init__.py
│   ├── yaml_io.py                  ← ler/escrever estrutura.yaml, mapeamento.yaml, variaveis.yaml
│   └── config.py                   ← ler/escrever config.yaml, gestão de projectos
├── ui/
│   ├── __init__.py
│   ├── state.py                    ← init_state(), clear_project_state(), get/set helpers
│   ├── sidebar.py                  ← sidebar: selecção projecto, criar/apagar, import/export
│   ├── tab_toc.py                  ← Tab TOC interactivo + compilação
│   ├── tab_estrutura.py            ← Tab editor de estrutura (Camada 1)
│   └── tab_mapeamento.py           ← Tab mapeamento (Camada 2)
├── compile.py                      ← sem alteração (já bem estruturado)
├── preprocessor.py                 ← sem alteração
├── semantic_type_registry.py       ← sem alteração
├── migrate_schema_v1_to_v2.py      ← sem alteração
├── config.yaml
├── requirements.txt
├── filters/
│   └── pagebreak.lua
└── venv/
```

### Mapeamento de responsabilidades

| Responsabilidade actual (app.py) | Destino | Camada |
|----------------------------------|---------|--------|
| `calcular_numeracao()` | `core/services.py` | Entity/Use Case |
| `gerar_estrutura_yaml()`, `gerar_mapeamento_yaml()` | `core/services.py` | Use Case |
| `parse_estrutura_yaml()`, `parse_mapeamento_yaml()` | `core/services.py` | Use Case |
| `_aplanar_elementos()`, `_obter_elementos_flat()` | `core/services.py` | Use Case |
| `_validar_elementos()`, `_todos_slugs()`, `_auto_slug()` | `core/services.py` | Use Case |
| `_elemento_vazio()` | `core/models.py` | Entity |
| `carregar_config()`, `guardar_config()` | `adapters/config.py` | Adapter |
| `_carregar_estrutura_yaml_ficheiro()`, `_guardar_estrutura_yaml_ficheiro()` | `adapters/yaml_io.py` | Adapter |
| `exportar_ficheiro()` | `adapters/yaml_io.py` | Adapter |
| `ler_paths_config()` | `adapters/config.py` | Adapter |
| `carregar_projecto()` | `adapters/config.py` + `ui/state.py` | Adapter + UI |
| 12+ session_state keys | `ui/state.py` | Framework |
| `limpar_chaves_checkboxes()` | `ui/state.py` | Framework |
| `_renderizar_formulario_elemento()` | `ui/tab_estrutura.py` | Framework |
| `_renderizar_elemento()`, `_renderizar_lista_elementos()` | `ui/tab_estrutura.py` | Framework |
| `_renderizar_camada2()` | `ui/tab_mapeamento.py` | Framework |
| TOC + sidebar + tabs | `ui/sidebar.py` + `ui/tab_toc.py` | Framework |
| Mock data | Eliminar (substituir por fixtures de teste futuras) | — |

---

## EXECUÇÃO

**2 prompts IDE sequenciais:**

### Step 1 — Extrair `core/` e `adapters/`
- Criar `core/models.py`, `core/services.py`
- Criar `adapters/yaml_io.py`, `adapters/config.py`
- Mover funções do app.py → novos módulos
- app.py importa dos novos módulos em vez de ter código inline
- **Verificação:** app.py funciona identicamente (sem mudança de comportamento)

### Step 2 — Partir `ui/` e reduzir app.py
- Criar `ui/state.py`, `ui/sidebar.py`, `ui/tab_toc.py`, `ui/tab_estrutura.py`, `ui/tab_mapeamento.py`
- Mover todo o código Streamlit para `ui/`
- app.py fica com 30-50 linhas: `st.set_page_config()` + imports + routing
- **Verificação:** app.py funciona identicamente

### Ordem de execução
```
Step 1 → testar → Step 2 → testar → retomar roadmap normal
```

---

## ALTERNATIVAS REJEITADAS

| Alternativa | Porquê rejeitada |
|-------------|-----------------|
| Reescrever do zero | Perda de funcionalidade testada; risco desnecessário |
| Só partir em 3 ficheiros (1 por tab) | Não resolve o problema de lógica misturada com UI |
| Framework de state management (Redux-like) | Overkill para app local interna |
| 4 camadas completas (como no diagrama original) | Desnecessário para tool interna — 3 camadas bastam |

---

## GUARDRAILS PARA AGENTES IDE (pós-refactorização)

Incluir em TODOS os prompts IDE futuros:

```
## REGRAS DE ARQUITECTURA (inviolável)

1. Nunca importar `streamlit` em ficheiros `core/` ou `adapters/`
2. Nunca importar `adapters/` ou `ui/` em ficheiros `core/`
3. Lógica de negócio nova → `core/services.py`
4. I/O de ficheiros novo → `adapters/`
5. UI nova → `ui/` (módulo existente ou novo)
6. `app.py` nunca excede 60 linhas
7. Nenhum ficheiro em `ui/` excede 300 linhas — partir se necessário
8. Session state: só aceder via `ui/state.py` helpers
```

---

**Fim — DECISAO-REFACTOR-CLEAN.md — 2026-04-04**
