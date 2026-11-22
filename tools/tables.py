"""Generate the original map, camera and SCREEN 2 tiles at build time."""

from math import cos, pi, sin

WORLD = (
    "################",
    "##.......#######",
    "##........######",
    "##...E.....#####",
    "##.........#####",
    "#####D##########",
    "#..+...+.......#",
    "#..#...#...##..#",
    "#......+...##..#",
    "#..............#",
    "#..#+..#+......#",
    "#..#+..#+......#",
    "#..............#",
    "#.....#.....+..#",
    "#.....#.....+..#",
    "################",
)
RAY_LIMIT = 160
START = (5, 12)
MONSTER = (5, 8)
AMMO = (5, 11)
TERRAIN = (
    (".", "CHAO LIVRE", None),
    ("#", "PAREDE AZUL", (7, 4, 5)),
    ("+", "PAREDE AMARELA", (11, 6, 10)),
    ("D", "PORTA FECHADA", (13, 4, 15)),
)

# Each hex pair is a row of a handmade 5x7 glyph.
FONT = {
    "A": "0e11111f111111",
    "B": "1e11111e11111e",
    "C": "0e11101010110e",
    "D": "1e11111111111e",
    "E": "1f10101e10101f",
    "F": "1f10101e101010",
    "G": "0e11101711110e",
    "H": "1111111f111111",
    "I": "0e04040404040e",
    "J": "0702020212120c",
    "L": "1010101010101f",
    "M": "111b1515111111",
    "N": "11191915131311",
    "O": "0e11111111110e",
    "P": "1e11111e101010",
    "Q": "0e11111115120d",
    "R": "1e11111e141211",
    "S": "0f10100e01011e",
    "T": "1f040404040404",
    "U": "1111111111110e",
    "V": "11111111110a04",
    "X": "11110a040a1111",
    "Z": "1f01020408101f",
    "/": "01020204080810",
    "0": "0e11131519110e",
    "1": "040c040404040e",
    "7": "1f010204080808",
}

# Original monochrome masks. Each size is converted to SCREEN 2 tiles separately.
CREATURE = (
    "..##........##..",
    "..###......###..",
    "...##########...",
    "..############..",
    "..##..####..##..",
    "..############..",
    "...###.##.###...",
    "..############..",
    ".###.######.###.",
    "###..######..###",
    "##...######...##",
    ".....######.....",
    "....###..###....",
    "...###....###...",
    "...###....###...",
    "..####....####..",
)
SUPPLY = (
    "................",
    "................",
    "................",
    "................",
    "....########....",
    "...##########...",
    "..############..",
    "..###......###..",
    "..###.####.###..",
    "..###.####.###..",
    "..###......###..",
    "..############..",
    "..############..",
    "................",
    "................",
    "................",
)
BEACON = (
    ".......##.......",
    "......####......",
    ".....######.....",
    "....########....",
    "...###.##.###...",
    ".......##.......",
    ".......##.......",
    ".......##.......",
    ".......##.......",
    ".......##.......",
    ".......##.......",
    ".......##.......",
    "......####......",
    ".....######.....",
    "....########....",
    "................",
)
OBJECT_ART = (
    ("creature", "MONSTRO", CREATURE, 9),
    ("ammo", "MUNICAO", SUPPLY, 10),
    ("exit", "SAIDA", BEACON, 3),
)


def data(label, values, directive="db"):
    values = list(values)
    lines = [f"{label}:"]
    for start in range(0, len(values), 16):
        fields = ",".join(str(value) for value in values[start:start + 16])
        lines.append(f"    {directive} {fields}")
    return "\n".join(lines)


def panel_data(field, rows):
    """Encode sparse rows of text as destination offset, length and tile IDs."""
    blocks = []
    for row, column, tiles in rows:
        if not (0 <= row < 16 and 0 <= column <= 32 - len(tiles) and tiles):
            raise ValueError("Elemento do menu fora da tela.")
        offset = row * 32 + column
        blocks.extend((len(tiles), offset & 255, offset >> 8, *tiles))
    return data(field, (*blocks, 0))


