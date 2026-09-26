"""
Flat-vector blog cover generator for dynamitemanagement.com, hoafiscal.com, hoameeting.com.

Replaces the ChatGPT image step. A cover is described by a small "scene spec":

    {"site": "dynamite", "state": "WA", "building": "condo",
     "props": ["scales", "document", "calendar"], "seed": 7}

Claude (in draft_posts) picks the spec from the post's topic; this module draws it
as SVG in the site's brand palette and renders a 1200x630 JPG. No text is ever
drawn on covers (titles live in the page / og:title), matching the old rule.

Pure Python + cairosvg + Pillow; no Django imports so it can run anywhere.
"""
from __future__ import annotations

import io
import random

W, H = 1200, 630

PALETTES = {
    "dynamite": dict(bg="#F6F1E4", bg2="#EDE4CF", primary="#003366", primary2="#1D4E80",
                     accent="#FF6F31", accent2="#FFB08C", gold="#D9A84A", green="#1F5F3F",
                     green2="#4E8A62", ink="#14263A", paper="#FFFFFF", line="#C9D3DE",
                     ground="#DCCFAE", sky="#E4EBF2"),
    "hoafiscal": dict(bg="#F4F2FB", bg2="#E7E2F7", primary="#5B3FB5", primary2="#7D63D1",
                      accent="#2E9E5B", accent2="#9ED6B3", gold="#F2B84B", green="#2E9E5B",
                      green2="#6FC08D", ink="#2A2440", paper="#FFFFFF", line="#D6D0EC",
                      ground="#DCD6EE", sky="#EAE6F8"),
    "hoameeting": dict(bg="#1C1733", bg2="#262045", primary="#8B7CF6", primary2="#A99DFA",
                       accent="#E0802A", accent2="#F3B36B", gold="#F3C969", green="#3FA27A",
                       green2="#6CC29C", ink="#0F0C1F", paper="#F3F4F6", line="#C8C2E6",
                       ground="#2F2855", sky="#241E40"),
}

STATES = {"WA", "OR", "FL", "AZ", "CA", "CO", "TX", "NV", "GA", "NC", "VA", "IL", "GENERIC"}


# --------------------------------------------------------------------------- helpers
def _g(body: str, x: float, y: float, s: float = 1.0) -> str:
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})">{body}</g>'


def _shadow(cx, cy, rx, ry=10, op=0.18):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#000" opacity="{op}"/>'


# --------------------------------------------------------------------------- landscapes
def _trees_evergreen(p, xs, base, h=90):
    out = []
    for x in xs:
        out.append(
            f'<rect x="{x-5}" y="{base-18}" width="10" height="18" fill="{p["ink"]}" opacity=".7"/>'
            f'<polygon points="{x},{base-h} {x-32},{base-18} {x+32},{base-18}" fill="{p["green"]}"/>'
            f'<polygon points="{x},{base-h} {x},{base-18} {x+32},{base-18}" fill="{p["green2"]}" opacity=".45"/>'
        )
    return "".join(out)


def _palm(p, x, base, h=150, flip=1):
    fronds = []
    top_x, top_y = x + 18 * flip, base - h
    for ang, ln in ((-160, 70), (-120, 80), (-60, 80), (-20, 70), (-95, 60)):
        import math
        a = math.radians(ang)
        ex, ey = top_x + ln * math.cos(a), top_y + ln * math.sin(a) + 30
        cx, cy = top_x + ln * 0.5 * math.cos(a), top_y + ln * 0.5 * math.sin(a) - 18
        fronds.append(f'<path d="M{top_x},{top_y} Q{cx:.0f},{cy:.0f} {ex:.0f},{ey:.0f} '
                      f'Q{cx+6:.0f},{cy+14:.0f} {top_x},{top_y}Z" fill="{p["green"]}"/>')
    trunk = (f'<path d="M{x-6},{base} Q{x+10*flip},{base-h/2} {top_x-4},{top_y} L{top_x+4},{top_y} '
             f'Q{x+18*flip},{base-h/2} {x+6},{base}Z" fill="{p["gold"]}" opacity=".85"/>')
    return trunk + "".join(fronds)


