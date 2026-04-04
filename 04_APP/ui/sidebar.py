"""
ui/sidebar.py — Sidebar da app.
Selectbox de projectos, criar/apagar projectos, import/export manual.
"""
import os, re
from pathlib import Path
import streamlit as st
import yaml

from core.services import migrar_v1_para_v2
from adapters.yaml_io import (
    exportar_ficheiro, gerar_estrutura_yaml, gerar_mapeamento_yaml,
    carregar_estrutura_yaml, parse_estrutura_yaml, parse_mapeamento_yaml,
)
from adapters.config import carregar_config, guardar_config
from ui.state import (
    clear_checkboxes, clear_map_keys, clear_project_state,
    get_elementos, get_estrutura_path, get_estrutura_raw,
    get_export_path_estrutura, get_export_path_mapeamento,
    get_projecto_activo, get_projecto_carregado, get_confirmar_apagar_proj,
    set_confirmar_apagar_proj, set_elementos, set_estrutura_path,
    set_estrutura_raw, set_export_path_estrutura, set_export_path_mapeamento,
    set_mapeamento, set_mapeamento_path, set_projecto_activo, set_projecto_carregado,
)


def carregar_projecto(projecto: dict) -> None:
    """Carrega estrutura.yaml e mapeamento.yaml do projecto para session_state."""
    path_estrutura = projecto.get("estrutura", "")
    path_mapeamento = projecto.get("mapeamento", "")

    # Fallback: se path é directório, tentar append do nome de ficheiro
    if path_estrutura and Path(path_estrutura).is_dir():
        for candidato in ("estrutura_v2.yaml", "estrutura.yaml"):
            p_cand = Path(path_estrutura) / candidato
            if p_cand.is_file():
                path_estrutura = str(p_cand)
                break
    if path_mapeamento and Path(path_mapeamento).is_dir():
        p_cand = Path(path_mapeamento) / "mapeamento.yaml"
        if p_cand.is_file():
            path_mapeamento = str(p_cand)

    if path_estrutura and Path(path_estrutura).is_file():
        raw = carregar_estrutura_yaml(path_estrutura)
        migrar_v1_para_v2(raw.get("elementos", []))
        set_estrutura_raw(raw)
        set_estrutura_path(path_estrutura)
        novos_elementos = parse_estrutura_yaml(
            yaml.dump(raw, allow_unicode=True, default_flow_style=False)
        )
        if novos_elementos:
            clear_checkboxes(get_elementos())
            set_elementos(novos_elementos)
    elif path_estrutura:
        st.warning(f"estrutura.yaml não encontrado: {path_estrutura}")

    if path_mapeamento and Path(path_mapeamento).is_file():
        with open(path_mapeamento, "r", encoding="utf-8") as f:
            conteudo_map = f.read()
        mapeamento_novo = parse_mapeamento_yaml(conteudo_map)
        clear_map_keys(mapeamento_novo.get("elementos", []))
        set_mapeamento(mapeamento_novo)
        set_mapeamento_path(path_mapeamento)

    set_projecto_activo({
        "id": projecto.get("id", ""),
        "name": projecto.get("name", ""),
        "reference_doc": projecto.get("reference_doc", ""),
    })


def render_sidebar(config: dict, paths_cfg: dict) -> None:
    """Renderiza a sidebar completa."""
    projectos = config.get("projects", [])
    last_id = config.get("last_project", "")
    if projectos and not get_projecto_carregado():
        proj_default = next((p for p in projectos if p["id"] == last_id), projectos[0])
        carregar_projecto(proj_default)
        set_projecto_carregado(True)

    with st.sidebar:
        st.title("JSJ-DOC-ENGINE")
        st.divider()
        _render_seleccao_projecto()
        st.divider()
        _render_novo_projecto()
        st.divider()
        _render_import_manual(paths_cfg)


