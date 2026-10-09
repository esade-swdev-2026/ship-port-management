from typer.testing import CliRunner

from ship_port_management.cli import app

runner = CliRunner()


def test_register_vessel_succeeds_within_capacity() -> None:
    result = runner.invoke(app, ["MV-ATLAS", "500", "--cargo-units", "40"])
    assert result.exit_code == 0


def test_register_vessel_fails_over_capacity() -> None:
    result = runner.invoke(app, ["MV-ATLAS", "40", "--cargo-units", "500"])
    assert result.exit_code == 1