def _saguaro(p, x, base, h=130):
    c = p["green"]
    return (f'<rect x="{x-11}" y="{base-h}" width="22" height="{h}" rx="11" fill="{c}"/>'
            f'<path d="M{x-11},{base-h*0.45} h-22 a11,11 0 0 1 -11,-11 v-34 a9,9 0 0 1 18,0 v27 h15z" fill="{c}"/>'
            f'<path d="M{x+11},{base-h*0.6} h20 a11,11 0 0 0 11,-11 v-26 a9,9 0 0 0 -18,0 v19 h-13z" fill="{c}"/>'
            f'<rect x="{x-3}" y="{base-h+10}" width="4" height="{h-20}" fill="{p["green2"]}" opacity=".5"/>')


def _sun(p, cx, cy, r=46, op=1.0):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r+22}" fill="{p["gold"]}" opacity="{0.18*op}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{p["gold"]}" opacity="{0.9*op}"/>')


def _cloud(p, x, y, s=1.0, op=0.9):
    col = p["paper"] if p is not PALETTES["hoameeting"] else p["bg2"]
    return _g(f'<g fill="{col}" opacity="{op}"><circle cx="40" cy="30" r="26"/><circle cx="72" cy="22" r="32"/>'
              f'<circle cx="104" cy="32" r="24"/><rect x="40" y="30" width="64" height="26"/></g>', x, y, s)


def landscape(p, state: str, rnd: random.Random) -> str:
    """Background band keyed to the state (no maps, no text)."""
    base = H - 110
    st = state.upper() if state else "GENERIC"
    parts = []
    dark = p is PALETTES["hoameeting"]
    # far hills / mountains
    if st in ("WA", "OR"):
        parts.append(f'<polygon points="700,{base} 900,{base-250} 1100,{base}" fill="{p["primary2"]}" opacity=".35"/>'
                     f'<polygon points="900,{base-250} 860,{base-200} 880,{base-205} 900,{base-185} 925,{base-208} 945,{base-200}" fill="{p["paper"]}" opacity=".9"/>')
        parts.append(_cloud(p, 120, 70, 1.1) + _cloud(p, 980, 40, 0.8))
    elif st == "CO":
        parts.append(f'<polygon points="600,{base} 760,{base-230} 860,{base-120} 960,{base-270} 1200,{base}" fill="{p["primary2"]}" opacity=".35"/>'
                     f'<polygon points="960,{base-270} 925,{base-215} 945,{base-222} 962,{base-200} 985,{base-225}" fill="{p["paper"]}" opacity=".9"/>'
                     f'<polygon points="760,{base-230} 735,{base-192} 760,{base-198} 780,{base-200}" fill="{p["paper"]}" opacity=".9"/>')
        parts.append(_cloud(p, 140, 60, 1.0))
    elif st in ("AZ", "NV", "TX"):
        parts.append(_sun(p, 1020, 150, 58))
        parts.append(f'<path d="M620,{base} L660,{base-120} L840,{base-120} L880,{base}Z" fill="{p["accent"]}" opacity=".35"/>'
                     f'<path d="M900,{base} L930,{base-80} L1060,{base-80} L1090,{base}Z" fill="{p["accent"]}" opacity=".25"/>')
    elif st in ("FL",):
        parts.append(_sun(p, 1040, 140, 52))
        parts.append(f'<rect x="0" y="{base-26}" width="{W}" height="26" fill="{p["primary2"]}" opacity=".30"/>'
                     f'<path d="M0,{base-26} q60,-10 120,0 t120,0 t120,0 t120,0 t120,0 t120,0 t120,0 t120,0 t120,0 t120,0" fill="none" stroke="{p["paper"]}" stroke-width="3" opacity=".5"/>')
        parts.append(_cloud(p, 160, 60, 0.9))
    elif st in ("CA",):
        parts.append(_sun(p, 1030, 150, 50))
        parts.append(f'<path d="M0,{base} Q300,{base-150} 620,{base-40} T1200,{base-60} V{base}Z" fill="{p["gold"]}" opacity=".35"/>')
        parts.append(_cloud(p, 180, 70, 0.9))
    else:
        parts.append(f'<path d="M0,{base} Q260,{base-110} 560,{base-30} T1200,{base-70} V{base}Z" fill="{p["green2"]}" opacity=".25"/>')
        parts.append(_cloud(p, 130, 70, 1.0) + _cloud(p, 960, 50, 0.85))
    # ground
    parts.append(f'<rect x="0" y="{base}" width="{W}" height="{H-base}" fill="{p["ground"]}"/>'
                 f'<rect x="0" y="{base}" width="{W}" height="6" fill="{p["ink"]}" opacity="{0.25 if dark else 0.08}"/>')
    # foreground flora
    if st in ("WA", "OR", "CO", "GENERIC", "GA", "NC", "VA", "IL"):
        parts.append(_trees_evergreen(p, [60, 110, 1150], base + 8, 110))
    elif st in ("AZ", "NV", "TX"):
        parts.append(_saguaro(p, 70, base + 6, 140) + _saguaro(p, 1140, base + 6, 110))
    elif st in ("FL", "CA"):
        parts.append(_palm(p, 70, base + 6, 190, 1) + _palm(p, 1140, base + 6, 160, -1))
    return "".join(parts)


