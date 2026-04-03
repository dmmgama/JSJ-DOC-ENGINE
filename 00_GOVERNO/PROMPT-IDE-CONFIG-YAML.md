# PROMPT IDE — JSJ-DOC-ENGINE — config.yaml multi-projecto + auto-load

> **Data:** 2026-04-03
> **Fase:** 2 — App Streamlit
> **Tarefa:** Substituir config.yaml (schema v0) pelo schema multi-projecto + integrar auto-load na app
> **Executar em:** VSCode + agente IDE
> **NÃO editar ficheiros fora de `04_APP\`**

---

## CONTEXTO

**Projecto:** JSJ-DOC-ENGINE — sistema local MD → DOCX via Pandoc + Streamlit.
**Raiz:** `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\`

O `config.yaml` actual (schema v0) é single-projecto e contém a lista de secções
inline — responsabilidade que passou para `estrutura.yaml` e `mapeamento.yaml`.
Precisa de ser substituído pelo schema multi-projecto definitivo.

A app arranca actualmente sem ler `config.yaml`. O utilizador importa
`estrutura.yaml` e `mapeamento.yaml` manualmente pela sidebar em cada sessão.
Após esta tarefa, a app lê `config.yaml` no arranque e carrega automaticamente
o último projecto usado (ou pede para escolher).

---

## ESTADO ACTUAL DE `04_APP\`

```
04_APP\
├── app.py                    ✅ Camada 1 v2 + Camada 3
├── compile.py                ✅ actualizado (lua filter + marcadores)
├── preprocessor.py           ✅
├── semantic_type_registry.py ✅
├── migrate_schema_v1_to_v2.py ✅
├── config.yaml               ⚠️ schema v0 — a substituir
├── filters\pagebreak.lua     ✅
├── requirements.txt          ✅
└── venv\
```

---

## TAREFA — 2 ENTREGAS

### ENTREGA 1 — Novo `config.yaml`

Substituir o conteúdo actual por este schema multi-projecto:

```yaml
# config.yaml — JSJ-DOC-ENGINE
# Fonte de verdade de todos os projectos/documentos.
# Editar manualmente para adicionar/remover projectos.
# A app lê este ficheiro no arranque.

defaults:
  templates_dir: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES"
  output_dir:    "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/03_OUTPUT"
  reference_doc: "C:/Users/JSJ/JSJ AI/JSJ-DOC-ENGINE/02_TEMPLATES/JSJ-CTE-reference.docx"

projects:
  - id:         CTE-SecI
    name:       "CTE Fundações e Estruturas"
    estrutura:  "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/estrutura_v2.yaml"
    mapeamento: "C:/Users/JSJ/JSJ AI/CTE/CTE-TEMPLATE-CLAUDE/mapeamento.yaml"
    variaveis:  ""   # opcional — deixar vazio se não existir

last_project: CTE-SecI
```

**Notas:**
- `last_project` guarda o id do último projecto carregado — a app actualiza este campo automaticamente
- `variaveis` é opcional — se vazio ou omitido, o preprocessor ignora
- Os paths são absolutos e específicos desta máquina (não versionar com paths de outras máquinas)

---

### ENTREGA 2 — Integrar auto-load na `app.py`

Modificar `app.py` para ler `config.yaml` no arranque e gerir projectos.

**2a. Funções de gestão do config (adicionar antes da sidebar)**

```python
# Conceito — adaptar ao estilo do código existente

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def carregar_config() -> dict:
    """Lê config.yaml. Devolve dict vazio se não existir."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def guardar_config(config: dict) -> None:
    """Escreve config.yaml com o estado actualizado."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

