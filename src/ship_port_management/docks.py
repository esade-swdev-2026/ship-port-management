import math
from dataclasses import dataclass

MIN_SHIP_SIZE = 1
MIN_HOURLY_RATE = 0.0


@dataclass(frozen=True)
class Dock:
    dock_id: str
    max_ship_size: int
    hourly_rate: float


def add_dock(new_dock: Dock, docks: list[Dock]) -> list[Dock]:
    if new_dock.max_ship_size < MIN_SHIP_SIZE:
        raise ValueError(f"Max ship size, {new_dock.max_ship_size}, must be a positive integer.")

    if not math.isfinite(new_dock.hourly_rate):
        raise ValueError(f"Hourly rate, {new_dock.hourly_rate}, must be a finite number.")

    if new_dock.hourly_rate < MIN_HOURLY_RATE:
        raise ValueError(f"Hourly rate, {new_dock.hourly_rate}, can not be negative.")

    for dock in docks:
        if new_dock.dock_id == dock.dock_id:
            raise ValueError(f"Dock: {new_dock.dock_id} is already present.")

    docks_copy = docks.copy()
    docks_copy.append(new_dock)
    return docks_copy


def is_dock_available(dock: Dock, occupied_dock_ids: set[str]) -> bool:
    return dock.dock_id not in occupied_dock_ids


def describe_dock(dock: Dock, occupied_dock_ids: set[str]) -> str:

    status = "available" if is_dock_available(dock, occupied_dock_ids) else "occupied"
    return (
        f"Dock id: {dock.dock_id}, Max ship size = {dock.max_ship_size}, "
        f"Hourly rate: {dock.hourly_rate}, Status: {status}"
    )


def find_dock(dock_id: str, docks: list[Dock]) -> Dock:
    for dock in docks:
        if dock.dock_id == dock_id:
            return dock
    raise ValueError(f"dock {dock_id} does not exist")
