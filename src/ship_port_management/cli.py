from datetime import datetime

import typer

from ship_port_management.ships import Ship, cargo_within_capacity, remaining_capacity

app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    pass


@app.command()
def register_vessel(ship_id: str, name: str, capacity: int, cargo_units: int = 0) -> None:
    arrival_time = datetime.now().isoformat(timespec="minutes")
    ship = Ship(ship_id, name, arrival_time, capacity, cargo_units)
    if not cargo_within_capacity(ship):
        typer.echo("cargo units must be between 0 and capacity", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Ship {ship_id} has room for {remaining_capacity(ship)} more units")


if __name__ == "__main__":
    app()
