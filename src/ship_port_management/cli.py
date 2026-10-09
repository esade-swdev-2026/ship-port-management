import typer

app = typer.Typer(help="Track ships, docks and cargo in a port.")


@app.callback()
def main() -> None:
    pass


@app.command()
def register_vessel(imo: str, capacity: int, cargo_units: int = 0) -> None:
    if cargo_units > capacity:
        typer.echo("cargo units can't exceed capacity", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Ship {imo} has room for {capacity - cargo_units} more units")


if __name__ == "__main__":
    app()
