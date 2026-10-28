#!/usr/bin/env python3
"""Planche V1 (brief marque §4) → docs/brand/previews/v1-sheet.png.

Usage :
  .venv-brand/bin/python scripts/brand/sheet.py [--no-open]

Tout est recalculé depuis les SVG livrés (docs/brand/source/) : IoU et écarts contre les
masques de la maquette redressée, cotes de construction, rendus des tuiles. De la maquette,
la planche ne montre que des silhouettes (bouclier, PRIM) : signature et saphir exclus (§1).
Rendu : librsvg pour les icônes et les masques, Chrome sans interface (DPR 2) pour la mise en page.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import subprocess
import tempfile
from pathlib import Path as FsPath

import numpy as np
from PIL import Image

import emblem
import geometry as geo
import letters
import reference as ref
from construct import LIGHT, silhouette

SOURCE = ref.ROOT / "docs" / "brand" / "source"
REPORT = ref.ROOT / "docs" / "brand" / "fit-report.json"
MEASURES = ref.ROOT / "docs" / "brand" / "measurements.json"
OUT = ref.ROOT / "docs" / "brand" / "previews" / "v1-sheet.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SIZES = (16, 32, 48, 96, 180)
SMALL_MAX = 32                      # variante ≤ 32 px pour les rasters de 32 px et moins
BACKGROUNDS = (("blanc", "#ffffff"), ("gris clair", "#f1f3f4"), ("sombre (site)", "#08090c"), ("noir", "#000000"))
SITE_BG = "#08090c"


def fr(v: float, n: int = 2) -> str:
    return f"{v:.{n}f}".replace(".", ",")


# ---------------------------------------------------------------- lecture des SVG livrés

def path_ds(svg: str) -> list[str]:
    return re.findall(r'<path fill="[^"]+" d="([^"]+)"', svg)


def subpaths(d: str) -> list[str]:
    return ["M" + s for s in d.split("M") if s.strip()]


NUM = r"-?(?:\d+\.?\d*|\.\d+)"
TOKEN = re.compile(rf"[MHVLCAZ]|{NUM}")


def nodes(d: str) -> int:
    """Nœuds d'un chemin produit par construct.py : un par segment, fermeture droite comprise."""
    total = 0
    for sp in subpaths(d):
        toks = TOKEN.findall(sp)
        i, cur, start = 0, None, None
        while i < len(toks):
            c = toks[i]
            i += 1
            if c == "M":
                cur = start = (float(toks[i]), float(toks[i + 1]))
                i += 2
            elif c == "H":
                cur = (float(toks[i]), cur[1]); i += 1; total += 1
            elif c == "V":
                cur = (cur[0], float(toks[i])); i += 1; total += 1
            elif c == "L":
                cur = (float(toks[i]), float(toks[i + 1])); i += 2; total += 1
            elif c == "C":
                cur = (float(toks[i + 4]), float(toks[i + 5])); i += 6; total += 1
            elif c == "A":
                cur = (float(toks[i + 5]), float(toks[i + 6])); i += 7; total += 1
            elif c == "Z" and abs(cur[0] - start[0]) + abs(cur[1] - start[1]) > 1e-6:
                total += 1
    return total


def png_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def svg_uri(path: FsPath) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()


def raster(svg_path: FsPath, px: int) -> Image.Image:
    return Image.fromarray(geo.rsvg_png(svg_path.read_text(encoding="utf-8"), px, px))


def plane_render(ds: list[str], offset, box, shape, shear: float, pivot: float, stroke: float = 0.0) -> np.ndarray:
    """Couverture des chemins livrés (repère local + `offset`) sur la grille d'un masque du plan."""
    h, w = shape
    paint = f'fill="none" stroke="#000" stroke-width="{stroke}"' if stroke else 'fill="#000"'
    body = "".join(f'<path d="{d}" {paint}/>' for d in ds)
    tr = (f"scale({ref.SCALE}) translate({-box[0]} {-box[1]}) matrix(1 0 {shear} 1 {-shear * pivot} 0) "
          f"translate({offset[0]} {offset[1]})")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<g transform="{tr}">{body}</g></svg>')
    return geo.rsvg_png(svg, w, h)[..., 3] / 255.0


