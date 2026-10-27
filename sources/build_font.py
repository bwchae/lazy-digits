"""Lazy Digits: digits + a few symbols as a real TrueType font, built from geometric parts (squircle rings, bars,
diagonals) united with skia-pathops, so the outlines are proper cubic curves (converted to TrueType quadratics).
Writes LazyDigits-<variant>.ttf; variant R = round-top 3, F = flat-top (Omata-like) 3.
Usage: build_font.py <out dir>"""
import math
import sys

import pathops
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
UPM = 1000
VERSION = '1.000'
H = 700            # digit (cap) height
W = 420            # digit body width (0.60 H)
TV = 124           # vertical stroke
TH = 110           # horizontal stroke (thinner, optical balance)
SB = 35            # side bearing -> tabular advance W + 2 SB
ADV = W + 2 * SB
R = 0.40           # bowl corner radius / bowl width
K = 0.72           # cubic handle factor: 0.55 ~ circle, higher ~ squircle
SP = 0.53 * H      # centre of the middle stroke (8, 3, 5)
# Design choices (compare_options.py builds A/B fonts that differ in one of them)
THREE = 'F'        # R: round-top 3, F: flat-top (Omata-like)
ONE_BASE = False   # 1 with a foot
FOUR = 'open'      # open: open top, closed: diagonal from the stem top
TAIL = 0.86        # 6 / 9 terminal end, share of the width
ZERO_R = 0.47      # 0 corner radius / width (0.40 = same squircle as the bowls)
SEVEN_X = 0.32     # 7 foot position, share of the width
COLON_MID = 0.50   # colon centre, share of H (0.35: lower dot on the baseline; 0.50: centred - picked 2026-10-27)
MINUS_Y = 0.42     # minus centre, share of H
ONE_DROP = 0.09    # 1 flag: drop over its length, share of H (0.09 ~ 27 deg at width 0.60; picked 2026-10-27)
DOT = round(TV * 1.08)


def configure(**kw):
    """Set design parameters and the values derived from them."""
    g = globals()
    g.update(kw)
    g['ADV'] = g['W'] + 2 * g['SB']
    g['DOT'] = round(g['TV'] * 1.08)


# ---------- path helpers (y up) ----------
def rrect(x0, y0, x1, y1, r, k=None, radii=None):
    """Rounded rectangle, corner order bl, br, tr, tl."""
    k = K if k is None else k
    bl, br, tr, tl = radii if radii else (r, r, r, r)
    m = min(x1 - x0, y1 - y0) / 2
    bl, br, tr, tl = (min(v, m) for v in (bl, br, tr, tl))
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo((x0 + bl, y0))
    pen.lineTo((x1 - br, y0))
    if br:
        pen.curveTo((x1 - br + k * br, y0), (x1, y0 + br - k * br), (x1, y0 + br))
    pen.lineTo((x1, y1 - tr))
    if tr:
        pen.curveTo((x1, y1 - tr + k * tr), (x1 - tr + k * tr, y1), (x1 - tr, y1))
    pen.lineTo((x0 + tl, y1))
    if tl:
        pen.curveTo((x0 + tl - k * tl, y1), (x0, y1 - tl + k * tl), (x0, y1 - tl))
    pen.lineTo((x0, y0 + bl))
    if bl:
        pen.curveTo((x0, y0 + bl - k * bl), (x0 + bl - k * bl, y0), (x0 + bl, y0))
    pen.closePath()
    return p


def rect(x0, y0, x1, y1):
    return rrect(x0, y0, x1, y1, 0)


def poly(pts):
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath()
    return p


def ring(x0, y0, x1, y1, r, tv=None, th=None, k=None, radii=None):
    tv = TV if tv is None else tv
    th = TH if th is None else th
    outer = rrect(x0, y0, x1, y1, r, k, radii)
    ri = max(r - (tv + th) / 2, r * 0.3)
    iradii = None if radii is None else tuple(max(v - (tv + th) / 2, v * 0.3) for v in radii)
    inner = rrect(x0 + tv, y0 + th, x1 - tv, y1 - th, ri, k, iradii)
    return D(outer, inner)


def U(*ps):
    out = ps[0]
    for p in ps[1:]:
        out = pathops.op(out, p, pathops.PathOp.UNION)
    return out


def D(a, b):
    return pathops.op(a, b, pathops.PathOp.DIFFERENCE)


