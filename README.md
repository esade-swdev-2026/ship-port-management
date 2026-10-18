# Ship Port Management

A command-line tool for port managers: register the ships arriving at the port and list
the ships that are there. Invalid input, such as a ship registered twice or cargo over
the ship's capacity, is dtected refused with a clear message.

## Who is this for 
This project is for port managers to track the activity in their ports, while making sure incoming movement is valid. 

## Install

```bash
git clone https://github.com/esade-swdev-2026/ship-port-management.git
cd ship-port-management
uv sync
```

This creates a virtual environment and installs everything, including the development
tools, from `uv.lock` — the committed file that pins exact versions so every teammate
and CI resolve the same ones. When you change a dependency in `pyproject.toml`, run
`uv lock` and commit the updated `uv.lock`; CI fails if the two disagree.

## Run

```bash
uv run ship-port-management --help
uv run ship-port-management register-vessel MV-ATLAS 500 --cargo-units 40 --arrival-time 2026-10-18T09:30
uv run ship-port-management list-vessels
```

What you should see is:

```
Registered MV-ATLAS (Atlas), room for 460 more units
MV-ATLAS  Atlas  arrived 2026-10-18T09:30  cargo 40/500
```

Ships are saved in `data/ships.csv`, which is created on first use and ignored by git.
`--cargo-units` defaults to 0 and `--arrival-time` defaults to now. To start again with
an empty port, delete the folder: `rm -rf data`.

Bad input is refused with a message and exit code 1, never a traceback:

```bash
uv run ship-port-management register-vessel MV-NOVA Nova 40 --cargo-units 500
```

```
could not register MV-NOVA: cargo units must be between 0 and capacity
```

## Develop

```bash
uv run ruff check .          # lint
uv run ruff format .         # format (CI runs `--check` and fails on a diff)
uv run mypy src tests        # types
uv run pytest                # tests
```

These four commands are exactly what `.github/workflows/check.yml` runs on every push.
If they pass here, CI passes.

## Layout

```
src/ship_port_management/   the package
  cli.py                    typer commands: the only module that prints or exits
  ships.py                  Ship and the rules for registering one
  docks.py                  Dock and the rules for adding one
  warehouses.py             Warehouse (storage area): capacity, used and free units
  csv_handling.py           reads and writes data/ships.csv
  __main__.py               lets `python -m ship_port_management` work
tests/                      pytest tests, one file per module
pyproject.toml              dependencies and tool configuration — the single source of truth
```