# ---------------------------------------------------------------- fidélité

def overlays(mask: np.ndarray, fit: np.ndarray, line: np.ndarray) -> tuple[str, str]:
    over = np.full(mask.shape + (3,), 255, np.uint8)
    over[mask] = (176, 190, 222)
    over[line] = (12, 26, 58)
    diff = np.full(mask.shape + (3,), 255, np.uint8)
    diff[mask & fit] = (214, 218, 226)
    diff[mask & ~fit] = (229, 72, 77)
    diff[fit & ~mask] = (0, 112, 243)
    return png_uri(Image.fromarray(over)), png_uri(Image.fromarray(diff))


def fidelity(report: dict) -> dict:
    rgb = ref.load_rgb()
    H, _, _ = ref.homography(rgb)
    out = {}
    # Emblème : origine du repère local retrouvée depuis les paramètres ajustés.
    _, mask, _ = ref.shield(rgb, H)
    p = emblem.regular(report["emblem"]["fitted"])
    ex0, ey0, _, _ = geo.bbox(emblem.build(p))
    ds = path_ds((SOURCE / "prim-monogram.svg").read_text(encoding="utf-8"))
    pivot = 0.5 * (ref.SHIELD_BOX[1] + ref.SHIELD_BOX[3])
    args = ((ex0, ey0), ref.SHIELD_BOX, mask.shape, p["shear"], pivot)
    fit = plane_render(ds, *args) >= 0.5
    line = plane_render(ds, *args, stroke=1.4) >= 0.35
    over, diff = overlays(mask, fit, line)
    out["emblem"] = {"iou": geo.iou(fit, mask), "iou_sil": geo.iou(silhouette(fit), silhouette(mask)),
                     "nodes": nodes(ds[0]), "ref_only": int((mask & ~fit).sum()), "fit_only": int((fit & ~mask).sum()),
                     "overlay": over, "diff": diff, "w": mask.shape[1]}
    # Mot-symbole : quatre chemins, IoU par lettre dans la fenêtre de chaque lettre.
    _, mask, _ = ref.word(rgb, H)
    pw = report["wordmark"]["params"]
    wx0, wy0, _, _ = geo.bbox(letters.build_all(pw))
    ds = path_ds((SOURCE / "prim-wordmark.svg").read_text(encoding="utf-8"))
    pivot = 0.5 * (ref.WORD_BOX[1] + ref.WORD_BOX[3])
    args = ((wx0, wy0), ref.WORD_BOX, mask.shape, pw["shear"], pivot)
    fit = plane_render(ds, *args) >= 0.5
    line = plane_render(ds, *args, stroke=1.4) >= 0.35
    over, diff = overlays(mask, fit, line)
    rows = {}
    for (k, build), d in zip(letters.LETTERS.items(), ds):
        x0, y0, x1, y1 = geo.bbox(build(pw))
        sel = np.zeros_like(mask)
        i0, i1 = int((y0 - ref.WORD_BOX[1] - 4) * ref.SCALE), int((y1 - ref.WORD_BOX[1] + 4) * ref.SCALE)
        j0, j1 = int((x0 - ref.WORD_BOX[0] - 4) * ref.SCALE), int((x1 - ref.WORD_BOX[0] + 4) * ref.SCALE)
        sel[max(i0, 0):i1, max(j0, 0):j1] = True
        rows[k] = {"iou": geo.iou(fit & sel, mask & sel), "nodes": nodes(d)}
    out["word"] = {"iou": geo.iou(fit, mask), "rows": rows, "overlay": over, "diff": diff, "w": mask.shape[1]}
    return out


# ---------------------------------------------------------------- construction cotée

