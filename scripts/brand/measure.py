#!/usr/bin/env python3
"""Mesures de la référence logo (brief marque §4) : palette, redressement, épaisseurs brutes.

Usage :
  .venv-brand/bin/python scripts/brand/measure.py [--crops]

Lit .brand-reference/prim_logo.jpeg (maquette photo, gitignorée, jamais publiée) et écrit
docs/brand/measurements.json : nombres uniquement, aucune image. La signature de la maquette
(« NATIVE iOS STUDIO », marque Apple) n'est jamais lue (§1). --crops écrit des vues de
contrôle dans .brand-reference/crops/ (quarantaine).
"""
from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import ndimage

import reference as ref

OUT = ref.ROOT / "docs" / "brand" / "measurements.json"
PLATE_BOX = (600.0, 380.0, 1300.0, 1110.0)   # face de la plaque autour du logo, signature exclue


def hexrgb(c) -> str:
    return "#" + "".join(f"{int(round(v)):02x}" for v in c)


def luminance(c) -> float:
    """Luminance relative WCAG 2.2 d'une couleur sRGB 8 bits."""
    lin = [(v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def core_color(img: np.ndarray, mask: np.ndarray, erode: int) -> tuple[list[float], list[float], list[float]]:
    """Médiane (et quartiles) des pixels de cœur : masque érodé, hors anticrénelage et biseaux."""
    core = ndimage.binary_erosion(mask, iterations=erode)
    px = img[core]
    return (np.median(px, axis=0).tolist(), np.percentile(px, 25, axis=0).tolist(),
            np.percentile(px, 75, axis=0).tolist())


def palette(rgb: np.ndarray, H: np.ndarray) -> dict:
    s_img, s_mask, _ = ref.shield(rgb, H)
    w_img, w_mask, _ = ref.word(rgb, H)
    blue, blue_q1, blue_q3 = core_color(s_img, s_mask, 6)
    gold, gold_q1, gold_q3 = core_color(w_img, w_mask, 4)
    face = ref.rectify(rgb, H, PLATE_BOX)
    u0, v0 = PLATE_BOX[:2]
    vv, uu = np.mgrid[0:face.shape[0], 0:face.shape[1]]
    uu, vv = u0 + (uu + 0.5) / ref.SCALE, v0 + (vv + 0.5) / ref.SCALE
    keep = np.ones(face.shape[:2], dtype=bool)
    for (a, b, c, d), m in ((ref.SHIELD_BOX, 15), (ref.WORD_BOX, 15), (ref.GEM_BOX, 15)):
        keep &= ~((uu > a - m) & (uu < c + m) & (vv > b - m) & (vv < d + m))
    plate = np.median(face[keep], axis=0).tolist()
    out = {}
    for name, c, q1, q3 in (("shield_blue", blue, blue_q1, blue_q3), ("gold", gold, gold_q1, gold_q3),
                            ("plate", plate, None, None)):
        out[name] = {"hex": hexrgb(c), "rgb": [round(v, 1) for v in c], "luminance": round(luminance([round(v) for v in c]), 4)}
        if q1 is not None:
            out[name]["iqr"] = [hexrgb(q1), hexrgb(q3)]
    # Contrastes sur les couleurs livrées (arrondies à 8 bits), pas sur les médianes flottantes.
    q = lambda c: [round(v) for v in c]
    out["contrast"] = {"gold_on_blue": round(contrast(q(gold), q(blue)), 2),
                       "blue_on_plate": round(contrast(q(blue), q(plate)), 2),
                       "gold_on_plate": round(contrast(q(gold), q(plate)), 2)}
    return out


def runs_at(field: np.ndarray, box, line: str, at: float) -> list[tuple[float, float]]:
    """Plages bleues [début, fin] sous-pixel le long d'une ligne (v = at) ou colonne (u = at)."""
    u0, v0 = box[:2]
    S, L = ref.SCALE, ref.SHIELD_LEVEL
    if line == "row":
        i = (at - v0) * S - 0.5
        prof = ndimage.map_coordinates(field, [np.full(field.shape[1], i), np.arange(field.shape[1])], order=1)
        origin = u0
    else:
        j = (at - u0) * S - 0.5
        prof = ndimage.map_coordinates(field, [np.arange(field.shape[0]), np.full(field.shape[0], j)], order=1)
        origin = v0
    s = prof - L
    idx = np.nonzero(np.sign(s[:-1]) != np.sign(s[1:]))[0]
    xs = [(origin + (k + s[k] / (s[k] - s[k + 1]) + 0.5) / S, s[k + 1] > 0) for k in idx]
    out, start = [], None
    for x, rising in xs:
        if rising:
            start = x
        elif start is not None:
            out.append((start, x))
            start = None
    return out


def band(field, line: str, positions, pick) -> dict:
    """Épaisseur médiane d'une bande : `pick(runs)` choisit la plage sur chaque ligne."""
    w = []
    for at in positions:
        r = pick(runs_at(field, ref.SHIELD_BOX, line, at))
        if r is not None:
            w.append(r[1] - r[0])
    w = np.array(w)
    return {"median": round(float(np.median(w)), 2), "min": round(float(w.min()), 2),
            "max": round(float(w.max()), 2), "samples": int(len(w))}


def corner_radius(contours, u0: float, v0: float, u1: float, v1: float) -> float:
    """Rayon du cercle ajusté (moindres carrés algébriques) sur les points de contour d'un coin."""
    pts = np.vstack([c[(c[:, 0] > u0) & (c[:, 0] < u1) & (c[:, 1] > v0) & (c[:, 1] < v1)] for c in contours])
    A = np.column_stack([2 * pts[:, 0], 2 * pts[:, 1], np.ones(len(pts))])
    cu, cv, k = np.linalg.lstsq(A, (pts ** 2).sum(1), rcond=None)[0]
    return float(np.sqrt(k + cu * cu + cv * cv))


def gap(field, positions, end_near: float, start_near: float) -> dict:
    """Coupure verticale entre une plage qui finit près de `end_near` et la suivante."""
    w = []
    for u in positions:
        rr = runs_at(field, ref.SHIELD_BOX, "col", u)
        ends = [r for r in rr if abs(r[1] - end_near) < 8]
        nxt = [r for r in rr if abs(r[0] - start_near) < 8]
        w.append(nxt[0][0] - ends[0][1] if ends and nxt else 0.0)
    w = np.array(w)
    return {"median": round(float(np.median(w)), 2), "min": round(float(w.min()), 2), "max": round(float(w.max()), 2)}


def thicknesses(rgb: np.ndarray, H: np.ndarray) -> dict:
    """Épaisseurs, rayons et coupures bruts du bouclier (unités du plan, seuil de chroma) :
    la maquette n'est ni symétrique ni à épaisseur constante, d'où la régularisation de emblem.py."""
    img = ref.rectify(rgb, H, ref.SHIELD_BOX)
    field = ndimage.gaussian_filter(img[..., 2] - 0.5 * (img[..., 0] + img[..., 1]), 1.5)
    _, _, contours = ref.shield(rgb, H)
    near = lambda x: (lambda rr: next((r for r in rr if r[0] - 8 < x < r[1] + 8), None))
    first = lambda rr: rr[0] if rr else None
    last = lambda rr: rr[-1] if rr else None
    return {"P_stem_left": band(field, "row", range(550, 681, 10), first),
            "J_side_right": band(field, "row", range(550, 721, 10), last),
            "top_band_P": band(field, "col", range(800, 951, 10), first),
            "top_hook_J": band(field, "col", range(1056, 1077, 4), first),
            "crossbar": band(field, "col", range(800, 831, 5), near(705)),
            "N_left_stem": band(field, "row", range(640, 671, 5), near(856)),
            "bottom_band_vertical": band(field, "col", range(890, 931, 10), last),
            "corner_radius_top_left": round(corner_radius(contours, 744, 459, 778, 494), 1),
            "corner_radius_top_right": round(corner_radius(contours, 1112, 454, 1138, 480), 1),
            "gap_below_crossbar": gap(field, range(845, 876, 5), 730, 740),
            "gap_above_crossbar": gap(field, range(845, 876, 5), 678, 682)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", action="store_true")
    args = ap.parse_args()
    rgb = ref.load_rgb()
    H, corners, lines = ref.homography(rgb)
    out = {"reference": {"file": ref.REFERENCE.name, "width": int(rgb.shape[1]), "height": int(rgb.shape[0])},
           "rectification": {"plane_side": ref.PLANE, "frame_rms_px": {k: round(v["rms"], 3) for k, v in lines.items()},
                             "frame_points": {k: [v["points"], v["sampled"]] for k, v in lines.items()}},
           "palette": palette(rgb, H),
           "shield_thickness_raw": thicknesses(rgb, H),
           "excluded": ["signature (v > 1110 du plan)", "saphir (GEM_BOX)", "relief et dégradés de la maquette"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["palette"], indent=1, ensure_ascii=False))
    print(json.dumps(out["shield_thickness_raw"], ensure_ascii=False))
    if args.crops:
        img, mask, _ = ref.shield(rgb, H)
        ref.save_quarantine(img, "shield-rect.png")
        img, mask, _ = ref.word(rgb, H)
        ref.save_quarantine(img, "prim-rect.png")
    print(f"✓ {OUT.relative_to(ref.ROOT)}")


if __name__ == "__main__":
    main()
