# DEBUG — app.py JSJ-DOC-ENGINE — Mapeamento não carrega dados

## PROBLEMA

A app Streamlit (`04_APP/app.py`) tem um bug na Camada 2 (tab Mapeamento).
O ficheiro `mapeamento.yaml` tem campos `md_source` preenchidos (ex: LEX e GERAL com paths de ficheiros .md), mas no tab Mapeamento da app os campos aparecem **sempre vazios** — só mostra o placeholder.

Além disso, ao reiniciar a app aparece intermitentemente:
```
AttributeError: st.session_state has no attribute "mapeamento"
```

## FICHEIROS RELEVANTES

```
C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py          ← app Streamlit (ficheiro principal)
C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\config.yaml     ← config multi-projecto
C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\semantic_type_registry.py  ← registry (não alterar)
```

Ficheiros de dados do projecto activo (paths no config.yaml):
```
C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\estrutura_v2.yaml
C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\mapeamento.yaml
```

## O QUE JÁ FOI TENTADO (sem sucesso)

1. config.yaml corrigido para apontar para ficheiros (não directórios)
2. `carregar_projecto()` faz fallback directório→ficheiro
3. `_renderizar_camada2()` alterada para inicializar widget keys no session_state antes de renderizar e não passar `value=` aos widgets
4. Limpeza de widget keys em `carregar_projecto()` após carregar mapeamento novo
5. Linha 876 alterada de `st.session_state.mapeamento` para `st.session_state.get("mapeamento")`
6. App reiniciada várias vezes, cache limpa

Nada disto resolveu. Os campos continuam vazios.

## TAREFA

1. **Lê** `app.py`, `config.yaml` e `mapeamento.yaml` (path no config.yaml)
2. **Corre** `streamlit run app.py` e observa o comportamento
3. **Diagnostica** a causa raiz de:
   - Os `md_source` do mapeamento.yaml não aparecerem nos widgets do tab Mapeamento
   - O AttributeError intermitente em `st.session_state.mapeamento`
4. **Corrige** o código — testa até funcionar
5. **Confirma** que:
   - App arranca sem erros
   - Tab Mapeamento mostra os `md_source` preenchidos (LEX e GERAL devem ter paths)
   - Editar um campo → guardar → reabrir → valor persiste
   - Tabs TOC e Estrutura continuam funcionais

## CONTEXTO TÉCNICO

- Stack: Python 3.x, Streamlit, PyYAML
- O Streamlit guarda valores de widgets no `session_state` usando a `key` do widget
- Quando uma key já existe no session_state, o Streamlit **ignora** o parâmetro `value=` e usa o valor da key
- O fluxo de dados é: `config.yaml` → `carregar_projecto()` → `parse_mapeamento_yaml()` → `st.session_state.mapeamento` → `_mapeamento_por_slug()` → `_renderizar_camada2()` → widgets
- A hipótese principal é que os widgets são renderizados com valores vazios antes do mapeamento ser carregado, e depois o Streamlit mantém os valores vazios nas keys
- O directório de trabalho para correr a app é `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\`

## RESTRIÇÕES

- Não alterar `semantic_type_registry.py`, `compile.py`, `preprocessor.py`, `filters/`
- Não alterar a lógica das tabs TOC e Estrutura excepto se necessário para o fix
- Comentários em português
- Não introduzir dependências novas
