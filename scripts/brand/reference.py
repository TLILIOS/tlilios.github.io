"""Lecture de la référence logo (maquette photo) : redressement et masques — usage local.

La référence (.brand-reference/prim_logo.jpeg, gitignorée) est une maquette en perspective :
plaque marine posée sur un marbre, cerné d'un filet or carré. Le filet est sur la table,
parallèle à la face de la plaque : l'homographie qui le ramène à un carré redresse la face
à une similitude près (angles et proportions conservés).

Elle porte la signature « NATIVE iOS STUDIO » : marque Apple, exclue de toute mesure et de
toute image produite (brief marque §1). Toute image dérivée ne s'écrit que dans
.brand-reference/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import argrelextrema
from skimage import measure

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / ".brand-reference" / "prim_logo.jpeg"
QUARANTINE = ROOT / ".brand-reference"

PLANE = 1800.0          # côté du filet carré redressé, en unités du plan
# Extrémités approchées des quatre côtés du filet (pixels source), affinées par ajustement.
FRAME_APPROX = {"top": ((176, 244), (836, 56)), "right": ((836, 56), (1152, 591)),
                "bottom": ((1152, 591), (420, 840)), "left": ((420, 840), (176, 244))}
# Zones du plan redressé (u0, v0, u1, v1) ; la signature (v > 1115) n'est jamais lue.
SHIELD_BOX = (730.0, 450.0, 1150.0, 930.0)
WORD_BOX = (660.0, 950.0, 1240.0, 1110.0)
GEM_BOX = (1300.0, 1150.0, 1460.0, 1300.0)
SCALE = 2               # pixels par unité pour les masques
SHIELD_LEVEL = 30.0     # chroma bleue B − (R+G)/2 : bouclier > 30, plaque ≈ 16–23
GOLD_LEVEL = 7.3        # R − B lissé : mi-chemin lettres (38,5) / plaque (−23,9)


def load_rgb(path: Path = REFERENCE) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64)


def luma(rgb: np.ndarray) -> np.ndarray:
    return rgb @ np.array([0.299, 0.587, 0.114])


def _strip_center(prof: np.ndarray, s: np.ndarray):
    """Axe d'un filet métallique : milieu de ses deux arêtes sombres (minima de luminance)."""
    p = ndimage.gaussian_filter1d(prof, 1.2)
    mins = argrelextrema(p, np.less, order=4)[0]
    best = None
    for i in range(len(mins)):
        for j in range(i + 1, len(mins)):
            a, b = mins[i], mins[j]
            if not 3.5 <= s[b] - s[a] <= 11:
                continue
            peak = p[a:b + 1].max()
            depth = min(peak - p[a], peak - p[b])
            if depth >= 15 and (best is None or depth > best[0]):
                best = (depth, 0.5 * (s[a] + s[b]))
    return None if best is None else best[1]


def frame_lines(rgb: np.ndarray) -> dict:
    """Droites (centre, direction) des quatre côtés du filet, ajustées en moindres carrés totaux."""
    lum = luma(rgb)
    out = {}
    for side, (a, b) in FRAME_APPROX.items():
        p0, p1 = np.array(a, float), np.array(b, float)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-d[1], d[0]])
        pts = []
        for t in np.linspace(0.05, 0.95, 70):
            c = p0 + t * (p1 - p0)
            s = np.arange(-12, 12.01, 0.25)
            xy = c[None, :] + s[:, None] * n[None, :]
            off = _strip_center(ndimage.map_coordinates(lum, [xy[:, 1] - 0.5, xy[:, 0] - 0.5], order=1), s)
            if off is not None:
                pts.append(c + off * n)
        pts = np.array(pts)
        keep = np.ones(len(pts), bool)
        for _ in range(5):
            q = pts[keep]
            cc = q.mean(0)
            dv = np.linalg.svd(q - cc)[2][0]
            nv = np.array([-dv[1], dv[0]])
            res = (pts - cc) @ nv
            keep = np.abs(res) < max(0.5, 2.5 * np.std(res[keep]))
        q = pts[keep]
        cc = q.mean(0)
        dv = np.linalg.svd(q - cc)[2][0]
        nv = np.array([-dv[1], dv[0]])
        out[side] = {"center": cc, "dir": dv, "points": int(keep.sum()), "sampled": len(pts),
                     "rms": float(np.sqrt(np.mean(((q - cc) @ nv) ** 2)))}
    return out


def _meet(l1: dict, l2: dict) -> np.ndarray:
    A = np.column_stack([l1["dir"], -l2["dir"]])
    t = np.linalg.solve(A, l2["center"] - l1["center"])
    return l1["center"] + t[0] * l1["dir"]


def homography(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """H : pixels source (centres en j + 0,5) → plan redressé, filet = carré [0, PLANE]²."""
    lines = frame_lines(rgb)
    corners = np.array([_meet(lines["left"], lines["top"]), _meet(lines["top"], lines["right"]),
                        _meet(lines["right"], lines["bottom"]), _meet(lines["bottom"], lines["left"])])
    dst = np.array([[0, 0], [PLANE, 0], [PLANE, PLANE], [0, PLANE]])
    A = []
    for (x, y), (u, v) in zip(corners, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    H = np.linalg.svd(np.array(A))[2][-1].reshape(3, 3)
    return H / H[2, 2], corners, lines


def rectify(rgb: np.ndarray, H: np.ndarray, box, scale: int = SCALE) -> np.ndarray:
    """Image redressée de la zone `box` du plan, `scale` pixels par unité (bicubique)."""
    u0, v0, u1, v1 = box
    uu, vv = np.meshgrid(u0 + (np.arange(int((u1 - u0) * scale)) + 0.5) / scale,
                         v0 + (np.arange(int((v1 - v0) * scale)) + 0.5) / scale)
    Q = np.linalg.inv(H) @ np.stack([uu.ravel(), vv.ravel(), np.ones(uu.size)])
    xs, ys = Q[0] / Q[2] - 0.5, Q[1] / Q[2] - 0.5
    chans = [ndimage.map_coordinates(rgb[..., c], [ys, xs], order=3, mode="nearest").reshape(uu.shape)
             for c in range(3)]
    return np.clip(np.stack(chans, -1), 0, 255)


def field_mask(field: np.ndarray, level: float, box, scale: int = SCALE):
    """Masque principal (composantes > 400 px) et contours sous-pixel en unités du plan."""
    mask = ndimage.binary_opening(field > level, iterations=2)
    lab, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 400])
    work = np.where(ndimage.binary_dilation(keep, iterations=3), field, field.min())
    contours = []
    for c in measure.find_contours(work, level):
        if len(c) < 60:
            continue
        contours.append(np.column_stack([box[0] + (c[:, 1] + 0.5) / scale, box[1] + (c[:, 0] + 0.5) / scale]))
    return keep, contours


def shield(rgb: np.ndarray, H: np.ndarray):
    img = rectify(rgb, H, SHIELD_BOX)
    field = ndimage.gaussian_filter(img[..., 2] - 0.5 * (img[..., 0] + img[..., 1]), 1.5)
    mask, contours = field_mask(field, SHIELD_LEVEL, SHIELD_BOX)
    return img, mask, contours


def word(rgb: np.ndarray, H: np.ndarray):
    img = rectify(rgb, H, WORD_BOX)
    field = ndimage.gaussian_filter(img[..., 0] - img[..., 2], 1.2)
    mask, contours = field_mask(field, GOLD_LEVEL, WORD_BOX)
    return img, mask, contours


def save_quarantine(img: np.ndarray, name: str) -> Path:
    path = QUARANTINE / "crops" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)
    return path
