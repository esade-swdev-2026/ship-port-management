# Ship Port Management

A command-line tool for port managers: register the ships arriving at the port and list
the ships that are there. Invalid input, such as a ship registered twice or cargo over
the ship's capacity, is refused with a clear message.

Also tracks different docks that ships can stay at. Any invalid input, such as 
adding 2 docks with the same dock_id is refused clearly. A ship can be docked at a
free dock that is big enough for it, and a dock never holds two ships at once.

Also tracks warehouses (storage areas) for cargo, with how many units each one has
used and free. A docked ship can unload cargo into a warehouse or load cargo from
one, never more than the ship carries, the warehouse holds, or either has room for.
Cargo kept in a warehouse is free for the first 3 days; after that each ship is charged
the warehouse's daily rate for every unit of its cargo, for every full day past the free period.

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

Register a ship, dock it, add a warehouse, then move cargo between them:

```bash
uv run ship-port-management register-vessel MV-ATLAS Atlas 500 --cargo-units 40 --arrival-time 2026-10-18T09:30
uv run ship-port-management list-vessels

uv run ship-port-management add-dock D1 500 120
uv run ship-port-management dock-vessel MV-ATLAS D1
uv run ship-port-management list-docks

uv run ship-port-management add-warehouse W-NORTH 200 1.5
uv run ship-port-management unload-cargo MV-ATLAS W-NORTH 30 --stored-at 2026-10-18T10:00
uv run ship-port-management load-cargo MV-ATLAS W-NORTH 10
uv run ship-port-management list-warehouses
uv run ship-port-management storage-fees --as-of 2026-10-23T10:00
```

```
Registered MV-ATLAS (Atlas), room for 460 more units
MV-ATLAS  Atlas  arrived 2026-10-18T09:30  cargo 40/500

Dock D1 successfully added (Max ship size: 500, hourly rate: 120.0)
Docked MV-ATLAS at D1
Dock id: D1, Max ship size = 500, Hourly rate: 120.0, Status: occupied

Added warehouse W-NORTH, room for 200 units at 1.5 per unit per day
Unloaded 30 units from MV-ATLAS into W-NORTH
Loaded 10 units from W-NORTH onto MV-ATLAS
W-NORTH  used 20/200  free 180  rate 1.5 per unit per day
MV-ATLAS owes 60.00 for storage
```

| Command | What it does |
|---|---|
| `register-vessel SHIP_ID NAME CAPACITY` | Adds a ship to the port |
| `--cargo-units N` | Cargo on board (default 0) |
| `--arrival-time TIME` | When it arrived, e.g. `2026-10-18T09:30` (default now) |
| `list-vessels` | Shows every ship in the port |
| `add-dock DOCK_ID MAX_SHIP_SIZE HOURLY_RATE` | Adds a dock (max ship size in cargo units, rate per hour) |
| `dock-vessel SHIP_ID DOCK_ID` | Docks a registered ship at a free dock that fits its size |
| ⁠ --docked-at TIME ⁠ | When it docked, e.g. ⁠ 2026-11-03T10:00 ⁠ (default now); not before the ship's arrival |
| `list-docks` | Shows every dock and if it is available or occupied |
| `add-warehouse WAREHOUSE_ID CAPACITY DAILY_RATE_PER_UNIT` | Adds a warehouse (capacity in cargo units, rate per unit per day) |
| `list-warehouses` | Shows every warehouse with its used and free units |
| `unload-cargo SHIP_ID WAREHOUSE_ID UNITS` | Moves cargo from a docked ship into a warehouse |
| `--stored-at TIME` | When the cargo went into storage, e.g. `2026-10-18T10:00` (default now) |
| `load-cargo SHIP_ID WAREHOUSE_ID UNITS` | Moves cargo from a warehouse onto a docked ship, taking that ship's own cargo first, oldest first |
| `storage-fees` | Shows the storage fee each ship owes for its cargo in storage |
| `--as-of TIME` | When to calculate the fees up to (default now) |
| `port-status` | Shows every ship and its dock, the free docks and how full each warehouse is |
| `--help` | Shows all commands and options |


Ships are saved in `data/ships.csv`, docks in `data/docks.csv`, which ship is at which
dock in `data/dockings.csv`, warehouses in `data/warehouses.csv` and which ship's cargo
is in which warehouse since when in `data/stored_cargo.csv`. Delete the `data` folder to start with an empty port.

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
  dockings.py               Docking a ship: size check, no double booking
  cargo.py                  Loading and unloading cargo between docked ships and warehouses
  warehouses.py             Warehouse (storage area): capacity, used and free units
  storage.py                Whose cargo is stored where since when, and the storage fees owed
  times.py                  Reading and checking times like 2026-10-18T09:30, and the current time
  csv_handling.py           reads and writes the ships, docks, dockings, warehouses and stored cargo CSV files
  __main__.py               lets `python -m ship_port_management` work
tests/                      pytest tests, one file per module
pyproject.toml              dependencies and tool configuration, the single source of truth
```

## Use of AI
```
We used Claude as an assistant while building this project: to explain course concepts, plan
the structure, review our code, suggest code snippets, write in .md, and help when we got lost with git. Every change was written into the
files, checked with ruff, mypy and pytest, and reviewed by the team before it was merged.
```
