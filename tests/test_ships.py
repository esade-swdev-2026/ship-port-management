import pytest

from ship_port_management.ships import (
    Ship,
    cargo_within_capacity,
    describe_ship,
    is_duplicate_ship,
    register_ship,
    remaining_capacity,
)

ATLAS_CAPACITY = 500

ATLAS = Ship("IMO9074729", "Atlas", "2026-10-14T09:30", ATLAS_CAPACITY, 40)
NOVA = Ship("IMO9012328", "Nova", "2026-10-14T11:00", 300, 0)


def atlas_carrying(cargo_units: int) -> Ship:
    return Ship("IMO9074729", "Atlas", "2026-10-14T09:30", ATLAS_CAPACITY, cargo_units)


def test_cargo_below_capacity() -> None:
    assert cargo_within_capacity(atlas_carrying(40))


def test_cargo_above_capacity() -> None:
    assert not cargo_within_capacity(atlas_carrying(ATLAS_CAPACITY + 1))


def test_cargo_exactly_at_capacity_allowed() -> None:
    assert cargo_within_capacity(atlas_carrying(ATLAS_CAPACITY))


def test_empty_ship_within_capacity() -> None:
    assert cargo_within_capacity(atlas_carrying(0))


def test_negative_cargo() -> None:
    assert not cargo_within_capacity(atlas_carrying(-5))


def test_duplicate_ship() -> None:
    assert is_duplicate_ship(ATLAS, [NOVA, ATLAS])


def test_not_duplicate_ship() -> None:
    assert not is_duplicate_ship(ATLAS, [NOVA])


def test_no_ships_registered_means_no_duplicate() -> None:
    assert not is_duplicate_ship(ATLAS, [])


def test_same_id_with_different_details_is_still_duplicate() -> None:
    renamed = Ship(ATLAS.ship_id, "Other name", "2026-10-15T08:00", 300, 0)
    assert is_duplicate_ship(renamed, [ATLAS])


def test_remaining_capacity() -> None:
    assert remaining_capacity(ATLAS) == 460


def test_register_first_ship() -> None:
    assert register_ship(ATLAS, []) == [ATLAS]


def test_register_adds_ship_at_the_end() -> None:
    assert register_ship(NOVA, [ATLAS]) == [ATLAS, NOVA]


def test_register_duplicate_id_is_refused() -> None:
    with pytest.raises(ValueError):
        register_ship(ATLAS, [ATLAS])


def test_register_over_capacity_is_refused() -> None:
    with pytest.raises(ValueError):
        register_ship(atlas_carrying(ATLAS_CAPACITY + 1), [])


def test_register_does_not_change_the_original_list() -> None:
    registered = [ATLAS]
    register_ship(NOVA, registered)
    assert registered == [ATLAS]


def test_register_zero_capacity_is_refused() -> None:
    no_room = Ship("IMO9000001", "Empty", "2026-10-14T09:30", 0, 0)
    with pytest.raises(ValueError):
        register_ship(no_room, [])


def test_describe_ship_shows_id_name_arrival_and_cargo() -> None:
    assert describe_ship(ATLAS) == "IMO9074729  Atlas  arrived 2026-10-14T09:30  cargo 40/500"
