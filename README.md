# Ubicaciones de Costa Rica

API JSON gratuita con las provincias, cantones, distritos y códigos postales de Costa Rica, según la **División Territorial Administrativa 2026** del Instituto Geográfico Nacional (IGN).

**URL:** https://ubicaciones-cr.ryze-cr.workers.dev

**English:** https://ubicaciones-cr.ryze-cr.workers.dev/en/

- **7 provincias, 84 cantones y 494 distritos**
- Sin API key, sin registro y con CORS abierto
- El código postal es el código oficial del distrito: provincia (1 dígito) + cantón (2) + distrito (2)

## Endpoints

| Ruta | Devuelve |
|---|---|
| `/provincias.json` | Las 7 provincias |
| `/provincia/{p}/cantones.json` | Cantones de una provincia |
| `/provincia/{p}/canton/{c}/distritos.json` | Distritos de un cantón |
| `/codigo-postal/{PCCDD}.json` | Un distrito por su código postal, con su cantón y provincia |
| `/distritos.json` | Lista plana de todos los distritos con código postal |
| `/todo.json` | Árbol completo con códigos oficiales y áreas en km² |
| `/meta.json` | Fuente, edición y totales |
| `/openapi.json` | Especificación OpenAPI 3.1 |
| `/llms.txt` | Guía de uso para agentes de IA |

Los números de cantón y distrito van sin ceros a la izquierda: `/provincia/1/canton/3/distritos.json`.

```js
const cantones = await fetch('https://ubicaciones-cr.ryze-cr.workers.dev/provincia/1/cantones.json').then(r => r.json());
// { "1": "San José", "2": "Escazú", "3": "Desamparados", ... }

const distrito = await fetch('https://ubicaciones-cr.ryze-cr.workers.dev/codigo-postal/10305.json').then(r => r.json());
// { "codigo_postal": "10305", "distrito": "San Antonio", "canton": "Desamparados", "provincia": "San José", ... }
```

Las tres primeras rutas tienen la misma forma que [ubicaciones.paginasweb.cr](https://ubicaciones.paginasweb.cr), así que para migrar solo cambiás la URL base.

## ¿Encontraste un error?

Abrí un [issue](https://github.com/ryze-cr/ubicaciones-cr/issues/new/choose) con la fuente oficial. Más detalles en [CONTRIBUTING.md](CONTRIBUTING.md).

## Créditos y licencia

- Hecho gracias a [Carl De Pass](https://github.com/ryze-cr).
- Datos: [Instituto Geográfico Nacional](https://www.snitcr.go.cr), Registro Nacional de Costa Rica.
- Inspirado en [lfbvyo/ubicaciones](https://github.com/lfbvyo/ubicaciones), de Luis Felipe Barnett Vásquez.
- Código bajo licencia [MIT](LICENSE).
