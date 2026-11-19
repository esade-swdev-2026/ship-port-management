from dataclasses import dataclass

from ship_port_management.times import parse_time


@dataclass(frozen=True)
class Ship:
    ship_id: str
    name: str
    arrival_time: str
    capacity: int
    cargo_units: int


def is_valid_ship_capacity(capacity: int) -> bool:
    return capacity > 0


def cargo_within_capacity(ship: Ship) -> bool:
    return 0 <= ship.cargo_units <= ship.capacity


def remaining_capacity(ship: Ship) -> int:
    return ship.capacity - ship.cargo_units


def is_duplicate_ship(ship_id: str, ships: list[Ship]) -> bool:
    return any(ship.ship_id == ship_id for ship in ships)


def register_ship(new_ship: Ship, ships: list[Ship]) -> list[Ship]:
    if not new_ship.ship_id.strip():
        raise ValueError("ship ID must not be empty")
    if not new_ship.name.strip():
        raise ValueError("ship name must not be empty")
    if not is_valid_ship_capacity(new_ship.capacity):
        raise ValueError(f"capacity must be positive, got {new_ship.capacity}")
    if not cargo_within_capacity(new_ship):
        raise ValueError("cargo units must be between 0 and capacity")
    parse_time(new_ship.arrival_time, "arrival time")
    if is_duplicate_ship(new_ship.ship_id, ships):
        raise ValueError(f"ship {new_ship.ship_id} has already been registered")
    return ships + [new_ship]


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


def replace_ship(updated_ship: Ship, ships: list[Ship]) -> list[Ship]:
    return [updated_ship if ship.ship_id == updated_ship.ship_id else ship for ship in ships]
