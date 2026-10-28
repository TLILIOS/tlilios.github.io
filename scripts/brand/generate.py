#!/usr/bin/env python3
"""Fichiers de marque publiés (brief marque §5), régénérés depuis les SVG validés (planche V1, option A).

Usage :
  .venv-brand/bin/python scripts/brand/generate.py

Idempotent : mêmes sources, mêmes octets (rendu librsvg, PNG sans horodatage). Sources :
docs/brand/source/*.svg. Sorties à la racine de public/, URL stables sans empreinte ni paramètre :
  favicon.ico          16, 32, 48 px — variante simplifiée (affichée à 18 px par Google)
  favicon.svg          variante simplifiée, en fichier
  favicon-96x96.png    variante simplifiée
  apple-touch-icon.png 180 px, carré plein et opaque (iOS applique son masque)
  icon-192.png         tuile, purpose "any"
  icon-512.png         tuile, purpose "any"
  icon-maskable-512.png plein cadre opaque, emblème inscrit dans le cercle central de rayon 40 %
  prim-logo-512.png    tuile, logo des données structurées
  og-image.png         1200 × 630 : emblème et PRIM en or, centrés, sur le fond sombre du site
Compression PNG sans perte (zlib 9). Budgets : .ico ≤ 15 Ko, PNG ≤ 512 px ≤ 100 Ko, og-image ≤ 300 Ko.
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

import geometry as geo
import reference as ref

SOURCE = ref.ROOT / "docs" / "brand" / "source"
REPORT = ref.ROOT / "docs" / "brand" / "fit-report.json"
PUBLIC = ref.ROOT / "public"
SITE_BG = "#08090c"                 # --bg-deep, theme-color du site
OG_W, OG_H = 1200, 630
MASKABLE_SAFE = 0.40                # rayon de la zone sûre des icônes maskable (fraction du côté)
BUDGET = {"favicon.ico": 15 * 1024, "og-image.png": 300 * 1024}
PNG_BUDGET = 100 * 1024


def source(name: str) -> str:
    """SVG validé, sans le commentaire d'en-tête (attribution conservée dans docs/brand/source/)."""
    return re.sub(r"<!--.*?-->\n?", "", (SOURCE / name).read_text(encoding="utf-8"), flags=re.S)


def render(svg: str, w: int, h: int | None = None) -> Image.Image:
    return Image.fromarray(geo.rsvg_png(svg, w, h or w))


def png_bytes(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def path_d(svg: str) -> list[str]:
    return re.findall(r'<path fill="[^"]+" d="([^"]+)"', svg)


def opaque(im: Image.Image) -> Image.Image:
    """RGB sans canal alpha : refuse toute transparence résiduelle."""
    a = np.asarray(im)
    if a.shape[-1] == 4 and a[..., 3].min() < 255:
        raise ValueError("image censée être opaque")
    return im.convert("RGB")


def square_tile(fill_bg: str, fill_fg: str, d: str, scale: float, center: tuple[float, float], side: int = 512) -> str:
    """Carré plein (sans coins arrondis) portant l'emblème mis à l'échelle autour de `center`."""
    s = scale
    tx, ty = 0.5 * side - s * center[0], 0.5 * side - s * center[1]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" width="{side}" height="{side}">'
            f'<rect width="{side}" height="{side}" fill="{fill_bg}"/>'
            f'<path fill="{fill_fg}" transform="translate({tx:.4f} {ty:.4f}) scale({s:.6f})" d="{d}"/></svg>')


def enclosing(d: str) -> tuple[tuple[float, float], float]:
    """Plus petit cercle centré sur l'axe vertical contenant le contour (bouclier symétrique) :
    recherche du centre en y, x fixé au milieu de l'emprise."""
    pts = np.vstack([geo.polyline(p, 0.25) for p in parse_paths(d)])
    cx = 0.5 * (pts[:, 0].min() + pts[:, 0].max())
    lo, hi = pts[:, 1].min(), pts[:, 1].max()
    radius = lambda cy: float(np.hypot(pts[:, 0] - cx, pts[:, 1] - cy).max())
    for _ in range(80):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        lo, hi = (lo, m2) if radius(m1) < radius(m2) else (m1, hi)
    cy = 0.5 * (lo + hi)
    return (cx, cy), radius(cy)


def parse_paths(d: str) -> list[geo.Path]:
    """Relit un chemin M/H/V/L/A/Z produit par construct.py en objets geometry.Path."""
    toks = re.findall(r"[MHVLAZ]|-?(?:\d+\.?\d*|\.\d+)", d)
    out, i, path, cur = [], 0, None, None
    while i < len(toks):
        c = toks[i]
        i += 1
        if c == "M":
            cur = np.array([float(toks[i]), float(toks[i + 1])]); i += 2
            path = geo.Path(cur)
        elif c == "H":
            cur = np.array([float(toks[i]), cur[1]]); i += 1; path.L(cur)
        elif c == "V":
            cur = np.array([cur[0], float(toks[i])]); i += 1; path.L(cur)
        elif c == "L":
            cur = np.array([float(toks[i]), float(toks[i + 1])]); i += 2; path.L(cur)
        elif c == "A":
            r, _, _, large, sweep, x, y = (float(t) for t in toks[i:i + 7]); i += 7
            p1 = np.array([x, y])
            path.A(arc_center(cur, p1, r, int(large), int(sweep)), p1, int(sweep))
            cur = p1
        elif c == "Z":
            out.append(path.close())
    return out


