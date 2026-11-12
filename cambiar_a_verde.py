"""Cambia la paleta del sitio de violeta a verde (y deja el blanco como está).

Uso (desde la carpeta del proyecto, donde está app.py):
    python cambiar_a_verde.py            -> aplica el cambio
    python cambiar_a_verde.py --probar   -> solo muestra qué cambiaría, sin tocar nada

Antes de modificar un archivo guarda una copia en la carpeta "respaldo_colores".
Para volver atrás: copiá los archivos de "respaldo_colores" de vuelta a "static".
Es seguro correrlo dos veces: lo que ya es verde no se vuelve a tocar.
"""
import colorsys
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CARPETAS = [RAIZ / "static" / "css", RAIZ / "static" / "js"]
EXTENSIONES = {".css", ".js"}
RESPALDO = RAIZ / "respaldo_colores"

# Qué colores se consideran "violeta" (matiz en grados) y a cuál se pasan.
MATIZ_DESDE, MATIZ_HASTA = 225, 300
SATURACION_MINIMA = 0.06          # los grises puros (sin tinte) no se tocan
MATIZ_VERDE = 148                 # verde esmeralda
MATIZ_VERDE_CLARO = 140           # para fondos muy claros

HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def a_rgb(texto):
    h = texto.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    alfa = h[6:8] if len(h) == 8 else ""
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)), alfa


def luminancia(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def convertir(texto):
    """Devuelve el color en verde, o None si no es violeta."""
    rgb, alfa = a_rgb(texto)
    h, l, s = colorsys.rgb_to_hls(*rgb)
    grados = h * 360
    if not (MATIZ_DESDE <= grados <= MATIZ_HASTA) or s < SATURACION_MINIMA:
        return None

    lum = luminancia(rgb)
    # El verde se ve más oscuro que el violeta con la misma luminosidad:
    # lo aclaramos un poco para que el texto blanco siga leyéndose bien.
    objetivo = min(lum * 1.9, 0.2) if lum < 0.12 else lum
    matiz = (MATIZ_VERDE_CLARO if l >= 0.85 else MATIZ_VERDE) / 360
    sat = min(max(s, 0.30), 0.75) if s >= 0.35 else s

    bajo, alto = 0.0, 1.0
    for _ in range(40):                      # búsqueda binaria de luminosidad
        medio = (bajo + alto) / 2
        if luminancia(colorsys.hls_to_rgb(matiz, medio, sat)) < objetivo:
            bajo = medio
        else:
            alto = medio
    r, g, b = colorsys.hls_to_rgb(matiz, (bajo + alto) / 2, sat)
    return "#{:02x}{:02x}{:02x}{}".format(round(r * 255), round(g * 255), round(b * 255), alfa)


def procesar(texto):
    cambios = 0

    def cambiar(m):
        nonlocal cambios
        nuevo = convertir(m.group(0))
        if nuevo is None:
            return m.group(0)
        cambios += 1
        return nuevo

    return HEX.sub(cambiar, texto), cambios


def main():
    solo_probar = "--probar" in sys.argv
    if not (RAIZ / "static").is_dir():
        sys.exit("No encuentro la carpeta 'static'. Ejecutá este script desde la carpeta del proyecto (donde está app.py).")

    total = 0
    for carpeta in CARPETAS:
        for ruta in sorted(carpeta.glob("*")):
            if ruta.suffix not in EXTENSIONES:
                continue
            original = ruta.read_text(encoding="utf-8")
            nuevo, cambios = procesar(original)
            if not cambios:
                continue
            total += cambios
            rel = ruta.relative_to(RAIZ)
            print(f"{'(prueba) ' if solo_probar else ''}{rel}: {cambios} colores")
            if solo_probar:
                continue
            copia = RESPALDO / rel
            if not copia.exists():
                copia.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ruta, copia)
            ruta.write_text(nuevo, encoding="utf-8")

    if total == 0:
        print("No encontré colores violetas para cambiar (¿ya está en verde?).")
    elif solo_probar:
        print(f"\nCambiaría {total} colores. Corré sin --probar para aplicarlo.")
    else:
        print(f"\nListo: {total} colores cambiados. Copias originales en 'respaldo_colores'.")
        print("Recargá el navegador con Ctrl+F5.")


if __name__ == "__main__":
    main()