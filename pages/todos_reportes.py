"""pages/todos_reportes.py — Vista consolidada de todos los reportes (admin)"""
import streamlit as st
import pandas as pd
from auth import (require_admin, ESTABLECIMIENTOS, PERIODOS_REPORTE,
                  load_reports, upsert_report)


def show():
    user = require_admin()

    st.title("📁 Todos los reportes — Vista consolidada")
    st.caption("Solo administradores del SSMOC pueden acceder a esta sección.")

    reports = load_reports()

    # ── Filtros ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_periodo = st.selectbox(
            "Período",
            options=["Todos"] + [p["id"] for p in PERIODOS_REPORTE],
            format_func=lambda x: "Todos los períodos" if x == "Todos" else
                next(p["label"] + " — " + p["periodo"] for p in PERIODOS_REPORTE if p["id"]==x),
        )
    with col2:
        filtro_nivel = st.selectbox("Nivel de riesgo", ["Todos", "Rojo", "Amarillo", "Verde"])
    with col3:
        filtro_estado = st.selectbox("Estado", ["Todos", "Enviado", "Borrador", "Pendiente"])

    # ── Tabla de estado completa ──────────────────────────────────────
    st.subheader("Estado de todos los establecimientos")

    rows = []
    for eid, e in ESTABLECIMIENTOS.items():
        if e["nivel"] == "verde":
            continue  # verde no reporta
        row = {
            "Establecimiento": e["nombre_corto"],
            "Nivel": e["nivel"].capitalize(),
            "% TD 2026": f"{e['pct_2026']:.2f}%",
            "Brecha": f"{'+' if e['brecha']>0 else ''}{e['brecha']:.1f} pp",
        }
        for p in PERIODOS_REPORTE:
            r = next((x for x in reports
                      if x.get("establecimiento_id")==eid and x.get("reporte_id")==p["id"]), None)
            if r:
                e_str = r.get("estado","borrador")
                row[p["label"]] = "✅ Enviado" if e_str=="enviado" else "📝 Borrador"
            else:
                row[p["label"]] = "⬜ Pendiente"
        rows.append(row)

    df_all = pd.DataFrame(rows)
    st.dataframe(df_all, use_container_width=True, hide_index=True)

    st.divider()

    # ── Detalle de reportes enviados ──────────────────────────────────
    st.subheader("Detalle de reportes ingresados")

    filtered = reports
    if filtro_periodo != "Todos":
        filtered = [r for r in filtered if r.get("reporte_id") == filtro_periodo]
    if filtro_nivel != "Todos":
        filtered = [r for r in filtered if r.get("nivel_riesgo","").lower() == filtro_nivel.lower()]
    if filtro_estado != "Todos":
        filtered = [r for r in filtered if r.get("estado","").lower() == filtro_estado.lower()]

    if not filtered:
        st.info("No hay reportes que coincidan con los filtros seleccionados.")
        return

    for r in sorted(filtered, key=lambda x: (x.get("reporte_id",""), x.get("nivel_riesgo",""))):
        estab = ESTABLECIMIENTOS.get(r["establecimiento_id"], {})
        nivel = r.get("nivel_riesgo", "verde")
        estado = r.get("estado", "borrador")

        nivel_bg  = {"rojo":"#FCEBEB","amarillo":"#FAEEDA","verde":"#EAF3DE"}.get(nivel,"#eee")
        nivel_tc  = {"rojo":"#A32D2D","amarillo":"#633806","verde":"#27500A"}.get(nivel,"#333")
        est_icon  = "✅" if estado == "enviado" else "📝"

        with st.expander(
            f"{est_icon} {r.get('establecimiento_nombre','')[:50]} — {r.get('periodo_label','')} — {estado.upper()}"
        ):
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Nivel", nivel.capitalize())
            col_b.metric("% TD 2026", f"{r.get('pct_td_2026', 0):.2f}%")
            col_c.metric("% TD período", f"{r.get('pct_td_periodo', 0):.2f}%")
            col_d.metric("N° procesos TD", r.get("n_procesos_td", "—"))

            st.markdown("**Causales identificadas:**")
            for causal in r.get("causas_sel", []):
                st.markdown(f"- {causal}")

            if r.get("causas_descripcion"):
                st.markdown("**Descripción de causas:**")
                st.markdown(f"> {r.get('causas_descripcion','')}")

            if r.get("medidas_descripcion"):
                st.markdown("**Medidas implementadas:**")
                st.markdown(f"> {r.get('medidas_descripcion','')}")

            if r.get("compromisos"):
                st.markdown("**Compromisos:**")
                st.markdown(f"> {r.get('compromisos','')}")

            st.markdown(f"""
            **Responsable:** {r.get('responsable_nombre','')} · {r.get('responsable_cargo','')} · {r.get('responsable_email','')}  
            **Meta próximo período:** {r.get('meta_proxima',16):.1f}% · **Fecha compromiso:** {r.get('fecha_compromiso','')}  
            **Ingresado por:** {r.get('usuario_ingreso','')} · {r.get('fecha_ingreso','')[:16]}
            """)

            # Botón cambiar estado (admin)
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                if estado == "borrador":
                    if st.button(f"✅ Marcar como enviado", key=f"mark_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"] = "enviado"
                        upsert_report(r)
                        st.success("Marcado como enviado.")
                        st.rerun()
                else:
                    if st.button(f"↩️ Volver a borrador", key=f"unmark_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"] = "borrador"
                        upsert_report(r)
                        st.rerun()
