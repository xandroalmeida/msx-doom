"""Generate the original map, camera and SCREEN 2 tiles at build time."""

from math import cos, pi, sin

SECTORS = (
    (
        "################",
        "##.......#######",
        "##........######",
        "##...E.....#####",
        "##.........#####",
        "#####D##########",
        "#..+...+.......#",
        "#..#...#...##..#",
        "#....M.+...##..#",
        "#..............#",
        "#..#+..#+......#",
        "#..#+A.#+......#",
        "#....P.........#",
        "#.....#.....+..#",
        "#.....#.....+..#",
        "################",
    ),
    (
        "################",
        "#######.......##",
        "#######.......##",
        "#######...E...##",
        "#######.......##",
        "##########D#####",
        "#.....##.......#",
        "#..+...+..K....#",
        "#..M.....B.....#",
        "#..............#",
        "#....++.....++.#",
        "#..A.#....###..#",
        "#..P.#.........#",
        "#.....##.......#",
        "#..............#",
        "################",
    ),
    (
        "################",
        "##.....#########",
        "##..E..#########",
        "##.....#########",
        "####D###########",
        "#..............#",
        "#......##......#",
        "#...K..##......#",
        "#..+........+..#",
        "#....M.....B...#",
        "#..++.....+.+..#",
        "#......#.......#",
        "#......#...A...#",
        "#..........P...#",
        "#..............#",
        "################",
    ),
)
RAY_LIMIT = 160
MAX_LIFE = 5
TERRAIN = (
    (".", "CHAO LIVRE", None),
    ("#", "PAREDE AZUL", (4, 5, 7, 1)),
    ("+", "PAREDE AMARELA", (6, 10, 11, 1)),
    ("D", "PORTA FECHADA", None),
)

# Two staggered courses, with chipped mortar and a highlight along each stone.
# Each scanline uses two palette entries, as required by SCREEN 2.
STONE_ROWS = (
    (0b01111110, 2, 0),
    (0b00100001, 0, 1),
    (0b01001010, 2, 1),
    (0b01111100, 0, 3),
    (0b11100111, 1, 0),
    (0b11001111, 2, 1),
    (0b01010100, 0, 1),
    (0b11000111, 0, 3),
)
OFFSET_STONE_ROWS = (
    (0b11110011, 2, 0),
    (0b10001010, 0, 1),
    (0b01010001, 2, 1),
    (0b11100011, 0, 3),
    (0b00111110, 1, 0),
    (0b10011101, 2, 1),
    (0b01001000, 0, 1),
    (0b00111100, 0, 3),
)
CORNER_ROWS = (
    (0b11100110, 2, 3),
    (0b01100100, 1, 3),
    (0b00100110, 2, 3),
    (0b00100010, 0, 3),
    (0b11100111, 2, 3),
    (0b01100101, 1, 3),
    (0b10100100, 1, 3),
    (0b00100110, 0, 3),
)


