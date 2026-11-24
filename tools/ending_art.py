"""Original pixel art for the ending: dawn over the ridge, seen from the radio room.

The scene is drawn at 128 × 44 art pixels, doubled to 256 × 88 on screen. The
key light is the window on the left: lit faces point up and left, and each
material keeps two or three tones. The radio adds a cool rim light from the
right. Animated parts are separate drawings of the same cells.
"""

from math import pi, sin

from title_art import Scene, pack_scanline

ROWS, COLS = 11, 32
BLACK, GREEN, LIME, NAVY, BLUE, MAROON, CYAN, RED, ROSE = 1, 2, 3, 4, 5, 6, 7, 8, 9
OCHRE, AMBER, PINE, MAGENTA, GREY, WHITE = 10, 11, 12, 13, 14, 15
DAWN_LEVELS = 3                    # night, dawn, sunrise
WAVE_FRAMES = 4


def dither(x, y, a, b, level):
    """Ordered 2 × 2 dither from colour a (level 0) to b (level 4)."""
    return b if (0, 2, 3, 1)[(x & 1) + 2 * (y & 1)] < level else a


def bevel(art, x, y, w, h, light, mid, dark):
    """A box lit from the upper left."""
    art.rect(x, y, w, h, mid)
    art.rect(x, y, w, 1, light)
    art.rect(x, y, 1, h, light)
    art.rect(x, y + h - 1, w, 1, dark)
    art.rect(x + w - 1, y, 1, h, dark)


def knob(art, x, y):
    art.rect(x, y, 3, 3, BLUE)
    art.pixel(x, y, WHITE)
    art.pixel(x + 1, y, GREY)
    art.pixel(x, y + 1, GREY)
    art.pixel(x + 2, y + 2, NAVY)
    art.pixel(x + 1, y + 2, NAVY)
    art.pixel(x + 1, y + 1, BLACK)


SKY = (                             # top, middle, horizon, far ridge, rim light
    (BLACK, BLACK, NAVY, NAVY, BLUE),
    (NAVY, MAGENTA, ROSE, MAROON, ROSE),
    (BLUE, ROSE, AMBER, MAROON, AMBER),
)


