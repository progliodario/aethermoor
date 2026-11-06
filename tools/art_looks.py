"""The looks of the people: what makes each protagonist and each kind of villager different from the base figure.

Every look is a set of layers added to a part of the humanoid rig (head, torso, arm, leg) and drawn only with the palette
variant of that person (`only`), or with every variant but theirs (`except`). A look can be behind the part (a cape, a
ponytail) or in front of it (a hat, an apron). Used by `art_chars.py`; the coordinates are the ones of the part before its
canvas grows. Spec 13 describes `only` and `except`.
"""
from __future__ import annotations

from artkit import Recipe, linear

OUT = "$p.outline"
GOLD = "#D8B65A"
PROTAGONISTS = ["sakura", "daichi", "haruka", "marco", "yuki", "lena", "gideon"]
PEOPLE = ["red", "green", "ochre", "purple", "teal", "cream", "brown"]


def _look(r: Recipe, name: str, build, behind: bool = False) -> None:
    """Runs `build(x)` on a scratch recipe and merges its layers, in front or behind, for the variant `name`."""
    x = Recipe("x", r.w, r.h, seed=name)
    build(x)
    for layer in x.layers:
        layer["only"] = [name]
    r.layers = x.layers + r.layers if behind else r.layers + x.layers


def _except(r: Recipe, names: list[str], build) -> None:
    x = Recipe("x", r.w, r.h)
    build(x)
    for layer in x.layers:
        layer["except"] = list(names)
    r.layers += x.layers


def _glasses(x: Recipe, color: str = "#2A2A36") -> None:
    for cx in (8.0, 14.0):
        x.ellipse(cx, 12.7, 2.9, 3.0, "#BFE6FF", alpha=0.18, stroke=color, width=0.9)
    x.line(10.9, 12.2, 11.1, 12.2, color, width=0.9)
    x.line(5.2, 12.0, 3.2, 11.2, color, width=0.8)
    x.line(16.8, 12.0, 18.8, 11.2, color, width=0.8)
    x.path("M 6 11 Q 7 10.3 8.4 10.5", None, stroke="#FFFFFF", width=0.6, alpha=0.7)


