"""Original pixel art for the Posto Umbra title, packed into SCREEN 2 tiles."""

from collections import Counter
from itertools import combinations


# TMS9918 palette. Index zero is reserved for transparency in the game.
PALETTE = (
    (0, 0, 0), (0, 0, 0), (33, 200, 66), (94, 220, 120),
    (84, 85, 237), (125, 118, 252), (212, 82, 77), (66, 235, 245),
    (252, 85, 84), (255, 121, 120), (212, 193, 84), (230, 206, 128),
    (33, 176, 59), (201, 91, 186), (204, 204, 204), (255, 255, 255),
)
DISTANCE = tuple(
    tuple(sum((a - b) ** 2 for a, b in zip(left, right)) for right in PALETTE)
    for left in PALETTE
)


class Scene:
    """Draw at 128 × 64, then double pixels for the VDP."""

    def __init__(self):
        self.pixels = [bytearray([1] * 128) for _ in range(64)]

    def pixel(self, x, y, color):
        if 0 <= x < 128 and 0 <= y < 64:
            self.pixels[y][x] = color

    def rect(self, x, y, w, h, color):
        for row in range(y, y + h):
            for col in range(x, x + w):
                self.pixel(col, row, color)

    def line(self, x, y, x2, y2, color):
        dx, dy = abs(x2 - x), -abs(y2 - y)
        sx, sy = (1 if x < x2 else -1), (1 if y < y2 else -1)
        error = dx + dy
        while True:
            self.pixel(x, y, color)
            if (x, y) == (x2, y2):
                return
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x += sx
            if doubled <= dx:
                error += dx
                y += sy

    def shape(self, points, color, fill=None):
        for y in range(min(y for _, y in points), max(y for _, y in points)):
            crossings = sorted(
                x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
                if min(y1, y2) <= y < max(y1, y2)
            )
            for left, right in zip(crossings[::2], crossings[1::2]):
                for x in range(round(left), round(right)):
                    self.pixel(x, y, color if fill is None else fill(x, y))

    def lettering(self, font, words, x, y, color):
        for char in words:
            if char != " ":
                for row, bits in enumerate(bytes.fromhex(font[char])):
                    for col in range(6):
                        if bits & (32 >> col):
                            self.pixel(x + col, y + row, color)
            x += 7


