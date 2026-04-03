# PROMPT IDE — JSJ-DOC-ENGINE — Bugfix App.py v1

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Corrigir 4 bugs na app.py + adicionar campo template ao config
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**

---

## CONTEXTO

**Stack:** Python 3.x, Streamlit, PyYAML
**Ficheiros a alterar:** `04_APP/app.py`, `04_APP/config.yaml`
**Ficheiros de referência (não alterar):** `semantic_type_registry.py`, `compile.py`, `preprocessor.py`

A app tem 3 tabs: TOC/Compilar, Estrutura, Mapeamento.
Multi-projecto via `config.yaml` com lista `projects[]`.

---

## ESTADO ACTUAL DO config.yaml

```yaml
defaults:
  output_dir: C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/03_OUTPUT
  reference_doc: C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx
  templates_dir: C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES
last_project: cte
projects:
- estrutura: C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE
  id: cte
  mapeamento: C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE
  name: cte
  variaveis: ''
```

**Problema:** Os campos `estrutura` e `mapeamento` apontam para **directórios**, não para ficheiros.
A função `carregar_projecto()` testa `Path(path).is_file()` → falha → nada é carregado.

---

## BUGS A CORRIGIR

### BUG 1 — config.yaml guarda directórios em vez de ficheiros

**Causa:** O formulário "Novo projecto" (sidebar) aceita qualquer path e grava-o tal qual no config.yaml. Não valida se é ficheiro ou directório.

**Correcção em `carregar_projecto()`:**
- Se o path existe como directório, tentar append do nome de ficheiro esperado:
  - `estrutura` → append `estrutura.yaml` (ou `estrutura_v2.yaml` — testar ambos)
  - `mapeamento` → append `mapeamento.yaml`
- Se o path com append existe como ficheiro → usar esse path
- Se nenhum existe → warning como já faz

**Correcção no formulário "Novo projecto":**
- Após submit, se o path é um directório, fazer o append automaticamente e gravar o path completo no config.yaml
- Adicionar `st.caption` abaixo de cada campo explicando: "Path do ficheiro .yaml, não da pasta"

**Correcção manual do config.yaml existente:**
- Actualizar o projecto `cte` para paths correctos:
```yaml
projects:
- id: cte
  name: cte
  estrutura: C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\estrutura_v2.yaml
  mapeamento: C:\Users\JSJ\JSJ AI\CTE\CTE-TEMPLATE-CLAUDE\mapeamento.yaml
  variaveis: ''
  reference_doc: ''
```

---

### BUG 2 — Mapeamento carregado do disco não aparece nos widgets da Camada 2

**Este é o bug mais crítico.** O mapeamento.yaml tem `md_source` preenchidos (e.g., LEX, GERAL), mas no tab Mapeamento os campos aparecem vazios.

**Causa raiz — ciclo vicioso de widget state no Streamlit:**

1. Na primeira renderização, os widgets `text_input` recebem `value=""` porque o mapeamento ainda não foi carregado
2. O Streamlit guarda o valor de cada widget no `session_state` usando a `key` (e.g., `map_LEX_md_source`)
3. `_renderizar_camada2()` nas linhas 843-845 **sobrescreve** `st.session_state.mapeamento["elementos"]` com os valores actuais dos widgets — que são vazios
4. Em reruns subsequentes, o Streamlit ignora o parâmetro `value=` e usa o valor da key — que é vazio
5. Resultado: os dados do mapeamento.yaml são **permanentemente perdidos** assim que o tab renderiza

**Correcção — estratégia:**

A solução correcta é **nunca usar `value=` directamente; usar `st.session_state[key]` para inicializar os widgets antes da renderização**.

Implementar assim:

