"""
app.py  —  Plataforma de Monitoreo Trato Directo SSMOC
Punto de entrada principal con pantalla de login.
"""
import streamlit as st
from auth import authenticate, ESTABLECIMIENTOS, COLORES_NIVEL, PERIODOS_REPORTE

st.set_page_config(
    page_title="Monitor TD — SSMOC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS INSTITUCIONAL ────────────────────────────────────────────────────
st.markdown("""
<style>
/* Colores institucionales */
:root {
    --azul: #1F3864;
    --azul2: #2E5F8A;
    --rojo: #C0392B;
    --verde: #27500A;
    --bg: #F4F6F9;
}

/* Header de la app */
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0A3964 !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.16) !important;
}

/* Niveles */
.nivel-rojo    { background:#FCEBEB;color:#A32D2D;padding:3px 10px;border-radius:4px;font-weight:600;font-size:13px }
.nivel-amarillo{ background:#FAEEDA;color:#633806;padding:3px 10px;border-radius:4px;font-weight:600;font-size:13px }
.nivel-verde   { background:#EAF3DE;color:#27500A;padding:3px 10px;border-radius:4px;font-weight:600;font-size:13px }

/* Metric cards custom */
.metric-card {
    background: white;
    border: 0.5px solid #dee2e6;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.metric-label { font-size: 11px; color: #6c757d; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 600; color: #1F3864; line-height: 1; }
.metric-note  { font-size: 11px; color: #6c757d; margin-top: 3px; }

/* Alert boxes */
.alert-rojo    { background:#FCEBEB;border-left:4px solid #E24B4A;padding:12px 14px;border-radius:0 6px 6px 0;margin-bottom:8px }
.alert-amarillo{ background:#FAEEDA;border-left:4px solid #BA7517;padding:12px 14px;border-radius:0 6px 6px 0;margin-bottom:8px }
.alert-verde   { background:#EAF3DE;border-left:4px solid #3B6D11;padding:12px 14px;border-radius:0 6px 6px 0;margin-bottom:8px }
.alert-info    { background:#E6F1FB;border-left:4px solid #185FA5;padding:12px 14px;border-radius:0 6px 6px 0;margin-bottom:8px }

/* Login card */
.login-card {
    max-width: 420px;
    margin: 60px auto 0;
    background: white;
    border-radius: 12px;
    border: 0.5px solid #dee2e6;
    padding: 36px 40px;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ─── SIDEBAR ─────────────────────────────────────────────────────────────
def render_sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:12px 0 16px">
            <div style="font-size:28px;color:white">🏥</div>
            <div style="font-size:14px;font-weight:600;color:white;margin-top:4px">Monitor TD</div>
            <div style="font-size:11px;color:rgba(255,255,255,.55)">SSMOC · 2026</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if user:
            st.markdown(f"""
            <div style="padding:10px 8px;background:rgba(255,255,255,.08);border-radius:6px;margin-bottom:12px">
                <div style="font-size:12px;color:rgba(255,255,255,.5);margin-bottom:2px">Usuario activo</div>
                <div style="font-size:13px;font-weight:600">{user["nombre"]}</div>
                <div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:2px">
                    {"🔑 Administrador" if user["rol"]=="admin" else "🏥 " + (ESTABLECIMIENTOS.get(user.get("establecimiento"),{}).get("nombre_corto",""))}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Navegación**")

            # Páginas comunes
            pages_all = [
                ("📊", "Dashboard",   "dashboard"),
                ("📋", "Mis reportes","mis_reportes"),
            ]
            # Solo admin
            pages_admin = [
                ("📁", "Todos los reportes", "todos_reportes"),
                ("📤", "Exportar MINSAL",     "exportar"),
                ("👥", "Gestión usuarios",    "usuarios"),
                ("⚙️", "Configuración",       "configuracion"),
            ]

            for icon, label, page_id in pages_all:
                active = "→ " if st.session_state.page == page_id else "   "
                if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True):
                    st.session_state.page = page_id
                    st.rerun()

            if user["rol"] == "admin":
                st.markdown("---")
                st.markdown("**Administración**")
                for icon, label, page_id in pages_admin:
                    if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True):
                        st.session_state.page = page_id
                        st.rerun()

            st.divider()
            if st.button("🚪 Cerrar sesión", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = "login"
                st.rerun()

            # Estado reportes en sidebar
            from auth import load_reports
            reports = load_reports()
            total_req = len([e for e in ESTABLECIMIENTOS.values() if e["nivel"] in ["rojo","amarillo"]])
            done_r1   = len([r for r in reports if r.get("reporte_id")=="R1" and r.get("estado")=="enviado"])
            st.markdown(f"""
            <div style="margin-top:12px;padding:10px 8px;background:rgba(255,255,255,.06);border-radius:6px">
                <div style="font-size:11px;color:rgba(255,255,255,.5);margin-bottom:6px">Avance 1° Reporte (31 Jul)</div>
                <div style="font-size:16px;font-weight:600;color:{'#86efac' if done_r1==total_req else '#fca5a5'}">{done_r1}/{total_req} enviados</div>
                <div style="background:rgba(255,255,255,.12);border-radius:3px;height:5px;margin-top:6px">
                    <div style="width:{int(done_r1/total_req*100) if total_req else 0}%;height:100%;background:#86efac;border-radius:3px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── LOGIN PAGE ───────────────────────────────────────────────────────────
def page_login():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:28px">
            <div style="font-size:48px">🏥</div>
            <div style="font-size:22px;font-weight:700;color:#1F3864;margin-top:8px">Monitor Trato Directo</div>
            <div style="font-size:14px;color:#6c757d;margin-top:4px">Servicio de Salud Metropolitano Occidente</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px">Subsecretaría de Redes Asistenciales · MINSAL</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            submitted = st.form_submit_button("Iniciar sesión", use_container_width=True, type="primary")

            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

        st.markdown("""
        <div style="margin-top:20px;padding:12px;background:#E6F1FB;border-radius:8px;font-size:12px;color:#0C447C">
            <strong>Credenciales de acceso:</strong> Utilice las credenciales asignadas por la Subdirección de 
            Recursos Físicos y Financieros del SSMOC. Para restablecer su contraseña, contacte al administrador.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center;margin-top:16px;font-size:11px;color:#9ca3af">
            Lineamiento MINSAL v1.0 · Junio 2026<br>
            Área de Compras Estratégicas y Procesos Logísticos
        </div>
        """, unsafe_allow_html=True)


# ─── ROUTING ─────────────────────────────────────────────────────────────
if st.session_state.user is None:
    page_login()
else:
    render_sidebar()
    page = st.session_state.page

    if page == "dashboard":
        import pages.dashboard as p; p.show()
    elif page == "mis_reportes":
        import pages.mis_reportes as p; p.show()
    elif page == "todos_reportes":
        import pages.todos_reportes as p; p.show()
    elif page == "exportar":
        import pages.exportar as p; p.show()
    elif page == "usuarios":
        import pages.usuarios as p; p.show()
    elif page == "configuracion":
        import pages.configuracion as p; p.show()
    else:
        import pages.dashboard as p; p.show()