def head_looks(r: Recipe) -> None:
    _except(r, PROTAGONISTS + PEOPLE, _glasses)  # Ren, the base look: glasses of a tired office worker

    def sakura_back(x: Recipe) -> None:  # two tails
        for sx in (-1, 1):
            c = 11 + sx * 11.4
            x.path(f"M {11 + sx * 8} 4 Q {c + sx * 4.5} 7 {c + sx * 3} 21 Q {c - sx * 0.5} 14 {11 + sx * 7} 9 Z", "$p.hair", stroke=OUT, width=1.2)
            x.path(f"M {c + sx * 2.4} 12 Q {c + sx * 1.2} 16 {c + sx * 2.2} 19", None, stroke="#000000", width=0.7, alpha=0.25)

    def sakura_front(x: Recipe) -> None:  # ribbons, goggles pushed up on the forehead
        for sx in (-1, 1):
            bx = 11 + sx * 8.4
            x.poly([(bx, 5), (bx + sx * 3.6, 2.8), (bx + sx * 3.6, 7.2)], "#FF6FA8", stroke=OUT, width=0.8)
            x.ellipse(bx, 5, 1.1, 1.1, "#FFD1E3", stroke=OUT, width=0.6)
        x.rect(2.8, 4.2, 16.4, 2.3, "#3A3A48", stroke=OUT, width=0.9)
        for cx in (7.2, 14.8):
            x.ellipse(cx, 5.3, 2.7, 2.2, "#7FDCFF", alpha=0.85, stroke=OUT, width=0.9)
            x.ellipse(cx - 0.8, 4.6, 0.8, 0.5, "#FFFFFF", alpha=0.9)

    _look(r, "sakura", sakura_back, behind=True)
    _look(r, "sakura", sakura_front)

    def daichi(x: Recipe) -> None:  # a firefighter's helmet with a badge, and a soot smudge
        x.path("M 1.4 8.6 Q 0.6 -1.6 11 -2 Q 21.4 -1.6 20.6 8.6 Z", linear(0, -2, 0, 9, (0, "#F2A03A"), (1, "#C45A1C")), stroke=OUT, width=1.3)
        x.path("M 9.4 -1.8 Q 11 -3.6 12.6 -1.8 L 12.4 8.4 L 9.6 8.4 Z", "#FFFFFF", alpha=0.22)
        x.path("M -0.4 8.2 Q 11 10.4 22.4 8.2 L 22 10 Q 11 12 0 10 Z", "#B04A16", stroke=OUT, width=1.1)
        x.poly([(8, 1.2), (14, 1.2), (14, 4.4), (11, 6.4), (8, 4.4)], "#F6E7B8", stroke=OUT, width=0.8)
        x.line(11, 2, 11, 5, "#C45A1C", width=0.8)
        x.ellipse(15.6, 16.4, 1.7, 1.0, "#000000", alpha=0.22)
        x.path("M 3 3 Q 6 -1 10 -1.4", None, stroke="#FFFFFF", width=1.0, alpha=0.4)

    _look(r, "daichi", daichi)

    def haruka_back(x: Recipe) -> None:  # a high ponytail
        x.path("M 12 2 Q 25 -2 23 15 Q 21 21 19 12 Q 18 7 14 6 Z", "$p.hair", stroke=OUT, width=1.2)
        x.path("M 19 5 Q 22 8 21.4 14", None, stroke="#FFFFFF", width=0.8, alpha=0.3)

    def haruka_front(x: Recipe) -> None:  # a green ribbon, a paw clip, freckles
        x.ellipse(15, 4.2, 1.8, 2.2, "#4FB06A", stroke=OUT, width=0.8)
        x.ellipse(5.2, 4.6, 1.3, 1.0, "#F2F2F2", stroke=OUT, width=0.6)
        for dx in (-0.9, 0, 0.9):
            x.ellipse(5.2 + dx, 3.6, 0.35, 0.4, "#F2F2F2", stroke=OUT, width=0.4)
        for fx, fy in ((6.6, 14.9), (7.6, 15.6), (15.4, 15.6), (16.4, 14.9)):
            x.ellipse(fx, fy, 0.35, 0.35, "#B8754A", alpha=0.75)

    _look(r, "haruka", haruka_back, behind=True)
    _look(r, "haruka", haruka_front)

    def marco(x: Recipe) -> None:  # a red bandana, a thick mustache and stubble
        x.path("M 1.6 8.4 Q 1.6 -0.4 11 -0.8 Q 20.4 -0.4 20.4 8.4 Q 11 4.2 1.6 8.4 Z", "#C9302C", stroke=OUT, width=1.2)
        for bx, by in ((6, 3.6), (10, 2.2), (14.6, 3), (17.6, 5.4), (3.8, 5.8), (11, 5)):
            x.ellipse(bx, by, 0.55, 0.55, "#FFFFFF", alpha=0.85)
        x.poly([(19.6, 5.4), (23.8, 3.2), (22.4, 7.6), (24, 10.4), (19.8, 8)], "#C9302C", stroke=OUT, width=0.9)
        x.path("M 6.4 16.4 Q 9 14.4 11 15.8 Q 13 14.4 15.6 16.4 Q 13 17.8 11 16.6 Q 9 17.8 6.4 16.4 Z", "#2A1E18", stroke=OUT, width=0.6)
        for sx, sy in ((6.5, 18.2), (8, 19.4), (11, 19.8), (14, 19.4), (15.5, 18.2), (9.5, 18.6), (12.5, 18.6)):
            x.ellipse(sx, sy, 0.3, 0.3, "#2A1E18", alpha=0.7)

    _look(r, "marco", marco)

    def yuki(x: Recipe) -> None:  # a black beret and a domino mask
        x.path("M 1 7.4 Q 0.6 -1.4 11 -1.2 Q 21 -1.4 21 6 Q 11 3 1 7.4 Z", "#26262E", stroke=OUT, width=1.2)
        x.path("M 3 3.4 Q 8 -0.4 14 0", None, stroke="#FFFFFF", width=0.9, alpha=0.25)
        x.ellipse(15.4, -1.6, 1.0, 1.0, "#26262E", stroke=OUT, width=0.7)
        x.path("M 3.6 10.2 Q 11 8.4 18.4 10.2 Q 19 13 17.4 15 Q 14.6 14 12.4 15.2 L 9.6 15.2 Q 7.4 14 4.6 15 Q 3 13 3.6 10.2 Z", "#1C1C24", stroke=OUT, width=0.8)
        for cx in (8.0, 14.0):
            x.ellipse(cx, 12.7, 1.7, 1.9, "#FFFFFF")
            x.ellipse(cx, 12.9, 1.15, 1.6, "#3E2E26")
            x.ellipse(cx, 13.1, 0.65, 1.0, OUT)
            x.ellipse(cx - 0.4, 12.3, 0.45, 0.5, "#FFFFFF")

    _look(r, "yuki", yuki)

    def lena_back(x: Recipe) -> None:  # a tight bun
        x.ellipse(11, -0.6, 4.6, 3.6, "$p.hair", stroke=OUT, width=1.2)
        x.path("M 8 -1.4 Q 11 -3 14 -1.4", None, stroke="#FFFFFF", width=0.8, alpha=0.3)

    def lena_front(x: Recipe) -> None:  # thin silver glasses and a white streak
        _glasses(x, "#B8C4D4")
        x.path("M 4.4 8.2 Q 3.6 5 6 3", None, stroke="#F2F2F8", width=1.6)

    _look(r, "lena", lena_back, behind=True)
    _look(r, "lena", lena_front)

    def gideon_back(x: Recipe) -> None:  # swept horns and pointed ears
        for sx in (-1, 1):
            c = 11 + sx * 6.4
            x.path(f"M {c - sx * 2} 5.4 Q {c + sx * 3.2} 0 {c + sx * 4.6} -7 Q {c + sx * 0.4} -2.4 {c + sx * 2.4} 6.4 Z", "#2B1B30", stroke=OUT, width=1.1)
            x.path(f"M {c + sx * 1} 3.4 Q {c + sx * 2.6} -0.6 {c + sx * 3.9} -5", None, stroke="#C7586A", width=0.7, alpha=0.8)
            x.poly([(11 + sx * 9.8, 10.5), (11 + sx * 14, 7.6), (11 + sx * 10.2, 14.6)], "$p.skin", stroke=OUT, width=1.0)

    def gideon_front(x: Recipe) -> None:  # red eyes, fangs, a golden circlet
        for cx in (8.0, 14.0):
            x.ellipse(cx, 12.9, 1.3, 1.8, "#D8283A")
            x.ellipse(cx, 13.0, 0.35, 1.5, "#1A0A10")
            x.ellipse(cx - 0.45, 12.2, 0.4, 0.45, "#FFFFFF")
        x.poly([(9.4, 17.4), (10.4, 17.4), (9.8, 19.2)], "#FFFFFF", stroke=OUT, width=0.4)
        x.poly([(11.8, 17.4), (12.8, 17.4), (12.2, 19.2)], "#FFFFFF", stroke=OUT, width=0.4)
        x.path("M 3.4 7.6 Q 11 5.2 18.6 7.6 L 18.4 9 Q 11 6.6 3.6 9 Z", GOLD, stroke=OUT, width=0.8)
        x.poly([(11, 5.2), (12.2, 7), (11, 8.8), (9.8, 7)], "#C92A3A", stroke=OUT, width=0.6)

    _look(r, "gideon", gideon_back, behind=True)
    _look(r, "gideon", gideon_front)

    # the people of the villages and the roads: one hat or hairdo each
    def red(x: Recipe) -> None:  # a guard: a cap with a rim
        x.path("M 1.6 8 Q 1.4 -0.6 11 -0.8 Q 20.6 -0.6 20.4 8 Q 11 5.6 1.6 8 Z", "#6E7280", stroke=OUT, width=1.2)
        x.rect(1.4, 6.6, 19.2, 1.8, "#8F94A4", stroke=OUT, width=0.8)
        x.path("M 11 -0.8 L 11 6", None, stroke="#4C505C", width=0.9)

    def green(x: Recipe) -> None:  # a ranger: a green hood
        x.path("M 0.6 12 Q -0.6 -1.6 11 -2.4 Q 22.6 -1.6 21.4 12 Q 19.6 6 11 5.2 Q 2.4 6 0.6 12 Z", "#3E7A48", stroke=OUT, width=1.2)
        x.path("M 3 6 Q 6 1 11 0.4", None, stroke="#FFFFFF", width=0.9, alpha=0.25)

    def ochre(x: Recipe) -> None:  # a farmer: a straw hat
        x.ellipse(11, 5.6, 12.4, 3.2, "#E3C77A", stroke=OUT, width=1.1)
        x.path("M 4.6 5 Q 5 -2.6 11 -2.6 Q 17 -2.6 17.4 5 Q 11 7 4.6 5 Z", "#EBD28E", stroke=OUT, width=1.1)
        x.rect(4.8, 3.2, 12.4, 1.6, "#A8503A")
        x.path("M 6 4 L 8 6.6 M 11 4.6 L 12.4 7 M 16 4 L 14.6 6.8", None, stroke="#C9A85A", width=0.6, alpha=0.8)

    def purple(x: Recipe) -> None:  # a mage: a tall pointed hat
        x.ellipse(11, 5.8, 11.6, 2.8, "#4F3C8A", stroke=OUT, width=1.1)
        x.path("M 4.4 5.6 Q 8 4 10 -3 Q 12 -8.5 15.4 -9 Q 14 -3 17.6 5.6 Q 11 7.4 4.4 5.6 Z", "#5E48A6", stroke=OUT, width=1.1)
        x.rect(4.6, 3.6, 13, 1.6, GOLD)
        x.ellipse(11, 2.8, 0.9, 0.9, "#FFF3B0")

    def teal(x: Recipe) -> None:  # a traveler: a headband and a bun
        x.ellipse(11, -0.8, 3.8, 3, "$p.hair", stroke=OUT, width=1.1)
        x.rect(2.4, 4.6, 17.2, 2.2, "#2E8AA6", stroke=OUT, width=0.9)
        x.path("M 19 5.4 L 23 8 L 20 8.6 L 23.4 12 L 18.6 7.8 Z", "#2E8AA6", stroke=OUT, width=0.8)

    def cream(x: Recipe) -> None:  # a baker: a tall white hat
        x.ellipse(7, 1.0, 4.4, 3.6, "#FFFFFF", stroke=OUT, width=1.0)
        x.ellipse(15, 1.0, 4.4, 3.6, "#FFFFFF", stroke=OUT, width=1.0)
        x.ellipse(11, -1.4, 5, 4, "#FFFFFF", stroke=OUT, width=1.0)
        x.rect(3.4, 3.2, 15.2, 4, "#F4F0E4", stroke=OUT, width=1.0)

    def brown(x: Recipe) -> None:  # a laborer: a flat cap and a bushy beard
        x.path("M 1.8 7.6 Q 1.4 0 11 -0.4 Q 20.6 0 20.2 7.6 Q 11 5 1.8 7.6 Z", "#6B4A32", stroke=OUT, width=1.1)
        x.path("M 12 6.2 Q 22 6 23 9.4 L 10 8.2 Z", "#58392A", stroke=OUT, width=0.9)
        x.path("M 4.4 15 Q 3.8 22.4 11 22.6 Q 18.2 22.4 17.6 15 Q 14 19 11 18.2 Q 8 19 4.4 15 Z", "$p.hair", stroke=OUT, width=1.0)

    for name, fn in (("red", red), ("green", green), ("ochre", ochre), ("purple", purple), ("teal", teal), ("cream", cream), ("brown", brown)):
        _look(r, name, fn)


