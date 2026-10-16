from dataclasses import dataclass


@dataclass(frozen=True)
class Warehouse:
    warehouse_id: str
    capacity: int
    daily_rate_per_unit: float
    stored_units: int = 0


def is_valid_storage_capacity(capacity: int) -> bool:
    return capacity > 0


def is_valid_daily_rate(daily_rate_per_unit: float) -> bool:
    return daily_rate_per_unit > 0


def is_duplicate_warehouse(warehouse_id: str, existing_warehouse_ids: set[str]) -> bool:
    return warehouse_id in existing_warehouse_ids


def _check_stored_units(capacity: int, stored_units: int) -> None:
    if not 0 <= stored_units <= capacity:
        raise ValueError("Used units must be between 0 and capacity")


def free_units(capacity: int, stored_units: int) -> int:
    _check_stored_units(capacity, stored_units)
    return capacity - stored_units


def fill_percentage(capacity: int, stored_units: int) -> float:
    _check_stored_units(capacity, stored_units)
    return stored_units / capacity * 100


def add_warehouse(warehouses: list[Warehouse], new_warehouse: Warehouse) -> list[Warehouse]:
    if not is_valid_storage_capacity(new_warehouse.capacity):
        raise ValueError(f"The capacity, {new_warehouse.capacity}, must be a positive integer.")
    if not is_valid_daily_rate(new_warehouse.daily_rate_per_unit):
        raise ValueError(f"The daily rate, {new_warehouse.daily_rate_per_unit}, must be positive.")
    if new_warehouse.stored_units != 0:
        raise ValueError(
            f"The new storage area must be empty, got {new_warehouse.stored_units} used units."
        )
    existing_ids = {area.warehouse_id for area in warehouses}
    if is_duplicate_warehouse(new_warehouse.warehouse_id, existing_ids):
        raise ValueError(f"Storage area {new_warehouse.warehouse_id} already exists.")
    return warehouses + [new_warehouse]
