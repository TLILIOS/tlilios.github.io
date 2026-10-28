#!/usr/bin/env python3
"""Reconstruction vectorielle du logo Prim depuis la maquette redressée (brief marque §4).

Usage :
  .venv-brand/bin/python scripts/brand/construct.py

Topologies construites à la main (letters.py, emblem.py) ; positions, épaisseurs et rayons
ajustés par moindres carrés sur les contours sous-pixel de la maquette redressée
(.brand-reference/, jamais publiée). Aucune vectorisation automatique, aucune image
embarquée. La signature de la maquette est exclue (§1).

Sorties : docs/brand/source/*.svg (hors de assets/, que le build publie) et docs/brand/fit-report.json.
"""
from __future__ import annotations

import json

import numpy as np
from scipy import ndimage
from skimage.morphology import disk

import emblem
import geometry as geo
import letters
import measure
import reference as ref

SOURCE = ref.ROOT / "docs" / "brand" / "source"
REPORT = ref.ROOT / "docs" / "brand" / "fit-report.json"
LIGHT = "#eceef4"          # token --text-primary du site (en-tête, pied de page)
TILE = 512                 # tuile standard ; variante ≤ 32 px sur la grille de 16
TILE_SCALE = 0.75          # hauteur du bouclier / côté de la tuile (variante : 12 px sur 16)
AUTHOR = "Auteur : TLILI HAMDI."


def fit_word(rgb, H):
    _, mask, contours = ref.word(rgb, H)
    target = geo.Target(mask, ref.WORD_BOX[:2], ref.SCALE, contours)
    pivot = 0.5 * (ref.WORD_BOX[1] + ref.WORD_BOX[3])
    p, stats = geo.fit(letters.build_all, letters.initial(), target, lower=letters.LOWER, pivot_y=pivot)
    ds = letters.glyph_ds(p)
    render = lambda d: geo.render_coverage(d, ref.WORD_BOX[:2], ref.SCALE, mask.shape, p["shear"], pivot) >= 0.5
    stats["shear_deg"] = round(float(np.degrees(np.arctan(p["shear"]))), 3)
    stats["iou"] = round(geo.iou(render(list(ds.values())), mask), 4)
    per_letter = {}
    for k, build in letters.LETTERS.items():
        lp = build(p)
        c = render([ds[k]])
        x0, y0, x1, y1 = geo.bbox(lp)
        sel = np.zeros_like(mask)
        i0, i1 = int((y0 - ref.WORD_BOX[1] - 4) * ref.SCALE), int((y1 - ref.WORD_BOX[1] + 4) * ref.SCALE)
        j0, j1 = int((x0 - ref.WORD_BOX[0] - 4) * ref.SCALE), int((x1 - ref.WORD_BOX[0] + 4) * ref.SCALE)
        sel[max(i0, 0):i1, max(j0, 0):j1] = True
        per_letter[k] = {"iou": round(geo.iou(c & sel, mask & sel), 4), "nodes": sum(pp.nodes for pp in lp)}
    stats["letters"] = per_letter
    return p, stats


def silhouette(mask: np.ndarray, r: int = 26) -> np.ndarray:
    """Silhouette pleine : fermeture (disque de r px, soit 13 unités) qui scelle l'encoche du J,
    seule ouverture des contre-formes vers l'extérieur, puis remplissage des trous."""
    big = np.pad(mask, r)
    return ndimage.binary_fill_holes(ndimage.binary_closing(big, structure=disk(r)))[r:-r, r:-r]


def fit_emblem(rgb, H):
    _, mask, contours = ref.shield(rgb, H)
    target = geo.Target(mask, ref.SHIELD_BOX[:2], ref.SCALE, contours)
    pivot = 0.5 * (ref.SHIELD_BOX[1] + ref.SHIELD_BOX[3])
    q, stats = geo.fit(emblem.build_regular, emblem.initial(), target, lower=emblem.LOWER, pivot_y=pivot,
                       per_path=1500, max_nfev=4000)
    p = emblem.regular(q)
    paths = emblem.build(p)
    d = "".join(geo.to_d(pp) for pp in paths)
    cov = geo.render_coverage([d], ref.SHIELD_BOX[:2], ref.SCALE, mask.shape, p["shear"], pivot) >= 0.5
    stats.update({"shear_deg": round(float(np.degrees(np.arctan(p["shear"]))), 3),
                  "iou": round(geo.iou(cov, mask), 4),
                  "iou_silhouette": round(geo.iou(silhouette(cov), silhouette(mask)), 4),
                  "paths": [pp.nodes for pp in paths]})
    return q, p, stats


# ---------------------------------------------------------------- écriture des sources

def header(what: str) -> str:
    return f"<!-- Prim — {what}. Construction : scripts/brand/construct.py. {AUTHOR} -->\n"


