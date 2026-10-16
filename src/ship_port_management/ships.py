from dataclasses import dataclass


@dataclass(frozen=True)
class Ship:
    ship_id: str
    name: str
    arrival_time: str  # ISO text, e.g. "2026-10-14T09:30"
    capacity: int
    cargo_units: int


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
    if not cargo_within_capacity(new_ship):
        raise ValueError("cargo units must be between 0 and capacity")
    return registered + [new_ship]