def _coat(color: str, edge: str, lapel: str):
    def build(x: Recipe) -> None:
        x.path("M 2.4 3.2 L 8.2 3.8 L 7.4 24.4 Q 4.6 25 1.6 24.2 Z", color, stroke=OUT, width=1.2)
        x.path("M 19.6 3.2 L 13.8 3.8 L 14.6 24.4 Q 17.4 25 20.4 24.2 Z", color, stroke=OUT, width=1.2)
        x.path("M 8.2 3.8 L 11 10 L 7.6 12 Z", lapel, stroke=OUT, width=0.7)
        x.path("M 13.8 3.8 L 11 10 L 14.4 12 Z", lapel, stroke=OUT, width=0.7)
        x.rect(3.2, 15, 3.4, 4, edge, stroke=OUT, width=0.6)
        x.path("M 2 20.5 L 7.4 20.9", None, stroke="#000000", width=0.7, alpha=0.2)

    return build


def torso_looks(r: Recipe) -> None:
    def tie(x: Recipe) -> None:
        x.poly([(9.6, 5.2), (12.4, 5.2), (11.8, 8), (10.2, 8)], "#B8323A", stroke=OUT, width=0.7)
        x.poly([(10.2, 8), (11.8, 8), (12.8, 17.6), (11, 19.4), (9.2, 17.6)], "#B8323A", stroke=OUT, width=0.7)
        x.path("M 10.4 10 L 11.6 10 M 10.2 13 L 11.8 13", None, stroke="#FFFFFF", width=0.5, alpha=0.4)

    _except(r, PROTAGONISTS + PEOPLE, tie)

    _look(r, "sakura", _coat("#F4F6FA", "#DDE3EE", "#FFFFFF"))
    _look(r, "sakura", lambda x: (x.rect(4.4, 14.2, 1.1, 3.4, "#E04A4A"), x.rect(5.7, 14.6, 0.9, 3.0, "#4A7AE0")))
    _look(r, "lena", _coat("#2A2A36", "#3A3A48", "#E8ECF4"))
    _look(r, "lena", lambda x: (x.line(16, 4, 16.6, 13, "#9FB0C8", width=0.8), x.ellipse(16.6, 13.6, 1.2, 1.2, None, stroke="#9FB0C8", width=0.8)))

    def daichi(x: Recipe) -> None:  # reflective bands, suspenders, a pocket
        for y in (11.4, 15.6):
            x.rect(2.4, y, 17.2, 1.8, "#E8E24A", stroke=OUT, width=0.5)
            x.rect(2.6, y + 0.2, 16.8, 0.5, "#FFFFFF", alpha=0.6)
        for sx in (6.4, 15.6):
            x.rect(sx - 0.8, 3.2, 1.6, 17, "#2A2A36", alpha=0.9)
        x.rect(8.6, 4.2, 4.8, 3.2, "#2A2A36", stroke=OUT, width=0.6)

    _look(r, "daichi", daichi)

    def haruka(x: Recipe) -> None:  # a clinic apron with a green paw
        x.path("M 6.4 3.6 L 15.6 3.6 L 17.2 23.2 Q 11 24.6 4.8 23.2 Z", "#F2EFE6", stroke=OUT, width=1.1)
        x.path("M 6.4 3.6 L 4.6 1.4 M 15.6 3.6 L 17.4 1.4", None, stroke="#F2EFE6", width=1.2)
        x.ellipse(11, 12.6, 2.2, 1.8, "#4FB06A")
        for dx in (-2.2, -0.8, 0.8, 2.2):
            x.ellipse(11 + dx, 9.8 + abs(dx) * 0.3, 0.7, 0.9, "#4FB06A")
        x.rect(7.4, 17.4, 7.2, 4.2, "#E0DACB", stroke=OUT, width=0.6)

    _look(r, "haruka", haruka)

    def marco(x: Recipe) -> None:  # a striped cook's apron and a spanner badge
        x.path("M 4 11 L 18 11 L 19.6 24 Q 11 25.4 2.4 24 Z", "#FFFFFF", stroke=OUT, width=1.1)
        for sx in (6.4, 9.6, 12.8, 16):
            x.rect(sx - 0.6, 11.4, 1.2, 12, "#C9302C", alpha=0.55)
        x.path("M 4 11 L 5.6 3.4 M 18 11 L 16.4 3.4", None, stroke="#FFFFFF", width=1.3)
        x.rect(14.4, 19, 3.8, 2.6, "#C9302C", stroke=OUT, width=0.6)
        x.ellipse(4, 17.4, 2.3, 2.3, "#8A929C", stroke=OUT, width=0.8)
        x.ellipse(4, 17.4, 0.8, 0.8, "#4A505A")

    _look(r, "marco", marco)

    def yuki(x: Recipe) -> None:  # a long red scarf and a dark belt
        x.path("M 3.6 1.4 Q 11 6.4 18.4 1.4 L 19 5.4 Q 11 10.4 3 5.4 Z", "#C23A4A", stroke=OUT, width=1.0)
        x.path("M 4 3.4 Q 11 8 18 3.4", None, stroke="#8A2030", width=0.8)
        x.path("M 13.2 7 L 18.6 6.6 L 17.8 21 L 13 19.4 Z", "#C23A4A", stroke=OUT, width=1.0)
        x.path("M 13.6 12 L 18.2 12.4 M 13.4 16 L 18 16.6", None, stroke="#8A2030", width=0.9)
        x.rect(2.2, 19.6, 17.6, 1.6, "#1C1C24")

    _look(r, "yuki", yuki)

    def gideon_back(x: Recipe) -> None:  # a cape
        x.path("M 0.4 3 Q -3.4 15 -2.4 27.6 Q 11 30 24.4 27.6 Q 25.4 15 21.6 3 Z", linear(0, 3, 0, 28, (0, "#9C1E34"), (1, "#4A0E1E")), stroke=OUT, width=1.3)
        x.path("M 4 10 Q 2 20 3 27", None, stroke="#000000", width=0.8, alpha=0.3)
        x.path("M 18 10 Q 20 20 19 27", None, stroke="#000000", width=0.8, alpha=0.3)

    def gideon_front(x: Recipe) -> None:  # golden clasps and a sigil
        for cx in (3.4, 18.6):
            x.ellipse(cx, 3.8, 2.0, 2.0, GOLD, stroke=OUT, width=0.8)
            x.ellipse(cx, 3.8, 0.7, 0.7, "#C92A3A")
        x.path("M 4.6 2.2 Q 11 5.4 17.4 2.2", None, stroke=GOLD, width=1.2)
        x.poly([(11, 10), (13.4, 13.4), (11, 17), (8.6, 13.4)], None, stroke="#C92A3A", width=0.9)
        x.ellipse(11, 13.4, 1, 1, "#C92A3A")

    _look(r, "gideon", gideon_back, behind=True)
    _look(r, "gideon", gideon_front)

    _look(r, "green", lambda x: x.path("M 4 5 L 18 5 L 17 24 L 5 24 Z", "#355E3C", alpha=0.55, stroke=OUT, width=0.8))
    _look(r, "ochre", lambda x: (x.rect(2.4, 9, 17.2, 2.2, "#7A5A36", stroke=OUT, width=0.6), x.rect(9.4, 8.6, 3.2, 3, GOLD, stroke=OUT, width=0.5)))
    _look(r, "purple", lambda x: (x.path("M 2.2 3 L 11 8 L 19.8 3 L 20.4 24.6 L 1.6 24.6 Z", "#3E2E76", alpha=0.6), x.ellipse(11, 12, 1.4, 1.4, "#FFF3B0")))
    _look(r, "teal", lambda x: x.path("M 3.4 3 Q 11 12 18.6 3 L 18.8 6 Q 11 14 3.2 6 Z", "#2E8AA6", stroke=OUT, width=0.8))
    _look(r, "cream", lambda x: x.path("M 5 9 L 17 9 L 18.4 24 Q 11 25 3.6 24 Z", "#FFFFFF", stroke=OUT, width=0.9))
    _look(r, "brown", lambda x: (x.rect(2.6, 6, 3, 17, "#5A3E28", alpha=0.85), x.rect(16.4, 6, 3, 17, "#5A3E28", alpha=0.85)))
    _look(r, "red", lambda x: (x.path("M 4 4 L 18 4 L 17 17 Q 11 19 5 17 Z", "#6E7280", alpha=0.85, stroke=OUT, width=0.9), x.line(11, 4, 11, 17, "#4C505C", width=0.9)))


