"""Genera public/og.png, la imagen que muestran redes sociales y chats al compartir el enlace.

Uso:
    pip install pillow
    python scripts/generar_imagen_og.py [--fuentes CARPETA]

Lee los totales de data/dta.json, así que hay que volver a correrlo cuando cambie la edición.
Usa Fraunces, Geist y Geist Mono (OFL, Google Fonts). Por defecto las busca en ~/Library/Fonts.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
# Paleta de la identidad visual
FONDO, TARJETA, LINEA, TENUE, TEXTO, ACENTO = '#0B0B0D', '#151519', '#26262E', '#8A8A96', '#FAFAFA', '#FFD231'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fuentes', default=str(Path.home() / 'Library/Fonts'))
    args = ap.parse_args()
    carpeta = Path(args.fuentes)

    def fraunces(tam, peso=500):
        f = ImageFont.truetype(str(carpeta / 'Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf'), tam)
        f.set_variation_by_axes([min(tam, 144), peso, 0, 0])  # opsz, wght, SOFT, WONK
        return f

    def geist(tam, peso=400, mono=False):
        nombre = 'GeistMono-VariableFont_wght.ttf' if mono else 'Geist-VariableFont_wght.ttf'
        f = ImageFont.truetype(str(carpeta / nombre), tam)
        f.set_variation_by_axes([peso])
        return f

    dta = json.loads((RAIZ / 'data/dta.json').read_text(encoding='utf-8'))
    cantones = sum(len(p['cantones']) for p in dta['provincias'])
    distritos = sum(len(c['distritos']) for p in dta['provincias'] for c in p['cantones'])
    totales = [(len(dta['provincias']), 'PROVINCIAS'), (cantones, 'CANTONES'), (distritos, 'DISTRITOS')]

    img = Image.new('RGB', (1200, 630), FONDO)
    d = ImageDraw.Draw(img)
    x = 80

    d.text((x, 80), 'API JSON GRATUITA', font=geist(24, 500, mono=True), fill=ACENTO)
    d.text((x, 130), 'Ubicaciones de Costa Rica', font=fraunces(76), fill=TEXTO)
    d.text((x, 240), 'Provincias, cantones, distritos y códigos postales', font=geist(36), fill=TENUE)

    y, cx = 345, x
    for valor, etiqueta in totales:
        d.rounded_rectangle((cx, y, cx + 300, y + 140), radius=16, fill=TARJETA, outline=LINEA, width=2)
        d.text((cx + 26, y + 18), str(valor), font=geist(64, 500, mono=True), fill=ACENTO)
        d.text((cx + 26, y + 98), etiqueta, font=geist(20, 400, mono=True), fill=TENUE)
        cx += 330

    edicion = dta['fuente']['edicion']
    d.text((x, 540), f'Datos oficiales: División Territorial Administrativa {edicion}, IGN',
           font=geist(24), fill=TENUE)

    img.save(RAIZ / 'public/og.png', optimize=True)
    print('Generado public/og.png')


if __name__ == '__main__':
    main()
