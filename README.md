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
tools, from `uv.lock` the committed file that pins exact versions so every teammate
and CI resolve the same ones. When you change a dependency in `pyproject.toml`, run
`uv lock` and commit the updated `uv.lock`; CI fails if the two disagree.

## Use

Register a ship, then list the ships in the port:

```bash
uv run ship-port-management register-vessel MV-ATLAS Atlas 500 --cargo-units 40 --arrival-time 2026-10-18T09:30
uv run ship-port-management list-vessels
```

```
Registered MV-ATLAS (Atlas), room for 460 more units
MV-ATLAS  Atlas  arrived 2026-10-18T09:30  cargo 40/500
```

| Command | What it does |
|---|---|
| `register-vessel SHIP_ID NAME CAPACITY` | Adds a ship to the port |
| `--cargo-units N` | Cargo on board (default 0) |
| `--arrival-time TIME` | When it arrived, e.g. `2026-10-18T09:30` (default now) |
| `list-vessels` | Shows every ship in the port |
| `--help` | Shows all commands and options |

Ships are saved in `data/ships.csv`. Delete the `data` folder to start with an empty port.

Bad input is refused with a message and exit code 1, for example cargo over capacity:

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
pyproject.toml              dependencies and tool configuration, the single source of truth
```

## Use of AI
```
We used Claude as an assistant while building this project: to explain course concepts, plan the structure, review our code and suggest code snippets. Every change was written into the files, checked with ruff, mypy and pytest, and reviewed by the team before it was merged.
```