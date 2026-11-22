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
DOCK_ATLAS_AT_TEN = [*DOCK_ATLAS_AT_D1, "--docked-at", "2026-10-18T10:00"]
DEPART_ATLAS = ["depart-vessel", "MV-ATLAS", "--departed-at", "2026-10-18T15:20"]


@pytest.fixture(autouse=True)
def work_in_empty_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_register_vessel_reports_remaining_room() -> None:
    result = runner.invoke(app, REGISTER_ATLAS)
    assert result.exit_code == 0
    assert "room for 460 more units" in result.output


def test_help_describes_each_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "List every dock" in result.output
    assert "Move cargo from a docked ship" in result.output


def test_register_vessel_over_capacity_fails_with_message() -> None:
    result = runner.invoke(app, REGISTER_OVERLOADED)
    assert result.exit_code == 1
    assert "between 0 and capacity" in result.output


def test_registering_the_same_ship_twice_fails() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    result = runner.invoke(app, REGISTER_ATLAS)
    assert result.exit_code == 1
    assert "is already registered" in result.output


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
    assert "per hour  occupied" in runner.invoke(app, ["list-docks"]).output


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


def test_docking_with_invalid_time_fails_with_message() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    runner.invoke(app, ADD_DOCK_D1)
    result = runner.invoke(app, [*DOCK_ATLAS_AT_D1, "--docked-at", "banana"])
    assert result.exit_code == 1
    assert "docking time" in result.output


def test_register_vessel_with_invalid_arrival_time_fails() -> None:
    result = runner.invoke(app, [*REGISTER_ATLAS, "--arrival-time", "banana"])
    assert result.exit_code == 1
    assert "arrival time must look like" in result.output


def test_add_dock_with_nan_rate_fails_with_message() -> None:
    result = runner.invoke(app, ["add-dock", "D1", "500", "nan"])
    assert result.exit_code == 1
    assert "finite number" in result.output


def dock_atlas_at_ten() -> None:
    runner.invoke(app, [*REGISTER_ATLAS, "--arrival-time", "2026-10-18T09:30"])
    runner.invoke(app, ADD_DOCK_D1)
    runner.invoke(app, DOCK_ATLAS_AT_TEN)


def test_depart_vessel_shows_the_docking_fee() -> None:
    dock_atlas_at_ten()
    result = runner.invoke(app, DEPART_ATLAS)
    assert result.exit_code == 0
    assert "MV-ATLAS left D1 after 6 hours, docking fee 720.00" in result.output


def test_departed_ship_makes_its_dock_available() -> None:
    dock_atlas_at_ten()
    runner.invoke(app, DEPART_ATLAS)
    assert "per hour  available" in runner.invoke(app, ["list-docks"]).output


def test_departed_ship_can_dock_again() -> None:
    dock_atlas_at_ten()
    runner.invoke(app, DEPART_ATLAS)
    result = runner.invoke(app, [*DOCK_ATLAS_AT_D1, "--docked-at", "2026-10-19T08:00"])
    assert result.exit_code == 0
    assert "Docked MV-ATLAS at D1" in result.output


def test_docking_again_before_the_last_departure_fails() -> None:
    dock_atlas_at_ten()
    runner.invoke(app, DEPART_ATLAS)
    result = runner.invoke(app, [*DOCK_ATLAS_AT_D1, "--docked-at", "2026-10-18T12:00"])
    assert result.exit_code == 1
    assert "can't be before the last departure" in result.output
    assert "available" in runner.invoke(app, ["list-docks"]).output


def test_departing_an_undocked_ship_fails_with_message() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    result = runner.invoke(app, ["depart-vessel", "MV-ATLAS"])
    assert result.exit_code == 1
    assert "is not docked" in result.output


def test_departing_before_docking_keeps_the_dock_occupied() -> None:
    dock_atlas_at_ten()
    result = runner.invoke(app, ["depart-vessel", "MV-ATLAS", "--departed-at", "2026-10-18T09:45"])
    assert result.exit_code == 1
    assert "before docking time" in result.output
    assert "per hour  occupied" in runner.invoke(app, ["list-docks"]).output


def test_departing_with_a_corrupt_departures_file_keeps_the_dock_occupied() -> None:
    dock_atlas_at_ten()
    Path("data/departures.csv").write_text("ship_id,dock_id\nMV-NOVA\n")
    result = runner.invoke(app, DEPART_ATLAS)
    assert result.exit_code == 1
    assert "malformed row" in result.output
    assert "per hour  occupied" in runner.invoke(app, ["list-docks"]).output


def dock_atlas_next_to_north_warehouse() -> None:
    dock_atlas_at_ten()
    runner.invoke(app, ADD_NORTH_WAREHOUSE)


def test_unload_cargo_moves_units_into_the_warehouse() -> None:
    dock_atlas_next_to_north_warehouse()
    result = runner.invoke(app, ["unload-cargo", "MV-ATLAS", "W-NORTH", "30"])
    assert result.exit_code == 0
    assert "used 30/200" in runner.invoke(app, ["list-warehouses"]).output
    assert "cargo 10/500" in runner.invoke(app, ["list-vessels"]).output


def test_load_cargo_moves_units_onto_the_ship() -> None:
    dock_atlas_next_to_north_warehouse()
    runner.invoke(app, ["unload-cargo", "MV-ATLAS", "W-NORTH", "30"])
    result = runner.invoke(app, ["load-cargo", "MV-ATLAS", "W-NORTH", "20"])
    assert result.exit_code == 0
    assert "used 10/200" in runner.invoke(app, ["list-warehouses"]).output


