"""Mot-symbole PRIM : topologies construites à la main (angles vifs, droites et cubiques).

Paramètres partagés par les quatre lettres : ligne de capitale `yt`, ligne de base `yb`,
fût `s` (P, R, I), fût du M `sm`, épaisseur des traverses de panse `h`. Les positions et
poignées propres à chaque lettre sont ajustées par moindres carrés (construct.py).
"""
from __future__ import annotations

from geometry import Path


def bowl_outer(path: Path, p: dict, k: str) -> Path:
    """Panse extérieure (P, R) : du haut droit jusqu'au point bas de la courbe."""
    return (path.L((p[f"{k}xb"], p["yt"]))
            .C((p[f"{k}xb"] + p[f"{k}h1"], p["yt"]), (p[f"{k}xr"], p[f"{k}ym"] - p[f"{k}h2"]), (p[f"{k}xr"], p[f"{k}ym"])))


def counter(p: dict, k: str) -> Path:
    """Contre-forme de panse (sens inverse) : bord gauche sur l'intérieur du fût."""
    x0 = p[f"{k}x0"] + p["s"]
    top, bot = p["yt"] + p["h"], p[f"{k}yl"] - p["h"]
    return (Path((x0, top)).L((x0, bot)).L((p[f"{k}ixb2"], bot))
            .C((p[f"{k}ixb2"] + p[f"{k}ih4"], bot), (p[f"{k}ixr"], p[f"{k}iym"] + p[f"{k}ih3"]), (p[f"{k}ixr"], p[f"{k}iym"]))
            .C((p[f"{k}ixr"], p[f"{k}iym"] - p[f"{k}ih2"]), (p[f"{k}ixb"] + p[f"{k}ih1"], top), (p[f"{k}ixb"], top))
            .close())


def build_P(p: dict) -> list[Path]:
    x0 = p["Px0"]
    outer = Path((x0, p["yb"])).L((x0, p["yt"]))
    bowl_outer(outer, p, "P")
    outer.C((p["Pxr"], p["Pym"] + p["Ph3"]), (p["Pxb2"] + p["Ph4"], p["Pyl"]), (p["Pxb2"], p["Pyl"]))
    outer.L((x0 + p["s"], p["Pyl"])).L((x0 + p["s"], p["yb"])).close()
    return [outer, counter(p, "P")]


def build_R(p: dict) -> list[Path]:
    x0 = p["Rx0"]
    outer = Path((x0, p["yb"])).L((x0, p["yt"]))
    bowl_outer(outer, p, "R")
    # Bas de panse jusqu'au départ de la jambe (tangente verticale en sortie du point droit).
    outer.C((p["Rxr"], p["Rym"] + p["Rh3"]), (p["Rxj"] + p["Rh4"], p["Ryj"] - p["Rh5"]), (p["Rxj"], p["Ryj"]))
    outer.L((p["Rxlr"], p["yb"])).L((p["Rxll"], p["yb"])).L((p["Rxjl"], p["Ryl"]))
    outer.L((x0 + p["s"], p["Ryl"])).L((x0 + p["s"], p["yb"])).close()
    return [outer, counter(p, "R")]


def build_I(p: dict) -> list[Path]:
    x0 = p["Ix0"]
    return [Path((x0, p["yb"])).L((x0, p["yt"])).L((x0 + p["s"], p["yt"])).L((x0 + p["s"], p["yb"])).close()]


def build_M(p: dict) -> list[Path]:
    x0, x3, sm = p["Mx0"], p["Mx3"], p["sm"]
    return [Path((x0, p["yb"])).L((x0, p["yt"])).L((x0 + p["Ma"], p["yt"]))
            .L((p["Mxi"], p["Myi"]))
            .L((x3 - p["Mb"], p["yt"])).L((x3, p["yt"])).L((x3, p["yb"])).L((x3 - sm, p["yb"]))
            .L((x3 - sm, p["Myr"])).L((p["Mxo"] + p["Me"], p["Myo"])).L((p["Mxo"] - p["Me"], p["Myo"]))
            .L((x0 + sm, p["Myl"]))
            .L((x0 + sm, p["yb"])).close()]


LETTERS = {"P": build_P, "R": build_R, "I": build_I, "M": build_M}


def build_all(p: dict) -> list[Path]:
    return [path for build in LETTERS.values() for path in build(p)]


def glyph_ds(p: dict) -> dict[str, str]:
    """Données SVG par lettre : silhouette et contre-forme dans le même chemin (nonzero)."""
    from geometry import to_d
    return {k: "".join(to_d(pp) for pp in build(p)) for k, build in LETTERS.items()}


def initial() -> dict:
    """Valeurs de départ relevées sur le masque redressé (unités du plan)."""
    p = {"yt": 966.0, "yb": 1098.0, "s": 35.0, "sm": 31.5, "h": 30.0, "shear": 0.0}
    for k, x0, xb, xr, yl in (("P", 675.0, 740.0, 790.0, 1062.0), ("R", 830.0, 885.0, 942.0, 1060.0)):
        p.update({f"{k}x0": x0, f"{k}xb": xb, f"{k}xr": xr, f"{k}ym": 1013.0, f"{k}yl": yl,
                  f"{k}h1": 28.0, f"{k}h2": 26.0, f"{k}h3": 26.0, f"{k}h4": 28.0,
                  f"{k}ixb": xb - 2, f"{k}ixb2": xb - 2, f"{k}ixr": xr - 37, f"{k}iym": 1013.0,
                  f"{k}ih1": 9.0, f"{k}ih2": 9.0, f"{k}ih3": 9.0, f"{k}ih4": 9.0})
    p.update({"Pxb2": 740.0, "Rxj": 928.0, "Ryj": 1052.0, "Rh5": 6.0,
              "Rxlr": 952.0, "Rxll": 922.0, "Rxjl": 900.0,
              "Ix0": 989.0,
              "Mx0": 1072.0, "Mx3": 1221.0, "Ma": 29.0, "Mb": 32.0, "Mxi": 1147.5, "Myi": 1035.0,
              "Myr": 1037.0, "Mxo": 1146.0, "Myo": 1082.0, "Myl": 1043.0, "Me": 4.0})
    return p


LOWER = {k: 0.5 for k in ("s", "sm", "h", "Ph1", "Ph2", "Ph3", "Ph4", "Rh1", "Rh2", "Rh3", "Rh4", "Rh5",
                          "Pih1", "Pih2", "Pih3", "Pih4", "Rih1", "Rih2", "Rih3", "Rih4", "Ma", "Mb")} | {"Me": 0.0}