def arm_looks(r: Recipe) -> None:
    _except(r, PROTAGONISTS + PEOPLE, lambda x: (x.rect(1.2, 10.4, 5.6, 1.2, "#8A929C", stroke=OUT, width=0.4), x.rect(2.4, 10.5, 2.6, 0.9, "#F2F2F2", alpha=0.8)))
    _look(r, "sakura", lambda x: (x.rect(0.8, 1, 6.4, 10.6, "#F4F6FA", stroke=OUT, width=1.2), x.rect(0.8, 9.6, 6.4, 2, "#DDE3EE")))
    _look(r, "lena", lambda x: (x.rect(0.8, 1, 6.4, 10.6, "#2A2A36", stroke=OUT, width=1.2), x.rect(0.8, 9.8, 6.4, 1.8, "#E8ECF4"), x.ellipse(4, 13.3, 3, 2.9, "#DDE8F4", alpha=0.8, stroke=OUT, width=1.0)))
    _look(r, "daichi", lambda x: (x.rect(1, 4.4, 6, 1.8, "#E8E24A", stroke=OUT, width=0.5), x.rect(1.1, 9.4, 5.8, 2.6, "#2A2A36", stroke=OUT, width=0.6)))
    _look(r, "haruka", lambda x: (x.rect(1, 6, 6, 5.6, "$p.skin", stroke=OUT, width=1.0), x.rect(1, 8.8, 6, 1.4, "#4FB06A")))
    _look(r, "marco", lambda x: (x.rect(1, 5, 6, 6.6, "$p.skin", stroke=OUT, width=1.0), x.rect(1, 9.4, 6, 2.2, "#8A5A32", stroke=OUT, width=0.6)))
    _look(r, "yuki", lambda x: (x.ellipse(4, 13.3, 3, 2.9, "#1C1C24", stroke=OUT, width=1.0), x.rect(1, 9.4, 6, 2.4, "#1C1C24", stroke=OUT, width=0.6)))
    _look(r, "gideon", lambda x: (x.rect(0.6, 7.6, 6.8, 4, GOLD, stroke=OUT, width=0.9), x.poly([(1.6, 9), (3, 9), (2.3, 6.4)], GOLD, stroke=OUT, width=0.5), x.poly([(5, 9), (6.4, 9), (5.7, 6.4)], GOLD, stroke=OUT, width=0.5)))
    _look(r, "green", lambda x: x.rect(1, 9, 6, 2.6, "#355E3C", stroke=OUT, width=0.6))
    _look(r, "ochre", lambda x: x.rect(1, 9.4, 6, 2.2, "#7A5A36", stroke=OUT, width=0.6))
    _look(r, "purple", lambda x: x.path("M 0 8 L 8 8 L 9 12 L -1 12 Z", "#3E2E76", stroke=OUT, width=0.8))
    _look(r, "cream", lambda x: x.rect(1, 8.4, 6, 3, "#FFFFFF", stroke=OUT, width=0.6))
    _look(r, "red", lambda x: x.rect(1, 8.6, 6, 3, "#8F94A4", stroke=OUT, width=0.7))


