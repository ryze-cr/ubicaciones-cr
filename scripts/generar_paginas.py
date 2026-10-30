"""Genera las páginas web por provincia, cantón y distrito (español e inglés), el índice del buscador y el sitemap.

Uso:
    python scripts/generar_paginas.py

Solo usa la biblioteca estándar. Lee data/dta.json y data/gam.json y escribe en public/:
  - /{provincia}/, /{provincia}/{canton}/ y /{provincia}/{canton}/{distrito}/ (y lo mismo bajo /en/)
  - /cantones-de-costa-rica/, /distritos-de-costa-rica/ y sus versiones en inglés
  - /buscador.json: índice que usa el buscador de la página principal
  - /sitemap.xml con todas las páginas y sus versiones en el otro idioma
  - el bloque de provincias y cantones entre los marcadores <!-- provincias:inicio --> y <!-- provincias:fin -->
    de public/index.html y public/en/index.html
Borra y vuelve a crear las carpetas que genera; no toca el resto de public/.
"""
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLIC = RAIZ / 'public'
SITIO = 'https://ubicaciones-cr.ryze-cr.workers.dev'
# Fecha de última modificación que se publica en el sitemap. Subirla cuando cambie el contenido de las páginas.
ACTUALIZADO = '2026-10-30'
LISTAS = {'es': ('cantones-de-costa-rica', 'distritos-de-costa-rica'), 'en': ('cantons-of-costa-rica', 'districts-of-costa-rica')}
GITHUB_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>')

T = {
    'es': {
        'inicio': 'Código postal de Costa Rica',
        'otro_idioma': 'English',
        'gam_si': 'GAM', 'gam_no': 'Fuera de la GAM',
        'gam_frase_si': 'Pertenece a la Gran Área Metropolitana (GAM).',
        'gam_frase_no': 'Está fuera de la Gran Área Metropolitana (GAM).',
        'copiar': 'Copiar',
        'buscar_otro': 'Buscar otro código postal',
        'pie': ('<p>Un proyecto de Flashout Labs. Hecho gracias a <a href="https://github.com/ryze-cr" target="_blank" rel="noopener">Carl De Pass</a>.</p>\n'
                '    <p>Datos: Instituto Geográfico Nacional, Registro Nacional de Costa Rica (División Territorial Administrativa 2026).</p>\n'
                '    <p>Código abierto bajo licencia MIT · <a href="https://github.com/ryze-cr/ubicaciones-cr" target="_blank" rel="noopener">GitHub</a> · '
                '<a href="/#api">API gratuita</a></p>'),
        'cols_distritos': ('Código postal', 'Distrito', 'Zona'),
    },
    'en': {
        'inicio': 'Costa Rica postal codes',
        'otro_idioma': 'Español',
        'gam_si': 'GAM', 'gam_no': 'Outside the GAM',
        'gam_frase_si': 'It is part of the Greater Metropolitan Area (GAM).',
        'gam_frase_no': 'It is outside the Greater Metropolitan Area (GAM).',
        'copiar': 'Copy',
        'buscar_otro': 'Look up another postal code',
        'pie': ('<p>A Flashout Labs project. Made by <a href="https://github.com/ryze-cr" target="_blank" rel="noopener">Carl De Pass</a>.</p>\n'
                '    <p>Data: National Geographic Institute (IGN), National Registry of Costa Rica (2026 Administrative Territorial Division).</p>\n'
                '    <p>Open source under the MIT license · <a href="https://github.com/ryze-cr/ubicaciones-cr" target="_blank" rel="noopener">GitHub</a> · '
                '<a href="/en/#api">Free API</a></p>'),
        'cols_distritos': ('Postal code', 'District', 'Zone'),
    },
}

e = html.escape


def slug(texto):
    s = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def ruta(lang, *partes):
    base = '/en/' if lang == 'en' else '/'
    return base + ''.join(f'{p}/' for p in partes)


def otro(lang):
    return 'en' if lang == 'es' else 'es'


