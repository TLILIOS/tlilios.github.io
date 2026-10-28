"""Emblème Prim (bouclier à monogramme P · N · J) : construction à la main, bandes d'épaisseur constante.

Trois brins de même épaisseur `t` :
- P : flanc gauche du bouclier (fût), bandeau du haut, panse (arc C1, verticale, arc C2) et traverse ;
- N : deux fûts verticaux et une diagonale, symétrique par rapport à son centre (nu, nv) ;
- J : flanc droit, crochet du haut. Le pied du bouclier réunit P et J à la pointe.
Entrelacs : la traverse passe sur le fût gauche du N ; la diagonale du N passe sur la panse ;
la panse passe sur le fût droit du N ; le crochet du J s'arrête contre la panse. Le brin du
dessous est coupé à distance `g` du brin du dessus (crochet : `gj`), parallèlement aux droites
et concentriquement aux arcs. Le fût droit du N s'arrête au creux exact qu'il forme avec la
diagonale : cette contrainte fixe le rayon de l'arc bas de la panse.

Contour exact : droites et arcs de cercle, sommets calculés par intersection (aucune
vectorisation). Deux chemins, même sens de parcours (règle nonzero) : le cadre, d'un seul
tenant (P, J et pied du fût gauche du N), et l'îlot du N.
"""
from __future__ import annotations

import math

import numpy as np

from geometry import Path

# ---------------------------------------------------------------- primitives

class Line:
    """Droite infinie p + s·d (d unitaire)."""

    def __init__(self, p, d):
        self.p = np.asarray(p, dtype=float)
        d = np.asarray(d, dtype=float)
        self.d = d / math.hypot(*d)

    def at(self, s: float) -> np.ndarray:
        return self.p + s * self.d

    def param(self, q) -> float:
        return float((np.asarray(q, dtype=float) - self.p) @ self.d)


def hline(v: float) -> Line:
    return Line((0.0, v), (1.0, 0.0))


def vline(u: float) -> Line:
    return Line((u, 0.0), (0.0, 1.0))


def meet(a: Line, b: Line) -> np.ndarray:
    s = np.linalg.solve(np.column_stack([a.d, -b.d]), b.p - a.p)
    return a.at(s[0])


def circle_hits(line: Line, c, r: float) -> tuple[np.ndarray, np.ndarray]:
    """Les deux intersections droite/cercle, dans l'ordre de la droite."""
    w = line.p - np.asarray(c, dtype=float)
    b = float(w @ line.d)
    disc = b * b - (float(w @ w) - r * r)
    if disc < 0:
        raise ValueError("droite et cercle disjoints")
    s = math.sqrt(disc)
    return line.at(-b - s), line.at(-b + s)


def ang(c, q) -> float:
    return math.atan2(q[1] - c[1], q[0] - c[0])


# Segment de chaîne : ("L", p0, p1) ou ("A", centre, rayon, p0, p1, sweep) ;
# sweep = 1 : sens horaire à l'écran (angle croissant, y vers le bas).

def seg_L(p0, p1) -> tuple:
    return ("L", np.asarray(p0, dtype=float), np.asarray(p1, dtype=float))


def seg_A(c, r, p0, p1, sweep: int) -> tuple:
    return ("A", np.asarray(c, dtype=float), float(r), np.asarray(p0, dtype=float), np.asarray(p1, dtype=float), sweep)


def end_of(seg) -> np.ndarray:
    return seg[2] if seg[0] == "L" else seg[4]


def start_of(seg) -> np.ndarray:
    return seg[1] if seg[0] == "L" else seg[3]


def _span(seg) -> tuple[float, float]:
    """Angles de départ et d'arrivée d'un arc, déroulés dans le sens du parcours."""
    _, c, _, p0, p1, sweep = seg
    a0, a1 = ang(c, p0), ang(c, p1)
    if sweep and a1 < a0:
        a1 += 2 * math.pi
    if not sweep and a1 > a0:
        a1 -= 2 * math.pi
    return a0, a1


