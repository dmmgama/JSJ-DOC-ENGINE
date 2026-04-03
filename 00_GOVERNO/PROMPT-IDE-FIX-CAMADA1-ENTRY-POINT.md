# PROMPT IDE — JSJ-DOC-ENGINE — Fix: Entry Point Único na Camada 1

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Remover entry point duplicado de carregamento de `estrutura.yaml` na tab "Estrutura"
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**

---

## CONTEXTO

A app tem dois tabs: `"TOC / Compilar"` e `"Estrutura"`.

Na sidebar existe um `st.file_uploader` para importar `estrutura.yaml` — este é o **único** mecanismo de carregamento. Quando o utilizador importa o ficheiro, o estado fica em `st.session_state.estrutura_yaml_raw`.

A tab "Estrutura" (Camada 1) implementa um segundo mecanismo redundante: campo de texto para path + botão "Carregar ficheiro". Este segundo entry point:
- Não funciona quando o ficheiro já foi carregado via sidebar
- Cria confusão — o utilizador vê dois locais para fazer a mesma coisa
- É inconsistente com a arquitectura stateless da app (carregamento via sidebar → estado em session_state)

---

## PROBLEMA OBSERVADO

Na tab "Estrutura":
- Campo "Path do estrutura.yaml" com botão "Carregar ficheiro"
- Mensagem "Carregue um ficheiro estrutura.yaml para começar a editar."
- A tab não detecta que o ficheiro já está carregado na sidebar (`st.session_state.estrutura_yaml_raw` já existe)
- O utilizador não consegue editar mesmo com o ficheiro carregado

---

## TAREFA

Modificar `04_APP\app.py` — **apenas a tab "Estrutura"** (Camada 1):

### 1. Remover o entry point duplicado

Apagar da tab "Estrutura":
- O campo de texto "Path do estrutura.yaml"
- O botão "Carregar ficheiro"
- A mensagem "Carregue um ficheiro estrutura.yaml para começar a editar."
- Qualquer lógica de `_carregar_estrutura_yaml_ficheiro(path)` invocada a partir deste entry point

A função `_carregar_estrutura_yaml_ficheiro(path)` pode ser mantida se for usada noutro contexto (ex: guardar/exportar). Remover **apenas a sua invocação** a partir do entry point da tab.

### 2. Substituir por detecção de session state

No início da tab "Estrutura", verificar se `st.session_state.estrutura_yaml_raw` existe e não é None:

```python
# Lógica a implementar (conceito — adaptar ao código existente)
if not st.session_state.get("estrutura_yaml_raw"):
    st.info("Importe o ficheiro estrutura.yaml na sidebar para começar a editar.")
    st.stop()

# Se chegou aqui, o ficheiro está carregado — mostrar editor directamente
```

### 3. Comportamento esperado após o fix

| Estado da sidebar | Tab "Estrutura" mostra |
|-------------------|----------------------|
| Nenhum ficheiro carregado | Mensagem: "Importe o ficheiro estrutura.yaml na sidebar para começar a editar." |
| `estrutura.yaml` carregado | Editor completo directamente — sem pedir nada |

### 4. Mensagem de estado no topo da tab (opcional mas recomendado)

Se o ficheiro estiver carregado, mostrar no topo da tab:

```python
st.caption(f"A editar: {st.session_state.get('estrutura_yaml_path', 'ficheiro importado')}")
```

---

## RESTRIÇÕES

- **Não tocar** em nada fora da tab "Estrutura" no `app.py`
- **Não tocar** em `compile.py`, `preprocessor.py`, `requirements.txt`
- **Não alterar** o mecanismo de import/export da sidebar (Camada 3)
- **Não alterar** o tab "TOC / Compilar"
- A função `_guardar_estrutura_yaml_ficheiro(path, dict)` deve continuar a funcionar para o botão "Guardar"
- Comentários em português

---

## VERIFICAÇÃO

A tarefa está concluída quando:

1. `streamlit run app.py` arranca sem erros
2. Sem ficheiro carregado na sidebar → tab "Estrutura" mostra mensagem de instrução (sem campos de path nem botões de carregamento)
3. Com `estrutura.yaml` importado na sidebar → tab "Estrutura" abre directamente no editor (metadados + tipos + lista de elementos)
4. Tab "TOC / Compilar" não foi alterada — continua funcional
5. Botão "Guardar" na tab "Estrutura" continua a funcionar

---

## ENTREGÁVEL

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ modificado — entry point duplicado removido |

---

**Fim — PROMPT-IDE-FIX-CAMADA1-ENTRY-POINT.md — 2026-04-03**
