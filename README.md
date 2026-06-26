# Monitor Trato Directo SSMOCC v2

Versión institucional del Monitor de Trato Directo del Servicio de Salud Metropolitano Occidente.

## Flujo principal

1. El administrador selecciona año y período.
2. Carga el CSV oficial MINSAL.
3. El dashboard se actualiza para ese período.
4. Los establecimientos en nivel rojo y amarillo ingresan sus causas, medidas, compromisos, responsable y fecha comprometida.
5. El administrador genera el Anexo N°1 MINSAL con el formato oficial.
6. El sistema mantiene histórico por período para comparar evolución.

## Ajuste clave incluido

El módulo **Exportar Anexo N°1 MINSAL** se alimenta exclusivamente de los reportes enviados por establecimientos en nivel **rojo** y **amarillo**.

El Excel generado contiene las columnas solicitadas por MINSAL:

- Servicio de salud
- Establecimiento
- Nivel de Riesgo
- Período informado
- Principales causas
- Medidas implementadas
- Compromisos
- Responsable
- Fecha comprometida

Los establecimientos verdes quedan fuera del Anexo, salvo que el lineamiento solicite incluirlos.

## Archivos

- `app.py`: aplicación Streamlit completa.
- `requirements.txt`: dependencias.
- `logo_ssmocc.jpg`: imagen institucional.
- `.gitignore`: reglas de repositorio.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Persistencia

La app usa archivos JSON locales y puede guardar en GitHub si se configuran secrets de Streamlit:

```toml
[github]
token = "ghp_TU_TOKEN"
repo = "usuario/repositorio"
branch = "main"
```
