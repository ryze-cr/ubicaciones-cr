# Política de seguridad

La API es un sitio estático de solo lectura: no tiene cuentas, formularios, base de datos ni código que corra en el servidor. Aun así, los reportes de seguridad son bienvenidos.

## Qué reportar

- Una forma de alterar los datos publicados sin pasar por el repositorio.
- Vulnerabilidades en la página de documentación, por ejemplo XSS.
- Configuraciones que expongan a quienes usan la API, como headers CORS o de caché mal configurados.
- Cambios maliciosos en el repositorio o en el flujo de publicación.

Un error en los datos (un distrito que falta, un nombre o un código mal escrito) no es un problema de seguridad: reportalo como [issue](https://github.com/ryze-cr/ubicaciones-cr/issues/new/choose).

## Cómo reportar

No abras un issue público. Usá el reporte privado de GitHub:

**[Reportar una vulnerabilidad](https://github.com/ryze-cr/ubicaciones-cr/security/advisories/new)**

Incluí qué encontraste, cómo reproducirlo y qué impacto puede tener. Se intentará responder en un plazo de 7 días y avisarte cuando esté corregido.

## Versiones con soporte

Solo se mantiene la versión publicada desde la rama `main`.
