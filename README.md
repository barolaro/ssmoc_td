# SIMOTD — Sistema de Monitoreo del Indicador de Trato Directo

Plataforma institucional para el Servicio de Salud Metropolitano Occidente (SSMOCC), orientada al seguimiento del indicador de Trato Directo, gestión de reportes por establecimiento, generación del Anexo N°1 MINSAL y trazabilidad por año/período.

## Funcionalidades principales

- Identidad institucional **SIMOTD**.
- Dashboard ejecutivo por año y período.
- Carga oficial MINSAL por CSV.
- Control de períodos con carga oficial.
- Reportes por establecimientos.
- Bloqueo automático del reporte una vez enviado.
- Habilitación excepcional de edición por administrador.
- Bitácora de trazabilidad del reporte.
- Vista previa institucional del Anexo N°1.
- Exportación consolidada MINSAL.
- Histórico y boletín ejecutivo.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Persistencia en Streamlit Cloud

Configurar `st.secrets`:

```toml
[github]
token = "ghp_xxxxxxxxx"
repo = "barolaro/ssmoc_td"
branch = "main"
```

## Nombre institucional

**SIMOTD**  
Sistema de Monitoreo del Indicador de Trato Directo  
Servicio de Salud Metropolitano Occidente
