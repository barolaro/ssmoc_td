"""
auth.py  —  Autenticación y datos base SSMOC
"""
import hashlib, json, datetime
from pathlib import Path
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE   = DATA_DIR / "users.json"
REPORTS_FILE = DATA_DIR / "reports.json"


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# ESTABLECIMIENTOS SSMOC (datos CSV MINSAL)
# ─────────────────────────────────────────────────────────────────────────────
ESTABLECIMIENTOS = {
    "traumatologico": {
        "nombre": "Instituto Traumatológico Dr. Teodoro Gebauer",
        "nombre_corto": "Inst. Traumatológico",
        "rut": "61.608.402-k",
        "codigo_deis": "110110",
        "pct_2026": 62.17,
        "pct_2025": 37.78,
        "brecha": 46.17,
        "variacion": 24.39,
        "nivel": "rojo",
        "denominador": 5868063000,
        "numerador": 3648431000,
    },
    "direccion": {
        "nombre": "Dirección del Servicio Metropolitano Occidente",
        "nombre_corto": "Dir. SSMOC",
        "rut": "61.608.200-0",
        "codigo_deis": "110010",
        "pct_2026": 37.16,
        "pct_2025": 5.30,
        "brecha": 21.16,
        "variacion": 31.86,
        "nivel": "rojo",
        "denominador": 5835193000,
        "numerador": 2168191000,
    },
    "felix_bulnes": {
        "nombre": "Hospital Dr. Félix Bulnes Cerda",
        "nombre_corto": "H. Félix Bulnes",
        "rut": "61.608.205-1",
        "codigo_deis": "110120",
        "pct_2026": 26.44,
        "pct_2025": 21.59,
        "brecha": 10.44,
        "variacion": 4.85,
        "nivel": "rojo",
        "denominador": 19487600000,
        "numerador": 5152787000,
    },
    "san_juan": {
        "nombre": "Hospital San Juan de Dios",
        "nombre_corto": "H. San Juan de Dios",
        "rut": "61.608.204-3",
        "codigo_deis": "110100",
        "pct_2026": 11.61,
        "pct_2025": 10.70,
        "brecha": -4.39,
        "variacion": 0.91,
        "nivel": "amarillo",
        "denominador": 39066760000,
        "numerador": 4535665000,
    },
    "crs_allende": {
        "nombre": "Centro de Referencia Salud Occidente Salvador Allende",
        "nombre_corto": "CRS Salvador Allende",
        "rut": "61.933.400-0",
        "codigo_deis": "110300",
        "pct_2026": 7.07,
        "pct_2025": 4.76,
        "brecha": -8.93,
        "variacion": 2.31,
        "nivel": "amarillo",
        "denominador": 1954204000,
        "numerador": 138205000,
    },
    "melipilla": {
        "nombre": "Hospital San José (Melipilla)",
        "nombre_corto": "H. Melipilla",
        "rut": "61.602.122-2",
        "codigo_deis": "110150",
        "pct_2026": 6.60,
        "pct_2025": 8.29,
        "brecha": -9.40,
        "variacion": -1.69,
        "nivel": "verde",
        "denominador": 6908127000,
        "numerador": 455863000,
    },
    "penaflor": {
        "nombre": "Hospital de Peñaflor",
        "nombre_corto": "H. Peñaflor",
        "rut": "61.602.123-0",
        "codigo_deis": "110140",
        "pct_2026": 6.89,
        "pct_2025": 17.58,
        "brecha": -9.11,
        "variacion": -10.69,
        "nivel": "verde",
        "denominador": 1677287000,
        "numerador": 115598000,
    },
    "curacavi": {
        "nombre": "Hospital de Curacaví",
        "nombre_corto": "H. Curacaví",
        "rut": "61.602.125-7",
        "codigo_deis": "110160",
        "pct_2026": 5.62,
        "pct_2025": 14.42,
        "brecha": -10.38,
        "variacion": -8.80,
        "nivel": "verde",
        "denominador": 1001068000,
        "numerador": 56257000,
    },
    "talagante": {
        "nombre": "Hospital Adalberto Steeger (Talagante)",
        "nombre_corto": "H. Talagante",
        "rut": "61.602.121-4",
        "codigo_deis": "110130",
        "pct_2026": 3.21,
        "pct_2025": 10.63,
        "brecha": -12.79,
        "variacion": -7.42,
        "nivel": "verde",
        "denominador": 7242042000,
        "numerador": 232417000,
    },
}

