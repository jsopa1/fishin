#!/usr/bin/env python3
"""Draws the original bait illustrations (V4, DECISIONS #056).

Why illustrations. 36 of 50 baits had no picture. The earlier photo search rejected
candidates that did not actually show the bait (a microscope slide, a group of students,
a moulted skin), and for several baits (stink bait, dough balls, tip-ups, "live bait")
no honest public-domain photograph exists. Rather than show a look-alike or nothing, each
missing bait gets an original flat illustration drawn here, released to the public domain
under CC0 and labelled "Illustration" on the page. Deterministic: re-running rewrites
identical files.

Output: webapp/static/img/baits/<bait_id>.svg (320 x 200).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "webapp" / "static" / "img" / "baits"
MANIFEST = ROOT / "data" / "v1" / "image_manifest_v1.json"

INK = "#1f2a44"
BG_TOP, BG_BOT = "#f4f7fc", "#e3eaf6"


def svg(body: str, tint: str = "#dbe6fb") -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" role="img">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/></linearGradient></defs>'
        '<rect width="320" height="200" fill="url(#g)"/>'
        f'<ellipse cx="160" cy="176" rx="118" ry="10" fill="{tint}"/>'
        f'<g stroke="{INK}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>\n'
    )


def hook(x, y, s=1.0, rot=0):
    """A simple J hook, eye at (x, y)."""
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})" fill="none" stroke="#5b6478">'
            '<circle r="4"/><path d="M0 4 V44 C0 64 -26 66 -26 46 L-20 40"/><path d="M-26 46 L-20 34" stroke-width="3"/></g>')


def treble(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke="#5b6478">'
            '<circle cy="-4" r="4"/><path d="M0 0 V14"/><path d="M0 14 C-4 30 -20 30 -20 20"/>'
            '<path d="M0 14 C4 30 20 30 20 20"/><path d="M0 14 V30"/></g>')


def wavy(x0, y0, x1, y1, amp, waves, width, color, rings=0, ring_color=None):
    import math
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + amp * math.sin(t * waves * math.pi * 2)
        pts.append((x, y))
    d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    out = (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width + 7}"/>'
           f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    for k in range(1, rings + 1):
        px, py = pts[int(n * k / (rings + 1))]
        out += (f'<path d="M{px:.1f} {py - width / 2:.1f} v{width}" stroke="{ring_color or INK}" '
                f'stroke-width="2" opacity=".55"/>')
    return out


def grub(cx, cy, s=1.0, color="#f3e6b8"):
    segs = "".join(f'<path d="M{-34 + i * 14} -14 q4 14 0 28" fill="none" stroke-width="2" opacity=".5"/>' for i in range(1, 5))
    return (f'<g transform="translate({cx} {cy}) scale({s})"><path d="M-46 8 C-46 -22 40 -26 46 2 C48 24 -10 34 -46 8Z" fill="{color}"/>{segs}'
            '<circle cx="-38" cy="0" r="3" fill="#3a2e1a" stroke="none"/></g>')


def bead(cx, cy, r, color):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'


def spinner_blade(cx, cy, color, s=1.0):
    return (f'<g transform="translate({cx} {cy}) scale({s})"><path d="M0 0 C6 -30 46 -34 50 -6 C46 22 10 24 0 0Z" fill="{color}"/>'
            '<path d="M10 -6 C20 -18 34 -18 40 -8" fill="none" stroke="#ffffff" opacity=".7" stroke-width="3"/></g>')


def minnow(cx, cy, s=1.0, color="#9fb3c8", rot=0):
    return (f'<g transform="translate({cx} {cy}) rotate({rot}) scale({s})"><path d="M-46 0 C-30 -22 20 -24 40 -4 L58 -16 L58 16 L40 4 C20 24 -30 22 -46 0Z" fill="{color}"/>'
            '<circle cx="-30" cy="-3" r="3.5" fill="#fff"/><circle cx="-30" cy="-3" r="1.5" fill="#1f2a44" stroke="none"/>'
            '<path d="M-8 -14 C4 -8 4 8 -8 14" fill="none" opacity=".45" stroke-width="2.5"/></g>')


def plug(cx, cy, s=1.0, body="#e8a03c", rot=0, lip=True):
    l = '<path d="M-52 -2 L-72 10 L-46 8Z" fill="#8fa3bf"/>' if lip else ''
    return (f'<g transform="translate({cx} {cy}) rotate({rot}) scale({s})">{l}'
            f'<path d="M-52 0 C-48 -22 30 -26 58 -6 L64 0 L58 6 C30 26 -48 22 -52 0Z" fill="{body}"/>'
            '<circle cx="-36" cy="-4" r="4.5" fill="#fff"/><circle cx="-36" cy="-4" r="2" fill="#1f2a44" stroke="none"/>'
            '<path d="M-14 -16 C-6 -6 -6 6 -14 16 M6 -18 C14 -6 14 6 6 18" fill="none" opacity=".45" stroke-width="2.5"/>'
            '<circle cx="0" cy="24" r="3.5" fill="none" stroke="#5b6478"/><circle cx="46" cy="18" r="3.5" fill="none" stroke="#5b6478"/></g>')


# --------------------------------------------------------------------------- the 36
def d_leeches():
    body = ('<path d="M40 128 C70 70 150 60 214 96 C250 116 280 112 290 100 C286 128 250 146 206 134 C150 118 90 132 40 128Z" fill="#4f5b3c"/>'
            + "".join(f'<path d="M{70 + i * 24} {112 - (i % 3) * 6} q6 14 0 26" fill="none" stroke-width="2" opacity=".5"/>' for i in range(8))
            + '<circle cx="290" cy="106" r="7" fill="#3a442b"/>')
    return svg(body)


def d_nightcrawlers():
    return svg(wavy(40, 118, 280, 92, 22, 1.5, 22, "#b8624a", rings=14, ring_color="#7a3a2c")
               + '<path d="M132 92 q20 -8 40 0 q4 26 -40 30Z" fill="#d9967f" opacity=".85" stroke="none"/>')


def d_worms():
    return svg(wavy(40, 66, 270, 60, 12, 2, 12, "#c97a68", rings=10, ring_color="#8a4b3d")
               + wavy(50, 108, 280, 118, 14, 2.5, 12, "#d08a76", rings=10, ring_color="#8a4b3d")
               + wavy(40, 148, 250, 140, 10, 2, 12, "#c47060", rings=9, ring_color="#8a4b3d"))


def d_plastic_worms():
    tail = '<path d="M250 118 C280 108 296 138 276 146 C262 150 262 134 272 134" fill="none" stroke="#5a3c9a" stroke-width="12"/>'
    return svg(wavy(50, 112, 250, 112, 8, 1.2, 16, "#8a63d8", rings=12, ring_color="#5a3c9a") + tail + hook(58, 86, 0.8))


def d_insect_larvae():
    return svg(grub(110, 96, 1.0) + grub(206, 132, 0.9, "#f0dcaa") + grub(150, 160, 0.7, "#f6ecc8"))


def d_insects_live():
    legs = "".join(f'<path d="M{x} 104 l{-18 * s} {26} M{x} 104 l{18 * s} {26}" fill="none" stroke-width="3.5"/>' for x, s in ((138, 1), (160, 1), (182, 1)))
    return svg(legs + '<ellipse cx="160" cy="96" rx="64" ry="30" fill="#6f7c3a"/><path d="M110 88 C130 60 200 60 214 88" fill="#8a984a"/>'
               '<circle cx="216" cy="92" r="16" fill="#5c6830"/><path d="M226 84 l32 -30 M230 90 l40 -10" fill="none" stroke-width="3"/>'
               '<circle cx="222" cy="90" r="3" fill="#fff"/>')


def d_hellgrammites():
    seg = "".join(f'<ellipse cx="{70 + i * 24}" cy="104" rx="16" ry="{20 - i * 0.6}" fill="#5c4630"/>' for i in range(9))
    fil = "".join(f'<path d="M{70 + i * 24} 122 l-4 18 M{70 + i * 24} 86 l-4 -18" stroke-width="2.5" fill="none"/>' for i in range(1, 8))
    head = ('<path d="M292 96 C300 70 318 72 316 96" fill="none"/><ellipse cx="290" cy="104" rx="20" ry="18" fill="#3f2f1e"/>'
            '<path d="M304 96 l16 -16 M304 112 l16 16" fill="none" stroke-width="5"/>')
    return svg('<g transform="translate(-34 0)">' + fil + seg + head + '</g>')


def d_dragonfly_larvae():
    legs = "".join(f'<path d="M{x} 110 l{d} 40" fill="none" stroke-width="4"/>' for x, d in ((110, -18), (140, -6), (170, 8), (110, 84), ))
    legs = "".join(f'<path d="M{x} 118 l{d} 34 M{x} 86 l{-d} -30" fill="none" stroke-width="4"/>' for x, d in ((120, -14), (150, 0), (180, 14)))
    return svg(legs + '<path d="M84 102 C90 76 200 72 226 92 C232 108 200 130 150 130 C110 130 86 122 84 102Z" fill="#6b6b3a"/>'
               '<ellipse cx="238" cy="98" rx="24" ry="20" fill="#575731"/><circle cx="248" cy="90" r="5" fill="#fff"/>'
               '<path d="M84 102 l-24 8 M84 96 l-22 -8" fill="none" stroke-width="4"/>')


def d_crayfish_tails():
    def tail(x, y, rot):
        return (f'<g transform="translate({x} {y}) rotate({rot})"><path d="M-40 0 C-30 -30 30 -30 40 -6 C46 -2 46 6 40 10 C30 34 -30 30 -40 0Z" fill="#f0a78a"/>'
                '<path d="M-14 -22 q6 22 0 42 M6 -24 q6 24 0 46 M24 -18 q5 18 0 34" fill="none" stroke-width="2.2" opacity=".5"/></g>')
    return svg(tail(110, 100, -14) + tail(210, 130, 12) + tail(190, 66, -4))


def d_crawfish_imitators():
    claw = lambda sx: (f'<g transform="scale({sx} 1)"><path d="M0 0 C20 -18 46 -22 60 -8 C46 -6 40 6 30 14 C16 8 6 6 0 0Z" fill="#e2663a"/></g>')
    return svg('<g transform="translate(160 100)">' + '<g transform="translate(30 -10)">' + claw(1) + '</g><g transform="translate(-30 -10)">' + claw(-1) + '</g>'
               '<path d="M-26 -2 C-20 -22 20 -22 26 -2 L22 44 C10 54 -10 54 -22 44Z" fill="#e2663a"/>'
               '<path d="M-20 12 h40 M-18 26 h36" fill="none" stroke-width="2.5" opacity=".5"/>'
               '<path d="M-14 -16 l-8 -22 M14 -16 l8 -22" fill="none"/></g>')


def d_shrimp():
    return svg('<path d="M70 132 C40 70 130 40 210 60 C260 74 268 112 240 124 C250 96 220 82 180 88 C130 96 130 130 70 132Z" fill="#f4a08c"/>'
               '<path d="M110 80 q10 26 -4 44 M150 68 q8 24 -2 40 M190 66 q8 20 0 36" fill="none" stroke-width="2.2" opacity=".5"/>'
               '<path d="M236 118 l34 12 l-10 16 l-18 -8Z" fill="#f4a08c"/><circle cx="82" cy="106" r="3.5" fill="#1f2a44" stroke="none"/>'
               '<path d="M74 100 C50 90 36 76 30 60" fill="none"/>')


def d_fish_pieces():
    return svg('<path d="M70 98 C90 60 210 56 244 84 C256 104 236 134 196 140 C150 148 90 138 70 98Z" fill="#f08a72"/>'
               '<path d="M70 98 C90 60 210 56 244 84" fill="none" stroke="#b7c3d6" stroke-width="7"/>'
               '<path d="M110 92 C140 100 176 100 214 92 M112 116 C142 124 178 124 220 114" fill="none" stroke-width="2.5" opacity=".45" stroke="#fff"/>')


def d_meat_strips():
    return svg('<path d="M60 84 C120 66 200 74 268 60 L274 88 C210 104 130 96 66 116Z" fill="#f08a72"/>'
               '<path d="M60 84 C120 66 200 74 268 60" fill="none" stroke="#b7c3d6" stroke-width="6"/>'
               '<path d="M64 132 C130 116 200 128 262 112 L268 136 C204 152 136 144 68 158Z" fill="#ef9c86"/>')


def d_small_bullheads():
    return svg('<path d="M60 108 C70 80 190 76 232 96 L280 76 L276 132 L232 112 C190 132 74 134 60 108Z" fill="#7d6a55"/>'
               '<path d="M96 100 C120 92 190 94 226 104" fill="none" stroke="#d8c7a8" stroke-width="3" opacity=".6"/>'
               '<circle cx="90" cy="98" r="4" fill="#fff"/><circle cx="90" cy="98" r="1.8" fill="#1f2a44" stroke="none"/>'
               '<path d="M56 108 l-24 -10 M58 116 l-26 6 M62 122 l-20 18" fill="none" stroke-width="3"/>'
               '<path d="M140 84 L150 60 L166 86" fill="#6a5846"/>')


def d_live_bait_unspecified():
    return svg('<path d="M110 70 h100 l-10 96 h-80Z" fill="#8fb6e8" opacity=".85"/><ellipse cx="160" cy="70" rx="50" ry="10" fill="#cfe0f7"/>'
               '<path d="M110 70 C110 40 210 40 210 70" fill="none"/>' + minnow(150, 116, 0.5) + minnow(176, 138, 0.42, "#b7c8d9", 8)
               + '<path d="M126 100 q34 -10 68 0" fill="none" stroke="#fff" stroke-width="2.5" opacity=".7"/>')


def d_live_bait_lmb():
    return svg('<g transform="translate(160 100)"><ellipse rx="70" ry="38" fill="#c8a94a"/>' + '<path d="M-56 -8 C-20 -34 30 -34 60 -10" fill="none" stroke="#e9d68a" stroke-width="5"/>'
               + '<path d="M50 -4 L88 -24 L84 12Z" fill="#c8a94a"/><circle cx="-44" cy="-6" r="6" fill="#fff"/><circle cx="-44" cy="-6" r="2.6" fill="#1f2a44" stroke="none"/></g>'
)


def d_frogs():
    return svg('<path d="M110 128 C82 132 66 150 92 156 C110 158 116 146 124 140Z M210 128 C238 132 254 150 228 156 C210 158 204 146 196 140Z" fill="#5fae5d"/>'
               '<ellipse cx="160" cy="110" rx="60" ry="42" fill="#69bd66"/><ellipse cx="160" cy="98" rx="44" ry="28" fill="#7ccb78" stroke="none"/>'
               '<circle cx="132" cy="70" r="15" fill="#69bd66"/><circle cx="188" cy="70" r="15" fill="#69bd66"/>'
               '<circle cx="132" cy="70" r="7" fill="#fff"/><circle cx="188" cy="70" r="7" fill="#fff"/><circle cx="133" cy="70" r="3" fill="#1f2a44" stroke="none"/><circle cx="187" cy="70" r="3" fill="#1f2a44" stroke="none"/>'
               '<path d="M136 108 q24 14 48 0" fill="none"/>')


def d_stink_bait():
    return svg('<path d="M112 86 h96 v78 a8 8 0 0 1 -8 8 h-80 a8 8 0 0 1 -8 -8Z" fill="#a98b5a"/><rect x="104" y="70" width="112" height="18" rx="6" fill="#6f7c8f"/>'
               '<path d="M124 112 h72 M124 132 h60" fill="none" stroke="#fff" opacity=".5" stroke-width="5"/>'
               + "".join(f'<path d="M{x} 60 c-10 -12 10 -20 0 -34" fill="none" stroke="#7aa05a" stroke-width="4"/>' for x in (130, 160, 190)))


def d_dough_balls():
    b = lambda x, y, r, c: f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/><path d="M{x - r * .5} {y - r * .3} q{r * .4} -{r * .5} {r * .9} -{r * .1}" fill="none" stroke="#fff" opacity=".6" stroke-width="2.5"/>'
    return svg(b(120, 118, 30, "#f0dbb0") + b(190, 110, 34, "#ecd2a0") + b(160, 152, 24, "#f4e4c0") + hook(228, 60, 0.7, 20))


def d_spawn():
    eggs = "".join(bead(x, y, 11, c) + f'<circle cx="{x - 3}" cy="{y - 3}" r="3" fill="#fff" stroke="none" opacity=".7"/>'
                   for x, y, c in ((120, 110, "#f59a3a"), (146, 96, "#f8ab52"), (172, 108, "#f59a3a"), (198, 96, "#f8ab52"), (134, 134, "#f8ab52"),
                                   (160, 132, "#f59a3a"), (186, 134, "#f8ab52"), (108, 132, "#f59a3a"), (212, 122, "#f59a3a"), (160, 78, "#f8ab52")))
    return svg(eggs)


def d_spawn_bag():
    net = "".join(f'<path d="M{110 + i * 20} 78 v88" fill="none" stroke-width="1.6" opacity=".4"/>' for i in range(6))
    net += "".join(f'<path d="M106 {88 + i * 18} h108" fill="none" stroke-width="1.6" opacity=".4"/>' for i in range(5))
    eggs = "".join(bead(x, y, 9, "#f59a3a") for x, y in ((130, 110), (152, 104), (174, 112), (196, 106), (142, 132), (166, 134), (188, 130), (156, 152)))
    return svg('<path d="M104 78 C104 172 216 172 216 78Z" fill="#dfe8f5" opacity=".9"/>' + net + eggs + '<path d="M96 78 h128" stroke-width="5"/><path d="M160 78 v-26" fill="none"/><circle cx="160" cy="48" r="5" fill="#fff"/>')


def d_tip_ups():
    return svg('<ellipse cx="160" cy="150" rx="96" ry="22" fill="#9cc0e6"/><ellipse cx="160" cy="146" rx="70" ry="13" fill="#5f8fc2"/>'
               '<path d="M78 136 L242 136" stroke-width="9" stroke="#8b6b45"/><path d="M160 136 V70" stroke-width="7" stroke="#8b6b45"/>'
               '<path d="M160 74 L214 60 L204 90Z" fill="#e0483a"/><circle cx="160" cy="146" r="0"/><path d="M160 140 V172" fill="none" stroke="#5b6478" stroke-width="2.5"/>')


def d_jigs_ice_teardrop():
    return svg('<path d="M160 40 C200 90 196 130 160 132 C124 130 120 90 160 40Z" fill="#f2b632"/><path d="M148 70 C142 90 146 108 156 118" fill="none" stroke="#fff" opacity=".7" stroke-width="4"/>'
               '<circle cx="160" cy="40" r="5" fill="#fff"/>' + treble(160, 134, 0.7))


def jig_head(cx, cy, color, skirt, hook_on=True):
    return (f'<g transform="translate({cx} {cy})"><path d="M-10 0 C-26 30 -20 50 0 52 C22 50 28 30 10 0Z" fill="{color}"/><circle cx="-8" cy="20" r="6" fill="#fff"/><circle cx="-8" cy="20" r="2.6" fill="#1f2a44" stroke="none"/>'
            f'<path d="M-4 54 L-20 100 M2 54 L4 106 M8 54 L26 98" stroke="{skirt}" stroke-width="7" fill="none"/></g>')


def d_jigs_light():
    return svg(jig_head(150, 44, "#5aa9e6", "#e6c440") + hook(200, 52, 0.7, 12))


def d_finesse_tubes():
    tube = '<path d="M70 96 h120 l10 -10 v40 l-10 -10 h-120Z" fill="#7fb85a"/><path d="M190 96 l40 -18 M190 106 l44 0 M190 116 l40 18" stroke="#7fb85a" stroke-width="7" fill="none"/>'
    return svg(tube + jig_head(96, 92, "#f2b632", "#7fb85a").replace("M-4 54 L-20 100 M2 54 L4 106 M8 54 L26 98", "M0 0"))


def d_jigging_spoons():
    return svg('<path d="M150 34 C176 40 182 132 150 170 C118 132 124 40 150 34Z" fill="#cfd7e4"/><path d="M150 50 C160 84 160 120 150 150" fill="none" stroke="#fff" stroke-width="4" opacity=".8"/>'
               '<circle cx="150" cy="44" r="5" fill="#fff"/>' + treble(150, 168, 0.55))


def d_spinners():
    return svg('<path d="M60 100 H262" stroke="#5b6478" stroke-width="3" fill="none"/>' + bead(96, 100, 9, "#e0483a") + spinner_blade(112, 100, "#e8edf5") + bead(170, 100, 11, "#f2b632") + bead(194, 100, 9, "#e0483a")
               + treble(232, 96, 0.9) + '<circle cx="60" cy="100" r="6" fill="#fff"/>')


def d_spinners_trolling():
    return svg('<path d="M40 100 H270" stroke="#5b6478" stroke-width="3" fill="none"/>' + spinner_blade(56, 92, "#f0c84a", 0.8) + spinner_blade(120, 92, "#e0483a", 0.8)
               + bead(190, 100, 10, "#5aa9e6") + bead(212, 100, 10, "#f2b632") + treble(246, 96, 0.9))


def d_bucktail_spinners():
    return svg('<path d="M60 100 H240" stroke="#5b6478" stroke-width="3" fill="none"/>' + spinner_blade(76, 100, "#e8edf5") + bead(150, 100, 13, "#e0483a")
               + '<path d="M162 96 C200 70 240 76 262 92 C240 100 200 108 162 104Z" fill="#c9a679"/><path d="M170 100 C210 92 240 96 258 96" fill="none" opacity=".5" stroke-width="2.5"/>' + treble(256, 100, 0.6))


def d_small_plugs():
    return svg(plug(160, 100, 1.5))


def d_surface_plugs():
    return svg('<path d="M60 150 q20 -12 40 0 t40 0 t40 0 t40 0 t40 0" fill="none" stroke="#5f8fc2" stroke-width="4"/>'
               '<g transform="translate(160 110)"><path d="M-64 0 C-60 -26 40 -32 64 -8 L70 0 L64 8 C40 30 -60 26 -64 0Z" fill="#5aa055"/><path d="M-64 0 C-66 -10 -60 -16 -54 -20 L-46 -2Z" fill="#3f7a3c"/>'
               '<circle cx="-30" cy="-6" r="5" fill="#fff"/><circle cx="-30" cy="-6" r="2.2" fill="#1f2a44" stroke="none"/></g>' + treble(150, 128, 0.7) + treble(200, 124, 0.7))


def d_surface_baits():
    prop = '<path d="M266 100 l16 -18 M266 100 l16 18" stroke-width="6" fill="none"/>'
    return svg('<path d="M46 156 q18 -10 36 0 t36 0 t36 0 t36 0 t36 0" fill="none" stroke="#5f8fc2" stroke-width="4"/>'
               '<path d="M60 96 C60 72 220 70 258 96 C220 122 60 122 60 96Z" fill="#e6a23a"/><circle cx="92" cy="92" r="5" fill="#fff"/><circle cx="92" cy="92" r="2.2" fill="#1f2a44" stroke="none"/>'
               + prop + treble(140, 122, 0.7) + treble(214, 120, 0.7))


def d_flatfish():
    return svg('<path d="M60 96 C90 50 210 50 254 92 C240 122 130 138 60 96Z" fill="#e0483a"/><path d="M80 96 C120 72 190 72 236 94" fill="none" stroke="#fff" opacity=".55" stroke-width="3"/>'
               '<circle cx="86" cy="92" r="5" fill="#fff"/><circle cx="86" cy="92" r="2.2" fill="#1f2a44" stroke="none"/>' + treble(150, 124, 0.6) + treble(224, 110, 0.6))


def d_small_artificial_lures():
    return svg(plug(90, 100, 0.8, "#5aa9e6") + plug(220, 84, 0.8, "#e6c440") + '<g transform="translate(160 150)">' + '<path d="M-40 0 h80" stroke="#5b6478" fill="none"/></g>'
               + spinner_blade(150, 150, "#e8edf5", 0.6) + bead(214, 150, 8, "#e0483a"))


def d_dodger_fly_combo():
    return svg('<path d="M46 100 H274" stroke="#5b6478" stroke-width="2.5" fill="none"/>'
               '<path d="M70 100 C70 56 130 52 150 82 C150 116 110 130 70 100Z" fill="#f0c84a"/><path d="M88 96 C100 74 122 72 136 84" fill="none" stroke="#fff" opacity=".7" stroke-width="3"/>'
               '<path d="M230 100 C248 84 268 84 282 96 C268 110 248 114 230 100Z" fill="#e0483a"/><path d="M230 100 l-10 -12 M230 100 l-10 12" stroke-width="4" fill="none"/>' + hook(236, 106, 0.6))


def d_yarn_flies():
    return svg(hook(160, 40, 1.2, 0) + '<path d="M150 56 C120 70 116 100 128 116 M170 56 C200 70 208 100 194 118" fill="none" stroke="#f26a8b" stroke-width="12"/>'
               '<path d="M156 50 C140 60 138 84 146 96 M164 50 C180 60 182 84 174 96" fill="none" stroke="#f2d04a" stroke-width="9"/>')


DRAWERS = {
    "leeches": d_leeches, "nightcrawlers": d_nightcrawlers, "small_plugs": d_small_plugs, "small_bullheads": d_small_bullheads,
    "spinners_trolling": d_spinners_trolling, "worms": d_worms, "insect_larvae": d_insect_larvae, "crayfish_tails": d_crayfish_tails,
    "shrimp": d_shrimp, "fish_pieces": d_fish_pieces, "jigs_ice_teardrop": d_jigs_ice_teardrop, "tip_ups": d_tip_ups,
    "bucktail_spinners": d_bucktail_spinners, "insects_live": d_insects_live, "small_artificial_lures": d_small_artificial_lures,
    "stink_bait": d_stink_bait, "meat_strips": d_meat_strips, "dough_balls": d_dough_balls, "frogs": d_frogs, "spinners": d_spinners,
    "plastic_worms": d_plastic_worms, "spawn": d_spawn, "live_bait_unspecified": d_live_bait_unspecified, "spawn_bag": d_spawn_bag,
    "flatfish": d_flatfish, "dodger_fly_combo": d_dodger_fly_combo, "yarn_flies": d_yarn_flies, "hellgrammites": d_hellgrammites,
    "dragonfly_larvae": d_dragonfly_larvae, "surface_baits": d_surface_baits, "live_bait_lmb": d_live_bait_lmb, "surface_plugs": d_surface_plugs,
    "jigs_light": d_jigs_light, "jigging_spoons": d_jigging_spoons, "finesse_tubes": d_finesse_tubes, "crawfish_imitators": d_crawfish_imitators,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data" / "v1" / "bait_catalog_v1.json").read_text(encoding="utf-8"))["baits"]
    wanted = [k for k, v in manifest["baits"].items() if "file" not in v and "reuse_bait_image" not in v and "reuse_species_image" not in v]
    wanted += [k for k in catalog if k not in manifest["baits"]]
    missing_drawers = [k for k in dict.fromkeys(wanted) if k not in DRAWERS]
    if missing_drawers:
        print("no drawing for:", missing_drawers)
        return 1
    for key, fn in DRAWERS.items():
        (OUT / f"{key}.svg").write_text(fn(), encoding="utf-8")
        entry = manifest["baits"].get(key, {})
        # keep any reviewer note; replace a photo-less/reuse entry with the original illustration
        manifest["baits"][key] = {
            "original": True,
            "kind": "illustration",
            "artist": "the fishin project",
            "license_short": "CC0 1.0 (public domain dedication)",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "page_url": f"https://github.com/jsopa1/fishin/blob/main/webapp/static/img/baits/{key}.svg",
            "generator": "analysis/v4_draw_bait_illustrations.py",
            "file": f"webapp/static/img/baits/{key}.svg",
            **({"note": entry["note"]} if "note" in entry else {}),
        }
    with open(MANIFEST, "w", encoding="utf-8", newline="\r\n") as fh:  # the file uses CRLF
        fh.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print("drew", len(DRAWERS), "illustrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
