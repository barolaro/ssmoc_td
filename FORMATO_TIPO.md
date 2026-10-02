# Formato Tipo consolidado MINSAL 2026

La actualización usa `assets/formato_minsal_2026.docx`, copia del formato vigente proporcionado por el Servicio. Conserva sus ocho secciones y duplica los bloques por establecimiento. El Anexo N.º 1 sigue disponible como resumen complementario.

Los establecimientos completan el plan por acción, avances anteriores, seguimiento según riesgo, cotejo con la comunicación de la Subsecretaría y referencias a respaldos y reclasificaciones de OC. El indicador cargado desde el CSV se conserva; la actualización no recalcula el indicador A.3.2 ni modifica su metodología.

En **Exportar MINSAL**, el administrador registra la identificación del remitente y el control de pendientes y descarga el Word completo. Si faltan antecedentes, el documento se identifica como borrador y los casos se incorporan a la sección 7. La firma, el visado y el envío ministerial requieren gestión institucional posterior; no se envían correos desde este módulo. Los enlaces de respaldo deben apuntar a repositorios institucionales y sus documentos deben adjuntarse o ponerse a disposición según el procedimiento de entrega.

Los reportes antiguos conservan sus campos originales. No se inventan avances ni clasificaciones de la comunicación MINSAL. Si un reporte ya enviado requiere completar los campos nuevos, el administrador habilita su edición desde **Todos los reportes**, registra el motivo y el referente lo reenvía.

Los nuevos datos se agregan en `formato_tipo` dentro del reporte. La identificación del consolidado se guarda por año y reporte en `data/gestion_consolidado.json`. Los archivos existentes de datos y usuarios no se migran ni reemplazan al desplegar. La escritura debe confirmarse en el backend configurado antes de mostrar éxito; sin configuración persistente se informa un error y se conserva el formulario.

Validación automatizada:

```bash
python -m unittest discover -s . -p 'test_*.py' -v
```

Las pruebas cubren acciones y seguimiento por riesgo, diferencias con MINSAL, OC Por Informar, reportes anteriores, separación de períodos, estructura y duplicación de bloques del Word y errores de almacenamiento.
