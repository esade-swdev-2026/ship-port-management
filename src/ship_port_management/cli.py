import typer

from ship_port_management.port import Ship, remaining_capacity

app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    """Track ships, docks and cargo in a port."""


@app.command()
def register_vessel(imo: str, capacity: int, cargo_units: int = 0) -> None:
    if cargo_units > capacity:
        typer.echo("cargo units can't exceed capacity", err=True)
        raise typer.Exit(code=1)
    ship = Ship(imo, capacity, cargo_units)
    typer.echo(f"Registered ship {ship.imo} with room for {remaining_capacity(ship)} more units")


if __name__ == "__main__":
    app()