def svg_doc(what: str, w: float, h: float, body: str) -> str:
    return (header(what) + f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {geo.fmt(w)} {geo.fmt(h)}" '
            f'width="{geo.fmt(w)}" height="{geo.fmt(h)}" role="img" aria-label="Prim">\n{body}</svg>\n')


def placed(paths, s: float, dx: float, dy: float) -> str:
    return "".join(geo.to_d(pp.transformed(s, dx, dy)) for pp in paths)


def write_sources(p_word: dict, p_emb: dict, pal: dict) -> dict:
    blue, gold = pal["shield_blue"]["hex"], pal["gold"]["hex"]
    SOURCE.mkdir(parents=True, exist_ok=True)
    for old in SOURCE.glob("*.svg"):
        old.unlink()
    out = {}

    def put(name: str, text: str) -> None:
        (SOURCE / name).write_text(text, encoding="utf-8")
        out[name] = len(text.encode())

    # Mot-symbole : quatre chemins (P, R, I, M), dessin droit, origine au coin de l'emprise.
    word = letters.build_all(p_word)
    x0, y0, x1, y1 = geo.bbox(word)
    by_letter = {k: build(p_word) for k, build in letters.LETTERS.items()}
    for name, color, what in (("prim-wordmark.svg", blue, f"mot-symbole, bleu {blue}"),
                              ("prim-wordmark-light.svg", LIGHT, f"mot-symbole clair {LIGHT} (en-tête et pied de page)")):
        body = "".join(f'  <path fill="{color}" d="{placed(by_letter[k], 1.0, -x0, -y0)}"/>\n' for k in letters.LETTERS)
        put(name, svg_doc(what, x1 - x0, y1 - y0, body))

    # Emblème complet : cadre + îlot du N dans un même chemin (règle nonzero).
    paths = emblem.build(p_emb)
    ex0, ey0, ex1, ey1 = geo.bbox(paths)
    put("prim-monogram.svg", svg_doc(f"emblème (bouclier P·N·J), bleu {blue}", ex1 - ex0, ey1 - ey0,
                                     f'  <path fill="{blue}" d="{placed(paths, 1.0, -ex0, -ey0)}"/>\n'))

    # Tuiles : bouclier à 75 % du côté, centré ; coins à 20 % du côté.
    s = TILE * TILE_SCALE / (ey1 - ey0)
    dx = 0.5 * TILE - s * 0.5 * (ex0 + ex1)
    dy = 0.5 * TILE - s * 0.5 * (ey0 + ey1)
    small = emblem.build_small(p_emb["beta"])
    for opt, bg, fg, label in (("a", blue, gold, f"option A (or {gold} sur bleu {blue})"),
                               ("b", gold, blue, f"option B (bleu {blue} sur or {gold})")):
        put(f"prim-tile-{opt}.svg", svg_doc(f"tuile d'icône {label}", TILE, TILE,
            f'  <rect width="{TILE}" height="{TILE}" rx="{geo.fmt(0.2 * TILE)}" fill="{bg}"/>\n'
            f'  <path fill="{fg}" d="{placed(paths, s, dx, dy)}"/>\n'))
        put(f"prim-tile-{opt}-small.svg", svg_doc(f"tuile d'icône {label}, variante ≤ 32 px (grille 16)", 16, 16,
            f'  <rect width="16" height="16" rx="3.2" fill="{bg}"/>\n'
            f'  <path fill="{fg}" d="{"".join(geo.to_d(pp) for pp in small)}"/>\n'))
    return out


def main() -> None:
    rgb = ref.load_rgb()
    H, _, _ = ref.homography(rgb)
    pal = measure.palette(rgb, H)
    p_word, s_word = fit_word(rgb, H)
    q_emb, p_emb, s_emb = fit_emblem(rgb, H)
    files = write_sources(p_word, p_emb, pal)
    report = {"palette": pal, "site_light": LIGHT,
              "wordmark": {"stats": s_word, "params": {k: round(v, 3) for k, v in p_word.items()}},
              "emblem": {"stats": s_emb, "fitted": {k: round(v, 3) for k, v in q_emb.items()},
                         "dims": {k: round(float(v), 2) for k, v in emblem.dims(p_emb).items()},
                         "rules": emblem.regular.__doc__.split(":", 1)[1].strip().replace("\n   ", "")},
              "small": {**emblem.SMALL, "beta_deg": round(p_emb["beta"], 3), "grid": 16},
              "tile": {"side": TILE, "shield_height_ratio": TILE_SCALE, "corner_ratio": 0.2},
              "files": files}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"wordmark": s_word, "emblem": s_emb, "dims": report["emblem"]["dims"]}, indent=1, ensure_ascii=False))
    for name, size in files.items():
        print(f"✓ docs/brand/source/{name} — {size} octets")


if __name__ == "__main__":
    main()
