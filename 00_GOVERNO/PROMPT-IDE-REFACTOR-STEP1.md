# PROMPT IDE — Refactor Step 1: Extrair core/ e adapters/

> **Decisão:** D15 — `DECISAO-REFACTOR-CLEAN.md`
> **Prioridade:** MÁXIMA — executar ANTES de qualquer outra tarefa

---

## CONTEXTO

- Stack: Python 3.x, Streamlit, PyYAML
- Path raiz: `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\`
- O `app.py` tem 1.403 linhas com lógica de negócio, I/O e UI misturados
- Este step extrai a lógica pura e o I/O para módulos separados
- O `app.py` continua a funcionar identicamente — apenas importa dos novos módulos

---

## ESTADO ACTUAL

Ficheiro único `app.py` com todas as funções. Os outros ficheiros (`compile.py`, `preprocessor.py`, `semantic_type_registry.py`) não são afectados.

---

## TAREFA

### 1. Criar `core/__init__.py` (vazio)

### 2. Criar `core/models.py`

Dataclasses/TypedDicts para os tipos de dados do sistema. Extrair de `app.py`:

```python
# Tipos que hoje são dicts inline:
# - Elemento (slug, titulo, semantic_type, nivel, include, display_order, behavior, filhos)
# - Projecto (id, name, estrutura path, mapeamento path, variaveis path)
#
# Implementar como dataclasses ou TypedDict — usar dataclasses se possível.
# Incluir factory method `elemento_vazio(slug)` — hoje é `_elemento_vazio()` em app.py (linha 364)
```

### 3. Criar `core/services.py`

Mover estas funções de `app.py` → `core/services.py` (renomear se necessário para nomes públicos):

| Função em app.py | Nome em core/services.py | Linha aprox. |
|------------------|-------------------------|-------------|
| `calcular_numeracao(elementos)` | `calcular_numeracao()` | 88 |
| `gerar_estrutura_yaml(elementos, projecto)` | `gerar_estrutura_yaml()` | 135 |
| `gerar_mapeamento_yaml(elementos, projecto)` | `gerar_mapeamento_yaml()` | 164 |
| `_aplanar_elementos(elementos_yaml, pai, contador)` | `aplanar_elementos()` | 209 |
| `parse_estrutura_yaml(conteudo)` | `parse_estrutura_yaml()` | 256 |
| `parse_mapeamento_yaml(conteudo)` | `parse_mapeamento_yaml()` | 277 |
| `_obter_tipos(raw)` | `obter_tipos()` | 334 |
| `_todos_slugs(elementos)` | `todos_slugs()` | 339 |
| `_auto_slug(elementos)` | `auto_slug()` | 353 |
| `_validar_elementos(elementos)` | `validar_elementos()` | 377 |
| `_obter_elementos_flat(elementos, nivel_max)` | `obter_elementos_flat()` | 757 |
| `_mapeamento_por_slug(mapeamento)` | `mapeamento_por_slug()` | 782 |
| `_migrar_v1_para_v2(elementos)` | `migrar_v1_para_v2()` | 656 |

**REGRA:** Nenhuma destas funções pode importar `streamlit`. Se alguma usa `st.session_state`, o acesso ao state deve ser passado como argumento.

### 4. Criar `adapters/__init__.py` (vazio)

### 5. Criar `adapters/yaml_io.py`

Mover de `app.py`:

| Função em app.py | Nome em adapters/yaml_io.py | Linha aprox. |
|------------------|----------------------------|-------------|
| `_carregar_estrutura_yaml_ficheiro(caminho)` | `carregar_estrutura_yaml(caminho)` | 632 |
| `_guardar_estrutura_yaml_ficheiro(caminho, dados)` | `guardar_estrutura_yaml(caminho, dados)` | 642 |
| `exportar_ficheiro(conteudo, caminho)` | `exportar_ficheiro(conteudo, caminho)` | 190 |

**REGRA:** Zero imports de `streamlit`.

### 6. Criar `adapters/config.py`

Mover de `app.py`:

| Função em app.py | Nome em adapters/config.py | Linha aprox. |
|------------------|-----------------------------|-------------|
| `ler_paths_config()` | `ler_paths_config()` | 300 |
| `carregar_config()` | `carregar_config()` | 675 |
| `guardar_config(config)` | `guardar_config(config)` | 686 |

**REGRA:** Zero imports de `streamlit`.

### 7. Actualizar `app.py`

- Remover as funções movidas
- Adicionar imports dos novos módulos:
  ```python
  from core.models import ...
  from core.services import ...
  from adapters.yaml_io import ...
  from adapters.config import ...
  ```
- Substituir todas as chamadas internas pelas novas importações
- Manter TODO o código UI (renderização, session_state, sidebar, tabs) em `app.py` — será partido no Step 2

### 8. Verificar que `carregar_projecto()` funciona

A função `carregar_projecto()` (linha 692) mistura I/O + state. Neste step:
- Mover a parte de I/O (ler ficheiros YAML) para `adapters/`
- Manter a parte de `st.session_state` em `app.py`
- A função em `app.py` chama `adapters/` para ler e depois actualiza o state

---

## RESTRIÇÕES

1. **NUNCA** importar `streamlit` em `core/` ou `adapters/`
2. **NUNCA** alterar `compile.py`, `preprocessor.py`, `semantic_type_registry.py` ou `filters/`
3. Manter backward compatibility — a app deve funcionar identicamente
4. Se uma função acede a `st.session_state` E faz lógica → separar: lógica vai para `core/`, acesso a state fica em `app.py`
5. Não introduzir dependências novas — usar só o que está em `requirements.txt`
6. Comentar código em português

---

## VERIFICAÇÃO

1. `streamlit run app.py` arranca sem erros
2. Nenhum import de `streamlit` em `core/` ou `adapters/`:
   ```bash
   grep -r "import streamlit" core/ adapters/
   # Resultado: vazio
   ```
3. Todas as tabs (TOC, Estrutura, Mapeamento) funcionam como antes
4. Carregar/guardar projectos funciona
5. Export/Import de YAML funciona

---

## ENTREGÁVEL

| Ficheiro | Estado |
|----------|--------|
| `core/__init__.py` | NOVO |
| `core/models.py` | NOVO |
| `core/services.py` | NOVO |
| `adapters/__init__.py` | NOVO |
| `adapters/yaml_io.py` | NOVO |
| `adapters/config.py` | NOVO |
| `app.py` | MODIFICADO (menos ~400-500 linhas) |

---

## REGRAS DE ARQUITECTURA (incluir em todos os prompts IDE futuros)

1. Nunca importar `streamlit` em ficheiros `core/` ou `adapters/`
2. Nunca importar `adapters/` ou `ui/` em ficheiros `core/`
3. Lógica de negócio nova → `core/services.py`
4. I/O de ficheiros novo → `adapters/`
5. UI nova → `ui/` (módulo existente ou novo)
6. `app.py` nunca excede 60 linhas (após Step 2)
7. Nenhum ficheiro em `ui/` excede 300 linhas — partir se necessário
8. Session state: só aceder via `ui/state.py` helpers (após Step 2)

---

**Fim — PROMPT-IDE-REFACTOR-STEP1.md — 2026-04-04**
