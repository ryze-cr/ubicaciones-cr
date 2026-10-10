# Accesibilidad

## Compromiso

La página de documentación busca cumplir las pautas [WCAG 2.2](https://www.w3.org/TR/WCAG22/) en nivel AA, para que cualquier persona pueda leerla y probar la API. Todavía no ha tenido una auditoría formal.

## Lo que ya está hecho

- HTML semántico, con encabezados en orden y tablas con encabezados.
- Cada selector y campo tiene su etiqueta (`<label>`).
- Todo se puede usar con teclado y el foco es visible.
- Los resultados del demo se anuncian a lectores de pantalla (`aria-live`).
- Tema oscuro con contraste de texto de al menos 4.5:1 (nivel AA).
- Funciona en pantallas desde 320 px de ancho sin scroll horizontal, y con zoom del navegador.
- No usa animaciones ni contenido que parpadee.

## Entornos probados

Navegadores basados en Chromium, en escritorio y con tamaño de celular. Todavía no se ha probado a fondo con lectores de pantalla (VoiceOver, NVDA, TalkBack).

## Limitaciones conocidas

- Los ejemplos de código están en bloques que se desplazan horizontalmente en pantallas pequeñas.
- La API devuelve JSON. Su accesibilidad depende de la aplicación que lo muestre.

## Reportar una barrera

Si algo te impide usar la página, abrí un [issue](https://github.com/ryze-cr/ubicaciones-cr/issues/new/choose). Contá qué intentabas hacer, qué pasó y qué navegador o tecnología de asistencia usás.
