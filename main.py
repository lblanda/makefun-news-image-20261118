#!/usr/bin/env python3
"""Draw a one-page news poster for Wednesday 18 November 2026.

Pure Python standard library only: no network, no third-party packages,
no fonts on disk. Text is drawn with a small 5x7 bitmap font defined
below; the image is encoded as a PNG with zlib. The program is fully
deterministic: the same input data always produces the same bytes.

Usage:
    python3 main.py            # writes /output/entry.png
    MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
"""

import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import news

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font, uppercase only. Each glyph is 7 rows of 5 bits.
# '#' is a set pixel, '.' is empty. Unknown characters render blank.
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
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}

BLANK = ("00000",) * 7


def text_width(text, scale):
    """Pixel width of text at the given integer scale."""
    return len(text) * 6 * scale - scale


def draw_text(canvas, x, y, text, colour, scale=2):
    """Draw upper-cased text; returns the x just past the last glyph."""
    for ch in text.upper():
        glyph = FONT.get(ch, BLANK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    canvas.fill_rect(
                        x + col * scale, y + row * scale, scale, scale, colour
                    )
        x += 6 * scale
    return x


def draw_text_centred(canvas, cx, y, text, colour, scale=2):
    x = cx - text_width(text, scale) // 2
    draw_text(canvas, x, y, text, colour, scale)
    return x


def wrap(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ PNG output ----
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Encode the canvas (list of RGB rows) as a deterministic PNG."""
    raw = bytearray()
    for row in canvas.pixels:
        raw.append(0)  # filter: none
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


class Canvas:
    def __init__(self, width, height, colour):
        self.w, self.h = width, height
        row = bytes(colour) * width
        self.pixels = [bytearray(row) for _ in range(height)]

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = x * 3
            self.pixels[y][i:i + 3] = bytes(colour)

    def fill_rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        fill = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            self.pixels[yy][x0 * 3:x1 * 3] = fill

    def rect(self, x, y, w, h, colour, thick=1):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill_rect(x0, y0, thick, thick, colour)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        for k in range(thick):
            rr = r - k
            if rr <= 0:
                break
            steps = max(8, rr * 6)
            for i in range(steps):
                import math
                a = 2 * math.pi * i / steps
                self.set(cx + int(rr * math.cos(a)), cy + int(rr * math.sin(a)), colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour):
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                self.fill_rect(int(min(xs)), yy, int(max(xs)) - int(min(xs)) + 1, 1, colour)

    def burst(self, cx, cy, r, colour, spikes=12):
        """Starburst: lines radiating from a centre, for explosions."""
        import math
        for i in range(spikes):
            a = 2 * math.pi * i / spikes
            rr = r if i % 2 == 0 else int(r * 0.55)
            self.line(cx, cy, cx + int(rr * math.cos(a)),
                      cy + int(rr * math.sin(a)), colour, 3)
        self.circle(cx, cy, max(3, r // 3), colour)


# ------------------------------------------------------------ palette ------
PAPER = (247, 243, 234)
NAVY = (20, 33, 61)
GOLD = (201, 162, 39)
INK = (24, 24, 24)
MUTED = (90, 90, 84)
CARD = (255, 255, 255)
RED = (178, 34, 34)
SEA = (46, 111, 152)
SAND = (214, 196, 150)
STEEL = (70, 80, 92)


def draw_masthead(c):
    c.fill_rect(0, 0, W, 118, NAVY)
    c.fill_rect(0, 118, W, 4, GOLD)
    draw_text_centred(c, W // 2, 16, news.MASTHEAD, (255, 255, 255), 6)
    draw_text_centred(c, W // 2, 66, news.DATE_LINE, GOLD, 3)
    draw_text(c, 24, 92, "MAKE.FUN - DAILY NEWS POSTER", (170, 180, 200), 1)
    draw_text(c, W - 24 - text_width("SIX STORIES, ONE DAY", 1), 92,
              "SIX STORIES, ONE DAY", (170, 180, 200), 1)


def draw_lead_scene(c, x, y, w, h):
    """Stylised Strait of Hormuz: sea, two shores, a tanker, bursts."""
    c.fill_rect(x, y, w, h, SEA)
    # northern shore (Iran) and southern shore (Arabian peninsula)
    c.triangle(x, y, x + w, y, x + int(w * 0.62), y + int(h * 0.34), SAND)
    c.triangle(x, y + h, x + w, y + h, x + int(w * 0.42), y + int(h * 0.66), SAND)
    c.fill_rect(x, y + int(h * 0.34), int(w * 0.62), 3, (160, 140, 100))
    c.fill_rect(x + int(w * 0.42), y + int(h * 0.66), int(w * 0.58), 3,
                (160, 140, 100))
    # tanker: dark hull, white superstructure, mast
    tx, ty = x + int(w * 0.30), y + int(h * 0.52)
    c.fill_rect(tx, ty, 120, 16, (30, 30, 34))
    c.fill_rect(tx + 82, ty - 14, 26, 14, (240, 240, 235))
    c.fill_rect(tx + 92, ty - 30, 4, 16, (240, 240, 235))
    c.fill_rect(tx, ty + 16, 120, 3, (200, 60, 40))
    # second, smaller ship
    tx2, ty2 = x + int(w * 0.66), y + int(h * 0.74)
    c.fill_rect(tx2, ty2, 76, 11, (30, 30, 34))
    c.fill_rect(tx2 + 52, ty2 - 10, 16, 10, (240, 240, 235))
    # explosion bursts over the strait
    c.burst(x + int(w * 0.55), y + int(h * 0.30), 26, (255, 176, 32), 12)
    c.burst(x + int(w * 0.55), y + int(h * 0.30), 12, (255, 90, 20), 8)
    c.burst(x + int(w * 0.82), y + int(h * 0.55), 20, (255, 176, 32), 10)
    # missile arcs
    c.line(x + int(w * 0.10), y + int(h * 0.22), x + int(w * 0.30),
           y + int(h * 0.10), (255, 255, 255), 2)
    c.line(x + int(w * 0.30), y + int(h * 0.10), x + int(w * 0.48),
           y + int(h * 0.26), (255, 255, 255), 2)
    c.circle(x + int(w * 0.48), y + int(h * 0.26), 4, (255, 255, 255))
    # labels
    draw_text(c, x + 10, y + 8, "IRAN", (60, 40, 20), 2)
    draw_text(c, x + w - 10 - text_width("GULF", 2), y + h - 30, "GULF",
              (220, 230, 235), 2)
    draw_text(c, x + 10, y + h - 30, "STRAIT OF HORMUZ", (255, 255, 255), 2)


def draw_lead(c):
    x, y, w, h = 24, 130, 976, 282
    c.fill_rect(x, y, w, h, CARD)
    c.rect(x, y, w, h, (200, 196, 184))
    c.fill_rect(x, y, 8, h, RED)
    tx = x + 28
    draw_text(c, tx, y + 16, news.LEAD["kicker"], RED, 2)
    yy = y + 44
    for line in news.LEAD["headline"]:
        draw_text(c, tx, yy, line, INK, 4)
        yy += 34
    yy += 6
    for line in news.LEAD["body"]:
        draw_text(c, tx, yy, line[:48], (52, 52, 52), 2)
        yy += 20
    draw_lead_scene(c, 668, y + 16, 308, h - 32)


def draw_icon(c, kind, x, y, s):
    """Small geometric icon, drawn in a s x s box at (x, y)."""
    if kind == "flags":
        for i, col in enumerate(((178, 34, 34), (31, 58, 95), (30, 90, 48))):
            px = x + i * (s // 3)
            c.fill_rect(px + 6, y + 4, 2, s - 8, STEEL)
            c.fill_rect(px + 8, y + 4, s // 3 - 4, 12, col)
    elif kind == "probe":
        c.circle(x + s // 2, y + s // 2, s // 4, GOLD)
        c.ring(x + s // 2, y + s // 2, s // 3, (180, 180, 170), 2)
        c.line(x + s // 2, y + s // 2 - s // 4, x + s - 2, y + 2, (120, 120, 110), 2)
        c.circle(x + s - 4, y + 4, 3, (120, 120, 110))
        c.circle(x + 4, y + s - 6, 2, (200, 200, 190))
        c.circle(x + s - 8, y + s - 4, 2, (200, 200, 190))
    elif kind == "virus":
        c.circle(x + s // 2, y + s // 2, s // 4, (178, 34, 34))
        for i in range(8):
            import math
            a = 2 * math.pi * i / 8
            c.line(x + s // 2, y + s // 2,
                   x + s // 2 + int((s // 2 - 2) * math.cos(a)),
                   y + s // 2 + int((s // 2 - 2) * math.sin(a)),
                   (178, 34, 34), 2)
        c.circle(x + s // 2 - 4, y + s // 2 - 4, 3, (255, 255, 255))
    elif kind == "chip":
        c.fill_rect(x + 8, y + 8, s - 16, s - 16, (30, 90, 48))
        c.fill_rect(x + 14, y + 14, s - 28, s - 28, (247, 243, 234))
        c.fill_rect(x + 18, y + 18, s - 36, s - 36, (30, 90, 48))
        for i in range(4):
            px = x + 12 + i * (s - 24) // 3
            c.fill_rect(px, y + 2, 3, 6, (30, 90, 48))
            c.fill_rect(px, y + s - 8, 3, 6, (30, 90, 48))
    elif kind == "storm":
        for r in (6, 12, 18):
            c.ring(x + s // 2, y + s // 2, r, (14, 94, 110), 3)
        c.circle(x + s // 2, y + s // 2, 4, (14, 94, 110))
        c.line(x + s // 2, y + s // 2, x + s - 2, y + s // 2, (14, 94, 110), 2)
    elif kind == "bridge":
        c.line(x + 2, y + s - 10, x + s // 2, y + 8, STEEL, 3)
        c.line(x + s // 2, y + 8, x + s - 2, y + s - 10, STEEL, 3)
        c.line(x + 2, y + s - 10, x + s - 2, y + s - 10, STEEL, 3)
        c.burst(x + s // 2, y + 8, 10, (255, 120, 20), 8)


def draw_panel(c, panel, x, y, w, h):
    c.fill_rect(x, y, w, h, CARD)
    c.rect(x, y, w, h, (200, 196, 184))
    c.fill_rect(x, y, w, 26, panel["colour"])
    draw_text(c, x + 10, y + 6, panel["kicker"], (255, 255, 255), 2)
    draw_icon(c, panel["icon"], x + w - 46, y + 32, 36)
    yy = y + 36
    for line in panel["headline"]:
        draw_text(c, x + 10, yy, line, INK, 2)
        yy += 19
    yy += 4
    for line in panel["body"]:
        draw_text(c, x + 10, yy, line[:25], (52, 52, 52), 2)
        yy += 19


def draw_ticker(c):
    x, y, w, h = 24, 812, 976, 116
    c.fill_rect(x, y, w, h, NAVY)
    draw_text(c, x + 14, y + 12, news.TICKER_HEAD, GOLD, 2)
    items = "  -  ".join(news.TICKER)
    lines = wrap(items, 78)
    yy = y + 40
    for line in lines[:4]:
        draw_text(c, x + 14, yy, line, (235, 235, 230), 2)
        yy += 20


def draw_footer(c):
    draw_text_centred(c, W // 2, 936, news.FOOTER_SOURCES, MUTED, 2)
    draw_text_centred(c, W // 2, 962, news.FOOTER_CREDIT, MUTED, 2)
    c.fill_rect(24, 996, W - 48, 2, GOLD)


def render():
    c = Canvas(W, H, PAPER)
    draw_masthead(c)
    draw_lead(c)
    xs = (24, 362, 700)
    ys = (424, 618)
    for i, panel in enumerate(news.PANELS):
        draw_panel(c, panel, xs[i % 3], ys[i // 3], 326, 182)
    draw_ticker(c)
    draw_footer(c)
    return encode_png(c)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = render()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
