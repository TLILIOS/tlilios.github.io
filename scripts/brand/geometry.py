"""Géométrie partagée de l'outillage marque : chemins L/C/A, échantillonnage, SVG,
ajustement par moindres carrés sur un champ de distance signée, rendu librsvg et IoU.

Coordonnées SVG (y vers le bas). Aucune dépendance au site : outillage local uniquement.
"""
from __future__ import annotations

import io
import math
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from skimage.draw import polygon as fill_polygon

SUPERSAMPLE = 8         # résolution du champ de distance signée des cibles


def unit(angle: float) -> np.ndarray:
    return np.array([math.cos(angle), math.sin(angle)])


def intersect(p, d, q, e) -> np.ndarray:
    """Intersection des droites p + t·d et q + u·e."""
    p, d, q, e = (np.asarray(v, dtype=float) for v in (p, d, q, e))
    t = np.linalg.solve(np.column_stack([d, -e]), q - p)
    return p + t[0] * d


class Path:
    """Contour fermé : segments L (droite), C (cubique), A (arc de cercle).

    Chaque segment se termine sur un nœud ; un contour fermé compte autant de nœuds
    que de segments, fermeture comprise.
    """

    def __init__(self, start):
        self.start = np.asarray(start, dtype=float)
        self.cur = self.start
        self.segs: list[tuple] = []

    def L(self, p):
        p = np.asarray(p, dtype=float)
        self.segs.append(("L", self.cur, p))
        self.cur = p
        return self

    def C(self, c1, c2, p):
        p = np.asarray(p, dtype=float)
        self.segs.append(("C", self.cur, np.asarray(c1, dtype=float), np.asarray(c2, dtype=float), p))
        self.cur = p
        return self

    def A(self, center, p, sweep: int):
        """Arc de centre `center` jusqu'à `p` ; sweep=1 : sens horaire à l'écran."""
        p = np.asarray(p, dtype=float)
        self.segs.append(("A", self.cur, np.asarray(center, dtype=float), p, sweep))
        self.cur = p
        return self

    def close(self):
        if np.hypot(*(self.cur - self.start)) > 1e-9:
            self.L(self.start)
        return self

    @property
    def nodes(self) -> int:
        return len(self.segs)

    def transformed(self, s: float, dx: float, dy: float) -> "Path":
        f = lambda q: np.asarray(q) * s + np.array([dx, dy])
        out = Path(f(self.start))
        for seg in self.segs:
            if seg[0] == "L":
                out.segs.append(("L", f(seg[1]), f(seg[2])))
            elif seg[0] == "C":
                out.segs.append(("C", f(seg[1]), f(seg[2]), f(seg[3]), f(seg[4])))
            else:
                out.segs.append(("A", f(seg[1]), f(seg[2]), f(seg[3]), seg[4]))
        out.cur = f(self.cur)
        return out


def _arc_angles(seg):
    _, p0, c, p1, sweep = seg
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    if sweep and a1 <= a0:
        a1 += 2 * math.pi
    if not sweep and a1 >= a0:
        a1 -= 2 * math.pi
    r = 0.5 * (math.hypot(*(p0 - c)) + math.hypot(*(p1 - c)))
    return a0, a1, r


def _bezier(p0, c1, c2, p1, t):
    u = 1 - t
    return ((u ** 3)[:, None] * p0 + (3 * u * u * t)[:, None] * c1
            + (3 * u * t * t)[:, None] * c2 + (t ** 3)[:, None] * p1)


def sample(path: Path, per_seg: dict | None = None):
    """Échantillons (N, 2) et poids √ds (intégration de la distance le long du contour)."""
    per_seg = per_seg or {"L": 24, "C": 48, "A": 16}
    pts, wts = [], []
    for seg in path.segs:
        kind = seg[0]
        n = per_seg[kind]
        t = (np.arange(n) + 0.5) / n
        if kind == "L":
            p0, p1 = seg[1], seg[2]
            q = p0 + t[:, None] * (p1 - p0)
            length = float(np.hypot(*(p1 - p0)))
        elif kind == "C":
            q = _bezier(*seg[1:], t)
            fine = _bezier(*seg[1:], np.linspace(0, 1, 65))
            length = float(np.hypot(*np.diff(fine, axis=0).T).sum())
        else:
            a0, a1, r = _arc_angles(seg)
            ang = a0 + t * (a1 - a0)
            c = seg[2]
            q = np.column_stack([c[0] + r * np.cos(ang), c[1] + r * np.sin(ang)])
            length = abs(a1 - a0) * r
        pts.append(q)
        wts.append(np.full(n, math.sqrt(max(length, 1e-9) / n)))
    return np.vstack(pts), np.concatenate(wts)