def construction_svg(report: dict, blue: str) -> str:
    """Emblème cote en main : bandes t, contre-forme c, coupures g et gj, centres de la panse."""
    p = emblem.regular(report["emblem"]["fitted"])
    c = emblem.construct(p)
    paths = emblem.build(p)
    x0, y0, x1, y1 = geo.bbox(paths)
    d = "".join(geo.to_d(pp) for pp in paths)
    t, g, gj, cc = p["t"], p["g"], p["gj"], report["emblem"]["dims"]["counter_left"]
    uL = p["ax"] - p["hw"]
    vcb = p["vcb"]
    a = p["nu"] - p["nw"]
    C1, C2 = c["C1"], c["C2"]
    pts = c["points"]
    ink, mark = "#0c1a3a", "#c2410c"

    def dim(xa, ya, xb, yb, label, lx, ly, anchor="middle"):
        return (f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" stroke="{mark}" stroke-width="1.6"/>'
                f'<circle cx="{xa:.1f}" cy="{ya:.1f}" r="2.6" fill="{mark}"/><circle cx="{xb:.1f}" cy="{yb:.1f}" r="2.6" fill="{mark}"/>'
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="13" font-weight="650" fill="{mark}" '
                f'stroke="#fff" stroke-width="4" paint-order="stroke">{label}</text>')

    def center(q, label):
        return (f'<path d="M{q[0]-7:.1f} {q[1]:.1f}H{q[0]+7:.1f}M{q[0]:.1f} {q[1]-7:.1f}V{q[1]+7:.1f}" stroke="{ink}" stroke-width="1.4"/>'
                f'<text x="{q[0]+8:.1f}" y="{q[1]-8:.1f}" font-size="13" fill="{ink}" stroke="#fff" stroke-width="4" '
                f'paint-order="stroke">{label}</text>')

    yN = 0.5 * (p["nv"] - p["nh"] + vcb - 0.5 * t - g)
    marks = [dim(uL, 600, uL + t, 600, "t", uL + 0.5 * t, 592),
             dim(uL + t, 640, a, 640, "c", uL + t + 0.5 * cc, 632),
             dim(a + 0.5 * t, vcb - 0.5 * t - g, a + 0.5 * t, vcb - 0.5 * t, "g", a + t + 8, vcb - 0.5 * t - 1, "start"),
             center(C1, "C1"), center(C2, "C2"),
             f'<circle cx="{C1[0]:.1f}" cy="{C1[1]:.1f}" r="{c["R1"]:.1f}" fill="none" stroke="{ink}" stroke-width="1" stroke-dasharray="5 4"/>',
             f'<circle cx="{C2[0]:.1f}" cy="{C2[1]:.1f}" r="{c["R2"]:.1f}" fill="none" stroke="{ink}" stroke-width="1" stroke-dasharray="5 4"/>']
    h1, h2 = pts["H1"], pts["H2"]
    mid = 0.5 * (h1 + h2)
    r1o = c["R1"] + 0.5 * t
    k = (mid - C1) / np.hypot(*(mid - C1))
    pa, pb = C1 + r1o * k, C1 + (r1o + gj) * k
    marks.append(dim(pa[0], pa[1], pb[0], pb[1], "gj", pb[0] + 8, pb[1] - 6, "start"))
    pad = 36
    vb = f"{x0 - pad:.1f} {y0 - pad:.1f} {x1 - x0 + 2 * pad:.1f} {y1 - y0 + 2 * pad:.1f}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{int((x1 - x0 + 2 * pad) * 1.15)}" '
            f'font-family="-apple-system,Helvetica,Arial,sans-serif">'
            f'<path d="{d}" fill="{blue}" fill-opacity="0.16" stroke="{blue}" stroke-width="1.6"/>{"".join(marks)}</svg>')