def sky(art, dawn, beacon):
    """The window: sky, stars or sun, two ridges and the mast with its beacon."""
    left, top, right, bottom = 5, 4, 43, 28
    *bands, far, rim = SKY[dawn]
    # Bands follow tile rows, so each band repeats one tile across the window.
    for y in range(top, bottom):
        index = min((y - top) // 8, 2)
        seam = (y - top) % 8 == 7 and index < 2
        for x in range(left, right):
            art.pixel(x, y, dither(x, y, bands[index], bands[index + 1], 2) if seam else bands[index])
    if dawn == 0:
        for x, y in ((8, 5), (13, 9), (21, 4), (28, 6), (38, 4), (11, 12), (40, 10)):
            art.pixel(x, y, WHITE if x % 3 else GREY)
        # Crescent moon.
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                inside = dx * dx + dy * dy <= 10
                shadow = (dx + 1.5) ** 2 + (dy - 0.5) ** 2 <= 7
                if inside and not shadow:
                    art.pixel(33 + dx, 8 + dy, WHITE if dx > 0 else AMBER)
    elif dawn == 2:
        for dy in range(-5, 1):
            for dx in range(-6, 7):
                distance = dx * dx + 2 * dy * dy
                if distance <= 36:
                    art.pixel(32 + dx, 17 + dy, WHITE if distance < 14 else AMBER)
    far_ridge = [(5, 19), (10, 16), (15, 18), (21, 15), (27, 18), (32, 16), (37, 18), (43, 16)]
    art.shape(far_ridge + [(43, 27), (5, 27)], far)
    for (x1, y1), (x2, y2) in zip(far_ridge, far_ridge[1:]):
        if y2 < y1:
            art.line(x1, y1, x2, y2, rim)
    ridge = [(5, 23), (9, 21), (14, 22), (19, 19), (24, 21), (29, 20), (35, 23), (43, 21)]
    art.shape(ridge + [(43, 27), (5, 27)], BLACK)
    for (x1, y1), (x2, y2) in zip(ridge, ridge[1:]):
        if y2 < y1:
            art.line(x1, y1, x2, y2, rim)
    # Lattice mast on the near ridge, a silhouette against the brightening sky.
    lit, body = (GREY, NAVY) if dawn == 0 else (rim, BLACK)
    art.line(14, 8, 14, 19, body)
    art.line(13, 10, 13, 19, lit)
    art.line(15, 10, 15, 19, body)
    for y in range(11, 19, 2):
        art.line(12, y, 16, y, body)
        art.pixel(12, y, lit)
    art.pixel(14, 7, (MAROON, RED)[beacon])
    if beacon:
        art.pixel(13, 7, ROSE)
        art.pixel(15, 7, ROSE)
        art.pixel(14, 6, WHITE)


def window(art):
    """Frame around the sky, with a lit sill."""
    bevel(art, 3, 2, 42, 28, GREY, BLUE, NAVY)
    art.rect(4, 28, 40, 1, WHITE)


def mullion(art):
    art.rect(24, 4, 1, 24, BLUE)
    art.rect(25, 4, 1, 24, NAVY)


def radio(art, wave, tx, rx):
    """The transceiver: oscilloscope, frequency readout, speaker and knobs."""
    art.line(120, 0, 120, 6, GREY)
    art.pixel(119, 0, WHITE)
    art.line(121, 1, 121, 6, NAVY)
    bevel(art, 76, 6, 51, 24, GREY, BLUE, NAVY)
    art.rect(77, 7, 49, 1, WHITE)
    art.rect(76, 29, 51, 1, BLACK)
    # Oscilloscope with a green phosphor trace and a graticule.
    bevel(art, 79, 9, 26, 15, NAVY, BLACK, GREY)
    for x in range(80, 104, 4):
        for y in range(11, 22, 2):
            art.pixel(x, y, PINE)
    for x in range(80, 104):
        if wave is None:
            art.pixel(x, 16, GREEN)
            continue
        envelope = 0.55 + 0.45 * sin((x + wave * 3) / 5)
        offset = round(4 * envelope * sin((x * 2 + wave * 6) / 24 * 2 * pi))
        art.pixel(x, 16 + offset, LIME)
        if offset:
            art.pixel(x, 16 + offset - (offset > 0) + (offset < 0), GREEN)
    # Frequency readout: red segments behind dark glass.
    bevel(art, 108, 9, 16, 6, NAVY, BLACK, GREY)
    for i, shape in enumerate(((1, 1, 1), (1, 0, 1), (1, 1, 1))):
        x = 110 + i * 4
        art.rect(x, 11, 3, 1, RED)
        art.rect(x + 2, 11, 1, 3, RED)
        if shape[1]:
            art.rect(x, 12, 1, 2, MAROON)
    art.pixel(121, 13, RED)
    # Speaker grille.
    bevel(art, 108, 17, 16, 7, NAVY, BLUE, GREY)
    for y in range(18, 23, 2):
        for x in range(109 + y % 4 // 2, 123, 2):
            art.pixel(x, y, NAVY)
    # Lamps and knobs on the lower strip.
    art.rect(80, 25, 3, 2, RED if tx else MAROON)
    art.pixel(80, 25, ROSE if tx else RED)
    art.rect(84, 25, 3, 2, LIME if rx else PINE)
    art.pixel(84, 25, WHITE if rx else GREEN)
    for x in (92, 98, 110, 116):
        knob(art, x, 25)
    art.rect(103, 25, 4, 2, BLACK)
    art.rect(104, 25, 2, 1, AMBER)


def desk(art):
    art.rect(40, 30, 88, 1, WHITE)
    art.rect(40, 31, 88, 2, GREY)
    art.rect(40, 33, 88, 11, NAVY)
    for x in range(40, 128):
        art.pixel(x, 33, BLUE if x % 2 else NAVY)
    for x in (56, 92, 126):
        art.rect(x, 34, 1, 10, BLACK)
    for x in (74, 109):
        art.rect(x - 3, 37, 7, 1, GREY)
        art.rect(x - 3, 38, 7, 1, BLACK)
    # Logbook and pencil.
    art.rect(62, 28, 11, 2, WHITE)
    art.rect(62, 29, 11, 1, GREY)
    art.line(64, 28, 70, 28, GREY)
    art.line(73, 27, 75, 29, AMBER)


# Hand-placed pixels. Light comes from the window on the left, so the back of
# the suit and the top of the hair catch it. The radio adds a cyan rim in front.
INK = {"K": BLACK, "N": NAVY, "B": BLUE, "G": GREY, "W": WHITE, "M": MAROON,
       "R": RED, "P": ROSE, "O": OCHRE, "A": AMBER, "C": CYAN}
OPERATOR = (
    "..............GGGG..............",
    ".............GWGGGG.............",
    "............GKKKKKKG............",
    "...........NKNKKKKKKP...........",
    "..........NBNKKKKKPPPP..........",
    "..........NBNKKKPPPPKPP.........",
    "..........NNNKMPPPPPPPP..GG.....",
    "...........NKMPPPPPPP...GWGG....",
    "............MMPPPPPPMP..GGGN....",
    ".............MMPPPPPM...PPPN....",
    "..............MMMMMM...PPPP.....",
    "..NNNB......AAAOOOO.....OOO.....",
    "..NBBBN...AAAAAAOOOOO...OOO.....",
    "..NBBBN..AAAAAAAAOOOOO..OOO.....",
    "..NBBNN..AAAAAAAAOOOOOOOOOC.....",
    "..NBBNN.AAAAAAAAAOOOOOOOOOC.....",
    "..NBBNN.AAAAAAAAAOOOOMOOOC......",
    "..NBBNN.AAAAAAAAAOOOOOMMM.......",
    "..NBBNN.AAAAAAAAAOOOOOOC........",
    "..NBBNN.AAAAAAAAAOOOOOOC........",
    "..NBBNN.AAAAAAAAOOOOOOOC........",
    "..NBBNN.AAAAAAAAOOOOOOOC........",
    "..NBBNN.MAAAAAAAOOOOOOOOAAAAA...",
    "..NBBNN.MMAAAAAAAAAAAAAAAAAAAAA.",
    "..NBBBBBBMMOOOOOOOOOOOOOOOOOOOM.",
    "..NNBBBBBBBBBBBBBBBNMMMMMMMMMM..",
    "...NNNNNNNNNNNNNNNNN............",
    "...........GB...................",
    "...........GB...................",
    "...........GB...................",
    "...........GB...................",
    "....GGGGGGGGGGGGGGGGG...........",
    "....KG.....KG......KG...........",
)
MOUTH = (20, 8)                     # lips that part while the operator talks


def operator(art, talking):
    left, top = 42, 8
    for y, row in enumerate(OPERATOR):
        for x, key in enumerate(row):
            if key != ".":
                art.pixel(left + x, top + y, INK[key])
    if talking:
        art.pixel(left + MOUTH[0], top + MOUTH[1], BLACK)
        art.pixel(left + MOUTH[0], top + MOUTH[1] + 1, BLACK)
    # Coiled cord from the microphone to the radio.
    for i, x in enumerate(range(left + 28, 77)):
        art.pixel(x, top + 9 + i // 2 + (i % 2), GREY if i % 2 else NAVY)


def floor(art):
    """The floor under the window fades from the light into the room's shadow."""
    art.rect(0, 38, 44, 1, BLUE)
    for y, level in zip(range(39, 43), (4, 2, 1, 0)):
        for x in range(0, 128):
            art.pixel(x, y, dither(x, y, BLACK, NAVY, level))


def room(dawn=0, beacon=False, wave=None, tx=False, rx=False, talking=False):
    art = Scene()
    floor(art)
    window(art)
    sky(art, dawn, beacon)
    mullion(art)
    radio(art, wave, tx, rx)
    desk(art)
    operator(art, talking)
    return [row[:COLS * 4] for row in art.pixels[:ROWS * 4]]


def tile_at(pixels, row, col):
    """Four stored scanlines; the cartridge draws each one twice."""
    return tuple(pack_scanline([pixel for pixel in pixels[row * 4 + y][col * 4:col * 4 + 4]
                                for _ in range(2)]) for y in range(4))


BLANK = ((0, 0x11),) * 4
# Each channel redraws some cells; the cartridge picks one frame per channel.
CHANNELS = (
    ("sky", [dict(dawn=level) for level in range(DAWN_LEVELS)]),
    # The beacon only owns the cells its light changes at each dawn level.
    ("beacon", [dict(dawn=level, beacon=blink) for level in range(DAWN_LEVELS) for blink in (False, True)]),
    ("wave", [dict(wave=None)] + [dict(wave=phase) for phase in range(WAVE_FRAMES)]),
    ("lamps", [dict(), dict(tx=True), dict(rx=True)]),
    ("mouth", [dict(), dict(talking=True)]),
)


def scene():
    """Tiles per bank, the base name table and the animation channels.

    Rows 0–7 use the upper bank; rows 8–10 use the middle bank, which also
    holds the font. Names are local to each bank.
    """
    banks = [{BLANK: 0}, {BLANK: 0}]

    def name(row, tile):
        bank = banks[row // 8]
        return bank.setdefault(tile, len(bank))

    def grid(**options):
        pixels = room(**options)
        return [[tile_at(pixels, row, col) for col in range(COLS)] for row in range(ROWS)]

    base = grid()
    names = [[name(row, tile) for tile in line] for row, line in enumerate(base)]
    channels, owner = [], {}
    for label, frames in CHANNELS:
        grids = [grid(**options) for options in frames]
        references = [grid(**{key: value for key, value in options.items() if key != "beacon"})
                      if label == "beacon" else base for options in frames]
        cells = sorted({(row, col) for g, ref in zip(grids, references)
                        for row in range(ROWS) for col in range(COLS) if g[row][col] != ref[row][col]})
        if not cells:
            raise ValueError(f"A animação {label} não muda a arte.")
        for cell in cells:
            if owner.get(cell, label) not in (label, "sky"):
                raise ValueError(f"As animações {owner[cell]} e {label} disputam um tile.")
            owner[cell] = label
        channels.append((label, cells, [[name(row, g[row][col]) for row, col in cells] for g in grids]))
    return banks, names, channels
