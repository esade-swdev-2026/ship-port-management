from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class Ship:
    imo: str
    capacity: int
    cargo_units: int = 0


@dataclass(frozen=True)
class Dock:
    name: str
    max_ship_size: int
    hourly_rate: float
    occupied: bool = False


def remaining_capacity(ship: Ship) -> int:
    return ship.capacity - ship.cargo_units


def can_dock(ship: Ship, dock: Dock) -> bool:
    return not dock.occupied and ship.capacity <= dock.max_ship_size


def find_available_dock(ship: Ship, docks: list[Dock]) -> Dock | None:
    for dock in docks:
        if can_dock(ship, dock):
            return dock
    return None


def unload_cargo(ship: Ship, units: int) -> Ship:
    if units <= 0:
        raise ValueError("units must be positive")
    if units > ship.cargo_units:
        raise ValueError("cannot unload more units than the ship carries")
    return replace(ship, cargo_units=ship.cargo_units - units)


def load_cargo(ship: Ship, units: int) -> Ship:
    if units <= 0:
        raise ValueError("units must be positive")
    if units > remaining_capacity(ship):
        raise ValueError("cannot load more units than the ship has room for")
    return replace(ship, cargo_units=ship.cargo_units + units)


def docking_fee(arrival: datetime, departure: datetime, hourly_rate: float) -> float:
    if departure < arrival:
        raise ValueError("departure cannot be before arrival")
    hours = (departure - arrival).total_seconds() / 3600
    return hours * hourly_rate
