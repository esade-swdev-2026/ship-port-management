import pytest

from ship_port_management.cargo import CargoMove, load_cargo, unload_cargo
from ship_port_management.dockings import Docking
from ship_port_management.ships import Ship
from ship_port_management.warehouses import Warehouse

ATLAS_DOCKED = [Docking("IMO9074729", "North")]


def atlas_carrying(cargo_units: int) -> Ship:
    return Ship("IMO9074729", "Atlas", "2026-10-14T09:30", 500, cargo_units)


def north_storing(stored_units: int) -> Warehouse:
    return Warehouse("W-NORTH", 200, 1.5, stored_units)


def test_unload_moves_units_from_ship_to_warehouse() -> None:
    move = unload_cargo(atlas_carrying(40), north_storing(0), 30, ATLAS_DOCKED)
    assert move == CargoMove(atlas_carrying(10), north_storing(30))


def test_unload_all_cargo_on_board_is_allowed() -> None:
    move = unload_cargo(atlas_carrying(40), north_storing(0), 40, ATLAS_DOCKED)
    assert move.ship.cargo_units == 0


def test_unload_more_than_on_board_is_refused() -> None:
    with pytest.raises(ValueError, match="carries only 40"):
        unload_cargo(atlas_carrying(40), north_storing(0), 41, ATLAS_DOCKED)


def test_unload_more_than_warehouse_room_is_refused() -> None:
    with pytest.raises(ValueError, match="room for only 10"):
        unload_cargo(atlas_carrying(40), north_storing(190), 11, ATLAS_DOCKED)


def test_unload_from_undocked_ship_is_refused() -> None:
    with pytest.raises(ValueError, match="not docked"):
        unload_cargo(atlas_carrying(40), north_storing(0), 10, [])


def test_moving_zero_units_is_refused() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        unload_cargo(atlas_carrying(40), north_storing(0), 0, ATLAS_DOCKED)


def test_load_moves_units_from_warehouse_to_ship() -> None:
    move = load_cargo(atlas_carrying(0), north_storing(50), 20, ATLAS_DOCKED)
    assert move == CargoMove(atlas_carrying(20), north_storing(30))


def test_load_more_than_stored_is_refused() -> None:
    with pytest.raises(ValueError, match="holds only 50"):
        load_cargo(atlas_carrying(0), north_storing(50), 51, ATLAS_DOCKED)


def test_load_more_than_ship_room_is_refused() -> None:
    with pytest.raises(ValueError, match="room for only 5 more"):
        load_cargo(atlas_carrying(495), north_storing(50), 6, ATLAS_DOCKED)


def test_load_onto_undocked_ship_is_refused() -> None:
    with pytest.raises(ValueError, match="not docked"):
        load_cargo(atlas_carrying(0), north_storing(50), 10, [])
