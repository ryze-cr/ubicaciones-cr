# Ubicaciones de Costa Rica

API JSON gratuita con las provincias, cantones, distritos y códigos postales de Costa Rica, según la **División Territorial Administrativa 2026** del Instituto Geográfico Nacional (IGN).

- **7 provincias, 84 cantones y 494 distritos**
- Archivos JSON estáticos, CORS abierto y sin API key
- El código postal es el código oficial del distrito (`PCCDD`)
- Las rutas son compatibles con [ubicaciones.paginasweb.cr](https://ubicaciones.paginasweb.cr)

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

Los números de cantón y distrito van sin ceros a la izquierda: `/provincia/1/canton/3/distritos.json`.

```js
const cantones = await fetch('https://<dominio>/provincia/1/cantones.json').then(r => r.json());
// { "1": "San José", "2": "Escazú", "3": "Desamparados", ... }

const distrito = await fetch('https://<dominio>/codigo-postal/10305.json').then(r => r.json());
// { "codigo_postal": "10305", "distrito": "San Antonio", "canton": "Desamparados", "provincia": "San José", ... }
```

## Diferencias con ubicaciones.paginasweb.cr

- Datos al día con la DTA 2026: incluye Monteverde y Puerto Jiménez, 11 distritos que faltaban (entre ellos Pijije y Cabagra, de 2025), y retira 3 códigos viejos de distritos que cambiaron de cantón.
- Corrige los códigos postales de 7 distritos de Desamparados (10305 a 10311).
- Usa los nombres oficiales del IGN, con tildes. El cantón 1 de cada provincia se llama por su nombre (por ejemplo, "San José"), no "Central".

## Cómo se generan los datos

```
PDF oficial del IGN ──► scripts/extraer_dta.py ──► data/dta.json ──► scripts/generar_api.py ──► public/
                              ▲
                     data/correcciones.json
```

1. **`scripts/extraer_dta.py`** lee el PDF *DTA-TABLA POR PROVINCIA-CANTÓN-DISTRITO* que publica el IGN en el [SNIT](https://www.snitcr.go.cr/biblioteca_DTA_menu) y genera `data/dta.json`.
2. **`data/correcciones.json`** documenta los ajustes al PDF, cada uno con su motivo. Hoy hay dos:
   - Se agrega **Duacarí (70605)**. El IGN lo cuenta en el total oficial, pero lo omite en la tabla de detalle.
   - Se agrega la tilde a **Puerto Jiménez** en el nombre del cantón.
3. **`scripts/generar_api.py`** genera todos los JSON de `public/` usando solo la biblioteca estándar de Python.
4. **`scripts/validar.py`** compara los totales con los que declara el IGN y revisa que códigos y archivos sean consistentes. Corre en GitHub Actions en cada push y en cada PR.

### Actualizar a una nueva edición del IGN

El IGN publica la DTA cada dos años, y entre ediciones puede haber leyes que crean distritos nuevos.

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
mkdir -p fuentes && curl -L -o fuentes/DTA.pdf "<url del PDF nuevo>"
.venv/bin/python scripts/extraer_dta.py fuentes/DTA.pdf --edicion 2028 --url "<url del PDF nuevo>"
python3 scripts/generar_api.py
python3 scripts/validar.py
```

Si el extractor avisa que una corrección ya no aplica (por ejemplo, porque el IGN agregó Duacarí a la tabla), quitala de `data/correcciones.json`.

## Desarrollo local

```bash
python3 -m http.server 8787 --directory public
```

## Despliegue

Es un sitio estático en `public/`, sin paso de build. En Cloudflare Pages: **Framework preset** None, **Build command** vacío y **Build output directory** `public`. El archivo `public/_headers` configura CORS y caché, y `public/404.html` hace que las rutas inexistentes respondan 404.

## Créditos y licencia

- Hecho gracias a [Carl De Pass](https://github.com/ryze-cr).
- Datos: [Instituto Geográfico Nacional](https://www.snitcr.go.cr), Registro Nacional de Costa Rica.
- Inspirado en [lfbvyo/ubicaciones](https://github.com/lfbvyo/ubicaciones), de Luis Felipe Barnett Vásquez.
- Código bajo licencia [MIT](LICENSE).