def cabeza(lang, titulo, descripcion, partes, jsonld):
    """<head> común: SEO, idiomas alternos, Open Graph y datos estructurados."""
    url_es, url_en = SITIO + ruta('es', *partes), SITIO + ruta('en', *partes)
    url = url_en if lang == 'en' else url_es
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="es" href="{url_es}">
<link rel="alternate" hreflang="en" href="{url_en}">
<link rel="alternate" hreflang="x-default" href="{url_es}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0B0B0D">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'en_US' if lang == 'en' else 'es_CR'}">
<meta property="og:site_name" content="Flashout Labs">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITIO}/og.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&family=Geist:wght@400;500&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/estilos.css">
</head>
'''


def migas_jsonld(migas):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': nombre, 'item': SITIO + url} for i, (nombre, url) in enumerate(migas)]}


def cuerpo(lang, partes, migas, contenido):
    """<body> común: selector de idioma, migas de pan, contenido y pie."""
    t = T[lang]
    # Cada separador va unido al elemento que le sigue, para que nunca quede colgando al final de una línea
    piezas = [f'<a href="{url}">{e(nombre)}</a>' if i < len(migas) - 1 else f'<span aria-current="page">{e(nombre)}</span>'
              for i, (nombre, url) in enumerate(migas)]
    nav_migas = piezas[0] + ''.join(f'<span class="miga"><span aria-hidden="true">›</span> {p}</span>' for p in piezas[1:])
    actual_es = ' aria-current="page"' if lang == 'es' else ''
    actual_en = ' aria-current="page"' if lang == 'en' else ''
    return f'''<body>
<div class="wrap">
  <header class="pagina">
    <nav class="idiomas" aria-label="Idioma / Language">
      <a href="{ruta('es', *partes)}" lang="es" hreflang="es"{actual_es}>Español</a>
      <a href="{ruta('en', *partes)}" lang="en" hreflang="en"{actual_en}>English</a>
    </nav>
    <nav class="migas" aria-label="{'Breadcrumb' if lang == 'en' else 'Ruta'}">{nav_migas}</nav>
  </header>
{contenido}
  <p class="buscar-otro"><a href="{ruta(lang)}">← {t['buscar_otro']}</a></p>
  <footer>
    {t['pie']}
  </footer>
