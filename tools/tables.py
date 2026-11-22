"""Generate the original map, camera and SCREEN 2 tiles at build time."""

from itertools import groupby
from math import cos, pi, sin

from levels import HEIGHT, sector_data

RAY_LIMIT = 224
WALL_PROJECTION = 460
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
    (0b01101110, 1, 0),
    (0b00100100, 0, 1),
    (0b00101010, 1, 0),
    (0b01110100, 0, 3),
    (0b11010111, 1, 0),
    (0b11000101, 1, 0),
    (0b01101000, 0, 1),
    (0b11010111, 0, 3),
)


def stone_rows(rows, palette):
    return tuple((mask, (palette[light] << 4) | palette[shade]) for mask, light, shade in rows)


# Umbra's six-pixel terminal font. Beveled corners and heavy stems read on CRT.
# Each hex pair encodes one scanline.
FONT = {
    "A": "0c1e33333f3333",
    "B": "3c36363e33333e",
    "C": "1f30303030301f",
    "D": "3c36333333363c",
    "E": "3f30303c30303f",
    "F": "3f30303c303030",
    "G": "1f30303733331f",
    "H": "3333333f333333",
    "I": "1e0c0c0c0c0c1e",
    "J": "0f06060636361c",
    "L": "3030303030303f",
    "M": "21333f2d212121",
    "N": "31393135273323",
    "O": "1e33333333331e",
    "P": "3e33333e303030",
    "Q": "1e333333352e17",
    "R": "3e33333e3c3633",
    "S": "1f30301e03033e",
    "T": "3f0c0c0c0c0c0c",
    "U": "3333333333331e",
    "V": "333333331e0c0c",
    "X": "33331e0c1e3333",
    "Z": "3f03060c18303f",
    "0": "1e33373b33331e",
    "1": "0c1c0c0c0c0c1e",
    "2": "1e3303060c183f",
    "3": "3e03031e03033e",
    "4": "060e1e363f0606",
    "5": "3f30303e03033e",
    "6": "1f30303e33331e",
    "7": "3f03060c181818",
    "8": "1e33331e33331e",
    "9": "1e33331f03033e",
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
        if not (0 <= row < 20 and 0 <= column <= 32 - len(tiles) and tiles):
            raise ValueError("Elemento do menu fora da tela.")
        offset = row * 32 + column
        blocks.extend((len(tiles), offset & 255, offset >> 8, *tiles))
    return data(field, (*blocks, 0))


def sloped_caps(heights, walls, palettes, ceiling, floor, used_tiles):
    """Assign sloped wall caps to tile IDs unused in their SCREEN 2 banks."""
    available = [iter(sorted(set(range(256)) - used)) for used in used_tiles]
    art, uploads, lookup = bytearray(), [], []

    def place(rows, outside_bank):
        art.extend(pattern for pattern, _ in rows)
        art.extend(color for _, color in rows)
        indices = []
        for bank in (1, outside_bank):
            index = next(available[bank], None)
            if index is None:
                raise ValueError(f"Sem tiles livres para as bordas no banco {bank}.")
            uploads.append(index)
            indices.append(index)
        return indices

    for rise in (2, 4):
        for material, ((wall, _, _, _), (shade, mid, _, _)) in enumerate(zip(walls, palettes)):
            for side in range(2):
                middle, outside = [], []
                for clip in range(0, 8, 2):
                    if clip + rise > 8:
                        offset = material * 32 + side * 16 + clip
                        middle.extend(lookup[offset:offset + 2])
                        outside.extend(lookup[offset + 8:offset + 10])
                        continue
                    # Color zero outside the wall shows the game backdrop and damage flash.
                    widths = (3, 6) if rise == 2 else (2, 4, 6, 7)
                    masks = [(1 << width) - 1 if side == 0 else 0xFF << (8 - width) & 0xFF
                             for width in widths]
                    upper_edge = [(mask, (mid if i % 2 == 0 else shade) << 4)
                                  for i, mask in enumerate(masks)]
                    lower_edge = [(mask, (mid if i % 2 == 0 else shade) << 4)
                                  for i, mask in enumerate(reversed(masks))]
                    upper = ceiling[:clip] + upper_edge + list(wall[clip + rise:])
                    bottom = list(wall[:8 - clip - rise]) + lower_edge + floor[8 - clip:]
                    top_ids, bottom_ids = place(upper, 0), place(bottom, 2)
                    middle.extend((top_ids[0], bottom_ids[0]))
                    outside.extend((top_ids[1], bottom_ids[1]))
                lookup.extend(middle + outside)

    tops = [64 - height for height in heights]
    return (
        f"wall_height_count: equ {len(heights)}",
        f"slope_tile_count: equ {len(uploads) // 2}",
        data("slope_sizes", heights),
        data("slope_profiles", (
            (top // 8 << 4) | (8 if top < 32 else 0) | (top & 7) for top in tops
        )),
        data("slope_tiles", lookup),
        data("slope_art", art),
        data("slope_uploads", uploads),
    )


def pack_wall_columns(tiles, height_count):
    # One RAM page per height. A high-bit token denotes repeated tile names.
    if height_count > HEIGHT - 2 or max(tiles) >= 128:
        raise ValueError("As colunas de parede excedem o espaço reservado.")
    for height in range(height_count):
        row = (tiles[style * height_count * 16 + height * 16 + y]
               for style in range(5) for y in range(16))
        for tile_id, group in groupby(row):
            length = sum(1 for _ in group)
            if length > 1:
                yield 128 + length
            yield tile_id


def generate():
    patterns, colors = bytearray(), bytearray()
    tile_ids = {}
    used_tiles = [set() for _ in range(3)]

    def tile(rows):
        rows = tuple(rows)
        if rows not in tile_ids:
            tile_ids[rows] = len(tile_ids)
            patterns.extend(pattern for pattern, _ in rows)
            colors.extend(color for _, color in rows)
        return tile_ids[rows]

    def panel(field, rows):
        for row, _, tiles in rows:
            used_tiles[(row + 4) // 8].update(tiles)
        return panel_data(field, rows)

    blank = tile([(0, 0x11)] * 8)
    # Transparent ground/ceiling pixels normally show the black backdrop.
    # When the player takes damage they show the red VDP backdrop instead.
    ceiling = [(0, 0x00)] * 8
    floor = [(0x22 if y % 2 else 0x88, 0x40) for y in range(8)]
    floor_tile = tile(floor)
    ceiling_tile = tile(ceiling)
    terrain_tiles = [floor_tile]

    # Two-pixel height increments bound the number of wall cap profiles.
    projected_heights = [min(96, 2 * round(WALL_PROJECTION / (2 * n))) for n in range(1, RAY_LIMIT + 2)]
    heights = [min(64, height) for height in projected_heights]
    # Outside the central band, round to the nearest complete tile row.
    extension_rows = [(height - 64 + 4) // 8 for height in projected_heights if height >= 68]
    wall_heights = sorted(set(heights))
    style_offsets = [32 + i * 16 for i in (0, 0, 1, 2, 0, 3, 4, 2)]
    templates = []
    door = [(0xFE, 0xD4), (0xBA, 0xD4)] + [(0x7E, 0xD4)] * 5 + [(0x7E, 0xF4)]
    stone_palettes = [palette for _, _, palette in TERRAIN if palette is not None]
    walls = [
        (stone_rows(STONE_ROWS, palette), stone_rows(OFFSET_STONE_ROWS, palette), palette, 0xFF)
        for palette in stone_palettes
    ]
    walls.append((door, None, None, 0))
    corners = [(stone_rows(CORNER_ROWS, palette), None, palette, 0xEF) for palette in stone_palettes]
    terrain_tiles.extend(tile(wall) for wall, _, _, _ in walls)
    mini_terrain = [tile([(bits, 0x41) for bits in (0x88, 0, 0, 0, 0x88, 0, 0, 0)])]
    for border, center in ((4, 5), (10, 11), (13, 13)):
        mini_terrain.append(tile([
            (0, 0x11), (0x7e, border << 4 | 1),
            *((0x42, border << 4 | center),) * 4,
            (0x7e, border << 4 | 1), (0, 0x11),
        ]))
    if len(terrain_tiles) + len(mini_terrain) + len(style_offsets) + len(heights) > 256:
        raise ValueError("As tabelas de material e profundidade devem caber na mesma página.")
    for wall, alternate, palette, rim in walls + corners:
        for half_height in wall_heights:
            top, bottom = 64 - half_height, 64 + half_height - 1
            column = ceiling * 8 + floor * 8
            column[top:bottom + 1] = [wall[y % 8] for y in range(top, bottom + 1)]
            if palette is not None and half_height < 64:
                shade, mid, _, _ = palette
                column[top] = (rim, (mid << 4) | shade)
                column[bottom] = (rim, (shade << 4) | mid)
            for y in range(0, 128, 8):
                rows = column[y:y + 8]
                if alternate and y % 16 and top < y and y + 7 < bottom:
                    rows = alternate
                index = tile(rows)
                templates.append(index)
                used_tiles[(y // 8 + 4) // 8].add(index)

    def label(text, accent):
        return [
            blank if char == " " else tile(
                [(row << 1, (accent << 4) | 1) for row in bytes.fromhex(FONT[char])]
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
    # Projected objects occupy viewport rows 6–9, all in the middle SCREEN 2 bank.
    used_tiles[1].update(index for _, _, art in objects for index in art)

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

    heart_full = tile([(bits, 0x91) for bits in (0, 0x66, 0xff, 0xff, 0x7e, 0x3c, 0x18, 0)])
    legend_panel = panel("legend_panel", [
        (1, 2, label("LEGENDA", 15)),
        (3, 2, label("TERRENO", 11)),
        (3, 20, label("OBJETOS", 11)),
        *((5 + index * 2, 2, marker_row(name, icon))
          for index, (name, icon) in enumerate(terrain_legend)),
        *((5 + index * 2, 20, marker_row(name, icon))
          for index, (_, name, icon) in enumerate(markers)),
        (15, 2, marker_row("CURA", heart_full)),
    ])
    menu_hud = label(" ESQ MAPA             M VOLTAR".ljust(32), 15)
    map_hud = label(" DIR LEGENDA  SUBIR DESCER  M".ljust(32), 15)

    def story_panel(field, title, detail, action, accent=7):
        return panel(field, [
            (3, (32 - len(title)) // 2, label(title, accent)),
            (7, (32 - len(detail)) // 2, label(detail, 15)),
            (12, (32 - len(action)) // 2, label(action, 11)),
        ])

    campaign_panels = (
        story_panel("death_panel", "VOCE CAIU", "O SETOR AINDA ESTA TOMADO", "ESP TENTAR DE NOVO", 9),
        story_panel("clear_panel", "SETOR SEGURO", "A ROTA ESTA LIVRE", "ESP PROXIMO SETOR", 7),
        story_panel("last_panel", "POSTO RECUPERADO", "CAMPANHA CONCLUIDA", "ESP VOLTAR AO INICIO", 7),
    )
    title_panel = panel("title_panel", [
        (12, 9, label("SINAL DE UMBRA", 15)),
        (16, 7, [directions[3], blank, *label("NIVEL", 15)]),
        (16, 24, [directions[1]]),
        (18, 6, label("ESP INICIAR CAMPANHA", 11)),
    ])
    difficulty_names = [index for name in ("FACIL", "NORMAL", "DIFICIL")
                        for index in label(name.ljust(8), 15)]
    meter_idle = tile([(bits, 0x41) for bits in (0, 0, 0, 0x7e, 0x7e, 0, 0, 0)])
    meter_active = tile([(bits, 0x71) for bits in (0, 0, 0x7e, 0x7e, 0x7e, 0x7e, 0, 0)])
    heart_empty = tile([(bits, 0xe1) for bits in (0, 0x66, 0x99, 0x81, 0x42, 0x24, 0x18, 0)])
    ammo_icon = next(art[0] for kind, _, art in objects if kind == "ammo")
    hud = [blank] + [heart_full] * MAX_LIFE + [blank, ammo_icon]
    ammo_offset = len(hud)
    hud += [blank] * 3
    weapon_offset = len(hud)
    hud += [blank] * 7 + label(" S", 7)
    sector_offset = len(hud)
    hud += [blank] * 2
    hint_offset = len(hud)
    hint_width = 32 - hint_offset
    hud.extend([blank] * hint_width)
    weapons = label("PISTOLAPULSO  ", 7)
    digits = label("0123456789", 15)
    hints = (
        "ACHE CHAVE", "ABRA PORTA", "ACHE SAIDA", "SEM MUN",
        "MUN EXTRA", "TRANCADA", "CURA EXTRA",
    )
    if any(len(message) > hint_width for message in hints):
        raise ValueError("Mensagem de objetivo excede a largura disponível no HUD.")
    hint_labels = [f"hud_hint_{index}" for index in range(len(hints))]
    hint_tiles = [label(message.ljust(hint_width), 11) for message in hints]
    hint_rows = [data(name, tiles) for name, tiles in zip(hint_labels, hint_tiles)]
    if len(tile_ids) > 256:
        raise ValueError("SCREEN 2 admite até 256 tiles por banco.")

    common_tiles = {blank, heart_full, door_passage, *directions, *terrain_tiles,
                    *(icon for _, _, icon in markers)}
    for bank in used_tiles:
        bank.update(common_tiles)
    used_tiles[0].update([ceiling_tile, *mini_terrain])
    used_tiles[2].update(menu_hud + map_hud + hud + weapons + digits + [heart_empty, meter_idle, meter_active])
    used_tiles[2].update(difficulty_names)
    used_tiles[2].update(index for hint in hint_tiles for index in hint)
    caps = sloped_caps(wall_heights, walls, stone_palettes, ceiling, floor, used_tiles)

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
        f"ceiling_tile: equ {ceiling_tile}",
        f"floor_tile: equ {floor_tile}",
        data("walk_vectors", walk_vectors, "dw"),
        data("ray_vectors", ray_vectors),
        data("camera_vectors", camera_vectors),
        "ray_limit: equ " + str(RAY_LIMIT),
        data("wall_columns", pack_wall_columns(templates, len(wall_heights))),
        "    ds align 256",
        data("terrain_tiles", terrain_tiles),
        data("mini_terrain", mini_terrain),
        # Index by material plus 4 for a corner. Doors use the same style in both cases.
        data("wall_styles", style_offsets),
        # The aligned terrain lookup and this depth lookup share a ROM page.
        data("heights", (wall_heights.index(height) for height in heights)),
        *caps,
        f"wall_extension_count: equ {len(extension_rows)}",
        data("wall_extensions", extension_rows),
        *(data(f"{kind}_tiles", art) for kind, _, art in objects),
        data("object_depths", (distance * 4 // 9 for distance in range(182))),
        data("object_offsets", (0, 1, 5, 14)),
        data("hud_template", hud),
        f"max_life: equ {MAX_LIFE}",
        "hud_life_offset: equ 1",
        f"hud_weapon_offset: equ {weapon_offset}",
        f"hud_sector_offset: equ {sector_offset}",
        f"hud_ammo_offset: equ {ammo_offset}",
        f"hud_hint_offset: equ {hint_offset}",
        f"hud_hint_width: equ {hint_width}",
        data("hud_hearts", (heart_empty, heart_full)),
        data("weapon_names", weapons),
        data("hud_digits", digits),
        data("hud_hint_addresses", hint_labels, "dw"),
        *hint_rows,
        *campaign_panels,
        title_panel,
        data("difficulty_names", difficulty_names),
        data("campaign_panels", ("death_panel", "clear_panel", "last_panel"), "dw"),
        legend_panel,
        data("menu_hud", menu_hud),
        data("map_hud", map_hud),
        data("map_arrows", directions),
        f"map_open_door: equ {door_passage}",
        *(f"map_{kind}: equ {icon}" for kind, _, icon in markers if kind != "player"),
        data("medic_tiles", (
            heart_full if cell == (size // 2) * (size + 1) else blank
            for size in range(1, 5) for cell in range(size * size)
        )),
        data("prop_art", ("ammo_tiles", "medic_tiles", "key_tiles", 0, "exit_tiles"), "dw"),
        data("prop_icons", ("map_ammo", heart_full, "map_key", "map_open_door", "map_exit")),
        sector_data(data),
        f"intro_meter_idle: equ {meter_idle}",
        f"intro_meter_active: equ {meter_active}",
        "",
    ))
