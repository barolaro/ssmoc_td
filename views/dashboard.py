"""views/dashboard.py"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from auth import require_login, ESTABLECIMIENTOS, PERIODOS_REPORTE, load_reports

def show(header_fn=None, logo_b64=None):
    require_login()

    if header_fn:
        header_fn(
            "Monitoreo Trato Directo — Red SSMOC 2026",
            "Lineamiento MINSAL v1.0 · Junio 2026 · Fuente: ChileCompra — monto neto CLP, OC aceptadas con recepción conforme"
        )

    reports = load_reports()

    # ── KPIs ──────────────────────────────────────────────────────────
    total_num = sum(e["numerador"] for e in ESTABLECIMIENTOS.values())
    total_den = sum(e["denominador"] for e in ESTABLECIMIENTOS.values())
    pct_ssmoc = round(total_num / total_den * 100, 2)
    rojos     = [e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="rojo"]
    amarillos = [e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="amarillo"]
    verdes    = [e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="verde"]
    r1_req    = len(rojos)+len(amarillos)
    r1_done   = len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])

    c1,c2,c3,c4 = st.columns(4)
    def kpi(col, label, value, note, color="#1F3864"):
        col.markdown(f"""
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;
                    padding:16px 18px;border-top:3px solid {color}">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                        letter-spacing:.06em;margin-bottom:6px">{label}</div>
            <div style="font-size:24px;font-weight:700;color:{color};line-height:1">{value}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">{note}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(c1,"Numerador SSMOC", f"${total_num/1e12:.1f} MMM", "Compras TD recepción conforme","#0C447C")
    kpi(c2,"Denominador SSMOC", f"${total_den/1e12:.1f} MMM", "Todas las modalidades","#0C447C")
    kpi(c3,"% TD SSMOC 2026", f"{pct_ssmoc:.1f}%", f"Meta ≤ 16% · Brecha +{pct_ssmoc-16:.1f} pp","#A32D2D")
    kpi(c4,"1° Reporte (31 Jul)", f"{r1_done}/{r1_req}", "Establecimientos enviados","#0F6E56")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráfico principal + semáforo ──────────────────────────────────
    col_g, col_s = st.columns([3, 1.4])

    with col_g:
        st.markdown("""
        <div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:10px">
            % Trato Directo por establecimiento — comparación 2025 vs 2026
        </div>
        """, unsafe_allow_html=True)

        df = pd.DataFrame([
            {"Establecimiento": e["nombre_corto"], "2025": e["pct_2025"],
             "2026": e["pct_2026"], "nivel": e["nivel"]}
            for e in ESTABLECIMIENTOS.values()
        ]).sort_values("2026", ascending=True)

        color_map = {"rojo":"#E24B4A","amarillo":"#F59E0B","verde":"#22C55E"}

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="% TD 2025", y=df["Establecimiento"], x=df["2025"],
            orientation="h", marker_color="#CBD5E1", opacity=0.7,
        ))
        fig.add_trace(go.Bar(
            name="% TD 2026", y=df["Establecimiento"], x=df["2026"],
            orientation="h",
            marker_color=[color_map[n] for n in df["nivel"]],
        ))
        fig.add_vline(x=16, line_dash="dash", line_color="#1F3864", line_width=1.5,
                      annotation_text="Meta 16%", annotation_font_color="#1F3864",
                      annotation_position="top right")
        fig.update_layout(
            barmode="overlay", height=310,
            margin=dict(l=0,r=20,t=10,b=30),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0,font=dict(size=11)),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(range=[0,70],gridcolor="#f1f5f9",title="% Trato Directo"),
            yaxis=dict(gridcolor="#f1f5f9"),
            font=dict(size=11, family="Arial"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Leyenda
        st.markdown("""
        <div style="display:flex;gap:16px;font-size:11px;color:#64748b;margin-top:-8px">
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#E24B4A;margin-right:4px"></span>Rojo &gt;18%</span>
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#F59E0B;margin-right:4px"></span>Amarillo 16–18%</span>
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#22C55E;margin-right:4px"></span>Verde ≤16%</span>
            <span><span style="display:inline-block;width:1.5px;height:13px;background:#1F3864;margin-right:4px;vertical-align:middle"></span>Meta 16%</span>
        </div>
        """, unsafe_allow_html=True)

    with col_s:
        st.markdown("""
        <div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:10px">
            Semáforo de riesgo
        </div>
        """, unsafe_allow_html=True)

        for nivel, estabs, bg, tc, bc in [
            ("🔴 Rojo", rojos, "#FEF2F2","#991B1B","#FECACA"),
            ("🟡 Amarillo", amarillos,"#FFFBEB","#92400E","#FDE68A"),
            ("🟢 Verde", verdes, "#F0FDF4","#166534","#BBF7D0"),
        ]:
            names = "<br>".join(f"• {e['nombre_corto']}" for e in estabs)
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-radius:8px;
                        padding:10px 12px;margin-bottom:8px">
                <div style="font-size:12px;font-weight:700;color:{tc}">{nivel} ({len(estabs)})</div>
                <div style="font-size:11px;color:{tc};opacity:.85;margin-top:4px;line-height:1.6">{names}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#f1f5f9'>", unsafe_allow_html=True)

    # ── Alertas críticas ──────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:10px">
        Establecimientos en nivel rojo — requieren plan de acción urgente
    </div>
    """, unsafe_allow_html=True)

    cols_r = st.columns(len(rojos))
    for i, e in enumerate(sorted(rojos, key=lambda x: -x["pct_2026"])):
        va = f"+{e['variacion']:.1f}" if e["variacion"]>0 else f"{e['variacion']:.1f}"
        with cols_r[i]:
            st.markdown(f"""
            <div style="background:white;border:1px solid #FECACA;border-top:4px solid #E24B4A;
                        border-radius:8px;padding:14px">
                <div style="font-size:11px;font-weight:600;color:#991B1B;margin-bottom:6px">{e['nombre_corto']}</div>
                <div style="font-size:28px;font-weight:800;color:#A32D2D;line-height:1">{e['pct_2026']:.1f}%</div>
                <div style="font-size:11px;color:#DC2626;margin-top:4px">Meta: 16% · Brecha: +{e['brecha']:.1f} pp</div>
                <div style="font-size:11px;color:#DC2626">Var. vs 2025: {va} pp</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Estado reportes ───────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:10px">
        Estado de reportes por período
    </div>
    """, unsafe_allow_html=True)

    rows = []
    for eid, e in ESTABLECIMIENTOS.items():
        if e["nivel"] == "verde": continue
        row = {"Establecimiento": e["nombre_corto"],
               "Nivel": f"{'🔴' if e['nivel']=='rojo' else '🟡'} {e['nivel'].capitalize()}",
               "% TD": f"{e['pct_2026']:.1f}%"}
        for p in PERIODOS_REPORTE:
            r = next((x for x in reports if x.get("establecimiento_id")==eid
                      and x.get("reporte_id")==p["id"]), None)
            row[p["label"]] = ("✅ Enviado" if r and r.get("estado")=="enviado"
                               else "📝 Borrador" if r else "⬜ Pendiente")
        rows.append(row)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={"Establecimiento": st.column_config.TextColumn(width="large")})

    # ── Contexto nacional ─────────────────────────────────────────────
    with st.expander("📊 Contexto nacional — 224 establecimientos MINSAL"):
        nc1,nc2,nc3,nc4 = st.columns(4)
        nc1.metric("Numerador nacional","$238,1 MMM")
        nc2.metric("Denominador nacional","$1.434,9 MMM")
        nc3.metric("% TD nacional 2026","16,6%")
        nc4.metric("Variación vs 2025","−4,3 pp")
        st.markdown("""
        | Nivel | Establecimientos | % total |
        |-------|----------------:|--------:|
        | 🟢 Verde | 95 | 42,4% |
        | 🟡 Amarillo | 46 | 20,5% |
        | 🔴 Rojo | 83 | 37,1% |
        | **Total** | **224** | **100%** |

        El Instituto Traumatológico SSMOC (62,2%) ocupa el **puesto 5° nacional** entre los establecimientos con mayor % TD.
        """)
