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


def stored_within_capacity(warehouse: Warehouse) -> bool:
    return 0 <= warehouse.stored_units <= warehouse.capacity


def free_units(warehouse: Warehouse) -> int:
    return warehouse.capacity - warehouse.stored_units


def is_duplicate_warehouse(warehouse_id: str, existing_warehouse_ids: set[str]) -> bool:
    return warehouse_id in existing_warehouse_ids


def add_warehouse(new_warehouse: Warehouse, warehouses: list[Warehouse]) -> list[Warehouse]:
    if not is_valid_storage_capacity(new_warehouse.capacity):
        raise ValueError(f"capacity must be positive, got {new_warehouse.capacity}")
    if not is_valid_daily_rate(new_warehouse.daily_rate_per_unit):
        raise ValueError(f"daily rate must be positive, got {new_warehouse.daily_rate_per_unit}")
    if not stored_within_capacity(new_warehouse):
        raise ValueError(
            f"stored units must be between 0 and capacity, got {new_warehouse.stored_units}"
        )
    existing_ids = {warehouse.warehouse_id for warehouse in warehouses}
    if is_duplicate_warehouse(new_warehouse.warehouse_id, existing_ids):
        raise ValueError(f"warehouse {new_warehouse.warehouse_id} is already registered")
    return warehouses + [new_warehouse]
