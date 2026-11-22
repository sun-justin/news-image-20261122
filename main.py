"""news-image-20261122: draws a newspaper front page summing up the
world news of Sunday 22 November 2026, as a 1024x1024 PNG.

Pure Python 3 standard library. No network, no clock, no randomness:
running it twice writes byte-identical output.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- PNG writer

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels):
    """pixels: list of H rows, each a bytearray of W*3 RGB bytes."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ------------------------------------------------------------------- canvas

class Canvas:
    def __init__(self):
        self.px = [bytearray(W * 3) for _ in range(H)]

    def fill(self, r, g, b):
        row = bytes((r, g, b)) * W
        for y in range(H):
            self.px[y][:] = row

    def rect(self, x0, y0, x1, y1, col):
        r, g, b = col
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(W, x1)
        y1 = min(H, y1)
        if x1 <= x0 or y1 <= y0:
            return
        span = bytes((r, g, b)) * (x1 - x0)
        for y in range(y0, y1):
            self.px[y][x0 * 3:x1 * 3] = span

    def hline(self, x0, x1, y, col, thick=1):
        self.rect(x0, y, x1, y + thick, col)

    def vline(self, x, y0, y1, col, thick=1):
        self.rect(x, y0, x + thick, y1, col)

    def disc(self, cx, cy, rad, col):
        r, g, b = col
        for dy in range(-rad, rad + 1):
            dx = int((rad * rad - dy * dy) ** 0.5)
            y = cy + dy
            if 0 <= y < H:
                x0 = max(0, cx - dx)
                x1 = min(W, cx + dx + 1)
                self.px[y][x0 * 3:x1 * 3] = bytes((r, g, b)) * (x1 - x0)

    def ring(self, cx, cy, rad, col, thick=2):
        r, g, b = col
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                d = (dx * dx + dy * dy) ** 0.5
                if rad - thick <= d <= rad:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < W and 0 <= y < H:
                        self.px[y][x * 3:x * 3 + 3] = bytes((r, g, b))

    def line(self, x0, y0, x1, y1, col, thick=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = x0 + dx * i // steps
            y = y0 + dy * i // steps
            self.rect(x - thick // 2, y - thick // 2,
                      x + thick - thick // 2, y + thick - thick // 2, col)

    def tri(self, x0, y0, x1, y1, x2, y2, col):
        # filled triangle via scanlines
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) // (yb - ya)
        for y in range(ay, cy + 1):
            if y < by:
                xa = edge(ax, ay, bx, by, y)
                xb = edge(ax, ay, cx, cy, y)
            else:
                xa = edge(bx, by, cx, cy, y)
                xb = edge(ax, ay, cx, cy, y)
            if xa > xb:
                xa, xb = xb, xa
            self.rect(xa, y, xb + 1, y + 1, col)


# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows, each a 5-bit value (bit 4 = leftmost pixel).

FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0, 0, 0, 0, 0),
    "[": (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    "]": (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
}

# ------------------------------------------------------------ text drawing

CHAR_W = 6   # 5 pixels + 1 gap, in font units
CHAR_H = 7


def text_w(s, scale):
    return len(s) * CHAR_W * scale - scale


def draw_char(cv, ch, x, y, scale, col):
    glyph = FONT.get(ch.upper(), FONT[" "])
    r, g, b = col
    for row in range(7):
        bits = glyph[row]
        for c in range(5):
            if bits & (0x10 >> c):
                cv.rect(x + c * scale, y + row * scale,
                        x + (c + 1) * scale, y + (row + 1) * scale,
                        (r, g, b))


def draw_text(cv, s, x, y, scale, col):
    cx = x
    for ch in s:
        draw_char(cv, ch, cx, y, scale, col)
        cx += CHAR_W * scale
    return cx


def draw_centered(cv, s, cx, y, scale, col):
    draw_text(cv, s, cx - text_w(s, scale) // 2, y, scale, col)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns list of lines that fit max_w pixels."""
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(cv, s, x, y, scale, col, max_w, leading=None):
    """Draw wrapped paragraph; returns y after the last line."""
    lh = leading if leading is not None else CHAR_H * scale + 4
    for line in wrap(s, scale, max_w):
        draw_text(cv, line, x, y, scale, col)
        y += lh
    return y


# ------------------------------------------------------------------- colours

INK = (24, 24, 28)
PAPER = (250, 247, 238)
NAVY = (18, 38, 74)
NAVY_LT = (38, 66, 112)
RED = (178, 34, 34)
GOLD = (198, 148, 42)
GREY = (96, 96, 100)
LINE = (180, 175, 160)
BLUE = (42, 96, 160)
GREEN = (34, 120, 70)
SKY = (176, 214, 235)
SEA = (52, 110, 158)
SAND = (226, 205, 160)
ORANGE = (224, 110, 30)
SMOKE = (120, 120, 118)


# ---------------------------------------------------------------- scene art

def draw_globe(cv, cx, cy, rad):
    """A warming globe: blue oceans, green land blobs, red heat arrow."""
    cv.disc(cx, cy, rad, BLUE)
    # land blobs (ellipses approximated by discs)
    cv.disc(cx - rad // 2, cy - rad // 3, rad // 4, GREEN)
    cv.disc(cx + rad // 3, cy + rad // 6, rad // 3, GREEN)
    cv.disc(cx - rad // 5, cy + rad // 2, rad // 5, GREEN)
    cv.disc(cx + rad // 2, cy - rad // 2, rad // 6, GREEN)
    cv.ring(cx, cy, rad, NAVY, 3)
    # latitude lines
    cv.hline(cx - rad + 6, cx + rad - 5, cy - rad // 2, (200, 225, 240), 2)
    cv.hline(cx - rad + 6, cx + rad - 5, cy + rad // 2, (200, 225, 240), 2)
    # heat arrow rising on the right
    ax = cx + rad + 16
    cv.line(ax, cy + rad // 2, ax, cy - rad // 2 - 8, RED, 5)
    cv.tri(ax - 9, cy - rad // 2 + 4, ax + 9, cy - rad // 2 + 4,
           ax, cy - rad // 2 - 16, RED)
    # small sun
    cv.disc(cx - rad - 26, cy - rad - 6, 14, GOLD)
    for k in range(8):
        ang = k * 0.785398
        x0 = int(cx - rad - 26 + 18 * math.cos(ang))
        y0 = int(cy - rad - 6 + 18 * math.sin(ang))
        x1 = int(cx - rad - 26 + 26 * math.cos(ang))
        y1 = int(cy - rad - 6 + 26 * math.sin(ang))
        cv.line(x0, y0, x1, y1, GOLD, 3)


def draw_tanker(cv, x, y, w, h):
    """Oil tanker on a strait at dusk, with a smoke plume."""
    # sky
    cv.rect(x, y, x + w, y + h // 2, (238, 196, 140))
    cv.disc(x + w - 46, y + 26, 18, (240, 120, 40))
    # sea
    cv.rect(x, y + h // 2, x + w, y + h, SEA)
    cv.hline(x, x + w, y + h // 2 + 8, (255, 255, 255), 2)
    cv.hline(x + 20, x + w - 30, y + h // 2 + 22, (255, 255, 255), 2)
    # hull
    hy = y + h // 2 + 26
    cv.rect(x + 14, hy, x + w - 14, hy + 22, (40, 40, 44))
    cv.rect(x + 14, hy, x + w - 14, hy + 6, RED)
    # deck + bridge
    cv.rect(x + w - 62, hy - 26, x + w - 22, hy, (245, 245, 240))
    cv.rect(x + w - 62, hy - 26, x + w - 22, hy - 18, NAVY)
    cv.rect(x + 34, hy - 14, x + w - 76, hy, (120, 120, 118))
    # funnel with smoke
    cv.rect(x + 44, hy - 30, x + 62, hy - 14, (30, 30, 34))
    cv.disc(x + 53, hy - 44, 10, SMOKE)
    cv.disc(x + 66, hy - 58, 13, SMOKE)
    cv.disc(x + 84, hy - 72, 16, SMOKE)


def draw_handcuffs(cv, x, y, s):
    """Two linked rings: a cartel boss in custody."""
    cv.ring(x, y, 16 * s // 2, NAVY, 3)
    cv.ring(x + 34 * s // 2, y, 16 * s // 2, NAVY, 3)
    cv.line(x + 14 * s // 2, y - 4, x + 20 * s // 2, y + 4, NAVY, 3)
    cv.line(x + 14 * s // 2, y + 4, x + 20 * s // 2, y - 4, NAVY, 3)


def draw_chart_down(cv, x, y, w, h):
    """A falling market line over bars."""
    cv.rect(x, y, x + w, y + h, (246, 240, 228))
    n = 6
    heights = [62, 74, 58, 44, 52, 26]
    bw = w // (n * 2)
    for i, ht in enumerate(heights):
        bx = x + 8 + i * 2 * bw
        cv.rect(bx, y + h - 6 - ht * h // 110, bx + bw, y + h - 6,
                (120, 130, 150) if i < 5 else RED)
    pts = [(x + 8 + i * 2 * bw + bw // 2,
            y + h - 10 - heights[i] * h // 110) for i in range(n)]
    for i in range(n - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 4)
    cv.tri(pts[-1][0] - 8, pts[-1][1] - 2, pts[-1][0] + 8, pts[-1][1] - 2,
           pts[-1][0], pts[-1][1] + 14, RED)


def draw_flags(cv, x, y, s):
    """Three small flag poles: US, China, Russia meeting."""
    cols = [(178, 34, 34), (222, 41, 16), (255, 255, 255)]
    for i, c in enumerate(cols):
        fx = x + i * 34
        cv.vline(fx, y, y + 44, NAVY, 3)
        cv.rect(fx + 3, y, fx + 27, y + 16, c)
    # table between the poles
    cv.rect(x - 4, y + 44, x + 3 * 34 + 4, y + 50, (120, 84, 50))

# ------------------------------------------------------------------- layout

def box(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, PAPER)
    cv.rect(x0, y0, x1, y0 + 2, LINE)
    cv.rect(x0, y1 - 2, x1, y1, LINE)
    cv.rect(x0, y0, x0 + 2, y1, LINE)
    cv.rect(x1 - 2, y0, x1, y1, LINE)


def kicker(cv, s, x, y, col=RED):
    draw_text(cv, s, x, y, 2, col)


def headline(cv, s, x, y, scale, max_w, col=INK, leading=None):
    lh = leading if leading is not None else CHAR_H * scale + 5
    for line in wrap(s, scale, max_w):
        draw_text(cv, line, x, y, scale, col)
        y += lh
    return y


def build():
    cv = Canvas()
    cv.fill(*PAPER)

    # ---- masthead
    cv.rect(0, 0, W, 120, NAVY)
    cv.rect(0, 120, W, 124, GOLD)
    draw_centered(cv, "THE WORLD TODAY", W // 2, 14, 6, (250, 247, 238))
    draw_centered(cv, "SUNDAY 22 NOVEMBER 2026", W // 2, 66, 2, GOLD)
    draw_centered(cv, "THE DAY'S WORLD NEWS IN ONE PAGE", W // 2, 92, 2,
                  (210, 215, 228))

    # ---- lead story: COP31, Antalya
    box(cv, 24, 136, 628, 452)
    kicker(cv, "CLIMATE - ANTALYA, TURKEY", 44, 152)
    y = headline(cv, "CLIMATE TALKS STALL AS DRAFT DROPS FOSSIL FUELS",
                 44, 178, 3, 556)
    y = para(cv, "THE UN CLIMATE SUMMIT ENTERED A 2ND DAY OF OVERTIME "
             "ON SUNDAY.", 44, y + 8, 2, INK, 330)
    y = para(cv, "THE LATEST DRAFT DEAL MAKES NO MENTION OF FOSSIL "
             "FUELS, COAL, OIL OR GAS.", 44, y + 6, 2, INK, 330)
    y = para(cv, "IT SETS A GOAL OF CAPTURING 1BN TONNES OF CARBON "
             "AND 35% ELECTRICITY BY 2035.", 44, y + 6, 2, INK, 330)
    draw_globe(cv, 500, 330, 62)

    # ---- Iran strikes Bahrain; tankers hit in Hormuz
    box(cv, 648, 136, 1000, 452)
    kicker(cv, "CONFLICT - THE GULF", 668, 152)
    y = headline(cv, "IRAN STRIKES BAHRAIN PLANT; 2 TANKERS HIT",
                 668, 178, 3, 312)
    y = para(cv, "BAHRAIN: IRAN HIT A CIVILIAN PLANT; FIRE, NO ONE HURT.",
             668, y + 6, 2, INK, 312)
    draw_tanker(cv, 664, 340, 320, 100)

    # ---- row 2: Mexico / Shenzhen / markets
    box(cv, 24, 468, 336, 692)
    kicker(cv, "JUSTICE - SINALOA", 40, 484)
    draw_handcuffs(cv, 292, 492, 1)
    y = headline(cv, "CARTEL BOSS 'EL CHAPO ISIDRO' CAPTURED; 11 KILLED",
                 40, 510, 2, 280)
    para(cv, "FBI TEN MOST WANTED FUGITIVE FAUSTO ISIDRO MEZA FLORES "
         "SEIZED IN GUASAVE. 7 GUNMEN AND 4 SOLDIERS DEAD.",
         40, y + 6, 2, INK, 280)

    box(cv, 356, 468, 668, 692)
    kicker(cv, "POLITICS - SHENZHEN", 372, 484)
    y = headline(cv, "TRUMP, XI AND PUTIN MEET IN SHENZHEN; AGREE "
                 "NUCLEAR-RISK TALKS", 372, 510, 2, 280)
    para(cv, "THE US, CHINA AND RUSSIA LEADERS MET AND AGREED TO "
         "START NUCLEAR-RISK TALKS.",
         372, y + 6, 2, INK, 280)
    draw_flags(cv, 400, 640, 1)

    box(cv, 688, 468, 1000, 692)
    kicker(cv, "ECONOMY - NEW YORK", 704, 484)
    y = headline(cv, "AI SELL-OFF PUSHES US STOCKS INTO CORRECTION",
                 704, 510, 2, 280)
    para(cv, "S&P 500 -3.70%; NASDAQ -5.3% IN A WEEK OF HEAVY "
         "TECH LOSSES.", 704, y + 6, 2, INK, 280)
    draw_chart_down(cv, 704, 612, 280, 64)

    # ---- row 3: briefs
    draw_text(cv, "MORE FROM 22 NOVEMBER", 24, 708, 2, NAVY_LT)
    cv.hline(24, 1000, 728, LINE, 2)

    briefs_left = [
        ("EU AND INDONESIA SIGN TRADE DEAL",
         "AFTER 10 YEARS OF TALKS; TARIFFS ON 98% OF EU EXPORTS TO GO."),
        ("RUSSIA HITS ZELENSKYY'S HOMETOWN",
         "MISSILE STRIKE ON KRYVYI RIH KILLS 2, WOUNDS DOZENS."),
        ("3 DEAD, 36 MISSING IN FACTORY FIRE",
         "FIRE AT A FACTORY IN INDONESIA; RESCUERS SEARCH FOR THE MISSING."),
    ]
    briefs_right = [
        ("GTA 6 SETS $3.79BN LAUNCH RECORD",
         "BIGGEST DAY-ONE ENTERTAINMENT LAUNCH EVER, AT AN ESTIMATED "
         "$3.79 BILLION."),
        ("UN STATES AGREE AUTONOMOUS-WEAPONS RULES",
         "TENTATIVE DEAL ON AI-WEAPONS LIMITS."),
        ("DENMARK EXPELS RUSSIAN ATTACHE",
         "COPENHAGEN CITES AN ALLEGED PLOT."),
    ]
    by = 740
    for head, body in briefs_left:
        y = headline(cv, head, 40, by, 2, 448, NAVY)
        para(cv, body, 40, y + 4, 2, INK, 448, leading=16)
        by += 60
    by = 740
    for head, body in briefs_right:
        y = headline(cv, head, 536, by, 2, 448, NAVY)
        para(cv, body, 536, y + 4, 2, INK, 448, leading=16)
        by += 60

    # ---- footer: markets strip
    cv.rect(0, 928, W, H, NAVY)
    draw_centered(cv, "MARKETS: S&P 500 6,910 -3.70%   NASDAQ -5.3%   "
                  "FTSE 100 10,346 -1.02%", W // 2, 942, 2,
                  (250, 247, 238))
    draw_centered(cv, "BRENT CRUDE $89.95 +0.57%   |   SOURCES: AP, AFP "
                  "AND REUTERS DIGESTS, 22 NOV 2026", W // 2, 970, 2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(os.path.join(out_dir, "entry.png"), cv.px)


if __name__ == "__main__":
    main()
