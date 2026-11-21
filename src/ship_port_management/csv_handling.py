import csv
from pathlib import Path

from ship_port_management.departures import Departure, record_departure
from ship_port_management.dockings import Docking, record_docking
from ship_port_management.docks import Dock, add_dock
from ship_port_management.ships import Ship, register_ship
from ship_port_management.storage import StoredCargo, store_cargo
from ship_port_management.warehouses import Warehouse, add_warehouse

SHIP_ID = 0
SHIP_NAME = 1
SHIP_ARRIVAL_TIME = 2
SHIP_CAPACITY = 3
SHIP_CARGO_UNITS = 4
SHIP_HEADER = ["ship_id", "name", "arrival_time", "capacity", "cargo_units"]
SHIP_FIELDS_PER_ROW = len(SHIP_HEADER)

DOCK_ID = 0
DOCK_MAX_SHIP_SIZE = 1
DOCK_HOURLY_RATE = 2
DOCK_HEADER = ["dock_id", "max_ship_size", "hourly_rate"]
DOCK_FIELDS_PER_ROW = len(DOCK_HEADER)

WAREHOUSE_ID = 0
WAREHOUSE_CAPACITY = 1
WAREHOUSE_DAILY_RATE_PER_UNIT = 2
WAREHOUSE_STORED_UNITS = 3
WAREHOUSE_HEADER = ["warehouse_id", "capacity", "daily_rate_per_unit", "stored_units"]
WAREHOUSE_FIELDS_PER_ROW = len(WAREHOUSE_HEADER)

DOCKING_SHIP_ID = 0
DOCKING_DOCK_ID = 1
DOCKING_DOCKED_AT = 2
DOCKING_HEADER = ["ship_id", "dock_id", "docked_at"]
DOCKING_FIELDS_PER_ROW = len(DOCKING_HEADER)

STORED_CARGO_SHIP_ID = 0
STORED_CARGO_WAREHOUSE_ID = 1
STORED_CARGO_UNITS = 2
STORED_CARGO_AT = 3
STORED_CARGO_HEADER = ["ship_id", "warehouse_id", "units", "stored_at"]
STORED_CARGO_FIELDS_PER_ROW = len(STORED_CARGO_HEADER)

DEPARTURE_SHIP_ID = 0
DEPARTURE_DOCK_ID = 1
DEPARTURE_DOCKED_AT = 2
DEPARTURE_DEPARTED_AT = 3
DEPARTURE_HOURS = 4
DEPARTURE_DOCKING_FEE = 5
DEPARTURE_HEADER = ["ship_id", "dock_id", "docked_at", "departed_at", "hours", "docking_fee"]
DEPARTURE_FIELDS_PER_ROW = len(DEPARTURE_HEADER)


def whole_number(text: str, column: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{column} must be a whole number, got {text!r}") from None


def decimal_number(text: str, column: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{column} must be a number, got {text!r}") from None


def read_ships(path: Path) -> list[Ship]:
    if not path.exists():
        return []
    ships: list[Ship] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != SHIP_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            try:
                ship = Ship(
                    ship_id=row[SHIP_ID],
                    name=row[SHIP_NAME],
                    arrival_time=row[SHIP_ARRIVAL_TIME],
                    capacity=whole_number(row[SHIP_CAPACITY], "capacity"),
                    cargo_units=whole_number(row[SHIP_CARGO_UNITS], "cargo units"),
                )
                ships = register_ship(ship, ships)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
    return ships


def write_ships(path: Path, ships: list[Ship]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SHIP_HEADER)
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
            try:
                dock = Dock(
                    dock_id=row[DOCK_ID],
                    max_ship_size=whole_number(row[DOCK_MAX_SHIP_SIZE], "max ship size"),
                    hourly_rate=decimal_number(row[DOCK_HOURLY_RATE], "hourly rate"),
                )
                docks = add_dock(dock, docks)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
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
            try:
                warehouse = Warehouse(
                    warehouse_id=row[WAREHOUSE_ID],
                    capacity=whole_number(row[WAREHOUSE_CAPACITY], "capacity"),
                    daily_rate_per_unit=decimal_number(
                        row[WAREHOUSE_DAILY_RATE_PER_UNIT], "daily rate"
                    ),
                    stored_units=whole_number(row[WAREHOUSE_STORED_UNITS], "stored units"),
                )
                warehouses = add_warehouse(warehouse, warehouses)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
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
            docking = Docking(
                ship_id=row[DOCKING_SHIP_ID],
                dock_id=row[DOCKING_DOCK_ID],
                docked_at=row[DOCKING_DOCKED_AT],
            )
            try:
                dockings = record_docking(docking, dockings)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
    return dockings


def write_dockings(path: Path, dockings: list[Docking]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(DOCKING_HEADER)
        for docking in dockings:
            writer.writerow([docking.ship_id, docking.dock_id, docking.docked_at])


def read_stored_cargo(path: Path) -> list[StoredCargo]:
    if not path.exists():
        return []
    stored: list[StoredCargo] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != STORED_CARGO_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            try:
                cargo = StoredCargo(
                    ship_id=row[STORED_CARGO_SHIP_ID],
                    warehouse_id=row[STORED_CARGO_WAREHOUSE_ID],
                    units=whole_number(row[STORED_CARGO_UNITS], "units"),
                    stored_at=row[STORED_CARGO_AT],
                )
                stored = store_cargo(cargo, stored)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
    return stored


def write_stored_cargo(path: Path, stored: list[StoredCargo]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(STORED_CARGO_HEADER)
        for cargo in stored:
            writer.writerow([cargo.ship_id, cargo.warehouse_id, cargo.units, cargo.stored_at])


def read_departures(path: Path) -> list[Departure]:
    if not path.exists():
        return []
    departures: list[Departure] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) != DEPARTURE_FIELDS_PER_ROW:
                raise ValueError(f"malformed row in {path}: {row}")
            try:
                departure = Departure(
                    ship_id=row[DEPARTURE_SHIP_ID],
                    dock_id=row[DEPARTURE_DOCK_ID],
                    docked_at=row[DEPARTURE_DOCKED_AT],
                    departed_at=row[DEPARTURE_DEPARTED_AT],
                    hours=whole_number(row[DEPARTURE_HOURS], "hours"),
                    docking_fee=decimal_number(row[DEPARTURE_DOCKING_FEE], "docking fee"),
                )
                departures = record_departure(departure, departures)
            except ValueError as error:
                raise ValueError(f"malformed row in {path}: {error}") from None
    return departures


def write_departures(path: Path, departures: list[Departure]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(DEPARTURE_HEADER)
        for departure in departures:
            writer.writerow(
                [
                    departure.ship_id,
                    departure.dock_id,
                    departure.docked_at,
                    departure.departed_at,
                    departure.hours,
                    departure.docking_fee,
                ]
            )
