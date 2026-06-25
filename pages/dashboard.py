"""pages/dashboard.py — Panel principal de monitoreo"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from auth import (require_login, ESTABLECIMIENTOS, PERIODOS_REPORTE,
                  load_reports, COLORES_NIVEL)


def show():
    user = require_login()

    st.markdown("""
    <div style="background:#1F3864;color:white;padding:18px 22px;border-radius:10px;margin-bottom:20px">
        <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;opacity:.6;margin-bottom:4px">
            Subsecretaría de Redes Asistenciales · División de Presupuesto
        </div>
        <div style="font-size:20px;font-weight:600">Monitoreo Compras Trato Directo — Red SSMOC 2026</div>
        <div style="font-size:12px;opacity:.65;margin-top:4px">
            Lineamiento v1.0 · Junio 2026 · Fuente: ChileCompra (órdenes aceptadas con recepción conforme, monto neto CLP)
        </div>
    </div>
    """, unsafe_allow_html=True)

    reports = load_reports()

    # ── KPIs globales SSMOC ───────────────────────────────────────────
    total_num = sum(e["numerador"] for e in ESTABLECIMIENTOS.values())
    total_den = sum(e["denominador"] for e in ESTABLECIMIENTOS.values())
    pct_ssmoc = round(total_num / total_den * 100, 2)

    rojos    = [e for e in ESTABLECIMIENTOS.values() if e["nivel"] == "rojo"]
    amarillos= [e for e in ESTABLECIMIENTOS.values() if e["nivel"] == "amarillo"]
    verdes   = [e for e in ESTABLECIMIENTOS.values() if e["nivel"] == "verde"]

    r1_total = len(rojos) + len(amarillos)
    r1_done  = len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Numerador SSMOC (CLP)", f"${total_num/1e12:.1f} MMM",
                  help="Monto compras TD con recepción conforme")
    with col2:
        st.metric("Denominador SSMOC (CLP)", f"${total_den/1e12:.1f} MMM",
                  help="Total todas las modalidades")
    with col3:
        delta_str = f"+{pct_ssmoc - 16:.1f} pp vs. meta"
        st.metric("% TD SSMOC 2026", f"{pct_ssmoc:.1f}%", delta=delta_str,
                  delta_color="inverse")
    with col4:
        st.metric("1° Reporte (31 Jul)", f"{r1_done}/{r1_total} enviados",
                  help="Establecimientos en rojo/amarillo que deben reportar")

    st.markdown("---")

    # ── Semáforo de establecimientos ─────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Estado por establecimiento — Período enero–junio 2026")

        df = pd.DataFrame([
            {
                "Establecimiento": e["nombre_corto"],
                "% TD 2026": e["pct_2026"],
                "% TD 2025": e["pct_2025"],
                "Brecha": e["brecha"],
                "Var. 2025": e["variacion"],
                "Nivel": e["nivel"].capitalize(),
                "eid": eid,
            }
            for eid, e in ESTABLECIMIENTOS.items()
        ]).sort_values("% TD 2026", ascending=False)

        color_map = {"Rojo": "#E24B4A", "Amarillo": "#BA7517", "Verde": "#3B6D11"}

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="% TD 2025",
            y=df["Establecimiento"],
            x=df["% TD 2025"],
            orientation="h",
            marker_color="#85B7EB",
            opacity=0.7,
        ))
        fig.add_trace(go.Bar(
            name="% TD 2026",
            y=df["Establecimiento"],
            x=df["% TD 2026"],
            orientation="h",
            marker_color=[color_map[n] for n in df["Nivel"]],
        ))
        fig.add_vline(x=16, line_dash="dash", line_color="#1F3864",
                      annotation_text="Meta 16%", annotation_position="top right")
        fig.update_layout(
            barmode="overlay",
            height=340,
            margin=dict(l=0, r=10, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            xaxis_title="% Trato Directo",
            yaxis_title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=11),
        )
        fig.update_xaxes(range=[0, 70], gridcolor="#f0f0f0")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Distribución de riesgo")

        # Donut chart
        fig2 = go.Figure(data=[go.Pie(
            labels=["Verde", "Amarillo", "Rojo"],
            values=[len(verdes), len(amarillos), len(rojos)],
            hole=0.55,
            marker_colors=["#3B6D11", "#BA7517", "#E24B4A"],
        )])
        fig2.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            paper_bgcolor="white",
        )
        fig2.add_annotation(text=f"<b>{len(ESTABLECIMIENTOS)}</b><br>establ.",
                            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#1F3864"))
        st.plotly_chart(fig2, use_container_width=True)

        # Counters
        for nivel, estabs, bg, tc in [
            ("Rojo — acción inmediata",   rojos,    "#FCEBEB", "#A32D2D"),
            ("Amarillo — monitorear",     amarillos,"#FAEEDA", "#633806"),
            ("Verde — mantener",          verdes,   "#EAF3DE", "#27500A"),
        ]:
            names = " · ".join(e["nombre_corto"] for e in estabs)
            st.markdown(f"""
            <div style="background:{bg};border-radius:6px;padding:8px 12px;margin-bottom:6px">
                <div style="font-size:12px;font-weight:600;color:{tc}">{nivel}</div>
                <div style="font-size:11px;color:{tc};opacity:.85;margin-top:2px">{names}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabla de estado reportes ──────────────────────────────────────
    st.subheader("Estado de reportes por período")

    periodos_ids = [p["id"] for p in PERIODOS_REPORTE]
    estabs_req = {eid: e for eid, e in ESTABLECIMIENTOS.items()
                  if e["nivel"] in ["rojo", "amarillo"]}

    rows = []
    for eid, e in estabs_req.items():
        row = {"Establecimiento": e["nombre_corto"], "Nivel": e["nivel"].capitalize()}
        for p in PERIODOS_REPORTE:
            r = next((x for x in reports
                      if x.get("establecimiento_id")==eid and x.get("reporte_id")==p["id"]), None)
            if r:
                estado = r.get("estado", "borrador")
                icon = "✅" if estado == "enviado" else "📝"
                row[p["label"]] = f"{icon} {estado.capitalize()}"
            else:
                row[p["label"]] = "⬜ Pendiente"
        rows.append(row)

    df_status = pd.DataFrame(rows)
    st.dataframe(df_status, use_container_width=True, hide_index=True)

    # ── Alerta crítica ────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#FCEBEB;border:1px solid #fca5a5;border-radius:8px;padding:14px 18px;margin-top:8px">
        <div style="font-size:13px;font-weight:700;color:#A32D2D;margin-bottom:8px">
            ⚠️  Establecimientos en nivel rojo — requieren plan de acción urgente
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
    """, unsafe_allow_html=True)

    for e in rojos:
        va_str = f"+{e['variacion']:.1f}" if e['variacion'] > 0 else f"{e['variacion']:.1f}"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.6);border-radius:6px;padding:10px 12px">
            <div style="font-size:12px;font-weight:700;color:#A32D2D">{e["nombre_corto"]}</div>
            <div style="font-size:20px;font-weight:800;color:#A32D2D;margin:2px 0">{e["pct_2026"]:.1f}%</div>
            <div style="font-size:11px;color:#791F1F">Brecha: +{e["brecha"]:.1f} pp · Var.: {va_str} pp vs 2025</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Contexto nacional ─────────────────────────────────────────────
    with st.expander("📊 Contexto nacional — 224 establecimientos MINSAL"):
        nc1, nc2, nc3, nc4 = st.columns(4)
        nc1.metric("Numerador nacional", "$238,1 MMM")
        nc2.metric("Denominador nacional", "$1.434,9 MMM")
        nc3.metric("% TD nacional 2026", "16,6%")
        nc4.metric("Variación vs 2025", "−4,3 pp")

        st.markdown("""
        | Nivel | N° establecimientos | % del total |
        |-------|--------------------:|------------:|
        | 🟢 Verde   | 95 | 42,4% |
        | 🟡 Amarillo| 46 | 20,5% |
        | 🔴 Rojo    | 83 | 37,1% |
        | **Total**  | **224** | **100%** |

        **SSMOC en el contexto nacional:** El Instituto Traumatológico (62,2%) ocupa el **puesto 5° nacional** entre
        los establecimientos con mayor % TD. La Dirección del Servicio (37,2%) registró el **mayor incremento
        respecto a 2025** en toda la red SSMOC (+31,9 pp).
        """)