def _frac_on(seg, q) -> float | None:
    """Position relative [0, 1] de q sur le segment (None si hors du segment)."""
    if seg[0] == "L":
        p0, p1 = seg[1], seg[2]
        v = p1 - p0
        n2 = float(v @ v)
        if n2 < 1e-18:
            return None
        f = float((q - p0) @ v) / n2
        return f if -1e-9 <= f <= 1 + 1e-9 else None
    a0, a1 = _span(seg)
    a = ang(seg[1], q)
    for k in (-1, 0, 1):
        x = a + 2 * math.pi * k
        f = (x - a0) / (a1 - a0) if abs(a1 - a0) > 1e-12 else None
        if f is not None and -1e-9 <= f <= 1 + 1e-9:
            return f
    return None


def hits(chain: list, line: Line) -> list[tuple[float, np.ndarray]]:
    """Intersections d'une droite avec une chaîne, triées dans l'ordre de la chaîne."""
    out = []
    for i, seg in enumerate(chain):
        if seg[0] == "L":
            p0, p1 = seg[1], seg[2]
            v = p1 - p0
            if math.hypot(*v) < 1e-12:
                continue
            m = np.column_stack([v, -line.d])
            if abs(np.linalg.det(m)) < 1e-12:
                continue
            f, _ = np.linalg.solve(m, line.p - p0)
            if -1e-9 <= f <= 1 + 1e-9:
                out.append((i + float(f), p0 + f * v))
        else:
            try:
                cand = circle_hits(line, seg[1], seg[2])
            except ValueError:
                continue
            for q in cand:
                f = _frac_on(seg, q)
                if f is not None:
                    out.append((i + f, q))
    out.sort(key=lambda h: h[0])
    return out


def first_hit(chain: list, line: Line, after: float = -1.0) -> tuple[float, np.ndarray]:
    for pos, q in hits(chain, line):
        if pos > after + 1e-9:
            return pos, q
    raise ValueError("aucune intersection sur la chaîne")


def sub(chain: list, pos0: float, q0, pos1: float, q1) -> list:
    """Portion de chaîne entre deux positions (pos0 ≤ pos1), extrémités q0 et q1."""
    i0 = min(int(math.floor(pos0)), len(chain) - 1)
    i1 = min(int(math.floor(pos1)), len(chain) - 1)
    out = []
    for i in range(i0, i1 + 1):
        seg = chain[i]
        a = q0 if i == i0 else start_of(seg)
        b = q1 if i == i1 else end_of(seg)
        out.append(seg_L(a, b) if seg[0] == "L" else seg_A(seg[1], seg[2], a, b, seg[5]))
    return out


def reverse(chain: list) -> list:
    out = []
    for seg in reversed(chain):
        if seg[0] == "L":
            out.append(seg_L(seg[2], seg[1]))
        else:
            out.append(seg_A(seg[1], seg[2], seg[4], seg[3], 1 - seg[5]))
    return out


def to_path(chain: list, eps: float = 1e-6) -> Path:
    """Chaîne fermée → Path (segments de longueur nulle omis)."""
    segs = [s for s in chain if math.hypot(*(end_of(s) - start_of(s))) > eps]
    path = Path(start_of(segs[0]))
    for s in segs:
        if s[0] == "L":
            path.L(end_of(s))
        else:
            path.A(s[1], s[4], s[5])
    return path.close()


# ---------------------------------------------------------------- construction

