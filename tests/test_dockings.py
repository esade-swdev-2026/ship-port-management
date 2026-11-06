import pytest

from ship_port_management.dockings import (
    Docking,
    dock_ship,
    is_ship_docked,
    occupied_dock_ids,
    ship_fits_dock,
)
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship

ATLAS = Ship("IMO9074729", "Atlas", "2026-10-14T09:30", 500, 40)
BEFORE_ATLAS_ARRIVES = "2026-10-14T08:00"
NOVA = Ship("IMO9012328", "Nova", "2026-10-14T11:00", 300, 0)
NORTH = Dock("North", 500, 120.0)
SOUTH = Dock("South", 300, 80.5)
DOCKED_AT = "2026-10-14T12:00"


def test_ship_exactly_at_max_size_fits() -> None:
    assert ship_fits_dock(ATLAS, NORTH)


def test_ship_bigger_than_dock_does_not_fit() -> None:
    assert not ship_fits_dock(ATLAS, SOUTH)


def test_occupied_dock_ids_lists_every_docked_dock() -> None:
    dockings = [
        Docking("IMO9074729", "North", DOCKED_AT),
        Docking("IMO9012328", "South", DOCKED_AT),
    ]
    assert occupied_dock_ids(dockings) == {"North", "South"}


def test_ship_with_a_docking_is_docked() -> None:
    assert is_ship_docked("IMO9074729", [Docking("IMO9074729", "North", DOCKED_AT)])


def test_dock_ship_adds_a_docking() -> None:
    assert dock_ship(ATLAS, NORTH, DOCKED_AT, []) == [Docking("IMO9074729", "North", DOCKED_AT)]


def test_dock_ship_leaves_the_original_list_unchanged() -> None:
    dockings: list[Docking] = []
    dock_ship(ATLAS, NORTH, DOCKED_AT, dockings)
    assert dockings == []


def test_ship_too_big_for_dock_is_refused() -> None:
    with pytest.raises(ValueError, match="takes at most 300"):
        dock_ship(ATLAS, SOUTH, DOCKED_AT, [])


def test_occupied_dock_is_refused() -> None:
    with pytest.raises(ValueError, match="already occupied"):
        dock_ship(NOVA, NORTH, DOCKED_AT, [Docking("IMO9074729", "North", DOCKED_AT)])


def test_ship_already_docked_elsewhere_is_refused() -> None:
    with pytest.raises(ValueError, match="already docked"):
        dock_ship(NOVA, NORTH, DOCKED_AT, [Docking("IMO9012328", "South", DOCKED_AT)])


def test_dock_ship_records_the_docking_time() -> None:
    [docking] = dock_ship(ATLAS, NORTH, DOCKED_AT, [])
    assert docking.docked_at == DOCKED_AT


def test_docking_before_arrival_is_refused() -> None:
    with pytest.raises(ValueError, match="before arrival"):
        dock_ship(ATLAS, NORTH, BEFORE_ATLAS_ARRIVES, [])


def test_docking_exactly_at_arrival_is_allowed() -> None:
    assert dock_ship(ATLAS, NORTH, ATLAS.arrival_time, []) == [
        Docking("IMO9074729", "North", ATLAS.arrival_time)
    ]


def test_docking_time_that_is_not_a_time_is_refused() -> None:
    with pytest.raises(ValueError, match="docking time"):
        dock_ship(ATLAS, NORTH, "banana", [])