# --------------------------------------------------------------------------- buildings
def condo(p):
    b = [f'<rect x="0" y="0" width="200" height="330" rx="6" fill="{p["primary"]}"/>',
         f'<rect x="140" y="0" width="60" height="330" rx="6" fill="{p["ink"]}" opacity=".25"/>',
         f'<rect x="-10" y="-14" width="220" height="18" rx="4" fill="{p["ink"]}" opacity=".6"/>']
    for r in range(6):
        y = 24 + r * 50
        for c in range(3):
            x = 20 + c * 58
            b.append(f'<rect x="{x}" y="{y}" width="40" height="30" rx="3" fill="{p["sky"] if p is not PALETTES["hoameeting"] else p["gold"]}" opacity="{0.95 if (r+c)%3 else 0.6}"/>')
        b.append(f'<rect x="12" y="{y+30}" width="176" height="6" rx="2" fill="{p["paper"]}" opacity=".55"/>')
    b.append(f'<rect x="80" y="284" width="40" height="46" rx="3" fill="{p["accent"]}"/>')
    return "".join(b)


def houses(p):
    out = []
    specs = [(0, 150, p["primary"]), (150, 190, p["accent"]), (320, 150, p["primary2"])]
    for i, (x, h, col) in enumerate(specs):
        w = 150 if i != 1 else 170
        top = 330 - h
        out.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h}" fill="{col}"/>'
                   f'<polygon points="{x-14},{top+4} {x+w/2},{top-80} {x+w+14},{top+4}" fill="{p["ink"]}" opacity=".85"/>'
                   f'<rect x="{x+w/2-18}" y="{330-62}" width="36" height="62" rx="3" fill="{p["paper"]}" opacity=".9"/>'
                   f'<rect x="{x+16}" y="{top+22}" width="34" height="30" rx="3" fill="{p["sky"] if p is not PALETTES["hoameeting"] else p["gold"]}"/>'
                   f'<rect x="{x+w-50}" y="{top+22}" width="34" height="30" rx="3" fill="{p["sky"] if p is not PALETTES["hoameeting"] else p["gold"]}"/>')
    return "".join(out)


