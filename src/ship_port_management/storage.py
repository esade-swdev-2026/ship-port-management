from dataclasses import dataclass, replace
from datetime import datetime

from ship_port_management.warehouses import Warehouse, find_warehouse

FREE_STORAGE_DAYS = 3


@dataclass(frozen=True)
class StoredCargo:
    ship_id: str
    warehouse_id: str
    units: int
    stored_at: str  # ISO text, e.g. "2026-10-14T09:30"


def parse_time(text: str, what: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{what} must look like 2026-10-18T09:30, got {text}") from None
    if parsed.tzinfo is not None:
        raise ValueError(f"{what} must be a local time without a timezone, got {text}")
    return parsed


def store_cargo(new_cargo: StoredCargo, stored: list[StoredCargo]) -> list[StoredCargo]:
    parse_time(new_cargo.stored_at, "storage time")
    return stored + [new_cargo]


def take_cargo(
    ship_id: str, warehouse_id: str, units: int, stored: list[StoredCargo]
) -> list[StoredCargo]:
    """Takes the ship's own cargo first, oldest first, then other ships' cargo, oldest first."""
    pickup_order = sorted(
        (index for index, cargo in enumerate(stored) if cargo.warehouse_id == warehouse_id),
        key=lambda index: (
            stored[index].ship_id != ship_id,
            parse_time(stored[index].stored_at, "storage time"),
        ),
    )
    remaining = list(stored)
    units_left = units
    for index in pickup_order:
        taken = min(units_left, remaining[index].units)
        remaining[index] = replace(remaining[index], units=remaining[index].units - taken)
        units_left -= taken
    return [cargo for cargo in remaining if cargo.units > 0]


def chargeable_days(cargo: StoredCargo, as_of: datetime) -> int:
    days_stored = (as_of - parse_time(cargo.stored_at, "storage time")).days
    return max(0, days_stored - FREE_STORAGE_DAYS)


def storage_fee(cargo: StoredCargo, warehouse: Warehouse, as_of: datetime) -> float:
    return cargo.units * warehouse.daily_rate_per_unit * chargeable_days(cargo, as_of)


def fees_by_ship(
    stored: list[StoredCargo], warehouses: list[Warehouse], as_of: str
) -> dict[str, float]:
    as_of_time = parse_time(as_of, "fee time")
    fees: dict[str, float] = {}
    for cargo in stored:
        warehouse = find_warehouse(cargo.warehouse_id, warehouses)
        fee = storage_fee(cargo, warehouse, as_of_time)
        fees[cargo.ship_id] = fees.get(cargo.ship_id, 0.0) + fee
    return fees


def describe_storage_fee(ship_id: str, fee: float) -> str:
    return f"{ship_id}  owes {fee:.2f} for storage"
