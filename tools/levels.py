"""Original campaign layouts. Coordinates are zero-based, with north at the top."""

from collections import deque
from itertools import groupby

WIDTH, HEIGHT = 32, 44
DOORS = "1234"
KEYS = "abcd"
# M/B are always present, m is added on Normal, and t only on Difícil.
MARKS = "PMBmtAHE" + DOORS + KEYS


def layout(rooms, corridors, cover, markers):
    world = [["#"] * WIDTH for _ in range(HEIGHT)]

    def fill(x1, y1, x2, y2, tile):
        for y in range(y1, y2 + 1):
            world[y][x1:x2 + 1] = [tile] * (x2 - x1 + 1)

    for room in rooms:
        fill(*room, ".")
    for corridor in corridors:
        for (x1, y1), (x2, y2) in zip(corridor, corridor[1:]):
            if x1 != x2 and y1 != y2:
                raise ValueError("Corredores devem seguir os eixos do mapa.")
            fill(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), ".")
    for x, y in cover:
        if world[y][x] != ".":
            raise ValueError(f"Cobertura fora de uma sala em {x},{y}.")
        world[y][x] = "+"
    for tile, positions in markers.items():
        for x, y in positions:
            expected = "#" if tile in DOORS else "."
            if world[y][x] != expected:
                raise ValueError(f"Marcador {tile} sobre {world[y][x]} em {x},{y}.")
            world[y][x] = tile
    return tuple("".join(row) for row in world)


# A loading entrance opens onto the depot. Cross the stacks, pump room and
# control wing for their access keys, then make for the evacuation platform.
DEPOT = layout(
    rooms=(
        (2, 34, 8, 42), (12, 38, 17, 41), (21, 36, 29, 41), (11, 35, 15, 36),
        (2, 24, 8, 32), (12, 24, 19, 29), (24, 25, 29, 31), (10, 31, 17, 32),
        (2, 16, 8, 21), (11, 17, 19, 21), (23, 13, 29, 19), (2, 12, 6, 14),
        (2, 4, 7, 10), (11, 2, 17, 6), (21, 2, 29, 8), (11, 8, 17, 9), (2, 1, 5, 2),
    ),
    corridors=(
        ((8, 40), (12, 40)), ((17, 40), (21, 40)),
        ((8, 35), (11, 35)), ((15, 35), (26, 35), (26, 36)), ((14, 36), (14, 38)),
        ((6, 24), (6, 23)), ((8, 26), (12, 26)), ((19, 27), (24, 27)),
        ((8, 32), (10, 32)), ((17, 32), (26, 32), (26, 31)), ((16, 31), (16, 29)),
        ((8, 20), (11, 20)), ((19, 19), (23, 19)), ((8, 17), (11, 17)),
        ((3, 16), (3, 14)), ((13, 17), (13, 14), (23, 14)),
        ((7, 8), (11, 8)), ((17, 9), (20, 9), (20, 8), (21, 8)),
        ((15, 8), (15, 6)), ((17, 4), (21, 4)),
    ),
    cover=((5, 37), (6, 37), (13, 39), (24, 38), (25, 38), (25, 39),
           (5, 28), (5, 29), (14, 25), (16, 27), (17, 27), (26, 28),
           (7, 19), (14, 19), (17, 18), (25, 15), (25, 16), (26, 16),
           (5, 6), (12, 4), (24, 5), (25, 5)),
    markers={
        "P": ((4, 40),), "E": ((4, 2),),
        "1": ((4, 33),), "2": ((6, 22),), "3": ((3, 11),), "4": ((3, 3),),
        "a": ((28, 39),), "b": ((28, 30),), "c": ((28, 14),), "d": ((28, 3),),
        "M": ((14, 40), (7, 26), (12, 20), (22, 3)),
        "m": ((24, 37), (18, 25), (26, 17)), "t": ((16, 41), (27, 30), (15, 8)),
        "B": ((27, 41), (26, 26), (27, 15), (26, 6)),
        "A": ((7, 41), (22, 39), (9, 26), (23, 27), (20, 19)),
        "H": ((28, 36), (17, 31), (17, 5)),
    },
)