```python
def _renderizar_camada2(elementos_flat: list, map_actual: dict) -> None:
    MD_SCOPE_OPCOES = ["ficheiro_inteiro", "heading_especifico"]
    novo_mapeamento_elementos = []

    for el in elementos_flat:
        slug          = el["slug"]
        titulo        = el["titulo"]
        semantic_type = el["semantic_type"]
        prof          = el["profundidade"]

        margem = "\u3000" * prof

        # Valores do mapeamento carregado
        map_el = map_actual.get(slug, {})

        # ── CHAVE: inicializar widget keys no session_state SE ainda não existirem ──
        # Isto garante que o primeiro rerun usa os valores do mapeamento,
        # e reruns seguintes preservam o que o utilizador editou.
        key_md   = f"map_{slug}_md_source"
        key_sc   = f"map_{slug}_md_scope"
        key_tpl  = f"map_{slug}_template"
        key_nota = f"map_{slug}_nota"

        if key_md not in st.session_state:
            st.session_state[key_md]   = map_el.get("md_source", "")
        if key_sc not in st.session_state:
            scope_val = map_el.get("md_scope", "ficheiro_inteiro")
            st.session_state[key_sc] = scope_val
        if key_tpl not in st.session_state:
            st.session_state[key_tpl]  = map_el.get("template_docx", "default")
        if key_nota not in st.session_state:
            st.session_state[key_nota] = map_el.get("nota", "")

        with st.expander(
            f"{margem}**{slug}** · *{semantic_type}* — {titulo}",
            expanded=(st.session_state[key_md] == ""),
        ):
            col1, col2 = st.columns([3, 1])

            # NÃO passar value= — o Streamlit usa o valor de session_state[key]
            md_source = col1.text_input(
                "Ficheiro MD (path absoluto)",
                key=key_md,
                placeholder=r"C:\caminho\para\ficheiro.md",
            )

            md_scope = col2.selectbox(
                "Scope",
                MD_SCOPE_OPCOES,
                key=key_sc,
            )

            col3, col4 = st.columns([3, 1])

            template_docx = col3.text_input(
                "Template DOCX (deixar 'default' para usar o geral)",
                key=key_tpl,
            )

            nota = col4.text_input(
                "Nota",
                key=key_nota,
            )

            if md_source and not Path(md_source).exists():
                st.warning(f"⚠️ Ficheiro não encontrado: {md_source}")
            elif md_source:
                st.success("✅ Ficheiro encontrado")

        novo_mapeamento_elementos.append({
            "slug":          slug,
            "md_source":     md_source,
            "md_scope":      md_scope,
            "template_docx": template_docx,
            "nota":          nota,
        })

    # Guardar em session_state
    if not st.session_state.mapeamento:
        st.session_state.mapeamento = {}
    st.session_state.mapeamento["elementos"] = novo_mapeamento_elementos

    # ... resto do código (botão guardar) sem alterações
```

**Adicionalmente**, em `carregar_projecto()`, após carregar o mapeamento com sucesso, **limpar as widget keys antigas** para forçar reinicialização:

```python
def carregar_projecto(projecto: dict) -> None:
    # ... (código existente de carregar estrutura) ...

    if path_mapeamento and Path(path_mapeamento).is_file():
        with open(path_mapeamento, "r", encoding="utf-8") as f:
            conteudo_map = f.read()
        mapeamento_novo = parse_mapeamento_yaml(conteudo_map)

        # ── Limpar widget keys da Camada 2 para forçar reinicialização ──
        # Sem isto, os widgets mantêm os valores da sessão anterior
        for el in mapeamento_novo.get("elementos", []):
            slug = el.get("slug", "")
            for sufixo in ("_md_source", "_md_scope", "_template", "_nota"):
                key = f"map_{slug}{sufixo}"
                if key in st.session_state:
                    del st.session_state[key]

        st.session_state.mapeamento           = mapeamento_novo
        st.session_state.mapeamento_yaml_path = path_mapeamento
```

**Mesma limpeza** no import manual via sidebar (secção `ficheiro_map is not None`):
- Após `parse_mapeamento_yaml()`, limpar as widget keys dos slugs do mapeamento importado
- Remover a comparação `meta_nova != meta_actual` — substituir por comparação completa ou simplesmente importar sempre (o ficheiro só é processado quando o utilizador faz upload)