def stone_rows(rows, palette):
    return tuple((mask, (palette[light] << 4) | palette[shade]) for mask, light, shade in rows)


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
BRUTE = (
    "....########....",
    "...##########...",
    "....##.##.##....",
    "....########....",
    "...####..####...",
    ".##############.",
    "################",
    "###.########.###",
    "###.########.###",
    "###.########.###",
    "##..########..##",
    "....###..###....",
    "....###..###....",
    "....###..###....",
    "...####..####...",
    "...####..####...",
)
KEY = (
    "................",
    "................",
    "....#####.......",
    "...#######......",
    "...##...##......",
    "...##...##......",
    "...#######......",
    "....##########..",
    "........######..",
    "..........##....",
    "..........##....",
    "................",
    "................",
    "................",
    "................",
    "................",
)
OBJECT_ART = (
    ("creature", "MONSTRO", CREATURE, 9),
    ("ammo", "MUNICAO", SUPPLY, 10),
    ("exit", "SAIDA", BEACON, 3),
    ("brute", "BRUTO", BRUTE, 13),
    ("key", "CHAVE", KEY, 11),
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


def level_data():
    def point(index, x_fraction=128):
        return (x_fraction, index & 15, 128, index >> 4)

    def reachable(world, start, door_open):
        reached = {start}
        frontier = [start]
        while frontier:
            current = frontier.pop()
            for neighbor in (current - 16, current + 16, current - 1, current + 1):
                if neighbor in reached or world[neighbor] in (("#", "+") if door_open else ("#", "+", "D")):
                    continue
                reached.add(neighbor)
                frontier.append(neighbor)
        return reached

    terrain = "".join(mark for mark, _, _ in TERRAIN)
    maps, records = [], []
    for index, rows in enumerate(SECTORS):
        world = "".join(rows)
        if (len(rows) != 16 or any(len(row) != 16 or row[0] not in "#+" or row[-1] not in "#+" for row in rows)
                or set(rows[0] + rows[-1]) - set("#+")
                or set(world) - set(terrain + "PMBAKE")
                or any(world.count(mark) != 1 for mark in ("PMABKDE" if index else "PMADE"))
                or (index == 0 and ("K" in world or "B" in world))):
            raise ValueError(f"Terreno ou marcadores inválidos no setor {index + 1}.")
        cells = {mark: world.index(mark) for mark in "PMBAKDE" if mark in world}
        before = reachable(world, cells["P"], door_open=False)
        after = reachable(world, cells["P"], door_open=True)
        if any(cell not in before for mark, cell in cells.items() if mark not in "DE") or (
            cells["E"] in before or cells["E"] not in after
        ):
            raise ValueError(f"Rota inválida no setor {index + 1}.")
        codes = [terrain.index(mark) if mark in terrain else 0 for mark in world]
        packed = [sum(codes[offset + i] << (6 - i * 2) for i in range(4))
                  for offset in range(0, 256, 4)]
        maps.append(data(f"sector_map_{index}", packed))
        brute = (3 if index == 1 else 4, *point(cells["B"]), 0) if index else (0,) * 6
        records.append("\n".join((
            f"sector_{index}:",
            f"    dw sector_map_{index}",
            "    db " + ",".join(str(value) for value in (
                *point(cells["P"]), 2, *point(cells["M"]), 0, *brute,
                *point(cells["D"]), *point(cells["E"]), *point(cells["A"], 32),
                *point(cells.get("K", 0)),              # unused when no key is required
                cells["D"], (2, 5, 6)[index], int(index != 0),
            )),
        )))
    pointers = data("sector_records", (f"sector_{i}" for i in range(len(SECTORS))), "dw")
    return "\n".join((f"sector_count: equ {len(SECTORS)}", pointers, *records, *maps))


def generate():
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
    # Transparent ground/ceiling pixels normally show the black backdrop.
    # When the player takes damage they show the red VDP backdrop instead.
    ceiling = [(0, 0x00)] * 8
    floor = [(0x22 if y % 2 else 0x88, 0x40) for y in range(8)]
    terrain_tiles = [tile(floor)]

    # Two-pixel clipping leaves room in the tile bank for both corner styles.
    heights = [min(64, 2 * round(355 / (2 * n))) for n in range(1, RAY_LIMIT + 2)]
    wall_heights = sorted(set(heights))
    templates = []
    door = [(0xFE, 0xD4), (0xBA, 0xD4)] + [(0x7E, 0xD4)] * 5 + [(0x7E, 0xF4)]
    stone_palettes = [palette for _, _, palette in TERRAIN if palette is not None]
    walls = [
        (stone_rows(STONE_ROWS, palette), stone_rows(OFFSET_STONE_ROWS, palette), palette, 0xFF)
        for palette in stone_palettes
    ]
    walls.append((door, None, None, 0))
    corners = [(stone_rows(CORNER_ROWS, palette), None, palette, 0xE7) for palette in stone_palettes]
    terrain_tiles.extend(tile(wall) for wall, _, _, _ in walls)
    for wall, alternate, palette, rim in walls + corners:
        for half_height in wall_heights:
            top, bottom = 64 - half_height, 64 + half_height - 1
            column = ceiling * 8 + floor * 8
            column[top:bottom + 1] = [wall[y % 8] for y in range(top, bottom + 1)]
            if palette is not None and half_height < 64:
                shade, _, light, grout = palette
                column[top] = (rim, (light << 4) | grout)
                column[bottom] = (rim, (shade << 4) | grout)
            for y in range(0, 128, 8):
                rows = column[y:y + 8]
                if alternate and y % 16 and top < y and y + 7 < bottom:
                    rows = alternate
                templates.append(tile(rows))

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
        *((5 + index * 2, 20, marker_row(name, icon))
          for index, (_, name, icon) in enumerate(markers)),
    ])
    menu_hud = label(" ESQ LEGENDA DIR MAPA M VOLTAR ".ljust(32), 15)

    def story_panel(field, title, detail, action, accent=7):
        return panel_data(field, [
            (3, (32 - len(title)) // 2, label(title, accent)),
            (7, (32 - len(detail)) // 2, label(detail, 15)),
            (12, (32 - len(action)) // 2, label(action, 11)),
        ])

    campaign_panels = (
        story_panel("death_panel", "VOCE CAIU", "O SETOR AINDA ESTA TOMADO", "ESP TENTAR DE NOVO", 9),
        story_panel("clear_panel", "SETOR SEGURO", "A ROTA ESTA LIVRE", "ESP PROXIMO SETOR", 7),
        story_panel("last_panel", "POSTO RECUPERADO", "CAMPANHA CONCLUIDA", "ESP VOLTAR AO INICIO", 7),
        story_panel("title_panel", "POSTO UMBRA", "SINAL DE UMBRA", "ESP INICIAR CAMPANHA", 7),
    )
    chrome = [blank] * (24 * 32)

    def write_chrome(row, col, tiles):
        offset = row * 32 + col
        chrome[offset:offset + len(tiles)] = tiles

    write_chrome(1, 2, label("POSTO UMBRA", 7))
    write_chrome(1, 22, label("SETOR 01", 11))
    write_chrome(2, 2, [stripe] * 28)
    write_chrome(20, 2, [stripe] * 28)
    write_chrome(23, 2, label("ESP TIRO  SHIFT ABRIR  M MENU", 15))
    meter_idle = tile([(bits, 0x41) for bits in (0, 0, 0, 0x7e, 0x7e, 0, 0, 0)])
    meter_active = tile([(bits, 0x71) for bits in (0, 0, 0x7e, 0x7e, 0x7e, 0x7e, 0, 0)])
    heart_full = tile([(bits, 0x91) for bits in (0, 0x66, 0xff, 0xff, 0x7e, 0x3c, 0x18, 0)])
    heart_empty = tile([(bits, 0xe1) for bits in (0, 0x66, 0x99, 0x81, 0x42, 0x24, 0x18, 0)])
    life_label = label(" VIDA ", 15)
    hud = life_label + [heart_full] * MAX_LIFE + label(" MUN ", 15)
    ammo_offset = len(hud)
    hint_offset = ammo_offset + 3
    hint_width = 32 - hint_offset
    hud.extend([blank] * (32 - len(hud)))
    weapons = label("PISTOLAPULSO  ", 7)
    digits = [
        tile([(row << 2, 0xf1) for row in bytes.fromhex(glyph)] + [(0, 0x11)])
        for glyph in (
            "0e11131519110e", "040c040404040e", "0e11010204081f", "1e01010e01011e",
            "02060a121f0202", "1f10101e01011e", "0608101e11110e", "1f010204080808",
            "0e11110e11110e", "0e11110f01020c",
        )
    ]
    hints = (
        "DERROTE TODOS", "ABRA A PORTA", "ACHE A SAIDA", "PORTA SELADA",
        "SEM MUNICAO", "MUNICAO EXTRA", "ACHE A CHAVE",
    )
    if any(len(message) > hint_width for message in hints):
        raise ValueError("Mensagem de objetivo excede a largura disponível no HUD.")
    hint_labels = [f"hud_hint_{index}" for index in range(len(hints))]
    hint_rows = [data(name, label(message.ljust(hint_width), 11)) for name, message in zip(hint_labels, hints)]
    if len(tile_ids) > 256:
        raise ValueError("SCREEN 2 admite até 256 tiles por banco.")

    walk_vectors, ray_vectors, camera_vectors = [], [], []
    for heading in range(64):
        angle = heading * 2 * pi / 64
        forward_x, forward_y = sin(angle), -cos(angle)
        walk_vectors.extend((round(40 * forward_x), round(40 * forward_y)))
        camera_vectors.extend((round(64 * forward_x) & 255, round(-64 * forward_y) & 255))
        for column in range(32 if heading < 16 else 0):
            camera_x = ((column + 0.5) / 16 - 1) * 0.65
            ray_vectors.extend((
                round(36 * (forward_x - forward_y * camera_x)) & 255,
                round(36 * (forward_y + forward_x * camera_x)) & 255,
            ))

    return "\n".join((
        data("tile_patterns", patterns),
        "tile_patterns_end:",
        data("tile_colors", colors),
        data("chrome", chrome),
        data("walk_vectors", walk_vectors, "dw"),
        data("ray_vectors", ray_vectors),
        data("camera_vectors", camera_vectors),
        "ray_limit: equ " + str(RAY_LIMIT),
        data("heights", (wall_heights.index(height) for height in heights)),
        data("wall_columns", templates),
        "    ds align 256",
        data("terrain_tiles", terrain_tiles),
        # Index by material plus 4 for a corner. Doors use the same style in both cases.
        data("wall_styles", (i * len(wall_heights) for i in (0, 0, 1, 2, 0, 3, 4, 2))),
        *(data(f"{kind}_tiles", art) for kind, _, art in objects),
        data("object_depths", (distance * 4 // 9 for distance in range(182))),
        data("object_offsets", (0, 1, 5, 14)),
        data("hud_template", hud),
        f"max_life: equ {MAX_LIFE}",
        f"hud_life_offset: equ {len(life_label)}",
        f"hud_ammo_offset: equ {ammo_offset}",
        f"hud_hint_offset: equ {hint_offset}",
        f"hud_hint_width: equ {hint_width}",
        data("hud_hearts", (heart_empty, heart_full)),
        data("weapon_names", weapons),
        data("hud_digits", digits),
        data("hud_hint_addresses", hint_labels, "dw"),
        *hint_rows,
        *campaign_panels,
        data("campaign_panels", ("death_panel", "clear_panel", "last_panel", "title_panel"), "dw"),
        legend_panel,
        map_panel,
        data("menu_hud", menu_hud),
        data("map_arrows", directions),
        f"map_open_door: equ {door_passage}",
        *(f"map_{kind}: equ {icon}" for kind, _, icon in markers if kind != "player"),
        level_data(),
        f"intro_meter_idle: equ {meter_idle}",
        f"intro_meter_active: equ {meter_active}",
        "",
    ))
