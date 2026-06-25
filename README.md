# Monitor Trato Directo — SSMOC 2026

Plataforma de monitoreo y reporte de compras mediante Trato Directo para la Red Asistencial del **Servicio de Salud Metropolitano Occidente (SSMOC)**, en cumplimiento del **Lineamiento MINSAL v1.0 — Junio 2026** (Área de Compras Estratégicas y Procesos Logísticos, División de Presupuesto, Subsecretaría de Redes Asistenciales).

---

## Funcionalidades

| Rol | Funcionalidades |
|-----|----------------|
| **Administrador** | Dashboard global · Ver todos los reportes · Exportar Anexo N°1 MINSAL · Gestionar usuarios · Marcar/desmarcar envíos |
| **Establecimiento** | Ver su estado de riesgo · Ingresar reporte de su período (causas, medidas, compromisos) · Guardar borrador o enviar |

## Estructura del proyecto

```
ssmoc_td_app/
├── app.py                  # Punto de entrada (login + routing)
├── auth.py                 # Autenticación, datos SSMOC, persistencia
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Tema institucional
├── pages/
│   ├── dashboard.py        # Panel principal con gráficos
│   ├── mis_reportes.py     # Formulario de ingreso por establecimiento
│   ├── todos_reportes.py   # Vista consolidada (admin)
│   ├── exportar.py         # Exportar Anexo N°1 MINSAL (Excel/CSV)
│   ├── usuarios.py         # Gestión de usuarios (admin)
│   └── configuracion.py    # Configuración y mantenimiento
└── data/                   # Generado automáticamente al iniciar
    ├── users.json          # Usuarios y contraseñas (hash SHA-256)
    └── reports.json        # Reportes ingresados
```

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/ssmoc-td-monitor.git
cd ssmoc-td-monitor

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`

## Despliegue en Streamlit Cloud

1. Hacer fork o subir este repositorio a GitHub.
2. Ir a [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub.
3. Seleccionar el repositorio y el archivo principal (`app.py`).
4. Clic en **Deploy**.

> ⚠️ En Streamlit Cloud el sistema de archivos es efímero — los datos de `data/` se pierden al reiniciar. Para producción, configurar una base de datos (ver sección de producción).

## Credenciales por defecto

| Usuario | Contraseña | Rol | Establecimiento |
|---------|-----------|-----|-----------------|
| `admin` | `Admin2026*` | Administrador | — |
| `bayron` | `Ssmoc2026*` | Administrador | — |
| `traumatologico` | `Trauma2026*` | Establecimiento | Inst. Traumatológico |
| `direccion` | `Dir2026*` | Establecimiento | Dir. SSMOC |
| `felix_bulnes` | `Felix2026*` | Establecimiento | H. Félix Bulnes |
| `san_juan` | `Sjd2026*` | Establecimiento | H. San Juan de Dios |
| `crs_allende` | `Crs2026*` | Establecimiento | CRS Salvador Allende |
| `melipilla` | `Meli2026*` | Establecimiento | H. Melipilla |
| `penaflor` | `Pen2026*` | Establecimiento | H. Peñaflor |
| `curacavi` | `Cura2026*` | Establecimiento | H. Curacaví |
| `talagante` | `Tala2026*` | Establecimiento | H. Talagante |

> 🔐 **Cambie todas las contraseñas** desde la sección "Gestión usuarios" antes de usar en producción.

## Metodología

- **Indicador:** % TD = Numerador (CLP) / Denominador (CLP) × 100
- **Numerador:** Monto neto CLP compras TD con recepción conforme (ChileCompra)
- **Denominador:** Monto neto CLP total todas las modalidades
- **Meta 2026:** ≤ 16%
- **Clasificación:** Verde ≤ 16% · Amarillo 16–18% · Rojo > 18% (y/o variación > 3 pp vs. 2025)
- Este monitoreo es **independiente** del indicador ADP A.3.2

## Calendario de reportes

| Reporte | Período | Fecha límite |
|---------|---------|-------------|
| 1° | Enero–Marzo 2026 | **31 julio 2026** |
| 2° | Abril–Junio 2026 | 31 agosto 2026 |
| 3° | Julio–Septiembre 2026 | 30 noviembre 2026 |
| 4° | Octubre–Diciembre 2026 | 28 febrero 2027 |

## Para producción

Para persistencia de datos en producción, reemplazar `auth.py` para usar:

- **SQLite** (simple, sin servidor): `pip install sqlalchemy`
- **PostgreSQL** (recomendado): configurar en Streamlit Secrets como `DATABASE_URL`
- **Supabase** (gratuito + PostgreSQL en la nube): ideal para Streamlit Cloud

## Contacto

Subdirección de Recursos Físicos y Financieros — SSMOC  
Coordinación: Bayron Retamal González — Encargado de Concesiones  
Email: bayron.retamal@ssmocc.cl

---
*Lineamiento MINSAL v1.0 · Área de Compras Estratégicas y Procesos Logísticos · Junio 2026*