# ---------------------------------------------------------------- HTML

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1400px;background:#f6f7f9;color:#14171f;font:15px/1.5 -apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;padding:40px 48px 0}
h1{font-size:30px;font-weight:650;letter-spacing:-.01em}
h2{font-size:19px;font-weight:650;margin:0 0 14px}
h3{font-size:14px;font-weight:600;margin:0 0 8px;color:#3b4252}
.sub{color:#4b5263;margin-top:4px}
.gate{margin-top:14px;display:inline-block;background:#0c1a3a;color:#fff;border-radius:8px;padding:8px 14px;font-weight:600}
section{background:#fff;border:1px solid #e1e4ea;border-radius:14px;padding:24px 28px;margin:22px 0}
.row{display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap}
.panel{border-radius:10px;padding:28px;display:flex;align-items:center;justify-content:center}
.note{font-size:13px;color:#4b5263}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}
table{border-collapse:collapse;font-size:14px}
td,th{padding:6px 14px;border-bottom:1px solid #e6e8ee;text-align:right;vertical-align:top}
th{color:#4b5263;font-weight:600}
td:first-child,th:first-child{text-align:left}
td.l,th.l{text-align:left}
.cell{display:flex;flex-direction:column;align-items:center;gap:4px}
.cell span{font-size:11px;color:#6a7183}
.trow{display:flex;align-items:flex-end;gap:8px;padding:12px 14px;border-radius:10px;margin-top:8px}
.trow.head{padding-top:0;padding-bottom:0;margin-top:0}
.tlabel{width:118px;flex:none;align-self:center;font-size:13px;line-height:1.35}
.tcell{flex:none;display:flex;flex-direction:column;align-items:center;gap:6px;font-size:11px}
.swatch{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;border:1px solid #0002}
.px{image-rendering:pixelated}
.serp{width:600px;padding:20px 22px;border-radius:12px;font-family:Arial,sans-serif}
.serp .site{display:flex;align-items:center;gap:12px}
.serp .fav{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.serp .name{font-size:14px;line-height:20px}
.serp .url{font-size:12px;line-height:18px}
.serp .title{font-size:20px;line-height:26px;margin-top:6px}
.serp .desc{font-size:14px;line-height:22px;margin-top:2px}
footer{padding:6px 0 30px;font-size:13px;color:#4b5263}
#end{height:2px;background:#ff00ff}
"""


def col_width(size: int) -> int:
    return max(size, 44) + 12


def tile_name(option: str, px: int) -> str:
    return f"prim-tile-{option}{'-small' if px <= SMALL_MAX else ''}.svg"


def tile_cell(option: str, size: int, density: int, ink: str) -> str:
    px = size * density
    cls = ' class="px"' if density == 1 else ""
    return (f'<div class="tcell" style="width:{col_width(size)}px;color:{ink}">'
            f'<img{cls} src="{png_uri(raster(SOURCE / tile_name(option, px), px))}" width="{size}" height="{size}" alt="">'
            f'<span>{size}·{density}x{"*" if px <= SMALL_MAX else ""}</span></div>')


def tiles_block(option: str, label: str) -> str:
    head = "".join(f'<div class="tcell" style="width:{col_width(s)}px;color:#6a7183">{s} px {d}x</div>'
                   for s in SIZES for d in (1, 2))
    rows = [f'<div class="trow head"><div class="tlabel"></div>{head}</div>']
    for name, color in BACKGROUNDS:
        ink = "#e8eaf0" if color in (SITE_BG, "#000000") else "#3b4252"
        border = "border:1px solid #e1e4ea;" if color == "#ffffff" else ""
        cells = "".join(tile_cell(option, s, d, ink) for s in SIZES for d in (1, 2))
        rows.append(f'<div class="trow" style="background:{color};{border}"><div class="tlabel" style="color:{ink}">'
                    f'{name}<br><span class="mono">{color}</span></div>{cells}</div>')
    return f'<h3>{label}</h3>{"".join(rows)}'


def zoom_compare(option: str) -> str:
    out = []
    for px in (16, 32):
        for small in (True, False):
            name = f"prim-tile-{option}{'-small' if small else ''}.svg"
            scale = 8 if px == 16 else 4
            out.append(f'<div class="cell"><img class="px" src="{png_uri(raster(SOURCE / name, px))}" '
                       f'width="{px * scale}" height="{px * scale}" alt="">'
                       f'<span>{px} px · {"variante ≤ 32 px" if small else "dessin standard"} · ×{scale}</span></div>')
    return "".join(out)


def serp(option: str, dark: bool, small: bool) -> str:
    bg, fav_bg = ("#1f1f1f", "#303134") if dark else ("#ffffff", "#f1f3f4")
    name_c, url_c, title_c, desc_c = (("#dadce0", "#bdc1c6", "#99c3ff", "#bdc1c6") if dark
                                      else ("#202124", "#4d5156", "#1a0dab", "#4d5156"))
    # Google affiche l'icône à 18 px CSS (36 px à DPR 2) : rendu vectoriel direct à 36 px.
    icon = png_uri(raster(SOURCE / f"prim-tile-{option}{'-small' if small else ''}.svg", 36))
    return (f'<div class="serp" style="background:{bg};border:1px solid {"#3c4043" if dark else "#e1e4ea"}">'
            f'<div class="site"><div class="fav" style="background:{fav_bg}"><img src="{icon}" width="18" height="18" alt=""></div>'
            f'<div><div class="name" style="color:{name_c}">Prim</div><div class="url" style="color:{url_c}">https://primapp.dev</div></div></div>'
            f'<div class="title" style="color:{title_c}">Prim — applications iOS natives premium</div>'
            f'<div class="desc" style="color:{desc_c}">Prim, studio indépendant d’applications iOS natives premium pour les pros et la conformité française…</div></div>')


def build_html(fid: dict, report: dict, meas: dict) -> str:
    pal = report["palette"]
    blue, gold, plate = pal["shield_blue"]["hex"], pal["gold"]["hex"], pal["plate"]["hex"]
    con = pal["contrast"]
    dims = report["emblem"]["dims"]
    es, ws = report["emblem"]["stats"], report["wordmark"]["stats"]
    raw = meas["shield_thickness_raw"]
    wm, wl = svg_uri(SOURCE / "prim-wordmark.svg"), svg_uri(SOURCE / "prim-wordmark-light.svg")
    mono = svg_uri(SOURCE / "prim-monogram.svg")
    gold_mono = "data:image/svg+xml;base64," + base64.b64encode(
        (SOURCE / "prim-monogram.svg").read_text(encoding="utf-8").replace(blue, gold).encode()).decode()
    small_sizes = "".join(
        f'<div class="panel" style="background:{bg};padding:18px 22px"><img src="{src}" height="{h}" alt=""></div>'
        for h in (48, 24, 16) for bg, src in (("#ffffff", wm), (SITE_BG, wl)))
    e, w = fid["emblem"], fid["word"]
    letter_rows = "".join(f'<tr><td>{k}</td><td>{fr(r["iou"], 4)}</td><td>{r["nodes"]}</td></tr>' for k, r in w["rows"].items())
    reg = [("Épaisseur des bandes", f'fût du P {fr(raw["P_stem_left"]["median"], 1)} · flanc du J {fr(raw["J_side_right"]["median"], 1)} · '
            f'bandeau {fr(raw["top_band_P"]["median"], 1)} · crochet {fr(raw["top_hook_J"]["median"], 1)} · traverse {fr(raw["crossbar"]["median"], 1)} · '
            f'fût du N {fr(raw["N_left_stem"]["median"], 1)}', f'une seule épaisseur t = {fr(dims["t"], 1)}'),
           ("Coins du haut", f'gauche r ≈ {fr(raw["corner_radius_top_left"], 1)} · droit r ≈ {fr(raw["corner_radius_top_right"], 1)}',
            f'les deux à t/2 = {fr(dims["rc"], 1)}, angle intérieur vif'),
           ("Silhouette", "pied et flancs dissymétriques, pointe décalée à droite", "symétrique par rapport à l’axe ; raccord bas r = "
            f'{fr(dims["rf"], 1)}, pans à {fr(dims["beta_deg"], 1)}°'),
           ("Coupures des entrelacs", f'sous la traverse {fr(raw["gap_below_crossbar"]["median"], 1)} ; au-dessus : soudée (0) ; '
            "autres 4 à 15 selon l’endroit", f'toutes à g = {fr(dims["g"], 1)}, parallèles aux droites, concentriques aux arcs ; '
            "coupure ajoutée au-dessus de la traverse (passage dessus/dessous cohérent)"),
           ("Crochet du J", "écart à la panse ≈ constant, concentrique", f'conservé : gj = {fr(dims["gj"], 1)}, concentrique à C1'),
           ("Contre-formes autour du N", "35,4 / 35,6 / 35,8 (ajustement libre)", f'égales : c = {fr(dims["counter_left"], 1)} ; N centré sur l’axe'),
           ("Fût droit du N", "coupé contre la panse, écart variable 4 à 9", "s’arrête au creux exact qu’il forme avec la diagonale (fixe R2)"),
           ("Penchement", f'maquette cisaillée de {fr(es["shear_deg"], 2)}° (bouclier) et {fr(ws["shear_deg"], 2)}° (PRIM)',
            "estimé pendant l’ajustement, non recopié : dessin droit")]
    reg_rows = "".join(f'<tr><td class="l">{a}</td><td class="l">{b}</td><td class="l">{c}</td></tr>' for a, b, c in reg)
    con_svg = construction_svg(report, blue)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Prim — planche V1</title><style>{CSS}</style></head><body>
<h1>Prim — planche V1</h1>
<p class="sub">Nouvelle référence (maquette bouclier + PRIM) · emblème et mot-symbole vectoriels reconstruits · tuiles A et B · 28/10/2026 · branche <span class="mono">feat/brand-logo</span> · TLILI HAMDI</p>
<div class="gate">Gate V1 — réponse attendue : « V1 OK + A » (ou B), ou corrections</div>

<section><h2>1. Emblème et mot-symbole</h2>
<div class="row">
<div class="panel" style="background:#ffffff;border:1px solid #e6e8ee;width:300px;height:300px"><img src="{mono}" height="236" alt=""></div>
<div class="panel" style="background:{blue};width:300px;height:300px"><img src="{gold_mono}" height="236" alt=""></div>
<div style="display:flex;flex-direction:column;gap:22px">
<div class="panel" style="background:#ffffff;border:1px solid #e6e8ee;width:560px;height:139px"><img src="{wm}" width="420" alt=""></div>
<div class="panel" style="background:{SITE_BG};width:560px;height:139px"><img src="{wl}" width="420" alt=""></div>
</div></div>
<p class="note" style="margin:12px 0 8px">Bleu <span class="swatch" style="background:{blue}"></span> <span class="mono">{blue}</span> et or
<span class="swatch" style="background:{gold}"></span> <span class="mono">{gold}</span> : médianes des pixels de cœur de la maquette (bouclier, lettres), même méthode pour les deux
(quartiles du bleu <span class="mono">{pal["shield_blue"]["iqr"][0]}–{pal["shield_blue"]["iqr"][1]}</span> : l’éclairage de la photo). Mot-symbole clair
<span class="swatch" style="background:{LIGHT}"></span> <span class="mono">{LIGHT}</span> (token <span class="mono">--text-primary</span>) pour l’en-tête et le pied de page.
Fond transparent, aucune signature, aucun relief ni dégradé.</p>
<div class="row" style="gap:12px">{small_sizes}</div>
<p class="note" style="margin-top:6px">Mot-symbole à 48, 24 et 16 px de haut.</p>
</section>

<section><h2>2. Fidélité à la maquette redressée</h2>
<div class="row">
<div><h3>Bouclier — silhouette de la maquette (bleu pâle) et contour reconstruit</h3><img src="{e['overlay']}" width="{e['w'] // 2}" alt=""></div>
<div><h3>Écarts pixel — accord gris · maquette seule rouge · reconstruction seule bleu</h3><img src="{e['diff']}" width="{e['w'] // 2}" alt=""></div>
</div>
<div class="row" style="margin-top:16px">
<div><h3>PRIM — superposition</h3><img src="{w['overlay']}" width="{w['w'] // 2}" alt=""></div>
<div><h3>PRIM — écarts</h3><img src="{w['diff']}" width="{w['w'] // 2}" alt=""></div>
</div>
<div class="row" style="margin-top:18px;gap:40px">
<table><tr><th>Bouclier</th><th>valeur</th></tr>
<tr><td>IoU (forme complète)</td><td>{fr(e["iou"], 4)}</td></tr>
<tr><td>IoU (silhouette, contre-formes remplies)</td><td>{fr(e["iou_sil"], 4)}</td></tr>
<tr><td>Écart au bord : RMS · p95 · max (unités du plan)</td><td>{fr(es["rms"])} · {fr(es["p95"])} · {fr(es["max"])}</td></tr>
<tr><td>Nœuds (cadre + îlot du N)</td><td>{" + ".join(str(n) for n in es["paths"])}</td></tr></table>
<table><tr><th>PRIM</th><th>IoU</th><th>Nœuds</th></tr>{letter_rows}
<tr><td>ensemble</td><td>{fr(w["iou"], 4)}</td><td></td></tr></table>
</div>
<p class="note" style="margin-top:10px">Masques : seuil de chroma bleue (bouclier) et R − B (lettres) sur la maquette redressée par l’homographie du filet or (2 px par unité ;
une unité ≈ 0,34–0,40 px de la photo). IoU recalculés ici depuis les SVG livrés, rendus par librsvg. Les écarts rouges et bleus viennent surtout des régularisations ci-dessous
et du relief photographié (biseaux, reflets) ; la maquette ne fournit pas de version à plat.</p>
<h3 style="margin-top:18px">Régularisations (relevés bruts de la maquette → dessin livré, unités du plan)</h3>
<table style="width:100%"><tr><th class="l">Élément</th><th class="l">Maquette</th><th class="l">Dessin</th></tr>{reg_rows}</table>
</section>

<section><h2>3. Construction</h2>
<div class="row" style="align-items:center;gap:36px">
<div>{con_svg}</div>
<div style="max-width:560px">
<p class="note">Trois brins de même épaisseur <b>t</b> : <b>P</b> (flanc gauche, bandeau, panse en deux arcs tangents C1 et C2, traverse), <b>N</b> (deux fûts et une diagonale,
symétrique autour de son centre) et <b>J</b> (flanc droit, crochet du haut). Passages : la traverse passe sur le fût gauche du N, la diagonale du N passe sur la panse,
la panse passe sur le fût droit du N, le crochet du J s’arrête contre la panse.</p>
<table style="margin-top:14px"><tr><th>Cote</th><th>valeur</th></tr>
<tr><td>épaisseur t</td><td>{fr(dims["t"])}</td></tr><tr><td>coupure g · crochet gj</td><td>{fr(dims["g"])} · {fr(dims["gj"])}</td></tr>
<tr><td>contre-forme c (gauche = droite = haut)</td><td>{fr(dims["counter_left"])}</td></tr>
<tr><td>panse : rayons d’axe R1 · R2</td><td>{fr(dims["R1_axis"])} · {fr(dims["R2_axis"])}</td></tr>
<tr><td>diagonale du N (depuis la verticale)</td><td>{fr(dims["theta_deg"])}°</td></tr>
<tr><td>coins du haut · raccords bas · pans du pied</td><td>{fr(dims["rc"])} · {fr(dims["rf"])} · {fr(dims["beta_deg"])}°</td></tr>
<tr><td>largeur × hauteur</td><td>{fr(dims["width"])} × {fr(dims["height"])}</td></tr></table>
<p class="note" style="margin-top:10px">Contour exact : droites et arcs de cercle seulement, sommets calculés par intersection ; aucune vectorisation automatique, aucune image embarquée.</p>
</div></div>
</section>

<section><h2>4. Tuiles d’icône — bouclier à 75 % du côté, coins arrondis à 20 %</h2>
<p class="note" style="margin-bottom:12px">Le bouclier bleu de la maquette sur sa plaque (<span class="mono">{plate}</span>) ne contraste qu’à {fr(con["blue_on_plate"])}:1 : les tuiles opposent bleu et or,
{fr(con["gold_on_blue"])}:1 dans les deux sens.</p>
{tiles_block('a', f'Option A (recommandée) — bouclier or sur tuile bleue')}
<div style="height:22px"></div>
{tiles_block('b', f'Option B — bouclier bleu sur tuile or')}
<p class="note" style="margin-top:12px">1x : raster à la taille affichée (pixels agrandis ×2 sur cette planche). 2x : raster double, net. * : variante ≤ 32 px (rasters de 32 px et moins).</p>
</section>

<section><h2>5. Variante ≤ 32 px</h2>
<p class="note" style="margin-bottom:12px">Dessinée sur la grille de 16 px (nette à 16 et 32 px) : épaisseur 2 px, panse à deux arcs de rayon 2 reliés par 1 px de verticale, contre-forme du P 3 × 3 px,
couloir et encoche du J 1 px. <b>Le N est retiré</b> : en 10 px de large, ses onze alternances plein/vide ne laissent que des traits de 1 px fondus (dessin standard, colonnes 2 et 4).
Cadre, P et crochet du J restent ceux du dessin standard.</p>
<div class="row" style="align-items:flex-end">{zoom_compare('a')}</div>
<div class="row" style="align-items:flex-end;margin-top:16px">{zoom_compare('b')}</div>
</section>

<section><h2>6. Maquette d’un résultat Google — taille réelle (icône 18 px dans une pastille de 28 px)</h2>
<div class="row">{serp('a', False, True)}{serp('a', True, True)}</div>
<div class="row" style="margin-top:14px">{serp('b', False, True)}{serp('b', True, True)}</div>
<h3 style="margin-top:18px">Même résultat si Google réduit le dessin standard (raster de 96 px) au lieu de la variante</h3>
<div class="row">{serp('a', False, False)}{serp('a', True, False)}</div>
<p class="note" style="margin-top:10px">Lignes 1 et 2 : options A et B depuis la variante ≤ 32 px. Ligne 3 : option A depuis le dessin standard. Approximation de la mise en page, sans élément de marque Google.</p>
</section>

<footer>Contrôle §1 : aucune pomme, aucune feuille, aucune forme évocatrice dans les fichiers produits ; aucune marque Apple dans le logo (signature « NATIVE … STUDIO » de la maquette retirée).
Maquette conservée dans <span class="mono">.brand-reference/</span> (gitignoré, hors de <span class="mono">public/</span>). Auteur : TLILI HAMDI.</footer>
<div id="end"></div>
</body></html>"""


def screenshot(html: str, out: FsPath) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        page = FsPath(tmp) / "sheet.html"
        page.write_text(html, encoding="utf-8")
        shot = FsPath(tmp) / "shot.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--user-data-dir={FsPath(tmp) / 'profile'}", "--window-size=1400,9000",
                        f"--screenshot={shot}", page.as_uri()],
                       check=True, capture_output=True, timeout=180)
        with Image.open(shot) as im:
            a = np.asarray(im.convert("RGB"))
    magenta = (a[:, :, 0] > 240) & (a[:, :, 1] < 20) & (a[:, :, 2] > 240)
    rows = np.nonzero(magenta.mean(axis=1) > 0.5)[0]
    if len(rows) == 0:
        raise RuntimeError("Fin de page non visible : agrandir --window-size")
    Image.fromarray(a[: rows.min()]).save(out, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    meas = json.loads(MEASURES.read_text(encoding="utf-8"))
    fid = fidelity(report)
    print(f"bouclier : IoU {fid['emblem']['iou']:.4f} · silhouette {fid['emblem']['iou_sil']:.4f} · nœuds {fid['emblem']['nodes']}")
    for k, r in fid["word"]["rows"].items():
        print(f"{k} : IoU {r['iou']:.4f} · nœuds {r['nodes']}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    screenshot(build_html(fid, report, meas), OUT)
    with Image.open(OUT) as im:
        print(f"✓ {OUT.relative_to(ref.ROOT)} — {im.width} × {im.height} px, {OUT.stat().st_size / 1024:.0f} Ko")
    if not args.no_open:
        subprocess.run(["open", str(OUT)], check=False)


if __name__ == "__main__":
    main()
