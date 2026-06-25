"""pages/exportar.py — Exportar reporte consolidado para MINSAL (Anexo N°1)"""
import io, datetime
import streamlit as st
import pandas as pd
from auth import require_admin, ESTABLECIMIENTOS, PERIODOS_REPORTE, load_reports


def show(header_fn=None):
    require_admin()

    st.title("📤 Exportar reporte consolidado — Formato MINSAL")
    st.caption("Genera el Anexo N°1 según el Lineamiento MINSAL v1.0 (Junio 2026).")

    reports = load_reports()

    # ── Selección de período ──────────────────────────────────────────
    periodo_sel = st.selectbox(
        "Seleccionar período a exportar",
        options=[p["id"] for p in PERIODOS_REPORTE],
        format_func=lambda x: next(f"{p['label']} — {p['periodo']} (plazo: {p['fecha_limite']})"
                                   for p in PERIODOS_REPORTE if p["id"]==x),
    )
    periodo_info = next(p for p in PERIODOS_REPORTE if p["id"] == periodo_sel)

    filtro_estado = st.radio("Incluir reportes en estado:", ["Enviado", "Todos (enviado + borrador)"],
                             horizontal=True)

    # Filtrar reportes
    r_periodo = [r for r in reports if r.get("reporte_id") == periodo_sel]
    if filtro_estado == "Enviado":
        r_periodo = [r for r in r_periodo if r.get("estado") == "enviado"]

    # ── Preview ───────────────────────────────────────────────────────
    st.subheader("Vista previa del archivo")

    if not r_periodo:
        st.warning(f"No hay reportes {filtro_estado.lower()} para el período {periodo_info['label']}.")
        # Mostrar qué falta
        st.markdown("**Establecimientos que aún no han enviado su reporte:**")
        for eid, e in ESTABLECIMIENTOS.items():
            if e["nivel"] in ["rojo","amarillo"]:
                r = next((x for x in reports if x.get("establecimiento_id")==eid
                          and x.get("reporte_id")==periodo_sel), None)
                est_icon = "⬜" if not r else ("✅" if r.get("estado")=="enviado" else "📝")
                st.markdown(f"{est_icon} {e['nombre']} — nivel {e['nivel'].capitalize()}")
        return

    # Construir DataFrame Anexo N°1
    rows = []
    for r in r_periodo:
        medidas = r.get("medidas_checks", {})
        medidas_impl = ", ".join(k.replace("_"," ").title()
                                  for k, v in medidas.items() if v)

        causas = "; ".join(r.get("causas_sel", []))
        if r.get("causas_descripcion"):
            causas += "\n\n" + r.get("causas_descripcion","")

        rows.append({
            "Servicio de Salud":          "Metropolitano Occidente",
            "Establecimiento":            r.get("establecimiento_nombre",""),
            "Código DEIS":                ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("codigo_deis",""),
            "RUT":                        ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("rut",""),
            "Nivel de Riesgo":            r.get("nivel_riesgo","").capitalize(),
            "Período informado":          r.get("periodo",""),
            "% TD 2026 (MINSAL)":         r.get("pct_td_2026",""),
            "% TD 2025 (mismo período)":  r.get("pct_td_periodo",""),
            "Brecha vs meta (pp)":        ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("brecha",""),
            "Variación vs 2025 (pp)":     ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("variacion",""),
            "Monto TD período (CLP)":     r.get("monto_td",0),
            "N° procesos TD":             r.get("n_procesos_td",0),
            "Principales causas":         causas,
            "Medidas implementadas":      medidas_impl + ("\n\n" + r.get("medidas_descripcion","") if r.get("medidas_descripcion") else ""),
            "Compromisos":                r.get("compromisos",""),
            "Meta próximo período (%)":   r.get("meta_proxima",""),
            "Responsable":                r.get("responsable_nombre",""),
            "Cargo":                      r.get("responsable_cargo",""),
            "Correo responsable":         r.get("responsable_email",""),
            "Fecha comprometida":         r.get("fecha_compromiso",""),
            "Observaciones":              r.get("observaciones",""),
            "Estado reporte":             r.get("estado","").upper(),
            "Fecha ingreso plataforma":   r.get("fecha_ingreso","")[:16],
        })

    df_export = pd.DataFrame(rows)
    st.dataframe(df_export, use_container_width=True, hide_index=True)

    st.markdown(f"**{len(rows)} establecimiento(s) incluido(s)** | Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # ── Botones de descarga ───────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            # Hoja Anexo N°1
            df_export.to_excel(writer, sheet_name="Anexo N°1 MINSAL", index=False)

            # Hoja resumen
            resumen_rows = []
            for eid, e in ESTABLECIMIENTOS.items():
                r = next((x for x in r_periodo if x.get("establecimiento_id")==eid), None)
                resumen_rows.append({
                    "Establecimiento": e["nombre"],
                    "Nivel": e["nivel"].capitalize(),
                    "% TD 2026": e["pct_2026"],
                    "% TD 2025": e["pct_2025"],
                    "Brecha (pp)": e["brecha"],
                    "Variación (pp)": e["variacion"],
                    "Reporte enviado": "✅ Sí" if (r and r.get("estado")=="enviado") else "⬜ No",
                })
            pd.DataFrame(resumen_rows).to_excel(writer, sheet_name="Resumen SSMOC", index=False)

            ws_a = writer.sheets["Anexo N°1 MINSAL"]
            for col_idx, col in enumerate(df_export.columns, 1):
                ws_a.column_dimensions[__import__("openpyxl").utils.get_column_letter(col_idx)].width = 25

        buffer.seek(0)
        fecha_archivo = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label="⬇️ Descargar Excel (.xlsx)",
            data=buffer,
            file_name=f"SSMOC_AnexoN1_MINSAL_{periodo_sel}_{fecha_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

    with col2:
        # CSV
        csv_data = df_export.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="⬇️ Descargar CSV",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"SSMOC_AnexoN1_MINSAL_{periodo_sel}_{fecha_archivo}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Información adicional ─────────────────────────────────────────
    with st.expander("ℹ️ Instrucciones de envío al MINSAL"):
        st.markdown(f"""
        ### Proceso de envío — {periodo_info['label']}

        **Fecha límite:** {periodo_info['fecha_limite']}

        **Instrucciones según Lineamiento MINSAL v1.0:**
        1. Descargue el archivo Excel generado por esta plataforma.
        2. Verifique que todos los establecimientos en nivel **Rojo** y **Amarillo** estén incluidos.
        3. El archivo debe ser remitido de manera **consolidada por el Servicio de Salud** — 
           no por establecimiento individual.
        4. Remitir a la **Subsecretaría de Redes Asistenciales**, Área de Compras Estratégicas 
           y Procesos Logísticos.
        5. Los establecimientos en nivel **Verde no requieren** remitir antecedentes.

        **Responsable de envío:** Juan Luis Pérez Pineda — Subdirector RFF, SSMOC  
        **Coordinación:** Bayron Retamal González — Encargado de Concesiones, SSMOC
        """)

    # ── Pendientes ────────────────────────────────────────────────────
    pendientes = [
        eid for eid, e in ESTABLECIMIENTOS.items()
        if e["nivel"] in ["rojo","amarillo"]
        and not any(r.get("establecimiento_id")==eid and r.get("estado")=="enviado"
                    for r in reports if r.get("reporte_id")==periodo_sel)
    ]
    if pendientes:
        st.warning(f"⚠️ **{len(pendientes)} establecimiento(s) aún no han enviado su reporte** para {periodo_info['label']}:")
        for eid in pendientes:
            e = ESTABLECIMIENTOS[eid]
            st.markdown(f"- **{e['nombre']}** — Nivel {e['nivel'].capitalize()} ({e['pct_2026']:.1f}%)")
