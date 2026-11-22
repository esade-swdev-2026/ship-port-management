from pathlib import Path

import pytest

from ship_port_management.csv_handling import (
    read_departures,
    read_dockings,
    read_docks,
    read_ships,
    read_stored_cargo,
    read_transfers,
    read_warehouses,
    write_departures,
    write_dockings,
    write_docks,
    write_ships,
    write_stored_cargo,
    write_transfers,
    write_warehouses,
)
from ship_port_management.departures import Departure
from ship_port_management.dockings import Docking
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship
from ship_port_management.storage import StoredCargo
from ship_port_management.visits import LOADED, UNLOADED, CargoTransfer
from ship_port_management.warehouses import Warehouse

ATLAS = Ship("IMO9074729", "Atlas", "2026-10-14T09:30", 500, 40)
NOVA = Ship("IMO9012328", "Nova", "2026-10-14T11:00", 300, 0)
NORTH_DOCK = Dock("North", 500, 120.0)
SOUTH_DOCK = Dock("South", 300, 80.5)
NORTH_WAREHOUSE = Warehouse("W-NORTH", 200, 1.5, 50)
SOUTH_WAREHOUSE = Warehouse("W-SOUTH", 100, 2.0)


def test_ships_written_can_be_read_back(tmp_path: Path) -> None:
    ships_file = tmp_path / "data" / "ships.csv"
    write_ships(ships_file, [ATLAS, NOVA])
    assert read_ships(ships_file) == [ATLAS, NOVA]


def test_missing_file_means_no_ships(tmp_path: Path) -> None:
    assert read_ships(tmp_path / "missing.csv") == []


def test_row_with_missing_columns_is_refused(tmp_path: Path) -> None:
    ships_file = tmp_path / "ships.csv"
    ships_file.write_text("ship_id,name,arrival_time,capacity,cargo_units\nIMO9074729,Atlas\n")
    with pytest.raises(ValueError):
        read_ships(ships_file)


def test_docks_written_can_be_read_back(tmp_path: Path) -> None:
    docks_file = tmp_path / "data" / "docks.csv"
    write_docks(docks_file, [NORTH_DOCK, SOUTH_DOCK])
    assert read_docks(docks_file) == [NORTH_DOCK, SOUTH_DOCK]


def test_missing_file_means_no_docks(tmp_path: Path) -> None:
    assert read_docks(tmp_path / "missing.csv") == []


def test_warehouses_written_can_be_read_back(tmp_path: Path) -> None:
    warehouses_file = tmp_path / "data" / "warehouses.csv"
    write_warehouses(warehouses_file, [NORTH_WAREHOUSE, SOUTH_WAREHOUSE])
    assert read_warehouses(warehouses_file) == [NORTH_WAREHOUSE, SOUTH_WAREHOUSE]


def test_missing_file_means_no_warehouses(tmp_path: Path) -> None:
    assert read_warehouses(tmp_path / "missing.csv") == []


def test_dockings_written_can_be_read_back(tmp_path: Path) -> None:
    dockings_file = tmp_path / "data" / "dockings.csv"
    dockings = [
        Docking("IMO9074729", "North", "2026-10-14T12:00"),
        Docking("IMO9012328", "South", "2026-10-14T13:30"),
    ]
    write_dockings(dockings_file, dockings)
    assert read_dockings(dockings_file) == dockings


def test_missing_file_means_no_dockings(tmp_path: Path) -> None:
    assert read_dockings(tmp_path / "missing.csv") == []


def test_stored_cargo_written_can_be_read_back(tmp_path: Path) -> None:
    stored_cargo_file = tmp_path / "data" / "stored_cargo.csv"
    stored = [
        StoredCargo("IMO9074729", "W-NORTH", 30, "2026-10-14T09:30"),
        StoredCargo("IMO9012328", "W-SOUTH", 10, "2026-10-15T12:00"),
    ]
    write_stored_cargo(stored_cargo_file, stored)
    assert read_stored_cargo(stored_cargo_file) == stored


def test_missing_file_means_no_stored_cargo(tmp_path: Path) -> None:
    assert read_stored_cargo(tmp_path / "missing.csv") == []


def test_departures_written_can_be_read_back(tmp_path: Path) -> None:
    departures_file = tmp_path / "data" / "departures.csv"
    departures = [
        Departure("IMO9074729", "North", "2026-10-14T10:00", "2026-10-14T15:20", 6, 720.0),
        Departure("IMO9012328", "South", "2026-10-14T13:30", "2026-10-14T15:30", 2, 161.0),
    ]
    write_departures(departures_file, departures)
    assert read_departures(departures_file) == departures


def test_missing_file_means_no_departures(tmp_path: Path) -> None:
    assert read_departures(tmp_path / "missing.csv") == []


def test_departure_row_with_missing_columns_is_refused(tmp_path: Path) -> None:
    departures_file = tmp_path / "departures.csv"
    departures_file.write_text(
        "ship_id,dock_id,docked_at,departed_at,hours,docking_fee\nIMO9074729,North\n"
    )
    with pytest.raises(ValueError):
        read_departures(departures_file)


def test_ship_row_with_a_word_for_capacity_is_refused(tmp_path: Path) -> None:
    ships_file = tmp_path / "ships.csv"
    ships_file.write_text(
        "ship_id,name,arrival_time,capacity,cargo_units\nIMO9074729,Atlas,2026-10-14T09:30,big,0\n"
    )
    with pytest.raises(ValueError, match="capacity must be a whole number, got 'big'"):
        read_ships(ships_file)