PERIODOS_REPORTE = [
    {"id": "R1", "label": "1° Reporte",  "periodo": "Enero–Marzo 2026",       "fecha_limite": "2026-07-31"},
    {"id": "R2", "label": "2° Reporte",  "periodo": "Abril–Junio 2026",       "fecha_limite": "2026-08-31"},
    {"id": "R3", "label": "3° Reporte",  "periodo": "Julio–Septiembre 2026",  "fecha_limite": "2026-11-30"},
    {"id": "R4", "label": "4° Reporte",  "periodo": "Octubre–Diciembre 2026", "fecha_limite": "2027-02-28"},
]

CAUSALES_TD = [
    "Proveedor único / exclusividad",
    "Emergencia o urgencia debidamente calificada",
    "Licitación desierta (2° vez)",
    "Confidencialidad / seguridad nacional",
    "Continuidad de servicios en ejecución",
    "Derechos de propiedad intelectual (software, licencias)",
    "Equipamiento especializado sin equivalente de mercado",
    "Convenio con otro organismo público (CENABAST, etc.)",
    "Compra ágil (< 30 UTM)",
    "Otra causal — especificar en observaciones",
]

COLORES_NIVEL = {
    "verde":    {"bg": "#EAF3DE", "text": "#27500A", "dot": "#3B6D11"},
    "amarillo": {"bg": "#FAEEDA", "text": "#412402", "dot": "#BA7517"},
    "rojo":     {"bg": "#FCEBEB", "text": "#501313", "dot": "#E24B4A"},
}


def _init_default_users() -> dict:
    raw = {
        "admin":          ("Administrador SSMOC",                           "admin",          "abastecimiento@ssmocc.cl",       None,             "Admin2026*"),
        "bayron":         ("Bayron Retamal González",                       "admin",          "bayron.retamal@ssmocc.cl",       None,             "Ssmoc2026*"),
        "traumatologico": ("Miguel Jara",                                   "establecimiento","miguel.jara@intraumatologico.cl",  "traumatologico", "Trauma2026*"),
        "direccion":      ("Referente — Dir. SSMOC",                        "establecimiento","abast.direccion@ssmocc.cl",             "direccion",      "Dir2026*"),
        "felix_bulnes":   ("Carolina Castro",                                "establecimiento","carolina.castroj@redsalud.gob.cl",     "felix_bulnes",   "Felix2026*"),
        "san_juan":       ("Rodrigo Bravo Gajardo",                          "establecimiento","rodrigo.bravog@redsalud.gob.cl",       "san_juan",       "Sjd2026*"),
        "crs_allende":    ("Eric Cubillo Antúnez",                           "establecimiento","eric.cubillo@redsalud.gob.cl",         "crs_allende",    "Crs2026*"),
        "melipilla":      ("María de los Ángeles Morales",                  "establecimiento","maria.moralesj@redsalud.gob.cl",      "melipilla",      "Meli2026*"),
        "penaflor":       ("Gissela Salvo",                                 "establecimiento","gissela.salvo@redsalud.gob.cl",       "penaflor",       "Pen2026*"),
        "curacavi":       ("Pablo Yévenes Olivares",                        "establecimiento","pablo.yevenes@redsalud.gob.cl",       "curacavi",       "Cura2026*"),
        "talagante":      ("María Andrea Villegas Albarrán",                "establecimiento","mandrea.villegas@redsalud.gob.cl",    "talagante",      "Tala2026*"),
    }
    users = {}
    for uid, (nombre, rol, email, estab, pwd) in raw.items():
        users[uid] = {
            "nombre": nombre, "rol": rol, "email": email,
            "establecimiento": estab,
            "password_hash": _hash(pwd),
            "activo": True,
        }
    return users


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────
def load_users() -> dict:
    if not USERS_FILE.exists():
        users = _init_default_users()
        save_users(users)
        return users
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_reports() -> list:
    if not REPORTS_FILE.exists():
        return []
    with open(REPORTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reports(reports: list):
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2, default=str)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
def authenticate(username: str, password: str):
    users = load_users()
    u = users.get(username.strip().lower())
    if u and u.get("activo") and u["password_hash"] == _hash(password):
        return {**u, "username": username.strip().lower()}
    return None


def require_login():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Debes iniciar sesión para acceder a esta sección.")
        st.stop()
    return st.session_state.user


def require_admin():
    user = require_login()
    if user.get("rol") != "admin":
        st.error("Acceso restringido — solo administradores.")
        st.stop()
    return user


# ─────────────────────────────────────────────────────────────────────────────
# REPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_report(establecimiento_id: str, reporte_id: str):
    for r in load_reports():
        if r["establecimiento_id"] == establecimiento_id and r["reporte_id"] == reporte_id:
            return r
    return None


def upsert_report(data: dict):
    reports = load_reports()
    for i, r in enumerate(reports):
        if r["establecimiento_id"] == data["establecimiento_id"] and r["reporte_id"] == data["reporte_id"]:
            reports[i] = data
            save_reports(reports)
            return
    reports.append(data)
    save_reports(reports)
