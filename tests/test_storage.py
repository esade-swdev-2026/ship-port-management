from datetime import datetime

import pytest

from ship_port_management.storage import (
    StoredCargo,
    chargeable_days,
    describe_storage_fee,
    fees_by_ship,
    store_cargo,
    take_cargo,
)
from ship_port_management.warehouses import Warehouse

NORTH = Warehouse("W-NORTH", 200, 1.5, 0)
SOUTH = Warehouse("W-SOUTH", 100, 2.0, 0)
ATLAS_IN_NORTH = StoredCargo("MV-ATLAS", "W-NORTH", 30, "2026-10-14T09:30")
NOVA_IN_NORTH = StoredCargo("MV-NOVA", "W-NORTH", 20, "2026-10-13T09:30")


def test_store_cargo_adds_a_record() -> None:
    assert store_cargo(ATLAS_IN_NORTH, []) == [ATLAS_IN_NORTH]


def test_store_cargo_with_invalid_time_is_refused() -> None:
    with pytest.raises(ValueError, match="must look like"):
        store_cargo(StoredCargo("MV-ATLAS", "W-NORTH", 30, "yesterday"), [])


def test_store_cargo_with_timezone_is_refused() -> None:
    with pytest.raises(ValueError, match="without a timezone"):
        store_cargo(StoredCargo("MV-ATLAS", "W-NORTH", 30, "2026-10-14T09:30+02:00"), [])


def test_take_cargo_takes_the_ships_own_cargo_first() -> None:
    remaining = take_cargo("MV-ATLAS", "W-NORTH", 10, [NOVA_IN_NORTH, ATLAS_IN_NORTH])
    assert remaining == [NOVA_IN_NORTH, StoredCargo("MV-ATLAS", "W-NORTH", 20, "2026-10-14T09:30")]


def test_take_cargo_takes_the_oldest_cargo_first() -> None:
    newer = StoredCargo("MV-ATLAS", "W-NORTH", 5, "2026-10-16T09:30")
    remaining = take_cargo("MV-ATLAS", "W-NORTH", 10, [newer, ATLAS_IN_NORTH])
    assert remaining == [newer, StoredCargo("MV-ATLAS", "W-NORTH", 20, "2026-10-14T09:30")]


def test_take_cargo_moves_on_to_other_ships_cargo() -> None:
    remaining = take_cargo("MV-ATLAS", "W-NORTH", 35, [NOVA_IN_NORTH, ATLAS_IN_NORTH])
    assert remaining == [StoredCargo("MV-NOVA", "W-NORTH", 15, "2026-10-13T09:30")]


def test_take_cargo_leaves_other_warehouses_alone() -> None:
    in_south = StoredCargo("MV-ATLAS", "W-SOUTH", 10, "2026-10-10T09:30")
    remaining = take_cargo("MV-ATLAS", "W-NORTH", 30, [in_south, ATLAS_IN_NORTH])
    assert remaining == [in_south]


def test_take_cargo_more_than_on_record_is_refused() -> None:
    with pytest.raises(ValueError, match="only 30 units on record"):
        take_cargo("MV-ATLAS", "W-NORTH", 31, [ATLAS_IN_NORTH])


def test_no_days_charged_within_the_free_period() -> None:
    assert chargeable_days(ATLAS_IN_NORTH, datetime(2026, 10, 17, 9, 30)) == 0


def test_days_charged_after_the_free_period() -> None:
    assert chargeable_days(ATLAS_IN_NORTH, datetime(2026, 10, 19, 9, 30)) == 2


def test_partial_days_are_not_charged() -> None:
    assert chargeable_days(ATLAS_IN_NORTH, datetime(2026, 10, 18, 9, 29)) == 0


def test_fees_are_added_up_per_ship() -> None:
    atlas_in_south = StoredCargo("MV-ATLAS", "W-SOUTH", 10, "2026-10-14T09:30")
    fees = fees_by_ship(
        [ATLAS_IN_NORTH, atlas_in_south, NOVA_IN_NORTH], [NORTH, SOUTH], "2026-10-19T09:30"
    )
    assert fees == {"MV-ATLAS": 30 * 1.5 * 2 + 10 * 2.0 * 2, "MV-NOVA": 20 * 1.5 * 3}


def test_fees_with_invalid_time_are_refused() -> None:
    with pytest.raises(ValueError, match="fee time must look like"):
        fees_by_ship([ATLAS_IN_NORTH], [NORTH], "tomorrow")


def test_describe_storage_fee_shows_two_decimals() -> None:
    assert describe_storage_fee("MV-ATLAS", 90) == "MV-ATLAS owes 90.00 for storage"