# --------------------------------------------------------------------------- props (≈200x200 local box)
def document(p):
    return (f'<rect x="18" y="8" width="150" height="196" rx="8" fill="{p["ink"]}" opacity=".18"/>'
            f'<rect x="8" y="0" width="150" height="196" rx="8" fill="{p["paper"]}"/>'
            f'<rect x="28" y="24" width="90" height="12" rx="4" fill="{p["primary"]}"/>'
            + "".join(f'<rect x="28" y="{52+i*18}" width="{110 - (i%3)*18}" height="7" rx="3" fill="{p["line"]}"/>' for i in range(6))
            + f'<circle cx="120" cy="164" r="20" fill="{p["accent"]}"/><circle cx="120" cy="164" r="12" fill="none" stroke="{p["paper"]}" stroke-width="3"/>'
              f'<path d="M108,180 l-6,22 12,-6 6,10 4,-22z M132,180 l6,22 -12,-6 -6,10 -4,-22z" fill="{p["accent"]}"/>')


def gavel(p):
    return (f'<rect x="20" y="168" width="160" height="22" rx="6" fill="{p["ink"]}" opacity=".85"/>'
            f'<rect x="40" y="152" width="120" height="20" rx="6" fill="{p["gold"]}"/>'
            f'<g transform="rotate(-35 100 90)"><rect x="92" y="40" width="16" height="140" rx="7" fill="{p["gold"]}"/>'
            f'<rect x="40" y="22" width="120" height="48" rx="12" fill="{p["primary"]}"/>'
            f'<rect x="40" y="22" width="22" height="48" rx="8" fill="{p["accent"]}"/><rect x="138" y="22" width="22" height="48" rx="8" fill="{p["accent"]}"/></g>')


def calendar(p):
    cells = []
    for r in range(4):
        for c in range(5):
            hl = (r, c) == (2, 3)
            cells.append(f'<rect x="{20+c*32}" y="{70+r*30}" width="24" height="22" rx="4" '
                         f'fill="{p["accent"] if hl else p["line"]}" opacity="{1 if hl else .8}"/>')
    return (f'<rect x="4" y="16" width="192" height="188" rx="12" fill="{p["paper"]}"/>'
            f'<rect x="4" y="16" width="192" height="44" rx="12" fill="{p["primary"]}"/>'
            f'<rect x="4" y="44" width="192" height="16" fill="{p["primary"]}"/>'
            f'<rect x="46" y="2" width="12" height="30" rx="6" fill="{p["ink"]}"/><rect x="142" y="2" width="12" height="30" rx="6" fill="{p["ink"]}"/>'
            + "".join(cells))


def laptop_chart(p):
    bars = "".join(f'<rect x="{50+i*26}" y="{120-h}" width="18" height="{h}" rx="3" fill="{c}"/>'
                   for i, (h, c) in enumerate([(30, p["primary2"]), (50, p["primary"]), (40, p["primary2"]), (72, p["accent"])]))
    return (f'<rect x="20" y="10" width="200" height="136" rx="10" fill="{p["ink"]}"/>'
            f'<rect x="30" y="20" width="180" height="116" rx="4" fill="{p["paper"]}"/>'
            f'<rect x="40" y="28" width="90" height="8" rx="3" fill="{p["accent"]}"/>' + bars +
            f'<circle cx="178" cy="84" r="22" fill="{p["primary"]}"/><path d="M178,84 L178,62 A22,22 0 0 1 199,90Z" fill="{p["accent"]}"/>'
            f'<circle cx="178" cy="84" r="9" fill="{p["paper"]}"/>'
            f'<path d="M0,146 H240 L226,166 H14Z" fill="{p["line"]}"/>')


def coins(p):
    stacks = []
    for sx, n in ((20, 4), (80, 6), (140, 8)):
        for i in range(n):
            y = 190 - i * 16
            stacks.append(f'<ellipse cx="{sx+25}" cy="{y}" rx="26" ry="9" fill="{p["gold"]}" stroke="{p["ink"]}" stroke-opacity=".25" stroke-width="2"/>')
    return ("".join(stacks) +
            f'<path d="M20,70 L80,40 L120,58 L180,10" fill="none" stroke="{p["accent"]}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<polygon points="186,0 190,30 162,14" fill="{p["accent"]}"/>')