```python
if ficheiro_map is not None:
    conteudo_map = ficheiro_map.read().decode("utf-8")
    mapeamento_importado = parse_mapeamento_yaml(conteudo_map)
    # Limpar widget keys para forçar reinicialização
    for el in mapeamento_importado.get("elementos", []):
        slug = el.get("slug", "")
        for sufixo in ("_md_source", "_md_scope", "_template", "_nota"):
            key = f"map_{slug}{sufixo}"
            if key in st.session_state:
                del st.session_state[key]
    st.session_state.mapeamento = mapeamento_importado
    n_el = len(mapeamento_importado.get("elementos", []))
    st.toast(f"✅ Mapeamento importado: {n_el} elementos.", icon="✅")
```

---

### BUG 3 — Botão apagar projecto (🗑) não reage

**Causa provável:** conflito de state entre `st.selectbox` e `st.button` no mesmo ciclo de rerun. Quando o botão é clicado, o Streamlit pode disparar o callback do selectbox primeiro, consumindo o rerun.

**Correcção:**
Usar `st.button` com um mecanismo de confirmação em dois passos (similar ao que já existe para remover elementos na Camada 1):

```python
# Adicionar ao session_state em inicializar_estado():
if "confirmar_apagar_proj" not in st.session_state:
    st.session_state.confirmar_apagar_proj = False

# Na sidebar, substituir o bloco actual do botão 🗑:
if st.session_state.confirmar_apagar_proj:
    st.warning(f"Apagar projecto **{_projs_sb[_idx_sel]['name']}** e os seus ficheiros YAML do disco?")
    col_sim, col_nao = st.columns(2)
    if col_sim.button("✅ Sim, apagar", key="btn_confirm_del_proj"):
        _proj_a_apagar = _projs_sb[_idx_sel]

        # 1. Apagar ficheiros YAML do disco (se existirem)
        for campo in ("estrutura", "mapeamento", "variaveis"):
            path_f = _proj_a_apagar.get(campo, "")
            if path_f and Path(path_f).is_file():
                try:
                    os.remove(path_f)
                except Exception:
                    pass  # Não bloquear se ficheiro não apagável

        # 2. Remover do config.yaml
        _cfg_sb["projects"] = [
            p for p in _cfg_sb["projects"] if p["id"] != _proj_a_apagar["id"]
        ]
        if _cfg_sb.get("last_project") == _proj_a_apagar["id"]:
            _cfg_sb["last_project"] = (
                _cfg_sb["projects"][0]["id"] if _cfg_sb["projects"] else ""
            )
        guardar_config(_cfg_sb)

        # 3. Limpar session_state se era o projecto activo
        if st.session_state.projecto_activo.get("id") == _proj_a_apagar["id"]:
            st.session_state.estrutura_yaml_raw   = {}
            st.session_state.estrutura_yaml_path  = ""
            st.session_state.mapeamento           = {}
            st.session_state.mapeamento_yaml_path = ""
            st.session_state.projecto_activo      = {"id": "", "name": ""}
            st.session_state.projecto_carregado   = False
            # Limpar widget keys da Camada 2
            keys_to_del = [k for k in st.session_state if k.startswith("map_")]
            for k in keys_to_del:
                del st.session_state[k]

        st.session_state.confirmar_apagar_proj = False
        st.toast(f"✅ Projecto apagado: {_proj_a_apagar['name']}", icon="✅")
        st.rerun()

    if col_nao.button("❌ Cancelar", key="btn_cancel_del_proj"):
        st.session_state.confirmar_apagar_proj = False
        st.rerun()
else:
    if col_del.button("🗑", key="btn_del_proj", help="Apagar projecto e ficheiros"):
        st.session_state.confirmar_apagar_proj = True
        st.rerun()
```

---

### BUG 4 — Sem campo "template" (reference_doc) no formulário de novo projecto

**Causa:** O formulário "Novo projecto" não tem campo para `reference_doc`. O mapeamento.yaml ao guardar usa fallback hardcoded.

**Correcção no formulário "Novo projecto":**

Adicionar campo `reference_doc` ao `st.form`:

