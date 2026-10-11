# Cómo contribuir

## Reportar un error en los datos

Abrí un [issue](https://github.com/ryze-cr/ubicaciones-cr/issues/new) con:

- El código postal o la ruta afectada (por ejemplo, `10305` o `/provincia/1/canton/3/distritos.json`).
- Qué dice la API y qué debería decir.
- La fuente oficial: la tabla de la DTA del IGN, una ley o un decreto publicado en La Gaceta.

Si el error es sobre la GAM (un distrito marcado dentro o fuera por error), indicá el distrito y por qué; la clasificación y sus fuentes están en `data/gam.json`.

Los datos siguen a la División Territorial Administrativa del IGN. Si hay una ley que crea o cambia un distrito y todavía no aparece en la DTA, también se puede agregar en `data/correcciones.json`, citando la ley.

## Proponer un cambio

1. Hacé un fork y una rama.
2. Si cambiás datos, agregá la corrección en `data/correcciones.json` con su motivo y volvé a correr `scripts/extraer_dta.py`. No edites a mano `data/dta.json` ni `public/`: esos cambios se pierden la próxima vez que se generen los archivos.
3. Corré `python3 scripts/generar_api.py` y `python3 scripts/validar.py`.
4. Abrí un PR. La validación automática tiene que pasar para poder hacer el merge.