# Start in the northern intake. The eastern tram doors cut off the service
# decks while the keys sit in western maintenance rooms and the cooling hall.
FOUNDRY = layout(
    rooms=(
        (22, 2, 29, 10), (12, 2, 19, 6), (3, 2, 8, 9), (11, 8, 17, 9),
        (23, 12, 29, 21), (13, 13, 19, 20), (2, 12, 8, 20), (10, 14, 11, 16),
        (22, 23, 29, 32), (12, 24, 18, 31), (3, 24, 8, 31), (10, 29, 12, 32),
        (24, 37, 29, 41), (15, 36, 20, 42), (3, 35, 10, 41), (12, 35, 15, 38), (24, 34, 25, 35),
    ),
    corridors=(
        ((22, 4), (19, 4)), ((12, 3), (8, 3)),
        ((22, 9), (17, 9)), ((11, 9), (8, 9)), ((14, 8), (14, 6)),
        ((23, 14), (19, 14)), ((13, 15), (11, 15)), ((10, 15), (8, 15)),
        ((23, 20), (19, 20)), ((13, 19), (8, 19)), ((5, 20), (5, 21), (12, 21), (12, 19)),
        ((22, 25), (18, 25)), ((12, 26), (8, 26)),
        ((22, 31), (18, 31)), ((10, 30), (8, 30)),
        ((28, 34), (28, 37)), ((24, 37), (20, 37)), ((12, 37), (10, 37)), ((15, 41), (10, 41)),
    ),
    cover=((25, 5), (25, 6), (16, 4), (16, 5), (6, 6), (5, 7),
           (26, 15), (27, 15), (27, 16), (17, 16), (17, 17), (4, 17), (5, 17),
           (26, 27), (25, 28), (16, 28), (15, 28), (6, 27), (6, 28),
           (26, 38), (26, 39), (18, 39), (8, 38), (7, 38)),
    markers={
        "P": ((27, 8),), "E": ((24, 34),),
        "1": ((27, 11),), "2": ((25, 22),), "3": ((28, 33),), "4": ((25, 36),),
        "a": ((4, 4),), "b": ((3, 13),), "c": ((4, 25),), "d": ((4, 39),),
        "M": ((20, 4), (21, 14), (7, 13), (20, 25), (16, 36)),
        "m": ((7, 4), (14, 18), (8, 25)), "t": ((14, 4), (24, 18), (8, 36)),
        "B": ((4, 8), (3, 19), (5, 30), (6, 40)),
        "A": ((24, 3), (8, 8), (22, 20), (10, 16), (20, 31)),
        "H": ((13, 9), (17, 19), (25, 37)),
    },
)

# Three north-south wings flank the reactor. A narrow central gallery links
# the two service shafts before the last door leads to the surface relay.
REACTOR = layout(
    rooms=(
        (2, 35, 8, 42), (2, 26, 7, 31), (3, 16, 8, 22), (2, 7, 8, 12), (3, 2, 8, 5),
        (10, 35, 18, 42), (11, 25, 17, 31), (13, 15, 18, 21), (10, 6, 17, 11), (13, 2, 18, 4),
        (20, 35, 29, 42), (22, 27, 29, 31), (20, 17, 28, 23), (22, 11, 29, 14),
        (21, 6, 29, 9), (26, 2, 29, 5), (21, 2, 24, 4),
    ),
    corridors=(
        ((3, 35), (3, 31)), ((7, 35), (7, 31)), ((5, 26), (5, 22)),
        ((4, 16), (4, 12)), ((7, 16), (7, 12)), ((5, 7), (5, 5)),
        ((12, 35), (12, 31)), ((17, 35), (17, 31)), ((15, 25), (15, 21)),
        ((15, 15), (15, 11)), ((17, 15), (17, 11)), ((14, 6), (14, 4)),
        ((23, 35), (23, 31)), ((28, 35), (28, 31)), ((26, 27), (26, 23)),
        ((23, 17), (23, 14)), ((28, 17), (28, 14)),
    ),
    cover=((5, 37), (5, 38), (4, 28), (5, 28), (6, 19), (4, 9), (5, 9),
           (14, 38), (15, 38), (14, 27), (15, 27), (16, 18), (13, 8), (13, 9),
           (24, 37), (25, 37), (25, 38), (25, 29), (26, 29), (24, 20), (25, 20),
           (26, 5), (27, 5)),
    markers={
        "P": ((4, 40),), "E": ((22, 3),),
        "1": ((9, 39),), "2": ((19, 36),), "3": ((24, 10),), "4": ((22, 5),),
        "a": ((7, 3),), "b": ((16, 3),), "c": ((28, 41),), "d": ((28, 3),),
        "M": ((7, 29), (6, 8), (17, 28), (15, 6), (27, 38)),
        "m": ((4, 20), (17, 17), (27, 22)), "t": ((3, 31), (13, 37), (21, 19)),
        "B": ((7, 4), (14, 3), (27, 28), (23, 12), (27, 7)),
        "A": ((6, 40), (4, 11), (11, 39), (12, 26), (22, 39)),
        "H": ((6, 26), (11, 10), (27, 13)),
    },
)

