import typer

from ship_port_management.ships import cargo_within_capacity

app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    pass


@app.command()
def register_vessel(ship_id: str, capacity: int, cargo_units: int = 0) -> None:
    if not cargo_within_capacity(capacity, cargo_units):
        typer.echo("cargo units must be between 0 and capacity", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Ship {ship_id} has room for {capacity - cargo_units} more units")


if __name__ == "__main__":
    app()