def shield_chains(uL: float, uR: float, top: float, rc: float, t: float, beta_deg: float, ax: float,
                  pt: float, rf: float) -> dict:
    """Silhouette (sens horaire depuis le coin haut gauche) et bord intérieur du cadre, décalé de t."""
    beta = math.radians(beta_deg)
    sb, cb = math.sin(beta), math.cos(beta)
    P0 = np.array([ax, pt])                                # pointe
    nL, nR = np.array([sb, -cb]), np.array([-sb, -cb])     # normales intérieures des pans du pied
    if rf <= t + 1e-3 or rc <= 1e-3:
        raise ValueError("rayons de raccord incompatibles avec l'épaisseur")
    vF = pt + ((uL + rf - ax) * sb - rf) / cb              # hauteur des centres des raccords bas
    if vF <= top + rc:
        raise ValueError("raccord bas au-dessus des coins")
    FL, FR = np.array([uL + rf, vF]), np.array([uR - rf, vF])
    tipi = np.array([ax, pt - t / cb])                     # pointe intérieure
    TL, TR = np.array([uL + rc, top + rc]), np.array([uR - rc, top + rc])
    tR, tL = FR - rf * nR, FL - rf * nL                    # tangences des pans du pied
    outer = [seg_L((uL + rc, top), (uR - rc, top)),
             seg_A(TR, rc, (uR - rc, top), (uR, top + rc), 1),
             seg_L((uR, top + rc), (uR, vF)),
             seg_A(FR, rf, (uR, vF), tR, 1),
             seg_L(tR, P0), seg_L(P0, tL),
             seg_A(FL, rf, tL, (uL, vF), 1),
             seg_L((uL, vF), (uL, top + rc)),
             seg_A(TL, rc, (uL, top + rc), (uL + rc, top), 1)]
    ri = rf - t
    tLi, tRi = FL - ri * nL, FR - ri * nR
    inner = [seg_L((uL + t, top + t), (uL + t, vF)),
             seg_A(FL, ri, (uL + t, vF), tLi, 0),
             seg_L(tLi, tipi), seg_L(tipi, tRi),
             seg_A(FR, ri, tRi, (uR - t, vF), 0),
             seg_L((uR - t, vF), (uR - t, top + t))]
    return {"outer": outer, "inner": inner, "tip": P0, "tip_in": tipi}


def bowl_chains(uL: float, top: float, t: float, ub: float, vcb: float, R1: float, R2: float) -> dict:
    """Bords extérieur et intérieur du brin P depuis le bandeau du haut jusqu'au fût : bandeau,
    arc C1 (rayon d'axe R1), verticale, arc C2 (R2), traverse. Arcs tangents, épaisseur t."""
    if R1 < 0.5 * t or R2 < 0.5 * t:
        raise ValueError("panse trop serrée pour l'épaisseur")
    v1 = top + 0.5 * t
    C1, C2 = np.array([ub - R1, v1 + R1]), np.array([ub - R2, vcb - R2])
    if C2[1] < C1[1] - 1e-9:
        raise ValueError("arcs de la panse en recouvrement")
    chains = {}
    for name, e, x0, y_top in (("outer", 0.5 * t, uL, top), ("inner", -0.5 * t, uL + t, top + t)):
        chains[name] = [seg_L((x0, y_top), (C1[0], y_top)),
                        seg_A(C1, R1 + e, (C1[0], y_top), (ub + e, C1[1]), 1),
                        seg_L((ub + e, C1[1]), (ub + e, C2[1])),
                        seg_A(C2, R2 + e, (ub + e, C2[1]), (C2[0], vcb + e), 1),
                        seg_L((C2[0], vcb + e), (uL + t, vcb + e))]
    return {"P_outer": chains["outer"], "P_inner": chains["inner"], "C1": C1, "C2": C2}


def hook(C1, R1o: float, gj: float, top: float, t: float, uR: float, rc: float) -> tuple[np.ndarray, np.ndarray, float]:
    """Crochet du J : coupure concentrique à C1, à gj du bord extérieur de la panse."""
    Rj = R1o + gj
    H1 = max(circle_hits(hline(top + t), C1, Rj), key=lambda q: q[0])
    H2 = max(circle_hits(hline(top), C1, Rj), key=lambda q: q[0])
    if not (C1[0] < H2[0] < uR - rc and H1[0] < uR - t):
        raise ValueError("crochet du J dégénéré")
    return H1, H2, Rj