SECTORS = (
    ("Deposito", 8, DEPOT),
    ("Fundicao", 9, FOUNDRY),
    ("Reator", 10, REACTOR),
)


def validate(name, rows):
    world = "".join(rows)
    if (len(rows) != HEIGHT or any(len(row) != WIDTH or row[0] != "#" or row[-1] != "#" for row in rows)
            or set(rows[0] + rows[-1]) != {"#"} or set(world) - set("#+." + MARKS)
            or any(world.count(marker) != 1 for marker in "PE" + DOORS + KEYS)):
        raise ValueError(f"Mapa ou marcadores inválidos em {name}.")

    def distances(start, closed):
        distance = {start: 0}
        todo = deque((start,))
        while todo:
            cell = todo.popleft()
            for neighbor in (cell - WIDTH, cell + WIDTH, cell - 1, cell + 1):
                if neighbor not in distance and world[neighbor] not in "#+" + closed:
                    distance[neighbor] = distance[cell] + 1
                    todo.append(neighbor)
        return distance

    current = world.index("P")
    exit_cell = world.index("E")
    minimum = 0
    for i, (key, door) in enumerate(zip(KEYS, DOORS)):
        closed = DOORS[i:]
        reachable = distances(current, closed)
        key_cell, gate = world.index(key), world.index(door)
        if (key_cell not in reachable or exit_cell in reachable
                or any(world.index(later) in reachable for later in KEYS[i + 1:])
                or not any(n in reachable for n in (gate - WIDTH, gate + WIDTH, gate - 1, gate + 1))):
            raise ValueError(f"Rota inválida para a chave {i + 1} em {name}.")
        minimum += reachable[key_cell]
        current = key_cell
    reachable = distances(current, "")
    if any(cell not in reachable for cell, mark in enumerate(world) if mark not in "#+"):
        raise ValueError(f"Trecho inacessível em {name}.")
    minimum += reachable[exit_cell]
    if minimum < 220:
        raise ValueError(f"Rota principal de {name} tem só {minimum} células.")
    return minimum


def sector_data(data):
    maps, records = [], []
    for index, (name, initial_ammo, rows) in enumerate(SECTORS):
        validate(name, rows)
        enemy_groups = ([], [], [])
        props, packed = [], []
        start = None
        world = "".join(rows)
        terrain = {"#": 1, "+": 2, **dict.fromkeys(DOORS, 3)}
        for material, run in groupby(terrain.get(mark, 0) for mark in world):
            length = len(list(run))
            while length:
                chunk = min(length, 64)
                packed.append(((chunk - 1) << 2) | material)
                length -= chunk
        for cell, mark in enumerate(world):
            x, y = cell % WIDTH, cell // WIDTH
            if mark == "P":
                start = (x, y)
            elif mark in "MBmt":
                group = {"m": 1, "t": 2}.get(mark, 0)
                brute = mark == "B"
                enemy_groups[group].append((x, y, int(brute), 3 + (index == 2) if brute else 2))
            elif mark == "A":
                props.append((x, y, 0, 8))
            elif mark == "H":
                props.append((x, y, 1, 2))
            elif mark in KEYS:
                props.append((x, y, 2, 1 << KEYS.index(mark)))
            elif mark in DOORS:
                props.append((x, y, 3, 1 << DOORS.index(mark)))
            elif mark == "E":
                props.append((x, y, 4, 0))
        if not enemy_groups[0] or any(len(group) != 3 for group in enemy_groups[1:]):
            raise ValueError(f"Reforços inválidos em {name}.")
        enemies = [enemy for group in enemy_groups for enemy in group]
        if len(enemies) > 16 or not 1 <= len(props) <= 17:
            raise ValueError(f"Objetos demais em {name}.")
        if initial_ammo + sum(prop[3] for prop in props if prop[2] == 0) < sum(enemy[3] for enemy in enemies):
            raise ValueError(f"Munição insuficiente em {name}.")
        map_label = f"sector_map_{index}"
        maps.append(data(map_label, packed))
        records.append(
            f"sector_{index}:\n    dw {map_label}\n    db "
            + ",".join(map(str, (*start, initial_ammo, len(enemies))))
            + "\n" + "\n".join("    db " + ",".join(map(str, enemy)) for enemy in enemies)
            + f"\n    db {len(props)}\n"
            + "\n".join("    db " + ",".join(map(str, prop)) for prop in props)
        )
    pointers = data("sector_records", (f"sector_{i}" for i in range(len(SECTORS))), "dw")
    return "\n".join((f"map_width: equ {WIDTH}", f"map_height: equ {HEIGHT}",
                      f"sector_count: equ {len(SECTORS)}", pointers, *records, *maps))
