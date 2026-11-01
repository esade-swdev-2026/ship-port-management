from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Ship:
    ship_id: str
    name: str
    arrival_time: str  # ISO text, e.g. "2026-10-14T09:30"
    capacity: int
    cargo_units: int


def is_valid_arrival_time(arrival_time: str) -> bool:
    try:
        datetime.fromisoformat(arrival_time)
    except ValueError:
        return False
    return True


def cargo_within_capacity(ship: Ship) -> bool:
    return 0 <= ship.cargo_units <= ship.capacity


def remaining_capacity(ship: Ship) -> int:
    return ship.capacity - ship.cargo_units


def is_duplicate_ship(new_ship: Ship, registered: list[Ship]) -> bool:
    registered_ids = {ship.ship_id for ship in registered}
    return new_ship.ship_id in registered_ids


def register_ship(new_ship: Ship, registered: list[Ship]) -> list[Ship]:
    if is_duplicate_ship(new_ship, registered):
        raise ValueError(f"ship: {new_ship.ship_id} has already been registered")
    if new_ship.capacity <= 0:
        raise ValueError("capacity must be positive")
    if not cargo_within_capacity(new_ship):
        raise ValueError("cargo units must be between 0 and capacity")
    if not is_valid_arrival_time(new_ship.arrival_time):
        raise ValueError(
            f"arrival time must look like 2026-10-18T09:30, got {new_ship.arrival_time}"
        )
    return registered + [new_ship]


def describe_ship(ship: Ship) -> str:
    return (
        f"{ship.ship_id}  {ship.name}  arrived {ship.arrival_time}  "
        f"cargo {ship.cargo_units}/{ship.capacity}"
    )


def find_ship(ship_id: str, ships: list[Ship]) -> Ship:
    for ship in ships:
        if ship.ship_id == ship_id:
            return ship
    raise ValueError(f"ship {ship_id} is not registered")