def construct(p: dict) -> dict:
    """Points, droites et chaînes de l'emblème complet (unités du plan)."""
    t, g, gj = p["t"], p["g"], p["gj"]
    uL, uR, top, rc = p["ax"] - p["hw"], p["ax"] + p["hw"], p["top"], p["rc"]
    sh = shield_chains(uL, uR, top, rc, t, p["beta"], p["ax"], p["pt"], p["rf"])
    outer, inner = sh["outer"], sh["inner"]

    # N : symétrie centrale autour de nc ; diagonale d'axe passant par nc.
    nc = np.array([p["nu"], p["nv"]])
    a, b = p["nu"] - p["nw"], p["nu"] + p["nw"]
    y0, y1 = p["nv"] - p["nh"], p["nv"] + p["nh"]
    th = math.radians(p["th"])
    d = np.array([math.sin(th), math.cos(th)])             # vers le bas à droite
    n = np.array([math.cos(th), -math.sin(th)])            # vers le haut à droite
    D_up, D_lo = Line(nc + 0.5 * t * n, d), Line(nc - 0.5 * t * n, d)
    D_upg, D_log = Line(nc + (0.5 * t + g) * n, d), Line(nc - (0.5 * t + g) * n, d)
    V = meet(D_up, vline(b - t))                          # creux diagonale / fût droit
    W = meet(D_lo, vline(a + t))                          # creux diagonale / fût gauche
    N1, N5 = meet(D_up, hline(y0)), meet(D_lo, hline(y1))

    # Panse : rayon de l'arc bas imposé par le creux V (coupure g, concentrique à C2).
    ub, vcb, sv = p["ub"], p["vcb"], p["sv"]
    k = 0.5 * t + g
    pp, qq = V[0] - ub, V[1] - vcb
    B = pp + qq - k
    disc = B * B - (pp * pp + qq * qq - k * k)
    if disc < 0:
        raise ValueError("creux du N hors de portée de la panse")
    R2 = -B + math.sqrt(disc)
    R1 = vcb - (top + 0.5 * t) - R2 - sv
    if R1 < 0.5 * t + 1 or R2 < 0.5 * t + 1:
        raise ValueError("panse trop serrée pour l'épaisseur")
    bw = bowl_chains(uL, top, t, ub, vcb, R1, R2)
    P_outer, P_inner, C1, C2 = bw["P_outer"], bw["P_inner"], bw["C1"], bw["C2"]
    P_outer[0] = seg_L((uL + rc, top), (C1[0], top))
    R2o = R2 + 0.5 * t
    H1, H2, Rj = hook(C1, R1 + 0.5 * t, gj, top, t, uR, rc)

    # Coupures.
    pos_tip, P_tip = first_hit(P_outer, D_upg, after=2.999)   # sur l'arc C2 extérieur
    tip_s = D_upg.param(P_tip)
    cand = [(D_upg.param(q), pos, q) for pos, q in hits(P_inner, D_upg) if D_upg.param(q) < tip_s - 1e-9]
    if not cand:
        raise ValueError("coupure de la panse introuvable")
    _, pos_ti, P_ti = max(cand, key=lambda c: c[0])
    pos_x1, X1 = first_hit(P_inner, D_log, after=pos_ti)
    pos_x2, X2 = first_hit(P_outer, D_log, after=pos_tip)
    pos_jt, Jt = first_hit(inner, hline(vcb - 0.5 * t))
    pos_jb, Jb = first_hit(inner, hline(vcb + 0.5 * t), after=pos_jt)
    f_jt, f_jb = _frac_on(P_inner[-1], Jt), _frac_on(P_outer[-1], Jb)
    if f_jt is None or f_jb is None:
        raise ValueError("traverse hors du fût")
    pos_b1, B1 = first_hit(inner, vline(a), after=pos_jb)
    pos_b2, B2 = first_hit(inner, vline(a + t), after=pos_b1)
    Rs = R2o + g                                           # coupure du fût droit, concentrique à C2
    N3 = max(circle_hits(vline(b), C2, Rs), key=lambda q: q[1])
    vcut_top, vcut_bot = vcb - 0.5 * t - g, vcb + 0.5 * t + g
    if not (y0 < W[1] < vcut_top and N3[1] < y1 and V[1] < y1 and vcut_bot < B1[1] and N1[0] < b - t):
        raise ValueError("N incompatible avec la traverse ou le pied")

    # Cadre : un seul contour.
    span = (uR - rc) - (uL + rc)
    pos_h2, pos_c1 = (H2[0] - (uL + rc)) / span, (C1[0] - (uL + rc)) / span
    frame = (sub(outer, pos_h2, H2, float(len(outer)), end_of(outer[-1]))
             + sub(outer, 0.0, start_of(outer[0]), pos_c1, np.array([C1[0], top]))
             + sub(P_outer, 1.0, start_of(P_outer[1]), pos_tip, P_tip)
             + [seg_L(P_tip, P_ti)]
             + reverse(sub(P_inner, 0.0, start_of(P_inner[0]), pos_ti, P_ti))
             + sub(inner, 0.0, start_of(inner[0]), pos_jt, Jt)
             + reverse(sub(P_inner, pos_x1, X1, len(P_inner) - 1 + f_jt, Jt))
             + [seg_L(X1, X2)]
             + sub(P_outer, pos_x2, X2, len(P_outer) - 1 + f_jb, Jb)
             + sub(inner, pos_jb, Jb, pos_b1, B1)
             + [seg_L(B1, (a, vcut_bot)), seg_L((a, vcut_bot), (a + t, vcut_bot)), seg_L((a + t, vcut_bot), B2)]
             + sub(inner, pos_b2, B2, float(len(inner)), end_of(inner[-1]))
             + [seg_L((uR - t, top + t), H1), seg_A(C1, Rj, H1, H2, 0)])
    island = [seg_L((a, y0), N1), seg_L(N1, V), seg_A(C2, Rs, V, N3, 0), seg_L(N3, (b, y1)),
              seg_L((b, y1), N5), seg_L(N5, W), seg_L(W, (a + t, vcut_top)),
              seg_L((a + t, vcut_top), (a, vcut_top)), seg_L((a, vcut_top), (a, y0))]
    return {"frame": frame, "island": island, "C1": C1, "C2": C2, "R1": R1, "R2": R2,
            "points": {"H1": H1, "H2": H2, "P_tip": P_tip, "P_ti": P_ti, "X1": X1, "X2": X2, "B1": B1, "B2": B2,
                       "V": V, "W": W, "N1": N1, "N3": N3, "N5": N5, "tip_in": sh["tip_in"], "tip": sh["tip"]},
            "box": (uL, top, uR, p["pt"])}


