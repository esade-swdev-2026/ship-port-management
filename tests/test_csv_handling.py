from pathlib import Path

import pytest

from ship_port_management.csv_handling import read_docks, read_ships, write_docks, write_ships
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship

ATLAS = Ship("IMO9074729", "Atlas", "2026-10-14T09:30", 500, 40)
NOVA = Ship("IMO9012328", "Nova", "2026-10-14T11:00", 300, 0)
NORTH_DOCK = Dock("North", 500, 120.0)
SOUTH_DOCK = Dock("South", 300, 80.5)


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
