import math
from collections.abc import Callable
from functools import cache

WIDTH = 100
HEIGHT = 68
SHIP_TOP = 12
BRAILLE_BLANK = 0x2800
DOT_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
CELL_WIDTH = 2
CELL_HEIGHT = 4

HULL_COLOR = ""
CRATE_WIDTH = 8
CRATE_HEIGHT = 4
FIRST_BAY_X = 32
STACKS = (
    ("red", "blue", "yellow"),
    ("blue", "green", "red", "magenta"),
    ("yellow", "red", "cyan", "blue"),
    ("green", "magenta", "yellow"),
    ("cyan", "yellow", "blue", "red"),
    ("red", "blue", "green"),
    ("magenta", "cyan"),
)
DECK_Y = 28

Point = tuple[float, float]
Shape = Callable[[float, float], bool]
Cell = tuple[str, str]


def polygon(points: list[Point]) -> Shape:
    def contains(x: float, y: float) -> bool:
        hit = False
        for (x1, y1), (x2, y2) in zip(points, points[-1:] + points[:-1], strict=True):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                hit = not hit
        return hit

    return contains


def box(left: float, top: float, right: float, bottom: float) -> Shape:
    return lambda x, y: left <= x <= right and top <= y <= bottom


def window_row(left: int, right: int, y: float, spacing: int = 3) -> list[Shape]:
    return [box(x, y, x + 1, y + 1) for x in range(left, right, spacing)]


HULL_OUTLINE: list[Point] = [
    (4, 28),
    (88, 28),
    (94, 25),
    (97, 25),
    (97, 31),
    (95, 36),
    (98, 38),
    (97, 41.5),
    (93, 42),
    (16, 42),
    (9, 39),
    (6, 34),
]
SHIP: list[Shape] = [
    polygon(HULL_OUTLINE),
    box(9, 14, 27, 28),
    box(6, 10, 30, 13.5),
    box(11, 6, 26, 10),
    polygon([(12, 6), (14, 0), (21, 0), (19, 6)]),
    box(23, 0, 23.8, 6),
    box(20.5, 2, 26.5, 2.8),
    box(88, 23, 97, 25),
    box(92, 15, 92.8, 23),
]
CUTOUTS: list[Shape] = [
    *window_row(8, 29, 11),
    *window_row(11, 26, 17),
    *window_row(11, 26, 21),
    box(13, 2.5, 20, 3.3),
    box(10, 35, 95, 35.9),
]
WAVES = ((58, 1.2, 23, 1.0, 3), (62.5, 1.0, 17, -1.4, 4), (66.5, 0.8, 13, 1.8, 5))
FUNNEL_TOP = (16.5, float(SHIP_TOP))
SMOKE_PUFFS = 4


def crate_color(x: float, y: float) -> str | None:
    bay, column = divmod(x - FIRST_BAY_X, CRATE_WIDTH)
    tier, row = divmod(DECK_Y - y, CRATE_HEIGHT)
    if not (0 <= bay < len(STACKS) and 0 <= tier < len(STACKS[int(bay)])):
        return None
    if column >= CRATE_WIDTH - 1 or row >= CRATE_HEIGHT - 1:
        return None
    return STACKS[int(bay)][int(tier)]


def ship_color(x: float, y: float) -> str | None:
    y -= SHIP_TOP
    crate = crate_color(x, y)
    if crate is not None:
        return crate
    if any(cutout(x, y) for cutout in CUTOUTS):
        return None
    return HULL_COLOR if any(shape(x, y) for shape in SHIP) else None


def is_ship(x: float, y: float) -> bool:
    return ship_color(x, y) is not None


def is_sea(x: float, y: float, phase: float) -> bool:
    for base, height, length, speed, gap in WAVES:
        crest = base + height * math.sin(2 * math.pi * x / length + phase * speed)
        broken = (int(x) // gap + int(phase * speed * 3)) % 4 == 0
        if abs(y - crest) < 0.5 and not broken:
            return True
    return False


def is_smoke(x: float, y: float, phase: float) -> bool:
    funnel_x, funnel_y = FUNNEL_TOP
    for puff in range(SMOKE_PUFFS):
        age = (phase * 0.35 + puff / SMOKE_PUFFS) % 1.0
        centre_x = funnel_x - 1 - age * 14
        centre_y = funnel_y - 1 - age * 7
        radius = 0.8 + age * 2.4
        if (x - centre_x) ** 2 + ((y - centre_y) * 1.6) ** 2 <= radius**2:
            return (int(x) + int(y)) % 2 == 0
    return False


def is_moving(x: float, y: float, phase: float) -> bool:
    return is_sea(x, y, phase) or is_smoke(x, y, phase)


def braille_cells(paint: Callable[[float, float], str | None]) -> list[list[Cell]]:
    rows = []
    for row in range(HEIGHT // CELL_HEIGHT):
        cells = []
        for column in range(WIDTH // CELL_WIDTH):
            bits = 0
            color = HULL_COLOR
            for dy, row_bits in enumerate(DOT_BITS):
                for dx, bit in enumerate(row_bits):
                    x = column * CELL_WIDTH + dx + 0.5
                    y = row * CELL_HEIGHT + dy + 0.5
                    dot = paint(x, y)
                    if dot is not None:
                        bits |= bit
                        color = dot or color
            cells.append((chr(BRAILLE_BLANK + bits) if bits else " ", color))
        rows.append(cells)
    return rows


@cache
def ship_cells() -> tuple[tuple[Cell, ...], ...]:
    return tuple(tuple(row) for row in braille_cells(ship_color))


def motion_rows(phase: float) -> list[str]:
    cells = braille_cells(lambda x, y: HULL_COLOR if is_moving(x, y, phase) else None)
    return ["".join(char for char, _ in row) for row in cells]
