# Monitor Trato Directo SSMOCC — Versión 2.0

Esta versión incorpora una lógica histórica por **Año + Período**, para que cada carga oficial MINSAL quede guardada sin sobrescribir los períodos anteriores.

## Flujo de uso

1. Ingresar como administrador.
2. Ir a **Carga MINSAL**.
3. Seleccionar año y período:
   - R1: Enero–Marzo, entrega 31 de julio.
   - R2: Abril–Junio, entrega 31 de agosto.
   - R3: Julio–Septiembre, entrega 30 de noviembre.
   - R4: Octubre–Diciembre, entrega 28 de febrero.
4. Subir CSV oficial MINSAL.
5. Confirmar carga histórica.
6. Revisar **Dashboard**.
7. Generar **Boletín Ejecutivo**.
8. Descargar **Excel MINSAL** desde Exportar.
9. Revisar comparativos en **Histórico**.

## Archivos principales

- `app.py`: aplicación Streamlit completa.
- `logo_ssmocc.jpg`: logo institucional usado por la aplicación.
- `requirements.txt`: dependencias.
- `.gitignore`: configuración Git.

## Persistencia

La app mantiene compatibilidad con la persistencia anterior y agrega:

- `data/datos_periodos.json`: base histórica por año y período.
- `data/datos_minsal.json`: compatibilidad con la versión previa.
- `data/reports.json`: reportes ingresados por establecimientos.
- `data/users.json`: usuarios.

En Streamlit Cloud, para persistencia real, mantener configurado GitHub en `st.secrets`:

```toml
[github]
token = "ghp_xxxxx"
repo = "usuario/repositorio"
branch = "main"
```

## Mejora incorporada

La plataforma ahora permite trabajar sucesivamente con enero–marzo, abril–junio, julio–septiembre y octubre–diciembre, generando para cada período:

- Dashboard ejecutivo.
- Boletín institucional HTML.
- Respaldo Excel del boletín.
- Exportación Anexo N°1 MINSAL.
- Histórico y comparativos.

