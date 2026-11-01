from dataclasses import dataclass, replace

from ship_port_management.dockings import Docking, is_ship_docked
from ship_port_management.ships import Ship, remaining_capacity
from ship_port_management.warehouses import Warehouse, free_units


@dataclass(frozen=True)
class CargoMove:
    ship: Ship
    warehouse: Warehouse


def check_ship_can_move_cargo(ship: Ship, units: int, dockings: list[Docking]) -> None:
    if units <= 0:
        raise ValueError(f"units to move must be positive, got {units}")
    if not is_ship_docked(ship.ship_id, dockings):
        raise ValueError(f"ship {ship.ship_id} is not docked")


def unload_cargo(
    ship: Ship, warehouse: Warehouse, units: int, dockings: list[Docking]
) -> CargoMove:
    check_ship_can_move_cargo(ship, units, dockings)
    if units > ship.cargo_units:
        raise ValueError(f"ship {ship.ship_id} carries only {ship.cargo_units} units")
    if units > free_units(warehouse):
        raise ValueError(
            f"warehouse {warehouse.warehouse_id} has room for only {free_units(warehouse)} units"
        )
    return CargoMove(
        ship=replace(ship, cargo_units=ship.cargo_units - units),
        warehouse=replace(warehouse, stored_units=warehouse.stored_units + units),
    )


def load_cargo(ship: Ship, warehouse: Warehouse, units: int, dockings: list[Docking]) -> CargoMove:
    check_ship_can_move_cargo(ship, units, dockings)
    if units > warehouse.stored_units:
        raise ValueError(
            f"warehouse {warehouse.warehouse_id} holds only {warehouse.stored_units} units"
        )
    if units > remaining_capacity(ship):
        raise ValueError(
            f"ship {ship.ship_id} has room for only {remaining_capacity(ship)} more units"
        )
    return CargoMove(
        ship=replace(ship, cargo_units=ship.cargo_units + units),
        warehouse=replace(warehouse, stored_units=warehouse.stored_units - units),
    )
