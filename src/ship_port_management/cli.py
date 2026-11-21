import sys
from pathlib import Path

import typer

from ship_port_management import (
    cargo,
    departures,
    dockings,
    docks,
    ships,
    status,
    storage,
    warehouses,
)
from ship_port_management.csv_handling import (
    read_departures,
    read_dockings,
    read_docks,
    read_ships,
    read_stored_cargo,
    read_warehouses,
    write_departures,
    write_dockings,
    write_docks,
    write_ships,
    write_stored_cargo,
    write_warehouses,
)
from ship_port_management.times import current_time

SHIPS_FILE = Path("data") / "ships.csv"
DOCKS_FILE = Path("data") / "docks.csv"
WAREHOUSES_FILE = Path("data") / "warehouses.csv"
DOCKINGS_FILE = Path("data") / "dockings.csv"
STORED_CARGO_FILE = Path("data") / "stored_cargo.csv"
DEPARTURES_FILE = Path("data") / "departures.csv"
app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.command()
def register_vessel(
    ship_id: str, name: str, capacity: int, cargo_units: int = 0, arrival_time: str = ""
) -> None:
    """Register a ship that has arrived at the port."""
    arrival = arrival_time or current_time()
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
    """List every registered ship and the cargo on board."""
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
    """Add a dock with the largest ship capacity it takes and its hourly rate."""
    new_dock = docks.Dock(dock_id, max_ship_size, hourly_rate)
    try:
        registered_docks = read_docks(DOCKS_FILE)
        write_docks(DOCKS_FILE, docks.add_dock(new_dock, registered_docks))
    except (OSError, ValueError) as error:
        typer.echo(f"could not add dock {dock_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        f"Added dock {dock_id}, takes ships up to {max_ship_size} units at {hourly_rate} per hour"
    )


@app.command()
def list_docks() -> None:
    """List every dock and whether it is available or occupied."""
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
def dock_vessel(ship_id: str, dock_id: str, docked_at: str = "") -> None:
    """Dock a registered ship at a free dock that fits it."""
    docking_time = docked_at or current_time()
    try:
        ship = ships.find_ship(ship_id, read_ships(SHIPS_FILE))
        dock = docks.find_dock(dock_id, read_docks(DOCKS_FILE))
        current_dockings = read_dockings(DOCKINGS_FILE)
        new_dockings = dockings.dock_ship(ship, dock, docking_time, current_dockings)
        departures.check_docked_after_last_departure(
            ship_id, docking_time, read_departures(DEPARTURES_FILE)
        )
        write_dockings(DOCKINGS_FILE, new_dockings)
    except (OSError, ValueError) as error:
        typer.echo(f"could not dock {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Docked {ship_id} at {dock_id}")


@app.command()
def depart_vessel(ship_id: str, departed_at: str = "") -> None:
    """Let a docked ship leave, free its dock and charge the docking fee."""
    departure_time = departed_at or current_time()
    try:
        result = departures.depart_ship(
            ship_id, departure_time, read_dockings(DOCKINGS_FILE), read_docks(DOCKS_FILE)
        )
        departures.check_departed_after_last_unload(
            ship_id,
            result.departure.docked_at,
            departure_time,
            read_stored_cargo(STORED_CARGO_FILE),
        )
        recorded_departures = read_departures(DEPARTURES_FILE)
        write_dockings(DOCKINGS_FILE, result.dockings)
        write_departures(DEPARTURES_FILE, recorded_departures + [result.departure])
    except (OSError, ValueError) as error:
        typer.echo(f"could not depart {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(departures.describe_departure(result.departure))


@app.command()
def add_warehouse(warehouse_id: str, capacity: int, daily_rate_per_unit: float) -> None:
    """Add a warehouse with its capacity and daily rate per unit."""
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
    """List every warehouse with its used and free units."""
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
    stored_cargo: list[storage.StoredCargo],
) -> None:
    write_ships(SHIPS_FILE, ships.replace_ship(move.ship, registered_ships))
    write_warehouses(
        WAREHOUSES_FILE, warehouses.replace_warehouse(move.warehouse, registered_warehouses)
    )
    write_stored_cargo(STORED_CARGO_FILE, stored_cargo)