def carregar_projecto(projecto: dict) -> None:
    """
    Carrega estrutura.yaml e mapeamento.yaml do projecto para session_state.
    Actualiza estrutura_yaml_raw, estrutura_yaml_path, mapeamento_yaml_raw, mapeamento_yaml_path.
    """
    path_estrutura  = projecto.get("estrutura", "")
    path_mapeamento = projecto.get("mapeamento", "")

    if path_estrutura and Path(path_estrutura).exists():
        with open(path_estrutura, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        st.session_state.estrutura_yaml_raw  = raw
        st.session_state.estrutura_yaml_path = path_estrutura
    else:
        st.warning(f"estrutura.yaml não encontrado: {path_estrutura}")

    if path_mapeamento and Path(path_mapeamento).exists():
        with open(path_mapeamento, "r", encoding="utf-8") as f:
            st.session_state.mapeamento = yaml.safe_load(f) or {}
        st.session_state.mapeamento_yaml_path = path_mapeamento

    st.session_state.projecto_activo = projecto
```

**2b. Lógica de arranque (no topo da app, após inicializar_estado)**

```python
# Conceito — integrar na lógica de inicialização existente

config = carregar_config()
projectos = config.get("projects", [])
last_id   = config.get("last_project", "")

# Auto-load: se há um last_project e ainda não carregámos nada nesta sessão
if projectos and not st.session_state.get("projecto_carregado"):
    proj_default = next((p for p in projectos if p["id"] == last_id), projectos[0])
    carregar_projecto(proj_default)
    st.session_state.projecto_carregado = True
```

**2c. Sidebar — secção de gestão de projectos**

Substituir (ou complementar) os actuais file_uploader da sidebar por um
selector de projecto baseado no config.yaml:

```
────────────────────────────
JSJ-DOC-ENGINE

Projecto activo
[ CTE Fundações e Estruturas ▾ ]   ← st.selectbox com lista de projects
[ Carregar ]

─ ou ─
[ + Novo projecto ]   ← expander para adicionar manualmente paths
────────────────────────────
```

Comportamento do selectbox:
- Lista os `name` de todos os projectos em `config.projects`
- Ao carregar: chama `carregar_projecto()` + actualiza `last_project` no config.yaml
- Manter os file_uploader actuais como fallback ("Importar manualmente") dentro
  de um `st.expander("Importar manualmente", expanded=False)`

**2d. Expander "Novo projecto" (na sidebar)**

Quando o utilizador quer adicionar um projecto novo sem editar o YAML manualmente:

```
Nome do projecto:    [ _________________ ]
Path estrutura.yaml: [ _________________ ]
Path mapeamento.yaml:[ _________________ ]
Path variaveis.yaml: [ _________________ ]  (opcional)
[ Adicionar ao config.yaml ]
```

Ao submeter:
1. Valida que `nome` e `path_estrutura` não estão vazios
2. Gera `id` automaticamente a partir do nome (ex: "Projecto X" → "projecto-x")
3. Adiciona à lista `projects` e guarda `config.yaml`
4. Carrega o novo projecto imediatamente

---

## RESTRIÇÕES

- **Não tocar** em `compile.py`, `preprocessor.py`, `semantic_type_registry.py`, `filters\`
- **Não remover** os file_uploader actuais — colocá-los dentro de `st.expander("Importar manualmente")`
- `carregar_config()` deve ser tolerante a falhas: se `config.yaml` não existir ou estiver corrompido, a app arranca normalmente sem erro
- `guardar_config()` só escreve os campos que existiam — não inventar campos novos
- Comentar código em **português**
- Não introduzir dependências novas

---

## VERIFICAÇÃO

A tarefa está concluída quando:

1. `streamlit run app.py` arranca sem erros
2. No arranque, a sidebar mostra "CTE Fundações e Estruturas" como projecto activo
3. O `estrutura_v2.yaml` do CTE é carregado automaticamente (sem importar manualmente)
4. O selectbox de projecto lista todos os projectos do `config.yaml`
5. Mudar de projecto no selectbox + "Carregar" → carrega os ficheiros do novo projecto
6. O `last_project` no `config.yaml` é actualizado após carregar um projecto
7. "Importar manualmente" ainda funciona dentro do expander
8. "Novo projecto" adiciona entry ao `config.yaml` e carrega imediatamente
9. Tab "Estrutura" e tab "TOC / Compilar" continuam funcionais

---

## ENTREGÁVEIS

| Path | Alteração |
|------|-----------|
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\config.yaml` | ✅ substituído — schema multi-projecto |
| `C:\Users\JSJ\JSJ AI\JSJ-DOC-ENGINE\04_APP\app.py` | ✅ modificado — auto-load + sidebar projectos |

Após concluir, actualizar `04_APP\README.md` secção 10:
- `config.yaml` → ✅ schema multi-projecto funcional
- `app.py` → ✅ auto-load de projecto no arranque

---

**Fim — PROMPT-IDE-CONFIG-YAML.md — 2026-04-03**