def I(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def diag(xt, yt, xb, yb, t=None):
    """Stroke of perpendicular width t from top point (xt, yt) (right edge) to bottom point (xb, yb) (left edge),
    with horizontal top / bottom cuts."""
    t = TV if t is None else t
    dw = t
    for _ in range(4):                       # horizontal width so that the perpendicular width is t
        dx, dy = (xt - dw) - xb, yt - yb
        dw = t * math.hypot(dx, dy) / dy
    return poly([(xt - dw, yt), (xt, yt), (xb + dw, yb), (xb, yb)])


def flip(p):
    """Rotate 180 degrees inside the W x H box (6 -> 9)."""
    q = pathops.Path()
    p.draw(TransformPen(q.getPen(), (-1, 0, 0, -1, W, H)))
    return q


# ---------- glyphs ----------
def g0():
    return ring(0, 0, W, H, W * ZERO_R, k=0.66 if ZERO_R > 0.44 else K)


def g1():
    xs = (W - TV) / 2 + 0.06 * W
    stem = rect(xs, 0, xs + TV, H)
    # Flag: its top edge starts at the stem's top-left corner and both edges are parallel (it used to join 40 units
    # lower, leaving a step, and widened towards its end, 2026-10-27).
    fx = xs - 0.30 * W
    m = ONE_DROP * H / (xs - fx)                   # slope of the flag
    v = TH * 1.1 * math.hypot(1, m)                # vertical thickness for TH * 1.1 across the stroke
    xi = xs + TV / 2                               # inner end, inside the stem
    flag = poly([(xs, H), (fx, H - m * (xs - fx)), (fx, H - m * (xs - fx) - v), (xi, H - v + m * (xi - xs)),
                 (xi, H)])
    if not ONE_BASE:
        return U(stem, flag)
    return U(stem, flag, rect(0.07 * W, 0, 0.93 * W, TH))


def g2():
    """Top bowl whose lower-right corner flows into the diagonal: the diagonal's outer edge is tangent to the corner."""
    y0 = 0.38 * H
    r = W * R
    uc = (y0 + H) / 2
    # The diagonal's inner edge must meet the top of the base exactly at its left end (x = 0): ending further right
    # left the base sticking out to the left as a ledge (2026-10-27).
    best = None
    for i in range(1, 400):                  # bottom-right corner cubic of the bowl, (W - r, y0) .. (W, y0 + r)
        t = i / 400
        p0, p1, p2, p3 = (W - r, y0), (W - r + K * r, y0), (W, y0 + r - K * r), (W, y0 + r)
        bez = lambda a, b, c, d: (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
        der = lambda a, b, c, d: 3 * (1 - t) ** 2 * (b - a) + 6 * (1 - t) * t * (c - b) + 3 * t * t * (d - c)
        px, py = bez(p0[0], p1[0], p2[0], p3[0]), bez(p0[1], p1[1], p2[1], p3[1])
        dx, dy = der(p0[0], p1[0], p2[0], p3[0]), der(p0[1], p1[1], p2[1], p3[1])
        if dx <= 1e-6:
            continue
        L = math.hypot(dx, dy)
        ix, iy = px - dy / L * TV, py + dx / L * TV   # point on the inner edge (offset towards the counter)
        xin = ix - (iy - TH) * dx / dy              # inner edge at the top of the base
        if best is None or abs(xin) < best[0]:
            best = (abs(xin), px, py, dx, dy)
    _, px, py, dx, dy = best
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L                  # along the diagonal, up-right
    nx, ny = -uy, ux                         # towards the counter (up-left)
    bx, by = px - ux * 2000, py - uy * 2000
    tx, ty = px + ux * 2000, py + uy * 2000
    strip = poly([(bx, by), (tx, ty), (tx + nx * TV, ty + ny * TV), (bx + nx * TV, by + ny * TV)])
    strip = I(strip, rect(0, 0, W + 10, py + TV))
    # Keep the strip out of the bowl's counter: its top end poked into it as a spur (2026-10-27).
    # The counter's lower-right corner is square, so its right wall runs straight down into the diagonal's inner
    # edge (a rounded corner there left a small hook).
    ri = max(r - (TV + TH) / 2, r * 0.3)
    counter = rrect(TV, y0 + TH, W - TV, H - TH, ri, radii=(ri, 0, ri, ri))
    bowl = ring(0, y0, W, H, r)
    below = poly([(bx, by), (tx, ty), (W + 100, ty), (W + 100, -100), (-100, -100)])
    # Also drop what is left of the bowl's bottom stroke on the counter side of the diagonal: it stuck out of the
    # diagonal's inner edge as a ledge (2026-10-27).
    left = I(poly([(bx + nx * TV, by + ny * TV), (tx + nx * TV, ty + ny * TV), (-3000, ty + ny * TV),
                   (-3000, by + ny * TV)]), rect(-10, -10, W + 10, y0 + TH))   # bottom stroke only
    bowl = D(bowl, U(rect(-10, -10, W * 0.5, uc), below, left, counter))
    strip = I(strip, U(rrect(0, y0, W, H, r), rect(-10, -10, W + 10, py)))
    # The strip stops where its inner edge meets the counter's right wall (above that it poked into the counter;
    # subtracting the whole counter instead left a step below the wall).
    ix, iy = bx + nx * TV, by + ny * TV
    yw = iy + (W - TV - ix) * uy / ux
    strip = D(strip, rect(-10, yw, W - TV, H + 10))
    return U(bowl, strip, rect(0, 0, W, TH))


def g3(flat):
    lo = ring(0, 0, W, SP + TH / 2, W * R)
    if flat:
        # Square top-left corner: the diagonal lands on a straight stroke, not on the corner curve (which left a gap).
        r = W * R
        lo = ring(0, 0, W, SP + TH / 2, r, radii=(r, r, r, 0))
        bar = rect(0, H - TH, W, H)
        # The diagonal lands exactly on the top of the lower bowl, which is cut straight below its left edge
        # (an end lower or further left left a spur, 2026-10-27).
        xb = 0.24 * W
        d = diag(W, H - TH, xb, SP + TH / 2)    # from the bar's lower edge to the bowl's top edge, no overlap
        lo = D(lo, U(rect(-10, TH, W * 0.5, SP - TH / 2), rect(-10, SP - TH / 2 - 1, xb, SP + TH / 2 + 1)))
        return U(bar, d, lo)
    up = ring(0.05 * W, SP - TH / 2, W, H, W * 0.95 * R)
    both = U(up, lo)
    cut = U(rect(-10, TH, W * 0.5, SP - TH / 2), rect(-10, SP + TH / 2, W * 0.5, H - TH),
            rect(-10, SP - TH / 2 - 1, 0.30 * W, SP + TH / 2 + 1))
    return D(both, cut)


def g4():
    cb = 0.25 * H
    sx = W - TV    # stem flush with the crossbar's right end (a 13-unit stub read as a spur)
    if FOUR == 'closed':
        return U(rect(sx, 0, sx + TV, H), rect(0, cb, W, cb + TH), diag(sx + TV, H, 0, cb + TH / 2))
    return U(rect(0, cb, TV, H), rect(0, cb, W, cb + TH), rect(sx, 0, sx + TV, 0.68 * H))


def g5():
    r = W * R
    bowl = ring(0, 0, W, SP + TH / 2, r, radii=(r, r, r, 0))
    bowl = D(bowl, rect(-10, TH, W * 0.5, SP - TH / 2))
    return U(bowl, rect(0, SP, TV, H), rect(0, H - TH, W * 0.97, H))


def g6():
    sl = 0.58 * H
    r = W * R
    # Lower bowl with a square outer top-left corner: the stem runs straight into its top edge (the rounded corner
    # left a 3-unit dip on the inside where they meet). The counter keeps its round corner.
    ri = max(r - (TV + TH) / 2, r * 0.3)
    lower = D(rrect(0, 0, W, sl, r, radii=(r, r, r, 0)), rrect(TV, TH, W - TV, sl - TH, ri))
    # The tail is a straight bar like the 3 / 5 / 7 tops, cut square: the top-right corner has no curve and the cut
    # ends at the stroke's inner edge (cutting into the corner curve made a drooping tip with a hanging lump).
    big = ring(0, 0, W, H, r, radii=(r, r, 0, r))
    keep = U(rect(-10, sl / 2, W * 0.5, H + 10), rect(-10, H - TH, W * TAIL, H + 10))
    return U(lower, I(big, keep))


def g7():
    return U(rect(0, H - TH, W, H), diag(W, H - TH, SEVEN_X * W, 0))


def g8():
    pw = 0.08 * W
    lower = ring(0, 0, W, SP + TH / 2, W * R)
    upper = ring(pw, SP - TH / 2, W - pw, H, (W - 2 * pw) * R)
    return U(lower, upper)


def g9():
    return flip(g6())


def gdot():
    return rrect(0, 0, DOT, DOT, DOT * 0.18)


def gcolon():
    """Two dots 0.50 H apart; COLON_MID = height of the pair's centre (0.35 H: lower dot on the baseline)."""
    y0 = COLON_MID * H - (0.50 * H + DOT) / 2
    return U(rrect(0, y0, DOT, y0 + DOT, DOT * 0.18), rrect(0, y0 + 0.50 * H, DOT, y0 + 0.50 * H + DOT, DOT * 0.18))


def gminus():
    return rect(0, MINUS_Y * H - TH / 2, 0.62 * W, MINUS_Y * H + TH / 2)


def gslash():
    return diag(0.62 * W, H, 0, 0, TV * 0.9)


def gdegree():
    s = 0.50 * W
    return ring(0, H - s, s, H, s * 0.45, tv=TV * 0.45, th=TV * 0.45, k=0.62)


def gpercent():
    pw = 1.55 * W
    s = 0.60 * W
    h = 0.44 * H
    a = ring(0, H - h, s, H, s * 0.42, tv=TV * 0.62, th=TH * 0.62)
    b = ring(pw - s, 0, pw, h, s * 0.42, tv=TV * 0.62, th=TH * 0.62)
    return U(a, b, diag(pw - 0.30 * W, H, 0.30 * W, 0, TV * 0.62))


def build(variant):
    """Write LazyDigits-<variant>.ttf with the current parameters."""
    flat = THREE == 'F'
    # Digits are tabular (one advance): live values must not shift as they change (spacing test, 2026-10-27).
    glyphs = {
        'zero': ('0', g0, ADV), 'one': ('1', g1, ADV), 'two': ('2', g2, ADV), 'three': ('3', lambda: g3(flat), ADV),
        'four': ('4', g4, ADV), 'five': ('5', g5, ADV), 'six': ('6', g6, ADV), 'seven': ('7', g7, ADV),
        'eight': ('8', g8, ADV), 'nine': ('9', g9, ADV),
        'period': ('.', gdot, DOT + 2 * SB), 'colon': (':', gcolon, DOT + 2 * SB),
        'minus': ('-', gminus, round(0.62 * W) + 2 * SB), 'slash': ('/', gslash, round(0.62 * W) + 2 * SB),
        'degree': ('°', gdegree, round(0.50 * W) + 2 * SB), 'percent': ('%', gpercent, round(1.55 * W) + 2 * SB),
    }
    order = ['.notdef', 'space'] + list(glyphs)
    cmap = {0x20: 'space'}
    glyf, metrics = {}, {}
    pen = TTGlyphPen(None)
    glyf['.notdef'], metrics['.notdef'] = pen.glyph(), (ADV, 0)
    glyf['space'], metrics['space'] = TTGlyphPen(None).glyph(), (ADV, 0)
    for name, (ch, fn, adv) in glyphs.items():
        path = fn()
        path.simplify()
        tp = TTGlyphPen(None)
        path.draw(Cu2QuPen(TransformPen(tp, (1, 0, 0, 1, SB, 0)), max_err=1.0, reverse_direction=True))
        g = tp.glyph()
        g.recalcBounds(None)
        glyf[name] = g
        metrics[name] = (adv, getattr(g, 'xMin', 0))
        cmap[ord(ch)] = name
        if ch == '-':
            cmap[0x2212] = name
    fam = 'Lazy Digits' if variant == 'Bold' else f'Lazy Digits {variant}'
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=850, descent=-150)
    fb.setupNameTable({'familyName': fam, 'styleName': 'Bold',
                       'copyright': 'Copyright 2026 Lazy Farmer (lazyfrmr@gmail.com)',
                       'version': f'Version {VERSION}', 'psName': fam.replace(' ', '') + '-Bold',
                       'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1.',
                       'licenseInfoURL': 'https://openfontlicense.org'})
    fb.setupOS2(sTypoAscender=850, sTypoDescender=-150, usWinAscent=900, usWinDescent=200, sCapHeight=H, sxHeight=H,
                usWeightClass=700, fsSelection=0x20)   # bold
    fb.font['head'].macStyle = 1       # bold, matching fsSelection
    fb.setupPost()
    path = f'{OUT}/LazyDigits-{variant}.ttf'
    fb.save(path)
    print(path)


if __name__ == '__main__':
    configure()
    build('Bold')     # design picked 2026-10-27: flat-top 3, width 0.60, 1 without foot, steep 7