def test_unload_cargo_from_undocked_ship_fails() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    runner.invoke(app, ADD_NORTH_WAREHOUSE)
    result = runner.invoke(app, ["unload-cargo", "MV-ATLAS", "W-NORTH", "10"])
    assert result.exit_code == 1
    assert "not docked" in result.output


def test_port_status_of_empty_port() -> None:
    result = runner.invoke(app, ["port-status"])
    assert result.exit_code == 0
    assert "none" in result.output


def test_port_status_shows_a_docked_ship() -> None:
    runner.invoke(app, REGISTER_ATLAS)
    runner.invoke(app, ADD_DOCK_D1)
    runner.invoke(app, DOCK_ATLAS_AT_D1)
    result = runner.invoke(app, ["port-status"])
    assert result.exit_code == 0
    assert "MV-ATLAS  Atlas  at dock D1" in result.output


def test_port_status_with_corrupt_warehouse_file_fails_cleanly() -> None:
    Path("data").mkdir()
    Path("data/warehouses.csv").write_text("warehouse_id,capacity,daily_rate,stored\nW1,0,1.5,0\n")
    result = runner.invoke(app, ["port-status"])
    assert result.exit_code == 1
    assert "capacity must be positive, got 0" in result.output


def test_storage_fees_with_no_cargo_stored() -> None:
    result = runner.invoke(app, ["storage-fees"])
    assert result.exit_code == 0
    assert "no cargo in storage" in result.output


def test_storage_fees_charge_unloaded_cargo_after_the_free_period() -> None:
    dock_atlas_next_to_north_warehouse()
    unload = ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "2026-10-18T10:00"]
    runner.invoke(app, unload)
    result = runner.invoke(app, ["storage-fees", "--as-of", "2026-10-23T10:00"])
    assert result.exit_code == 0
    assert "MV-ATLAS owes 90.00 for storage" in result.output


def test_loaded_cargo_is_no_longer_charged() -> None:
    dock_atlas_next_to_north_warehouse()
    unload = ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "2026-10-18T10:00"]
    runner.invoke(app, unload)
    runner.invoke(app, ["load-cargo", "MV-ATLAS", "W-NORTH", "30"])
    result = runner.invoke(app, ["storage-fees", "--as-of", "2026-10-23T10:00"])
    assert "no cargo in storage" in result.output


def test_unload_cargo_with_invalid_storage_time_changes_nothing() -> None:
    dock_atlas_next_to_north_warehouse()
    result = runner.invoke(
        app, ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "soon"]
    )
    assert result.exit_code == 1
    assert "must look like" in result.output
    assert "used 0/200" in runner.invoke(app, ["list-warehouses"]).output


def test_unloading_cargo_stored_before_the_ship_docked_changes_nothing() -> None:
    dock_atlas_next_to_north_warehouse()
    unload = ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "2026-10-18T09:00"]
    result = runner.invoke(app, unload)
    assert result.exit_code == 1
    assert "can't be before docking time" in result.output
    assert "used 0/200" in runner.invoke(app, ["list-warehouses"]).output


def test_departing_before_the_last_unload_keeps_the_ship_docked() -> None:
    dock_atlas_next_to_north_warehouse()
    unload = ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "2026-10-25T10:00"]
    runner.invoke(app, unload)
    depart = ["depart-vessel", "MV-ATLAS", "--departed-at", "2026-10-19T10:00"]
    result = runner.invoke(app, depart)
    assert result.exit_code == 1
    assert "can't be before the last unload" in result.output
    assert "occupied" in runner.invoke(app, ["list-docks"]).output


def test_visit_history_with_no_departures() -> None:
    result = runner.invoke(app, ["visit-history"])
    assert result.exit_code == 0
    assert "no visits yet" in result.output


def test_visit_history_shows_the_cargo_moved_and_the_fee() -> None:
    dock_atlas_next_to_north_warehouse()
    unload = ["unload-cargo", "MV-ATLAS", "W-NORTH", "30", "--stored-at", "2026-10-18T11:00"]
    runner.invoke(app, unload)
    runner.invoke(app, ["load-cargo", "MV-ATLAS", "W-NORTH", "10"])
    runner.invoke(app, DEPART_ATLAS)
    result = runner.invoke(app, ["visit-history"])
    assert result.exit_code == 0
    assert (
        "MV-ATLAS  at D1 from 2026-10-18T10:00 to 2026-10-18T15:20  "
        "unloaded 30  loaded 10  docking fee 720.00"
    ) in result.output


def test_visit_history_with_a_corrupt_transfers_file_fails_cleanly() -> None:
    Path("data").mkdir()
    Path("data/cargo_transfers.csv").write_text("ship_id,docked_at\nMV-ATLAS\n")
    result = runner.invoke(app, ["visit-history"])
    assert result.exit_code == 1
    assert "could not show the visit history" in result.output


def test_storage_fees_with_invalid_time_fails_with_message() -> None:
    result = runner.invoke(app, ["storage-fees", "--as-of", "later"])
    assert result.exit_code == 1
    assert "fee time must look like" in result.output


@pytest.mark.parametrize("command", ["tui", "tutor"])
def test_interface_without_a_terminal_says_how_to_run_it(command: str) -> None:
    result = runner.invoke(app, [command])
    assert result.exit_code == 1
    assert f"{command} needs a terminal: with Docker, run it with docker run -it" in result.output