def generate():
    terrain_chars = "".join(mark for mark, _, _ in TERRAIN)
    if (
        len(WORLD) != 16
        or any(len(row) != 16 or row[0] not in "#+" or row[-1] not in "#+" for row in WORLD)
        or set(WORLD[0] + WORLD[-1]) - set("#+")
        or any(WORLD[y][x] != "." for x, y in (START, MONSTER, AMMO))
        or set("".join(WORLD)) - set(terrain_chars + "E")
        or sum(row.count("D") for row in WORLD) != 1
        or sum(row.count("E") for row in WORLD) != 1
    ):
        raise ValueError("O mapa exige borda sólida, 16 × 16 células e início livre.")

    patterns, colors = bytearray(), bytearray()
    tile_ids = {}

    def tile(rows):
        rows = tuple(rows)
        if rows not in tile_ids:
            tile_ids[rows] = len(tile_ids)
            patterns.extend(pattern for pattern, _ in rows)
            colors.extend(color for _, color in rows)
        return tile_ids[rows]

    blank = tile([(0, 0x11)] * 8)
    stripe = tile([(0, 0x11)] * 6 + [(0, 0x77), (0, 0x11)])
    ceiling = [(0, 0x11)] * 8
    floor = [(0x22 if y % 2 else 0x88, 0x41) for y in range(8)]
    terrain_tiles = [tile(floor)]
    templates = []
    for _, _, (light, shade, trim) in TERRAIN[1:]:
        wall = [
            (0xFE if y == 0 else 0xBA if y == 1 else 0x7E, (light << 4) | shade)
            for y in range(8)
        ]
        wall[7] = (0x7E, (trim << 4) | shade)
        terrain_tiles.append(tile(wall))
        for half_height in range(65):
            for row in range(16):
                templates.append(tile(
                    wall[y] if 64 - half_height <= row * 8 + y < 64 + half_height
                    else ceiling[y] if row < 8 else floor[y]
                    for y in range(8)
                ))

    def label(text, accent):
        return [
            blank if char == " " else tile(
                [(row << 2, (accent << 4) | 1) for row in bytes.fromhex(FONT[char])]
                + [(0, 0x11)]
            )
            for char in text
        ]

    def object_tiles(mask, color, size):
        # Each tile is fully transparent when the corresponding mask area is empty.
        tiles = []
        pixels = size * 8
        for tx in range(size):
            for ty in range(size):
                rows = []
                for y in range(ty * 8, ty * 8 + 8):
                    source_y = (y * 16 + 8) // pixels
                    pattern = 0
                    for x in range(tx * 8, tx * 8 + 8):
                        source_x = (x * 16 + 8) // pixels
                        pattern = pattern * 2 + (mask[source_y][source_x] == "#")
                    rows.append((pattern, ((color if y % 4 else 15) << 4) | 1))
                tiles.append(tile(rows) if any(bits for bits, _ in rows) else 0)
        return tiles

    def object_art(mask, color):
        return [index for size in range(1, 5) for index in object_tiles(mask, color, size)]

    objects = [(kind, name, object_art(mask, color)) for kind, name, mask, color in OBJECT_ART]

    door_passage = tile([(0x81, 0xd1)] * 8)
    arrow = (
        "...##...",
        "..####..",
        ".######.",
        "...##...",
        "...##...",
        "...##...",
        "...##...",
        "........",
    )
    directions = []
    for _ in range(4):
        directions.append(tile([
            (int(row.replace(".", "0").replace("#", "1"), 2), 0xf1)
            for row in arrow
        ]))
        arrow = tuple("".join(row[x] for row in reversed(arrow)) for x in range(8))

    open_door_label = "PORTA ABERTA"
    markers = [("player", "VOCE", directions[0])]
    markers.extend((kind, name, art[0]) for kind, name, art in objects)
    terrain_legend = [(name, icon) for (_, name, _), icon in zip(TERRAIN, terrain_tiles)]
    terrain_legend.append((open_door_label, door_passage))

    def marker_row(name, icon):
        return [icon, blank, *label(name, 15)]

    legend_panel = panel_data("legend_panel", [
        (1, 2, label("LEGENDA", 7)),
        (3, 2, label("TERRENO", 11)),
        (3, 20, label("OBJETOS", 11)),
        *((5 + index * 2, 2, marker_row(name, icon))
          for index, (name, icon) in enumerate(terrain_legend)),
        *((5 + index * 2, 20, marker_row(name, icon))
          for index, (_, name, icon) in enumerate(markers)),
    ])
    map_panel = panel_data("map_panel", [
        (1, 20, label("MAPA", 7)),
        (3, 20, [directions[0], blank, *label("NORTE", 11)]),
        *((6 + index * 2, 20, marker_row(name, icon))
          for index, (_, name, icon) in enumerate(markers)),
    ])
    menu_hud = label(" ESQ LEGENDA DIR MAPA M VOLTAR ".ljust(32), 15)

    def screen_message(message, color):
        line = [blank] * 32
        start = (32 - len(message)) // 2
        line[start:start + len(message)] = label(message, color)
        return line

    defeat = screen_message("VOCE CAIU   ESP REINICIA", 9)
    victory = screen_message("SETOR SEGURO   ESP REINICIA", 3)
    chrome = [blank] * (24 * 32)

    def write_chrome(row, col, tiles):
        offset = row * 32 + col
        chrome[offset:offset + len(tiles)] = tiles

    write_chrome(1, 2, label("POSTO UMBRA", 7))
    write_chrome(1, 22, label("SETOR 07", 11))
    write_chrome(2, 2, [stripe] * 28)
    write_chrome(20, 2, [stripe] * 28)
    write_chrome(23, 2, label("ESP TIRO  SHIFT ABRIR  M MENU", 15))
    hud = label(" VIDA    MUN   ".ljust(32), 15)
    digits = [
        tile([(row << 2, 0xf1) for row in bytes.fromhex(glyph)] + [(0, 0x11)])
        for glyph in (
            "0e11131519110e", "040c040404040e", "0e11010204081f", "1e01010e01011e",
            "02060a121f0202", "1f10101e01011e", "0608101e11110e", "1f010204080808",
            "0e11110e11110e", "0e11110f01020c",
        )
    ]
    hints = (
        "ELIMINE O MONSTRO", "ABRA A PORTA", "ACHE A SAIDA", "PORTA TRANCADA",
        "SEM MUNICAO", "MUNICAO EXTRA",
    )
    hint_tiles = [
        index for message in hints for index in label(message[:17].ljust(17), 11)
    ]
    if len(tile_ids) > 256:
        raise ValueError("SCREEN 2 admite até 256 tiles por banco.")

    walk_vectors, ray_vectors, camera_vectors = [], [], []
    for heading in range(64):
        angle = heading * 2 * pi / 64
        forward_x, forward_y = sin(angle), -cos(angle)
        walk_vectors.extend((round(40 * forward_x), round(40 * forward_y)))
        camera_vectors.extend((round(64 * forward_x) & 255, round(-64 * forward_y) & 255))
        for column in range(32):
            camera_x = ((column + 0.5) / 16 - 1) * 0.65
            ray_vectors.extend((
                round(36 * (forward_x - forward_y * camera_x)) & 255,
                round(36 * (forward_y + forward_x * camera_x)) & 255,
            ))

    door_y, door_x = next((y, row.index("D")) for y, row in enumerate(WORLD) if "D" in row)
    exit_y, exit_x = next((y, row.index("E")) for y, row in enumerate(WORLD) if "E" in row)
    return "\n".join((
        data("tile_patterns", patterns),
        "tile_patterns_end:",
        data("tile_colors", colors),
        data("chrome", chrome),
        data("walk_vectors", walk_vectors, "dw"),
        data("ray_vectors", ray_vectors),
        data("camera_vectors", camera_vectors),
        "ray_limit: equ " + str(RAY_LIMIT),
        data("heights", (min(64, round(355 / n)) for n in range(1, RAY_LIMIT + 2))),
        data("wall_columns", templates),
        "    ds align 256",
        data("world_map", (terrain_chars.index(cell.replace("E", ".")) for row in WORLD for cell in row)),
        data("terrain_tiles", terrain_tiles),
        *(data(f"{kind}_tiles", art) for kind, _, art in objects),
        data("object_depths", (distance * 4 // 9 for distance in range(182))),
        data("object_offsets", (0, 1, 5, 14)),
        data("hud_template", hud),
        data("hud_digits", digits),
        data("hud_hints", hint_tiles),
        data("defeat_line", defeat),
        data("victory_line", victory),
        legend_panel,
        map_panel,
        data("menu_hud", menu_hud),
        data("map_arrows", directions),
        f"map_open_door: equ {door_passage}",
        *(f"map_{kind}: equ {icon}" for kind, _, icon in markers if kind != "player"),
        f"start_x: equ {START[0] * 256 + 128}",
        f"start_y: equ {START[1] * 256 + 128}",
        f"spawn_x: equ {MONSTER[0] * 256 + 128}",
        f"spawn_y: equ {MONSTER[1] * 256 + 128}",
        f"ammo_x: equ {AMMO[0] * 256 + 32}",
        f"ammo_y: equ {AMMO[1] * 256 + 128}",
        f"ammo_index: equ {AMMO[1] * 16 + AMMO[0]}",
        f"door_index: equ {door_y * 16 + door_x}",
        f"door_x: equ {door_x * 256 + 128}",
        f"door_y: equ {door_y * 256 + 128}",
        f"exit_x: equ {exit_x * 256 + 128}",
        f"exit_y: equ {exit_y * 256 + 128}",
        f"exit_index: equ {exit_y * 16 + exit_x}",
        "rom_end:",
        "",
    ))
