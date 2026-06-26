"""
app.py — Monitor Trato Directo SSMOCC v10
Navegación sin sidebar para evitar problema de colapso en Streamlit Cloud
"""
import streamlit as st
import hashlib, json, datetime, io, base64, csv
from pathlib import Path

st.set_page_config(
    page_title="Monitor TD — SSMOCC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebarNavItems"]{display:none!important;}
[data-testid="stSidebarNav"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding-top:0!important;padding-bottom:2rem!important;max-width:100%!important;}
/* Navbar top */
.topbar{background:#0A3964;padding:0;margin-bottom:0;position:sticky;top:0;z-index:999;}
.topbar-inner{display:flex;align-items:center;gap:0;padding:0 8px;}
.topbar-logo{padding:8px 12px;border-right:3px solid #C0392B;display:flex;align-items:center;}
.topbar-logo img{height:38px;border-radius:3px;}
.topbar-title{padding:0 16px;flex:1;}
.topbar-title .t1{font-size:14px;font-weight:700;color:#fff;}
.topbar-title .t2{font-size:10px;color:rgba(255,255,255,.5);}
.topbar-user{padding:8px 14px;border-left:1px solid rgba(255,255,255,.15);text-align:right;}
.topbar-user .u1{font-size:12px;font-weight:600;color:#fff;}
.topbar-user .u2{font-size:10px;color:rgba(255,255,255,.45);}
/* Nav pills */
.navpills{background:#1F3864;display:flex;gap:4px;padding:6px 16px;flex-wrap:wrap;align-items:center;}
.stButton>button{border-radius:6px!important;font-size:12px!important;padding:5px 14px!important;}
/* Cards */
.kcard{background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;border-top:3px solid #1F3864;}
.kcard .lbl{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:5px;}
.kcard .val{font-size:22px;font-weight:700;line-height:1;}
.kcard .note{font-size:11px;color:#94a3b8;margin-top:4px;}
/* Niveles */
.nr{background:#FEF2F2;color:#991B1B;border:1px solid #FECACA;padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700;}
.na{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A;padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700;}
.nv{background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# DATOS
# ═══════════════════════════════════════════════════════════════════════
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE   = DATA_DIR / "users.json"
REPORTS_FILE = DATA_DIR / "reports.json"
DATOS_FILE   = DATA_DIR / "datos_minsal.json"

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

ESTABLECIMIENTOS = {
    "traumatologico": {"nombre":"Instituto Traumatológico Dr. Teodoro Gebauer","nombre_corto":"Inst. Traumatológico","rut":"61.608.203-5","codigo_deis":"110110","pct_2026":62.17,"pct_2025":37.78,"brecha":46.17,"variacion":24.39,"nivel":"rojo","denominador":5868063249,"numerador":3648430684},
    "direccion":      {"nombre":"Dirección del Servicio Metropolitano Occidente","nombre_corto":"Dir. SSMOCC","rut":"61.608.200-0","codigo_deis":"110010","pct_2026":37.16,"pct_2025":5.30,"brecha":21.16,"variacion":31.86,"nivel":"rojo","denominador":5835193133,"numerador":2168191360},
    "felix_bulnes":   {"nombre":"Hospital Dr. Félix Bulnes Cerda","nombre_corto":"H. Félix Bulnes","rut":"61.608.205-1","codigo_deis":"110120","pct_2026":26.44,"pct_2025":21.59,"brecha":10.44,"variacion":4.85,"nivel":"rojo","denominador":19487598854,"numerador":5152786649},
    "san_juan":       {"nombre":"Hospital San Juan de Dios","nombre_corto":"H. San Juan de Dios","rut":"61.608.204-3","codigo_deis":"110100","pct_2026":11.61,"pct_2025":10.70,"brecha":-4.39,"variacion":0.91,"nivel":"amarillo","denominador":39066763291,"numerador":4535664841},
    "crs_allende":    {"nombre":"Centro de Referencia Salud Occidente Salvador Allende","nombre_corto":"CRS Salvador Allende","rut":"61.933.400-0","codigo_deis":"110300","pct_2026":7.07,"pct_2025":4.76,"brecha":-8.93,"variacion":2.31,"nivel":"amarillo","denominador":1954204231,"numerador":138204661},
    "melipilla":      {"nombre":"Hospital San José (Melipilla)","nombre_corto":"H. Melipilla","rut":"61.602.122-2","codigo_deis":"110150","pct_2026":6.60,"pct_2025":8.29,"brecha":-9.40,"variacion":-1.69,"nivel":"verde","denominador":6908126647,"numerador":455863218},
    "penaflor":       {"nombre":"Hospital de Peñaflor","nombre_corto":"H. Peñaflor","rut":"61.602.121-4","codigo_deis":"110140","pct_2026":6.89,"pct_2025":17.58,"brecha":-9.11,"variacion":-10.69,"nivel":"verde","denominador":1677287316,"numerador":115598031},
    "curacavi":       {"nombre":"Hospital de Curacaví","nombre_corto":"H. Curacaví","rut":"61.602.125-7","codigo_deis":"110160","pct_2026":5.62,"pct_2025":14.42,"brecha":-10.38,"variacion":-8.80,"nivel":"verde","denominador":1001068453,"numerador":56257312},
    "talagante":      {"nombre":"Hospital Adalberto Steeger (Talagante)","nombre_corto":"H. Talagante","rut":"61.602.121-4","codigo_deis":"110130","pct_2026":3.21,"pct_2025":10.63,"brecha":-12.79,"variacion":-7.42,"nivel":"verde","denominador":7242041556,"numerador":232416794},
}

# Mapa de DEIS → clave interna (para actualización desde CSV MINSAL)
DEIS_MAP = {
    "110110": "traumatologico",
    "110010": "direccion",
    "110120": "felix_bulnes",
    "110100": "san_juan",
    "110300": "crs_allende",
    "110150": "melipilla",
    "110140": "penaflor",
    "110160": "curacavi",
    "110130": "talagante",
}

def load_datos_minsal():
    """Carga datos MINSAL desde JSON guardado (si existe), si no usa los hardcoded."""
    if DATOS_FILE.exists():
        try:
            saved = json.loads(DATOS_FILE.read_text(encoding="utf-8"))
            # Merge saved data into ESTABLECIMIENTOS
            for eid, vals in saved.items():
                if eid in ESTABLECIMIENTOS:
                    ESTABLECIMIENTOS[eid].update(vals)
        except Exception:
            pass

def save_datos_minsal(updates: dict):
    """Guarda datos actualizados de MINSAL en JSON."""
    DATOS_FILE.write_text(json.dumps(updates, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_csv_minsal(file_bytes) -> dict:
    """
    Parsea el CSV oficial MINSAL con columnas:
    Codigo DEIS | RUT | Establecimiento | Servicio de Salud |
    Denominador | Numerador | % Trato Directo 2026 |
    % Trato Directo periodo equivalente 2025 | Brecha vs meta |
    Variacion vs 2025 | Nivel de riesgo
    Retorna dict con clave = eid_interno, valor = campos actualizados.
    """
    import io as _io
    content_str = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(_io.StringIO(content_str), delimiter=";")
    updates = {}
    errors = []
    rows_found = 0

    for row in reader:
        # Normalizar claves (strip espacios)
        row = {k.strip(): v.strip() for k, v in row.items() if k}
        deis = row.get("Codigo DEIS","").strip().zfill(6)
        eid = DEIS_MAP.get(deis)
        if not eid:
            # Intentar por nombre
            nombre_csv = row.get("Establecimiento","").lower()
            for k, e in ESTABLECIMIENTOS.items():
                if e["nombre"].lower() in nombre_csv or nombre_csv in e["nombre"].lower():
                    eid = k; break

        if not eid:
            errors.append(f"DEIS {deis} no reconocido: {row.get('Establecimiento','')}")
            continue

        rows_found += 1
        try:
            def parse_float(v):
                v = v.replace(",",".").replace(" ","").replace("$","").replace("%","")
                return float(v) if v else 0.0

            pct_2026 = parse_float(row.get("% Trato Directo 2026", "0"))
            pct_2025 = parse_float(row.get("% Trato Directo periodo equivalente 2025", "0"))
            brecha   = parse_float(row.get("Brecha vs meta", "0"))
            variacion= parse_float(row.get("Variacion vs 2025", "0"))
            den      = int(float(row.get("Denominador","0").replace(",",".").replace(" ","")))
            num      = int(float(row.get("Numerador","0").replace(",",".").replace(" ","")))
            nivel_raw= row.get("Nivel de riesgo","verde").strip().lower()
            nivel    = nivel_raw if nivel_raw in ["rojo","amarillo","verde"] else "verde"

            updates[eid] = {
                "pct_2026":  pct_2026,
                "pct_2025":  pct_2025,
                "brecha":    brecha,
                "variacion": variacion,
                "denominador": den,
                "numerador":   num,
                "nivel":       nivel,
                "rut":  row.get("RUT", ESTABLECIMIENTOS[eid].get("rut","")),
                "codigo_deis": deis,
                "ultima_actualizacion": datetime.datetime.now().isoformat()[:10],
                "fuente_csv": row.get("Establecimiento",""),
            }
        except Exception as ex:
            errors.append(f"{eid}: {ex}")

    return updates, errors, rows_found

# Cargar datos actualizados al iniciar
load_datos_minsal()
PERIODOS = [
    {"id":"R1","label":"1° Reporte","periodo":"Enero–Marzo 2026",     "fecha_limite":"2026-07-31","fecha_txt":"31 Jul 2026"},
    {"id":"R2","label":"2° Reporte","periodo":"Abril–Junio 2026",     "fecha_limite":"2026-08-31","fecha_txt":"31 Ago 2026"},
    {"id":"R3","label":"3° Reporte","periodo":"Jul–Sep 2026",         "fecha_limite":"2026-11-30","fecha_txt":"30 Nov 2026"},
    {"id":"R4","label":"4° Reporte","periodo":"Oct–Dic 2026",         "fecha_limite":"2027-02-28","fecha_txt":"28 Feb 2027"},
]
CAUSALES = ["Proveedor único / exclusividad","Emergencia o urgencia debidamente calificada","Licitación desierta (2° vez)","Confidencialidad / seguridad nacional","Continuidad de servicios en ejecución","Derechos de propiedad intelectual (software/licencias)","Equipamiento especializado sin equivalente","Convenio con otro organismo público (CENABAST, etc.)","Compra ágil (< 30 UTM)","Otra causal — especificar en observaciones"]

def _default_users():
    raw = {
        "admin":         ("Administrador SSMOCC",            "admin",          "abastecimiento@ssmocc.cl",         None,             "Admin2026*"),
        "bayron":        ("Bayron Retamal González",         "admin",          "bayron.retamal@ssmocc.cl",         None,             "Ssmoc2026*"),
        "traumatologico":("Miguel Jara",                    "establecimiento","miguel.jara@intraumatologico.cl",  "traumatologico", "Trauma2026*"),
        "direccion":     ("Referente Dir. SSMOCC",           "establecimiento","abast.direccion@ssmocc.cl",        "direccion",      "Dir2026*"),
        "felix_bulnes":  ("Carolina Castro",                "establecimiento","carolina.castroj@redsalud.gob.cl", "felix_bulnes",   "Felix2026*"),
        "san_juan":      ("Rodrigo Bravo Gajardo",          "establecimiento","rodrigo.bravog@redsalud.gob.cl",   "san_juan",       "Sjd2026*"),
        "crs_allende":   ("Eric Cubillo Antúnez",           "establecimiento","eric.cubillo@redsalud.gob.cl",     "crs_allende",    "Crs2026*"),
        "melipilla":     ("María de los Ángeles Morales",   "establecimiento","maria.moralesj@redsalud.gob.cl",   "melipilla",      "Meli2026*"),
        "penaflor":      ("Gissela Salvo",                  "establecimiento","gissela.salvo@redsalud.gob.cl",    "penaflor",       "Pen2026*"),
        "curacavi":      ("Pablo Yévenes Olivares",         "establecimiento","pablo.yevenes@redsalud.gob.cl",    "curacavi",       "Cura2026*"),
        "talagante":     ("María Andrea Villegas Albarrán", "establecimiento","mandrea.villegas@redsalud.gob.cl", "talagante",      "Tala2026*"),
    }
    return {uid:{"nombre":n,"rol":r,"email":e,"establecimiento":est,"password_hash":_hash(p),"activo":True} for uid,(n,r,e,est,p) in raw.items()}

def load_users():
    if not USERS_FILE.exists(): u=_default_users(); save_users(u); return u
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))
def save_users(u): USERS_FILE.write_text(json.dumps(u,ensure_ascii=False,indent=2),encoding="utf-8")
def load_reports():
    if not REPORTS_FILE.exists(): return []
    return json.loads(REPORTS_FILE.read_text(encoding="utf-8"))
def save_reports(r): REPORTS_FILE.write_text(json.dumps(r,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
def upsert_report(data):
    rpts=load_reports()
    for i,r in enumerate(rpts):
        if r["establecimiento_id"]==data["establecimiento_id"] and r["reporte_id"]==data["reporte_id"]:
            rpts[i]=data; save_reports(rpts); return
    rpts.append(data); save_reports(rpts)
def delete_report(eid,rid):
    save_reports([r for r in load_reports() if not(r["establecimiento_id"]==eid and r["reporte_id"]==rid)])
def authenticate(u,p):
    users=load_users(); usr=users.get(u.strip().lower())
    if usr and usr.get("activo") and usr["password_hash"]==_hash(p): return {**usr,"username":u.strip().lower()}
    return None

def get_logo():
    p=Path(__file__).parent/"logo_ssmocc.jpg"
    if p.exists(): return base64.b64encode(p.read_bytes()).decode()
    return None
LOGO=get_logo()
def logo_img(h=38):
    if LOGO: return f'<img src="data:image/jpeg;base64,{LOGO}" style="height:{h}px;border-radius:3px">'
    return '<span style="font-size:26px">🏥</span>'

# Session
for k,v in [("user",None),("page","dashboard")]:
    if k not in st.session_state: st.session_state[k]=v

# ═══════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown(f"""
    <div style="text-align:center;margin:50px auto 24px;max-width:400px">
        {logo_img(90)}
        <div style="font-size:22px;font-weight:700;color:#1F3864;margin-top:12px">Monitor Trato Directo</div>
        <div style="font-size:13px;color:#64748b;margin-top:4px">Servicio de Salud Metropolitano Occidente</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:2px">Lineamiento MINSAL v1.0 · Junio 2026</div>
    </div>""", unsafe_allow_html=True)
    _,col,_ = st.columns([1,1,1])
    with col:
        with st.form("lf"):
            u=st.text_input("👤 Usuario",placeholder="Ingrese su usuario")
            p=st.text_input("🔒 Contraseña",type="password",placeholder="Ingrese su contraseña")
            if st.form_submit_button("Ingresar",use_container_width=True,type="primary"):
                usr=authenticate(u,p)
                if usr: st.session_state.user=usr; st.session_state.page="dashboard"; st.rerun()
                else: st.error("Usuario o contraseña incorrectos.")
        st.markdown('<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:11px 14px;margin-top:12px;font-size:12px;color:#1E40AF">Acceso restringido — sistema exclusivo para referentes de abastecimiento SSMOCC.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TOPBAR + NAV (reemplaza al sidebar)
# ═══════════════════════════════════════════════════════════════════════
def render_topbar():
    user=st.session_state.user
    reports=load_reports()
    r1_req=len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
    r1_done=len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])
    pct=int(r1_done/r1_req*100) if r1_req else 0
    col_pct="#4ade80" if r1_done==r1_req else "#fbbf24" if r1_done>0 else "#f87171"
    estab=ESTABLECIMIENTOS.get(user.get("establecimiento"),{})
    rol_txt="🔑 Admin" if user["rol"]=="admin" else f"🏥 {estab.get('nombre_corto','')}"

    st.markdown(f"""
    <div class="topbar">
      <div class="topbar-inner">
        <div class="topbar-logo">{logo_img(38)}</div>
        <div class="topbar-title">
          <div class="t1">Monitor Trato Directo — SSMOCC 2026</div>
          <div class="t2">Lineamiento MINSAL v1.0 · Subsecretaría de Redes Asistenciales</div>
        </div>
        <div style="padding:6px 14px;border-left:1px solid rgba(255,255,255,.15);text-align:center;min-width:120px">
          <div style="font-size:10px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.06em">1° Reporte</div>
          <div style="font-size:16px;font-weight:700;color:{col_pct}">{r1_done}/{r1_req}</div>
          <div style="background:rgba(255,255,255,.15);border-radius:3px;height:3px;margin-top:4px">
            <div style="width:{pct}%;height:100%;background:{col_pct};border-radius:3px"></div>
          </div>
        </div>
        <div class="topbar-user">
          <div class="u1">{user['nombre']}</div>
          <div class="u2">{rol_txt}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Nav pills
    nav=[("📊","Dashboard","dashboard"),("📋","Mis reportes","mis_reportes")]
    if user["rol"]=="admin":
        nav+=[("📁","Todos los reportes","todos_reportes"),("📤","Exportar MINSAL","exportar"),("📂","Actualizar datos","actualizar_datos"),("👥","Usuarios","usuarios"),("⚙️","Config.","configuracion")]
    nav.append(("🚪","Cerrar sesión","__logout__"))

    cols=st.columns(len(nav))
    for i,(icon,label,pid) in enumerate(nav):
        active=st.session_state.page==pid
        with cols[i]:
            if st.button(f"{icon} {label}",key=f"nav_{pid}",use_container_width=True,
                        type="primary" if active else "secondary"):
                if pid=="__logout__":
                    st.session_state.user=None; st.session_state.page="dashboard"; st.rerun()
                else:
                    st.session_state.page=pid; st.rerun()
    st.markdown("<hr style='margin:0 0 12px;border-color:#e2e8f0'>",unsafe_allow_html=True)
    st.markdown('''<div style="text-align:right;font-size:10px;color:#94a3b8;margin-top:-10px;padding-right:4px;margin-bottom:4px">
        Desarrollado por <strong style="color:#64748b">Bayron Retamal González</strong> &nbsp;·&nbsp; Subdirección RFF &nbsp;·&nbsp; SSMOCC 2026
    </div>''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# HELPERS UI
# ═══════════════════════════════════════════════════════════════════════
def page_header(title,sub=""):
    st.markdown(f"""
    <div style="background:#1F3864;padding:12px 20px;border-radius:10px;margin-bottom:16px;display:flex;align-items:center;gap:12px">
        {logo_img(36)}
        <div style="width:4px;background:#C0392B;border-radius:2px;align-self:stretch;min-height:30px"></div>
        <div>
            <div style="font-size:16px;font-weight:700;color:white">{title}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:2px">{sub}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def kpi_card(col,label,value,note,color="#1F3864"):
    col.markdown(f"""
    <div class="kcard" style="border-top-color:{color}">
        <div class="lbl">{label}</div>
        <div class="val" style="color:{color}">{value}</div>
        <div class="note">{note}</div>
    </div>""", unsafe_allow_html=True)

def nivel_pill(nivel):
    cls={"rojo":"nr","amarillo":"na","verde":"nv"}.get(nivel,"nv")
    return f'<span class="{cls}">{nivel.capitalize()}</span>'

def cal_cards(reports, eid_filter=None):
    hoy=datetime.date.today()
    req=len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
    cols=st.columns(4)
    for i,p in enumerate(PERIODOS):
        fl=datetime.date.fromisoformat(p["fecha_limite"])
        dias=(fl-hoy).days
        if eid_filter:
            r=next((x for x in reports if x.get("establecimiento_id")==eid_filter and x.get("reporte_id")==p["id"]),None)
            est=r.get("estado","pendiente") if r else "pendiente"
            if est=="enviado":     bg,tc,bc,tag="#F0FDF4","#166534","#BBF7D0","✅ ENVIADO"
            elif est=="borrador":  bg,tc,bc,tag="#FFFBEB","#92400E","#FDE68A","📝 BORRADOR"
            elif dias<0:           bg,tc,bc,tag="#FEF2F2","#991B1B","#FECACA","⛔ VENCIDO"
            elif dias<=14:         bg,tc,bc,tag="#FEF2F2","#991B1B","#FECACA",f"⚠️ {dias}d"
            elif dias<=30:         bg,tc,bc,tag="#FFFBEB","#92400E","#FDE68A",f"🔔 {dias}d"
            else:                  bg,tc,bc,tag="#F8FAFC","#475569","#E2E8F0",f"📅 {dias}d"
            sub=f"Estado: <b>{est.upper()}</b>"
        else:
            env=len([r for r in reports if r.get("reporte_id")==p["id"] and r.get("estado")=="enviado"])
            if env==req:           bg,tc,bc,tag="#F0FDF4","#166534","#BBF7D0","✅ COMPLETO"
            elif dias<0:           bg,tc,bc,tag="#FEF2F2","#991B1B","#FECACA","⛔ VENCIDO"
            elif dias<=14:         bg,tc,bc,tag="#FEF2F2","#991B1B","#FECACA",f"⚠️ {dias}d"
            elif dias<=30:         bg,tc,bc,tag="#FFFBEB","#92400E","#FDE68A",f"🔔 {dias}d"
            else:                  bg,tc,bc,tag="#F8FAFC","#475569","#E2E8F0",f"📅 {dias}d"
            sub=f"{env}/{req} enviados"
        with cols[i]:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bc};border-top:3px solid {tc};
                        border-radius:8px;padding:10px;text-align:center;height:110px;display:flex;flex-direction:column;justify-content:center">
                <div style="font-size:14px;font-weight:800;color:{tc}">{p['label']}</div>
                <div style="font-size:10px;color:{tc};margin:2px 0">{p['periodo']}</div>
                <div style="font-size:11px;font-weight:600;color:{tc}">{p['fecha_txt']}</div>
                <div style="background:rgba(0,0,0,.07);border-radius:4px;padding:2px 6px;margin-top:5px;font-size:10px;color:{tc};font-weight:700">{tag}</div>
                <div style="font-size:10px;color:{tc};margin-top:2px">{sub}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# PÁGINA DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
def pg_dashboard():
    import plotly.graph_objects as go
    import pandas as pd
    user=st.session_state.user
    es_admin=user["rol"]=="admin"
    eid_user=user.get("establecimiento")
    reports=load_reports()

    # ── VISTA ESTABLECIMIENTO ─────────────────────────────────────────
    if not es_admin and eid_user:
        e=ESTABLECIMIENTOS.get(eid_user,{})
        nivel=e.get("nivel","verde")
        nc={"rojo":"#E24B4A","amarillo":"#F59E0B","verde":"#22C55E"}.get(nivel,"#22C55E")
        nt={"rojo":"#991B1B","amarillo":"#92400E","verde":"#166534"}.get(nivel,"#166534")
        nb={"rojo":"#FEF2F2","amarillo":"#FFFBEB","verde":"#F0FDF4"}.get(nivel,"#F0FDF4")
        nbc={"rojo":"#FECACA","amarillo":"#FDE68A","verde":"#BBF7D0"}.get(nivel,"#BBF7D0")
        va=f"+{e.get('variacion',0):.2f}" if e.get("variacion",0)>0 else f"{e.get('variacion',0):.2f}"

        page_header(f"Mi establecimiento — {e.get('nombre_corto','')}",
                    "Datos oficiales MINSAL · Período enero–junio 2026 · Meta institucional ≤ 16%")

        c1,c2,c3,c4=st.columns(4)
        kpi_card(c1,"Numerador CLP",f"${e.get('numerador',0)/1e9:.1f} MM","Monto TD recepción conforme","#0C447C")
        kpi_card(c2,"Denominador CLP",f"${e.get('denominador',0)/1e9:.1f} MM","Total todas las modalidades","#0C447C")
        kpi_card(c3,"% TD 2026",f"{e.get('pct_2026',0):.2f}%",f"Brecha {'+' if e.get('brecha',0)>0 else ''}{e.get('brecha',0):.2f} pp vs meta",nt)
        kpi_card(c4,"% TD 2025 mismo período",f"{e.get('pct_2025',0):.2f}%",f"Variación: {va} pp","#0C447C")

        acciones={"rojo":"Elaborar plan de acción · Reunión técnica de seguimiento · Monitoreo mensual · Ingresar reporte con causas y compromisos.","amarillo":"Analizar causas del resultado · Identificar compras para migrar a mecanismos competitivos · Ingresar reporte con medidas implementadas.","verde":"Mantener buenas prácticas · No se requiere remitir antecedentes a la Subsecretaría."}
        titulo_e={"rojo":"Requiere plan de acción urgente","amarillo":"Monitoreo reforzado","verde":"Mantener buenas prácticas"}
        st.markdown(f"""
        <div style="background:{nb};border-left:5px solid {nc};border:1px solid {nbc};padding:12px 16px;border-radius:8px;margin:12px 0">
            <div style="font-size:13px;font-weight:700;color:{nt}">Nivel {nivel.upper()} — {titulo_e[nivel]}</div>
            <div style="font-size:12px;color:{nt};margin-top:4px;line-height:1.6">{acciones[nivel]}</div>
        </div>""", unsafe_allow_html=True)

        col_g,col_r=st.columns([1.2,1])
        with col_g:
            st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:6px">Comparación % TD — 2025 vs 2026</div>',unsafe_allow_html=True)
            fig=go.Figure()
            fig.add_trace(go.Bar(name="% TD 2025",x=["Mismo período 2025"],y=[e.get("pct_2025",0)],marker_color="#CBD5E1",text=[f"{e.get('pct_2025',0):.1f}%"],textposition="outside"))
            fig.add_trace(go.Bar(name="% TD 2026",x=["Acumulado 2026"],y=[e.get("pct_2026",0)],marker_color=nc,text=[f"{e.get('pct_2026',0):.1f}%"],textposition="outside"))
            fig.add_hline(y=16,line_dash="dash",line_color="#1F3864",line_width=1.5,annotation_text="Meta 16%",annotation_position="top right")
            fig.update_layout(height=200,margin=dict(l=0,r=60,t=20,b=20),plot_bgcolor="white",paper_bgcolor="white",showlegend=True,legend=dict(orientation="h",y=1.1,x=0),yaxis=dict(range=[0,max(e.get("pct_2026",0)+15,30)],gridcolor="#f1f5f9"),font=dict(size=11,family="Arial"))
            st.plotly_chart(fig,use_container_width=True)
        with col_r:
            st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:6px">Datos MINSAL oficiales</div>',unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:white;border:0.5px solid #e2e8f0;border-radius:8px;padding:12px">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
                    <div><span style="color:#64748b">Código DEIS</span><br><b>{e.get('codigo_deis','')}</b></div>
                    <div><span style="color:#64748b">RUT</span><br><b>{e.get('rut','')}</b></div>
                    <div><span style="color:#64748b">Numerador</span><br><b>${e.get('numerador',0):,.0f}</b></div>
                    <div><span style="color:#64748b">Denominador</span><br><b>${e.get('denominador',0):,.0f}</b></div>
                    <div><span style="color:#64748b">% TD 2026</span><br><b style="color:{nt}">{e.get('pct_2026',0):.2f}%</b></div>
                    <div><span style="color:#64748b">Brecha vs meta</span><br><b style="color:{nt}">{'+' if e.get('brecha',0)>0 else ''}{e.get('brecha',0):.2f} pp</b></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin:14px 0 8px">Estado de mis reportes</div>',unsafe_allow_html=True)
        cal_cards(reports, eid_filter=eid_user)

        st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin:14px 0 8px">📅 Plazos — Lineamiento MINSAL v1.0</div>',unsafe_allow_html=True)
        st.markdown('<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:6px;padding:9px 14px;font-size:11px;color:#1E40AF">Los antecedentes se remiten de manera consolidada por el SSMOCC, incluyendo únicamente establecimientos en categoría Amarilla y Roja.</div>',unsafe_allow_html=True)

        if nivel in ["rojo","amarillo"]:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("📋  Ingresar mi reporte →",type="primary"):
                st.session_state.page="mis_reportes"; st.rerun()
        return

    # ── VISTA ADMIN ───────────────────────────────────────────────────
    page_header("Monitoreo Trato Directo — Red SSMOCC 2026",
                "Lineamiento MINSAL v1.0 · Junio 2026 · Fuente: ChileCompra — OC aceptadas con recepción conforme, monto neto CLP")

    total_num=sum(e["numerador"] for e in ESTABLECIMIENTOS.values())
    total_den=sum(e["denominador"] for e in ESTABLECIMIENTOS.values())
    pct_s=round(total_num/total_den*100,2)
    rojos=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="rojo"]
    amarillos=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="amarillo"]
    verdes=[e for e in ESTABLECIMIENTOS.values() if e["nivel"]=="verde"]
    r1_req=len(rojos)+len(amarillos)
    r1_done=len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])

    c1,c2,c3,c4=st.columns(4)
    kpi_card(c1,"Numerador SSMOCC",f"${total_num/1e12:.2f} MMM","TD con recepción conforme","#0C447C")
    kpi_card(c2,"Denominador SSMOCC",f"${total_den/1e12:.2f} MMM","Todas las modalidades","#0C447C")
    kpi_card(c3,"% TD SSMOCC 2026",f"{pct_s:.2f}%",f"Meta ≤ 16% · Brecha +{pct_s-16:.2f} pp","#A32D2D")
    kpi_card(c4,"1° Reporte (31 Jul)",f"{r1_done}/{r1_req}","Establecimientos enviados","#0F6E56")

    st.markdown("<br>",unsafe_allow_html=True)
    col_g,col_s=st.columns([3,1.2])
    with col_g:
        st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:6px">% TD por establecimiento — comparación 2025 vs 2026</div>',unsafe_allow_html=True)
        df=pd.DataFrame([{"Establecimiento":e["nombre_corto"],"2025":e["pct_2025"],"2026":e["pct_2026"],"nivel":e["nivel"]} for e in ESTABLECIMIENTOS.values()]).sort_values("2026",ascending=True)
        cmap={"rojo":"#E24B4A","amarillo":"#F59E0B","verde":"#22C55E"}
        fig=go.Figure()
        fig.add_trace(go.Bar(name="% TD 2025",y=df["Establecimiento"],x=df["2025"],orientation="h",marker_color="#CBD5E1",opacity=0.7))
        fig.add_trace(go.Bar(name="% TD 2026",y=df["Establecimiento"],x=df["2026"],orientation="h",marker_color=[cmap[n] for n in df["nivel"]]))
        fig.add_vline(x=16,line_dash="dash",line_color="#1F3864",line_width=1.5,annotation_text="Meta 16%",annotation_font_color="#1F3864")
        fig.update_layout(barmode="overlay",height=280,margin=dict(l=0,r=20,t=10,b=20),legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0,font=dict(size=10)),plot_bgcolor="white",paper_bgcolor="white",xaxis=dict(range=[0,70],gridcolor="#f1f5f9"),font=dict(size=10,family="Arial"))
        st.plotly_chart(fig,use_container_width=True)
    with col_s:
        st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:6px">Semáforo de riesgo</div>',unsafe_allow_html=True)
        for nv,estabs,bg,tc,bc in [("🔴 Rojo",rojos,"#FEF2F2","#991B1B","#FECACA"),("🟡 Amarillo",amarillos,"#FFFBEB","#92400E","#FDE68A"),("🟢 Verde",verdes,"#F0FDF4","#166534","#BBF7D0")]:
            names="<br>".join(f"• {e['nombre_corto']}" for e in estabs)
            st.markdown(f'<div style="background:{bg};border:1px solid {bc};border-radius:8px;padding:8px 12px;margin-bottom:6px"><div style="font-size:11px;font-weight:700;color:{tc}">{nv} ({len(estabs)})</div><div style="font-size:10px;color:{tc};margin-top:3px;line-height:1.6">{names}</div></div>',unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#f1f5f9;margin:12px 0'>",unsafe_allow_html=True)

    # Casos críticos
    st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:8px">Establecimientos en nivel rojo</div>',unsafe_allow_html=True)
    cols_r=st.columns(len(rojos))
    for i,e in enumerate(sorted(rojos,key=lambda x:-x["pct_2026"])):
        va=f"+{e['variacion']:.1f}" if e["variacion"]>0 else f"{e['variacion']:.1f}"
        with cols_r[i]:
            st.markdown(f'<div style="background:white;border:1px solid #FECACA;border-top:4px solid #E24B4A;border-radius:8px;padding:12px"><div style="font-size:11px;font-weight:600;color:#991B1B">{e["nombre_corto"]}</div><div style="font-size:26px;font-weight:800;color:#A32D2D;line-height:1.1">{e["pct_2026"]:.1f}%</div><div style="font-size:10px;color:#DC2626;margin-top:3px">Brecha: +{e["brecha"]:.1f} pp · Var.: {va} pp</div></div>',unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#f1f5f9;margin:12px 0'>",unsafe_allow_html=True)

    # Tabla estado
    st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:6px">Estado de reportes</div>',unsafe_allow_html=True)
    rows=[]
    for eid,e in ESTABLECIMIENTOS.items():
        if e["nivel"]=="verde": continue
        row={"Establecimiento":e["nombre_corto"],"Nivel":f"{'🔴' if e['nivel']=='rojo' else '🟡'} {e['nivel'].capitalize()}","% TD":f"{e['pct_2026']:.1f}%"}
        for p in PERIODOS:
            r=next((x for x in reports if x.get("establecimiento_id")==eid and x.get("reporte_id")==p["id"]),None)
            row[p["label"]]="✅ Enviado" if r and r.get("estado")=="enviado" else "📝 Borrador" if r else "⬜ Pendiente"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    st.markdown("<hr style='border-color:#f1f5f9;margin:12px 0'>",unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;font-weight:600;color:#1F3864;margin-bottom:8px">📅 Calendario de reportes — Lineamiento MINSAL v1.0</div>',unsafe_allow_html=True)
    cal_cards(reports)
    st.markdown('<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:6px;padding:9px 14px;font-size:11px;color:#1E40AF;margin-top:8px"><strong>Nota MINSAL:</strong> Los antecedentes se remiten consolidados por el Servicio de Salud, incluyendo únicamente establecimientos en categoría Amarilla y Roja. Las fechas pueden ajustarse según disponibilidad de ChileCompra.</div>',unsafe_allow_html=True)

    with st.expander("📊 Contexto nacional — 224 establecimientos MINSAL"):
        nc1,nc2,nc3,nc4=st.columns(4)
        nc1.metric("Numerador nacional","$238,1 MMM"); nc2.metric("Denominador nacional","$1.434,9 MMM")
        nc3.metric("% TD nacional 2026","16,6%"); nc4.metric("Variación vs 2025","−4,3 pp")
        st.markdown("El **Instituto Traumatológico SSMOCC** (62,2%) ocupa el **5° lugar nacional** entre establecimientos con mayor % TD.")


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA MIS REPORTES
# ═══════════════════════════════════════════════════════════════════════

def pg_todos_reportes():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    import pandas as pd
    page_header("Todos los reportes","Vista consolidada y gestión — solo administradores")
    reports=load_reports()
    c1,c2,c3=st.columns(3)
    fp=c1.selectbox("Período",["Todos"]+[p["id"] for p in PERIODOS],format_func=lambda x:"Todos" if x=="Todos" else next(p["label"]+" — "+p["periodo"] for p in PERIODOS if p["id"]==x))
    fn=c2.selectbox("Nivel",["Todos","Rojo","Amarillo","Verde"])
    fe=c3.selectbox("Estado",["Todos","Enviado","Borrador","Pendiente"])
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
    st.subheader("Detalle de reportes")
    filtered=reports
    if fp!="Todos": filtered=[r for r in filtered if r.get("reporte_id")==fp]
    if fn!="Todos": filtered=[r for r in filtered if r.get("nivel_riesgo","").lower()==fn.lower()]
    if fe!="Todos": filtered=[r for r in filtered if r.get("estado","").lower()==fe.lower()]
    if not filtered: st.info("No hay reportes con los filtros seleccionados."); return
    for r in sorted(filtered,key=lambda x:(x.get("reporte_id",""),x.get("nivel_riesgo",""))):
        estado=r.get("estado","borrador")
        icon="✅" if estado=="enviado" else "📝"
        with st.expander(f"{icon} {r.get('establecimiento_nombre','')[:45]} — {r.get('periodo_label','')} — {estado.upper()}"):
            ca,cb,cc,cd=st.columns(4)
            ca.metric("Nivel",r.get("nivel_riesgo","").capitalize()); cb.metric("% TD 2026",f"{r.get('pct_2026',0):.2f}%")
            cc.metric("% TD período",f"{r.get('pct_per',0):.2f}%"); cd.metric("N° procesos TD",r.get("n_proc","—"))
            if r.get("causas_sel"): st.markdown("**Causales:** "+", ".join(r["causas_sel"]))
            if r.get("causas_desc"): st.markdown(f"**Descripción:** {r['causas_desc']}")
            if r.get("compromisos"): st.markdown(f"**Compromisos:** {r['compromisos']}")
            st.markdown(f"**Responsable:** {r.get('resp_nombre','')} · {r.get('resp_cargo','')} · {r.get('resp_email','')}  \n**Meta próximo período:** {r.get('meta_prox',16):.1f}% · **Fecha:** {r.get('fecha_comp','')}  \n**Ingresado:** {r.get('usuario','')} · {r.get('fecha_ingreso','')[:16]}")
            col1,col2,_=st.columns([1,1,3])
            with col1:
                if estado=="borrador":
                    if st.button("✅ Marcar enviado",key=f"s_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"]="enviado"; upsert_report(r); st.rerun()
                else:
                    if st.button("↩️ A borrador",key=f"b_{r['establecimiento_id']}_{r['reporte_id']}"):
                        r["estado"]="borrador"; upsert_report(r); st.rerun()
            with col2:
                if st.button("🗑️ Eliminar",key=f"d_{r['establecimiento_id']}_{r['reporte_id']}",type="secondary"):
                    delete_report(r["establecimiento_id"],r["reporte_id"])
                    st.warning(f"Reporte eliminado."); st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA EXPORTAR
# ═══════════════════════════════════════════════════════════════════════
def pg_exportar():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    import pandas as pd
    page_header("Exportar reporte consolidado","Formato Anexo N°1 — Lineamiento MINSAL v1.0")
    reports=load_reports()
    ps=st.selectbox("Período",options=[p["id"] for p in PERIODOS],format_func=lambda x:next(f"{p['label']} — {p['periodo']} (plazo: {p['fecha_txt']})" for p in PERIODOS if p["id"]==x))
    pinfo=next(p for p in PERIODOS if p["id"]==ps)
    inc=st.radio("Incluir",["Solo enviados","Enviados y borradores"],horizontal=True)
    r_p=[r for r in reports if r.get("reporte_id")==ps]
    if inc=="Solo enviados": r_p=[r for r in r_p if r.get("estado")=="enviado"]
    if not r_p:
        st.warning(f"No hay reportes para {pinfo['label']} con los filtros seleccionados.")
        pend=[eid for eid,e in ESTABLECIMIENTOS.items() if e["nivel"] in ["rojo","amarillo"]]
        for eid in pend:
            e=ESTABLECIMIENTOS[eid]; r=next((x for x in reports if x.get("establecimiento_id")==eid and x.get("reporte_id")==ps),None)
            ic="✅" if r and r.get("estado")=="enviado" else "📝" if r else "⬜"
            st.markdown(f"{ic} {e['nombre']} — {e['nivel'].capitalize()}")
        return
    rows=[]
    for r in r_p:
        eid=r["establecimiento_id"]; estab_d=ESTABLECIMIENTOS.get(eid,{})
        med=r.get("medidas",{})
        med_labels={"pac":"Actualizacion Plan Anual Compras","lic":"Inicio procesos licitatorios","cm":"Migracion Convenio Marco","cenabast":"Gestion CENABAST","cap":"Capacitacion equipo Ley 21.634","venc":"Control vencimiento contratos"}
        med_txt="; ".join(lbl for k,lbl in med_labels.items() if med.get(k))
        if r.get("med_desc"): med_txt=(med_txt+" | " if med_txt else "")+r.get("med_desc","")
        causas_txt="; ".join(r.get("causas_sel",[]))
        if r.get("causas_desc"): causas_txt=(causas_txt+" | " if causas_txt else "")+r.get("causas_desc","")
        rows.append({
            "Servicio de salud":"Metropolitano Occidente",
            "Establecimiento":r.get("establecimiento_nombre",""),
            "Nivel de Riesgo":r.get("nivel_riesgo","").capitalize(),
            "Periodo informado":r.get("periodo",""),
            "Principales causas":causas_txt,
            "Medidas implementadas":med_txt,
            "Compromisos":r.get("compromisos",""),
            "Responsable":r.get("resp_nombre","")+" - "+r.get("resp_cargo",""),
            "Fecha comprometida":r.get("fecha_comp",""),
            "Codigo DEIS":estab_d.get("codigo_deis",""),
            "RUT":estab_d.get("rut",""),
            "Pct TD 2026":r.get("pct_2026",""),
            "Pct TD 2025":r.get("pct_2025",""),
            "Brecha pp":estab_d.get("brecha",""),
            "Variacion pp":estab_d.get("variacion",""),
            "Denominador CLP":estab_d.get("denominador",""),
            "Numerador CLP":estab_d.get("numerador",""),
            "Monto TD periodo CLP":r.get("monto_td",0),
            "N procesos TD":r.get("n_proc",0),
            "Correo responsable":r.get("resp_email",""),
            "Meta proximo periodo":r.get("meta_prox",""),
            "Observaciones":r.get("obs",""),
            "Estado reporte":r.get("estado","").upper(),
            "Fecha ingreso":r.get("fecha_ingreso","")[:16],
        })
    df=pd.DataFrame(rows)
    cols_minsal=["Servicio de salud","Establecimiento","Nivel de Riesgo","Periodo informado","Principales causas","Medidas implementadas","Compromisos","Responsable","Fecha comprometida"]
    st.markdown("**Vista previa Anexo N°1 MINSAL** (columnas exactas del lineamiento):")
    st.dataframe(df[cols_minsal],use_container_width=True,hide_index=True)
    st.markdown(f"**{len(rows)} establecimiento(s)** · Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        df[cols_minsal].to_excel(w,sheet_name="Anexo N1 MINSAL",index=False)
        df.to_excel(w,sheet_name="Datos completos",index=False)
        resumen=pd.DataFrame([{"Establecimiento":e["nombre"],"Nivel":e["nivel"].capitalize(),"Pct TD 2026":e["pct_2026"],"Pct TD 2025":e["pct_2025"],"Brecha pp":e["brecha"],"Variacion pp":e["variacion"],"Denominador":e["denominador"],"Numerador":e["numerador"],"Enviado":"Si" if any(r.get("establecimiento_id")==eid and r.get("estado")=="enviado" and r.get("reporte_id")==ps for r in reports) else "No"} for eid,e in ESTABLECIMIENTOS.items()])
        resumen.to_excel(w,sheet_name="Resumen SSMOCC",index=False)
    buf.seek(0)
    fecha=datetime.datetime.now().strftime("%Y%m%d_%H%M")
    c1,c2=st.columns(2)
    c1.download_button("⬇️ Descargar Excel (.xlsx)",buf,f"SSMOCC_AnexoN1_{ps}_{fecha}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,type="primary")
    c2.download_button("⬇️ Descargar CSV",df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),f"SSMOCC_AnexoN1_{ps}_{fecha}.csv","text/csv",use_container_width=True)
    pend=[eid for eid,e in ESTABLECIMIENTOS.items() if e["nivel"] in ["rojo","amarillo"] and not any(r.get("establecimiento_id")==eid and r.get("estado")=="enviado" and r.get("reporte_id")==ps for r in reports)]
    if pend:
        st.warning(f"⚠️ {len(pend)} establecimiento(s) sin enviar para {pinfo['label']}:")
        for eid in pend: e=ESTABLECIMIENTOS[eid]; st.markdown(f"- **{e['nombre']}** — {e['nivel'].capitalize()} ({e['pct_2026']:.1f}%)")


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA USUARIOS
# ═══════════════════════════════════════════════════════════════════════
def pg_usuarios():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    import pandas as pd
    page_header("Gestión de usuarios","Alta, baja y restablecimiento de contraseñas")
    users=load_users()
    tab1,tab2=st.tabs(["📋 Usuarios","➕ Crear/Editar"])
    with tab1:
        rows=[{"Usuario":uid,"Nombre":u["nombre"],"Rol":u["rol"].capitalize(),"Establecimiento":ESTABLECIMIENTOS.get(u.get("establecimiento"),{}).get("nombre_corto","— Admin —"),"Email":u.get("email",""),"Activo":"✅" if u.get("activo") else "❌"} for uid,u in users.items()]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        ca,cb=st.columns(2)
        uid_sel=ca.selectbox("Usuario",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}")
        act=users.get(uid_sel,{}).get("activo",True)
        if cb.button(f"{'🔴 Desactivar' if act else '🟢 Activar'}",use_container_width=True):
            users[uid_sel]["activo"]=not act; save_users(users); st.success("Actualizado."); st.rerun()
        with st.expander("🔑 Restablecer contraseña"):
            ur=st.selectbox("Usuario",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}",key="ur")
            np=st.text_input("Nueva contraseña",type="password",key="np")
            if st.button("Restablecer"):
                if len(np)<8: st.error("Mínimo 8 caracteres.")
                else: users[ur]["password_hash"]=_hash(np); save_users(users); st.success(f"Contraseña restablecida para '{ur}'.")
        with st.expander("📋 Credenciales por defecto"):
            st.markdown("""| Usuario | Contraseña | Referente |\n|---------|-----------|----------|\n| `admin` | `Admin2026*` | Administrador |\n| `bayron` | `Ssmoc2026*` | Bayron Retamal |\n| `san_juan` | `Sjd2026*` | Rodrigo Bravo |\n| `traumatologico` | `Trauma2026*` | Miguel Jara |\n| `felix_bulnes` | `Felix2026*` | Carolina Castro |\n| `talagante` | `Tala2026*` | M.A. Villegas |\n| `penaflor` | `Pen2026*` | Gissela Salvo |\n| `melipilla` | `Meli2026*` | M.A. Morales |\n| `curacavi` | `Cura2026*` | Pablo Yévenes |\n| `crs_allende` | `Crs2026*` | Eric Cubillo |""")
    with tab2:
        modo=st.radio("Modo",["Crear nuevo","Editar existente"],horizontal=True)
        uid_e=None; u_e={}
        if modo=="Editar existente":
            uid_e=st.selectbox("Usuario a editar",list(users.keys()),format_func=lambda x:f"{x} — {users[x]['nombre']}",key="ue"); u_e=users.get(uid_e,{})
        with st.form("fu"):
            c1,c2=st.columns(2)
            nuevo_uid=c1.text_input("Nombre de usuario") if modo=="Crear nuevo" else st.text_input("Usuario",value=uid_e,disabled=True)
            nombre=c1.text_input("Nombre completo",value=u_e.get("nombre",""))
            email=c1.text_input("Correo",value=u_e.get("email",""))
            rol=c2.selectbox("Rol",["establecimiento","admin"],index=0 if u_e.get("rol","establecimiento")=="establecimiento" else 1)
            estab_ops={"":"— Solo admin —"}; estab_ops.update({eid:e["nombre_corto"] for eid,e in ESTABLECIMIENTOS.items()})
            estab_sel=c2.selectbox("Establecimiento",list(estab_ops.keys()),format_func=lambda x:estab_ops[x],index=list(estab_ops.keys()).index(u_e.get("establecimiento","") or ""))
            pwd=c2.text_input("Contraseña"+" (vacío=no cambiar)" if modo=="Editar existente" else "",type="password")
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
                    save_users(users); st.success(f"✅ Usuario '{uid_f}' guardado."); st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════
def pg_configuracion():
    if st.session_state.user["rol"]!="admin": st.error("Solo administradores."); return
    import pandas as pd
    page_header("Configuración del sistema","Estado y mantenimiento de la plataforma")
    reports=load_reports()
    c1,c2=st.columns(2)
    with c1:
        st.subheader("Resumen del sistema")
        st.markdown(f"""| Parámetro | Valor |\n|-----------|-------|\n| Versión | 1.0.0 |\n| Lineamiento | MINSAL v1.0 · Jun 2026 |\n| Meta | ≤ 16% |\n| Establecimientos | {len(ESTABLECIMIENTOS)} |\n| Períodos | {len(PERIODOS)} |\n| Reportes totales | {len(reports)} |\n| Enviados | {len([r for r in reports if r.get("estado")=="enviado"])} |\n| Borradores | {len([r for r in reports if r.get("estado")=="borrador"])} |""")
    with c2:
        st.subheader("Avance por período")
        req=len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
        for p in PERIODOS:
            done=len([r for r in reports if r.get("reporte_id")==p["id"] and r.get("estado")=="enviado"])
            st.markdown(f"**{p['label']}** — {p['periodo']} · Plazo: `{p['fecha_txt']}`")
            st.progress(done/req if req else 0,text=f"{done}/{req} enviados")
    st.divider()
    st.subheader("Datos de referencia SSMOCC (CSV MINSAL)")
    df=pd.DataFrame([{"Establecimiento":e["nombre_corto"],"Nivel":e["nivel"].capitalize(),"% TD 2026":e["pct_2026"],"% TD 2025":e["pct_2025"],"Brecha (pp)":e["brecha"],"Var. (pp)":e["variacion"],"Denominador":e["denominador"],"Numerador":e["numerador"]} for e in ESTABLECIMIENTOS.values()])
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.divider()
    with st.expander("🗑️ Mantenimiento"):
        st.warning("⚠️ Acción irreversible.")
        if st.button("Eliminar TODOS los reportes"):
            save_reports([]); st.success("Reportes eliminados."); st.rerun()


def pg_mis_reportes():
    user = st.session_state.user
    page_header("Ingreso de antecedentes — Anexo N°1",
                "Lineamiento MINSAL v1.0 · Jun 2026 · Subsecretaría de Redes Asistenciales")

    if user["rol"] == "admin":
        opciones = {eid: e["nombre_corto"] for eid, e in ESTABLECIMIENTOS.items() if e["nivel"] in ["rojo","amarillo"]}
        eid_sel = st.selectbox("Establecimiento", options=list(opciones.keys()), format_func=lambda x: opciones[x])
    else:
        eid_sel = user.get("establecimiento")
        if not eid_sel: st.error("Sin establecimiento asignado."); return
        if ESTABLECIMIENTOS.get(eid_sel,{}).get("nivel") == "verde":
            est_v = ESTABLECIMIENTOS[eid_sel]
            st.markdown(f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-left:5px solid #22C55E;
                        border-radius:8px;padding:24px;text-align:center;margin-top:20px">
                <div style="font-size:42px">✅</div>
                <div style="font-size:17px;font-weight:700;color:#166534;margin-top:8px">Nivel Verde — {est_v['nombre']}</div>
                <div style="font-size:12px;color:#16a34a;margin-top:8px;line-height:1.6">
                    No se requiere remitir antecedentes al MINSAL.<br>
                    El SSMOCC mantendrá el seguimiento interno.
                </div>
            </div>""", unsafe_allow_html=True)
            return

    estab = ESTABLECIMIENTOS.get(eid_sel, {})
    nivel = estab.get("nivel","verde")
    nc = {"rojo":"#E24B4A","amarillo":"#F59E0B","verde":"#22C55E"}[nivel]
    nt = {"rojo":"#991B1B","amarillo":"#92400E","verde":"#166534"}[nivel]
    nb = {"rojo":"#FEF2F2","amarillo":"#FFFBEB","verde":"#F0FDF4"}[nivel]
    nivel_icon = {"rojo":"🔴","amarillo":"🟡","verde":"🟢"}[nivel]
    brecha_s = ("+" if estab.get("brecha",0)>0 else "") + f'{estab.get("brecha",0):.2f} pp'

    st.markdown(f"""
    <div style="background:#1F3864;border-radius:12px 12px 0 0;padding:16px 22px;
                display:flex;justify-content:space-between;align-items:center">
        <div>
            <div style="font-size:16px;font-weight:700;color:white">{estab.get("nombre","")}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:3px">
                RUT: {estab.get("rut","")} &nbsp;·&nbsp; DEIS: {estab.get("codigo_deis","")}
            </div>
        </div>
        <div style="background:{nb};color:{nt};border-radius:8px;padding:6px 16px;font-size:13px;font-weight:700">
            {nivel_icon} {nivel.upper()}
        </div>
    </div>
    <div style="background:{nb};border:1px solid {nc};border-top:none;border-radius:0 0 12px 12px;
                padding:10px 22px;margin-bottom:20px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
        <div style="text-align:center">
            <div style="font-size:10px;color:{nt};text-transform:uppercase">% TD 2026</div>
            <div style="font-size:22px;font-weight:800;color:{nt}">{estab.get("pct_2026",0):.2f}%</div>
        </div>
        <div style="text-align:center">
            <div style="font-size:10px;color:{nt};text-transform:uppercase">% TD 2025</div>
            <div style="font-size:22px;font-weight:700;color:{nt}">{estab.get("pct_2025",0):.2f}%</div>
        </div>
        <div style="text-align:center">
            <div style="font-size:10px;color:{nt};text-transform:uppercase">Brecha vs meta</div>
            <div style="font-size:22px;font-weight:700;color:{nt}">{brecha_s}</div>
        </div>
        <div style="text-align:center">
            <div style="font-size:10px;color:{nt};text-transform:uppercase">Meta 2026</div>
            <div style="font-size:22px;font-weight:700;color:{nt}">16%</div>
        </div>
    </div>""", unsafe_allow_html=True)

    reports_all = load_reports()
    if f"per_{eid_sel}" not in st.session_state:
        st.session_state[f"per_{eid_sel}"] = "R1"

    st.markdown('<div style="font-size:13px;font-weight:600;color:#1F3864;margin-bottom:8px">Seleccionar período</div>', unsafe_allow_html=True)
    cols_per = st.columns(4)
    for i, p in enumerate(PERIODOS):
        r_ex = next((x for x in reports_all if x.get("establecimiento_id")==eid_sel and x.get("reporte_id")==p["id"]), None)
        est_ex = r_ex.get("estado","pendiente") if r_ex else "pendiente"
        icon_p = {"enviado":"✅","borrador":"📝","pendiente":"⬜"}[est_ex]
        sel = st.session_state[f"per_{eid_sel}"] == p["id"]
        border = "3px solid #1F3864" if sel else "1px solid #e2e8f0"
        bg_p = {"enviado":"#F0FDF4","borrador":"#EFF6FF","pendiente":"white"}[est_ex]
        tc_p = {"enviado":"#166534","borrador":"#1E40AF","pendiente":"#64748b"}[est_ex]
        with cols_per[i]:
            st.markdown(f"""
            <div style="background:{bg_p};border:{border};border-radius:10px;padding:12px 8px;text-align:center">
                <div style="font-size:24px">{icon_p}</div>
                <div style="font-size:12px;font-weight:700;color:#1F3864;margin-top:4px">{p["label"]}</div>
                <div style="font-size:10px;color:#64748b">{p["periodo"]}</div>
                <div style="font-size:10px;color:#94a3b8">Plazo: {p["fecha_txt"]}</div>
                <div style="font-size:10px;font-weight:600;color:{tc_p};margin-top:4px">{est_ex.upper()}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Selec. {p['label']}", key=f"selp_{p['id']}_{eid_sel}", use_container_width=True):
                st.session_state[f"per_{eid_sel}"] = p["id"]; st.rerun()

    periodo_id = st.session_state[f"per_{eid_sel}"]
    pinfo = next(p for p in PERIODOS if p["id"] == periodo_id)
    existing = next((r for r in reports_all if r.get("establecimiento_id")==eid_sel and r.get("reporte_id")==periodo_id), None)

    st.markdown("<br>", unsafe_allow_html=True)
    if existing:
        ec = "#166534" if existing.get("estado")=="enviado" else "#1E40AF"
        eb = "#F0FDF4" if existing.get("estado")=="enviado" else "#EFF6FF"
        ei = "✅" if existing.get("estado")=="enviado" else "📝"
        st.markdown(f"""
        <div style="background:{eb};border-radius:8px;padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;gap:10px">
            <span style="font-size:22px">{ei}</span>
            <div>
                <div style="font-size:13px;font-weight:700;color:{ec}">{pinfo["label"]} — {existing.get("estado","borrador").upper()}</div>
                <div style="font-size:11px;color:{ec}">Ingresado por {existing.get("usuario","")} · {existing.get("fecha_ingreso","")[:16]} · Puedes editarlo.</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f'''
    <div style="background:#1F3864;border-radius:8px 8px 0 0;padding:12px 20px">
        <div style="font-size:14px;font-weight:700;color:white">📋 {pinfo["label"]} — {pinfo["periodo"]}</div>
        <div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:2px">Plazo: {pinfo["fecha_txt"]}</div>
    </div>''', unsafe_allow_html=True)

    with st.form(f"frm_{eid_sel}_{periodo_id}", clear_on_submit=False):

        st.markdown('''<div style="background:#EFF6FF;border-left:4px solid #1F3864;border-radius:0 6px 6px 0;padding:10px 16px;margin:12px 0 10px">
            <div style="font-size:13px;font-weight:700;color:#1F3864">1 · Principales causas del resultado observado</div>
            <div style="font-size:11px;color:#3B82F6;margin-top:2px">Seleccione todas las causales aplicables y describa el contexto</div>
        </div>''', unsafe_allow_html=True)

        _dc = [c for c in (existing.get("causas_sel",[]) if existing else []) if c in CAUSALES]
        causas_sel = st.multiselect("Causales de Trato Directo *", CAUSALES, default=_dc)
        causas_desc = st.text_area("Descripción detallada *", value=existing.get("causas_desc","") if existing else "", height=110,
                                   placeholder="Describa las causas específicas del período...")

        st.markdown('<div style="font-size:12px;font-weight:600;color:#374151;margin:10px 0 4px">Datos cuantitativos</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        monto_td = c1.number_input("💰 Monto TD ($CLP)", min_value=0, step=1_000_000, value=int(existing.get("monto_td",0)) if existing else 0, format="%d")
        n_proc   = c2.number_input("📦 N° procesos TD", min_value=0, step=1, value=int(existing.get("n_proc",0)) if existing else 0)
        pct_per  = c3.number_input("📊 % TD período MINSAL", min_value=0.0, max_value=100.0, step=0.01,
                                   value=float(existing.get("pct_per",estab.get("pct_2026",0.0))) if existing else float(estab.get("pct_2026",0.0)), format="%.2f")

        st.markdown('''<div style="background:#F0FDF4;border-left:4px solid #22C55E;border-radius:0 6px 6px 0;padding:10px 16px;margin:16px 0 10px">
            <div style="font-size:13px;font-weight:700;color:#166534">2 · Medidas implementadas</div>
            <div style="font-size:11px;color:#16A34A;margin-top:2px">Acciones ejecutadas para reducir el uso del Trato Directo</div>
        </div>''', unsafe_allow_html=True)

        med_labels = {"pac":("📅","Actualización Plan Anual de Compras"),"lic":("📄","Inicio procesos licitatorios"),
                      "cm":("🛒","Migración a Convenio Marco"),"cenabast":("🏥","Gestión CENABAST"),
                      "cap":("📚","Capacitación equipo Ley 21.634"),"venc":("⏰","Control vencimiento contratos")}
        ex_med = existing.get("medidas",{}) if existing else {}
        med_sel = {}
        cols_m = st.columns(3)
        for i,(k,(icon_m,lbl)) in enumerate(med_labels.items()):
            med_sel[k] = cols_m[i%3].checkbox(f"{icon_m} {lbl}", value=ex_med.get(k,False), key=f"m_{k}")
        med_desc = st.text_area("Descripción adicional de medidas", value=existing.get("med_desc","") if existing else "", height=80,
                                placeholder="Describa el resultado de las acciones y el impacto observado...")

        st.markdown('''<div style="background:#FFF7ED;border-left:4px solid #F59E0B;border-radius:0 6px 6px 0;padding:10px 16px;margin:16px 0 10px">
            <div style="font-size:13px;font-weight:700;color:#92400E">3 · Compromisos para el próximo período</div>
            <div style="font-size:11px;color:#D97706;margin-top:2px">Acciones concretas con plazos verificables</div>
        </div>''', unsafe_allow_html=True)

        compromisos = st.text_area("Compromisos adoptados *", value=existing.get("compromisos","") if existing else "", height=110,
                                   placeholder="1. Iniciar licitación para [insumo] antes del [fecha]")
        c4,c5 = st.columns(2)
        meta_prox  = c4.number_input("🎯 Meta % TD próximo período", min_value=0.0, max_value=100.0, step=0.5,
                                     value=float(existing.get("meta_prox",16.0)) if existing else 16.0, format="%.1f")
        fecha_comp = c5.date_input("📆 Fecha comprometida",
                                   value=datetime.date.fromisoformat(existing["fecha_comp"])
                                   if existing and existing.get("fecha_comp") else datetime.date(2026,8,31))

        st.markdown('''<div style="background:#F8FAFC;border-left:4px solid #64748B;border-radius:0 6px 6px 0;padding:10px 16px;margin:16px 0 10px">
            <div style="font-size:13px;font-weight:700;color:#374151">4 · Responsable del reporte</div>
        </div>''', unsafe_allow_html=True)

        c6,c7,c8 = st.columns(3)
        resp_nombre = c6.text_input("👤 Nombre completo", value=existing.get("resp_nombre",user["nombre"]) if existing else user["nombre"])
        resp_cargo  = c7.text_input("💼 Cargo", value=existing.get("resp_cargo","Jefe/a de Abastecimiento") if existing else "Jefe/a de Abastecimiento")
        resp_email  = c8.text_input("📧 Correo", value=existing.get("resp_email",user.get("email","")) if existing else user.get("email",""))
        obs = st.text_area("💬 Observaciones (opcional)", value=existing.get("obs","") if existing else "", height=60)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('''<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:11px;color:#64748b">
            <strong>* Obligatorios para enviar.</strong> Puedes guardar como borrador y completar después.
        </div>''', unsafe_allow_html=True)

        cg,ce,_ = st.columns([1,1,2])
        guardar = cg.form_submit_button("💾  Guardar borrador", use_container_width=True)
        enviar  = ce.form_submit_button("📤  Enviar a SSMOCC",  use_container_width=True, type="primary")

        if guardar or enviar:
            ok = True
            if enviar:
                errs = []
                if not causas_sel:          errs.append("⚠️ Seleccione al menos una causal.")
                if not causas_desc.strip(): errs.append("⚠️ Complete la descripción de causas.")
                if not compromisos.strip(): errs.append("⚠️ Complete los compromisos.")
                if not resp_nombre.strip(): errs.append("⚠️ Ingrese el nombre del responsable.")
                if errs:
                    for e in errs: st.error(e)
                    ok = False
            if ok:
                data = {"establecimiento_id":eid_sel,"establecimiento_nombre":estab["nombre"],"reporte_id":periodo_id,"periodo":pinfo["periodo"],"periodo_label":pinfo["label"],"nivel_riesgo":nivel,"pct_2026":estab.get("pct_2026"),"pct_2025":estab.get("pct_2025"),"pct_per":pct_per,"monto_td":monto_td,"n_proc":n_proc,"causas_sel":causas_sel,"causas_desc":causas_desc,"medidas":med_sel,"med_desc":med_desc,"compromisos":compromisos,"meta_prox":meta_prox,"fecha_comp":str(fecha_comp),"resp_nombre":resp_nombre,"resp_cargo":resp_cargo,"resp_email":resp_email,"obs":obs,"estado":"enviado" if enviar else "borrador","usuario":user["username"],"fecha_ingreso":str(datetime.datetime.now().isoformat())}
                upsert_report(data)
                if enviar: st.success(f"✅ **Reporte {pinfo['label']}** enviado exitosamente."); st.balloons()
                else: st.info("💾 Borrador guardado correctamente.")
                st.rerun()


def pg_actualizar_datos():
    """Página para actualizar datos MINSAL desde CSV mensual."""
    if st.session_state.user["rol"] != "admin":
        st.error("Solo administradores."); return

    page_header("Actualización de datos MINSAL",
                "Sube el CSV mensual de ChileCompra · Lineamiento 3.1 — Monitoreo Mensual")

    # Estado actual
    st.markdown('''<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-left:4px solid #1F3864;
                border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:16px">
        <div style="font-size:13px;font-weight:700;color:#1F3864;margin-bottom:6px">
            📋 Proceso de actualización — Lineamiento MINSAL v1.0 · Art. 3.1
        </div>
        <div style="font-size:12px;color:#1E40AF;line-height:1.7">
            La Subsecretaría de Redes Asistenciales envía mensualmente un Dashboard con datos de ChileCompra.<br>
            Cuando recibas el nuevo CSV, súbelo aquí para actualizar los indicadores de todos los establecimientos.<br>
            <strong>Los reportes ya ingresados por los establecimientos NO se pierden.</strong>
        </div>
    </div>''', unsafe_allow_html=True)

    # Datos actuales
    st.subheader("Estado actual de los datos")
    import pandas as pd
    rows_act = []
    for eid, e in ESTABLECIMIENTOS.items():
        ult = e.get("ultima_actualizacion", "Datos originales Jun 2026")
        rows_act.append({
            "Establecimiento": e["nombre_corto"],
            "Nivel": e["nivel"].capitalize(),
            "% TD 2026": f"{e['pct_2026']:.2f}%",
            "% TD 2025": f"{e['pct_2025']:.2f}%",
            "Brecha": f"{e['brecha']:+.2f} pp",
            "Denominador ($)": f"${e['denominador']:,.0f}",
            "Numerador ($)": f"${e['numerador']:,.0f}",
            "Última actualización": ult,
        })
    st.dataframe(pd.DataFrame(rows_act), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Subir CSV
    st.subheader("📤 Subir nuevo CSV MINSAL")
    st.markdown('''<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:12px 14px;margin-bottom:12px;font-size:12px;color:#92400E">
        <strong>Formato esperado:</strong> CSV con separador <code>;</code> y columnas:
        <code>Codigo DEIS · RUT · Establecimiento · Servicio de Salud · Denominador · Numerador ·
        % Trato Directo 2026 · % Trato Directo periodo equivalente 2025 · Brecha vs meta ·
        Variacion vs 2025 · Nivel de riesgo</code><br>
        Exactamente el mismo formato que envía el MINSAL mensualmente.
    </div>''', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Seleccionar archivo CSV del MINSAL",
        type=["csv"],
        help="Archivo CSV enviado por la Subsecretaría de Redes Asistenciales con datos de ChileCompra"
    )

    if uploaded:
        try:
            file_bytes = uploaded.read()
            updates, errors, rows_found = parse_csv_minsal(file_bytes)

            st.markdown(f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:12px 14px;margin-bottom:12px">
                <div style="font-size:13px;font-weight:700;color:#166534">✅ Archivo leído correctamente</div>
                <div style="font-size:12px;color:#16a34a;margin-top:4px">
                    {rows_found} establecimiento(s) reconocidos en el CSV
                    {f" · {len(errors)} advertencia(s)" if errors else ""}
                </div>
            </div>""", unsafe_allow_html=True)

            if errors:
                with st.expander(f"⚠️ {len(errors)} advertencia(s)"):
                    for e in errors: st.warning(e)

            if updates:
                # Preview
                st.markdown("**Vista previa de los cambios:**")
                preview_rows = []
                for eid, vals in updates.items():
                    e_old = ESTABLECIMIENTOS.get(eid, {})
                    cambio_nivel = "⚠️ CAMBIA" if vals["nivel"] != e_old.get("nivel","") else "—"
                    cambio_pct = f"{vals['pct_2026']:.2f}% (era {e_old.get('pct_2026',0):.2f}%)"
                    preview_rows.append({
                        "Establecimiento": e_old.get("nombre_corto", eid),
                        "% TD nuevo": f"{vals['pct_2026']:.2f}%",
                        "% TD anterior": f"{e_old.get('pct_2026',0):.2f}%",
                        "Variación": f"{vals['pct_2026']-e_old.get('pct_2026',0):+.2f} pp",
                        "Nivel nuevo": vals["nivel"].capitalize(),
                        "Nivel anterior": e_old.get("nivel","").capitalize(),
                        "Cambio nivel": cambio_nivel,
                    })
                st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("✅ Confirmar y guardar", type="primary", use_container_width=True):
                        save_datos_minsal(updates)
                        # Apply to in-memory ESTABLECIMIENTOS
                        for eid, vals in updates.items():
                            if eid in ESTABLECIMIENTOS:
                                ESTABLECIMIENTOS[eid].update(vals)
                        st.success(f"✅ Datos MINSAL actualizados correctamente para {len(updates)} establecimiento(s).")
                        st.info("Los indicadores del dashboard y los formularios de reporte ahora reflejan los nuevos datos.")
                        st.rerun()
                with col2:
                    st.markdown('<div style="padding:8px 0;font-size:12px;color:#64748b">Los reportes ya enviados por los establecimientos NO se modifican. Solo se actualizan los datos de referencia MINSAL.</div>', unsafe_allow_html=True)
            else:
                st.error("No se reconoció ningún establecimiento SSMOCC en el CSV. Verifica el formato y los códigos DEIS.")

        except Exception as ex:
            st.error(f"Error al leer el archivo: {ex}")
            st.markdown("Verifica que el archivo sea un CSV con separador `;` y el formato correcto del MINSAL.")

    st.markdown("---")

    # Historial
    if DATOS_FILE.exists():
        with st.expander("🔄 Restaurar datos originales (Jun 2026)"):
            st.warning("Esto elimina los datos actualizados y vuelve a los datos del CSV original de junio 2026.")
            if st.button("🗑️ Restaurar datos originales", type="secondary"):
                DATOS_FILE.unlink()
                st.success("Datos restaurados. Recarga la página para ver los cambios.")
                st.rerun()

    st.markdown('''<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px;margin-top:16px;font-size:11px;color:#64748b">
        <strong>Lineamiento MINSAL v1.0 · Art. 3.1:</strong> La Subsecretaría de Redes Asistenciales realizará mensualmente la
        consolidación de información de ChileCompra, el cálculo del % TD, la clasificación de riesgo y la elaboración del
        Dashboard de seguimiento. La emisión de reportes estará sujeta a la disponibilidad de ChileCompra.
    </div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════════════
if st.session_state.user is None:
    page_login()
else:
    render_topbar()
    pg = st.session_state.page
    if   pg == "dashboard":      pg_dashboard()
    elif pg == "mis_reportes":   pg_mis_reportes()
    elif pg == "todos_reportes": pg_todos_reportes()
    elif pg == "exportar":       pg_exportar()
    elif pg == "usuarios":       pg_usuarios()
    elif pg == "configuracion":   pg_configuracion()
    elif pg == "actualizar_datos": pg_actualizar_datos()
    else:                         pg_dashboard()
