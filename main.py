#!/usr/bin/env python3
"""Solmara Daily -- Wednesday 25 November 2026 world news poster.

Draws a 1024x1024 newspaper front page as a PNG using only the Python
standard library (zlib + struct for the PNG encoder, a hand-built 5x7
bitmap font for text). No network, no third-party packages.
Deterministic: identical input always produces identical bytes.
SPDX-License-Identifier: MIT
"""
import os
import struct
import zlib

SIZE = 1024

# --- palette ---------------------------------------------------------------
PAPER = (248, 244, 232)
INK = (22, 28, 44)
RED = (178, 34, 28)
NAVY = (18, 52, 86)
GREEN = (16, 110, 66)
GOLD = (176, 132, 40)
CREAM = (234, 226, 204)
GREY = (110, 106, 96)
WHITE = (255, 255, 255)
SKY = (196, 220, 232)
SEA = (28, 78, 92)
SMOKE = (146, 142, 132)
FIRE = (226, 96, 30)
BROWN = (122, 82, 44)

# --- 5x7 bitmap font, drawn for this poster --------------------------------
# Each glyph: 7 rows of 5 bits. Text is uppercased before drawing.
GLYPHS = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
BLANK = ("00000",) * 7
ADVANCE = 6  # pixels per character at scale 1 (5 glyph + 1 gap)


def text_width(text, scale):
    return len(text) * ADVANCE * scale


