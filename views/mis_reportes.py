"""pages/mis_reportes.py — Ingreso de reportes por establecimiento"""
import streamlit as st
import datetime
from auth import (require_login, ESTABLECIMIENTOS, PERIODOS_REPORTE,
                  CAUSALES_TD, get_report, upsert_report, load_reports)


def show(header_fn=None):
    user = require_login()

    # Determinar qué establecimiento puede ver
    if user["rol"] == "admin":
        # Admin puede ver/editar cualquiera
        opciones = {eid: e["nombre_corto"] for eid, e in ESTABLECIMIENTOS.items()
                    if e["nivel"] in ["rojo", "amarillo"]}
        if not opciones:
            st.info("No hay establecimientos en nivel rojo o amarillo.")
            return
        eid_sel = st.selectbox(
            "Seleccionar establecimiento",
            options=list(opciones.keys()),
            format_func=lambda x: opciones[x],
        )
    else:
        eid_sel = user.get("establecimiento")
        if not eid_sel:
            st.error("Tu usuario no tiene un establecimiento asignado.")
            return
        estab_info = ESTABLECIMIENTOS.get(eid_sel, {})
        if estab_info.get("nivel") == "verde":
            st.success(f"""
            ✅ **{estab_info.get('nombre')}** está clasificado en nivel **Verde** (TD: {estab_info.get('pct_2026',0):.1f}%).
            
            No se requiere remitir antecedentes a la Subsecretaría para establecimientos en nivel verde.
            El SSMOC mantendrá el seguimiento interno.
            """)
            return

    estab = ESTABLECIMIENTOS.get(eid_sel, {})

    # ── Cabecera del establecimiento ──────────────────────────────────
    nivel = estab.get("nivel", "verde")
    nivel_colors = {"rojo": ("#FCEBEB","#A32D2D"), "amarillo": ("#FAEEDA","#633806"), "verde": ("#EAF3DE","#27500A")}
    nb, nt = nivel_colors.get(nivel, ("#eee","#333"))

    st.markdown(f"""
    <div style="background:#1F3864;color:white;padding:14px 20px;border-radius:10px 10px 0 0;margin-bottom:0">
        <div style="font-size:11px;opacity:.55;margin-bottom:3px">Ingreso de antecedentes — Anexo N°1 Lineamiento MINSAL v1.0</div>
        <div style="font-size:18px;font-weight:600">{estab.get('nombre','')}</div>
        <div style="font-size:12px;opacity:.65;margin-top:2px">RUT: {estab.get('rut','')} · Código DEIS: {estab.get('codigo_deis','')}</div>
    </div>
    <div style="background:{nb};color:{nt};padding:10px 20px;border-radius:0 0 6px 6px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
        <span style="font-size:13px;font-weight:600">Nivel de riesgo: {nivel.capitalize()}</span>
        <span style="font-size:12px">
            % TD 2026: <strong>{estab.get('pct_2026',0):.2f}%</strong> &nbsp;|&nbsp;
            % TD 2025: {estab.get('pct_2025',0):.2f}% &nbsp;|&nbsp;
            Brecha vs meta: {'+' if estab.get('brecha',0)>0 else ''}{estab.get('brecha',0):.2f} pp
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Selección de período ──────────────────────────────────────────
    periodo_labels = {p["id"]: f"{p['label']} — {p['periodo']} (plazo: {p['fecha_limite']})"
                      for p in PERIODOS_REPORTE}
    reporte_id = st.selectbox(
        "Período a informar",
        options=[p["id"] for p in PERIODOS_REPORTE],
        format_func=lambda x: periodo_labels[x],
    )
    periodo_info = next(p for p in PERIODOS_REPORTE if p["id"] == reporte_id)

    # Cargar reporte existente si lo hay
    existing = get_report(eid_sel, reporte_id)
    if existing:
        st.info(f"ℹ️ Ya existe un reporte {periodo_info['label']} en estado **{existing.get('estado','borrador').upper()}**. Puedes editarlo.")

    # ── Formulario ────────────────────────────────────────────────────
    with st.form(f"form_{eid_sel}_{reporte_id}", clear_on_submit=False):
        st.markdown(f"### {periodo_info['label']} · {periodo_info['periodo']}")

        # 1. CAUSAS PRINCIPALES
        st.markdown("#### 1. Principales causas que explican el resultado observado")
        st.caption("Seleccione todas las causales aplicables y describa el contexto específico de su establecimiento.")

        causas_sel = st.multiselect(
            "Causales de Trato Directo identificadas",
            options=CAUSALES_TD,
            default=existing.get("causas_sel", []) if existing else [],
        )
        causas_descripcion = st.text_area(
            "Descripción detallada de las causas (mínimo 3 líneas)",
            value=existing.get("causas_descripcion", "") if existing else "",
            height=120,
            placeholder=(
                "Ejemplo: Durante el período enero–marzo 2026, el establecimiento debió recurrir "
                "a Trato Directo principalmente debido a...\n"
                "- Quiebres de stock de [insumo] ante indisponibilidad de CENABAST...\n"
                "- Equipamiento especializado [nombre] cuya mantención es exclusiva del fabricante..."
            ),
        )

        # Resumen cuantitativo
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            monto_td = st.number_input(
                "Monto TD período ($ CLP)",
                min_value=0, step=1_000_000,
                value=int(existing.get("monto_td", 0)) if existing else 0,
                format="%d",
            )
        with col_b:
            n_procesos_td = st.number_input(
                "N° procesos TD en el período",
                min_value=0, step=1,
                value=int(existing.get("n_procesos_td", 0)) if existing else 0,
            )
        with col_b:
            pass
        with col_c:
            pct_td_periodo = st.number_input(
                "% TD período (según datos MINSAL)",
                min_value=0.0, max_value=100.0, step=0.01,
                value=float(existing.get("pct_td_periodo", estab.get("pct_2026", 0.0))) if existing else float(estab.get("pct_2026", 0.0)),
                format="%.2f",
            )

        st.divider()

        # 2. MEDIDAS IMPLEMENTADAS
        st.markdown("#### 2. Medidas implementadas")
        st.caption("Acciones ya ejecutadas durante o después del período para reducir el uso del Trato Directo.")

        medidas_checks = {
            "plan_anual": "Actualización del Plan Anual de Compras (PAC)",
            "licitaciones": "Inicio de procesos licitatorios para compras recurrentes",
            "convenio_marco": "Migración de compras a Convenio Marco de ChileCompra",
            "cenabast": "Gestión de abastecimiento a través de CENABAST",
            "capacitacion": "Capacitación del equipo de abastecimiento (Ley 21.634)",
            "control_vencimientos": "Implementación de sistema de control de vencimientos de contratos",
        }

        existing_medidas = existing.get("medidas_checks", {}) if existing else {}
        medidas_sel = {}
        cols_m = st.columns(2)
        for i, (key, label) in enumerate(medidas_checks.items()):
            with cols_m[i % 2]:
                medidas_sel[key] = st.checkbox(
                    label, value=existing_medidas.get(key, False), key=f"med_{key}"
                )

        medidas_descripcion = st.text_area(
            "Descripción de medidas implementadas y resultados observados",
            value=existing.get("medidas_descripcion", "") if existing else "",
            height=100,
            placeholder="Describa las acciones concretas ejecutadas, los plazos y el impacto estimado...",
        )

        st.divider()

        # 3. COMPROMISOS
        st.markdown("#### 3. Compromisos y plan de acción para el próximo período")

        compromisos_text = st.text_area(
            "Compromisos adoptados",
            value=existing.get("compromisos", "") if existing else "",
            height=120,
            placeholder=(
                "1. Iniciar licitación pública para [insumo/servicio] antes del [fecha]...\n"
                "2. Gestionar disponibilidad en CENABAST de [medicamento] para el próximo trimestre...\n"
                "3. Reducir % TD a menos de 16% para el 2° período..."
            ),
        )

        col_d, col_e = st.columns(2)
        with col_d:
            meta_proxima = st.number_input(
                "Meta % TD para próximo período",
                min_value=0.0, max_value=100.0, step=0.5,
                value=float(existing.get("meta_proxima", 16.0)) if existing else 16.0,
                format="%.1f",
            )
        with col_e:
            fecha_compromiso = st.date_input(
                "Fecha comprometida de cumplimiento",
                value=datetime.date.fromisoformat(existing["fecha_compromiso"]) if existing and existing.get("fecha_compromiso") else datetime.date(2026, 8, 31),
            )

        st.divider()

        # 4. RESPONSABLE
        st.markdown("#### 4. Responsable")
        col_f, col_g, col_h = st.columns(3)
        with col_f:
            responsable_nombre = st.text_input(
                "Nombre del responsable",
                value=existing.get("responsable_nombre", user["nombre"]) if existing else user["nombre"],
            )
        with col_g:
            responsable_cargo = st.text_input(
                "Cargo",
                value=existing.get("responsable_cargo", "Jefe/a de Abastecimiento") if existing else "Jefe/a de Abastecimiento",
            )
        with col_h:
            responsable_email = st.text_input(
                "Correo electrónico",
                value=existing.get("responsable_email", user.get("email","")) if existing else user.get("email",""),
            )

        observaciones = st.text_area(
            "Observaciones adicionales (opcional)",
            value=existing.get("observaciones", "") if existing else "",
            height=80,
        )

        st.divider()

        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            guardar = st.form_submit_button("💾 Guardar borrador", use_container_width=True)
        with col_btn2:
            enviar = st.form_submit_button("📤 Enviar a SSMOC", use_container_width=True, type="primary")

        # Procesamiento
        if guardar or enviar:
            # Validaciones básicas para envío
            if enviar:
                errores = []
                if not causas_descripcion.strip():
                    errores.append("Debe completar la descripción de causas.")
                if not causas_sel:
                    errores.append("Debe seleccionar al menos una causal.")
                if not compromisos_text.strip():
                    errores.append("Debe completar los compromisos.")
                if not responsable_nombre.strip():
                    errores.append("Debe indicar el nombre del responsable.")
                if errores:
                    for e in errores:
                        st.error(e)
                    st.stop()

            estado = "enviado" if enviar else "borrador"
            data = {
                "establecimiento_id":   eid_sel,
                "establecimiento_nombre": estab["nombre"],
                "reporte_id":            reporte_id,
                "periodo_label":         periodo_info["label"],
                "periodo":               periodo_info["periodo"],
                "nivel_riesgo":          nivel,
                "pct_td_2026":           estab.get("pct_2026"),
                "pct_td_2025":           estab.get("pct_2025"),
                "pct_td_periodo":        pct_td_periodo,
                "monto_td":              monto_td,
                "n_procesos_td":         n_procesos_td,
                "causas_sel":            causas_sel,
                "causas_descripcion":    causas_descripcion,
                "medidas_checks":        medidas_sel,
                "medidas_descripcion":   medidas_descripcion,
                "compromisos":           compromisos_text,
                "meta_proxima":          meta_proxima,
                "fecha_compromiso":      str(fecha_compromiso),
                "responsable_nombre":    responsable_nombre,
                "responsable_cargo":     responsable_cargo,
                "responsable_email":     responsable_email,
                "observaciones":         observaciones,
                "estado":                estado,
                "usuario_ingreso":       user["username"],
                "fecha_ingreso":         str(datetime.datetime.now().isoformat()),
            }
            upsert_report(data)

            if enviar:
                st.success(f"✅ Reporte **{periodo_info['label']}** enviado exitosamente a la Subdirección RFF-SSMOC.")
                st.balloons()
            else:
                st.info("💾 Borrador guardado. Puede continuar editando antes de enviar.")
            st.rerun()