def clock(p):
    return (f'<circle cx="100" cy="104" r="92" fill="{p["primary"]}"/>'
            f'<circle cx="100" cy="104" r="78" fill="{p["paper"]}"/>'
            f'<path d="M100,104 L100,26 A78,78 0 0 1 178,104Z" fill="{p["accent"]}" opacity=".85"/>'
            + "".join(f'<rect x="97" y="30" width="6" height="12" rx="2" fill="{p["ink"]}" transform="rotate({a} 100 104)"/>' for a in range(0, 360, 30))
            + f'<rect x="96" y="50" width="8" height="58" rx="4" fill="{p["ink"]}"/>'
              f'<rect x="96" y="100" width="46" height="8" rx="4" fill="{p["ink"]}"/>'
              f'<circle cx="100" cy="104" r="8" fill="{p["ink"]}"/>'
              f'<rect x="86" y="0" width="28" height="16" rx="4" fill="{p["primary"]}"/>')


def meeting(p):
    people = []
    for x, col in ((30, p["primary"]), (80, p["accent"]), (130, p["primary2"]), (180, p["green"])):
        people.append(f'<circle cx="{x}" cy="52" r="18" fill="{p["gold"]}" opacity=".95"/>'
                      f'<path d="M{x-26},120 Q{x-26},76 {x},76 Q{x+26},76 {x+26},120Z" fill="{col}"/>')
    return ("".join(people) +
            f'<rect x="0" y="112" width="210" height="26" rx="8" fill="{p["ink"]}" opacity=".85"/>'
            f'<rect x="20" y="138" width="14" height="60" fill="{p["ink"]}" opacity=".7"/><rect x="176" y="138" width="14" height="60" fill="{p["ink"]}" opacity=".7"/>'
            f'<rect x="60" y="100" width="40" height="14" rx="2" fill="{p["paper"]}"/><rect x="118" y="100" width="40" height="14" rx="2" fill="{p["paper"]}"/>')


def lock(p):
    return (f'<path d="M50,90 V60 a50,50 0 0 1 100,0 V90" fill="none" stroke="{p["ink"]}" stroke-width="20" stroke-linecap="round"/>'
            f'<rect x="20" y="86" width="160" height="116" rx="18" fill="{p["primary"]}"/>'
            f'<rect x="20" y="86" width="160" height="22" rx="10" fill="{p["primary2"]}" opacity=".6"/>'
            f'<circle cx="100" cy="138" r="18" fill="{p["gold"]}"/><rect x="92" y="140" width="16" height="36" rx="6" fill="{p["gold"]}"/>')


def magnifier(p):
    return (f'<rect x="118" y="120" width="30" height="90" rx="14" fill="{p["ink"]}" transform="rotate(-45 133 165)"/>'
            f'<circle cx="84" cy="84" r="72" fill="{p["primary"]}"/>'
            f'<circle cx="84" cy="84" r="54" fill="{p["sky"] if p is not PALETTES["hoameeting"] else p["paper"]}"/>'
            f'<path d="M50,64 a40,40 0 0 1 36,-22" fill="none" stroke="{p["paper"]}" stroke-width="10" stroke-linecap="round" opacity=".9"/>'
            f'<rect x="54" y="86" width="60" height="8" rx="3" fill="{p["line"]}"/><rect x="54" y="102" width="40" height="8" rx="3" fill="{p["accent"]}"/>')


def calculator(p):
    keys = []
    for r in range(4):
        for c in range(4):
            col = p["accent"] if c == 3 else (p["primary2"] if r == 0 else p["paper"])
            keys.append(f'<rect x="{20+c*36}" y="{76+r*30}" width="28" height="22" rx="5" fill="{col}"/>')
    return (f'<rect x="4" y="4" width="164" height="200" rx="16" fill="{p["ink"]}"/>'
            f'<rect x="20" y="20" width="132" height="42" rx="6" fill="{p["green2"]}"/>'
            f'<rect x="96" y="32" width="46" height="18" rx="3" fill="{p["ink"]}" opacity=".35"/>' + "".join(keys))


