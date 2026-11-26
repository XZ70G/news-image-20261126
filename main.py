#!/usr/bin/env python3
"""news-image-20261126 entry.

Draws a one-page newspaper front page summing up the world news of
Thursday 26 November 2026, using only the Python standard library.
Writes one deterministic PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png). No network access.

The picture is painted pixel by pixel with a small 5x7 bitmap font
written for this entry, so the program is fully self-contained and
its output bytes are identical on every run.

Layout (different from the 25 November entry): a dark masthead, one
wide lead panel with a drawn tanker-and-flame scene, a row of three
equal story columns, a row of two wider story panels, and a dark
ticker strip with three short items.
"""

import os
import struct
import zlib

W, H = 1024, 1024

NAVY = (15, 30, 52)
PAPER = (250, 246, 236)
INK = (24, 24, 24)
ORANGE = (198, 74, 24)
TEAL = (13, 92, 92)
RUST = (146, 42, 28)
GOLD = (184, 134, 22)
LIGHT = (233, 227, 210)
PANEL = (255, 255, 255)
MUTED = (90, 88, 80)
WHITE = (255, 255, 255)

# 5x7 bitmap font, uppercase. Each glyph is seven rows of five
# characters; '#' is a filled pixel. Written for this entry.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


class Canvas:
    """A small RGB raster canvas with text and shape helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thick) ** 2 <= d <= r * r:
                    self.set(xx, yy, color)

    def tri(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle by scanline interpolation.
        lo = min(y0, y1, y2)
        hi = max(y0, y1, y2)

        def edge_x(y, p, q):
            if p[1] == q[1]:
                return None
            t = (y - p[1]) / (q[1] - p[1])
            if 0.0 <= t <= 1.0:
                return p[0] + t * (q[0] - p[0])
            return None

        pts = [(x0, y0), (x1, y1), (x2, y2)]
        for y in range(lo, hi + 1):
            xs = [e for e in (edge_x(y, pts[0], pts[1]),
                              edge_x(y, pts[1], pts[2]),
                              edge_x(y, pts[2], pts[0])) if e is not None]
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(xx, y, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_c(self, y, s, scale, color, cx=512):
        self.text(cx - self.text_w(s, scale) // 2, y, s, scale, color)

    def wrap(self, s, scale, max_w):
        """Greedy word wrap; returns a list of lines."""
        words = s.upper().split(" ")
        lines = []
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def to_png(self):
        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            return out

        header = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        raw = bytearray()
        stride = W * 3
        for y in range(H):
            raw.append(0)
            raw += self.px[y * stride:(y + 1) * stride]
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


def flame(cv, x, y, s, color, inner=None):
    """A flame pictogram inside a box of side s, top-left (x, y)."""
    cv.tri(x + s // 2, y, x + s // 6, y + s * 2 // 3,
           x + s * 5 // 6, y + s * 2 // 3, color)
    cv.tri(x + s // 4, y + s // 3, x, y + s, x + s // 2, y + s, color)
    cv.tri(x + s * 3 // 4, y + s // 3, x + s // 2, y + s, x + s, y + s, color)
    if inner:
        cv.tri(x + s // 2, y + s // 2, x + s * 3 // 8, y + s * 5 // 6,
               x + s * 5 // 8, y + s * 5 // 6, inner)


def tanker_scene(cv, x, y, w, h):
    """Drawn scene for the lead panel: a tanker truck under flames."""
    cv.rect(x, y, w, h, LIGHT)
    cv.frame(x, y, w, h, NAVY, 3)
    # Smoke.
    cv.disc(x + 70, y + 40, 16, MUTED)
    cv.disc(x + 96, y + 30, 12, MUTED)
    cv.disc(x + 118, y + 42, 10, MUTED)
    # Flames above the tanker.
    flame(cv, x + 60, y + 18, 46, ORANGE, GOLD)
    flame(cv, x + 150, y + 8, 56, RUST, ORANGE)
    flame(cv, x + 240, y + 22, 40, ORANGE, GOLD)
    # Tanker body, cab and wheels.
    by = y + h - 78
    cv.rect(x + 30, by, 190, 44, TEAL)
    cv.rect(x + 30, by, 190, 8, NAVY)
    cv.rect(x + 220, by + 10, 56, 34, RUST)
    cv.rect(x + 232, by + 16, 22, 16, WHITE)
    for wx in (x + 62, x + 122, x + 182, x + 248):
        cv.disc(wx, by + 48, 13, INK)
        cv.disc(wx, by + 48, 5, LIGHT)
    # Road.
    cv.rect(x, by + 64, w, 8, INK)
    for rx in range(x + 12, x + w - 12, 44):
        cv.rect(rx, by + 67, 22, 2, GOLD)


def icon_drop(cv, x, y, s, color):
    cv.tri(x + s // 2, y, x + s // 6, y + s // 2,
           x + s * 5 // 6, y + s // 2, color)
    cv.disc(x + s // 2, y + s * 3 // 5, s * 2 // 5, color)


def icon_bars(cv, x, y, s, color):
    bw = s // 4
    for i, hh in enumerate((s // 3, s * 2 // 3, s)):
        cv.rect(x + i * (bw + 4), y + s - hh, bw, hh, color)


def icon_shield(cv, x, y, s, color):
    cv.rect(x + s // 6, y, s * 2 // 3, s * 3 // 4, color)
    cv.tri(x + s // 6, y + s * 3 // 4, x + s * 5 // 6, y + s * 3 // 4,
           x + s // 2, y + s, color)
    cv.rect(x + s // 2 - 2, y + s // 4, 4, s // 3, WHITE)


def icon_flag(cv, x, y, s, color):
    cv.vline(x + 4, y, s, INK)
    cv.rect(x + 6, y + 2, s - 8, s // 2, color)
    cv.rect(x + 6, y + 2, (s - 8) // 2, s // 4, WHITE)


def icon_chip(cv, x, y, s, color):
    cv.rect(x + s // 5, y + s // 5, s * 3 // 5, s * 3 // 5, color)
    cv.rect(x + s * 2 // 5, y + s * 2 // 5, s // 5, s // 5, WHITE)
    for i in range(3):
        cv.rect(x + s // 5 + i * s // 5, y, 3, s // 5, INK)
        cv.rect(x + s // 5 + i * s // 5, y + s * 4 // 5, 3, s // 5, INK)


def story_column(cv, x, y, w, h, kicker, kcolor, heads, body, icon, icolor):
    cv.rect(x, y, w, h, PANEL)
    cv.frame(x, y, w, h, NAVY, 2)
    cv.rect(x, y, w, 6, kcolor)
    tx = x + 16
    ty = y + 20
    cv.text(tx, ty, kicker, 2, kcolor)
    ty += 26
    for ln in heads:
        cv.text(tx, ty, ln, 3, INK)
        ty += 27
    ty += 6
    # Narrow the body so its lines stop short of the icon at bottom right.
    for ln in cv.wrap(body, 2, w - 96):
        cv.text(tx, ty, ln, 2, INK)
        ty += 18
    icon(cv, x + w - 56, y + h - 52, 40, icolor)


def story_wide(cv, x, y, w, h, kicker, kcolor, heads, body, icon, icolor):
    cv.rect(x, y, w, h, PANEL)
    cv.frame(x, y, w, h, NAVY, 2)
    cv.rect(x, y, w, 6, kcolor)
    tx = x + 16
    ty = y + 20
    cv.text(tx, ty, kicker, 2, kcolor)
    ty += 26
    for ln in heads:
        cv.text(tx, ty, ln, 3, INK)
        ty += 27
    ty += 6
    # Narrow the body so its lines stop short of the icon at bottom right.
    for ln in cv.wrap(body, 2, w - 96):
        cv.text(tx, ty, ln, 2, INK)
        ty += 18
    icon(cv, x + w - 56, y + h - 52, 40, icolor)


def build():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 124, NAVY)
    cv.text_c(14, "THE WORLD", 7, WHITE)
    cv.hline(212, 70, 600, GOLD)
    cv.text_c(78, "THURSDAY, 26 NOVEMBER 2026", 2, GOLD)
    cv.text_c(100, "SIX STORIES FROM ONE DAY AROUND THE GLOBE", 2, WHITE)

    # Lead panel: Cairo tanker fire, text left, drawn scene right.
    lx, ly, lw, lh = 24, 140, 976, 256
    cv.rect(lx, ly, lw, lh, PANEL)
    cv.frame(lx, ly, lw, lh, NAVY, 2)
    cv.rect(lx, ly, lw, 6, ORANGE)
    cv.text(lx + 24, ly + 20, "LEAD - EGYPT", 2, ORANGE)
    cv.text(lx + 24, ly + 56, "FIRE ON CAIRO", 4, INK)
    cv.text(lx + 24, ly + 90, "RING ROAD KILLS 31", 4, INK)
    cv.text(lx + 24, ly + 134, "WEDNESDAY EVENING, WARRAQ, GIZA", 2, MUTED)
    for i, ln in enumerate(cv.wrap(
            "A FUEL TANKER OVERTURNED ON THE RING ROAD IN GIZA AND BURST "
            "INTO FLAMES, KILLING AT LEAST 31 PEOPLE AND INJURING 21. "
            "DOZENS OF CARS BURNED.", 2, 592)):
        cv.text(lx + 24, ly + 162 + i * 18, ln, 2, INK)
    cv.text(lx + 24, ly + 224, "31 DEAD - 21 INJURED", 3, RUST)
    tanker_scene(cv, lx + 640, ly + 20, 312, lh - 40)

    # Row of three columns.
    ry, rh = 412, 240
    cw = 315
    story_column(cv, 24, ry, cw, rh, "MIDDLE EAST", RUST,
                 ["HOUTHIS CLAIM", "REFINERY STRIKE"],
                 "HOUTHIS SAY THEY HIT THE RAS TANURA REFINERY. IRAN SAYS "
                 "MORE TANKERS HIT MINES IN HORMUZ.",
                 icon_drop, RUST)
    story_column(cv, 354, ry, cw, rh, "TRADE - USA", TEAL,
                 ["NEW US TARIFFS", "ON 14 PARTNERS"],
                 "WASHINGTON PLANS NEW TARIFFS ON 14 PARTNERS OVER "
                 "OVERCAPACITY. CHINA FACES THE TOP RATES.",
                 icon_bars, TEAL)
    story_column(cv, 684, ry, cw, rh, "EUROPE - NATO", NAVY,
                 ["POLAND WANTS", "A NO-FLY ZONE"],
                 "POLAND PLANS A NO-FLY ZONE ON ITS EAST BORDER AND URGES "
                 "NATO TO DOWN RUSSIAN MISSILES.",
                 icon_shield, NAVY)

    # Row of two wider panels.
    wy, wh = 668, 204
    ww = 480
    story_wide(cv, 24, wy, ww, wh, "ASIA - DIPLOMACY", GOLD,
               ["PYONGYANG EXPELS", "SWISS DIPLOMAT"],
               "NORTH KOREA ORDERED SWITZERLAND'S ENVOY OUT IN 48 HOURS "
               "AND SHUT ITS PYONGYANG OFFICE IN A SANCTIONS ROW.",
               icon_flag, GOLD)
    story_wide(cv, 520, wy, ww, wh, "TECH - MARKETS", TEAL,
               ["S&P PUTS NVIDIA", "ON DOWNGRADE WATCH"],
               "S&P PUT NVIDIA'S AA RATING ON CREDITWATCH NEGATIVE AFTER "
               "HUANG'S EXIT AND RETURN EXPOSED BOARD WEAKNESSES.",
               icon_chip, TEAL)

    # Ticker strip.
    ty = 888
    cv.rect(0, ty, W, 112, NAVY)
    cv.text(24, ty + 14, "ALSO TODAY", 2, GOLD)
    cv.text(24, ty + 40,
            "MACY'S THANKSGIVING PARADE PUT OFF TO SATURDAY AS STORMS "
            "DELAY 4,500 US FLIGHTS", 2, WHITE)
    cv.text(24, ty + 62,
            "DURAN DURAN GUITARIST ANDY TAYLOR DIES AT 65 - BANGLADESH "
            "GARMENT WAGE TK 17,000", 2, WHITE)
    cv.text(24, ty + 84,
            "SECOND JUDGE BLOCKS TRUMP'S BIRTHRIGHT CITIZENSHIP ORDER",
            2, WHITE)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    png = build().to_png()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