# Variante ≤ 32 px, en pixels de la tuile de 16 : bouclier x 3–13, y 2–14 (axe x = 8), épaisseur
# 2 px, panse à deux arcs de rayon d'axe 2 (centres C1 = (7, 5), C2 = (7, 6)) reliés par 1 px de
# verticale, contre-forme du P 3 × 3 px, couloir et encoche du J 1 px. Le N, ses coupures et le
# pied de son fût sont retirés : à 16 px, ses onze alternances plein/vide ne tiennent pas en 10 px.
SMALL = {"uL": 3.0, "uR": 13.0, "top": 2.0, "pt": 14.0, "t": 2.0, "ub": 9.0, "vcb": 8.0,
         "R1": 2.0, "R2": 2.0, "rf": 5.0, "gj": 1.0}


def construct_small(beta_deg: float, s: dict = SMALL) -> dict:
    """Cadre, P (panse et traverse) et crochet du J ; angle du pied repris de l'emblème complet."""
    t, uL, uR, top, rc = s["t"], s["uL"], s["uR"], s["top"], 0.5 * s["t"]
    ax = 0.5 * (uL + uR)
    sh = shield_chains(uL, uR, top, rc, t, beta_deg, ax, s["pt"], s["rf"])
    outer, inner = sh["outer"], sh["inner"]
    bw = bowl_chains(uL, top, t, s["ub"], s["vcb"], s["R1"], s["R2"])
    P_outer, P_inner, C1 = bw["P_outer"], bw["P_inner"], bw["C1"]
    H1, H2, Rj = hook(C1, s["R1"] + 0.5 * t, s["gj"], top, t, uR, rc)
    vcb = s["vcb"]
    pos_jt, Jt = first_hit(inner, hline(vcb - 0.5 * t))
    pos_jb, Jb = first_hit(inner, hline(vcb + 0.5 * t), after=pos_jt)
    f_jt, f_jb = _frac_on(P_inner[-1], Jt), _frac_on(P_outer[-1], Jb)
    if f_jt is None or f_jb is None:
        raise ValueError("traverse hors du fût")
    span = (uR - rc) - (uL + rc)
    pos_h2, pos_c1 = (H2[0] - (uL + rc)) / span, (C1[0] - (uL + rc)) / span
    frame = (sub(outer, pos_h2, H2, float(len(outer)), end_of(outer[-1]))
             + sub(outer, 0.0, start_of(outer[0]), pos_c1, np.array([C1[0], top]))
             + sub(P_outer, 1.0, start_of(P_outer[1]), len(P_outer) - 1 + f_jb, Jb)
             + sub(inner, pos_jb, Jb, float(len(inner)), end_of(inner[-1]))
             + [seg_L((uR - t, top + t), H1), seg_A(C1, Rj, H1, H2, 0)])
    # Contre-forme du P : boucle parcourue en sens inverse (trou en règle nonzero).
    counter = reverse(sub(P_inner, 0.0, start_of(P_inner[0]), len(P_inner) - 1 + f_jt, Jt)
                      + reverse(sub(inner, 0.0, start_of(inner[0]), pos_jt, Jt)))
    return {"frame": frame, "counter": counter, "points": {"H1": H1, "H2": H2, "Jt": Jt, "Jb": Jb}}