def checklist(p):
    rows = []
    for i in range(4):
        y = 56 + i * 36
        done = i < 3
        rows.append(f'<rect x="30" y="{y}" width="22" height="22" rx="5" fill="{p["accent"] if done else p["line"]}"/>'
                    + (f'<path d="M35,{y+11} l5,6 l9,-12" fill="none" stroke="{p["paper"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' if done else "")
                    + f'<rect x="64" y="{y+7}" width="{90 - (i%2)*20}" height="8" rx="3" fill="{p["line"]}"/>')
    return (f'<rect x="6" y="14" width="168" height="190" rx="12" fill="{p["primary"]}"/>'
            f'<rect x="18" y="30" width="144" height="164" rx="6" fill="{p["paper"]}"/>'
            f'<rect x="60" y="2" width="60" height="26" rx="8" fill="{p["gold"]}"/>' + "".join(rows))


def scales(p):
    return (f'<rect x="94" y="30" width="12" height="160" fill="{p["gold"]}"/>'
            f'<rect x="50" y="186" width="100" height="16" rx="6" fill="{p["ink"]}" opacity=".85"/>'
            f'<circle cx="100" cy="26" r="12" fill="{p["accent"]}"/>'
            f'<rect x="10" y="44" width="180" height="10" rx="5" fill="{p["gold"]}" transform="rotate(-6 100 49)"/>'
            f'<path d="M30,48 L8,120 M30,48 L52,120" stroke="{p["ink"]}" stroke-width="3" opacity=".6"/>'
            f'<path d="M170,40 L148,108 M170,40 L192,108" stroke="{p["ink"]}" stroke-width="3" opacity=".6"/>'
            f'<path d="M0,120 h60 a30,18 0 0 1 -60,0z" fill="{p["primary"]}"/>'
            f'<path d="M140,108 h60 a30,18 0 0 1 -60,0z" fill="{p["primary"]}"/>')


def piggy(p):
    return (f'<ellipse cx="100" cy="120" rx="86" ry="66" fill="{p["accent2"]}"/>'
            f'<circle cx="178" cy="112" r="24" fill="{p["accent2"]}"/><ellipse cx="190" cy="114" rx="10" ry="12" fill="{p["accent"]}" opacity=".6"/>'
            f'<polygon points="70,64 86,30 104,60" fill="{p["accent"]}"/>'
            f'<circle cx="150" cy="100" r="6" fill="{p["ink"]}"/>'
            f'<rect x="40" y="170" width="22" height="34" rx="6" fill="{p["accent"]}"/><rect x="130" y="170" width="22" height="34" rx="6" fill="{p["accent"]}"/>'
            f'<rect x="76" y="58" width="50" height="10" rx="5" fill="{p["ink"]}" opacity=".6"/>'
            f'<circle cx="101" cy="30" r="22" fill="{p["gold"]}" stroke="{p["ink"]}" stroke-opacity=".25" stroke-width="3"/>')


def shield(p):
    return (f'<path d="M100,4 L184,34 V96 C184,150 146,188 100,204 C54,188 16,150 16,96 V34Z" fill="{p["primary"]}"/>'
            f'<path d="M100,4 L184,34 V96 C184,150 146,188 100,204Z" fill="{p["ink"]}" opacity=".2"/>'
            f'<path d="M62,104 l26,28 l52,-60" fill="none" stroke="{p["gold"]}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>')


PROPS = {
    "document": (document, 170, 206), "gavel": (gavel, 200, 196), "calendar": (calendar, 200, 206),
    "laptop_chart": (laptop_chart, 240, 170), "coins": (coins, 200, 200), "clock": (clock, 200, 200),
    "meeting": (meeting, 210, 200), "lock": (lock, 200, 204), "magnifier": (magnifier, 180, 200),
    "calculator": (calculator, 172, 206), "checklist": (checklist, 180, 206), "scales": (scales, 200, 204),
    "piggy": (piggy, 210, 206), "shield": (shield, 200, 206),
}
BUILDINGS = {"condo": condo, "houses": houses, "none": None}


