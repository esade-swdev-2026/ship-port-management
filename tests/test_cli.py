from pathlib import Path

import pytest
from typer.testing import CliRunner

from ship_port_management.cli import app

runner = CliRunner()

REGISTER_ATLAS = ["register-vessel", "MV-ATLAS", "Atlas", "500", "--cargo-units", "40"]
REGISTER_OVERLOADED = ["register-vessel", "MV-ATLAS", "Atlas", "40", "--cargo-units", "500"]


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
