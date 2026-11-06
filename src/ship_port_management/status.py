from ship_port_management.dockings import Docking, occupied_dock_ids
from ship_port_management.docks import Dock, describe_dock, is_dock_available
from ship_port_management.ships import Ship
from ship_port_management.warehouses import (
    Warehouse,
    is_valid_storage_capacity,
    stored_within_capacity,
)

PERCENT = 100
EMPTY_SECTION = "none"


def current_dock_id(ship_id: str, dockings: list[Docking]) -> str | None:
    for docking in dockings:
        if docking.ship_id == ship_id:
            return docking.dock_id
    return None


def available_docks(docks: list[Dock], occupied: set[str]) -> list[Dock]:
    return [dock for dock in docks if is_dock_available(dock, occupied)]


def fill_percentage(warehouse: Warehouse) -> float:
    name = warehouse.warehouse_id
    if not is_valid_storage_capacity(warehouse.capacity):
        raise ValueError(f"warehouse {name} has capacity {warehouse.capacity}, it must be positive")
    if not stored_within_capacity(warehouse):
        raise ValueError(
            f"warehouse {name} holds {warehouse.stored_units} units "
            f"but its capacity is {warehouse.capacity}"
        )
    return warehouse.stored_units / warehouse.capacity * PERCENT


def describe_ship_location(ship: Ship, dockings: list[Docking]) -> str:
    dock_id = current_dock_id(ship.ship_id, dockings)
    location = "not docked" if dock_id is None else f"at dock {dock_id}"
    return f"{ship.ship_id}  {ship.name}  {location}"


def describe_fill_level(warehouse: Warehouse) -> str:
    return (
        f"{warehouse.warehouse_id}  {warehouse.stored_units}/{warehouse.capacity} units  "
        f"{fill_percentage(warehouse):.0f}% full"
    )


def format_section(title: str, lines: list[str]) -> list[str]:
    return [title] + [f"  {line}" for line in lines or [EMPTY_SECTION]]


def format_port_status(
    ships: list[Ship], docks: list[Dock], warehouses: list[Warehouse], dockings: list[Docking]
) -> list[str]:
    occupied = occupied_dock_ids(dockings)
    ship_lines = [describe_ship_location(ship, dockings) for ship in ships]
    dock_lines = [describe_dock(dock, occupied) for dock in available_docks(docks, occupied)]
    storage_lines = [describe_fill_level(warehouse) for warehouse in warehouses]
    return (
        format_section("Ships", ship_lines)
        + format_section("Available docks", dock_lines)
        + format_section("Storage", storage_lines)
    )