@app.command()
def unload_cargo(ship_id: str, warehouse_id: str, units: int, stored_at: str = "") -> None:
    """Move cargo from a docked ship into a warehouse."""
    storage_time = stored_at or current_time()
    try:
        registered_ships = read_ships(SHIPS_FILE)
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
        current_dockings = read_dockings(DOCKINGS_FILE)
        move = cargo.unload_cargo(
            ships.find_ship(ship_id, registered_ships),
            warehouses.find_warehouse(warehouse_id, registered_warehouses),
            units,
            current_dockings,
        )
        storage.check_stored_after_docking(
            storage_time, departures.find_docking(ship_id, current_dockings).docked_at
        )
        new_cargo = storage.StoredCargo(ship_id, warehouse_id, units, storage_time)
        stored_cargo = storage.store_cargo(new_cargo, read_stored_cargo(STORED_CARGO_FILE))
        save_cargo_move(move, registered_ships, registered_warehouses, stored_cargo)
    except (OSError, ValueError) as error:
        typer.echo(f"could not unload {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Unloaded {units} units from {ship_id} into {warehouse_id}")


@app.command()
def load_cargo(ship_id: str, warehouse_id: str, units: int) -> None:
    """Move cargo from a warehouse onto a docked ship, the ship's own cargo first."""
    try:
        registered_ships = read_ships(SHIPS_FILE)
        registered_warehouses = read_warehouses(WAREHOUSES_FILE)
        move = cargo.load_cargo(
            ships.find_ship(ship_id, registered_ships),
            warehouses.find_warehouse(warehouse_id, registered_warehouses),
            units,
            read_dockings(DOCKINGS_FILE),
        )
        stored_cargo = storage.take_cargo(
            ship_id, warehouse_id, units, read_stored_cargo(STORED_CARGO_FILE)
        )
        save_cargo_move(move, registered_ships, registered_warehouses, stored_cargo)
    except (OSError, ValueError) as error:
        typer.echo(f"could not load {ship_id}: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Loaded {units} units from {warehouse_id} onto {ship_id}")


@app.command()
def storage_fees(as_of: str = "") -> None:
    """Show the storage fee each ship owes for its cargo in storage."""
    fee_time = as_of or current_time()
    try:
        fees = storage.fees_by_ship(
            read_stored_cargo(STORED_CARGO_FILE), read_warehouses(WAREHOUSES_FILE), fee_time
        )
    except (OSError, ValueError) as error:
        typer.echo(f"could not calculate storage fees: {error}", err=True)
        raise typer.Exit(code=1) from None
    if not fees:
        typer.echo("no cargo in storage")
        return
    for ship_id, fee in fees.items():
        typer.echo(storage.describe_storage_fee(ship_id, fee))


@app.command()
def port_status() -> None:
    """Show every ship and its dock, the free docks and how full each warehouse is."""
    try:
        lines = status.format_port_status(
            read_ships(SHIPS_FILE),
            read_docks(DOCKS_FILE),
            read_warehouses(WAREHOUSES_FILE),
            read_dockings(DOCKINGS_FILE),
        )
    except (OSError, ValueError) as error:
        typer.echo(f"could not show the port status: {error}", err=True)
        raise typer.Exit(code=1) from None
    for line in lines:
        typer.echo(line)


def require_terminal(command: str) -> None:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        typer.echo(f"{command} needs a terminal: with Docker, run it with docker run -it", err=True)
        raise typer.Exit(code=1)


@app.command()
def tui() -> None:
    """Open the terminal interface with tabs for ships, docks, warehouses and fees."""
    require_terminal("tui")
    from ship_port_management.tui import HarbourApp

    HarbourApp().run()


if __name__ == "__main__":
    app()
