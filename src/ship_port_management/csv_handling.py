import csv
from pathlib import Path

from ship_port_management.dockings import Docking
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship
from ship_port_management.warehouses import Warehouse

SHIP_ID = 0
NAME = 1
ARRIVAL_TIME = 2
CAPACITY = 3
CARGO_UNITS = 4
HEADER = ["ship_id", "name", "arrival_time", "capacity", "cargo_units"]
FIELDS_PER_ROW = len(HEADER)

DOCK_ID = 0
MAX_SHIP_SIZE = 1
HOURLY_RATE = 2
DOCK_HEADER = ["dock_id", "max_ship_size", "hourly_rate"]
DOCK_FIELDS_PER_ROW = len(DOCK_HEADER)

WAREHOUSE_ID = 0
WAREHOUSE_CAPACITY = 1
DAILY_RATE_PER_UNIT = 2
STORED_UNITS = 3
WAREHOUSE_HEADER = ["warehouse_id", "capacity", "daily_rate_per_unit", "stored_units"]
WAREHOUSE_FIELDS_PER_ROW = len(WAREHOUSE_HEADER)

DOCKING_SHIP_ID = 0
DOCKING_DOCK_ID = 1
DOCKING_HEADER = ["ship_id", "dock_id"]
DOCKING_FIELDS_PER_ROW = len(DOCKING_HEADER)


def read_ships(path: Path) -> list[Ship]:
    if not path.exists():
        return []
    ships: list[Ship] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            ships.append(
                Ship(
                    ship_id=row[SHIP_ID],
                    name=row[NAME],
                    arrival_time=row[ARRIVAL_TIME],
                    capacity=int(row[CAPACITY]),
                    cargo_units=int(row[CARGO_UNITS]),
                )
            )
    return ships


def write_ships(path: Path, ships: list[Ship]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        for ship in ships:
            writer.writerow(
                [ship.ship_id, ship.name, ship.arrival_time, ship.capacity, ship.cargo_units]
            )


def read_docks(path: Path) -> list[Dock]:
    if not path.exists():
        return []
    docks: list[Dock] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != DOCK_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            docks.append(
                Dock(
                    dock_id=row[DOCK_ID],
                    max_ship_size=int(row[MAX_SHIP_SIZE]),
                    hourly_rate=float(row[HOURLY_RATE]),
                )
            )
    return docks


def write_docks(path: Path, docks: list[Dock]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(DOCK_HEADER)
        for dock in docks:
            writer.writerow([dock.dock_id, dock.max_ship_size, dock.hourly_rate])


def read_warehouses(path: Path) -> list[Warehouse]:
    if not path.exists():
        return []
    warehouses: list[Warehouse] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != WAREHOUSE_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            warehouses.append(
                Warehouse(
                    warehouse_id=row[WAREHOUSE_ID],
                    capacity=int(row[WAREHOUSE_CAPACITY]),
                    daily_rate_per_unit=float(row[DAILY_RATE_PER_UNIT]),
                    stored_units=int(row[STORED_UNITS]),
                )
            )
    return warehouses


def write_warehouses(path: Path, warehouses: list[Warehouse]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(WAREHOUSE_HEADER)
        for warehouse in warehouses:
            writer.writerow(
                [
                    warehouse.warehouse_id,
                    warehouse.capacity,
                    warehouse.daily_rate_per_unit,
                    warehouse.stored_units,
                ]
            )


def read_dockings(path: Path) -> list[Docking]:
    if not path.exists():
        return []
    dockings: list[Docking] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != DOCKING_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            dockings.append(Docking(ship_id=row[DOCKING_SHIP_ID], dock_id=row[DOCKING_DOCK_ID]))
    return dockings


def write_dockings(path: Path, dockings: list[Docking]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(DOCKING_HEADER)
        for docking in dockings:
            writer.writerow([docking.ship_id, docking.dock_id])