def polyline(path: Path, step: float = 0.25) -> np.ndarray:
    """Polyligne dense du contour (distances, rastérisation, emprise)."""
    out = []
    for seg in path.segs:
        kind = seg[0]
        if kind == "L":
            n = max(2, int(np.hypot(*(seg[2] - seg[1])) / step))
            t = np.arange(n) / n
            out.append(seg[1] + t[:, None] * (seg[2] - seg[1]))
        elif kind == "C":
            p0, c1, c2, p1 = seg[1:]
            approx = np.hypot(*(c1 - p0)) + np.hypot(*(c2 - c1)) + np.hypot(*(p1 - c2))
            n = max(8, int(approx / step))
            out.append(_bezier(p0, c1, c2, p1, np.arange(n) / n))
        else:
            a0, a1, r = _arc_angles(seg)
            n = max(4, int(abs(a1 - a0) * r / step))
            ang = a0 + (np.arange(n) / n) * (a1 - a0)
            c = seg[2]
            out.append(np.column_stack([c[0] + r * np.cos(ang), c[1] + r * np.sin(ang)]))
    return np.vstack(out)


def bbox(paths) -> tuple[float, float, float, float]:
    pts = np.vstack([polyline(p, 0.25) for p in paths])
    return float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())


def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def to_d(path: Path) -> str:
    """Données SVG : M, H/V pour les droites d'axe, L, C, A, Z."""
    parts = [f"M{fmt(path.start[0])} {fmt(path.start[1])}"]
    segs = path.segs
    if segs and segs[-1][0] == "L" and np.hypot(*(segs[-1][2] - path.start)) < 1e-9:
        segs = segs[:-1]          # la fermeture droite est portée par Z
    for seg in segs:
        kind = seg[0]
        if kind == "L":
            p0, p1 = seg[1], seg[2]
            if abs(p1[1] - p0[1]) < 1e-9:
                parts.append(f"H{fmt(p1[0])}")
            elif abs(p1[0] - p0[0]) < 1e-9:
                parts.append(f"V{fmt(p1[1])}")
            else:
                parts.append(f"L{fmt(p1[0])} {fmt(p1[1])}")
        elif kind == "C":
            _, _, c1, c2, p1 = seg
            parts.append(f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p1[0])} {fmt(p1[1])}")
        else:
            a0, a1, r = _arc_angles(seg)
            large = 1 if abs(a1 - a0) > math.pi + 1e-9 else 0
            p1 = seg[3]
            parts.append(f"A{fmt(r)} {fmt(r)} 0 {large} {seg[4]} {fmt(p1[0])} {fmt(p1[1])}")
    parts.append("Z")
    return "".join(parts)


# ---------------------------------------------------------------- cible et ajustement

class Target:
    """Masque mesuré : champ de distance signée (positif dehors) + échantillons de bord.

    `mask` est un masque booléen dont le pixel (i, j) a pour centre
    (origin_x + (j + 0,5)/scale, origin_y + (i + 0,5)/scale) en unités du plan.
    """

    def __init__(self, mask: np.ndarray, origin: tuple[float, float], scale: float, contours: list[np.ndarray]):
        self.origin = np.asarray(origin, dtype=float)
        self.scale = float(scale)
        S = SUPERSAMPLE
        # Bords reconstruits depuis les contours sous-pixel (plus fins que le masque),
        # remplissage pair-impair : les contours intérieurs creusent les trous.
        h, w = mask.shape
        inside = np.zeros((h * S, w * S), dtype=bool)
        for c in contours:
            rr, cc = fill_polygon((c[:, 1] - self.origin[1]) * self.scale * S - 0.5,
                                  (c[:, 0] - self.origin[0]) * self.scale * S - 0.5, inside.shape)
            inside[rr, cc] ^= True
        self.sdf = ((ndimage.distance_transform_edt(~inside) - ndimage.distance_transform_edt(inside))
                    / (S * self.scale)).astype(np.float32)
        samples = []
        for c in contours:
            closed = np.vstack([c, c[:1]])
            seglen = np.hypot(*np.diff(closed, axis=0).T)
            s = np.concatenate([[0], np.cumsum(seglen)])
            u = np.arange(0, s[-1], 0.5 / self.scale)
            samples.append(np.column_stack([np.interp(u, s, closed[:, 0]), np.interp(u, s, closed[:, 1])]))
        self.samples = np.vstack(samples)

    def signed(self, pts: np.ndarray) -> np.ndarray:
        S = SUPERSAMPLE * self.scale
        coords = [(pts[:, 1] - self.origin[1]) * S - 0.5, (pts[:, 0] - self.origin[0]) * S - 0.5]
        return ndimage.map_coordinates(self.sdf, coords, order=1, mode="nearest")


