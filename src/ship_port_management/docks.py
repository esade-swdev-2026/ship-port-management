from dataclasses import dataclass


@dataclass(frozen=True)
class Dock:
    dock_id: str
    max_ship_size: int
    hourly_rate: float


def add_dock(docks: list[Dock], new_dock: Dock) -> list[Dock]:

    if new_dock.max_ship_size <= 0:
        raise ValueError(f"Max ship size, {new_dock.max_ship_size}, must be a positive integer.")

    if new_dock.hourly_rate < 0:
        raise ValueError(f"Hourly Rate, {new_dock.hourly_rate}, can not be negative.")

    for dock in docks:
        if new_dock.dock_id == dock.dock_id:
            raise ValueError(f"Dock: {new_dock.dock_id} is already present.")

    docks_copy = docks.copy()
    docks_copy.append(new_dock)
    return docks_copy


def is_dock_available(dock: Dock, occupied_dock_ids: set[str]) -> bool:
    return dock.dock_id not in occupied_dock_ids
