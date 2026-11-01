from pathlib import Path

import pytest
from typer.testing import CliRunner

from ship_port_management.cli import app

runner = CliRunner()

REGISTER_ATLAS = ["register-vessel", "MV-ATLAS", "Atlas", "500", "--cargo-units", "40"]
REGISTER_OVERLOADED = ["register-vessel", "MV-ATLAS", "Atlas", "40", "--cargo-units", "500"]
ADD_NORTH_WAREHOUSE = ["add-warehouse", "W-NORTH", "200", "1.5"]
ADD_DOCK_D1 = ["add-dock", "D1", "500", "120"]
DOCK_ATLAS_AT_D1 = ["dock-vessel", "MV-ATLAS", "D1"]


@pytest.fixture(autouse=True)
def work_in_empty_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_register_vessel_reports_remaining_room() -> None:
    result = runner.invoke(app, REGISTER_ATLAS)
    assert result.exit_code == 0
    assert "room for 460 more units" in result.output


def test_register_vessel_over_capacity_fails_with_message() -> None:
    result = runner.invoke(app, REGISTER_OVERLOADED)
    assert result.exit_code == 1
    assert "between 0 and capacity" in result.output


def test_registering_the_same_ship_twice_fails() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    result = runner.invoke(app, REGISTER_ATLAS)
    assert result.exit_code == 1
    assert "already been registered" in result.output


def test_list_vessels_with_no_ships() -> None:
    result = runner.invoke(app, ["list-vessels"])
    assert result.exit_code == 0
    assert "no ships registered" in result.output


def test_list_vessels_shows_a_registered_ship() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    result = runner.invoke(app, ["list-vessels"])
    assert "MV-ATLAS  Atlas" in result.output


def test_add_dock_with_zero_size_fails_with_message() -> None:
    result = runner.invoke(app, ["add-dock", "D1", "0", "100"])
    assert result.exit_code == 1
    assert "positive" in result.output


def test_list_warehouses_shows_an_added_warehouse() -> None:
    runner.invoke(app, ADD_NORTH_WAREHOUSE)
    result = runner.invoke(app, ["list-warehouses"])
    assert result.exit_code == 0
    assert "W-NORTH  used 0/200  free 200" in result.output


def test_adding_the_same_warehouse_twice_fails() -> None:
    runner.invoke(app, ADD_NORTH_WAREHOUSE)
    result = runner.invoke(app, ADD_NORTH_WAREHOUSE)
    assert result.exit_code == 1
    assert "already registered" in result.output


def test_add_warehouse_with_zero_capacity_fails_with_message() -> None:
    result = runner.invoke(app, ["add-warehouse", "W-NORTH", "0", "1.5"])
    assert result.exit_code == 1
    assert "capacity must be positive" in result.output


def test_docked_ship_makes_its_dock_occupied() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    runner.invoke(app, ADD_DOCK_D1)
    result = runner.invoke(app, DOCK_ATLAS_AT_D1)
    assert result.exit_code == 0
    assert "Docked MV-ATLAS at D1" in result.output
    assert "Status: occupied" in runner.invoke(app, ["list-docks"]).output


def test_docking_an_unregistered_ship_fails_with_message() -> None:
    runner.invoke(app, ADD_DOCK_D1)
    result = runner.invoke(app, DOCK_ATLAS_AT_D1)
    assert result.exit_code == 1
    assert "not registered" in result.output


def test_docking_into_an_occupied_dock_fails() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    runner.invoke(app, ["register-vessel", "MV-NOVA", "Nova", "300"])
    runner.invoke(app, ADD_DOCK_D1)
    runner.invoke(app, DOCK_ATLAS_AT_D1)
    result = runner.invoke(app, ["dock-vessel", "MV-NOVA", "D1"])
    assert result.exit_code == 1
    assert "already occupied" in result.output


def test_register_vessel_with_invalid_arrival_time_fails() -> None:
    result = runner.invoke(app, [*REGISTER_ATLAS, "--arrival-time", "banana"])
    assert result.exit_code == 1
    assert "arrival time must look like" in result.output


def test_add_dock_with_nan_rate_fails_with_message() -> None:
    result = runner.invoke(app, ["add-dock", "D1", "500", "nan"])
    assert result.exit_code == 1
    assert "finite number" in result.output