def leg_looks(r: Recipe) -> None:
    _look(r, "sakura", lambda x: (x.rect(1.5, 6, 6, 4, "#F2F2F8", stroke=OUT, width=0.6), x.rect(0.6, 12.4, 7.8, 2.6, "#F2F2F8", stroke=OUT, width=0.8), x.rect(0.8, 13.4, 7.4, 0.8, "#E04A6A")))
    _look(r, "daichi", lambda x: (x.rect(0.6, 5.8, 7.8, 8.6, "#2A2A36", stroke=OUT, width=1.2), x.rect(0.7, 8.6, 7.6, 1.6, "#E8E24A"), x.rect(0.8, 6, 7.4, 1.2, "#FFFFFF", alpha=0.2)))
    _look(r, "haruka", lambda x: (x.path("M 0.5 7.4 L 8.5 7.4 Q 9 15 6 15 L 1 15 Q 0 13 0.5 7.4 Z", "#4FB06A", stroke=OUT, width=1.2), x.rect(0.7, 7.4, 7.6, 1.4, "#FFFFFF", alpha=0.25)))
    _look(r, "marco", lambda x: (x.rect(2.2, 4.4, 4.2, 3.4, "#7A6A46", stroke=OUT, width=0.7), x.line(2.2, 5.6, 6.4, 5.6, "#000000", width=0.5, alpha=0.4)))
    _look(r, "yuki", lambda x: (x.rect(1.5, 0, 6, 15, "#1C1C24", stroke=OUT, width=1.3), x.path("M 0.5 8.4 L 8.5 8.4 Q 9 15 6 15 L 1 15 Q 0 13 0.5 8.4 Z", "#26262E", stroke=OUT, width=1.2), x.rect(0.7, 8.6, 7.6, 1.2, "#C23A4A")))
    _look(r, "lena", lambda x: (x.rect(1.5, 0, 6, 9.6, "#2A2A36", stroke=OUT, width=1.3), x.path("M 0.5 9.4 L 8.5 9.4 Q 9 15 6 15 L 1 15 Q 0 13 0.5 9.4 Z", "#3A3A48", stroke=OUT, width=1.2)))
    _look(r, "gideon", lambda x: (x.path("M 0.3 7.4 L 8.7 7.4 Q 9.2 15 6 15 L 1 15 Q -0.2 13 0.3 7.4 Z", "#2B1B30", stroke=OUT, width=1.2), x.poly([(1, 8), (2.6, 8), (1.8, 5.6)], GOLD, stroke=OUT, width=0.5), x.poly([(5.4, 8), (7, 8), (6.2, 5.6)], GOLD, stroke=OUT, width=0.5), x.rect(0.5, 7.4, 8, 1.2, GOLD)))
    for name, c in (("green", "#355E3C"), ("ochre", "#6B4A32"), ("purple", "#3E2E76"), ("teal", "#245E70"), ("cream", "#E8E0CC"), ("brown", "#4A3424"), ("red", "#5A5E6A")):
        _look(r, name, lambda x, c=c: x.rect(1.5, 0, 6, 9.6, c, stroke=OUT, width=1.2))