def outpost(font, phase):
    art = Scene()
    dark, blue, steel, weld, ember, amber = 1, 4, 5, 7, 6, 11

    # Twilight, a red moon, and two ridges behind the communications tower.
    for x, y in ((5, 21), (8, 18), (11, 30), (43, 20), (48, 16), (56, 23),
                 (60, 18), (68, 20), (74, 16), (83, 22), (92, 16), (116, 10), (121, 22)):
        art.pixel(x, y, steel if x % 3 else weld)
    for x, y, flash in ((53, 19, 1), (91, 19, 3)):
        art.pixel(x, y, weld if phase == flash else steel)
        if phase == flash:
            art.line(x - 1, y, x + 1, y, steel)
            art.pixel(x, y - 1, weld)
    for y in range(17, 41):
        for x in range(13, 42):
            if (x - 27) ** 2 + (y - 30) ** 2 <= 13 ** 2:
                color = 9 if y < 30 else 8
                if y > 26 and (x + 3 * y) % 7 < (y - 25) // 3:
                    color = ember
                art.pixel(x, y, color)
    for x, y, w in ((3, 28, 12), (14, 32, 18), (21, 35, 26), (1, 40, 40), (30, 38, 20)):
        art.rect(x, y, w, 1, dark)
        art.line(x, y + 1, x + w - 1, y + 1, ember)
    art.shape([(0, 43), (9, 39), (15, 41), (30, 34), (40, 40), (53, 30),
               (65, 41), (83, 35), (99, 40), (116, 28), (128, 38), (128, 52), (0, 53)],
              blue, lambda x, y: blue if (x + y) % 3 == 0 else dark)
    art.shape([(0, 47), (15, 44), (23, 39), (36, 46), (45, 43), (56, 39),
               (66, 46), (92, 42), (103, 38), (116, 44), (128, 41), (128, 64), (0, 64)], dark)

    # Route across the yard, with runway studs and puddles of light.
    art.shape([(69, 50), (91, 50), (111, 63), (51, 63)], blue,
              lambda x, y: blue if (x + 3 * y) % 5 <= 1 else dark)
    for x, y, length, color in ((65, 55, 29, blue), (57, 59, 42, blue), (50, 62, 61, blue),
                                (76, 54, 12, ember), (70, 57, 16, ember),
                                (80, 60, 12, ember), (64, 61, 10, 10), (78, 56, 4, 10)):
        art.rect(x, y, length, 1, color)
    for x, y in ((65, 54), (60, 57), (54, 61), (96, 54), (102, 58), (108, 62)):
        art.rect(x, y, 2, 1, amber)

    # Perimeter fence and pylons sit to the west of the entrance.
    art.line(0, 47, 48, 44, steel)
    art.line(0, 50, 48, 47, blue)
    for x, y in ((4, 46), (12, 45), (20, 45), (28, 44), (36, 43), (44, 43)):
        art.line(x, y, x, y + 9, blue)
        art.pixel(x, y, weld)
    art.rect(8, 43, 4, 2, steel)
    art.rect(9, 43, 2, 1, amber)
    art.rect(10, 45, 1, 9, blue)
    art.rect(32, 41, 4, 2, blue)
    art.rect(33, 41, 2, 1, amber)
    art.rect(34, 43, 1, 8, blue)

    # Angled blast walls. The turquoise steel frame encloses an amber airlock.
    art.shape([(42, 44), (50, 33), (111, 33), (124, 43), (124, 54), (42, 54)], blue)
    art.shape([(48, 38), (55, 28), (105, 28), (114, 37), (102, 41), (54, 41)], steel)
    art.line(55, 28, 105, 28, weld)
    art.line(50, 33, 55, 28, weld)
    art.line(54, 38, 112, 38, blue)
    art.shape([(49, 39), (62, 37), (102, 37), (117, 41), (117, 53), (49, 53)], blue,
              lambda x, y: blue if (x - y) % 7 < 4 else dark)
    art.line(43, 44, 48, 39, steel)
    art.line(43, 53, 63, 53, steel)
    art.line(101, 53, 123, 53, steel)
    art.rect(52, 42, 12, 1, steel)
    art.rect(102, 42, 13, 1, steel)
    for x in (53, 56, 59, 105, 108, 111):
        art.line(x, 46, x - 1, 49, dark)
    for x in (54, 61, 104, 112):
        art.pixel(x, 43, amber)

    art.shape([(63, 52), (63, 38), (69, 32), (96, 32), (102, 38), (102, 53)], dark)
    art.shape([(67, 53), (67, 39), (72, 35), (92, 35), (98, 40), (98, 53)], steel)
    art.line(72, 35, 92, 35, weld)
    art.line(67, 39, 67, 51, weld)
    art.line(97, 41, 97, 51, blue)
    art.shape([(71, 54), (71, 42), (75, 38), (90, 38), (94, 42), (94, 54)], dark)
    art.rect(75, 39, 15, 1, amber)
    art.rect(79, 39, 6, 1, (amber, 15, amber, 10)[phase])
    art.rect(74, 41, 1, 10, 10)
    art.rect(91, 41, 1, 10, ember)
    art.rect(76, 42, 13, 10, ember)
    art.rect(77, 43, 11, 8, dark)
    art.rect(78, 43, 1, 7, amber)
    art.rect(86, 43, 1, 7, 10)
    art.rect(80, 45, 5, 5, blue)
    art.rect(81, 47, 3, 2, (weld, 15, weld, steel)[phase])
    art.line(74, 52, 92, 52, 10)
    for x in (69, 96):
        art.rect(x, 45, 1, 3, amber)

    # A mast, dish, and light on the communications wing.
    art.rect(103, 25, 10, 4, blue)
    art.rect(106, 24, 6, 1, steel)
    art.line(109, 12, 109, 25, steel)
    art.line(110, 14, 110, 24, blue)
    art.line(104, 17, 114, 17, steel)
    art.line(106, 20, 113, 20, blue)
    art.line(109, 16, 119, 26, blue)
    art.pixel(109, 11, (9, 9, ember, dark)[phase])
    art.pixel(109, 10, (amber, amber, ember, dark)[phase])
    if phase == 1:
        art.pixel(108, 10, ember)
        art.pixel(110, 10, ember)
    art.shape([(108, 24), (114, 20), (120, 21), (115, 25)], steel)
    art.line(110, 24, 117, 21, weld)

    # Foreground rubble and a restrained cyan wordmark.
    art.shape([(0, 58), (6, 55), (17, 57), (27, 56), (42, 64), (0, 64)],
              blue, lambda x, y: blue if (x + 2 * y) % 5 == 0 else dark)
    art.shape([(115, 57), (121, 55), (128, 56), (128, 64), (108, 64)],
              blue, lambda x, y: blue if (2 * x + y) % 5 == 0 else dark)
    for x, y, w in ((8, 60, 7), (20, 62, 9), (114, 61, 6), (121, 58, 2)):
        art.rect(x, y, w, 1, steel)
    art.lettering(font, "POSTO UMBRA", 8, 5, weld)
    art.line(8, 14, 36, 14, blue)
    art.line(38, 14, 40, 14, weld)
    return art.pixels