def poly_distance(q: np.ndarray, poly: np.ndarray) -> np.ndarray:
    tree = cKDTree(poly)
    _, idx = tree.query(q)
    M = len(poly)
    best = np.full(len(q), np.inf)
    for off in (-1, 0):
        a = poly[(idx + off) % M]
        b = poly[(idx + off + 1) % M]
        ab = b - a
        t = np.clip(((q - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
        best = np.minimum(best, np.hypot(*(q - (a + t[:, None] * ab)).T))
    return best


def shear_pts(pts: np.ndarray, shear: float, pivot_y: float) -> np.ndarray:
    """Cisaillement horizontal x' = x + shear·(y − pivot_y) : passe du dessin (droit) à la cible."""
    out = np.array(pts, dtype=float, copy=True)
    out[:, 0] += shear * (out[:, 1] - pivot_y)
    return out


def resample(path: Path, n: int) -> tuple[np.ndarray, np.ndarray]:
    """n échantillons équidistants le long du contour et poids √(L/n) : leur nombre ne dépend
    pas des segments, donc reste fixe quand la topologie d'une construction varie."""
    poly = polyline(path, 0.25)
    closed = np.vstack([poly, poly[:1]])
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(closed, axis=0).T))])
    u = (np.arange(n) + 0.5) / n * s[-1]
    pts = np.column_stack([np.interp(u, s, closed[:, 0]), np.interp(u, s, closed[:, 1])])
    return pts, np.full(n, math.sqrt(s[-1] / n))


def fit(build, p0: dict, target: Target, free: list[str] | None = None, lower: dict | None = None,
        reverse_weight: float = 1.0, max_nfev: int = 4000, pivot_y: float = 0.0,
        upper: dict | None = None, per_path: int | None = None):
    """Moindres carrés (perte soft-L1) : distance signée des échantillons du modèle au bord
    mesuré + distance des échantillons mesurés au modèle. `build(p)` renvoie une liste de Path.

    Si `p0` contient "shear", le dessin reste droit et c'est sa projection cisaillée (pivot
    `pivot_y`) qui est comparée à la cible : le cisaillement résiduel de la maquette est estimé
    au lieu d'être recopié.

    `per_path` : échantillonnage à nombre fixe par chemin (constructions dont le nombre de
    segments varie) ; une géométrie impossible (ValueError dans `build`) reçoit alors un
    résidu uniforme élevé au lieu d'interrompre l'ajustement."""
    keys = free or list(p0)
    fixed = {k: v for k, v in p0.items() if k not in keys}
    lower, upper = lower or {}, upper or {}

    def model(x):
        p = dict(fixed)
        p.update(zip(keys, x))
        return p

    def residuals(x):
        p = model(x)
        try:
            paths = build(p)
        except ValueError:
            if per_path is None:
                raise
            return np.full(n_res, 50.0)
        k = p.get("shear", 0.0)
        pts, w = zip(*(resample(pp, per_path) if per_path else sample(pp) for pp in paths))
        fwd = target.signed(shear_pts(np.vstack(pts), k, pivot_y)) * np.concatenate(w)
        poly = shear_pts(np.vstack([polyline(pp, 0.5) for pp in paths]), k, pivot_y)
        rev = poly_distance(target.samples, poly) * math.sqrt(0.5) * reverse_weight
        return np.concatenate([fwd, rev])

    x0 = np.array([p0[k] for k in keys], dtype=float)
    n_res = len(build(model(x0))) * (per_path or 0) + len(target.samples)
    lo = np.array([lower.get(k, -np.inf) for k in keys])
    hi = np.array([upper.get(k, np.inf) for k in keys])
    res = least_squares(residuals, x0, bounds=(lo, hi), loss="soft_l1",
                        f_scale=0.5, x_scale="jac", max_nfev=max_nfev)
    p = model(res.x)
    paths = build(p)
    poly = shear_pts(np.vstack([polyline(pp, 0.1) for pp in paths]), p.get("shear", 0.0), pivot_y)
    d = poly_distance(target.samples, poly)
    stats = {"nodes": sum(pp.nodes for pp in paths), "rms": round(float(np.sqrt(np.mean(d ** 2))), 3),
             "p95": round(float(np.percentile(d, 95)), 3), "max": round(float(d.max()), 3),
             "nfev": int(res.nfev), "status": int(res.status)}
    return p, stats


# ---------------------------------------------------------------- rendu

def rsvg_png(svg: str, width: int, height: int) -> np.ndarray:
    out = subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), "-f", "png"],
                         input=svg.encode(), capture_output=True, check=True).stdout
    with Image.open(io.BytesIO(out)) as im:
        return np.asarray(im.convert("RGBA"))


def render_coverage(ds: list[str], origin, scale: float, shape, shear: float = 0.0, pivot_y: float = 0.0) -> np.ndarray:
    """Couverture [0, 1] de chemins (unités du plan) rendus sur la grille d'un masque.

    Chaque chaîne de `ds` est un élément <path> : un glyphe et ses contre-formes doivent
    partager la même chaîne (règle nonzero, enroulements opposés). `shear` projette le
    dessin dans le repère cisaillé de la cible (voir shear_pts)."""
    h, w = shape
    paths = "".join(f'<path d="{d}" fill="#000"/>' for d in ds)
    skew = f"matrix(1 0 {shear} 1 {-shear * pivot_y} 0)"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<g transform="scale({scale}) translate({-origin[0]} {-origin[1]}) {skew}">{paths}</g></svg>')
    return rsvg_png(svg, w, h)[..., 3] / 255.0


def iou(a: np.ndarray, b: np.ndarray) -> float:
    return float((a & b).sum() / (a | b).sum())