def arc_center(p0, p1, r: float, large: int, sweep: int) -> np.ndarray:
    """Centre d'un arc circulaire SVG (A r r 0 large sweep x y)."""
    m = 0.5 * (p0 + p1)
    v = p1 - p0
    q = float(np.hypot(*v))
    h = np.sqrt(max(r * r - 0.25 * q * q, 0.0))
    n = np.array([-v[1], v[0]]) / q
    # y vers le bas : sweep = 1 (sens horaire à l'écran) avec petit arc → centre à droite du segment.
    sign = 1.0 if (sweep == 1) != (large == 1) else -1.0
    return m + sign * h * n


def og_image(blue: str, gold: str, report: dict) -> Image.Image:
    """Fond sombre du site, halo bleu discret ; emblème au-dessus de PRIM, en or, dans le carré
    central de 630 px, aux proportions de la maquette (hauteur de PRIM et interligne rapportés à
    l'emblème). Aucun autre texte (« Craft at prime. » ne figurait pas sur l'ancienne image)."""
    mono = source("prim-monogram.svg")
    word = source("prim-wordmark.svg")
    mw, mh = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', mono).groups())
    ww, wh = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', word).groups())
    pw, pe = report["wordmark"]["params"], report["emblem"]["fitted"]
    emb_h = 290.0                                   # pixels
    word_h = emb_h * (pw["yb"] - pw["yt"]) / mh     # capitale de PRIM / hauteur de l'emblème
    gap = emb_h * (pw["yt"] - pe["pt"]) / mh        # pointe du bouclier → haut de PRIM
    total = emb_h + gap + word_h
    y0 = 0.5 * (OG_H - total)
    se, sw = emb_h / mh, word_h / wh
    ex, wx = 0.5 * (OG_W - mw * se), 0.5 * (OG_W - ww * sw)
    if max(mw * se, ww * sw) > 630 or total > 630:
        raise ValueError("composition hors du carré central de 630 px")
    emb = "".join(f'<path fill="{gold}" d="{d}"/>' for d in path_d(mono))
    wrd = "".join(f'<path fill="{gold}" d="{d}"/>' for d in path_d(word))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {OG_W} {OG_H}" width="{OG_W}" height="{OG_H}">'
           f'<defs><radialGradient id="halo" cx="{OG_W / 2}" cy="{y0 + emb_h * 0.45:.1f}" r="560" gradientUnits="userSpaceOnUse">'
           # Décroissance en cloche (paliers intermédiaires) : pas d'arc visible en fin de halo.
           + "".join(f'<stop offset="{o}" stop-color="{blue}" stop-opacity="{a}"/>'
                     for o, a in ((0, 0.42), (0.3, 0.3), (0.55, 0.15), (0.8, 0.04), (1, 0)))
           + f'</radialGradient></defs>'
           f'<rect width="{OG_W}" height="{OG_H}" fill="{SITE_BG}"/><rect width="{OG_W}" height="{OG_H}" fill="url(#halo)"/>'
           f'<g transform="translate({ex:.3f} {y0:.3f}) scale({se:.6f})">{emb}</g>'
           f'<g transform="translate({wx:.3f} {y0 + emb_h + gap:.3f}) scale({sw:.6f})">{wrd}</g></svg>')
    return opaque(render(svg, OG_W, OG_H))


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    blue, gold = report["palette"]["shield_blue"]["hex"], report["palette"]["gold"]["hex"]
    tile, small = source("prim-tile-a.svg"), source("prim-tile-a-small.svg")
    mono = source("prim-monogram.svg")
    d_mono = "".join(path_d(mono))
    out: dict[str, bytes] = {}

    # Variante simplifiée : tout ce que Google ou un onglet affiche à ≤ 32 px CSS.
    frames = {s: render(small, s) for s in (16, 32, 48)}
    buf = io.BytesIO()
    frames[48].save(buf, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[frames[16], frames[32]])
    out["favicon.ico"] = buf.getvalue()
    out["favicon.svg"] = small.encode("utf-8")
    out["favicon-96x96.png"] = png_bytes(render(small, 96))

    # Dessin standard : mêmes proportions que la tuile (bouclier à 75 % du côté).
    mw, mh = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', mono).groups())
    s_tile = 512 * 0.75 / mh
    out["apple-touch-icon.png"] = png_bytes(opaque(render(square_tile(blue, gold, d_mono, s_tile, (mw / 2, mh / 2)), 180)))
    for px in (192, 512):
        out[f"icon-{px}.png"] = png_bytes(render(tile, px))
    (cx, cy), r = enclosing(d_mono)
    s_mask = (MASKABLE_SAFE * 512 - 1.0) / r               # 1 px de marge pour l'anticrénelage
    out["icon-maskable-512.png"] = png_bytes(opaque(render(square_tile(blue, gold, d_mono, s_mask, (cx, cy)), 512)))
    out["prim-logo-512.png"] = png_bytes(render(tile, 512))
    out["og-image.png"] = png_bytes(og_image(blue, gold, report))

    for name, data in out.items():
        limit = BUDGET.get(name, PNG_BUDGET if name.endswith(".png") else None)
        if limit is not None and len(data) > limit:
            raise SystemExit(f"✗ {name} : {len(data)} octets > budget {limit}")
        target = PUBLIC / name
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
            state = "écrit"
        else:
            state = "inchangé"
        print(f"✓ public/{name} — {len(data) / 1024:.1f} Ko ({state})")


if __name__ == "__main__":
    main()
