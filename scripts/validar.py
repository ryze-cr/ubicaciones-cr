"""Valida que los datos y los archivos generados sean consistentes.

Uso:
    python scripts/validar.py

Sale con código 1 si encuentra algún problema.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLIC = RAIZ / 'public'
errores = []


def leer(ruta):
    return json.loads((PUBLIC / ruta).read_text(encoding='utf-8'))


def revisar(condicion, mensaje):
    if not condicion:
        errores.append(mensaje)


dta = json.loads((RAIZ / 'data/dta.json').read_text(encoding='utf-8'))
oficiales = dta['fuente']['totales_oficiales']
cantones = [c for p in dta['provincias'] for c in p['cantones']]
distritos = [d for c in cantones for d in c['distritos']]

revisar(len(dta['provincias']) == oficiales['provincias'], f"provincias: {len(dta['provincias'])} != {oficiales['provincias']}")
revisar(len(cantones) == oficiales['cantones'], f"cantones: {len(cantones)} != {oficiales['cantones']}")
revisar(len(distritos) == oficiales['distritos'], f"distritos: {len(distritos)} != {oficiales['distritos']}")

codigos = [d['codigo'] for d in distritos]
revisar(len(codigos) == len(set(codigos)), 'hay códigos de distrito repetidos')
for p in dta['provincias']:
    for c in p['cantones']:
        revisar(c['codigo'].startswith(p['codigo']) and len(c['codigo']) == 3, f"código de cantón inválido: {c['codigo']}")
        revisar(c['distritos'], f"el cantón {c['codigo']} no tiene distritos")
        for d in c['distritos']:
            revisar(d['codigo'].startswith(c['codigo']) and len(d['codigo']) == 5, f"código de distrito inválido: {d['codigo']}")
            revisar(d['nombre'].strip() == d['nombre'] and d['nombre'], f"nombre inválido en {d['codigo']}")

# Los archivos de public/ deben corresponder a data/dta.json
revisar(leer('provincias.json') == {p['codigo']: p['nombre'] for p in dta['provincias']}, 'provincias.json desactualizado')
for p in dta['provincias']:
    for c in p['cantones']:
        nc = int(c['codigo'][1:])
        revisar(leer(f"provincia/{p['codigo']}/cantones.json").get(str(nc)) == c['nombre'], f"cantones.json desactualizado ({c['codigo']})")
        archivo = leer(f"provincia/{p['codigo']}/canton/{nc}/distritos.json")
        revisar(archivo == {str(int(d['codigo'][3:])): d['nombre'] for d in c['distritos']}, f"distritos.json desactualizado ({c['codigo']})")
        for d in c['distritos']:
            revisar(leer(f"codigo-postal/{d['codigo']}.json")['distrito'] == d['nombre'], f"codigo-postal/{d['codigo']}.json desactualizado")
revisar(len(list((PUBLIC / 'codigo-postal').glob('*.json'))) == len(distritos), 'sobran archivos en codigo-postal/')
revisar(len(leer('distritos.json')) == len(distritos), 'distritos.json desactualizado')
edicion = dta['fuente']['edicion']
indice = (PUBLIC / 'index.html').read_text(encoding='utf-8')
revisar(f'DTA {edicion}' in indice and f'{len(distritos)} distritos' in indice,
        f'index.html no menciona la DTA {edicion} o los {len(distritos)} distritos (SEO desactualizado)')
ingles = (PUBLIC / 'en/index.html').read_text(encoding='utf-8')
revisar(f'DTA {edicion}' in ingles and f'{len(distritos)} districts' in ingles,
        f'en/index.html no menciona la DTA {edicion} o los {len(distritos)} districts')
guia = (PUBLIC / 'llms.txt').read_text(encoding='utf-8')
revisar(f'DTA {edicion}' in guia and f'{len(distritos)} distritos' in guia,
        f'llms.txt no menciona la DTA {edicion} o los {len(distritos)} distritos')
spec = json.loads((PUBLIC / 'openapi.json').read_text(encoding='utf-8'))
revisar(spec['info']['version'] == f'DTA {edicion}', f'openapi.json no tiene la versión DTA {edicion}')
for ruta, op in spec['paths'].items():
    ejemplo = op['get']['responses']['200']['content']['application/json'].get('example')
    if ejemplo is None:
        continue
    params = {'provincia': '1', 'canton': '3', 'codigoPostal': ejemplo.get('codigo_postal', '') if isinstance(ejemplo, dict) else ''}
    real = leer(ruta.lstrip('/').format(**params))
    esperado = real if isinstance(real, dict) and 'codigo_postal' in real else {k: real.get(k) for k in ejemplo}
    revisar(ejemplo == esperado, f'el ejemplo de {ruta} en openapi.json no coincide con los datos')
revisar((PUBLIC / 'og.png').exists(), 'falta public/og.png (correr scripts/generar_imagen_og.py)')
revisar((PUBLIC / '404.html').exists(), 'falta public/404.html (sin él, Cloudflare Pages responde 200 a rutas inexistentes)')

if errores:
    print('\n'.join(f'✗ {e}' for e in errores))
    sys.exit(1)
print(f"✓ {len(dta['provincias'])} provincias, {len(cantones)} cantones, {len(distritos)} distritos. Todo consistente.")
