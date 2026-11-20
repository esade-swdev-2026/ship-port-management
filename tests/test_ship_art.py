from ship_port_management import ship_art

BRAILLE = range(0x2800, 0x2900)


def is_braille_or_blank(row: str) -> bool:
    return all(cell == " " or ord(cell) in BRAILLE for cell in row)


def ship_text(row: tuple[ship_art.Cell, ...]) -> str:
    return "".join(char for char, _ in row)


def test_ship_and_motion_layers_have_the_same_shape() -> None:
    ship = [ship_text(row) for row in ship_art.ship_cells()]
    motion = ship_art.motion_rows(0.0)
    assert len(ship) == len(motion) == ship_art.HEIGHT // ship_art.CELL_HEIGHT
    assert {len(row) for row in ship + motion} == {ship_art.WIDTH // ship_art.CELL_WIDTH}


def test_art_is_drawn_in_braille_dots() -> None:
    rows = [ship_text(row) for row in ship_art.ship_cells()] + ship_art.motion_rows(0.0)
    assert all(is_braille_or_blank(row) for row in rows)
    assert any(row.strip() for row in rows)


def test_sea_and_smoke_move_with_the_phase() -> None:
    assert ship_art.motion_rows(0.0) != ship_art.motion_rows(1.0)


def test_crates_are_colored_and_the_hull_is_not() -> None:
    colors = {color for row in ship_art.ship_cells() for char, color in row if char != " "}
    assert ship_art.HULL_COLOR in colors
    assert {color for stack in ship_art.STACKS for color in stack} <= colors


def test_touching_crates_never_share_a_color() -> None:
    stacks = ship_art.STACKS
    for bay, stack in enumerate(stacks):
        for tier, color in enumerate(stack):
            assert tier + 1 >= len(stack) or stack[tier + 1] != color
            beside = stacks[bay + 1] if bay + 1 < len(stacks) else ()
            assert tier >= len(beside) or beside[tier] != color


def test_crates_have_gaps_between_them() -> None:
    gap_x = ship_art.FIRST_BAY_X + ship_art.CRATE_WIDTH - 0.5
    assert ship_art.crate_color(gap_x, ship_art.DECK_Y - 1.5) is None


def test_bridge_windows_are_cut_out_of_the_superstructure() -> None:
    bridge_y = ship_art.SHIP_TOP + 17.5
    assert ship_art.is_ship(13.5, bridge_y)
    assert not ship_art.is_ship(11.5, bridge_y)


def test_smoke_rises_above_the_funnel() -> None:
    funnel_x, funnel_y = ship_art.FUNNEL_TOP
    assert any(
        ship_art.is_smoke(x + 0.5, y + 0.5, 0.0)
        for y in range(int(funnel_y))
        for x in range(int(funnel_x) + 1)
    )
