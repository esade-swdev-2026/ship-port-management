import typer

app = typer.Typer(help="Replace this with your project's command-line interface.")


@app.command()
def register_vessel(imo: str, capacity: int, cargo_units: int = 0) -> None:
    if cargo_units > capacity:
        typer.echo("cago units can't exceed capacity", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Ship {imo} has {abs(cargo_units - capacity)} too many units")


if __name__ == "__main__":
    app()
