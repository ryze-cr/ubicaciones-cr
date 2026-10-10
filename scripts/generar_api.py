"""Genera los archivos JSON estáticos de la API en public/ a partir de data/dta.json.

Uso:
    python scripts/generar_api.py

Solo usa la biblioteca estándar. Borra y vuelve a crear los archivos generados;
no toca index.html, 404.html ni _headers.
"""
import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLIC = RAIZ / 'public'
# Versión de la API (semver): mayor = cambios que rompen integraciones, menor = rutas o datos nuevos,
# parche = correcciones. Se publica en /meta.json y en cada release de GitHub.
VERSION = '1.0.0'
GENERADOS = ['provincias.json', 'provincia', 'codigo-postal', 'todo.json', 'distritos.json', 'meta.json']


def escribir(ruta, datos, compacto=True):
    ruta = PUBLIC / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(datos, ensure_ascii=False, separators=(',', ':') if compacto else None,
                       indent=None if compacto else 1)
    ruta.write_text(texto + '\n', encoding='utf-8')


def main():
    dta = json.loads((RAIZ / 'data/dta.json').read_text(encoding='utf-8'))
    for nombre in GENERADOS:
        destino = PUBLIC / nombre
        if destino.is_dir():
            shutil.rmtree(destino)
        elif destino.exists():
            destino.unlink()

    # Endpoints compatibles con ubicaciones.paginasweb.cr: { "<número>": "<nombre>" }
    escribir('provincias.json', {p['codigo']: p['nombre'] for p in dta['provincias']})
    planos = []
    for p in dta['provincias']:
        escribir(f"provincia/{p['codigo']}/cantones.json",
                 {str(int(c['codigo'][1:])): c['nombre'] for c in p['cantones']})
        for c in p['cantones']:
            nc = int(c['codigo'][1:])
            escribir(f"provincia/{p['codigo']}/canton/{nc}/distritos.json",
                     {str(int(d['codigo'][3:])): d['nombre'] for d in c['distritos']})
            for d in c['distritos']:
                item = {
                    'codigo_postal': d['codigo'],
                    'distrito': d['nombre'],
                    'canton': c['nombre'],
                    'provincia': p['nombre'],
                    'codigos': {'provincia': int(p['codigo']), 'canton': nc, 'distrito': int(d['codigo'][3:])},
                    'area_km2': d['area_km2'],
                }
                planos.append(item)
                escribir(f"codigo-postal/{d['codigo']}.json", item)

    # Endpoints nuevos
    escribir('distritos.json', planos)
    escribir('todo.json', dta)
    escribir('meta.json', {
        'version': VERSION,
        'fuente': dta['fuente'],
        'totales': {
            'provincias': len(dta['provincias']),
            'cantones': sum(len(p['cantones']) for p in dta['provincias']),
            'distritos': len(planos),
        },
    }, compacto=False)
    print(f'Generados {len(planos)} distritos en public/')


if __name__ == '__main__':
    main()