</div>
<script src="/pagina.js" defer></script>
</body>
</html>
'''


def etiqueta(lang, gam, extra=''):
    clases = 'etiqueta-gam' + (' si' if gam else '') + (f' {extra}' if extra else '')
    return f'<span class="{clases}">{T[lang]["gam_si"] if gam else T[lang]["gam_no"]}</span>'


def celda_distrito(lang, url, d, detalle=''):
    """Nombre del distrito con su detalle y su zona, que en celular reemplazan a las columnas que se ocultan."""
    sub = f'<span class="sub">{e(detalle)}</span>' if detalle else ''
    return f'<td><a href="{url}">{e(d["nombre"])}</a>{sub}{etiqueta(lang, d["gam"], "sub-gam")}</td>'


def tabla_distritos(lang, p, c):
    filas = ''.join(
        f'\n      <tr><td><code>{d["codigo"]}</code></td>{celda_distrito(lang, ruta(lang, p["slug"], c["slug"], d["slug"]), d)}'
        f'<td>{etiqueta(lang, d["gam"])}</td></tr>' for d in c['distritos'])
    cols = ''.join(f'<th>{x}</th>' for x in T[lang]['cols_distritos'])
    return f'''<div class="table-scroll">
    <table class="tabla-distritos con-zona">
      <thead><tr>{cols}</tr></thead>
      <tbody>{filas}
      </tbody>
    </table>
    </div>'''


def escribir(rel, texto):
    destino = PUBLIC / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding='utf-8')


def pagina_distrito(lang, p, c, d, hermanos):
    partes = (p['slug'], c['slug'], d['slug'])
    area = f"{d['area_km2']:.1f} km²".replace('.', ',' if lang == 'es' else '.') if d['area_km2'] is not None else '—'
    gam_txt = T[lang]['gam_frase_si'] if d['gam'] else T[lang]['gam_frase_no']
    direccion = f"{d['nombre']}, {c['nombre']}, {p['nombre']}, {d['codigo']}, Costa Rica"
    if lang == 'es':
        titulo = f"Código postal de {d['nombre']}, {c['nombre']}: {d['codigo']}"
        desc = (f"El código postal de {d['nombre']} (cantón {c['nombre']}, provincia {p['nombre']}, Costa Rica) es {d['codigo']}. "
                f"{gam_txt} Datos oficiales del IGN, DTA 2026.")
        h1 = f"Código postal de {d['nombre']}, {c['nombre']}"
        frase = (f"El código postal de <b>{e(d['nombre'])}</b>, distrito del cantón {e(c['nombre'])} en la provincia de "
                 f"{e(p['nombre'])}, es <b>{d['codigo']}</b>. {gam_txt}")
        etiquetas = ('Provincia', 'Cantón', 'Distrito', 'Código postal', 'Zona', 'Área')
        h2_dir, p_dir = 'Cómo escribirlo en una dirección', 'Para envíos y formularios (incluidos los que piden "zip code"), usá el código de 5 dígitos:'
        h2_otros = f"Otros distritos de {c['nombre']}"
        api = f'¿Lo necesitás en tu sistema? Este dato está en la <a href="/#api">API gratuita</a>: <code>/codigo-postal/{d["codigo"]}.json</code>'
    else:
        titulo = f"{d['nombre']}, {c['nombre']} postal code (ZIP): {d['codigo']}"
        desc = (f"The postal code (ZIP code) of {d['nombre']}, in the canton of {c['nombre']}, {p['nombre']} province, Costa Rica, is "
                f"{d['codigo']}. {gam_txt} Official IGN data, DTA 2026.")
        h1 = f"{d['nombre']}, {c['nombre']} postal code"
        frase = (f"The postal code (ZIP code) of <b>{e(d['nombre'])}</b>, a district of the canton of {e(c['nombre'])} in "
                 f"{e(p['nombre'])} province, is <b>{d['codigo']}</b>. {gam_txt}")
        etiquetas = ('Province', 'Canton', 'District', 'Postal code', 'Zone', 'Area')
        h2_dir, p_dir = 'How to write it in an address', 'For shipping and online forms that ask for a "ZIP code", use the 5-digit code:'
        h2_otros = f"Other districts in {c['nombre']}"
        api = f'Need it in your system? This data is in the <a href="/en/#api">free API</a>: <code>/codigo-postal/{d["codigo"]}.json</code>'
    migas = [(T[lang]['inicio'], ruta(lang)), (p['nombre'], ruta(lang, p['slug'])), (c['nombre'], ruta(lang, p['slug'], c['slug'])),
             (d['nombre'], ruta(lang, *partes))]
    jsonld = {'@context': 'https://schema.org', '@graph': [migas_jsonld(migas), {
        '@type': 'Place', 'name': f"{d['nombre']}, {c['nombre']}, {p['nombre']}, Costa Rica", 'url': SITIO + ruta(lang, *partes),
        'address': {'@type': 'PostalAddress', 'postalCode': d['codigo'], 'addressLocality': d['nombre'],
                    'addressRegion': p['nombre'], 'addressCountry': 'CR'},
        'containedInPlace': {'@type': 'AdministrativeArea', 'name': f"{c['nombre']}, {p['nombre']}"}}]}
    valores = (p['nombre'], c['nombre'], d['nombre'], f'<code>{d["codigo"]}</code>', etiqueta(lang, d['gam']), area)
    filas = ''.join(f'\n        <tr><th scope="row">{k}</th><td>{v if i in (3, 4) else e(v)}</td></tr>'
                    for i, (k, v) in enumerate(zip(etiquetas, valores)))
    otros = ''.join(f'\n      <li><a href="{ruta(lang, p["slug"], c["slug"], h["slug"])}">{e(h["nombre"])}</a> <code>{h["codigo"]}</code></li>'
                    for h in hermanos if h is not d)
    contenido = f'''  <main>
    <h1>{e(h1)}</h1>
    <div class="cp-ficha">
      <span class="cp" id="cp">{d['codigo']}</span>
      {etiqueta(lang, d['gam'])}
      <button type="button" class="copiar" data-copiar="{d['codigo']}">{T[lang]['copiar']}</button>
    </div>
    <p class="lede">{frase}</p>
    <table class="ficha">
      <tbody>{filas}
      </tbody>
    </table>
    <h2>{h2_dir}</h2>
    <p>{p_dir}</p>
    <div class="direccion"><code>{', '.join(f'<span class="nw">{e(x)}</span>' for x in direccion.split(', '))}</code> <button type="button" class="copiar" data-copiar="{e(direccion)}">{T[lang]['copiar']}</button></div>
    <h2>{e(h2_otros)}</h2>
    <ul class="enlaces">{otros}
    </ul>
    <p class="nota-api">{api}</p>
  </main>'''
    escribir(Path(ruta(lang, *partes).lstrip('/')) / 'index.html',
             cabeza(lang, titulo, desc, partes, jsonld) + cuerpo(lang, partes, migas, contenido))


def pagina_canton(lang, p, c):
    partes = (p['slug'], c['slug'])
    codigos = [d['codigo'] for d in c['distritos']]
    n, gam = len(c['distritos']), sum(d['gam'] for d in c['distritos'])
    if lang == 'es':
        titulo = f"Códigos postales de {c['nombre']}, {p['nombre']}"
        desc = (f"Los {n} distritos del cantón {c['nombre']} ({p['nombre']}, Costa Rica) con su código postal, del {codigos[0]} "
                f"al {codigos[-1]}. Datos oficiales del IGN, DTA 2026.")
        frase = (f"El cantón <b>{e(c['nombre'])}</b> ({c['codigo']}), en la provincia de {e(p['nombre'])}, tiene <b>{n} "
                 f"{'distrito' if n == 1 else 'distritos'}</b>. Sus códigos postales van del <code>{codigos[0]}</code> al <code>{codigos[-1]}</code>"
                 f"; {gam} de ellos {'está' if gam == 1 else 'están'} en la Gran Área Metropolitana.")
    else:
        titulo = f"{c['nombre']}, {p['nombre']} postal codes (ZIP codes)"
        desc = (f"The {n} districts of the canton of {c['nombre']} ({p['nombre']}, Costa Rica) with their postal codes, from "
                f"{codigos[0]} to {codigos[-1]}. Official IGN data, DTA 2026.")
        frase = (f"The canton of <b>{e(c['nombre'])}</b> ({c['codigo']}), in {e(p['nombre'])} province, has <b>{n} "
                 f"{'district' if n == 1 else 'districts'}</b>. Its postal codes range from <code>{codigos[0]}</code> to "
                 f"<code>{codigos[-1]}</code>; {gam} of them {'is' if gam == 1 else 'are'} in the Greater Metropolitan Area.")
    migas = [(T[lang]['inicio'], ruta(lang)), (p['nombre'], ruta(lang, p['slug'])), (c['nombre'], ruta(lang, *partes))]
    jsonld = {'@context': 'https://schema.org', '@graph': [migas_jsonld(migas)]}
    contenido = f'''  <main>
    <h1>{e(titulo)}</h1>
    <p class="lede">{frase}</p>
    {tabla_distritos(lang, p, c)}
  </main>'''
    escribir(Path(ruta(lang, *partes).lstrip('/')) / 'index.html',
             cabeza(lang, titulo, desc, partes, jsonld) + cuerpo(lang, partes, migas, contenido))


def pagina_provincia(lang, p):
    partes = (p['slug'],)
    nc, nd = len(p['cantones']), sum(len(c['distritos']) for c in p['cantones'])
    if lang == 'es':
        titulo = f"Códigos postales de la provincia de {p['nombre']}"
        desc = (f"Los {nc} cantones y {nd} distritos de {p['nombre']}, Costa Rica, con su código postal. "
                f"Los códigos de esta provincia empiezan con {p['codigo']}. Datos oficiales del IGN, DTA 2026.")
        frase = (f"La provincia de <b>{e(p['nombre'])}</b> tiene <b>{nc} cantones y {nd} distritos</b>. "
                 f"Todos sus códigos postales empiezan con <code>{p['codigo']}</code>.")
        canton_txt = 'Cantón'
    else:
        titulo = f"{p['nombre']} province postal codes (ZIP codes)"
        desc = (f"The {nc} cantons and {nd} districts of {p['nombre']}, Costa Rica, with their postal codes. "
                f"All codes in this province start with {p['codigo']}. Official IGN data, DTA 2026.")
        frase = (f"<b>{e(p['nombre'])}</b> province has <b>{nc} cantons and {nd} districts</b>. "
                 f"All of its postal codes start with <code>{p['codigo']}</code>.")
        canton_txt = 'Canton'
    migas = [(T[lang]['inicio'], ruta(lang)), (p['nombre'], ruta(lang, *partes))]
    jsonld = {'@context': 'https://schema.org', '@graph': [migas_jsonld(migas)]}
    bloques = ''.join(f'''
    <h2 id="{c['slug']}"><a href="{ruta(lang, p['slug'], c['slug'])}">{canton_txt} {e(c['nombre'])}</a></h2>
    {tabla_distritos(lang, p, c)}''' for c in p['cantones'])
    indice = '&nbsp;· '.join(f'<a href="#{c["slug"]}">{e(c["nombre"])}</a>' for c in p['cantones'])
    contenido = f'''  <main>
    <h1>{e(titulo)}</h1>
    <p class="lede">{frase}</p>
    <p class="indice-cantones">{indice}</p>{bloques}
  </main>'''
    escribir(Path(ruta(lang, *partes).lstrip('/')) / 'index.html',
             cabeza(lang, titulo, desc, partes, jsonld) + cuerpo(lang, partes, migas, contenido))


def rango(c):
    primero, ultimo = c['distritos'][0]['codigo'], c['distritos'][-1]['codigo']
    return f'<code>{primero}</code>' if primero == ultimo else f'<code>{primero}</code> – <code>{ultimo}</code>'


def paginas_lista(lang, provincias, n_cantones, n_distritos):
    cant_slug, dist_slug = LISTAS[lang]
    es = lang == 'es'
    # Cantones
    filas = ''.join(
        f'\n      <tr><td><a href="{ruta(lang, p["slug"], c["slug"])}">{e(c["nombre"])}</a>'
        f'<span class="sub">{e(p["nombre"])} · {len(c["distritos"])} {("distritos" if es else "districts") if len(c["distritos"]) != 1 else ("distrito" if es else "district")}</span></td>'
        f'<td>{e(p["nombre"])}</td><td>{len(c["distritos"])}</td>'
        f'<td class="rango">{rango(c)}</td></tr>'
        for p in provincias for c in p['cantones'])
    titulo = f'Los {n_cantones} cantones de Costa Rica y sus códigos postales' if es else f'The {n_cantones} cantons of Costa Rica and their postal codes'
    desc = (f'Lista de los {n_cantones} cantones de Costa Rica por provincia, con su cantidad de distritos y sus códigos postales. Datos oficiales del IGN, DTA 2026.'
            if es else f'List of the {n_cantones} cantons of Costa Rica by province, with their number of districts and postal codes. Official IGN data, DTA 2026.')
    cols = ('Cantón', 'Provincia', 'Distritos', 'Códigos postales') if es else ('Canton', 'Province', 'Districts', 'Postal codes')
    migas = [(T[lang]['inicio'], ruta(lang)), (f'{n_cantones} {"cantones" if es else "cantons"}', ruta(lang, cant_slug))]
    contenido = f'''  <main>
    <h1>{e(titulo)}</h1>
    <p class="lede">{'Costa Rica tiene' if es else 'Costa Rica has'} <b>7 {'provincias' if es else 'provinces'}, {n_cantones} {'cantones' if es else 'cantons'} {'y' if es else 'and'} {n_distritos} {'distritos' if es else 'districts'}</b>. {'Elegí un cantón para ver los códigos postales de sus distritos.' if es else 'Choose a canton to see the postal codes of its districts.'}</p>
    <div class="table-scroll">
    <table class="tabla-distritos tabla-cantones">
      <thead><tr>{''.join(f'<th>{x}</th>' for x in cols)}</tr></thead>
      <tbody>{filas}
      </tbody>
    </table>
    </div>
  </main>'''
    jsonld = {'@context': 'https://schema.org', '@graph': [migas_jsonld(migas)]}
    escribir(Path(ruta(lang, cant_slug).lstrip('/')) / 'index.html',
             cabeza_lista(lang, titulo, desc, 0, jsonld) + cuerpo_lista(lang, 0, migas, contenido))
    # Distritos
    filas = ''.join(
        f'\n      <tr><td><code>{d["codigo"]}</code></td>'
        f'{celda_distrito(lang, ruta(lang, p["slug"], c["slug"], d["slug"]), d, c["nombre"] + " · " + p["nombre"])}'
        f'<td>{e(c["nombre"])}</td><td>{e(p["nombre"])}</td><td>{etiqueta(lang, d["gam"])}</td></tr>'
        for p in provincias for c in p['cantones'] for d in c['distritos'])
    titulo = f'Los {n_distritos} distritos de Costa Rica con su código postal' if es else f'All {n_distritos} districts of Costa Rica with their postal code'
    desc = (f'Lista completa de los {n_distritos} distritos de Costa Rica con su código postal, cantón, provincia y zona GAM. Datos oficiales del IGN, DTA 2026.'
            if es else f'Complete list of the {n_distritos} districts of Costa Rica with their postal code (ZIP code), canton, province and GAM zone. Official IGN data, DTA 2026.')
    cols = ('Código postal', 'Distrito', 'Cantón', 'Provincia', 'Zona') if es else ('Postal code', 'District', 'Canton', 'Province', 'Zone')
    migas = [(T[lang]['inicio'], ruta(lang)), (f'{n_distritos} {"distritos" if es else "districts"}', ruta(lang, dist_slug))]
    contenido = f'''  <main>
    <h1>{e(titulo)}</h1>
    <p class="lede">{'El código postal de Costa Rica tiene 5 dígitos: provincia (1), cantón (2) y distrito (2).' if es else 'Costa Rican postal codes have 5 digits: province (1), canton (2) and district (2).'}</p>
    <div class="table-scroll">
    <table class="tabla-distritos tabla-lista con-zona">
      <thead><tr>{''.join(f'<th>{x}</th>' for x in cols)}</tr></thead>
      <tbody>{filas}
      </tbody>
    </table>
    </div>
  </main>'''
    jsonld = {'@context': 'https://schema.org', '@graph': [migas_jsonld(migas)]}
    escribir(Path(ruta(lang, dist_slug).lstrip('/')) / 'index.html',
             cabeza_lista(lang, titulo, desc, 1, jsonld) + cuerpo_lista(lang, 1, migas, contenido))


def cabeza_lista(lang, titulo, desc, i, jsonld):
    """Las páginas de lista tienen slugs distintos por idioma, así que los alternos se calculan aparte."""
    h = cabeza(lang, titulo, desc, (), jsonld)
    for l in ('es', 'en'):
        h = h.replace(f'href="{SITIO}{ruta(l)}"', f'href="{SITIO}{ruta(l, LISTAS[l][i])}"')
    return h.replace(f'content="{SITIO}{ruta(lang)}"', f'content="{SITIO}{ruta(lang, LISTAS[lang][i])}"')


def cuerpo_lista(lang, i, migas, contenido):
    c = cuerpo(lang, (), migas, contenido)
    for l in ('es', 'en'):
        c = c.replace(f'<a href="{ruta(l)}" lang="{l}"', f'<a href="{ruta(l, LISTAS[l][i])}" lang="{l}"')
    return c


def bloque_inicio(lang, provincias):
    """Enlaces a todas las provincias y cantones para la página principal."""
    cant_slug, dist_slug = LISTAS[lang]
    items = ''.join(
        f'''
      <div class="provincia">
        <h3><a href="{ruta(lang, p['slug'])}">{e(p['nombre'])}</a> <code>{p['codigo']}</code></h3>
        <p>{'&nbsp;· '.join(f'<a href="{ruta(lang, p["slug"], c["slug"])}">{e(c["nombre"])}</a>' for c in p['cantones'])}</p>
      </div>''' for p in provincias)
    ver = (f'<a href="{ruta(lang, cant_slug)}">Ver los 84 cantones</a> · <a href="{ruta(lang, dist_slug)}">Ver los 494 distritos</a>'
           if lang == 'es' else f'<a href="{ruta(lang, cant_slug)}">See all 84 cantons</a> · <a href="{ruta(lang, dist_slug)}">See all 494 districts</a>')
    return f'''<!-- provincias:inicio -->
    <div class="provincias">{items}
    </div>
    <p class="ver-listas">{ver}</p>
    <!-- provincias:fin -->'''


def main():
    dta = json.loads((RAIZ / 'data/dta.json').read_text(encoding='utf-8'))
    en_gam = set(json.loads((RAIZ / 'data/gam.json').read_text(encoding='utf-8'))['gam'])
    provincias = dta['provincias']
    for p in provincias:
        p['slug'] = slug(p['nombre'])
        for c in p['cantones']:
            c['slug'] = slug(c['nombre'])
            for d in c['distritos']:
                d['slug'] = slug(d['nombre'])
                d['gam'] = d['codigo'] in en_gam
            assert len({d['slug'] for d in c['distritos']}) == len(c['distritos']), f"slugs repetidos en {c['nombre']}"
        assert len({c['slug'] for c in p['cantones']}) == len(p['cantones']), f"slugs repetidos en {p['nombre']}"

    # Borrar lo generado antes
    for lang in ('es', 'en'):
        base = PUBLIC / ('en' if lang == 'en' else '')
        for nombre in [p['slug'] for p in provincias] + list(LISTAS[lang]):
            if (base / nombre).is_dir():
                shutil.rmtree(base / nombre)

    n_cantones = sum(len(p['cantones']) for p in provincias)
    n_distritos = sum(len(c['distritos']) for p in provincias for c in p['cantones'])
    urls = [()]
    for lang in ('es', 'en'):
        for p in provincias:
            pagina_provincia(lang, p)
            for c in p['cantones']:
                pagina_canton(lang, p, c)
                for d in c['distritos']:
                    pagina_distrito(lang, p, c, d, c['distritos'])
        paginas_lista(lang, provincias, n_cantones, n_distritos)
        # Bloque de provincias en la página principal
        inicio = PUBLIC / ('en/index.html' if lang == 'en' else 'index.html')
        texto = inicio.read_text(encoding='utf-8')
        texto, n = re.subn(r'<!-- provincias:inicio -->.*?<!-- provincias:fin -->', lambda m: bloque_inicio(lang, provincias),
                           texto, flags=re.S)
        assert n == 1, f'faltan los marcadores de provincias en {inicio}'
        inicio.write_text(texto, encoding='utf-8')

    for p in provincias:
        urls.append((p['slug'],))
        for c in p['cantones']:
            urls.append((p['slug'], c['slug']))
            urls.extend((p['slug'], c['slug'], d['slug']) for d in c['distritos'])

    # Índice del buscador de la página principal
    indice = [{'c': d['codigo'], 'd': d['nombre'], 'k': c['nombre'], 'p': p['nombre'], 'g': int(d['gam']),
               'u': '/'.join(('', p['slug'], c['slug'], d['slug'], ''))}
              for p in provincias for c in p['cantones'] for d in c['distritos']]
    escribir('buscador.json', json.dumps(indice, ensure_ascii=False, separators=(',', ':')) + '\n')

    # Sitemap con las versiones en ambos idiomas
    def entrada(url_es, url_en):
        alternos = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{h}" href="{SITIO}{u}"/>'
                           for h, u in (('es', url_es), ('en', url_en), ('x-default', url_es)))
        return ''.join(f'''
  <url>
    <loc>{SITIO}{u}</loc>
    <lastmod>{ACTUALIZADO}</lastmod>{alternos}
  </url>''' for u in (url_es, url_en))
    pares = [(ruta('es', *u), ruta('en', *u)) for u in urls]
    pares += [(ruta('es', LISTAS['es'][i]), ruta('en', LISTAS['en'][i])) for i in (0, 1)]
    escribir('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + ''.join(entrada(*par) for par in pares) + '\n</urlset>\n')
    print(f'Generadas {len(pares) * 2} páginas en el sitemap ({n_distritos} distritos por idioma)')


if __name__ == '__main__':
    main()