def _render_seleccao_projecto() -> None:
    """Selectbox + botões Carregar / Reimportar / Apagar."""
    cfg = carregar_config()
    projs = cfg.get("projects", [])
    st.subheader("Projecto activo")

    if not projs:
        proj_disp = get_projecto_activo()
        st.markdown(f"**{proj_disp.get('name', '')}**")
        st.caption(f"ID: `{proj_disp.get('id', '')}`")
        return

    nomes = [p.get("name", p.get("id", "sem nome")) for p in projs]
    id_actual = get_projecto_activo().get("id", "")
    idx_actual = next((i for i, p in enumerate(projs) if p["id"] == id_actual), 0)
    idx_sel = st.selectbox("Projecto", options=range(len(nomes)),
                           format_func=lambda i: nomes[i], index=idx_actual,
                           key="sel_projecto", label_visibility="collapsed")

    col_load, col_reimp, col_del = st.columns([3, 2, 1])
    if col_load.button("Carregar", width="stretch", key="btn_carregar_proj"):
        proj_sel = projs[idx_sel]
        carregar_projecto(proj_sel)
        set_projecto_carregado(True)
        cfg["last_project"] = proj_sel["id"]
        guardar_config(cfg)
        st.toast(f"Projecto carregado: {proj_sel.get('name', proj_sel.get('id', '?'))}", icon="✅")
        st.rerun()

    if col_reimp.button("🔄 Reimportar", width="stretch", key="btn_reimportar_proj"):
        clear_project_state()
        st.toast("Dados limpos — clique Carregar ou importe manualmente.", icon="🔄")
        st.rerun()

    # Apagar (confirmação dois passos)
    if get_confirmar_apagar_proj():
        proj_nome = projs[idx_sel].get('name', projs[idx_sel].get('id', '?'))
        st.warning(f"Apagar projecto **{proj_nome}** e ficheiros do disco?")
        col_sim, col_nao = st.columns(2)
        if col_sim.button("✅ Sim, apagar", key="btn_confirm_del_proj"):
            proj_a_apagar = projs[idx_sel]
            for campo in ("estrutura", "mapeamento", "variaveis"):
                path_f = proj_a_apagar.get(campo, "")
                if path_f and Path(path_f).is_file():
                    try:
                        os.remove(path_f)
                    except Exception:
                        pass
            cfg["projects"] = [p for p in cfg["projects"] if p["id"] != proj_a_apagar["id"]]
            if cfg.get("last_project") == proj_a_apagar["id"]:
                cfg["last_project"] = cfg["projects"][0]["id"] if cfg["projects"] else ""
            guardar_config(cfg)
            if get_projecto_activo().get("id") == proj_a_apagar["id"]:
                clear_project_state()
                set_projecto_activo({"id": "", "name": "", "reference_doc": ""})
            set_confirmar_apagar_proj(False)
            st.toast(f"Projecto apagado: {proj_a_apagar.get('name', proj_a_apagar.get('id', '?'))}", icon="✅")
            st.rerun()
        if col_nao.button("❌ Cancelar", key="btn_cancel_del_proj"):
            set_confirmar_apagar_proj(False)
            st.rerun()
    else:
        if col_del.button("🗑", key="btn_del_proj", help="Apagar projecto e ficheiros"):
            set_confirmar_apagar_proj(True)
            st.rerun()


def _render_novo_projecto() -> None:
    """Formulário para criar um novo projecto."""
    with st.expander("+ Novo projecto", expanded=False):
        cfg = carregar_config()
        with st.form(key="form_novo_proj", clear_on_submit=True):
            np_nome = st.text_input("Nome do projecto")
            np_estrutura = st.text_input("Path estrutura.yaml",
                                          placeholder=r"C:\caminho\para\estrutura.yaml")
            st.caption("Path do ficheiro .yaml, não da pasta")
            np_mapeamento = st.text_input("Path mapeamento.yaml",
                                           placeholder=r"C:\caminho\para\mapeamento.yaml")
            st.caption("Path do ficheiro .yaml, não da pasta")
            np_variaveis = st.text_input("Path variaveis.yaml (opcional)",
                                          placeholder=r"C:\caminho\para\variaveis.yaml")
            np_reference = st.text_input("Template DOCX (reference.docx)",
                                          placeholder=r"C:\caminho\para\reference.docx",
                                          value=cfg.get("defaults", {}).get("reference_doc", ""))
            st.caption("Deixar vazio para usar o template por defeito em defaults.")
            submitted = st.form_submit_button("💾 Gravar projecto", use_container_width=True)

        if submitted:
            if not np_nome.strip():
                st.error("O nome do projecto não pode estar vazio.")
            elif not np_estrutura.strip():
                st.error("O path de estrutura.yaml não pode estar vazio.")
            else:
                novo_id = re.sub(r"[^a-z0-9]+", "-", np_nome.strip().lower()).strip("-")
                cfg_add = carregar_config()
                ids_existentes = {p["id"] for p in cfg_add.get("projects", [])}
                if novo_id in ids_existentes:
                    novo_id = f"{novo_id}-{len(ids_existentes) + 1}"
                est_path = np_estrutura.strip()
                if est_path and Path(est_path).is_dir():
                    for cand in ("estrutura_v2.yaml", "estrutura.yaml"):
                        if (Path(est_path) / cand).is_file():
                            est_path = str(Path(est_path) / cand)
                            break
                    else:
                        est_path = str(Path(est_path) / "estrutura.yaml")
                map_path = np_mapeamento.strip()
                if map_path and Path(map_path).is_dir():
                    map_path = str(Path(map_path) / "mapeamento.yaml")
                novo_proj = {
                    "id": novo_id, "name": np_nome.strip(),
                    "estrutura": est_path, "mapeamento": map_path,
                    "variaveis": np_variaveis.strip(), "reference_doc": np_reference.strip(),
                }
                if "projects" not in cfg_add:
                    cfg_add["projects"] = []
                cfg_add["projects"].append(novo_proj)
                cfg_add["last_project"] = novo_id
                guardar_config(cfg_add)
                carregar_projecto(novo_proj)
                set_projecto_carregado(True)
                st.toast(f"Projecto gravado: {np_nome.strip()}", icon="✅")
                st.rerun()


