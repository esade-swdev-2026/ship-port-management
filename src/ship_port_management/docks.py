import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Dock:
    dock_id: str
    max_ship_size: int
    hourly_rate: float


def is_valid_max_ship_size(max_ship_size: int) -> bool:
    return max_ship_size > 0


def is_valid_hourly_rate(hourly_rate: float) -> bool:
    return math.isfinite(hourly_rate) and hourly_rate > 0


def is_duplicate_dock(dock_id: str, docks: list[Dock]) -> bool:
    return any(dock.dock_id == dock_id for dock in docks)


def add_dock(new_dock: Dock, docks: list[Dock]) -> list[Dock]:
    if not new_dock.dock_id.strip():
        raise ValueError("dock ID must not be empty")
    if not is_valid_max_ship_size(new_dock.max_ship_size):
        raise ValueError(f"max ship size must be positive, got {new_dock.max_ship_size}")
    if not is_valid_hourly_rate(new_dock.hourly_rate):
        raise ValueError(
            f"hourly rate must be a positive, finite number, got {new_dock.hourly_rate}"
        )
    if is_duplicate_dock(new_dock.dock_id, docks):
        raise ValueError(f"dock {new_dock.dock_id} is already registered")
    return docks + [new_dock]


def is_dock_available(dock: Dock, occupied_dock_ids: set[str]) -> bool:
    return dock.dock_id not in occupied_dock_ids


def describe_dock(dock: Dock, occupied_dock_ids: set[str]) -> str:
    status = "available" if is_dock_available(dock, occupied_dock_ids) else "occupied"
    return (
        f"{dock.dock_id}  max ship size {dock.max_ship_size}  "
        f"rate {dock.hourly_rate} per hour  {status}"
    )


def find_dock(dock_id: str, docks: list[Dock]) -> Dock:
    for dock in docks:
        if dock.dock_id == dock_id:
            return dock
    raise ValueError(f"dock {dock_id} does not exist")
