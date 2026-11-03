import pytest

from ship_port_management.dockings import Docking
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship
from ship_port_management.status import (
    available_docks,
    current_dock_id,
    describe_fill_level,
    describe_ship_location,
    fill_percentage,
    format_port_status,
    format_section,
)
from ship_port_management.warehouses import Warehouse

ATLAS = Ship("MV-ATLAS", "Atlas", "2026-11-03T09:30", 500, 40)
NOVA = Ship("MV-NOVA", "Nova", "2026-11-03T11:00", 300, 0)
NORTH_DOCK = Dock("D1", 500, 120.0)
SOUTH_DOCK = Dock("D2", 300, 80.0)
ATLAS_AT_NORTH = Docking("MV-ATLAS", "D1")
WAREHOUSE_CAPACITY = 200
HALF_FULL = Warehouse("W1", WAREHOUSE_CAPACITY, 1.5, WAREHOUSE_CAPACITY // 2)
EMPTY = Warehouse("W2", WAREHOUSE_CAPACITY, 1.5)


def test_docked_ship_reports_its_dock() -> None:
    assert current_dock_id("MV-ATLAS", [ATLAS_AT_NORTH]) == "D1"


def test_undocked_ship_has_no_dock() -> None:
    assert current_dock_id("MV-NOVA", [ATLAS_AT_NORTH]) is None


def test_occupied_dock_is_not_available() -> None:
    assert available_docks([NORTH_DOCK, SOUTH_DOCK], {"D1"}) == [SOUTH_DOCK]


def test_all_docks_available_when_none_occupied() -> None:
    assert available_docks([NORTH_DOCK, SOUTH_DOCK], set()) == [NORTH_DOCK, SOUTH_DOCK]


def test_fill_percentage_of_half_full_warehouse() -> None:
    assert fill_percentage(HALF_FULL) == 50


def test_fill_percentage_of_empty_warehouse_is_zero() -> None:
    assert fill_percentage(EMPTY) == 0


def test_zero_capacity_warehouse_is_refused() -> None:
    with pytest.raises(ValueError):
        fill_percentage(Warehouse("W3", 0, 1.5))


def test_overfull_warehouse_is_refused() -> None:
    with pytest.raises(ValueError):
        fill_percentage(Warehouse("W3", WAREHOUSE_CAPACITY, 1.5, WAREHOUSE_CAPACITY + 1))


def test_no_free_docks_says_none() -> None:
    lines = format_port_status([], [NORTH_DOCK], [], [ATLAS_AT_NORTH])
    assert lines[lines.index("Available docks") + 1] == "  none"


def test_ship_location_names_the_dock() -> None:
    assert describe_ship_location(ATLAS, [ATLAS_AT_NORTH]) == "MV-ATLAS  Atlas  at dock D1"


def test_ship_location_says_not_docked() -> None:
    assert describe_ship_location(NOVA, [ATLAS_AT_NORTH]) == "MV-NOVA  Nova  not docked"


def test_fill_level_shows_units_and_percentage() -> None:
    assert describe_fill_level(HALF_FULL) == "W1  100/200 units  50% full"


def test_empty_section_says_none() -> None:
    assert format_section("Storage", []) == ["Storage", "  none"]


def test_port_status_has_all_three_sections() -> None:
    lines = format_port_status(
        [ATLAS, NOVA], [NORTH_DOCK, SOUTH_DOCK], [HALF_FULL], [ATLAS_AT_NORTH]
    )
    assert all(title in lines for title in ("Ships", "Available docks", "Storage"))
    assert "  MV-NOVA  Nova  not docked" in lines


def test_port_status_lists_only_free_docks() -> None:
    lines = format_port_status([ATLAS], [NORTH_DOCK, SOUTH_DOCK], [], [ATLAS_AT_NORTH])
    dock_lines = [line for line in lines if "Dock id:" in line]
    assert len(dock_lines) == 1
    assert "D2" in dock_lines[0]