```python
with st.form(key="form_novo_proj", clear_on_submit=True):
    _np_nome        = st.text_input("Nome do projecto")
    _np_estrutura   = st.text_input("Path estrutura.yaml",
                                     placeholder=r"C:\caminho\para\estrutura.yaml")
    _np_mapeamento  = st.text_input("Path mapeamento.yaml",
                                     placeholder=r"C:\caminho\para\mapeamento.yaml")
    _np_variaveis   = st.text_input("Path variaveis.yaml (opcional)",
                                     placeholder=r"C:\caminho\para\variaveis.yaml")
    _np_reference   = st.text_input("Template DOCX (reference.docx)",
                                     placeholder=r"C:\caminho\para\reference.docx",
                                     value=_cfg_sb.get("defaults", {}).get("reference_doc", ""))
    st.caption("Deixar vazio para usar o template por defeito em defaults.")
    _submitted = st.form_submit_button("💾 Gravar projecto", use_container_width=True)
```

**Gravar `reference_doc` no projecto:**

```python
_novo_proj = {
    "id":            _novo_id,
    "name":          _np_nome.strip(),
    "estrutura":     _np_estrutura.strip(),
    "mapeamento":    _np_mapeamento.strip(),
    "variaveis":     _np_variaveis.strip(),
    "reference_doc": _np_reference.strip(),
}
```

**Actualizar `carregar_projecto()` para guardar `reference_doc` no projecto_activo:**

```python
st.session_state.projecto_activo = {
    "id":            projecto.get("id", ""),
    "name":          projecto.get("name", ""),
    "reference_doc": projecto.get("reference_doc", ""),
}
```

**Actualizar `_renderizar_camada2()` botão guardar — usar `reference_doc` do projecto em vez de hardcoded:**

```python
# No bloco de guardar mapeamento.yaml:
_defaults_cfg = carregar_config().get("defaults", {})
_ref_doc = (
    st.session_state.projecto_activo.get("reference_doc")
    or _defaults_cfg.get("reference_doc", "")
)
dados_export = {
    ...
    "templates": {
        "geral": _ref_doc,
    },
    ...
}
```

---

## RESTRIÇÕES

- **Não tocar** em `compile.py`, `preprocessor.py`, `semantic_type_registry.py`, `filters/`
- **Não alterar** a lógica das tabs TOC e Estrutura excepto onde indicado para limpeza de widget keys
- Comentários em **português**
- Não introduzir dependências novas
- Manter `sort_keys=False` em todos os `yaml.dump()`
- O import de `os` já existe no topo do ficheiro

---

## VERIFICAÇÃO

1. `streamlit run app.py` arranca sem erros
2. Projecto `cte` carrega automaticamente com paths correctos de estrutura e mapeamento
3. Tab Mapeamento mostra os `md_source` preenchidos do mapeamento.yaml (LEX e GERAL devem ter paths)
4. Editar um `md_source` no tab Mapeamento → guardar → reabrir → valor persiste
5. Botão 🗑 na sidebar abre confirmação → "Sim" apaga projecto do config.yaml E ficheiros do disco
6. Formulário "Novo projecto" tem campo "Template DOCX"
7. Criar novo projecto com paths de **directórios** → app faz append automático dos nomes de ficheiro
8. Tabs TOC e Estrutura continuam funcionais
9. Import manual de mapeamento.yaml na sidebar → paths aparecem no tab Mapeamento

---

## ENTREGÁVEL

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ modificado — 4 bugs corrigidos |
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\config.yaml` | ✅ modificado — projecto cte com paths de ficheiros + campo reference_doc |

---

## RESUMO DAS ALTERAÇÕES (checklist para o agente)

- [ ] `config.yaml`: corrigir paths do projecto `cte` para ficheiros (não directórios)
- [ ] `inicializar_estado()`: adicionar `confirmar_apagar_proj` ao session_state
- [ ] `carregar_projecto()`: fallback directório→ficheiro + limpar widget keys da Camada 2
- [ ] Sidebar import mapeamento: remover comparação `meta_nova != meta_actual`, limpar widget keys
- [ ] Sidebar apagar projecto: confirmação em dois passos + apagar ficheiros do disco
- [ ] Sidebar novo projecto: campo `reference_doc` + auto-append se path é directório
- [ ] `_renderizar_camada2()`: inicializar widget keys no session_state antes de renderizar, não passar `value=`
- [ ] Guardar mapeamento: usar `reference_doc` do projecto_activo em vez de hardcoded

---

**Fim — PROMPT-IDE-BUGFIX-APP-V1.md — 2026-04-03**
