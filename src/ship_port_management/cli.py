from datetime import datetime
from pathlib import Path

import typer

from ship_port_management import cargo, dockings, docks, ships, warehouses
from ship_port_management.csv_handling import (
    read_dockings,
    read_docks,
    read_ships,
    read_warehouses,
    write_dockings,
    write_docks,
    write_ships,
    write_warehouses,
)

SHIPS_FILE = Path("data") / "ships.csv"
DOCKS_FILE = Path("data") / "docks.csv"
WAREHOUSES_FILE = Path("data") / "warehouses.csv"
DOCKINGS_FILE = Path("data") / "dockings.csv"
app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    pass


@app.command()
def register_vessel(
    ship_id: str, name: str, capacity: int, cargo_units: int = 0, arrival_time: str = ""
) -> None:
    arrival = arrival_time or datetime.now().isoformat(timespec="minutes")
    new_ship = ships.Ship(ship_id, name, arrival, capacity, cargo_units)
    try:
        registered_ships = read_ships(SHIPS_FILE)
        write_ships(SHIPS_FILE, ships.register_ship(new_ship, registered_ships))
    except (OSError, ValueError) as error:
        typer.echo(f"could not register {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    room = ships.remaining_capacity(new_ship)
    typer.echo(f"Registered {ship_id} ({name}), room for {room} more units")


@app.command()
def list_vessels() -> None:
    try:
        registered_ships = read_ships(SHIPS_FILE)
    except (OSError, ValueError) as error:
        typer.echo(f"could not read {SHIPS_FILE}: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not registered_ships:
        typer.echo("no ships registered")
        return
    for ship in registered_ships:
        typer.echo(ships.describe_ship(ship))


@app.command()
def add_dock(dock_id: str, max_ship_size: int, hourly_rate: float) -> None:
    new_dock = docks.Dock(dock_id, max_ship_size, hourly_rate)
    try:
        registered_docks = read_docks(DOCKS_FILE)
        write_docks(DOCKS_FILE, docks.add_dock(new_dock, registered_docks))
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
        registered_docks = read_docks(DOCKS_FILE)
        occupied = dockings.occupied_dock_ids(read_dockings(DOCKINGS_FILE))
    except (OSError, ValueError) as error:
        typer.echo(f"could not read the dock files: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not registered_docks:
        typer.echo("no docks registered")
        return
    for dock in registered_docks:
        typer.echo(docks.describe_dock(dock, occupied))


@app.command()
def dock_vessel(ship_id: str, dock_id: str) -> None:
    try:
        ship = ships.find_ship(ship_id, read_ships(SHIPS_FILE))
        dock = docks.find_dock(dock_id, read_docks(DOCKS_FILE))
        current_dockings = read_dockings(DOCKINGS_FILE)
        write_dockings(DOCKINGS_FILE, dockings.dock_ship(ship, dock, current_dockings))
    except (OSError, ValueError) as error:
        typer.echo(f"could not dock {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Docked {ship_id} at {dock_id}")


@app.command()
def add_warehouse(warehouse_id: str, capacity: int, daily_rate_per_unit: float) -> None:
    new_warehouse = warehouses.Warehouse(warehouse_id, capacity, daily_rate_per_unit)
    try:
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
        write_warehouses(
            WAREHOUSES_FILE, warehouses.add_warehouse(new_warehouse, registered_warehouses)
        )
    except (OSError, ValueError) as error:
        typer.echo(f"could not add warehouse {warehouse_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        f"Added warehouse {warehouse_id}, room for {capacity} units "
        f"at {daily_rate_per_unit} per unit per day"
    )


@app.command()
def list_warehouses() -> None:
    try:
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
    except (OSError, ValueError) as error:
        typer.echo(f"could not read {WAREHOUSES_FILE}: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not registered_warehouses:
        typer.echo("no warehouses registered")
        return
    for warehouse in registered_warehouses:
        typer.echo(warehouses.describe_warehouse(warehouse))


def save_cargo_move(
    move: cargo.CargoMove,
    registered_ships: list[ships.Ship],
    registered_warehouses: list[warehouses.Warehouse],
) -> None:
    write_ships(SHIPS_FILE, ships.replace_ship(move.ship, registered_ships))
    write_warehouses(
        WAREHOUSES_FILE, warehouses.replace_warehouse(move.warehouse, registered_warehouses)
    )


@app.command()
def unload_cargo(ship_id: str, warehouse_id: str, units: int) -> None:
    try:
        registered_ships = read_ships(SHIPS_FILE)
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
        move = cargo.unload_cargo(
            ships.find_ship(ship_id, registered_ships),
            warehouses.find_warehouse(warehouse_id, registered_warehouses),
            units,
            read_dockings(DOCKINGS_FILE),
        )
        save_cargo_move(move, registered_ships, registered_warehouses)
    except (OSError, ValueError) as error:
        typer.echo(f"could not unload {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Unloaded {units} units from {ship_id} into {warehouse_id}")


@app.command()
def load_cargo(ship_id: str, warehouse_id: str, units: int) -> None:
    try:
        registered_ships = read_ships(SHIPS_FILE)
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
        move = cargo.load_cargo(
            ships.find_ship(ship_id, registered_ships),
            warehouses.find_warehouse(warehouse_id, registered_warehouses),
            units,
            read_dockings(DOCKINGS_FILE),
        )
        save_cargo_move(move, registered_ships, registered_warehouses)
    except (OSError, ValueError) as error:
        typer.echo(f"could not load {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Loaded {units} units from {warehouse_id} onto {ship_id}")


if __name__ == "__main__":
    app()
