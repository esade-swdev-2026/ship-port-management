from dataclasses import dataclass

from ship_port_management.docks import Dock
from ship_port_management.ships import Ship


@dataclass(frozen=True)
class Docking:
    ship_id: str
    dock_id: str


def ship_fits_dock(ship: Ship, dock: Dock) -> bool:
    return ship.capacity <= dock.max_ship_size


def occupied_dock_ids(dockings: list[Docking]) -> set[str]:
    return {docking.dock_id for docking in dockings}


def is_ship_docked(ship_id: str, dockings: list[Docking]) -> bool:
    return any(docking.ship_id == ship_id for docking in dockings)


def dock_ship(ship: Ship, dock: Dock, dockings: list[Docking]) -> list[Docking]:
    if not ship_fits_dock(ship, dock):
        raise ValueError(
            f"ship {ship.ship_id} has size {ship.capacity}, "
            f"dock {dock.dock_id} takes at most {dock.max_ship_size}"
        )
    if dock.dock_id in occupied_dock_ids(dockings):
        raise ValueError(f"dock {dock.dock_id} is already occupied")
    if is_ship_docked(ship.ship_id, dockings):
        raise ValueError(f"ship {ship.ship_id} is already docked")
    return dockings + [Docking(ship.ship_id, dock.dock_id)]
