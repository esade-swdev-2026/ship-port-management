from datetime import datetime
from pathlib import Path

import typer

from ship_port_management.csv_handling import read_docks, read_ships, write_docks, write_ships
from ship_port_management.docks import Dock, add_dock, describe_dock
from ship_port_management.ships import Ship, describe_ship, register_ship, remaining_capacity

DATA_FILE = Path("data") / "ships.csv"
DOCKS_FILE = Path("data") / "docks.csv"
app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    pass


@app.command()
def register_vessel(
    ship_id: str, name: str, capacity: int, cargo_units: int = 0, arrival_time: str = ""
) -> None:
    arrival = arrival_time or datetime.now().isoformat(timespec="minutes")
    new_ship = Ship(ship_id, name, arrival, capacity, cargo_units)
    try:
        registered = read_ships(DATA_FILE)
        write_ships(DATA_FILE, register_ship(new_ship, registered))
    except (OSError, ValueError) as error:
        typer.echo(f"could not register {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    room = remaining_capacity(new_ship)
    typer.echo(f"Registered {ship_id} ({name}), room for {room} more units")


@app.command()
def list_vessels() -> None:
    try:
        ships = read_ships(DATA_FILE)
    except (OSError, ValueError) as error:
        typer.echo(f"could not read {DATA_FILE}: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not ships:
        typer.echo("no ships registered")
        return
    for ship in ships:
        typer.echo(describe_ship(ship))


@app.command(name="add-dock")
def add_new_dock(dock_id: str, max_ship_size: int, hourly_rate: float) -> None:
    new_dock = Dock(dock_id, max_ship_size, hourly_rate)
    try:
        existing = read_docks(DOCKS_FILE)
        write_docks(DOCKS_FILE, add_dock(existing, new_dock))
    except (OSError, ValueError) as error:
        typer.echo(f"could not add dock {dock_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        f"Dock {dock_id} successfully added (Max ship size: {max_ship_size}, "
        f"hourly rate: {hourly_rate})"
    )


@app.command()
def list_docks() -> None:
    try:
        docks = read_docks(DOCKS_FILE)
    except (OSError, ValueError) as error:
        typer.echo(f"could not read {DOCKS_FILE}: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not docks:
        typer.echo("no docks registered")
        return
    for dock in docks:
        typer.echo(describe_dock(dock, set()))


if __name__ == "__main__":
    app()