# --------------------------------------------------------------------------- compose
def build_svg(spec: dict) -> str:
    site = spec.get("site", "dynamite")
    p = PALETTES.get(site, PALETTES["dynamite"])
    rnd = random.Random(spec.get("seed", 1))
    state = (spec.get("state") or "GENERIC").upper()
    if state not in STATES:
        state = "GENERIC"
    props = [x for x in spec.get("props", []) if x in PROPS][:3] or ["document", "calendar"]
    building = spec.get("building", "condo")
    base = H - 110

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>',
             f'<circle cx="{rnd.randint(250, 450)}" cy="{rnd.randint(-40, 60)}" r="220" fill="{p["bg2"]}"/>',
             f'<circle cx="{rnd.randint(850, 1100)}" cy="{rnd.randint(380, 520)}" r="260" fill="{p["bg2"]}" opacity=".7"/>']
    parts.append(landscape(p, state, rnd))

    # building, left third
    fn = BUILDINGS.get(building)
    if fn is condo:
        parts.append(_shadow(310, base + 4, 130, 12))
        parts.append(_g(condo(p), 210, base - 330, 1.0))
    elif fn is houses:
        parts.append(_shadow(330, base + 4, 210, 12))
        parts.append(_g(houses(p), 145, base - 330 * 0.78, 0.78))

    # desk slab + props laid out left-to-right without overlap
    desk_x0, desk_x1 = (500, 1140) if fn else (300, 1000)
    desk_y = base + 40
    parts.append(f'<rect x="{desk_x0}" y="{desk_y}" width="{desk_x1-desk_x0}" height="20" rx="10" fill="{p["ink"]}" opacity=".85"/>'
                 f'<rect x="{desk_x0+30}" y="{desk_y+20}" width="16" height="{H-desk_y-20}" fill="{p["ink"]}" opacity=".6"/>'
                 f'<rect x="{desk_x1-46}" y="{desk_y+20}" width="16" height="{H-desk_y-20}" fill="{p["ink"]}" opacity=".6"/>')
    scales_ = [1.35, 0.95, 0.8][:len(props)]
    gap = 34
    widths = [PROPS[n][1] * sc for n, sc in zip(props, scales_)]
    avail = (desk_x1 - desk_x0) - 60
    total = sum(widths) + gap * (len(props) - 1)
    k = min(1.0, avail / total)
    x = desk_x0 + 30 + (avail - total * k) / 2
    for name, sc in zip(props, scales_):
        fn_, w, h = PROPS[name]
        sc *= k
        parts.append(_g(fn_(p), x, desk_y - h * sc, sc))
        x += w * sc + gap * k
    parts.append("</svg>")
    return "".join(parts)


def render_jpg(spec: dict, quality: int = 88) -> bytes:
    """Return 1200x630 JPEG bytes for a scene spec."""
    import cairosvg
    from PIL import Image
    png = cairosvg.svg2png(bytestring=build_svg(spec).encode(), output_width=W, output_height=H)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def spec_prompt_help() -> str:
    """Text given to Claude so it can choose a valid scene spec."""
    return ("Return a cover scene spec as JSON: {\"state\": one of " + ", ".join(sorted(STATES)) +
            ", \"building\": \"condo\" | \"houses\" | \"none\", \"props\": 2-3 of " + ", ".join(PROPS) +
            " (first = hero prop, most tied to the topic), \"seed\": any integer}. Use \"condo\" for condominium topics, "
            "\"houses\" for HOA/planned-community topics. Examples: budget ratification -> calculator, calendar, document; "
            "reserves -> piggy, coins, laptop_chart; executive session -> lock, meeting; collections -> coins, gavel, document; "
            "statute roundup -> scales, document, calendar; minutes -> checklist, document, magnifier.")
