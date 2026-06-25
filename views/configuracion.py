"""pages/configuracion.py — Configuración del sistema"""
import streamlit as st
from auth import require_admin, ESTABLECIMIENTOS, PERIODOS_REPORTE, load_reports


def show(header_fn=None):
    require_admin()

    st.title("⚙️ Configuración del sistema")

    reports = load_reports()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información del sistema")
        st.markdown(f"""
        | Parámetro | Valor |
        |-----------|-------|
        | Versión plataforma | 1.0.0 |
        | Lineamiento | MINSAL v1.0 — Junio 2026 |
        | Meta institucional | ≤ 16% |
        | Establecimientos configurados | {len(ESTABLECIMIENTOS)} |
        | Períodos de reporte | {len(PERIODOS_REPORTE)} |
        | Reportes ingresados | {len(reports)} |
        | Enviados | {len([r for r in reports if r.get("estado")=="enviado"])} |
        | Borradores | {len([r for r in reports if r.get("estado")=="borrador"])} |
        """)

    with col2:
        st.subheader("Calendario de reportes")
        for p in PERIODOS_REPORTE:
            enviados = len([r for r in reports
                            if r.get("reporte_id")==p["id"] and r.get("estado")=="enviado"])
            total_req = len([e for e in ESTABLECIMIENTOS.values()
                             if e["nivel"] in ["rojo","amarillo"]])
            prog = int(enviados/total_req*100) if total_req else 0
            st.markdown(f"**{p['label']}** — {p['periodo']}  ")
            st.markdown(f"Plazo: `{p['fecha_limite']}` · Avance: {enviados}/{total_req}")
            st.progress(prog/100)

    st.divider()

    st.subheader("Datos de referencia — CSV MINSAL")
    import pandas as pd
    rows = []
    for eid, e in ESTABLECIMIENTOS.items():
        rows.append({
            "ID": eid, "Nombre": e["nombre"], "Código DEIS": e["codigo_deis"],
            "RUT": e["rut"], "% TD 2026": e["pct_2026"], "% TD 2025": e["pct_2025"],
            "Brecha": e["brecha"], "Variación": e["variacion"],
            "Denominador ($)": e["denominador"], "Numerador ($)": e["numerador"],
            "Nivel": e["nivel"].capitalize(),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    with st.expander("🗑️ Herramientas de mantenimiento"):
        st.warning("⚠️ Estas acciones son irreversibles.")
        if st.button("🗑️ Eliminar TODOS los reportes (reset)", type="secondary"):
            from auth import save_reports, REPORTS_FILE
            if REPORTS_FILE.exists():
                REPORTS_FILE.unlink()
            st.success("Todos los reportes eliminados.")
            st.rerun()
