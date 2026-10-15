import csv
from pathlib import Path

from ship_port_management.ships import Ship

SHIP_ID = 0
NAME = 1
ARRIVAL_TIME = 2
CAPACITY = 3
CARGO_UNITS = 4
HEADER = ["ship_id", "name", "arrival_time", "capacity", "cargo_units"]
FIELDS_PER_ROW = len(HEADER)


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