def split_lines(text, max_w, scale):
    """Greedy word wrap into lines that fit max_w pixels."""
    lines, current = [], ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, size, bg):
        self.size = size
        self.buf = bytearray(bg * (size * size))

    def pixel(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            i = (y * self.size + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.pixel(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def write(self, x, y, text, scale, color):
        cx = x
        for ch in text.upper():
            bits = GLYPHS.get(ch, BLANK)
            for r in range(7):
                row = bits[r]
                for c in range(5):
                    if row[c] == '1':
                        self.rect(cx + c * scale, y + r * scale,
                                  scale, scale, color)
            cx += ADVANCE * scale
        return cx

    def write_center(self, cx, y, text, scale, color):
        return self.write(cx - text_width(text, scale) // 2, y,
                          text, scale, color)

    def paragraph(self, x, y, text, scale, color, max_w, gap=None):
        if gap is None:
            gap = 9 * scale
        for line in split_lines(text, max_w, scale):
            self.write(x, y, line, scale, color)
            y += gap
        return y


# --- PNG writer ------------------------------------------------------------
def encode_png(path, canvas):
    raw = bytearray()
    stride = canvas.size * 3
    for y in range(canvas.size):
        raw.append(0)
        start = y * stride
        raw += canvas.buf[start:start + stride]
    packed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.size, canvas.size, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", packed)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# --- drawn scenes ----------------------------------------------------------
def draw_sea_battle(cv, x, y, w, h):
    """Gulf of Finland at dawn: sky, sea, a struck ship, smoke, a drone."""
    horizon = h * 2 // 5
    cv.rect(x, y, w, horizon, SKY)
    cv.rect(x, y + horizon, w, h - horizon, SEA)
    # low sun
    cv.rect(x + w - 150, y + 8, 44, 44, GOLD)
    # ship: hull, superstructure, funnels -- kept inside the scene box
    hull_y = y + horizon + 15
    cv.rect(x + 70, hull_y, w - 260, 28, INK)
    cv.rect(x + 150, hull_y - 30, 170, 30, INK)
    cv.rect(x + 185, hull_y - 48, 20, 20, INK)
    cv.rect(x + 250, hull_y - 48, 20, 20, INK)
    # fire on the deck
    cv.rect(x + 330, hull_y - 12, 96, 12, FIRE)
    cv.rect(x + 352, hull_y - 24, 52, 12, FIRE)
    # smoke columns
    cv.rect(x + 350, y + 6, 32, 28, SMOKE)
    cv.rect(x + 368, y + 2, 24, 20, SMOKE)
    cv.rect(x + 326, y + 30, 20, 18, SMOKE)
    # drone above the ship
    cv.rect(x + 560, y + 26, 60, 10, INK)
    cv.rect(x + 560, y + 20, 10, 22, INK)
    cv.rect(x + 610, y + 20, 10, 22, INK)
    # waves below the hull
    for wx in range(x + 20, x + w - 40, 90):
        cv.rect(wx, y + h - 6, 56, 4, WHITE)


def draw_chip(cv, x, y, w, h):
    """A green computer chip with pins and a rising chart arrow."""
    cv.rect(x, y, w, h, CREAM)
    # chip body, left half
    cw, ch = 96, 72
    cx, cy = x + 14, y + (h - ch) // 2
    cv.rect(cx, cy, cw, ch, GREEN)
    cv.rect(cx + 26, cy + 20, 44, 32, PAPER)
    cv.write(cx + 32, cy + 28, "AI", 2, GREEN)
    # pins
    for px in range(cx + 10, cx + cw - 6, 22):
        cv.rect(px, cy - 12, 7, 12, GREEN)
        cv.rect(px, cy + ch, 7, 12, GREEN)
    for py in range(cy + 10, cy + ch - 6, 22):
        cv.rect(cx - 12, py, 12, 7, GREEN)
        cv.rect(cx + cw, py, 12, 7, GREEN)
    # rising arrow chart, right half
    ax = x + w // 2 + 16
    base = y + h - 22
    cv.hline(ax, base, w - (ax - x) - 10, INK, 3)
    cv.vline(ax, y + 22, h - 44, INK, 3)
    pts = [(ax + 6, base - 10), (ax + 34, base - 28),
           (ax + 62, base - 20), (ax + 92, base - 52)]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for s in range(steps + 1):
            px = x0 + (x1 - x0) * s // steps
            py = y0 + (y1 - y0) * s // steps
            cv.rect(px, py, 4, 4, RED)
    cv.rect(pts[-1][0] - 3, pts[-1][1] - 3, 20, 5, RED)
    cv.rect(pts[-1][0] + 12, pts[-1][1] - 3, 5, 20, RED)


def draw_tower(cv, x, y, w, h):
    """Riyadh's tallest tower: a tapering skyscraper, antenna, a drone."""
    cv.rect(x, y, w, h, CREAM)
    # night sky band
    cv.rect(x, y, w, 26, NAVY)
    # tower
    tx = x + w // 2 - 34
    cv.rect(tx, y + 44, 68, h - 44, INK)
    cv.rect(tx - 14, y + 70, 96, 12, NAVY)
    cv.rect(tx + 26, y + 20, 16, 26, INK)
    cv.rect(tx + 30, y + 8, 8, 14, RED)
    # lit windows
    for wy in range(y + 88, y + h - 16, 26):
        for wx in (tx + 10, tx + 30, tx + 50):
            cv.rect(wx, wy, 10, 12, GOLD)
    # drone + blast marks
    cv.rect(x + w - 66, y + 46, 44, 8, RED)
    cv.rect(x + w - 66, y + 40, 8, 20, RED)
    cv.rect(x + w - 30, y + 40, 8, 20, RED)
    cv.rect(x + w - 60, y + 66, 30, 6, FIRE)
    cv.rect(x + w - 52, y + 76, 14, 6, FIRE)


def draw_court(cv, x, y, w, h):
    """A judge's gavel over a law book."""
    cv.rect(x, y, w, h, CREAM)
    # gavel head and handle
    gw = w - 90
    cv.rect(x + 34, y + 18, gw, 26, BROWN)
    cv.rect(x + 22, y + 13, 12, 36, BROWN)
    cv.rect(x + 34 + gw, y + 13, 12, 36, BROWN)
    cv.rect(x + w // 2 - 8, y + 44, 16, h - 100, BROWN)
    # sound block and book
    cv.rect(x + w // 2 - 30, y + h - 62, 60, 12, INK)
    cv.rect(x + 20, y + h - 44, w - 40, 28, RED)
    cv.rect(x + 20, y + h - 48, w - 40, 4, WHITE)
    cv.write(x + w // 2 - 18, y + h - 38, "LAW", 2, WHITE)


def draw_medal(cv, x, y, w, h):
    """A gold medal on a ribbon, with stars."""
    cv.rect(x, y, w, h, CREAM)
    # ribbon
    cv.rect(x + w // 2 - 26, y + 8, 22, 52, RED)
    cv.rect(x + w // 2 + 4, y + 8, 22, 52, NAVY)
    # medal disc
    disc = min(w - 24, h - 66)
    mx, my = x + (w - disc) // 2, y + 56
    cv.rect(mx, my, disc, disc, GOLD)
    inner = disc - 24
    cv.rect(mx + 12, my + 12, inner, inner, PAPER)
    cv.write(mx + disc // 2 - 9, my + disc // 2 - 14, "1", 4, GOLD)
    # stars
    cv.write(x + 8, y + 14, "*", 2, GOLD)
    cv.write(x + w - 26, y + 14, "*", 2, GOLD)


def draw_turkey(cv, x, y, w, h):
    """A plump turkey with a fanned tail, spared for Thanksgiving."""
    # tail feathers fanning out, sized to the art box
    fw = w // 6
    for i in range(5):
        col = FIRE if i % 2 == 0 else GOLD
        cv.rect(x + 4 + i * fw, y + 8, fw - 3, h - 76, col)
    # body and head
    bw = w * 2 // 5
    bx = x + (w - bw) // 2
    cv.rect(bx, y + h - 66, bw, 52, BROWN)
    cv.rect(bx + 8, y + h - 80, bw - 16, 20, BROWN)
    cv.rect(bx + bw // 2 - 8, y + h - 94, 18, 18, BROWN)
    cv.rect(bx + bw // 2 + 10, y + h - 90, 12, 6, RED)
    # legs and ground
    cv.rect(bx + 10, y + h - 16, 8, 16, GOLD)
    cv.rect(bx + bw - 18, y + h - 16, 8, 16, GOLD)
    cv.rect(x, y + h - 8, w, 8, GREEN)


# --- content: Wednesday 25 November 2026 -----------------------------------
LEAD = {
    "kicker": "UKRAINE WAR AT SEA",
    "headline": "KYIV CONFIRMS STRIKES ON RUSSIAN SHIPS",
    "standfirst": ("President Zelenskyy says Ukraine hit a Russian cargo "
                   "ship in the Gulf of Finland and sank a warship off "
                   "Libya, opening new fronts far from home."),
}

COLUMNS = [
    {
        "kicker": "MARKETS",
        "color": GREEN,
        "art": draw_chip,
        "headline": "HUANG BACK AS NVIDIA SOARS 31%",
        "body": ("Nvidia gains $1 trillion in a day as Huang returns as "
                 "chief executive."),
    },
    {
        "kicker": "MIDDLE EAST",
        "color": RED,
        "art": draw_tower,
        "headline": "HOUTHIS HIT RIYADH TOWER",
        "body": ("A drone hits the capital's tallest tower; eleven people "
                 "are wounded."),
    },
    {
        "kicker": "JUSTICE",
        "color": NAVY,
        "art": draw_court,
        "headline": "HUAWEI GUILTY IN US TRIAL",
        "body": ("The Chinese tech giant is found guilty over its Iran "
                 "business in a US trial."),
    },
]

WIDE = {
    "kicker": "WASHINGTON",
    "color": NAVY,
    "art": draw_medal,
    "headline": "GIULIANI GIVEN MEDAL OF FREEDOM",
    "body": ("Trump awards the Medal of Freedom to former New York mayor "
             "Rudy Giuliani."),
}

TURKEY = {
    "kicker": "THANKSGIVING",
    "color": BROWN,
    "art": draw_turkey,
    "headline": "TURKEYS SPARED FOR THANKSGIVING",
    "body": ("Trump pardons two Thanksgiving turkeys at the White House."),
}

BRIEFS = [
    "NATO TO SEND JETS TO POLAND.",
    "IRAN: TANKERS HIT IN HORMUZ.",
    "ENGLAND LEVEL T20 SERIES.",
    "GTA 6 OUT WORLDWIDE 19 NOV.",
]


# --- layout ----------------------------------------------------------------
def column(cv, x, top, item, width):
    item["art"](cv, x, top, width, 120)
    top += 132
    cv.hline(x, top, width, item["color"], 4)
    top += 12
    cv.write(x, top, item["kicker"], 2, item["color"])
    top += 26
    top = cv.paragraph(x, top, item["headline"], 3, INK, width, gap=26)
    top += 6
    top = cv.paragraph(x, top, item["body"], 2, GREY, width, gap=18)
    return top


def half_story(cv, x, top, item, width):
    """Art on the left, text on the right, for the half-width row."""
    art_w = 130
    item["art"](cv, x, top, art_w, 140)
    tx = x + art_w + 16
    tw = width - art_w - 16
    cv.write(tx, top + 4, item["kicker"], 2, item["color"])
    hy = cv.paragraph(tx, top + 30, item["headline"], 3, INK, tw, gap=26)
    cv.paragraph(tx, hy + 6, item["body"], 2, GREY, tw, gap=18)
    return top + 146


def build():
    cv = Canvas(SIZE, PAPER)
    M = 40
    inner = SIZE - 2 * M

    # --- masthead ----------------------------------------------------------
    cv.hline(M, 24, inner, INK, 5)
    cv.write_center(SIZE // 2, 42, "SOLMARA DAILY", 7, INK)
    cv.hline(M, 116, inner, RED, 4)
    cv.write(M, 130, "WEDNESDAY 25 NOVEMBER 2026", 2, RED)
    right = "WORLD NEWS IN ONE PAGE"
    cv.write(SIZE - M - text_width(right, 2), 130, right, 2, GREY)
    cv.hline(M, 156, inner, INK, 2)

    # --- lead story ----------------------------------------------------------
    y = 172
    cv.write(M, y, LEAD["kicker"], 2, RED)
    y += 26
    y = cv.paragraph(M, y, LEAD["headline"], 4, INK, inner, gap=36)
    y += 8
    y = cv.paragraph(M, y, LEAD["standfirst"], 2, GREY, inner, gap=18)
    y += 12
    draw_sea_battle(cv, M, y, inner, 84)
    y += 84 + 12
    cv.hline(M, y, inner, INK, 2)
    y += 16

    # --- three-column row ----------------------------------------------------
    gap = 24
    col_w = (inner - 2 * gap) // 3
    bottom = y
    for i, item in enumerate(COLUMNS):
        end = column(cv, M + i * (col_w + gap), y, item, col_w)
        bottom = max(bottom, end)
    y = bottom + 14
    cv.hline(M, y, inner, INK, 2)
    y += 16

    # --- half-width row: medal story + turkey story -------------------------
    half_w = (inner - gap) // 2
    y = half_story(cv, M, y, WIDE, half_w)
    half_story(cv, M + half_w + gap, y - 146, TURKEY, half_w)
    y += 12
    cv.hline(M, y, inner, GOLD, 3)
    y += 12

    # --- briefs ticker ---------------------------------------------------------
    cv.write(M, y, "ALSO TODAY", 2, RED)
    y += 20
    brief_w = (inner - gap) // 2
    for i, brief in enumerate(BRIEFS):
        bx = M + (i % 2) * (brief_w + gap)
        by = y + (i // 2) * 20
        cv.rect(bx, by + 4, 9, 9, RED if i % 2 == 0 else GREEN)
        cv.write(bx + 18, by, brief, 2, INK)
    y += 38 + 2

    # --- footer ---------------------------------------------------------------
    cv.hline(M, SIZE - 54, inner, INK, 2)
    cv.write_center(SIZE // 2, SIZE - 42,
                    "ALL STORIES FROM PUBLIC REPORTING", 2, GREY)
    cv.write_center(SIZE // 2, SIZE - 24,
                    "SOLMARA DAILY  -  25 NOVEMBER 2026", 2, GREY)
    assert y < SIZE - 54, "layout overflow: content ends at %d" % y
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "entry.png")
    page = build()
    encode_png(out, page)
    print("wrote", out)


if __name__ == "__main__":
    main()
