from datetime import datetime

import pytest

from ship_port_management.port import (
    Dock,
    Ship,
    can_dock,
    docking_fee,
    find_available_dock,
    load_cargo,
    remaining_capacity,
    unload_cargo,
)

ATLAS = Ship("MV-ATLAS", capacity=500, cargo_units=40)


def test_remaining_capacity_is_capacity_minus_cargo() -> None:
    assert remaining_capacity(ATLAS) == 460


def test_full_ship_has_no_remaining_capacity() -> None:
    assert remaining_capacity(Ship("MV-FULL", capacity=100, cargo_units=100)) == 0


@pytest.mark.parametrize(
    ("dock", "expected"),
    [
        (Dock("A", max_ship_size=1000, hourly_rate=50.0), True),
        (Dock("B", max_ship_size=500, hourly_rate=50.0), True),
        (Dock("C", max_ship_size=499, hourly_rate=50.0), False),
        (Dock("D", max_ship_size=1000, hourly_rate=50.0, occupied=True), False),
    ],
)
def test_can_dock_needs_a_free_dock_that_fits(dock: Dock, expected: bool) -> None:
    assert can_dock(ATLAS, dock) is expected


def test_find_available_dock_skips_occupied_and_too_small_docks() -> None:
    docks = [
        Dock("A", max_ship_size=1000, hourly_rate=50.0, occupied=True),
        Dock("B", max_ship_size=100, hourly_rate=50.0),
        Dock("C", max_ship_size=1000, hourly_rate=50.0),
    ]
    found = find_available_dock(ATLAS, docks)
    assert found is not None
    assert found.name == "C"


def test_no_docks_means_no_available_dock() -> None:
    assert find_available_dock(ATLAS, []) is None


def test_unload_cargo_reduces_units_on_board() -> None:
    assert unload_cargo(ATLAS, 15).cargo_units == 25


def test_unload_more_than_on_board_is_rejected() -> None:
    with pytest.raises(ValueError):
        unload_cargo(ATLAS, 41)


@pytest.mark.parametrize("units", [0, -5])
def test_unload_zero_or_negative_units_is_rejected(units: int) -> None:
    with pytest.raises(ValueError):
        unload_cargo(ATLAS, units)


def test_load_cargo_up_to_exactly_full() -> None:
    assert load_cargo(ATLAS, 460).cargo_units == 500


def test_load_beyond_capacity_is_rejected() -> None:
    with pytest.raises(ValueError):
        load_cargo(ATLAS, 461)


def test_docking_fee_is_hours_times_rate() -> None:
    fee = docking_fee(datetime(2026, 10, 9, 8, 0), datetime(2026, 10, 9, 10, 30), 40.0)
    assert fee == pytest.approx(100.0)


def test_departure_before_arrival_is_rejected() -> None:
    with pytest.raises(ValueError):
        docking_fee(datetime(2026, 10, 9, 10, 0), datetime(2026, 10, 9, 8, 0), 40.0)
