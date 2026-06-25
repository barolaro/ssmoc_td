"""
app.py — Plataforma Monitor Trato Directo SSMOC
"""
import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Monitor TD — SSMOC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Logo en base64 ────────────────────────────────────────────────────
def get_logo_b64():
    logo_path = Path(__file__).parent / "logo_ssmocc.jpg"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_B64 = get_logo_b64()

# ── CSS global ────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Ocultar menú hamburguesa y footer de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Layout general */
.block-container {padding-top: 0rem !important; padding-bottom: 2rem;}

/* Sidebar azul institucional */
[data-testid="stSidebar"] {background: #0A3964 !important; min-width: 240px;}
[data-testid="stSidebar"] > div {background: #0A3964 !important;}
[data-testid="stSidebar"] * {color: rgba(255,255,255,0.85) !important;}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 6px !important;
    text-align: left !important;
    padding: 8px 14px !important;
    margin-bottom: 2px !important;
    width: 100% !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.16) !important;
    border-color: rgba(255,255,255,0.35) !important;
}

/* Separador sidebar */
[data-testid="stSidebar"] hr {border-color: rgba(255,255,255,0.12) !important;}

/* Cards métricas */
.metric-card {
    background: white;
    border: 0.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 18px;
}
.metric-label {font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing:.06em; margin-bottom:5px;}
.metric-value {font-size: 26px; font-weight: 700; line-height: 1;}
.metric-note  {font-size: 11px; color: #94a3b8; margin-top:4px;}

/* Niveles */
.nivel-rojo    {background:#FEF2F2;color:#991B1B;padding:3px 10px;border-radius:5px;font-weight:700;font-size:12px;border:1px solid #FECACA;}
.nivel-amarillo{background:#FFFBEB;color:#92400E;padding:3px 10px;border-radius:5px;font-weight:700;font-size:12px;border:1px solid #FDE68A;}
.nivel-verde   {background:#F0FDF4;color:#166534;padding:3px 10px;border-radius:5px;font-weight:700;font-size:12px;border:1px solid #BBF7D0;}

/* Header institucional */
.inst-header {
    background: linear-gradient(135deg, #1F3864 0%, #0A3964 100%);
    padding: 16px 24px;
    border-radius: 10px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.inst-stripe {width: 5px; background: #C0392B; border-radius: 3px; align-self: stretch;}

/* Login card */
.login-wrap {max-width:400px; margin: 40px auto;}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# ── Login ─────────────────────────────────────────────────────────────
def page_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Logo
        if LOGO_B64:
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:20px">
                <img src="data:image/jpeg;base64,{LOGO_B64}" style="width:160px;border-radius:8px">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center;font-size:50px;margin-bottom:16px'>🏥</div>",
                        unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center;margin-bottom:24px">
            <div style="font-size:20px;font-weight:700;color:#1F3864">Monitor Trato Directo</div>
            <div style="font-size:13px;color:#64748b;margin-top:4px">Servicio de Salud Metropolitano Occidente</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px">Lineamiento MINSAL v1.0 · Junio 2026</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            col_a, col_b = st.columns([1,1])
            with col_a:
                submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

            if submitted:
                from auth import authenticate
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        st.markdown("""
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:12px 14px;margin-top:16px;font-size:12px;color:#1E40AF">
            <strong>Acceso restringido</strong> — Sistema exclusivo para referentes de abastecimiento de la red SSMOC.
            Para credenciales contacte a la Subdirección RFF.
        </div>
        """, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────
def render_sidebar():
    user = st.session_state.user
    from auth import ESTABLECIMIENTOS, load_reports

    with st.sidebar:
        # Logo
        if LOGO_B64:
            st.markdown(f"""
            <div style="text-align:center;padding:16px 8px 10px">
                <img src="data:image/jpeg;base64,{LOGO_B64}"
                     style="width:130px;border-radius:6px">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:16px 8px 10px">
                <div style="font-size:36px">🏥</div>
                <div style="font-size:13px;font-weight:700;color:white">Monitor TD</div>
                <div style="font-size:11px;color:rgba(255,255,255,.5)">SSMOC · 2026</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # Info usuario
        estab = ESTABLECIMIENTOS.get(user.get("establecimiento"), {})
        rol_label = "🔑 Administrador" if user["rol"] == "admin" else f"🏥 {estab.get('nombre_corto','')}"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);
                    border-radius:8px;padding:10px 12px;margin-bottom:14px">
            <div style="font-size:11px;color:rgba(255,255,255,.45);margin-bottom:3px">Sesión activa</div>
            <div style="font-size:13px;font-weight:600;color:white">{user['nombre']}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.55);margin-top:2px">{rol_label}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navegación
        st.markdown('<div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:6px;padding-left:2px">Navegación</div>', unsafe_allow_html=True)

        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("📋", "Mis reportes", "mis_reportes"),
        ]
        if user["rol"] == "admin":
            nav_items += [
                ("📁", "Todos los reportes", "todos_reportes"),
                ("📤", "Exportar MINSAL", "exportar"),
                ("👥", "Usuarios", "usuarios"),
                ("⚙️", "Configuración", "configuracion"),
            ]

        for icon, label, pid in nav_items:
            active = st.session_state.page == pid
            btn_style = "border-left: 3px solid #C0392B !important;" if active else ""
            if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True):
                st.session_state.page = pid
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # Avance reportes
        reports = load_reports()
        total_req = len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
        done_r1 = len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])
        pct = int(done_r1/total_req*100) if total_req else 0
        color = "#4ade80" if done_r1 == total_req else "#fbbf24" if done_r1 > 0 else "#f87171"

        st.markdown(f"""
        <div style="background:rgba(255,255,255,.06);border-radius:8px;padding:10px 12px;margin-bottom:12px">
            <div style="font-size:10px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">
                1° Reporte · Plazo 31 Jul
            </div>
            <div style="font-size:18px;font-weight:700;color:{color}">{done_r1}/{total_req} enviados</div>
            <div style="background:rgba(255,255,255,.12);border-radius:4px;height:4px;margin-top:8px">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪  Cerrar sesión", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown("""
        <div style="text-align:center;padding:8px 0;font-size:10px;color:rgba(255,255,255,.25)">
            Monitor TD SSMOC v1.0<br>Lineamiento MINSAL Jun 2026
        </div>
        """, unsafe_allow_html=True)


# ── Header institucional ──────────────────────────────────────────────
def inst_header(title, subtitle=""):
    logo_html = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="height:44px;border-radius:4px">' if LOGO_B64 else '<span style="font-size:32px">🏥</span>'
    st.markdown(f"""
    <div style="background:#1F3864;padding:14px 22px;border-radius:10px;
                margin-bottom:20px;display:flex;align-items:center;gap:14px">
        {logo_html}
        <div style="width:4px;background:#C0392B;border-radius:2px;align-self:stretch"></div>
        <div>
            <div style="font-size:17px;font-weight:600;color:white">{title}</div>
            <div style="font-size:11px;color:rgba(255,255,255,.55);margin-top:2px">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Hacer disponible globalmente
st.session_state["inst_header"] = inst_header
st.session_state["logo_b64"] = LOGO_B64

# ── Routing ───────────────────────────────────────────────────────────
if st.session_state.user is None:
    page_login()
else:
    render_sidebar()
    page = st.session_state.page

    if page == "dashboard":
        from views import dashboard as p; p.show(inst_header, LOGO_B64)
    elif page == "mis_reportes":
        from views import mis_reportes as p; p.show(inst_header)
    elif page == "todos_reportes":
        from views import todos_reportes as p; p.show(inst_header)
    elif page == "exportar":
        from views import exportar as p; p.show(inst_header)
    elif page == "usuarios":
        from views import usuarios as p; p.show(inst_header)
    elif page == "configuracion":
        from views import configuracion as p; p.show(inst_header)
    else:
        from views import dashboard as p; p.show(inst_header, LOGO_B64)
