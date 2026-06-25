"""
app.py — Monitor Trato Directo SSMOC · Todo en un archivo
"""
import streamlit as st
import hashlib, json, datetime, io, base64
from pathlib import Path

st.set_page_config(
    page_title="Monitor TD — SSMOC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── OCULTAR navegación automática de Streamlit ────────────────────────
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebarNavItems"] {display:none !important;}
[data-testid="stSidebarNav"] {display:none !important;}
section[data-testid="stSidebarNav"] {display:none !important;}
.block-container {padding-top:0.5rem !important;}
[data-testid="stSidebar"] {background:#0A3964 !important;}
[data-testid="stSidebar"] > div {background:#0A3964 !important;}
[data-testid="stSidebar"] * {color:rgba(255,255,255,0.85) !important;}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,0.12) !important;}
[data-testid="stSidebar"] .stButton > button {
    background:rgba(255,255,255,0.07) !important;
    color:white !important;
    border:1px solid rgba(255,255,255,0.15) !important;
    border-radius:6px !important;
    text-align:left !important;
    padding:8px 12px !important;
    margin-bottom:2px !important;
    font-size:13px !important;
    width:100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(255,255,255,0.15) !important;
    border-color:rgba(255,255,255,0.3) !important;
}
.nav-active button {
    background:rgba(255,255,255,0.18) !important;
    border-left:3px solid #C0392B !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# DATOS Y AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════════════
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE   = DATA_DIR / "users.json"
REPORTS_FILE = DATA_DIR / "reports.json"

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

ESTABLECIMIENTOS = {
    "traumatologico": {"nombre":"Instituto Traumatológico Dr. Teodoro Gebauer","nombre_corto":"Inst. Traumatológico","rut":"61.608.402-k","codigo_deis":"110110","pct_2026":62.17,"pct_2025":37.78,"brecha":46.17,"variacion":24.39,"nivel":"rojo","denominador":5868063000,"numerador":3648431000},
    "direccion":      {"nombre":"Dirección del Servicio Metropolitano Occidente","nombre_corto":"Dir. SSMOC","rut":"61.608.200-0","codigo_deis":"110010","pct_2026":37.16,"pct_2025":5.30,"brecha":21.16,"variacion":31.86,"nivel":"rojo","denominador":5835193000,"numerador":2168191000},
    "felix_bulnes":   {"nombre":"Hospital Dr. Félix Bulnes Cerda","nombre_corto":"H. Félix Bulnes","rut":"61.608.205-1","codigo_deis":"110120","pct_2026":26.44,"pct_2025":21.59,"brecha":10.44,"variacion":4.85,"nivel":"rojo","denominador":19487600000,"numerador":5152787000},
    "san_juan":       {"nombre":"Hospital San Juan de Dios","nombre_corto":"H. San Juan de Dios","rut":"61.608.204-3","codigo_deis":"110100","pct_2026":11.61,"pct_2025":10.70,"brecha":-4.39,"variacion":0.91,"nivel":"amarillo","denominador":39066760000,"numerador":4535665000},
    "crs_allende":    {"nombre":"Centro de Referencia Salud Occidente Salvador Allende","nombre_corto":"CRS Salvador Allende","rut":"61.933.400-0","codigo_deis":"110300","pct_2026":7.07,"pct_2025":4.76,"brecha":-8.93,"variacion":2.31,"nivel":"amarillo","denominador":1954204000,"numerador":138205000},
    "melipilla":      {"nombre":"Hospital San José (Melipilla)","nombre_corto":"H. Melipilla","rut":"61.602.122-2","codigo_deis":"110150","pct_2026":6.60,"pct_2025":8.29,"brecha":-9.40,"variacion":-1.69,"nivel":"verde","denominador":6908127000,"numerador":455863000},
    "penaflor":       {"nombre":"Hospital de Peñaflor","nombre_corto":"H. Peñaflor","rut":"61.602.123-0","codigo_deis":"110140","pct_2026":6.89,"pct_2025":17.58,"brecha":-9.11,"variacion":-10.69,"nivel":"verde","denominador":1677287000,"numerador":115598000},
    "curacavi":       {"nombre":"Hospital de Curacaví","nombre_corto":"H. Curacaví","rut":"61.602.125-7","codigo_deis":"110160","pct_2026":5.62,"pct_2025":14.42,"brecha":-10.38,"variacion":-8.80,"nivel":"verde","denominador":1001068000,"numerador":56257000},
    "talagante":      {"nombre":"Hospital Adalberto Steeger (Talagante)","nombre_corto":"H. Talagante","rut":"61.602.121-4","codigo_deis":"110130","pct_2026":3.21,"pct_2025":10.63,"brecha":-12.79,"variacion":-7.42,"nivel":"verde","denominador":7242042000,"numerador":232417000},
}

PERIODOS = [
    {"id":"R1","label":"1° Reporte","periodo":"Enero–Marzo 2026",      "fecha_limite":"31 Jul 2026"},
    {"id":"R2","label":"2° Reporte","periodo":"Abril–Junio 2026",      "fecha_limite":"31 Ago 2026"},
    {"id":"R3","label":"3° Reporte","periodo":"Jul–Sep 2026",          "fecha_limite":"30 Nov 2026"},
    {"id":"R4","label":"4° Reporte","periodo":"Oct–Dic 2026",          "fecha_limite":"28 Feb 2027"},
]

CAUSALES = [
    "Proveedor único / exclusividad",
    "Emergencia o urgencia debidamente calificada",
    "Licitación desierta (2° vez)",
    "Confidencialidad / seguridad nacional",
    "Continuidad de servicios en ejecución",
    "Derechos de propiedad intelectual (software/licencias)",
    "Equipamiento especializado sin equivalente",
    "Convenio con otro organismo público (CENABAST, etc.)",
    "Compra ágil (< 30 UTM)",
    "Otra causal — especificar en observaciones",
]

def _default_users():
    raw = {
        "admin":         ("Administrador SSMOC",              "admin",          "abastecimiento@ssmocc.cl",          None,             "Admin2026*"),
        "bayron":        ("Bayron Retamal González",           "admin",          "bayron.retamal@ssmocc.cl",          None,             "Ssmoc2026*"),
        "traumatologico":("Miguel Jara",                      "establecimiento","miguel.jara@intraumatologico.cl",   "traumatologico", "Trauma2026*"),
        "direccion":     ("Referente Dir. SSMOC",             "establecimiento","abast.direccion@ssmocc.cl",         "direccion",      "Dir2026*"),
        "felix_bulnes":  ("Carolina Castro",                  "establecimiento","carolina.castroj@redsalud.gob.cl",  "felix_bulnes",   "Felix2026*"),
        "san_juan":      ("Rodrigo Bravo Gajardo",            "establecimiento","rodrigo.bravog@redsalud.gob.cl",    "san_juan",       "Sjd2026*"),
        "crs_allende":   ("Eric Cubillo Antúnez",             "establecimiento","eric.cubillo@redsalud.gob.cl",      "crs_allende",    "Crs2026*"),
        "melipilla":     ("María de los Ángeles Morales",     "establecimiento","maria.moralesj@redsalud.gob.cl",    "melipilla",      "Meli2026*"),
        "penaflor":      ("Gissela Salvo",                    "establecimiento","gissela.salvo@redsalud.gob.cl",     "penaflor",       "Pen2026*"),
        "curacavi":      ("Pablo Yévenes Olivares",           "establecimiento","pablo.yevenes@redsalud.gob.cl",     "curacavi",       "Cura2026*"),
        "talagante":     ("María Andrea Villegas Albarrán",   "establecimiento","mandrea.villegas@redsalud.gob.cl",  "talagante",      "Tala2026*"),
    }
    return {uid:{"nombre":n,"rol":r,"email":e,"establecimiento":est,"password_hash":_hash(p),"activo":True}
            for uid,(n,r,e,est,p) in raw.items()}

def load_users():
    if not USERS_FILE.exists():
        u = _default_users(); save_users(u); return u
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(u): USERS_FILE.write_text(json.dumps(u,ensure_ascii=False,indent=2),encoding="utf-8")

def load_reports():
    if not REPORTS_FILE.exists(): return []
    return json.loads(REPORTS_FILE.read_text(encoding="utf-8"))

def save_reports(r): REPORTS_FILE.write_text(json.dumps(r,ensure_ascii=False,indent=2,default=str),encoding="utf-8")

def upsert_report(data):
    rpts = load_reports()
    for i,r in enumerate(rpts):
        if r["establecimiento_id"]==data["establecimiento_id"] and r["reporte_id"]==data["reporte_id"]:
            rpts[i]=data; save_reports(rpts); return
    rpts.append(data); save_reports(rpts)

def delete_report(eid, rid):
    rpts = [r for r in load_reports()
            if not (r["establecimiento_id"]==eid and r["reporte_id"]==rid)]
    save_reports(rpts)

def authenticate(u,p):
    users=load_users(); usr=users.get(u.strip().lower())
    if usr and usr.get("activo") and usr["password_hash"]==_hash(p):
        return {**usr,"username":u.strip().lower()}
    return None

# ── Logo ──────────────────────────────────────────────────────────────
def get_logo():
    p = Path(__file__).parent/"logo_ssmocc.jpg"
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return None

LOGO = get_logo()

def logo_img(h=44):
    if LOGO:
        return f'<img src="data:image/jpeg;base64,{LOGO}" style="height:{h}px;border-radius:4px">'
    return '<span style="font-size:28px">🏥</span>'

# ── Session state ─────────────────────────────────────────────────────
for k,v in [("user",None),("page","dashboard")]:
    if k not in st.session_state: st.session_state[k]=v

# ═══════════════════════════════════════════════════════════════════════
# COMPONENTES UI
# ═══════════════════════════════════════════════════════════════════════
def page_header(title, sub=""):
    st.markdown(f"""
    <div style="background:#1F3864;padding:14px 22px;border-radius:10px;
                margin-bottom:20px;display:flex;align-items:center;gap:14px">
        {logo_img(42)}
        <div style="width:4px;background:#C0392B;border-radius:2px;align-self:stretch;min-height:36px"></div>
        <div>
            <div style="font-size:17px;font-weight:700;color:white">{title}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.55);margin-top:2px">{sub}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def nivel_pill(nivel):
    cfg={"rojo":("#FEF2F2","#991B1B","#FECACA"),"amarillo":("#FFFBEB","#92400E","#FDE68A"),"verde":("F0FDF4","#166534","#BBF7D0")}
    bg,tc,bc=cfg.get(nivel,("#f5f5f5","#333","#ccc"))
    return f'<span style="background:{bg};color:{tc};border:1px solid {bc};padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700">{nivel.capitalize()}</span>'

def kpi_card(col, label, value, note, color="#1F3864"):
    col.markdown(f"""
    <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;
                padding:16px 18px;border-top:3px solid {color};height:100%">
        <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">{label}</div>
        <div style="font-size:24px;font-weight:700;color:{color};line-height:1">{value}</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:5px">{note}</div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════
def page_login():
    _,col,_ = st.columns([1,1.1,1])
    with col:
        if LOGO:
            st.markdown(f'<div style="text-align:center;margin-bottom:16px"><img src="data:image/jpeg;base64,{LOGO}" style="width:150px;border-radius:8px"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:24px">
            <div style="font-size:21px;font-weight:700;color:#1F3864">Monitor Trato Directo</div>
            <div style="font-size:13px;color:#64748b;margin-top:4px">Servicio de Salud Metropolitano Occidente</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px">Lineamiento MINSAL v1.0 · Junio 2026</div>
        </div>""", unsafe_allow_html=True)
        with st.form("lf"):
            u = st.text_input("Usuario", placeholder="Ingrese su usuario")
            p = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            if st.form_submit_button("Ingresar", use_container_width=True, type="primary"):
                usr = authenticate(u,p)
                if usr:
                    st.session_state.user=usr
                    st.session_state.page="dashboard"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
        st.markdown("""
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;
                    padding:11px 14px;margin-top:14px;font-size:12px;color:#1E40AF">
            Acceso restringido — sistema exclusivo para referentes de abastecimiento SSMOC.
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════
def render_sidebar():
    user=st.session_state.user
    reports=load_reports()
    r1_req=len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
    r1_done=len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])
    pct=int(r1_done/r1_req*100) if r1_req else 0
    color="#4ade80" if r1_done==r1_req else "#fbbf24" if r1_done>0 else "#f87171"

    with st.sidebar:
        if LOGO:
            st.markdown(f'<div style="text-align:center;padding:14px 8px 8px"><img src="data:image/jpeg;base64,{LOGO}" style="width:130px;border-radius:6px"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;padding:16px 0;font-size:36px">🏥</div>', unsafe_allow_html=True)

        estab=ESTABLECIMIENTOS.get(user.get("establecimiento"),{})
        rol_label="🔑 Administrador" if user["rol"]=="admin" else f"🏥 {estab.get('nombre_corto','')}"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);
                    border-radius:8px;padding:10px 12px;margin:8px 0 14px">
            <div style="font-size:10px;color:rgba(255,255,255,.4);margin-bottom:3px">Sesión activa</div>
            <div style="font-size:13px;font-weight:700">{user['nombre']}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.55);margin-top:2px">{rol_label}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:6px;padding-left:2px">Navegación</div>', unsafe_allow_html=True)

        nav=[("📊","Dashboard","dashboard"),("📋","Mis reportes","mis_reportes")]
        if user["rol"]=="admin":
            nav+=[("📁","Todos los reportes","todos_reportes"),
                  ("📤","Exportar MINSAL","exportar"),
                  ("👥","Usuarios","usuarios"),
                  ("⚙️","Configuración","configuracion")]

        for icon,label,pid in nav:
            if st.button(f"{icon}  {label}", key=f"nb_{pid}", use_container_width=True):
                st.session_state.page=pid; st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.06);border-radius:8px;padding:10px 12px;margin-bottom:10px">
            <div style="font-size:10px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px">1° Reporte · Plazo 31 Jul</div>
            <div style="font-size:18px;font-weight:700;color:{color}">{r1_done}/{r1_req} enviados</div>
            <div style="background:rgba(255,255,255,.12);border-radius:4px;height:4px;margin-top:7px">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button("🚪  Cerrar sesión", use_container_width=True):
            st.session_state.user=None; st.session_state.page="dashboard"; st.rerun()

        st.markdown('<div style="text-align:center;padding:6px 0;font-size:10px;color:rgba(255,255,255,.2)">Monitor TD SSMOC v1.0</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# PÁGINAS
# ═══════════════════════════════════════════════════════════════════════
def pg_dashboard():
    import plotly.graph_objects as go
    import pandas as pd

    page_header("Monitoreo Trato Directo — Red SSMOC 2026",
                "Lineamiento MINSAL v1.0 · Junio 2026 · Fuente: ChileCompra — OC aceptadas con recepción conforme, monto neto CLP")

    reports=load_reports()
    total_num=sum(e["numerador"] for e in ESTABLECIMIENTOS.values())
    total_den=sum(e["denominador"] for e in ESTABLECIMIENTOS.values())
    pct_ssmoc=round(total_num/total_den*100,2)
    rojos=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="rojo"]
    amarillos=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="amarillo"]
    verdes=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="verde"]
    r1_req=len(rojos)+len(amarillos)
    r1_done=len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])

    c1,c2,c3,c4=st.columns(4)
    kpi_card(c1,"Numerador SSMOC",f"${total_num/1e12:.1f} MMM","TD con recepción conforme","#0C447C")
    kpi_card(c2,"Denominador SSMOC",f"${total_den/1e12:.1f} MMM","Todas las modalidades","#0C447C")
    kpi_card(c3,"% TD SSMOC 2026",f"{pct_ssmoc:.1f}%",f"Meta ≤ 16% · Brecha +{pct_ssmoc-16:.1f} pp","#A32D2D")
    kpi_card(c4,"1° Reporte (31 Jul)",f"{r1_done}/{r1_req}","Establecimientos enviados","#0F6E56")

    st.markdown("<br>", unsafe_allow_html=True)

    col_g,col_s=st.columns([3,1.4])
    with col_g:
        st.markdown('<div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:8px">% TD por establecimiento — comparación 2025 vs 2026</div>', unsafe_allow_html=True)
        df=pd.DataFrame([{"Establecimiento":e["nombre_corto"],"2025":e["pct_2025"],"2026":e["pct_2026"],"nivel":e["nivel"]} for e in ESTABLECIMIENTOS.values()]).sort_values("2026",ascending=True)
        cmap={"rojo":"#E24B4A","amarillo":"#F59E0B","verde":"#22C55E"}
        fig=go.Figure()
        fig.add_trace(go.Bar(name="% TD 2025",y=df["Establecimiento"],x=df["2025"],orientation="h",marker_color="#CBD5E1",opacity=0.7))
        fig.add_trace(go.Bar(name="% TD 2026",y=df["Establecimiento"],x=df["2026"],orientation="h",marker_color=[cmap[n] for n in df["nivel"]]))
        fig.add_vline(x=16,line_dash="dash",line_color="#1F3864",line_width=1.5,annotation_text="Meta 16%",annotation_font_color="#1F3864",annotation_position="top right")
        fig.update_layout(barmode="overlay",height=310,margin=dict(l=0,r=20,t=10,b=30),legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0,font=dict(size=11)),plot_bgcolor="white",paper_bgcolor="white",xaxis=dict(range=[0,70],gridcolor="#f1f5f9",title="% Trato Directo"),font=dict(size=11,family="Arial"))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('<div style="display:flex;gap:16px;font-size:11px;color:#64748b;margin-top:-8px"><span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#E24B4A;margin-right:4px"></span>Rojo &gt;18%</span><span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#F59E0B;margin-right:4px"></span>Amarillo 16–18%</span><span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#22C55E;margin-right:4px"></span>Verde ≤16%</span><span><span style="display:inline-block;width:1.5px;height:13px;background:#1F3864;margin-right:4px;vertical-align:middle"></span>Meta 16%</span></div>', unsafe_allow_html=True)

    with col_s:
        st.markdown('<div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:8px">Semáforo de riesgo</div>', unsafe_allow_html=True)
        for nv,estabs,bg,tc,bc in [("🔴 Rojo",rojos,"#FEF2F2","#991B1B","#FECACA"),("🟡 Amarillo",amarillos,"#FFFBEB","#92400E","#FDE68A"),("🟢 Verde",verdes,"#F0FDF4","#166534","#BBF7D0")]:
            names="<br>".join(f"• {e['nombre_corto']}" for e in estabs)
            st.markdown(f'<div style="background:{bg};border:1px solid {bc};border-radius:8px;padding:10px 12px;margin-bottom:8px"><div style="font-size:12px;font-weight:700;color:{tc}">{nv} ({len(estabs)})</div><div style="font-size:11px;color:{tc};opacity:.85;margin-top:4px;line-height:1.6">{names}</div></div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#f1f5f9;margin:16px 0'>", unsafe_allow_html=True)

    # Alertas críticas
    st.markdown('<div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:10px">Establecimientos en nivel rojo — requieren plan de acción urgente</div>', unsafe_allow_html=True)
    cols_r=st.columns(len(rojos))
    for i,e in enumerate(sorted(rojos,key=lambda x:-x["pct_2026"])):
        va=f"+{e['variacion']:.1f}" if e["variacion"]>0 else f"{e['variacion']:.1f}"
        with cols_r[i]:
            st.markdown(f'<div style="background:white;border:1px solid #FECACA;border-top:4px solid #E24B4A;border-radius:8px;padding:14px"><div style="font-size:11px;font-weight:600;color:#991B1B;margin-bottom:6px">{e["nombre_corto"]}</div><div style="font-size:28px;font-weight:800;color:#A32D2D;line-height:1">{e["pct_2026"]:.1f}%</div><div style="font-size:11px;color:#DC2626;margin-top:4px">Brecha: +{e["brecha"]:.1f} pp · Var.: {va} pp</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabla estado reportes
    st.markdown('<div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:8px">Estado de reportes por período</div>', unsafe_allow_html=True)
    rows=[]
    for eid,e in ESTABLECIMIENTOS.items():
        if e["nivel"]=="verde": continue
        row={"Establecimiento":e["nombre_corto"],"Nivel":f"{'🔴' if e['nivel']=='rojo' else '🟡'} {e['nivel'].capitalize()}","% TD":f"{e['pct_2026']:.1f}%"}
        for p in PERIODOS:
            r=next((x for x in reports if x.get("establecimiento_id")==eid and x.get("reporte_id")==p["id"]),None)
            row[p["label"]]="✅ Enviado" if r and r.get("estado")=="enviado" else "📝 Borrador" if r else "⬜ Pendiente"
        rows.append(row)
    import pandas as pd
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    with st.expander("📊 Contexto nacional — 224 establecimientos MINSAL"):
        nc1,nc2,nc3,nc4=st.columns(4)
        nc1.metric("Numerador nacional","$238,1 MMM")
        nc2.metric("Denominador nacional","$1.434,9 MMM")
        nc3.metric("% TD nacional 2026","16,6%")
        nc4.metric("Variación vs 2025","−4,3 pp")
        st.markdown("El Instituto Traumatológico SSMOC (62,2%) ocupa el **5° lugar nacional** entre establecimientos con mayor % TD.")


def pg_mis_reportes():
    user=st.session_state.user
    page_header("Mis reportes — Ingreso de antecedentes","Anexo N°1 · Lineamiento MINSAL v1.0 · Junio 2026")

    if user["rol"]=="admin":
        opciones={eid:e["nombre_corto"] for eid,e in ESTABLECIMIENTOS.items() if e["nivel"] in ["rojo","amarillo"]}
        eid_sel=st.selectbox("Establecimiento",options=list(opciones.keys()),format_func=lambda x:opciones[x])
    else:
        eid_sel=user.get("establecimiento")
        if not eid_sel: st.error("Sin establecimiento asignado."); return
        estab_i=ESTABLECIMIENTOS.get(eid_sel,{})
        if estab_i.get("nivel")=="verde":
            st.success(f"✅ **{estab_i.get('nombre')}** está en nivel Verde ({estab_i.get('pct_2026',0):.1f}%). No se requiere remitir antecedentes al MINSAL.")
            return

    estab=ESTABLECIMIENTOS.get(eid_sel,{})
    nivel=estab.get("nivel","verde")
    nbg={"rojo":"#FEF2F2","amarillo":"#FFFBEB","verde":"#F0FDF4"}[nivel]
    ntc={"rojo":"#991B1B","amarillo":"#92400E","verde":"#166534"}[nivel]

    st.markdown(f"""
    <div style="background:#1F3864;color:white;padding:12px 18px;border-radius:10px 10px 0 0">
        <div style="font-size:11px;opacity:.5;margin-bottom:3px">Establecimiento</div>
        <div style="font-size:16px;font-weight:700">{estab.get('nombre','')}</div>
        <div style="font-size:11px;opacity:.6;margin-top:2px">RUT: {estab.get('rut','')} · Código DEIS: {estab.get('codigo_deis','')}</div>
    </div>
    <div style="background:{nbg};color:{ntc};padding:9px 18px;border-radius:0 0 6px 6px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:700">Nivel: {nivel.capitalize()}</span>
        <span>% TD 2026: <strong>{estab.get('pct_2026',0):.2f}%</strong> · 2025: {estab.get('pct_2025',0):.2f}% · Brecha: {'+' if estab.get('brecha',0)>0 else ''}{estab.get('brecha',0):.2f} pp</span>
    </div>""", unsafe_allow_html=True)

    periodo_id=st.selectbox("Período a informar",options=[p["id"] for p in PERIODOS],
                            format_func=lambda x:next(f"{p['label']} — {p['periodo']} (plazo: {p['fecha_limite']})" for p in PERIODOS if p["id"]==x))
    pinfo=next(p for p in PERIODOS if p["id"]==periodo_id)

    existing=next((r for r in load_reports() if r.get("establecimiento_id")==eid_sel and r.get("reporte_id")==periodo_id),None)
    if existing:
        ec={"enviado":"✅","borrador":"📝"}.get(existing.get("estado","borrador"),"📝")
        st.info(f"{ec} Reporte {pinfo['label']} en estado **{existing.get('estado','borrador').upper()}** — puedes editarlo.")

    with st.form(f"frm_{eid_sel}_{periodo_id}"):
        st.markdown(f"#### {pinfo['label']} · {pinfo['periodo']}")

        st.markdown("**1. Principales causas del resultado observado**")
        causas_sel=st.multiselect("Causales de Trato Directo identificadas",CAUSALES,default=existing.get("causas_sel",[]) if existing else [])
        causas_desc=st.text_area("Descripción detallada",value=existing.get("causas_desc","") if existing else "",height=110,placeholder="Describa el contexto específico del establecimiento durante el período...")

        c1,c2,c3=st.columns(3)
        monto_td=c1.number_input("Monto TD período ($CLP)",min_value=0,step=1_000_000,value=int(existing.get("monto_td",0)) if existing else 0,format="%d")
        n_proc=c2.number_input("N° procesos TD",min_value=0,step=1,value=int(existing.get("n_proc",0)) if existing else 0)
        pct_per=c3.number_input("% TD período (MINSAL)",min_value=0.0,max_value=100.0,step=0.01,value=float(existing.get("pct_per",estab.get("pct_2026",0.0))) if existing else float(estab.get("pct_2026",0.0)),format="%.2f")

        st.divider()
        st.markdown("**2. Medidas implementadas**")
        med_opts={"pac":"Actualización Plan Anual de Compras","lic":"Inicio procesos licitatorios","cm":"Migración a Convenio Marco","cenabast":"Gestión CENABAST","cap":"Capacitación equipo (Ley 21.634)","venc":"Control vencimiento contratos"}
        ex_med=existing.get("medidas",{}) if existing else {}
        med_sel={}
        cols_m=st.columns(2)
        for i,(k,lbl) in enumerate(med_opts.items()):
            med_sel[k]=cols_m[i%2].checkbox(lbl,value=ex_med.get(k,False),key=f"m_{k}")
        med_desc=st.text_area("Descripción de medidas",value=existing.get("med_desc","") if existing else "",height=90,placeholder="Describa las acciones ejecutadas y resultados...")

        st.divider()
        st.markdown("**3. Compromisos para el próximo período**")
        compromisos=st.text_area("Compromisos adoptados",value=existing.get("compromisos","") if existing else "",height=110,placeholder="1. Iniciar licitación para [insumo] antes del [fecha]...\n2. Reducir % TD a menos de 16%...")
        c4,c5=st.columns(2)
        meta_prox=c4.number_input("Meta % TD próximo período",min_value=0.0,max_value=100.0,step=0.5,value=float(existing.get("meta_prox",16.0)) if existing else 16.0,format="%.1f")
        fecha_comp=c5.date_input("Fecha comprometida",value=datetime.date.fromisoformat(existing["fecha_comp"]) if existing and existing.get("fecha_comp") else datetime.date(2026,8,31))

        st.divider()
        st.markdown("**4. Responsable**")
        c6,c7,c8=st.columns(3)
        resp_nombre=c6.text_input("Nombre",value=existing.get("resp_nombre",user["nombre"]) if existing else user["nombre"])
        resp_cargo=c7.text_input("Cargo",value=existing.get("resp_cargo","Jefe/a Abastecimiento") if existing else "Jefe/a Abastecimiento")
        resp_email=c8.text_input("Correo",value=existing.get("resp_email",user.get("email","")) if existing else user.get("email",""))
        obs=st.text_area("Observaciones adicionales",value=existing.get("obs","") if existing else "",height=70)

        st.divider()
        cb1,cb2,_=st.columns([1,1,2])
        guardar=cb1.form_submit_button("💾 Guardar borrador",use_container_width=True)
        enviar=cb2.form_submit_button("📤 Enviar a SSMOC",use_container_width=True,type="primary")

        if guardar or enviar:
            if enviar:
                errs=[]
                if not causas_sel: errs.append("Seleccione al menos una causal.")
                if not causas_desc.strip(): errs.append("Complete la descripción de causas.")
                if not compromisos.strip(): errs.append("Complete los compromisos.")
                if errs:
                    for e in errs: st.error(e)
                    st.stop()
            data={"establecimiento_id":eid_sel,"establecimiento_nombre":estab["nombre"],"reporte_id":periodo_id,"periodo":pinfo["periodo"],"periodo_label":pinfo["label"],"nivel_riesgo":nivel,"pct_2026":estab.get("pct_2026"),"pct_2025":estab.get("pct_2025"),"pct_per":pct_per,"monto_td":monto_td,"n_proc":n_proc,"causas_sel":causas_sel,"causas_desc":causas_desc,"medidas":med_sel,"med_desc":med_desc,"compromisos":compromisos,"meta_prox":meta_prox,"fecha_comp":str(fecha_comp),"resp_nombre":resp_nombre,"resp_cargo":resp_cargo,"resp_email":resp_email,"obs":obs,"estado":"enviado" if enviar else "borrador","usuario":user["username"],"fecha_ingreso":str(datetime.datetime.now().isoformat())}
            upsert_report(data)
            if enviar: st.success(f"✅ Reporte {pinfo['label']} enviado exitosamente."); st.balloons()
            else: st.info("💾 Borrador guardado.")
            st.rerun()


def pg_todos_reportes():
    user=st.session_state.user
    if user["rol"]!="admin": st.error("Solo administradores."); return
    page_header("Todos los reportes","Vista consolidada y gestión — solo administradores")

    reports=load_reports()
    import pandas as pd

    # Filtros
    c1,c2,c3=st.columns(3)
    fp=c1.selectbox("Período",["Todos"]+[p["id"] for p in PERIODOS],format_func=lambda x:"Todos" if x=="Todos" else next(p["label"]+" — "+p["periodo"] for p in PERIODOS if p["id"]==x))
    fn=c2.selectbox("Nivel",["Todos","Rojo","Amarillo","Verde"])
    fe=c3.selectbox("Estado",["Todos","Enviado","Borrador","Pendiente"])

    # Tabla resumen
    st.subheader("Estado consolidado")
    rows=[]
    for eid,e in ESTABLECIMIENTOS.items():
        if e["nivel"]=="verde": continue
        row={"Establecimiento":e["nombre_corto"],"Nivel":e["nivel"].capitalize(),"% TD":f"{e['pct_2026']:.1f}%"}
        for p in PERIODOS:
            r=next((x for x in reports if x.get("establecimiento_id")==eid and x.get("reporte_id")==p["id"]),None)
            row[p["label"]]="✅ Enviado" if r and r.get("estado")=="enviado" else "📝 Borrador" if r else "⬜ Pendiente"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.divider()

    # Detalle
    st.subheader("Detalle de reportes ingresados")
    filtered=reports
    if fp!="Todos": filtered=[r for r in filtered if r.get("reporte_id")==fp]
    if fn!="Todos": filtered=[r for r in filtered if r.get("nivel_riesgo","").lower()==fn.lower()]
    if fe!="Todos": filtered=[r for r in filtered if r.get("estado","").lower()==fe.lower()]

    if not filtered:
        st.info("No hay reportes con los filtros seleccionados.")
        return

    for r in sorted(filtered,key=lambda x:(x.get("reporte_id",""),x.get("nivel_riesgo",""))):
        est=ESTABLECIMIENTOS.get(r["establecimiento_id"],{})
        estado=r.get("estado","borrador")
        icon="✅" if estado=="enviado" else "📝"

        with st.expander(f"{icon} {r.get('establecimiento_nombre','')[:45]} — {r.get('periodo_label','')} — {estado.upper()}"):
            ca,cb,cc,cd=st.columns(4)
            ca.metric("Nivel",r.get("nivel_riesgo","").capitalize())
            cb.metric("% TD 2026",f"{r.get('pct_2026',0):.2f}%")
            cc.metric("% TD período",f"{r.get('pct_per',0):.2f}%")
            cd.metric("N° procesos TD",r.get("n_proc","—"))

            if r.get("causas_sel"):
                st.markdown("**Causales:** " + " · ".join(r["causas_sel"]))
            if r.get("causas_desc"):
                st.markdown(f"**Descripción:** {r['causas_desc']}")
            if r.get("compromisos"):
                st.markdown(f"**Compromisos:** {r['compromisos']}")
            st.markdown(f"**Responsable:** {r.get('resp_nombre','')} · {r.get('resp_cargo','')} · {r.get('resp_email','')}  \n**Meta próximo período:** {r.get('meta_prox',16):.1f}% · **Fecha:** {r.get('fecha_comp','')}  \n**Ingresado:** {r.get('usuario','')} · {r.get('fecha_ingreso','')[:16]}")

            col_acc1,col_acc2,_=st.columns([1,1,3])
            # Cambiar estado
            with col_acc1:
                if estado=="borrador":
                    if st.button("✅ Marcar enviado",key=f"send_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"]="enviado"; upsert_report(r); st.rerun()
                else:
                    if st.button("↩️ A borrador",key=f"rev_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"]="borrador"; upsert_report(r); st.rerun()
            # Eliminar
            with col_acc2:
                if st.button("🗑️ Eliminar reporte",key=f"del_{r['establecimiento_id']}_{r['reporte_id']}",type="secondary"):
                    delete_report(r["establecimiento_id"],r["reporte_id"])
                    st.warning(f"Reporte eliminado: {r.get('establecimiento_nombre','')} — {r.get('periodo_label','')}")
                    st.rerun()


def pg_exportar():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    page_header("Exportar reporte consolidado","Formato Anexo N°1 — Lineamiento MINSAL v1.0")

    reports=load_reports()
    import pandas as pd

    ps=st.selectbox("Período",options=[p["id"] for p in PERIODOS],format_func=lambda x:next(f"{p['label']} — {p['periodo']} (plazo: {p['fecha_limite']})" for p in PERIODOS if p["id"]==x))
    pinfo=next(p for p in PERIODOS if p["id"]==ps)
    inc=st.radio("Incluir",["Solo enviados","Enviados y borradores"],horizontal=True)

    r_p=[r for r in reports if r.get("reporte_id")==ps]
    if inc=="Solo enviados": r_p=[r for r in r_p if r.get("estado")=="enviado"]

    if not r_p:
        st.warning(f"No hay reportes para {pinfo['label']} con los filtros seleccionados.")
        # Mostrar pendientes
        st.markdown("**Establecimientos pendientes:**")
        for eid,e in ESTABLECIMIENTOS.items():
            if e["nivel"] in ["rojo","amarillo"]:
                r=next((x for x in reports if x.get("establecimiento_id")==eid and x.get("reporte_id")==ps),None)
                ic="✅" if r and r.get("estado")=="enviado" else "📝" if r else "⬜"
                st.markdown(f"{ic} {e['nombre']} — {e['nivel'].capitalize()}")
        return

    rows=[]
    for r in r_p:
        med=r.get("medidas",{}); med_txt=", ".join(k.replace("_"," ").title() for k,v in med.items() if v)
        rows.append({"Servicio de Salud":"Metropolitano Occidente","Establecimiento":r.get("establecimiento_nombre",""),"Código DEIS":ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("codigo_deis",""),"RUT":ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("rut",""),"Nivel de Riesgo":r.get("nivel_riesgo","").capitalize(),"Período informado":r.get("periodo",""),"% TD 2026 (MINSAL)":r.get("pct_2026",""),"% TD 2025":r.get("pct_2025",""),"Brecha vs meta (pp)":ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("brecha",""),"Variación vs 2025 (pp)":ESTABLECIMIENTOS.get(r["establecimiento_id"],{}).get("variacion",""),"Monto TD ($CLP)":r.get("monto_td",0),"N° procesos TD":r.get("n_proc",0),"Principales causas":"; ".join(r.get("causas_sel",[])) + ("\n\n"+r.get("causas_desc","") if r.get("causas_desc") else ""),"Medidas implementadas":med_txt+("\n\n"+r.get("med_desc","") if r.get("med_desc") else ""),"Compromisos":r.get("compromisos",""),"Meta próximo período (%)":r.get("meta_prox",""),"Responsable":r.get("resp_nombre",""),"Cargo":r.get("resp_cargo",""),"Correo":r.get("resp_email",""),"Fecha comprometida":r.get("fecha_comp",""),"Observaciones":r.get("obs",""),"Estado":r.get("estado","").upper(),"Fecha ingreso":r.get("fecha_ingreso","")[:16]})

    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.markdown(f"**{len(rows)} establecimiento(s)** · Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        df.to_excel(w,sheet_name="Anexo N°1 MINSAL",index=False)
        resumen=pd.DataFrame([{"Establecimiento":e["nombre"],"Nivel":e["nivel"].capitalize(),"% TD 2026":e["pct_2026"],"Enviado":"✅" if any(r.get("establecimiento_id")==eid and r.get("estado")=="enviado" and r.get("reporte_id")==ps for r in reports) else "⬜"} for eid,e in ESTABLECIMIENTOS.items()])
        resumen.to_excel(w,sheet_name="Resumen SSMOC",index=False)
    buf.seek(0)
    fecha=datetime.datetime.now().strftime("%Y%m%d_%H%M")
    c1,c2=st.columns(2)
    c1.download_button("⬇️ Descargar Excel",buf,f"SSMOC_AnexoN1_{ps}_{fecha}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,type="primary")
    c2.download_button("⬇️ Descargar CSV",df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),f"SSMOC_AnexoN1_{ps}_{fecha}.csv","text/csv",use_container_width=True)

    # Pendientes
    pend=[eid for eid,e in ESTABLECIMIENTOS.items() if e["nivel"] in ["rojo","amarillo"] and not any(r.get("establecimiento_id")==eid and r.get("estado")=="enviado" and r.get("reporte_id")==ps for r in reports)]
    if pend:
        st.warning(f"⚠️ {len(pend)} establecimiento(s) aún sin enviar para {pinfo['label']}:")
        for eid in pend:
            e=ESTABLECIMIENTOS[eid]; st.markdown(f"- **{e['nombre']}** — {e['nivel'].capitalize()} ({e['pct_2026']:.1f}%)")


def pg_usuarios():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    page_header("Gestión de usuarios","Alta, baja y restablecimiento de contraseñas")

    users=load_users()
    import pandas as pd

    tab1,tab2=st.tabs(["📋 Usuarios registrados","➕ Crear / Editar"])

    with tab1:
        rows=[{"Usuario":uid,"Nombre":u["nombre"],"Rol":u["rol"].capitalize(),"Establecimiento":ESTABLECIMIENTOS.get(u.get("establecimiento"),{}).get("nombre_corto","— Admin —"),"Email":u.get("email",""),"Activo":"✅" if u.get("activo") else "❌"} for uid,u in users.items()]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

        st.subheader("Activar / Desactivar usuario")
        ca,cb=st.columns(2)
        uid_sel=ca.selectbox("Usuario",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}")
        activo_act=users.get(uid_sel,{}).get("activo",True)
        if cb.button(f"{'🔴 Desactivar' if activo_act else '🟢 Activar'}",use_container_width=True):
            users[uid_sel]["activo"]=not activo_act; save_users(users)
            st.success(f"Usuario '{uid_sel}' {'desactivado' if activo_act else 'activado'}."); st.rerun()

        with st.expander("🔑 Restablecer contraseña"):
            ur=st.selectbox("Usuario a resetear",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}",key="ur")
            np=st.text_input("Nueva contraseña",type="password",key="np")
            if st.button("Restablecer"):
                if len(np)<8: st.error("Mínimo 8 caracteres.")
                else: users[ur]["password_hash"]=_hash(np); save_users(users); st.success(f"Contraseña restablecida para '{ur}'.")

    with tab2:
        modo=st.radio("Modo",["Crear nuevo","Editar existente"],horizontal=True)
        uid_e=None; u_e={}
        if modo=="Editar existente":
            uid_e=st.selectbox("Usuario a editar",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}",key="ue")
            u_e=users.get(uid_e,{})

        with st.form("fu"):
            c1,c2=st.columns(2)
            nuevo_uid=c1.text_input("Nombre de usuario",placeholder="ej: san_pedro_jefe") if modo=="Crear nuevo" else st.text_input("Usuario",value=uid_e,disabled=True)
            nombre=c1.text_input("Nombre completo",value=u_e.get("nombre",""))
            email=c1.text_input("Correo",value=u_e.get("email",""))
            rol=c2.selectbox("Rol",["establecimiento","admin"],index=0 if u_e.get("rol","establecimiento")=="establecimiento" else 1)
            estab_ops={"":"— Solo admin —"}; estab_ops.update({eid:e["nombre_corto"] for eid,e in ESTABLECIMIENTOS.items()})
            estab_sel=c2.selectbox("Establecimiento",list(estab_ops.keys()),format_func=lambda x:estab_ops[x],index=list(estab_ops.keys()).index(u_e.get("establecimiento","") or ""))
            pwd=c2.text_input("Contraseña"+" (vacío = no cambiar)" if modo=="Editar existente" else "",type="password")
            activo=c2.checkbox("Activo",value=u_e.get("activo",True))

            if st.form_submit_button("💾 Guardar",use_container_width=True,type="primary"):
                uid_f=(nuevo_uid if modo=="Crear nuevo" else uid_e).strip().lower()
                errs=[]
                if not uid_f: errs.append("Usuario vacío.")
                if not nombre.strip(): errs.append("Nombre requerido.")
                if modo=="Crear nuevo" and uid_f in users: errs.append(f"'{uid_f}' ya existe.")
                if modo=="Crear nuevo" and not pwd: errs.append("Contraseña requerida.")
                if errs:
                    for e in errs: st.error(e)
                else:
                    if uid_f not in users: users[uid_f]={}
                    users[uid_f].update({"nombre":nombre.strip(),"rol":rol,"email":email.strip(),"establecimiento":estab_sel or None,"activo":activo})
                    if pwd: users[uid_f]["password_hash"]=_hash(pwd)
                    save_users(users)
                    st.success(f"✅ Usuario '{uid_f}' {'creado' if modo=='Crear nuevo' else 'actualizado'}."); st.rerun()

    with st.expander("📋 Credenciales por defecto"):
        st.markdown("""
| Usuario | Contraseña | Rol | Referente |
|---------|-----------|-----|-----------|
| `admin` | `Admin2026*` | Admin | — |
| `bayron` | `Ssmoc2026*` | Admin | Bayron Retamal |
| `san_juan` | `Sjd2026*` | Establecimiento | Rodrigo Bravo Gajardo |
| `traumatologico` | `Trauma2026*` | Establecimiento | Miguel Jara |
| `felix_bulnes` | `Felix2026*` | Establecimiento | Carolina Castro |
| `talagante` | `Tala2026*` | Establecimiento | M.A. Villegas Albarrán |
| `penaflor` | `Pen2026*` | Establecimiento | Gissela Salvo |
| `melipilla` | `Meli2026*` | Establecimiento | M.A. Morales |
| `curacavi` | `Cura2026*` | Establecimiento | Pablo Yévenes |
| `crs_allende` | `Crs2026*` | Establecimiento | Eric Cubillo |

> ⚠️ Cambie las contraseñas antes de usar en producción.
        """)


def pg_configuracion():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    page_header("Configuración del sistema","Estado y mantenimiento de la plataforma")

    reports=load_reports()
    import pandas as pd

    c1,c2=st.columns(2)
    with c1:
        st.subheader("Resumen del sistema")
        st.markdown(f"""
| Parámetro | Valor |
|-----------|-------|
| Versión | 1.0.0 |
| Lineamiento | MINSAL v1.0 · Junio 2026 |
| Meta institucional | ≤ 16% |
| Establecimientos | {len(ESTABLECIMIENTOS)} |
| Períodos de reporte | {len(PERIODOS)} |
| Reportes totales | {len(reports)} |
| Enviados | {len([r for r in reports if r.get("estado")=="enviado"])} |
| Borradores | {len([r for r in reports if r.get("estado")=="borrador"])} |
        """)
    with c2:
        st.subheader("Avance por período")
        for p in PERIODOS:
            done=len([r for r in reports if r.get("reporte_id")==p["id"] and r.get("estado")=="enviado"])
            req=len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
            st.markdown(f"**{p['label']}** — {p['periodo']} · Plazo: `{p['fecha_limite']}`")
            st.progress(done/req if req else 0, text=f"{done}/{req} enviados")

    st.divider()
    st.subheader("Datos de referencia SSMOC (CSV MINSAL)")
    df=pd.DataFrame([{"Establecimiento":e["nombre_corto"],"Nivel":e["nivel"].capitalize(),"% TD 2026":e["pct_2026"],"% TD 2025":e["pct_2025"],"Brecha (pp)":e["brecha"],"Var. (pp)":e["variacion"],"Denominador":e["denominador"],"Numerador":e["numerador"]} for e in ESTABLECIMIENTOS.values()])
    st.dataframe(df,use_container_width=True,hide_index=True)

    st.divider()
    with st.expander("🗑️ Mantenimiento — eliminar datos"):
        st.warning("⚠️ Acción irreversible.")
        if st.button("Eliminar TODOS los reportes"):
            save_reports([]); st.success("Reportes eliminados."); st.rerun()

# ═══════════════════════════════════════════════════════════════════════
# ROUTING PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════
if st.session_state.user is None:
    page_login()
else:
    render_sidebar()
    pg = st.session_state.page
    if   pg=="dashboard":      pg_dashboard()
    elif pg=="mis_reportes":   pg_mis_reportes()
    elif pg=="todos_reportes": pg_todos_reportes()
    elif pg=="exportar":       pg_exportar()
    elif pg=="usuarios":       pg_usuarios()
    elif pg=="configuracion":  pg_configuracion()
    else:                      pg_dashboard()