def pack_scanline(pixels):
    counts = Counter(pixels)
    if len(counts) == 1:
        return 0, counts.most_common(1)[0][0]
    bg, fg = min(
        combinations(sorted(counts), 2),
        key=lambda pair: sum(count * min(DISTANCE[color][pair[0]], DISTANCE[color][pair[1]])
                             for color, count in counts.items()),
    )
    mask = sum(128 >> x for x, color in enumerate(pixels) if DISTANCE[color][fg] < DISTANCE[color][bg])
    return mask, fg << 4 | bg


def title_data(data, font):
    frames = [outpost(font, phase) for phase in range(4)]
    motion = [[] for _ in frames]
    layout = []
    sections = []
    for bank in range(2):
        ids, patterns, colors = {}, [], []
        for row in range(bank * 8, bank * 8 + 8):
            for col in range(32):
                tiles = [tuple(pack_scanline([
                    pixels[(row * 8 + y) // 2][(col * 8 + x) // 2] for x in range(8)
                ]) for y in range(8)) for pixels in frames]
                tile = tiles[0]
                changing = any(other != tile for other in tiles[1:])
                if changing or tile not in ids:
                    index = len(patterns) // 8
                    patterns.extend(pattern for pattern, _ in tile)
                    colors.extend(color for _, color in tile)
                    if changing:
                        for patch, phase_tile in zip(motion, tiles):
                            patch.extend((index, bank * 8))
                            patch.extend(pattern for pattern, _ in phase_tile)
                            patch.extend(color for _, color in phase_tile)
                    else:
                        ids[tile] = index
                else:
                    index = ids[tile]
                layout.append(index)
        sections.extend((
            f"title_bank_{bank}_size: equ {len(patterns)}",
            data(f"title_patterns_{bank}", patterns),
            data(f"title_colors_{bank}", colors),
        ))
    frame_labels = [f"title_motion_{phase}" for phase in range(len(frames))]
    return "\n".join((
        data("title_picture", layout), *sections,
        f"title_motion_tiles: equ {len(motion[0]) // 18}",
        data("title_motion_frames", frame_labels, "dw"),
        *(data(label, patches) for label, patches in zip(frame_labels, motion)),
    ))