def build_small(beta_deg: float) -> list[Path]:
    c = construct_small(beta_deg)
    return [to_path(c["frame"]), to_path(c["counter"])]


def build(p: dict) -> list[Path]:
    c = construct(p)
    return [to_path(c["frame"]), to_path(c["island"])]


def dims(p: dict) -> dict:
    """Cotes de la construction (rapport, planche)."""
    c = construct(p)
    uL, uR = p["ax"] - p["hw"], p["ax"] + p["hw"]
    a, b = p["nu"] - p["nw"], p["nu"] + p["nw"]
    return {"t": p["t"], "g": p["g"], "gj": p["gj"], "rc": p["rc"], "rf": p["rf"], "beta_deg": p["beta"],
            "theta_deg": p["th"], "R1_axis": c["R1"], "R2_axis": c["R2"],
            "counter_left": a - (uL + p["t"]), "counter_right": (uR - p["t"]) - b,
            "counter_top": (p["nv"] - p["nh"]) - (p["top"] + p["t"]),
            "width": uR - uL, "height": p["pt"] - p["top"]}


def regular(q: dict) -> dict:
    """Règles de régularité appliquées au jeu réduit `q` (ajusté sur la maquette) :
    coins du haut au rayon t/2 ; panse sans verticale (arcs C1 et C2 tangents au point le plus
    à droite) ; N centré sur l'axe du bouclier ; contre-formes égales `c` à gauche, à droite et
    au-dessus du N."""
    t, c = q["t"], q["c"]
    y0 = q["top"] + t + c
    return {"ax": q["ax"], "hw": q["hw"], "top": q["top"], "rc": 0.5 * t, "t": t, "beta": q["beta"],
            "pt": q["pt"], "rf": q["rf"], "g": q["g"], "gj": q["gj"], "ub": q["ub"], "vcb": q["vcb"], "sv": 0.0,
            "nu": q["ax"], "nv": 0.5 * (y0 + q["y1"]), "nw": q["hw"] - t - c, "nh": 0.5 * (q["y1"] - y0),
            "th": q["th"], "shear": q.get("shear", 0.0)}


def build_regular(q: dict) -> list[Path]:
    return build(regular(q))


def initial() -> dict:
    """Valeurs de départ (jeu réduit) relevées sur le masque redressé, unités du plan."""
    return {"ax": 940.5, "hw": 195.0, "top": 460.0, "t": 50.0, "beta": 26.0, "pt": 920.5, "rf": 150.0,
            "g": 11.0, "gj": 22.0, "ub": 1025.7, "vcb": 705.0, "c": 36.0, "y1": 779.5, "th": 36.4, "shear": 0.0}


LOWER = {"t": 20.0, "g": 3.0, "gj": 3.0, "beta": 5.0, "th": 5.0, "c": 5.0}
