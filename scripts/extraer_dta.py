"""Extrae la División Territorial Administrativa (DTA) del PDF oficial del IGN.

Uso:
    pip install -r scripts/requirements.txt
    python scripts/extraer_dta.py fuentes/DTA-2026.pdf --edicion 2026 --url <url del PDF>

Genera data/dta.json aplicando las correcciones documentadas en data/correcciones.json.

Para actualizar a una nueva edición del IGN (sale cada dos años en snitcr.go.cr):
    1. python scripts/extraer_dta.py <PDF nuevo> --edicion <año> --url <url del PDF>
    2. python scripts/generar_api.py
    3. python scripts/generar_imagen_og.py
    4. Actualizar la edición y los totales en public/index.html, public/en/index.html, public/llms.txt y
       public/openapi.json, y la fecha en public/sitemap.xml
    5. python scripts/validar.py
Si una corrección ya no aplica (por ejemplo, el IGN agregó Duacarí a la tabla), el script
lo avisa: hay que quitarla de data/correcciones.json.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

import pdfplumber

RAIZ = Path(__file__).resolve().parent.parent
AREA = r'(\d[\d.]*(?:,\d+)?)'

RE_TOTAL = re.compile(r'^(Provincias|Cantones|Distritos) (\d+)$')
RE_PROVINCIA = re.compile(rf'^160103 (\d) (.+) {AREA}$')
RE_CANTON = re.compile(rf'^160104 (\d) .+? (\d)(\d\d) (.+) {AREA}$')
RE_DISTRITO = re.compile(rf'^160105 (\d) .+? (\d)(\d\d) (.+?) \2(\d\d)(\d\d) (.+) {AREA}$')


def area(texto):
    return float(texto.replace('.', '').replace(',', '.'))


def leer_pdf(ruta):
    totales, provincias, cantones, distritos = {}, {}, {}, {}
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            for linea in (pagina.extract_text() or '').splitlines():
                linea = linea.strip()
                if m := RE_TOTAL.match(linea):
                    totales[m[1].lower()] = int(m[2])
                elif m := RE_PROVINCIA.match(linea):
                    provincias[m[1]] = {'nombre': m[2], 'area_km2': area(m[3])}
                elif m := RE_CANTON.match(linea):
                    cantones[f'{m[2]}{m[3]}'] = {'nombre': m[4], 'area_km2': area(m[5])}
                elif m := RE_DISTRITO.match(linea):
                    distritos[f'{m[2]}{m[3]}{m[6]}'] = {'nombre': m[7], 'area_km2': area(m[8])}
    return totales, provincias, cantones, distritos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--edicion', required=True)
    ap.add_argument('--url', required=True)
    args = ap.parse_args()

    totales, provincias, cantones, distritos = leer_pdf(args.pdf)
    correcciones = json.loads((RAIZ / 'data/correcciones.json').read_text(encoding='utf-8'))

    for c in correcciones['agregar_distritos']:
        assert c['codigo'] not in distritos, f"{c['codigo']} ya viene en el PDF; quitar la corrección"
        distritos[c['codigo']] = {'nombre': c['nombre'], 'area_km2': c['area_km2']}
    for c in correcciones['renombrar']:
        tabla = {'canton': cantones, 'distrito': distritos}[c['tipo']]
        assert tabla[c['codigo']]['nombre'] == c['de'], f"{c['codigo']}: el PDF ya no dice '{c['de']}'"
        tabla[c['codigo']]['nombre'] = c['a']

    arbol = []
    for p, prov in sorted(provincias.items()):
        lista_cantones = []
        for cc, canton in sorted(cantones.items(), key=lambda kv: int(kv[0])):
            if cc[0] != p:
                continue
            lista_distritos = [
                {'codigo': dd, **distrito}
                for dd, distrito in sorted(distritos.items(), key=lambda kv: int(kv[0]))
                if dd[:3] == cc
            ]
            lista_cantones.append({'codigo': cc, **canton, 'distritos': lista_distritos})
        arbol.append({'codigo': p, **prov, 'cantones': lista_cantones})

    salida = {
        'fuente': {
            'nombre': f'División Territorial Administrativa {args.edicion}',
            'institucion': 'Instituto Geográfico Nacional (IGN), Registro Nacional de Costa Rica',
            'edicion': args.edicion,
            'url': args.url,
            'totales_oficiales': totales,
            'extraido': date.today().isoformat(),
        },
        'provincias': arbol,
    }
    (RAIZ / 'data/dta.json').write_text(json.dumps(salida, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(provincias)} provincias, {len(cantones)} cantones, {len(distritos)} distritos '
          f'(totales oficiales: {totales})')


if __name__ == '__main__':
    main()
