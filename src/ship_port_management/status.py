from ship_port_management.dockings import Docking, occupied_dock_ids
from ship_port_management.docks import Dock, describe_dock, is_dock_available
from ship_port_management.ships import Ship
from ship_port_management.warehouses import Warehouse

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
    return warehouse.stored_units / warehouse.capacity * PERCENT


def stored_percentage(warehouses: list[Warehouse]) -> int:
    capacity = sum(warehouse.capacity for warehouse in warehouses)
    stored = sum(warehouse.stored_units for warehouse in warehouses)
    return round(stored / capacity * PERCENT) if capacity else 0


def describe_port_summary(
    ships: list[Ship], docks: list[Dock], warehouses: list[Warehouse], dockings: list[Docking]
) -> str:
    free = len(available_docks(docks, occupied_dock_ids(dockings)))
    ship_count = f"{len(ships)} ship" + ("" if len(ships) == 1 else "s")
    return (
        f"{ship_count} · {free}/{len(docks)} docks free · {stored_percentage(warehouses)}% stored"
    )


def describe_ship_location(ship: Ship, dockings: list[Docking]) -> str:
    dock_id = current_dock_id(ship.ship_id, dockings)
    location = "not docked" if dock_id is None else f"at dock {dock_id}"
    return f"{ship.ship_id}  {ship.name}  {location}"


def describe_fill_level(warehouse: Warehouse) -> str:
    return (
        f"{warehouse.warehouse_id}  {warehouse.stored_units}/{warehouse.capacity} units  "
        f"{int(fill_percentage(warehouse))}% full"
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