def _render_import_manual(paths_cfg: dict) -> None:
    """Import/export manual de estrutura.yaml e mapeamento.yaml."""
    with st.expander("Importar manualmente", expanded=False):
        # ── estrutura.yaml ───────────────────────────────────────────
        st.subheader("estrutura.yaml")
        export_path_est = st.text_input(
            "Path de exportação",
            value=(get_export_path_estrutura() or get_estrutura_path()
                   or paths_cfg.get("estrutura", "")),
            key="input_path_estrutura",
            placeholder=r"C:\caminho\para\estrutura.yaml",
        )
        set_export_path_estrutura(export_path_est)

        if st.button("Exportar estrutura.yaml", width="stretch"):
            if not export_path_est.strip():
                st.error("Defina o path de exportação antes de exportar.")
            else:
                conteudo = gerar_estrutura_yaml(get_elementos(), get_projecto_activo())
                ok, msg = exportar_ficheiro(conteudo, export_path_est.strip())
                st.success(msg) if ok else st.error(msg)

        ficheiro_est = st.file_uploader("Importar estrutura.yaml",
                                         type=["yaml", "yml"], key="uploader_estrutura")
        if ficheiro_est is not None:
            conteudo_est = ficheiro_est.read().decode("utf-8")
            dados_raw = yaml.safe_load(conteudo_est) or {}
            migrar_v1_para_v2(dados_raw.get("elementos", []))
            if dados_raw != get_estrutura_raw():
                set_estrutura_raw(dados_raw)
                set_estrutura_path(ficheiro_est.name)
            novos_elementos = parse_estrutura_yaml(conteudo_est)
            if novos_elementos:
                slugs_novos = {el["slug"] for el in novos_elementos}
                slugs_actuais = {el["slug"] for el in get_elementos()}
                if slugs_novos != slugs_actuais:
                    clear_checkboxes(get_elementos())
                    set_elementos(novos_elementos)
                    st.toast(f"Estrutura importada: {len(novos_elementos)} elementos.", icon="✅")
                    st.rerun()
            else:
                st.warning("Nenhum elemento encontrado no ficheiro importado.")

        st.divider()

        # ── mapeamento.yaml ──────────────────────────────────────────
        st.subheader("mapeamento.yaml")
        export_path_map = st.text_input(
            "Path de exportação",
            value=get_export_path_mapeamento() or paths_cfg.get("mapeamento", ""),
            key="input_path_mapeamento",
            placeholder=r"C:\caminho\para\mapeamento.yaml",
        )
        set_export_path_mapeamento(export_path_map)

        if st.button("Exportar mapeamento.yaml", width="stretch"):
            if not export_path_map.strip():
                st.error("Defina o path de exportação antes de exportar.")
            else:
                conteudo = gerar_mapeamento_yaml(get_elementos(), get_projecto_activo())
                ok, msg = exportar_ficheiro(conteudo, export_path_map.strip())
                st.success(msg) if ok else st.error(msg)

        ficheiro_map = st.file_uploader("Importar mapeamento.yaml",
                                         type=["yaml", "yml"], key="uploader_mapeamento")
        if ficheiro_map is not None:
            conteudo_map = ficheiro_map.read().decode("utf-8")
            mapeamento_importado = parse_mapeamento_yaml(conteudo_map)
            clear_map_keys(mapeamento_importado.get("elementos", []))
            set_mapeamento(mapeamento_importado)
            n_el = len(mapeamento_importado.get("elementos", []))
            st.toast(f"Mapeamento importado: {n_el} elementos.", icon="✅")