def test_ship_row_that_breaks_the_rules_is_refused(tmp_path: Path) -> None:
    ships_file = tmp_path / "ships.csv"
    ships_file.write_text(
        "ship_id,name,arrival_time,capacity,cargo_units\nIMO9074729,Atlas,banana,-5,999\n"
    )
    with pytest.raises(ValueError, match="malformed row"):
        read_ships(ships_file)


def test_dock_row_with_a_rate_that_is_not_a_number_is_refused(tmp_path: Path) -> None:
    docks_file = tmp_path / "docks.csv"
    docks_file.write_text("dock_id,max_ship_size,hourly_rate\nNorth,500,cheap\n")
    with pytest.raises(ValueError, match="hourly rate must be a number, got 'cheap'"):
        read_docks(docks_file)


def test_warehouse_row_holding_more_than_its_capacity_is_refused(tmp_path: Path) -> None:
    warehouses_file = tmp_path / "warehouses.csv"
    warehouses_file.write_text(
        "warehouse_id,capacity,daily_rate_per_unit,stored_units\nW-NORTH,100,1.5,150\n"
    )
    with pytest.raises(ValueError, match="stored units must be between 0 and capacity"):
        read_warehouses(warehouses_file)


def test_docking_row_with_a_bad_time_is_refused(tmp_path: Path) -> None:
    dockings_file = tmp_path / "dockings.csv"
    dockings_file.write_text("ship_id,dock_id,docked_at\nIMO9074729,North,yesterday\n")
    with pytest.raises(ValueError, match="docking time must look like"):
        read_dockings(dockings_file)


def test_stored_cargo_row_with_a_bad_time_is_refused(tmp_path: Path) -> None:
    stored_cargo_file = tmp_path / "stored_cargo.csv"
    stored_cargo_file.write_text(
        "ship_id,warehouse_id,units,stored_at\nIMO9074729,W-NORTH,30,soon\n"
    )
    with pytest.raises(ValueError, match="storage time must look like"):
        read_stored_cargo(stored_cargo_file)


def test_departure_row_with_a_word_for_hours_is_refused(tmp_path: Path) -> None:
    departures_file = tmp_path / "departures.csv"
    departures_file.write_text(
        "ship_id,dock_id,docked_at,departed_at,hours,docking_fee\n"
        "IMO9074729,North,2026-10-14T10:00,2026-10-14T15:20,six,720.0\n"
    )
    with pytest.raises(ValueError, match="hours must be a whole number, got 'six'"):
        read_departures(departures_file)


def test_stored_cargo_row_with_negative_units_is_refused(tmp_path: Path) -> None:
    stored_cargo_file = tmp_path / "stored_cargo.csv"
    stored_cargo_file.write_text(
        "ship_id,warehouse_id,units,stored_at\nIMO9074729,W-NORTH,-30,2026-10-14T09:30\n"
    )
    with pytest.raises(ValueError, match="units stored must be positive, got -30"):
        read_stored_cargo(stored_cargo_file)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("IMO9074729,North,2026-10-14T10:00,2026-10-14T15:20,-6,720.0", "hours must be 6"),
        ("IMO9074729,North,2026-10-14T10:00,2026-10-14T15:20,6,nan", "docking fee must be"),
        ("IMO9074729,North,2026-10-14T10:00,2026-10-14T09:00,0,0.0", "before docking time"),
    ],
)
def test_departure_row_that_breaks_the_rules_is_refused(
    tmp_path: Path, row: str, message: str
) -> None:
    departures_file = tmp_path / "departures.csv"
    departures_file.write_text(f"ship_id,dock_id,docked_at,departed_at,hours,docking_fee\n{row}\n")
    with pytest.raises(ValueError, match=message):
        read_departures(departures_file)


def test_two_ships_at_the_same_dock_are_refused(tmp_path: Path) -> None:
    dockings_file = tmp_path / "dockings.csv"
    dockings_file.write_text(
        "ship_id,dock_id,docked_at\n"
        "IMO9074729,North,2026-10-14T12:00\n"
        "IMO9012328,North,2026-10-14T13:30\n"
    )
    with pytest.raises(ValueError, match="dock North is already occupied"):
        read_dockings(dockings_file)


def test_transfers_written_can_be_read_back(tmp_path: Path) -> None:
    transfers_file = tmp_path / "data" / "cargo_transfers.csv"
    transfers = [
        CargoTransfer("IMO9074729", "2026-10-14T10:00", "W-NORTH", UNLOADED, 30),
        CargoTransfer("IMO9074729", "2026-10-14T10:00", "W-NORTH", LOADED, 10),
    ]
    write_transfers(transfers_file, transfers)
    assert read_transfers(transfers_file) == transfers


def test_missing_file_means_no_transfers(tmp_path: Path) -> None:
    assert read_transfers(tmp_path / "missing.csv") == []


def test_transfer_row_with_an_unknown_direction_is_refused(tmp_path: Path) -> None:
    transfers_file = tmp_path / "cargo_transfers.csv"
    transfers_file.write_text(
        "ship_id,docked_at,warehouse_id,direction,units\n"
        "IMO9074729,2026-10-14T10:00,W-NORTH,sideways,30\n"
    )
    with pytest.raises(ValueError, match="direction must be unloaded or loaded"):
        read_transfers(transfers_file)
